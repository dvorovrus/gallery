from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str = "user"
    created_at: datetime

    class Config:
        from_attributes = True

# Album Schemas
class AlbumBase(BaseModel):
    title: str

class AlbumCreate(AlbumBase):
    expiration_type: str = "unlimited"  # unlimited, 7_days, 14_days, 30_days

class AlbumResponse(AlbumBase):
    id: int
    user_id: int
    created_at: datetime
    is_public: bool
    expiration_type: str
    expires_at: Optional[datetime] = None
    auto_delete_scheduled: bool

    class Config:
        from_attributes = True

# Photo Schemas
class PhotoBase(BaseModel):
    caption: Optional[str] = None

class PhotoCreate(PhotoBase):
    filename: str
    drive_file_id: str

class PhotoResponse(PhotoBase):
    id: int
    album_id: int
    drive_file_id: str
    thumbnail_file_id: Optional[str] = None
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True

# Share Schemas
class ShareCreate(BaseModel):
    password: Optional[str] = None

class ShareResponse(BaseModel):
    id: int
    album_id: Optional[int] = None
    token: str
    password_required: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
