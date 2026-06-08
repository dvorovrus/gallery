"""
Scheduler service for managing album expiration and automatic deletion.
Uses APScheduler with SQLAlchemy jobstore for persistence across restarts.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Expiration type to timedelta mapping
EXPIRATION_DELTAS = {
    "7_days": timedelta(days=7),
    "14_days": timedelta(days=14),
    "30_days": timedelta(days=30),
}


def delete_album_task(album_id: int):
    """
    Delete an album and all its photos.
    This is called by the scheduler at the scheduled time.
    
    Args:
        album_id: ID of the album to delete
    """
    db: Session = SessionLocal()
    
    try:
        # Import here to avoid circular imports
        from app.models.models import Album, Photo
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Select storage service
        if settings.STORAGE_TYPE == "google_drive":
            from app.services.google_drive import drive_service as storage_service
        elif settings.STORAGE_TYPE == "google_drive_oauth":
            from app.services.google_drive_oauth import drive_oauth_service as storage_service
        else:
            from app.services.local_storage import storage_service
        
        # Fetch album
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            logger.warning(f"Album {album_id} not found, may have been deleted already")
            return
        
        # Check if album is actually expired
        if album.expires_at and album.expires_at > datetime.utcnow():
            logger.warning(f"Album {album_id} not yet expired, skipping deletion")
            return
        
        logger.info(f"Deleting expired album {album_id}: {album.title}")
        
        # Delete all photos from storage and database
        photos = db.query(Photo).filter(Photo.album_id == album_id).all()
        for photo in photos:
            try:
                storage_service.delete_file(photo.drive_file_id)
                if photo.thumbnail_file_id:
                    storage_service.delete_file(photo.thumbnail_file_id)
            except Exception as e:
                logger.error(f"Failed to delete photo file {photo.id}: {str(e)}")
            
            db.delete(photo)
        
        # Delete album folder from storage
        try:
            user_folder_id = storage_service.create_user_folder(album.user_id)
            album_folder_id = storage_service.get_album_folder_id(user_folder_id, album_id)
            if album_folder_id:
                storage_service.delete_folder(album_folder_id)
        except Exception as e:
            logger.error(f"Failed to delete album folder: {str(e)}")
        
        # Delete album from database
        db.delete(album)
        db.commit()
        
        logger.info(f"Successfully deleted expired album {album_id}")
        
    except Exception as e:
        logger.error(f"Error deleting album {album_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()


def cleanup_expired_albums_task():
    """
    Cleanup job that runs periodically to catch any albums
    that may have been missed by the scheduler.
    """
    db: Session = SessionLocal()
    
    try:
        from app.models.models import Album
        
        now = datetime.utcnow()
        
        # Find albums that are expired but still exist
        expired_albums = db.query(Album).filter(
            Album.expires_at.isnot(None),
            Album.expires_at <= now
        ).all()
        
        if expired_albums:
            logger.info(f"Cleanup found {len(expired_albums)} expired albums")
            
            for album in expired_albums:
                logger.info(f"Cleaning up expired album {album.id}")
                delete_album_task(album.id)
        
    except Exception as e:
        logger.error(f"Error in cleanup job: {str(e)}")
    finally:
        db.close()


class AlbumSchedulerService:
    """Service for scheduling album deletion tasks"""
    
    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
    
    def start(self):
        """Initialize and start the scheduler"""
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return
        
        # Configure jobstore to use the same database as the app
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)
        }
        
        job_defaults = {
            'coalesce': True,  # Combine multiple missed executions into one
            'max_instances': 1,  # Only one instance of a job at a time
            'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add cleanup job to run every 10 minutes
        self.scheduler.add_job(
            func=cleanup_expired_albums_task,
            trigger=CronTrigger(minute='*/10'),
            id='cleanup_expired_albums',
            name='Cleanup expired albums',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Album scheduler started successfully")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
            logger.info("Album scheduler stopped")
    
    def schedule_album_deletion(self, album_id: int, expires_at: datetime) -> bool:
        """
        Schedule an album for deletion at a specific datetime.
        
        Args:
            album_id: ID of the album to delete
            expires_at: Datetime when the album should be deleted (UTC)
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        if self.scheduler is None:
            logger.error("Scheduler not started")
            return False
        
        job_id = f"delete_album_{album_id}"
        
        try:
            # Remove existing job if present
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Schedule new deletion job
            self.scheduler.add_job(
                func=delete_album_task,
                trigger=DateTrigger(run_date=expires_at),
                args=[album_id],
                id=job_id,
                name=f"Delete album {album_id}",
                replace_existing=True
            )
            
            logger.info(f"Scheduled deletion for album {album_id} at {expires_at}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule deletion for album {album_id}: {str(e)}")
            return False
    
    def cancel_album_deletion(self, album_id: int) -> bool:
        """
        Cancel a scheduled album deletion.
        
        Args:
            album_id: ID of the album
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if self.scheduler is None:
            logger.error("Scheduler not started")
            return False
        
        job_id = f"delete_album_{album_id}"
        
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled scheduled deletion for album {album_id}")
                return True
            else:
                logger.warning(f"No scheduled deletion found for album {album_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel deletion for album {album_id}: {str(e)}")
            return False
    
    def calculate_expires_at(self, expiration_type: str) -> Optional[datetime]:
        """
        Calculate expiration datetime based on expiration type.
        
        Args:
            expiration_type: Type of expiration (unlimited, 7_days, 14_days, 30_days)
            
        Returns:
            Expiration datetime in UTC, or None if unlimited
        """
        if expiration_type == "unlimited":
            return None
        
        delta = EXPIRATION_DELTAS.get(expiration_type)
        if delta is None:
            logger.warning(f"Unknown expiration type: {expiration_type}, treating as unlimited")
            return None
        
        return datetime.utcnow() + delta


# Global scheduler instance
album_scheduler = AlbumSchedulerService()
