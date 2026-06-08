"""Initialize database with test data"""
from app.core.database import SessionLocal, engine, Base
from app.models.models import User, Album, Photo
from app.core.security import get_password_hash
from datetime import datetime

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if test user exists
    test_user = db.query(User).filter(User.email == "test@example.com").first()

    if not test_user:
        # Create test user
        test_user = User(
            email="test@example.com",
            password_hash=get_password_hash("test")
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created test user: test@example.com / test")
    else:
        print(f"Test user already exists: test@example.com")

    # Check if albums exist
    existing_albums = db.query(Album).filter(Album.user_id == test_user.id).all()

    if not existing_albums:
        # Create test albums
        albums_data = [
            {"title": "Пейзажи", "is_public": False},
            {"title": "Улицы", "is_public": False},
            {"title": "Студия", "is_public": False},
        ]

        albums = []
        for album_data in albums_data:
            album = Album(
                user_id=test_user.id,
                title=album_data["title"],
                is_public=album_data["is_public"]
            )
            db.add(album)
            albums.append(album)

        db.commit()
        for album in albums:
            db.refresh(album)

        print(f"Created {len(albums)} test albums")

        # Create test photos
        photos_data = [
            {"album_idx": 0, "drive_file_id": "fake_id_1", "filename": "mountains.jpg", "caption": "Летние горы"},
            {"album_idx": 0, "drive_file_id": "fake_id_2", "filename": "valley.jpg", "caption": "Утренняя долина"},
            {"album_idx": 0, "drive_file_id": "fake_id_3", "filename": "peak.jpg", "caption": "Туманный пик"},
            {"album_idx": 1, "drive_file_id": "fake_id_4", "filename": "lights.jpg", "caption": "Вечерние огни"},
            {"album_idx": 1, "drive_file_id": "fake_id_5", "filename": "architecture.jpg", "caption": "Архитектура"},
            {"album_idx": 2, "drive_file_id": "fake_id_6", "filename": "portrait.jpg", "caption": "Портрет"},
        ]

        photos = []
        for photo_data in photos_data:
            photo = Photo(
                album_id=albums[photo_data["album_idx"]].id,
                drive_file_id=photo_data["drive_file_id"],
                filename=photo_data["filename"],
                caption=photo_data["caption"]
            )
            db.add(photo)
            photos.append(photo)

        db.commit()
        print(f"Created {len(photos)} test photos")
    else:
        print(f"Test data already exists ({len(existing_albums)} albums)")

    print("\n=== Test Credentials ===")
    print("Email: test@example.com")
    print("Password: test")
    print("========================\n")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
