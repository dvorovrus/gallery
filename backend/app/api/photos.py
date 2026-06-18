from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import io
import uuid
import tempfile
import os
import mimetypes
import zipfile
import re
from urllib.parse import quote
from app.core.database import get_db
from app.core.config import get_settings
from app.api.auth import get_current_user
from app.models.models import User, Album, Photo, Share
from app.schemas.schemas import PhotoResponse
from app.services.photo_thumbnails import generate_thumbnail_bytes

settings = get_settings()

# Выбор хранилища в зависимости от настроек
if settings.STORAGE_TYPE == "google_drive":
    from app.services.google_drive import drive_service as storage_service
elif settings.STORAGE_TYPE == "google_drive_oauth":
    from app.services.google_drive_oauth import drive_oauth_service as storage_service
else:
    from app.services.local_storage import storage_service

router = APIRouter(tags=["photos"])

# Pydantic модель для batch delete
class BatchDeleteRequest(BaseModel):
    photo_ids: List[int]


def build_thumbnail_file_name(photo_id: int) -> str:
    return f"photo_{photo_id}_thumbnail.jpg"


def build_thumbnail_bytes(file_content: bytes, width: int) -> bytes:
    return generate_thumbnail_bytes(file_content, width)


def store_thumbnail_file(original_content: bytes, photo_id: int, album_folder_id: str) -> str:
    try:
        print(f"Generating thumbnail bytes for photo {photo_id}")
        thumbnail_bytes = build_thumbnail_bytes(original_content, 400)
        print(f"Thumbnail bytes generated, size: {len(thumbnail_bytes)} bytes")
    except Exception as e:
        print(f"Error generating thumbnail bytes: {str(e)}")
        raise
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_thumb_{photo_id}.jpg") as temp_file:
        temp_file.write(thumbnail_bytes)
        temp_path = temp_file.name

    try:
        print(f"Uploading thumbnail to Google Drive: {build_thumbnail_file_name(photo_id)}")
        thumbnail_file_id = storage_service.upload_file(temp_path, build_thumbnail_file_name(photo_id), album_folder_id)
        print(f"Thumbnail uploaded successfully, file_id: {thumbnail_file_id}")
        return thumbnail_file_id
    except Exception as e:
        print(f"Error uploading thumbnail: {str(e)}")
        raise
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def build_safe_filename(filename: str, fallback: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]+', "_", (filename or "").strip())
    return sanitized or fallback


def build_photo_download_name(photo: Photo) -> str:
    extension = os.path.splitext(photo.filename or "")[1]
    caption_part = build_safe_filename(photo.caption or "", "")
    if caption_part:
        return f"{caption_part}{extension}" if extension else caption_part
    return build_safe_filename(photo.filename, f"photo-{photo.id}{extension}")


def build_content_disposition(filename: str) -> str:
    ascii_fallback = re.sub(r"[^\x20-\x7E]+", "_", filename).strip() or "download"
    encoded_filename = quote(filename)
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_filename}"


def _is_file_gone_error(exc: Exception) -> bool:
    """Распознать ошибку «файл не найден / удалён» от провайдера хранилища."""
    msg = str(exc)
    return any(s in msg for s in ("404", "File not found", "fileId", "cannotDownloadAbusiveFile"))


def _purge_photo_if_gone(db: Session, photo: Photo, exc: Exception) -> bool:
    """
    Самоисцеление: если файл фото пропал на хранилище — удалить запись из БД.
    Возвращает True, если запись была удалена.
    """
    if not _is_file_gone_error(exc):
        return False
    try:
        print(f"[self-heal] photo {photo.id} file gone, removing DB row")
        db.query(Share).filter(Share.photo_id == photo.id).delete(synchronize_session=False)
        db.delete(photo)
        db.commit()
        return True
    except Exception as purge_err:
        print(f"[self-heal] failed to purge photo {photo.id}: {purge_err}")
        db.rollback()
        return False

