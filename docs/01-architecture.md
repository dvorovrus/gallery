# Архитектура системы Gallery

## Обзор

Gallery - это веб-приложение для управления фотоальбомами с использованием Google Drive в качестве хранилища файлов. Система построена на современном стеке технологий с разделением на фронтенд и бэкенд.

## Архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────┐
│                    Пользователь                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              React Frontend (SPA)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  - React 19.2.1 + TypeScript                     │  │
│  │  - Vite 6.0 (Build Tool)                         │  │
│  │  - Tailwind CSS 4.1 (Styling)                    │  │
│  │  - Axios (HTTP Client)                           │  │
│  │  - Lucide React (Icons)                          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (JSON)
                     │ Authorization: Bearer <JWT>
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Layer (FastAPI 0.136.3)                     │  │
│  │  ├── /auth      - Аутентификация                │  │
│  │  ├── /albums    - Управление альбомами           │  │
│  │  ├── /photos    - Управление фото                │  │
│  │  └── /share     - Публичные ссылки               │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────┴───────────────────────────────┐  │
│  │  Business Logic Layer                            │  │
│  │  ├── JWT Authentication                          │  │
│  │  ├── Password Hashing (bcrypt)                   │  │
│  │  ├── File Upload Handling                        │  │
│  │  └── Share Link Generation                       │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────┴───────────────────────────────┐  │
│  │  Data Access Layer                               │  │
│  │  ├── SQLAlchemy 2.0 ORM                          │  │
│  │  ├── Alembic Migrations                          │  │
│  │  └── Google Drive Service                        │  │
│  └──────────────────┬───────────────────────────────┘  │
└────────────────────┬┴───────────────────────────────────┘
                     │                │
                     │                │
         ┌───────────▼─────┐  ┌──────▼──────────────────┐
         │   PostgreSQL    │  │  Google Drive API       │
         │   Database      │  │  (Service Account)      │
         │                 │  │                         │
         │  - users        │  │  PhotoGalleryStorage/   │
         │  - albums       │  │  ├── user_1/            │
         │  - photos       │  │  │   ├── album_1/       │
         │  - shares       │  │  │   └── album_2/       │
         └─────────────────┘  │  └── user_2/            │
                              │      └── album_5/        │
                              └─────────────────────────┘
```

## Компоненты системы

### 1. Frontend (React SPA)

**Технологии:**
- React 19.2.6 с TypeScript
- Vite 8.0.10 для быстрой разработки и сборки
- Tailwind CSS 4.1 для стилизации
- Axios для HTTP запросов
- Lucide React для иконок

**Ключевые возможности:**
- Регистрация и авторизация пользователей
- Создание и управление альбомами
- Загрузка фотографий (multipart/form-data)
- Просмотр галереи с адаптивной сеткой (masonry layout)
- Полноэкранный просмотр (Lightbox)
- Генерация публичных ссылок
- Темная/светлая тема

**Структура:**
```
frontend/
├── src/
│   ├── components/    # React компоненты
│   ├── api/          # API клиент (Axios)
│   ├── types/        # TypeScript типы
│   ├── styles/       # Tailwind CSS
│   └── App.tsx       # Главный компонент
├── index.html
├── vite.config.ts
└── package.json
```

### 2. Backend (FastAPI)

**Технологии:**
- FastAPI 0.136.3 - современный асинхронный веб-фреймворк
- SQLAlchemy 2.0 - ORM для работы с БД
- Alembic - миграции базы данных
- PyJWT - генерация и валидация JWT токенов
- Passlib + bcrypt - безопасное хеширование паролей
- Google API Python Client - интеграция с Google Drive

**API Endpoints:**

```
POST   /auth/register     - Регистрация нового пользователя
POST   /auth/login        - Вход (получение JWT токена)
GET    /auth/me           - Получение текущего пользователя

GET    /albums            - Список альбомов пользователя
POST   /albums            - Создание нового альбома
DELETE /albums/{id}       - Удаление альбома (каскадное)

GET    /albums/{id}/photos      - Список фото в альбоме
POST   /albums/{id}/photos      - Загрузка фото в альбом
GET    /photos/{id}             - Получение фото (stream из Drive)
DELETE /photos/{id}              - Удаление фото

