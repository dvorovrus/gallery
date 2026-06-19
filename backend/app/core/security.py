from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

# Use argon2 instead of bcrypt to avoid compatibility issues
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

MEDIA_TOKEN_TYPE = "media"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except PyJWTError:
        return None


def create_media_token(scope: str, ref_id: int, expires_minutes: Optional[int] = None) -> str:
    """
    Подписанный короткоживущий токен, авторизующий доступ к бинарю фото/миниатюры.

    :param scope: "album" — доступ ко всем фото альбома ``ref_id``;
                  "share" — доступ к контенту share-ссылки ``ref_id`` (id строки Share).
    :param ref_id: идентификатор scope-объекта.
    """
    minutes = expires_minutes if expires_minutes is not None else settings.MEDIA_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"type": MEDIA_TOKEN_TYPE, "scope": scope, "ref": ref_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_media_token(token: str) -> Optional[dict]:
    """Декодировать media-токен. Возвращает payload или None."""
    payload = decode_access_token(token)
    if not payload or payload.get("type") != MEDIA_TOKEN_TYPE:
        return None
    return payload

