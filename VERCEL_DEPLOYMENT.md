# Vercel Deployment Guide

## Конфигурация проекта

Проект настроен для автоматического деплоя на Vercel при коммитах с тегом `[deploy]` в сообщении.

## Предварительные требования

1. Аккаунт на Vercel
2. GitHub репозиторий подключен к Vercel
3. Google Drive Service Account credentials (JSON файл)
4. Google Drive Folder ID для хранения фотографий

## Настройка Vercel Project

### 1. Подключите репозиторий к Vercel

Импортируйте проект в Vercel Dashboard.

### 2. Настройте Environment Variables

В настройках проекта на Vercel добавьте следующие переменные окружения:

```
DATABASE_URL=sqlite:////tmp/gallery.db
SECRET_KEY=<ваш-секретный-ключ-минимум-32-символа>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
STORAGE_TYPE=google_drive
GOOGLE_CREDENTIALS_PATH=/tmp/service-account.json
GOOGLE_DRIVE_FOLDER_ID=<ваш-folder-id>
CORS_ORIGINS=https://gallery.fatbox.org
VITE_API_URL=/api
```

**Важно:**
- Для `SECRET_KEY` используйте надежный случайный ключ (можно сгенерировать: `openssl rand -base64 32`)
- `GOOGLE_DRIVE_FOLDER_ID` - ID папки в Google Drive, куда будут загружаться фото

### 3. Добавьте Google Service Account Credentials

Создайте секрет с содержимым вашего `service-account.json`:

**Способ 1: Через Vercel CLI**
```bash
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON
# Вставьте содержимое service-account.json файла
```

**Способ 2: Через Dashboard**
В настройках проекта добавьте переменную `GOOGLE_SERVICE_ACCOUNT_JSON` со всем содержимым JSON файла.

Затем обновите `api/index.py` чтобы использовать эту переменную:
```python
import json
google_creds = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
if google_creds:
    with open('/tmp/service-account.json', 'w') as f:
        f.write(google_creds)
```

### 4. Настройте Custom Domain

В настройках проекта на Vercel:
1. Перейдите в раздел "Domains"
2. Добавьте домен `gallery.fatbox.org`
3. Настройте DNS записи согласно инструкциям Vercel

## Процесс деплоя

### Автоматический деплой

Проект настроен на деплой только при коммитах с `[deploy]` в сообщении:

```bash
git add .
git commit -m "[deploy] Добавлена новая функция"
git push origin main
```

### Ручной деплой

Через Vercel Dashboard или CLI:

```bash
vercel --prod
```

## Структура проекта для Vercel

```
gallery/
├── api/
│   └── index.py          # Vercel serverless function (FastAPI handler)
├── frontend/
│   ├── dist/             # Билд frontend (генерируется)
│   └── src/              # Исходники React
├── backend/
│   └── app/              # FastAPI приложение
├── vercel.json           # Конфигурация Vercel
└── requirements.txt      # Python зависимости для serverless functions
```

## Особенности Vercel Deployment

### Хранилище

- **База данных:** SQLite в `/tmp/` (временное хранилище, сбрасывается при каждом деплое)
- **Фотографии:** Google Drive (постоянное хранилище)

⚠️ **Важно:** Для production рекомендуется использовать внешнюю БД (PostgreSQL на Railway, Supabase, и т.д.)

### Ограничения Serverless Functions

- Максимальное время выполнения: 10 секунд (Hobby), 60 секунд (Pro)
- Максимальный размер загружаемого файла: 4.5 MB (Hobby), 100 MB (Pro)
- Файловая система доступна только для чтения (кроме `/tmp/`)

## Google Drive Setup

### 1. Создание Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Drive API
4. Создайте Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Скачайте JSON ключ
5. Поделитесь папкой Google Drive с email Service Account

### 2. Получение Folder ID

1. Откройте папку в Google Drive
2. URL будет выглядеть так: `https://drive.google.com/drive/folders/FOLDER_ID`
3. Скопируйте `FOLDER_ID`

## Troubleshooting

### Ошибки деплоя

**"Module not found"**
- Проверьте `requirements.txt` в корне проекта
- Убедитесь что все зависимости указаны

**"Function timeout"**
- Загрузка больших файлов может занять время
- Рассмотрите upgrade до Pro плана
- Оптимизируйте обработку изображений

**"Google Drive API error"**
- Проверьте правильность `GOOGLE_SERVICE_ACCOUNT_JSON`
- Убедитесь что папка расшарена на Service Account email
- Проверьте `GOOGLE_DRIVE_FOLDER_ID`

### Проверка логов

```bash
vercel logs <deployment-url>
```

Или в Vercel Dashboard → Deployments → выберите деплой → Function Logs

## Production Checklist

- [ ] Все environment variables настроены
- [ ] Google Service Account credentials добавлены
- [ ] Custom domain настроен
- [ ] SSL сертификат активен (автоматически через Vercel)
- [ ] База данных (для production - использовать внешнюю БД)
- [ ] Google Drive папка создана и расшарена
- [ ] Протестирован деплой с тегом [deploy]

## Команды

```bash
# Установить Vercel CLI
npm i -g vercel

# Залогиниться
vercel login

# Деплой в development
vercel

# Деплой в production
vercel --prod

# Просмотр логов
vercel logs

# Список переменных окружения
vercel env ls

# Добавить переменную окружения
vercel env add
```
