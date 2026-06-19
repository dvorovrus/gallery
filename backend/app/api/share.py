from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import secrets
import io
import zipfile
import os
import mimetypes
import re
import logging
from urllib.parse import quote
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_media_token, decode_media_token
from app.api.auth import get_current_user
from app.models.models import User, Album, Share, Photo
from app.schemas.schemas import ShareCreate, ShareResponse, AlbumResponse, PhotoResponse
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Select storage based on settings
if settings.STORAGE_TYPE == "google_drive":
    from app.services.google_drive import drive_service as storage_service
elif settings.STORAGE_TYPE == "google_drive_oauth":
    from app.services.google_drive_oauth import drive_oauth_service as storage_service
else:
    from app.services.local_storage import storage_service

router = APIRouter(tags=["share"])

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

@router.post("/albums/{album_id}/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_album_share_link(
    album_id: int,
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    # Generate unique token
    token = secrets.token_urlsafe(16)

    # Hash password if provided
    password_hash = None
    if share_data.password:
        password_hash = get_password_hash(share_data.password)

    new_share = Share(
        album_id=album_id,
        photo_id=None,
        token=token,
        password_hash=password_hash
    )

    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return ShareResponse(
        id=new_share.id,
        album_id=new_share.album_id,
        token=new_share.token,
        password_required=password_hash is not None,
        expires_at=new_share.expires_at,
        created_at=new_share.created_at
    )

@router.post("/photos/{photo_id}/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_photo_share_link(
    photo_id: int,
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get photo and verify ownership through album
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    album = db.query(Album).filter(Album.id == photo.album_id, Album.user_id == current_user.id).first()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Generate unique token
    token = secrets.token_urlsafe(16)

    # Hash password if provided
    password_hash = None
    if share_data.password:
        password_hash = get_password_hash(share_data.password)

    new_share = Share(
        album_id=None,
        photo_id=photo_id,
        token=token,
        password_hash=password_hash
    )

    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return ShareResponse(
        id=new_share.id,
        album_id=None,
        token=new_share.token,
        password_required=password_hash is not None,
        expires_at=new_share.expires_at,
        created_at=new_share.created_at
    )

class ShareAccessRequest(BaseModel):
    password: Optional[str] = None


def _resolve_share(db: Session, token: str) -> Share:
    share = db.query(Share).filter(Share.token == token).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")
    return share


def _verify_share_password(share: Share, password: Optional[str]) -> None:
    """Если share запаролен — проверить пароль, иначе поднять 401."""
    if share.password_hash:
        if not password or not verify_password(password, share.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )


def _share_media_token_ok(share: Share, token: Optional[str]) -> bool:
    """
    Проверить, что подписанный media-token (scope=share) соответствует данной share-ссылке.
    Пароль уже был проверен при выдаче токена (см. access-эндпоинт), поэтому здесь
    сверяется только принадлежность токена к этой share.
    """
    if not token:
        return False
    payload = decode_media_token(token)
    if not payload or payload.get("scope") != "share":
        return False
    try:
        return int(payload.get("ref")) == share.id
    except (TypeError, ValueError):
        return False


def _build_share_payload(db: Session, share: Share, with_content: bool) -> dict:
    """
    Сформировать ответ share-ссылки. Если with_content=False (запароленный шар
    до ввода пароля) — отдаются только метаданные и флаг passwordRequired,
    контент и mediaToken отсутствуют.
    """
    media_token = create_media_token(scope="share", ref_id=share.id) if with_content else None
    is_password = share.password_hash is not None

    def photo_url(photo: Photo, thumbnail: bool) -> str:
        base = f"/api/photos/{photo.id}" + ("?thumbnail=true&width=400" if thumbnail else "")
        return f"{base}&token={media_token}" if media_token else base

    # Handle album share
    if share.album_id:
        album = db.query(Album).filter(Album.id == share.album_id).first()
        photo_responses: List[dict] = []
        if with_content:
            for photo in db.query(Photo).filter(Photo.album_id == share.album_id).all():
                photo_responses.append({
                    "id": photo.id,
                    "caption": photo.caption,
                    "created_at": photo.created_at,
                    "fullUrl": photo_url(photo, False),
                    "thumbnailUrl": photo_url(photo, True),
                })

        return {
            "version": 1,
            "token": share.token,
            "mediaToken": media_token,
            "type": "album",
            "title": album.title if album else "Album",
            "accessType": "password" if is_password else "public",
            "album": {
                "id": album.id,
                "title": album.title,
                "created_at": album.created_at,
            } if album else None,
            "photo": None,
            "photos": photo_responses,
            "passwordRequired": is_password,
            "expirationType": album.expiration_type if album else "unlimited",
            "expiresAt": album.expires_at if album else None,
        }

    # Handle photo share
    if share.photo_id:
        photo = db.query(Photo).filter(Photo.id == share.photo_id).first()
        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        album = db.query(Album).filter(Album.id == photo.album_id).first()

        photo_data = None
        if with_content:
            photo_data = {
                "id": photo.id,
                "caption": photo.caption,
                "created_at": photo.created_at,
                "fullUrl": photo_url(photo, False),
                "thumbnailUrl": photo_url(photo, True),
            }

        return {
            "version": 1,
            "token": share.token,
            "mediaToken": media_token,
            "type": "photo",
            "title": photo.caption or "Фото",
            "accessType": "password" if is_password else "public",
            "album": {
                "id": album.id,
                "title": album.title,
                "created_at": album.created_at,
            } if album else None,
            "photo": photo_data,
            "photos": [photo_data] if photo_data else [],
            "passwordRequired": is_password,
            "expirationType": "unlimited",
            "expiresAt": None,
        }

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid share configuration")


@router.get("/share/{token}")
def get_shared_content(token: str, db: Session = Depends(get_db)):
    """
    Метаданные share-ссылки. Для публичной ссылки сразу возвращается контент и
    mediaToken; для запароленной — только флаг passwordRequired (контент скрыт).
    Пароль передаётся отдельным POST-запросом, чтобы не утекал в URL/логах.
    """
    share = _resolve_share(db, token)
    with_content = share.password_hash is None
    return _build_share_payload(db, share, with_content)


@router.post("/share/{token}/access")
def access_shared_content(
    token: str,
    body: ShareAccessRequest,
    db: Session = Depends(get_db),
):
    """
    Разблокировать контент share-ссылки. Пароль передаётся в теле JSON,
    а не в query. При успехе возвращает полный контент и короткоживущий
    mediaToken для бинарного доступа (просмотр/скачивание фото).
    """
    share = _resolve_share(db, token)
    _verify_share_password(share, body.password)
    return _build_share_payload(db, share, with_content=True)

@router.get("/share/{token}/download/photo/{photo_id}")
def download_shared_photo(
    token: str,
    photo_id: int,
    access: Optional[str] = Query(None, description="Share media access token"),
    db: Session = Depends(get_db),
):
    share = _resolve_share(db, token)

    # Доступ к бинарнику авторизуется подписанным media-token, полученным после
    # ввода пароля (POST /api/share/{token}/access). Пароль больше не летит в URL.
    if not _share_media_token_ok(share, access):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid access token required",
            headers={"WWW-Authenticate": 'Bearer realm="share"'},
        )

    # Verify photo belongs to shared content
    if share.album_id:
        photo = db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.album_id == share.album_id
        ).first()
    elif share.photo_id:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo and photo.id != share.photo_id:
            photo = None
    else:
        photo = None

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
        # Самоисцеление: файл пропал на хранилище — убираем фото из БД
        msg = str(e)
        if any(s in msg for s in ("404", "File not found", "fileId")):
            try:
                logger.info("[self-heal] shared photo %s file gone, removing DB row", photo.id)
                db.query(Share).filter(Share.photo_id == photo.id).delete(synchronize_session=False)
                db.delete(photo)
                db.commit()
            except Exception as purge_err:
                logger.error("[self-heal] failed to purge shared photo %s: %s", photo.id, purge_err)
                db.rollback()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Photo no longer exists in storage"
            )
        logger.exception("Failed to download shared photo %s", photo_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download photo"
        )

@router.get("/share/{token}/download/album")
def download_shared_album(
    token: str,
    access: Optional[str] = Query(None, description="Share media access token"),
    db: Session = Depends(get_db),
):
    share = _resolve_share(db, token)

    if not _share_media_token_ok(share, access):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid access token required",
            headers={"WWW-Authenticate": 'Bearer realm="share"'},
        )

    # Only album shares can be downloaded as zip
    if not share.album_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This share is not an album"
        )

    album = db.query(Album).filter(Album.id == share.album_id).first()
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )

    photos = db.query(Photo).filter(Photo.album_id == share.album_id).all()
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
        logger.exception("Failed to download shared album %s", share.album_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download album"
        )