POST   /albums/{id}/share       - Создание публичной ссылки
GET    /share/{token}           - Просмотр альбома по токену
```

**Структура:**
```
backend/
├── app/
│   ├── api/              # API роутеры
│   │   ├── auth.py       # Аутентификация
│   │   ├── albums.py     # Альбомы
│   │   ├── photos.py     # Фотографии
│   │   └── share.py      # Шаринг
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   │   └── google_drive.py
│   └── core/             # Конфигурация
│       ├── config.py
│       ├── database.py
│       └── security.py
├── alembic/              # Миграции БД
├── main.py               # Точка входа
└── requirements.txt
```

### 3. База данных (PostgreSQL)

**Схема базы данных:**

```sql
-- Пользователи
users
------
id              SERIAL PRIMARY KEY
email           VARCHAR UNIQUE NOT NULL
password_hash   VARCHAR NOT NULL
created_at      TIMESTAMP DEFAULT NOW()

-- Альбомы
albums
------
id              SERIAL PRIMARY KEY
user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE
title           VARCHAR NOT NULL
created_at      TIMESTAMP DEFAULT NOW()
is_public       BOOLEAN DEFAULT FALSE
password_hash   VARCHAR NULL

-- Фотографии
photos
------
id              SERIAL PRIMARY KEY
album_id        INTEGER REFERENCES albums(id) ON DELETE CASCADE
drive_file_id   VARCHAR NOT NULL       -- ID файла в Google Drive
filename        VARCHAR NOT NULL
caption         VARCHAR
created_at      TIMESTAMP DEFAULT NOW()

-- Публичные ссылки
shares
------
id              SERIAL PRIMARY KEY
album_id        INTEGER REFERENCES albums(id) ON DELETE CASCADE
token           VARCHAR UNIQUE NOT NULL
password_hash   VARCHAR NULL
expires_at      TIMESTAMP NULL
created_at      TIMESTAMP DEFAULT NOW()
```

**Связи:**
- `users` → `albums` (1:N, cascade delete)
- `albums` → `photos` (1:N, cascade delete)
- `albums` → `shares` (1:N, cascade delete)

### 4. Google Drive Storage

**Структура хранилища:**

```
PhotoGalleryStorage/              (Root папка)
├── user_1/                       (Папка пользователя)
│   ├── album_1/                  (Папка альбома)
│   │   ├── uuid_photo1.jpg
│   │   └── uuid_photo2.jpg
│   └── album_2/
│       └── uuid_photo3.jpg
└── user_2/
    └── album_5/
        └── uuid_photo4.jpg
```

**Service Account:**
- Используется Service Account (не OAuth2)
- JSON ключ хранится на сервере
- Root папка расшарена на Service Account email
- Scope: `https://www.googleapis.com/auth/drive`

**Операции:**
- `create_user_folder()` - создание папки пользователя
- `create_album_folder()` - создание папки альбома
- `upload_file()` - загрузка файла
- `get_file()` - получение файла (streaming)
- `delete_file()` - удаление файла
- `delete_folder()` - удаление папки

## Поток данных

### 1. Регистрация и авторизация

```
User → Frontend → POST /auth/register → Backend
                                        ├─ Hash password (bcrypt)
                                        ├─ Save to PostgreSQL
                                        └─ Return user data

User → Frontend → POST /auth/login → Backend
                                     ├─ Verify credentials
                                     ├─ Generate JWT token (7 days)
                                     └─ Return access_token

Frontend → Store token in localStorage
Frontend → Add "Authorization: Bearer <token>" to all requests
```

### 2. Загрузка фото

```
User → Select files → Frontend
                      ├─ Create FormData
                      └─ POST /albums/{id}/photos

Backend receives files
├─ Verify JWT token
├─ Check album ownership
├─ Save to temp file
├─ Upload to Google Drive
│  └─ Returns drive_file_id
├─ Save metadata to PostgreSQL
│  └─ (id, album_id, drive_file_id, filename, caption)
└─ Return photo metadata

Frontend → Display uploaded photos
```

### 3. Просмотр фото

```
Frontend → GET /photos/{id} → Backend
                              ├─ Query PostgreSQL for drive_file_id
                              ├─ Fetch file from Google Drive
                              └─ Stream bytes to client

Browser → Display image
```

### 4. Публичный шаринг

