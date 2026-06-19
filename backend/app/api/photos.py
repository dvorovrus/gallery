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
import logging
from urllib.parse import quote
from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_media_token, decode_media_token
from app.api.auth import get_current_user
from app.models.models import User, Album, Photo, Share
from app.schemas.schemas import PhotoResponse
from app.services.photo_thumbnails import generate_thumbnail_bytes

logger = logging.getLogger(__name__)
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


# Whitest расширений и content-type для загрузки изображений.
ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".heic"}
ALLOWED_PHOTO_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/bmp", "image/tiff", "image/heic", "image/heif",
    "application/octet-stream",  # браузеры иногда так шлют; опираемся на сигнатуру
}
# Magic-байты для второй линии защиты (не полагаемся только на имя/content-type).
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
    (b"II*\x00", "tiff"),
    (b"MM\x00*", "tiff"),
)


def _looks_like_image(content: bytes) -> bool:
    head = content[:16]
    if any(head.startswith(sig) for sig, _ in _IMAGE_SIGNATURES):
        return True
    # WEBP: "RIFF"...."WEBP"
    if len(content) >= 12 and head[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return True
    # HEIC/HEIF: ftyp box с брендом heic/heix/mif1
    if len(content) >= 12 and content[4:8] == b"ftyp" and content[8:12] in (b"heic", b"heix", b"mif1", b"heif"):
        return True
    return False


def _validate_upload_metadata(file: UploadFile) -> None:
    """Проверить расширение и заявленный content-type ещё до чтения тела файла."""
    filename = (file.filename or "").lower()
    ext = os.path.splitext(filename)[1]
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext or '(none)'}'. Allowed: {', '.join(sorted(ALLOWED_PHOTO_EXTENSIONS))}",
        )
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type '{content_type}'.",
        )


async def _stream_to_temp(file: UploadFile, dest_path: str, max_bytes: int) -> int:
    """
    Стримить UploadFile в файл на диске чанками, считая размер.
    Если размер превышает max_bytes — удаляет файл и бросает 413.
    Возвращает фактический размер в байтах.
    """
    written = 0
    chunk_size = 1024 * 1024  # 1 MiB
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    out.close()
                    os.unlink(dest_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File '{file.filename}' exceeds the maximum allowed size "
                        f"({max_bytes // (1024 * 1024)} MiB).",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        if os.path.exists(dest_path):
            try:
                os.unlink(dest_path)
            except OSError:
                pass
        raise
    return written


def build_thumbnail_file_name(photo_id: int) -> str:
    return f"photo_{photo_id}_thumbnail.jpg"


def build_thumbnail_bytes(file_content: bytes, width: int) -> bytes:
    return generate_thumbnail_bytes(file_content, width)


def store_thumbnail_file(original_content: bytes, photo_id: int, album_folder_id: str) -> str:
    try:
        logger.debug("Generating thumbnail bytes for photo %s", photo_id)
        thumbnail_bytes = build_thumbnail_bytes(original_content, 400)
        logger.debug("Thumbnail bytes generated, size: %s bytes", len(thumbnail_bytes))
    except Exception as e:
        logger.error("Error generating thumbnail bytes: %s", e)
        raise

    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_thumb_{photo_id}.jpg") as temp_file:
        temp_file.write(thumbnail_bytes)
        temp_path = temp_file.name

    try:
        logger.debug("Uploading thumbnail: %s", build_thumbnail_file_name(photo_id))
        thumbnail_file_id = storage_service.upload_file(temp_path, build_thumbnail_file_name(photo_id), album_folder_id)
        logger.debug("Thumbnail uploaded, file_id: %s", thumbnail_file_id)
        return thumbnail_file_id
    except Exception as e:
        logger.error("Error uploading thumbnail: %s", e)
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
        logger.info("[self-heal] photo %s file gone, removing DB row", photo.id)
        db.query(Share).filter(Share.photo_id == photo.id).delete(synchronize_session=False)
        db.delete(photo)
        db.commit()
        return True
    except Exception as purge_err:
        logger.error("[self-heal] failed to purge photo %s: %s", photo.id, purge_err)
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
        # Валидация имени/content-type до чтения тела
        _validate_upload_metadata(file)

        # Save file temporarily (streaming с лимитом размера, без загрузки всего файла в память запроса)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        temp_path = temp_file.name
        temp_file.close()

        try:
            size = await _stream_to_temp(file, temp_path, settings.MAX_PHOTO_UPLOAD_BYTES)

            # Вторая линия защиты: проверка magic-байтов (не доверяем только имени/content-type)
            with open(temp_path, "rb") as probe:
                head = probe.read(32)
            if not _looks_like_image(head):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"File '{file.filename}' is not a recognized image.",
                )

            # Upload to storage
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            logger.info("Uploading to storage: %s (size=%s)", unique_filename, size)
            drive_file_id = storage_service.upload_file(temp_path, unique_filename, album_folder_id)

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

            try:
                # Генерируем миниатюру из сохранённого временного файла.
                with open(temp_path, "rb") as src:
                    content = src.read()
                thumbnail_file_id = store_thumbnail_file(content, new_photo.id, album_folder_id)
                new_photo.thumbnail_file_id = thumbnail_file_id
            except Exception as thumbnail_error:
                logger.warning("Could not create thumbnail for %s: %s", file.filename, thumbnail_error)

            uploaded_photos.append(new_photo)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error uploading file %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file {file.filename}."
            )
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError as e:
                logger.warning("Could not delete temp file %s: %s", temp_path, e)

    db.commit()
    for photo in uploaded_photos:
        db.refresh(photo)

    return uploaded_photos

