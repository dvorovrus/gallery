import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from app.core.config import get_settings
from typing import Optional
import io
import os

settings = get_settings()

def get_credentials_from_db():
    """Получить credentials из БД или из файла"""
    try:
        from app.core.database import SessionLocal
        from app.models.models import Settings as SettingsModel
        
        db = SessionLocal()
        try:
            credentials_setting = db.query(SettingsModel).filter(
                SettingsModel.key == "google_service_account_json"
            ).first()
            
            if credentials_setting and credentials_setting.value:
                credentials_data = json.loads(credentials_setting.value)
                return service_account.Credentials.from_service_account_info(
                    credentials_data,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
        finally:
            db.close()
    except Exception as e:
        print(f"Could not load credentials from DB: {e}")
    
    # Fallback to file-based credentials
    if settings.GOOGLE_CREDENTIALS_PATH and os.path.exists(settings.GOOGLE_CREDENTIALS_PATH):
        return service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=['https://www.googleapis.com/auth/drive']
        )
    
    raise Exception("Google Drive credentials not configured")

def get_folder_id_from_db():
    """Получить folder ID из БД или из настроек"""
    try:
        from app.core.database import SessionLocal
        from app.models.models import Settings as SettingsModel
        
        db = SessionLocal()
        try:
            folder_setting = db.query(SettingsModel).filter(
                SettingsModel.key == "google_drive_folder_id"
            ).first()
            
            if folder_setting and folder_setting.value:
                return folder_setting.value
        finally:
            db.close()
    except Exception as e:
        print(f"Could not load folder_id from DB: {e}")
    
    # Fallback to settings
    if settings.GOOGLE_DRIVE_FOLDER_ID:
        return settings.GOOGLE_DRIVE_FOLDER_ID
    
    raise Exception("Google Drive folder ID not configured")

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.root_folder_id = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Google Drive service"""
        if self._initialized:
            return
        
        try:
            self.credentials = get_credentials_from_db()
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.root_folder_id = get_folder_id_from_db()
            self._initialized = True
        except Exception as e:
            print(f"Failed to initialize Google Drive service: {str(e)}")
            raise Exception(
                "Google Drive is not configured. Please go to Settings page and configure Google Drive credentials."
            ) from e

    def create_user_folder(self, user_id: int) -> str:
        """Создать папку пользователя в корневой папке"""
        self._ensure_initialized()
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
        self._ensure_initialized()
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
        self._ensure_initialized()
        try:
            print(f"Preparing to upload file: {filename} to folder: {parent_folder_id}")
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            print(f"Starting upload to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            file_id = file.get('id')
            print(f"File uploaded successfully, file_id: {file_id}")
            return file_id
        except Exception as e:
            print(f"Error uploading file to Google Drive: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def get_file(self, file_id: str) -> bytes:
        """Получить файл из Google Drive"""
        self._ensure_initialized()
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
        self._ensure_initialized()
        self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()

    def delete_folder(self, folder_id: str):
        """Удалить папку из Google Drive"""
        self._ensure_initialized()
        self.service.files().delete(fileId=folder_id, supportsAllDrives=True).execute()

    def get_album_folder_id(self, user_folder_id: str, album_id: int) -> str:
        """Получить ID папки альбома"""
        self._ensure_initialized()
        folder_name = f'album_{album_id}'
        query = f"name='{folder_name}' and '{user_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)', supportsAllDrives=True).execute()
        items = results.get('files', [])
        return items[0]['id'] if items else None

drive_service = GoogleDriveService()