```
User → Click "Share" → Frontend → POST /albums/{id}/share
                                  Body: { password?: "secret" }

Backend
├─ Generate unique token (secrets.token_urlsafe)
├─ Hash password if provided
├─ Save to shares table
└─ Return { token, password_required }

Frontend → Display link: https://site.com/share/{token}

---

Recipient → Open link → GET /share/{token}?password=secret

Backend
├─ Find share by token
├─ Verify password if required
├─ Return album + photos
└─ Frontend displays public gallery
```

## Безопасность

### Аутентификация
- **JWT токены** с expiration (7 дней)
- Токены хранятся в localStorage
- Bearer Authentication в заголовках

### Пароли
- Хеширование через **bcrypt** (passlib)
- Salt автоматически генерируется
- Никогда не храним plain text

### Доступ к фото
- Фото **НЕ публичные** в Google Drive
- Доступ только через Backend API
- Backend проверяет ownership перед отдачей файла

### CORS
- Настроен белый список origins
- Credentials allowed
- Preflight requests поддерживаются

### Валидация
- Pydantic схемы валидируют все входные данные
- SQLAlchemy защищает от SQL injection
- File upload с проверкой типов

## Масштабирование

### Текущая архитектура (MVP)
- Один FastAPI сервер
- Один PostgreSQL инстанс
- Google Drive для файлов
- Без кэширования

### Возможные улучшения

**1. Кэширование:**
```
Frontend → Nginx → Redis Cache → FastAPI → Google Drive
```
- Кэшировать часто запрашиваемые изображения
- TTL 1 час
- Уменьшает нагрузку на Drive API

**2. CDN:**
- Использовать CloudFlare для статики
- Кэширование изображений на edge серверах

**3. Горизонтальное масштабирование:**
- Несколько инстансов FastAPI за Load Balancer
- Stateless backend (JWT не требует сессий)
- PostgreSQL connection pooling

**4. Миграция хранилища:**
- Google Drive → AWS S3 / Cloudflare R2 / Backblaze B2
- Только изменение слоя `services/google_drive.py`
- API и БД остаются без изменений

**5. Оптимизация БД:**
- Индексы на `email`, `token`, `drive_file_id`
- Read replicas для масштабирования чтения
- Партиционирование таблицы `photos`

**6. Background tasks:**
- Celery для асинхронной обработки
- Tasks: генерация thumbnails, оптимизация изображений

## Мониторинг и логирование

**Метрики:**
- API response time
- Database query time
- Google Drive API latency
- Upload/download throughput

**Логирование:**
- Структурированные JSON логи
- Уровни: DEBUG, INFO, WARNING, ERROR
- Логи ошибок Google Drive API
- Логи неудачных авторизаций

**Инструменты:**
- Prometheus + Grafana (метрики)
- ELK Stack (логи)
- Sentry (error tracking)

## Зависимости

### External Services
- **Google Drive API** - хранилище файлов
- **PostgreSQL** - реляционная БД

### Внутренние
- Frontend зависит от Backend API
- Backend зависит от PostgreSQL и Google Drive
- Полная независимость frontend и backend (можно деплоить отдельно)

## Деплоймент

### Варианты деплоя

**1. Separate deployment:**
- Frontend → Vercel / Netlify / CloudFlare Pages
- Backend → Railway / Render / AWS EC2
- Database → Railway / Supabase / AWS RDS

**2. Docker-compose (single server):**
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["80:80"]
  
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db]
  
  db:
    image: postgres:15
    volumes: ["pgdata:/var/lib/postgresql/data"]
```

**3. Kubernetes (production scale):**
- Frontend: Static files в Nginx pod
- Backend: Multiple replicas за Ingress
- Database: StatefulSet или managed service
- Secrets: Kubernetes Secrets для credentials

## Заключение

Архитектура Gallery построена на принципах:
- **Separation of Concerns** - четкое разделение frontend/backend
- **Stateless Backend** - JWT позволяет горизонтальное масштабирование
- **External Storage** - Google Drive для файлов, PostgreSQL для метаданных
- **Security First** - JWT, bcrypt, non-public files
- **Scalability** - архитектура готова к росту нагрузки

Текущая реализация - это MVP, который можно запустить бесплатно и масштабировать по мере роста.
