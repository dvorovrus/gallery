import os
import shutil
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()

class LocalStorageService:
    def __init__(self):
        self.storage_root = Path("uploads")
        self.storage_root.mkdir(exist_ok=True)

    def create_user_folder(self, user_id: int) -> str:
        """Создать папку пользователя"""
        user_folder = self.storage_root / f"user_{user_id}"
        user_folder.mkdir(exist_ok=True)
        return str(user_folder)

    def create_album_folder(self, user_folder_path: str, album_id: int) -> str:
        """Создать папку альбома"""
        album_folder = Path(user_folder_path) / f"album_{album_id}"
        album_folder.mkdir(exist_ok=True)
        return str(album_folder)

    def upload_file(self, file_path: str, filename: str, parent_folder_path: str) -> str:
        """Сохранить файл в папку альбома"""
        dest_path = Path(parent_folder_path) / filename
        shutil.copy2(file_path, dest_path)
        return str(dest_path)

    def get_file(self, file_path: str) -> bytes:
        """Получить файл"""
        with open(file_path, 'rb') as f:
            return f.read()

    def delete_file(self, file_path: str):
        """Удалить файл"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    def delete_folder(self, folder_path: str):
        """Удалить папку"""
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    def get_album_folder_id(self, user_folder_path: str, album_id: int) -> str:
        """Получить путь к папке альбома"""
        album_folder = Path(user_folder_path) / f"album_{album_id}"
        return str(album_folder) if album_folder.exists() else None

storage_service = LocalStorageService()
