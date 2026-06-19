import json
import logging
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from app.core.config import get_settings
from typing import Optional
import io
import os

logger = logging.getLogger(__name__)
settings = get_settings()
SCOPES = ['https://www.googleapis.com/auth/drive']


def get_setting_value(key: str) -> Optional[str]:
    try:
        from app.core.database import SessionLocal
        from app.models.models import Settings as SettingsModel

        db = SessionLocal()
        try:
            setting = db.query(SettingsModel).filter(SettingsModel.key == key).first()
            return setting.value if setting and setting.value else None
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not load setting %s from DB: %s", key, e)
        return None


def set_setting_value(key: str, value: str):
    from app.core.database import SessionLocal
    from app.models.models import Settings as SettingsModel

    db = SessionLocal()
    try:
        setting = db.query(SettingsModel).filter(SettingsModel.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(SettingsModel(key=key, value=value))
        db.commit()
    finally:
        db.close()

def get_credentials_from_db():
    """Получить credentials из БД или из файла"""
    auth_type = get_setting_value("google_drive_auth_type")
    oauth_token = get_setting_value("google_oauth_token_json")

    if auth_type == "oauth" and oauth_token:
        token_data = json.loads(oauth_token)
        credentials = Credentials.from_authorized_user_info(token_data, scopes=SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            set_setting_value("google_oauth_token_json", credentials.to_json())
        return credentials

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
                    scopes=SCOPES
                )
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not load credentials from DB: %s", e)
    
    # Fallback to file-based credentials
    if settings.GOOGLE_CREDENTIALS_PATH and os.path.exists(settings.GOOGLE_CREDENTIALS_PATH):
        return service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=SCOPES
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
        logger.warning("Could not load folder_id from DB: %s", e)
    
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
        self._auth_type = None
    
    def _ensure_initialized(self):
        """Lazy initialization of Google Drive service"""
        try:
            auth_type = get_setting_value("google_drive_auth_type") or "service_account"
            root_folder_id = get_folder_id_from_db()
            if self._initialized and self._auth_type == auth_type and self.root_folder_id == root_folder_id:
                return

            self.credentials = get_credentials_from_db()
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.root_folder_id = root_folder_id
            self._auth_type = auth_type
            self._initialized = True
        except Exception as e:
            logger.error("Failed to initialize Google Drive service: %s", e)
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
            logger.debug("Preparing to upload file: %s to folder: %s", filename, parent_folder_id)
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            logger.debug("Starting upload to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            file_id = file.get('id')
            logger.debug("File uploaded successfully, file_id: %s", file_id)
            return file_id
        except Exception as e:
            logger.error("Error uploading file to Google Drive: %s", e)
            if "storageQuotaExceeded" in str(e) or "Service Accounts do not have storage quota" in str(e):
                raise Exception(
                    "Google Drive folder must be inside a Shared Drive. Service Accounts cannot upload files to a regular My Drive folder because they have no storage quota."
                ) from e
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

    def file_exists(self, file_id: str) -> bool:
        """Проверить существование файла (не в корзине) на Drive"""
        self._ensure_initialized()
        try:
            meta = self.service.files().get(
                fileId=file_id,
                fields='id,trashed',
                supportsAllDrives=True
            ).execute()
            return not meta.get('trashed', False)
        except Exception as e:
            msg = str(e)
            # 404 / not found → файл удалён
            if '404' in msg or 'File not found' in msg or 'fileId' in msg:
                return False
            raise

    def list_descendants(self, folder_id: str) -> set:
        """
        Рекурсивно собрать множество ID всех файлов/папок внутри folder_id.
        Используется для первичной полной сверки (один обход вместо N проверок).
        """
        self._ensure_initialized()
        all_ids = set()
        page_token = None
        while True:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='nextPageToken, files(id, name, mimeType)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
                pageSize=1000
            ).execute()
            for item in results.get('files', []):
                all_ids.add(item['id'])
                # Рекурсивно внутрь подпапок
                if item.get('mimeType') == 'application/vnd.google-apps.folder':
                    all_ids.update(self.list_descendants(item['id']))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return all_ids

    def get_start_page_token(self) -> str:
        """Текущий токен состояния Drive (точка отсчёта для инкрементальной сверки)"""
        self._ensure_initialized()
        resp = self.service.changes().getStartPageToken(supportsAllDrives=True).execute()
        return resp.get('startPageToken')

    def list_changes(self, page_token: str) -> dict:
        """
        Получить изменения с момента page_token.
        Возвращает {
            'changes': [{'fileId': str, 'removed': bool, 'trashed': bool, 'is_folder': bool}],
            'new_start_page_token': str | None,  # присутствует на последней странице
            'next_page_token': str | None         # присутствует, если есть ещё страницы
        }
        """
        self._ensure_initialized()
        resp = self.service.changes().list(
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            fields='nextPageToken,newStartPageToken,changes(fileId,removed,file(id,mimeType,trashed))'
        ).execute()

        changes = []
        for ch in resp.get('changes', []):
            f = ch.get('file') or {}
            changes.append({
                'fileId': ch.get('fileId'),
                'removed': bool(ch.get('removed', False)),
                'trashed': bool(f.get('trashed', False)),
                'is_folder': f.get('mimeType') == 'application/vnd.google-apps.folder',
            })

        return {
            'changes': changes,
            'new_start_page_token': resp.get('newStartPageToken'),
            'next_page_token': resp.get('nextPageToken'),
        }

drive_service = GoogleDriveService()