@router.get("/albums/{album_id}/photos", response_model=List[PhotoResponse])
def get_album_photos(album_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    photos = db.query(Photo).filter(Photo.album_id == album_id).all()
    return photos

@router.post("/albums/{album_id}/photos", response_model=List[PhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_photos(
    album_id: int,
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    uploaded_photos = []

    # Create user and album folders
    try:
        user_folder_id = storage_service.create_user_folder(current_user.id)
        album_folder_id = storage_service.create_album_folder(user_folder_id, album_id)
    except Exception as e:
        error_msg = str(e)
        if "not configured" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Drive is not configured. Please contact administrator to configure storage in Settings."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize storage: {error_msg}"
        )

    for file in files:
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        temp_path = temp_file.name

        try:
            print(f"Starting upload for file: {file.filename}")
            content = await file.read()
            print(f"File read successfully, size: {len(content)} bytes")
            temp_file.write(content)
            temp_file.close()

            # Upload to storage
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            print(f"Uploading to Google Drive with filename: {unique_filename}")
            drive_file_id = storage_service.upload_file(temp_path, unique_filename, album_folder_id)
            print(f"File uploaded successfully, drive_file_id: {drive_file_id}")

            # Save to database
            new_photo = Photo(
                album_id=album_id,
                drive_file_id=drive_file_id,
                thumbnail_file_id=None,
                filename=file.filename,
                caption=caption or "Без подписи"
            )

            db.add(new_photo)
            db.flush()
            print(f"Photo saved to database with id: {new_photo.id}")

            try:
                print(f"Generating thumbnail for photo {new_photo.id}")
                thumbnail_file_id = store_thumbnail_file(content, new_photo.id, album_folder_id)
                new_photo.thumbnail_file_id = thumbnail_file_id
                print(f"Thumbnail created successfully, thumbnail_file_id: {thumbnail_file_id}")
            except Exception as thumbnail_error:
                print(f"Warning: Could not create thumbnail for {file.filename}: {str(thumbnail_error)}")
                import traceback
                traceback.print_exc()

            uploaded_photos.append(new_photo)

        except Exception as e:
            print(f"Error uploading file {file.filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file {file.filename}: {str(e)}"
            )
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_path}: {str(e)}")

    db.commit()
    for photo in uploaded_photos:
        db.refresh(photo)

    return uploaded_photos

@router.get("/photos/{photo_id}")
def get_photo(
    photo_id: int,
    thumbnail: bool = Query(False, description="Return thumbnail instead of full image"),
    width: int = Query(400, description="Thumbnail width", ge=50, le=1000),
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    # Get file from storage
    try:
        print(f"Attempting to get photo {photo_id} with drive_file_id: {photo.drive_file_id}")
        if thumbnail:
            if photo.thumbnail_file_id:
                thumbnail_bytes = storage_service.get_file(photo.thumbnail_file_id)
            else:
                file_content = storage_service.get_file(photo.drive_file_id)
                thumbnail_bytes = build_thumbnail_bytes(file_content, width)
                try:
                    user_folder_id = storage_service.create_user_folder(photo.album.user_id)
                    album_folder_id = storage_service.create_album_folder(user_folder_id, photo.album_id)
                    photo.thumbnail_file_id = store_thumbnail_file(file_content, photo.id, album_folder_id)
                    db.commit()
                except Exception as store_error:
                    print(f"Warning: Could not persist thumbnail for photo {photo_id}: {str(store_error)}")

            return StreamingResponse(
                io.BytesIO(thumbnail_bytes),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400, immutable"},
            )

        file_content = storage_service.get_file(photo.drive_file_id)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400, immutable"},
        )
    except Exception as e:
        print(f"Error retrieving photo {photo_id}: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if _purge_photo_if_gone(db, photo, e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo no longer exists in storage and was removed"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve photo: {str(e)}"
        )


@router.get("/photos/{photo_id}/download")
def download_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).join(Album).filter(
        Photo.id == photo_id,
        Album.user_id == current_user.id
    ).first()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    try:
        file_content = storage_service.get_file(photo.drive_file_id)
        media_type = mimetypes.guess_type(photo.filename or "")[0] or "application/octet-stream"
        download_name = build_photo_download_name(photo)
        headers = {
            "Content-Disposition": build_content_disposition(download_name)
        }
        return StreamingResponse(io.BytesIO(file_content), media_type=media_type, headers=headers)
    except Exception as e:
        if _purge_photo_if_gone(db, photo, e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo no longer exists in storage and was removed"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download photo: {str(e)}"
        )


@router.get("/albums/{album_id}/download")
def download_album(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    photos = db.query(Photo).filter(Photo.album_id == album_id).all()
    if not photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album has no photos"
        )

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for index, photo in enumerate(photos, start=1):
                file_content = storage_service.get_file(photo.drive_file_id)
                original_name = build_photo_download_name(photo)
                file_root, file_ext = os.path.splitext(original_name)
                safe_name = build_safe_filename(file_root, f"photo-{photo.id}")
                archive_name = f"{index:02d}_{safe_name}{file_ext}"
                zip_file.writestr(archive_name, file_content)

        zip_buffer.seek(0)
        album_name = build_safe_filename(album.title, f"album-{album.id}")
        headers = {
            "Content-Disposition": build_content_disposition(f"{album_name}.zip")
        }
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download album: {str(e)}"
        )

@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    photo = db.query(Photo).join(Album).filter(
        Photo.id == photo_id,
        Album.user_id == current_user.id
    ).first()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    # Delete from storage
    try:
        storage_service.delete_file(photo.drive_file_id)
        if photo.thumbnail_file_id:
            storage_service.delete_file(photo.thumbnail_file_id)
    except Exception:
        pass

    db.delete(photo)
    db.commit()

    return None

@router.post("/photos/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def batch_delete_photos(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить несколько фото одновременно"""
    if not request.photo_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No photo IDs provided"
        )

    # Получаем все фото, принадлежащие текущему пользователю
    photos = db.query(Photo).join(Album).filter(
        Photo.id.in_(request.photo_ids),
        Album.user_id == current_user.id
    ).all()

    if not photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No photos found"
        )

    # Удаляем файлы из хранилища и записи из БД
    deleted_count = 0
    for photo in photos:
        try:
            storage_service.delete_file(photo.drive_file_id)
            if photo.thumbnail_file_id:
                storage_service.delete_file(photo.thumbnail_file_id)
        except Exception as e:
            print(f"Failed to delete photo file {photo.id}: {str(e)}")

        db.delete(photo)
        deleted_count += 1

    db.commit()
    print(f"Batch deleted {deleted_count} photos")

    return None
