from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import secrets
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.api.auth import get_current_user
from app.models.models import User, Album, Share, Photo
from app.schemas.schemas import ShareCreate, ShareResponse, AlbumResponse, PhotoResponse
from typing import List

router = APIRouter(tags=["share"])

@router.post("/albums/{album_id}/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_share_link(
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

@router.get("/share/{token}")
def get_shared_album(
    token: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter(Share.token == token).first()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found"
        )

    # Check password if required
    if share.password_hash:
        if not password or not verify_password(password, share.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

    # Get album and photos
    album = db.query(Album).filter(Album.id == share.album_id).first()
    photos = db.query(Photo).filter(Photo.album_id == share.album_id).all()

    return {
        "album": album,
        "photos": photos
    }
