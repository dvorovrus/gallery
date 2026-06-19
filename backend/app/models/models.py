from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.dt import utcnow

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # "user" or "admin"
    created_at = Column(DateTime, default=utcnow)

    albums = relationship("Album", back_populates="user", cascade="all, delete-orphan")

class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    is_public = Column(Boolean, default=False)
    password_hash = Column(String, nullable=True)
    expiration_type = Column(String, default="unlimited", nullable=False)
    expires_at = Column(DateTime, nullable=True)
    auto_delete_scheduled = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="albums")
    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan")
    shares = relationship("Share", back_populates="album", cascade="all, delete-orphan")

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    drive_file_id = Column(String, nullable=False)
    thumbnail_file_id = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    caption = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    album = relationship("Album", back_populates="photos")
    shares = relationship("Share", back_populates="photo", cascade="all, delete-orphan")

class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=True)
    token = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    album = relationship("Album", back_populates="shares")
    photo = relationship("Photo", back_populates="shares")

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
