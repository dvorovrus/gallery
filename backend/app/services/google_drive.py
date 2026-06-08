import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from app.core.config import get_settings
from typing import Optional
import io

settings = get_settings()

class GoogleDriveService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=credentials)
        self.root_folder_id = settings.GOOGLE_DRIVE_FOLDER_ID

    def create_user_folder(self, user_id: int) -> str:
        """Создать папку пользователя в корневой папке"""
        folder_name = f'user_{user_id}'
        query = f"name='{folder_name}' and '{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(
            q=query,
            fields='files(id, name)',
            supportsAllDrives=True
        ).execute()
        items = results.get('files', [])

        if items:
            return items[0]['id']

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.root_folder_id]
        }
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return folder.get('id')

    def create_album_folder(self, user_folder_id: str, album_id: int) -> str:
        """Создать папку альбома в папке пользователя"""
        folder_name = f'album_{album_id}'
        query = f"name='{folder_name}' and '{user_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(
            q=query,
            fields='files(id, name)',
            supportsAllDrives=True
        ).execute()
        items = results.get('files', [])

        if items:
            return items[0]['id']

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [user_folder_id]
        }
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return folder.get('id')

    def upload_file(self, file_path: str, filename: str, parent_folder_id: str) -> str:
        """Загрузить файл в папку альбома"""
        file_metadata = {
            'name': filename,
            'parents': [parent_folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return file.get('id')

    def get_file(self, file_id: str) -> bytes:
        """Получить файл из Google Drive"""
        request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_buffer.seek(0)
        return file_buffer.read()

    def delete_file(self, file_id: str):
        """Удалить файл из Google Drive"""
        self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()

    def delete_folder(self, folder_id: str):
        """Удалить папку из Google Drive"""
        self.service.files().delete(fileId=folder_id, supportsAllDrives=True).execute()

    def get_album_folder_id(self, user_folder_id: str, album_id: int) -> str:
        """Получить ID папки альбома"""
        folder_name = f'album_{album_id}'
        query = f"name='{folder_name}' and '{user_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)', supportsAllDrives=True).execute()
        items = results.get('files', [])
        return items[0]['id'] if items else None

drive_service = GoogleDriveService()
