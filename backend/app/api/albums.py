from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.config import get_settings
from app.api.auth import get_current_user
from app.models.models import User, Album, Photo
from app.schemas.schemas import AlbumCreate, AlbumResponse

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
    # Create user folder if doesn't exist (stored in user metadata or created on first album)
    # For simplicity, we'll create it on each album creation and handle duplicates in Drive

    new_album = Album(
        user_id=current_user.id,
        title=album_data.title,
        is_public=False
    )

    db.add(new_album)
    db.commit()
    db.refresh(new_album)

    return new_album

@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    # Delete all photos from storage and database
    photos = db.query(Photo).filter(Photo.album_id == album_id).all()
    for photo in photos:
        try:
            storage_service.delete_file(photo.drive_file_id)
        except Exception as e:
            print(f"Failed to delete photo file {photo.id}: {str(e)}")

        # Delete photo record from database
        db.delete(photo)

    # Delete album folder from storage
    try:
        # Находим папку альбома по имени
        user_folder_id = storage_service.create_user_folder(current_user.id)
        album_folder_id = storage_service.get_album_folder_id(user_folder_id, album_id)
        if album_folder_id:
            storage_service.delete_folder(album_folder_id)
            print(f"Deleted album folder: album_{album_id}")
    except Exception as e:
        print(f"Failed to delete album folder: {str(e)}")

    # Delete album record from database
    db.delete(album)
    db.commit()

    return None
