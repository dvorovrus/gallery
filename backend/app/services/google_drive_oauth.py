import json
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport import requests as google_requests
from app.core.config import get_settings
import io

settings = get_settings()

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'oauth_credentials.json'

class GoogleDriveOAuthService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.root_folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self._load_credentials()

    def _load_credentials(self):
        """Загрузить сохраненные токены или запустить OAuth flow"""
        # Проверяем существующие токены
        if os.path.exists(TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # Если токены невалидны, обновляем или запускаем OAuth
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing access token...")
                self.creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"OAuth credentials file '{CREDENTIALS_FILE}' not found. "
                        "Please download it from Google Cloud Console."
                    )
                print("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                self.creds = flow.run_local_server(port=8090)

            # Сохраняем токены для последующего использования
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
            print("✅ Credentials saved to", TOKEN_FILE)

        # Используем requests вместо httplib2 для избежания SSL ошибок
        self.service = build('drive', 'v3', credentials=self.creds, cache_discovery=False)

    def create_user_folder(self, user_id: int) -> str:
        """Создать папку пользователя в корневой папке"""
        folder_name = f'user_{user_id}'

        # Проверяем, существует ли папка
        query = f"name='{folder_name}' and '{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        items = results.get('files', [])

        if items:
            return items[0]['id']

        # Создаем новую папку
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.root_folder_id]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def create_album_folder(self, user_folder_id: str, album_id: int) -> str:
        """Создать папку альбома в папке пользователя"""
        folder_name = f'album_{album_id}'

        # Проверяем, существует ли папка
        query = f"name='{folder_name}' and '{user_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        items = results.get('files', [])

        if items:
            return items[0]['id']

        # Создаем новую папку
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [user_folder_id]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
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
            fields='id'
        ).execute()
        return file.get('id')

    def get_file(self, file_id: str) -> bytes:
        """Получить файл из Google Drive с retry логикой"""
        import requests

        # Используем прямой HTTP запрос с токеном вместо mediaIoBaseDownload
        # Это избегает проблем с httplib2 SSL на Windows
        url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'

        # Обновляем токен если нужно
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())

        headers = {
            'Authorization': f'Bearer {self.creds.token}'
        }

        # Retry логика для SSL ошибок
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.content
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} for file {file_id}: {str(e)}")
                    continue
                raise

    def delete_file(self, file_id: str):
        """Удалить файл из Google Drive"""
        self.service.files().delete(fileId=file_id).execute()

    def delete_folder(self, folder_id: str):
        """Удалить папку из Google Drive"""
        self.service.files().delete(fileId=folder_id).execute()

    def get_album_folder_id(self, user_folder_id: str, album_id: int) -> str:
        """Получить ID папки альбома"""
        folder_name = f'album_{album_id}'
        query = f"name='{folder_name}' and '{user_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)').execute()
        items = results.get('files', [])
        return items[0]['id'] if items else None

drive_oauth_service = GoogleDriveOAuthService()
