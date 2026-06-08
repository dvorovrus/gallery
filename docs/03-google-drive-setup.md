# Настройка Google Drive Integration

## Обзор

Приложение Gallery использует Google Drive в качестве хранилища для фотографий через **Service Account** (не OAuth2). Это означает, что пользователи приложения не авторизуются в своих Google аккаунтах - вместо этого приложение использует специальный сервисный аккаунт с доступом к выделенной папке на Drive.

## Шаг 1: Создание Google Cloud Project

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)

2. Создайте новый проект:
   - Нажмите на выпадающий список проектов сверху
   - Нажмите "New Project"
   - Название: `gallery-storage` (или любое другое)
   - Нажмите "Create"

3. Выберите созданный проект

## Шаг 2: Включение Google Drive API

1. В боковом меню перейдите: **APIs & Services** → **Library**

2. Найдите "Google Drive API"

3. Нажмите "Enable"

## Шаг 3: Создание Service Account

1. Перейдите: **APIs & Services** → **Credentials**

2. Нажмите **"Create Credentials"** → **"Service Account"**

3. Заполните форму:
   - **Service account name:** `gallery-service`
   - **Service account ID:** `gallery-service` (автоматически)
   - **Description:** "Service account for Gallery photo storage"
   - Нажмите **"Create and Continue"**

4. Grant permissions (опционально для этого шага):
   - Можно пропустить, нажав **"Continue"**

5. Нажмите **"Done"**

## Шаг 4: Создание JSON ключа

1. В списке Service Accounts найдите созданный `gallery-service`

2. Нажмите на email аккаунта (например: `gallery-service@project.iam.gserviceaccount.com`)

3. Перейдите на вкладку **"Keys"**

4. Нажмите **"Add Key"** → **"Create new key"**

5. Выберите тип: **JSON**

6. Нажмите **"Create"**

7. **Файл автоматически скачается** на ваш компьютер с именем вроде:
   ```
   project-name-xxxxx-yyy.json
   ```

8. **Переименуйте файл** в `service-account.json`

9. **Переместите файл** в папку backend проекта:
   ```
   gallery/backend/service-account.json
   ```

**⚠️ ВАЖНО:** Этот файл содержит приватный ключ. **НЕ коммитьте его в Git!** (уже добавлен в `.gitignore`)

## Шаг 5: Создание корневой папки на Google Drive