def _photo_accessible_via_token(db: Session, photo: Photo, token: Optional[str]) -> bool:
    """
    Проверить, что подписанный media-token даёт право на чтение фото.

    Поддерживаются два scope:
      * "album" — token выдавался владельцу альбома; фото должно принадлежать этому альбому;
      * "share" — token привязан к Share-ссылке; фото должно входить в её контент.
    Пароль share уже проверяется при выдаче токена (см. app.api.share), поэтому
    здесь достаточно сверить принадлежность.
    """
    if not token:
        return False
    payload = decode_media_token(token)
    if not payload:
        return False

    scope = payload.get("scope")
    ref = payload.get("ref")
    if ref is None:
        return False

    if scope == "album":
        try:
            return photo.album_id == int(ref)
        except (TypeError, ValueError):
            return False

    if scope == "share":
        share = db.query(Share).filter(Share.id == ref).first()
        if not share:
            return False
        if share.album_id is not None:
            return photo.album_id == share.album_id
        if share.photo_id is not None:
            return photo.id == share.photo_id
        return False

    return False


@router.get("/albums/{album_id}/media-token")
def get_album_media_token(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Выдать подписанный короткоживущий media-token для бинарного доступа к фото
    альбома. Используется фронтом, чтобы рендерить ``<img src="/api/photos/{id}?token=...">``
    без передачи JWT в URL. Токен выдаётся только владельцу альбома.
    """
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    token = create_media_token(scope="album", ref_id=album.id)
    return {"token": token, "album_id": album.id}


@router.get("/photos/{photo_id}")
def get_photo(
    photo_id: int,
    token: Optional[str] = Query(None, description="Signed media access token"),
    thumbnail: bool = Query(False, description="Return thumbnail instead of full image"),
    width: int = Query(400, description="Thumbnail width", ge=50, le=1000),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    # Авторизация: доступ к байнам фото только по валидному media-token.
    # Это закрывает IDOR — перебор последовательных ID без токена невозможен.
    if not _photo_accessible_via_token(db, photo, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid media token required",
            headers={"WWW-Authenticate": 'Bearer realm="media"'},
        )

    # Get file from storage
    try:
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
                    logger.warning("Could not persist thumbnail for photo %s: %s", photo_id, store_error)

            return StreamingResponse(
                io.BytesIO(thumbnail_bytes),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400, immutable"},
            )

        file_content = storage_service.get_file(photo.drive_file_id)
        # Определяем реальный MIME-тип по имени файла, а не хардкодим image/jpeg.
        media_type = mimetypes.guess_type(photo.filename or "")[0] or "application/octet-stream"
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=86400, immutable"},
        )
    except Exception as e:
        logger.exception("Error retrieving photo %s", photo_id)
        if _purge_photo_if_gone(db, photo, e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo no longer exists in storage and was removed"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve photo"
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
        logger.exception("Failed to download photo %s", photo_id)
        if _purge_photo_if_gone(db, photo, e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo no longer exists in storage and was removed"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download photo"
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
    except Exception:
        logger.exception("Failed to download album %s", album_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download album"
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
    except Exception as e:
        logger.warning("Failed to delete photo file %s from storage: %s", photo_id, e)

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
            logger.warning("Failed to delete photo file %s: %s", photo.id, e)

        db.delete(photo)
        deleted_count += 1

    db.commit()
    logger.info("Batch deleted %s photos", deleted_count)

    return None
