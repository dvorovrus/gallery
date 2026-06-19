from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from app.core.database import get_db
from app.core.config import get_settings
from app.core.dt import utcnow
from app.api.auth import get_current_user
from app.models.models import User, Album, Photo
from app.schemas.schemas import AlbumCreate, AlbumResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Выбор хранилища в зависимости от настроек
if settings.STORAGE_TYPE == "google_drive":
    from app.services.google_drive import drive_service as storage_service
elif settings.STORAGE_TYPE == "google_drive_oauth":
    from app.services.google_drive_oauth import drive_oauth_service as storage_service
else:
    from app.services.local_storage import storage_service

router = APIRouter(prefix="/albums", tags=["albums"])

@router.get("", response_model=List[AlbumResponse])
def get_albums(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    albums = db.query(Album).filter(Album.user_id == current_user.id).all()
    return albums

@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(album_data: AlbumCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.scheduler import album_scheduler
    
    # Create user folder if doesn't exist (stored in user metadata or created on first album)
    # For simplicity, we'll create it on each album creation and handle duplicates in Drive

    # Calculate expiration datetime
    expires_at = album_scheduler.calculate_expires_at(album_data.expiration_type)
    
    new_album = Album(
        user_id=current_user.id,
        title=album_data.title,
        is_public=False,
        expiration_type=album_data.expiration_type,
        expires_at=expires_at,
        auto_delete_scheduled=False
    )

    db.add(new_album)
    db.commit()
    db.refresh(new_album)
    
    # Schedule deletion if album has expiration
    if expires_at is not None:
        if album_scheduler.schedule_album_deletion(new_album.id, expires_at):
            new_album.auto_delete_scheduled = True
            db.commit()
            db.refresh(new_album)

    return new_album

@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.scheduler import album_scheduler
    
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    # Cancel scheduled deletion if exists
    if album.auto_delete_scheduled:
        album_scheduler.cancel_album_deletion(album_id)

    # Delete all photos from storage and database
    photos = db.query(Photo).filter(Photo.album_id == album_id).all()
    for photo in photos:
        try:
            storage_service.delete_file(photo.drive_file_id)
            if photo.thumbnail_file_id:
                storage_service.delete_file(photo.thumbnail_file_id)
        except Exception as e:
            logger.warning("Failed to delete photo file %s: %s", photo.id, e)

        # Delete photo record from database
        db.delete(photo)

    # Delete album folder from storage
    try:
        user_folder_id = storage_service.create_user_folder(current_user.id)
        album_folder_id = storage_service.get_album_folder_id(user_folder_id, album_id)
        if album_folder_id:
            storage_service.delete_folder(album_folder_id)
            logger.info("Deleted album folder: album_%s", album_id)
    except Exception as e:
        logger.warning("Failed to delete album folder: %s", e)

    # Delete album record from database
    db.delete(album)
    db.commit()

    return None

@router.get("/{album_id}/time-remaining")
def get_album_time_remaining(album_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get remaining time until album expiration"""
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    if album.expiration_type == "unlimited" or album.expires_at is None:
        return {
            "album_id": album_id,
            "expiration_type": album.expiration_type,
            "expires_at": None,
            "is_expired": False,
            "seconds_remaining": None,
            "days_remaining": None,
            "hours_remaining": None,
            "minutes_remaining": None
        }
    
    now = utcnow()
    is_expired = album.expires_at <= now
    
    if is_expired:
        return {
            "album_id": album_id,
            "expiration_type": album.expiration_type,
            "expires_at": album.expires_at.isoformat(),
            "is_expired": True,
            "seconds_remaining": 0,
            "days_remaining": 0,
            "hours_remaining": 0,
            "minutes_remaining": 0
        }
    
    time_delta = album.expires_at - now
    total_seconds = int(time_delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    return {
        "album_id": album_id,
        "expiration_type": album.expiration_type,
        "expires_at": album.expires_at.isoformat(),
        "is_expired": False,
        "seconds_remaining": total_seconds,
        "days_remaining": days,
        "hours_remaining": hours,
        "minutes_remaining": minutes
    }