1. Откройте [Google Drive](https://drive.google.com) в браузере

2. Создайте новую папку:
   - Нажмите **"New"** → **"Folder"**
   - Название: `PhotoGalleryStorage`

3. **Скопируйте ID папки:**
   - Откройте созданную папку
   - Посмотрите на URL в адресной строке:
     ```
     https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                            ^^^^^^^^^^^^^^^^^^^^
                                            Это ID папки
     ```
   - Скопируйте ID (например: `1a2b3c4d5e6f7g8h9i0j`)

## Шаг 6: Расшаривание папки на Service Account

1. **Правый клик** на папку `PhotoGalleryStorage`

2. Выберите **"Share"** (Поделиться)

3. В поле **"Add people, groups, and calendar events"** вставьте email Service Account:
   ```
   gallery-service@project-name-xxxxx.iam.gserviceaccount.com
   ```
   (Этот email можно найти в скачанном JSON файле в поле `client_email`)

4. Установите права: **"Editor"** (Редактор)

5. **Снимите галочку** "Notify people" (не нужно отправлять уведомления)

6. Нажмите **"Share"**

## Шаг 7: Настройка Backend

1. Откройте файл `backend/.env` (или создайте из `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/gallery

# JWT
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Google Drive Configuration
GOOGLE_CREDENTIALS_PATH=./service-account.json
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

2. Замените `GOOGLE_DRIVE_FOLDER_ID` на ID вашей папки из Шага 5

3. Убедитесь, что `GOOGLE_CREDENTIALS_PATH` указывает на правильный путь к JSON файлу

## Шаг 8: Проверка настройки

### Тест 1: Проверка credentials

Создайте тестовый скрипт `backend/test_drive.py`:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = './service-account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# List files in root folder
results = service.files().list(
    q="'ROOT_FOLDER_ID' in parents",
    pageSize=10,
    fields="files(id, name)"
).execute()

items = results.get('files', [])

if not items:
    print('✅ Service Account работает! (Папка пустая)')
else:
    print('✅ Service Account работает! Найдены файлы:')
    for item in items:
        print(f"  - {item['name']} ({item['id']})")
```

Замените `ROOT_FOLDER_ID` на ваш ID папки и запустите:

```bash
cd backend
python test_drive.py
```

### Тест 2: Загрузка тестового файла

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = './service-account.json'
ROOT_FOLDER_ID = '1a2b3c4d5e6f7g8h9i0j'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# Create test file
with open('test.txt', 'w') as f:
    f.write('Hello from Gallery!')

# Upload
file_metadata = {
    'name': 'test.txt',
    'parents': [ROOT_FOLDER_ID]
}
media = MediaFileUpload('test.txt', resumable=True)
file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

print(f"✅ Файл загружен! ID: {file.get('id')}")
```

### Тест 3: Запуск backend

```bash
cd backend
uvicorn main:app --reload
```

Откройте http://localhost:8000/docs и проверьте, что API доступен.

## Структура хранилища на Drive

После запуска приложение создаст следующую структуру:

```
PhotoGalleryStorage/
├── user_1/
│   ├── album_1/
│   │   ├── uuid_photo1.jpg
│   │   └── uuid_photo2.jpg
│   └── album_2/
│       └── uuid_photo3.jpg
├── user_2/
│   └── album_5/
│       └── uuid_photo4.jpg
└── user_3/
    ├── album_10/
    └── album_11/
```

**Папки создаются автоматически** при загрузке первого фото в альбом.

## Квоты Google Drive API

### Free Tier (бесплатно):

- **Storage:** 15 GB на Google аккаунт
- **API Queries:** 1,000,000,000 queries/day
- **Upload:** 750 GB/day
- **Download:** Нет лимита

### Оптимизация использования:

1. **Сжатие изображений** перед загрузкой:
   ```python
   from PIL import Image
   
   img = Image.open('photo.jpg')
   img.thumbnail((1920, 1920))  # Max 1920px
   img.save('compressed.jpg', quality=85, optimize=True)
   ```

2. **Кэширование** для уменьшения запросов к API (см. документацию по архитектуре)

3. **Batch requests** для множественных операций

## Безопасность

### ✅ Правильно:

- Service Account JSON хранится **только на сервере**
- Файл **НЕ в Git** (в `.gitignore`)
- Папка расшарена **только на Service Account**
- Фото **НЕ публичные** - доступ только через API

### ❌ Неправильно:

- ❌ Публичная ссылка на папку Drive
- ❌ OAuth flow для каждого пользователя (усложняет архитектуру)
- ❌ API ключ в коде (используйте `.env`)
- ❌ Публичные файлы на Drive

## Troubleshooting

### Ошибка: "Permission denied"

**Причина:** Service Account не имеет доступа к папке

**Решение:**
1. Проверьте, что папка расшарена на email Service Account
2. Убедитесь, что права "Editor" (не "Viewer")
3. Проверьте правильность `GOOGLE_DRIVE_FOLDER_ID`

### Ошибка: "Invalid credentials"

**Причина:** Неправильный путь к JSON файлу или поврежденный файл

**Решение:**
1. Проверьте путь в `GOOGLE_CREDENTIALS_PATH`
2. Убедитесь, что файл валидный JSON
3. Пересоздайте ключ в Google Cloud Console

### Ошибка: "API not enabled"

**Причина:** Google Drive API не включен в проекте

**Решение:**
1. Перейдите в Google Cloud Console
2. APIs & Services → Library
3. Найдите "Google Drive API" и включите

### Ошибка: "Quota exceeded"

**Причина:** Превышен лимит запросов или хранилища

**Решение:**
1. Проверьте квоты в Google Cloud Console → IAM & Admin → Quotas
2. Добавьте кэширование для уменьшения запросов
3. Рассмотрите переход на платный план

## Миграция на другое хранилище

Если Google Drive не подходит, архитектура позволяет легко мигрировать:

### AWS S3:
```python
# backend/app/services/s3_storage.py
import boto3

s3 = boto3.client('s3')

def upload_file(file_path, bucket, key):
    s3.upload_file(file_path, bucket, key)
    return key

def get_file(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()
```

### Cloudflare R2:
```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='https://account_id.r2.cloudflarestorage.com',
    aws_access_key_id='access_key',
    aws_secret_access_key='secret_key'
)
```

### Backblaze B2:
```python
from b2sdk.v2 import InMemoryAccountInfo, B2Api

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", application_key_id, application_key)
```

**Нужно изменить только:** `backend/app/services/google_drive.py`

**Без изменений:** API endpoints, модели БД, frontend

## Полезные ссылки

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Service Accounts Documentation](https://cloud.google.com/iam/docs/service-accounts)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)
