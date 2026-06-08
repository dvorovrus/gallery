# Gallery - Photo Album Application

Полноценное веб-приложение для управления фотоальбомами с возможностью хранения в Google Drive или локально, аутентификацией и публичным шарингом.

## 🏗️ Архитектура

```
┌─────────────────────┐
│    React Frontend   │
│   (Vite + Tailwind) │
└──────────┬──────────┘
           │ HTTPS/REST API
           ▼
┌─────────────────────┐
│   FastAPI Backend   │
│   (Python 3.12+)    │
└──────┬───────┬──────┘
       │       │
       │       ▼
       │   SQLite DB
       │
       ▼
 Local Storage or
 Google Drive API
       │
       ▼
 Local Files or
 Google Drive
```

## 📦 Технологический стек

### Frontend
- **React 19.2.6** - UI библиотека
- **TypeScript 5.7** - типизация
- **Vite 8.0.10** - сборщик
- **Tailwind CSS 4.1** - стилизация
- **Lucide React** - иконки
- **Axios** - HTTP клиент

### Backend
- **FastAPI 0.136.3** - веб-фреймворк
- **SQLite** - встроенная база данных
- **SQLAlchemy 2.0** - ORM
- **JWT** - аутентификация
- **Google Drive API (опционально)** - облачное хранилище
- **Local Storage** - локальное хранилище файлов

## 🚀 Быстрый старт

### Требования
- Node.js 20+
- Python 3.12+
- Google Cloud OAuth credentials (опционально, для Google Drive интеграции)

### 1. Установка зависимостей

#### Frontend
```bash
cd frontend
npm install
```

#### Backend
```bash
cd backend

# Создать виртуальное окружение
python -m venv venv

# Активировать venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка окружения

Создайте файл `backend/.env` на основе `backend/.env.example`:

```env
# База данных (SQLite)
DATABASE_URL=sqlite:///./gallery.db

# JWT секретный ключ (сгенерируйте свой)
SECRET_KEY=your-secret-key-here-change-this

# Тип хранилища: "local" или "google_drive_oauth"
STORAGE_TYPE=local

# Google Drive (опционально, если STORAGE_TYPE=google_drive_oauth)
GOOGLE_CREDENTIALS_PATH=./oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id

# CORS
CORS_ORIGINS=http://localhost:5173
```

### 3. Инициализация базы данных

```bash
cd backend

# Применить миграции
alembic upgrade head

# Или создать БД через init_db.py
python init_db.py
```

### 4. Запуск приложения

#### Backend (порт 8000)
```bash
cd backend

# Активировать venv (если еще не активирован)
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Запустить сервер
uvicorn main:app --reload
```

#### Frontend (порт 5173)
```bash
cd frontend
npm run dev
```

Откройте [http://localhost:5173](http://localhost:5173)

## 📖 Документация

Подробная документация находится в папке [`docs/`](./docs/):

- [Архитектура системы](./docs/01-architecture.md)
- [API Reference](./docs/02-api-reference.md)
- [Настройка Google Drive](./docs/03-google-drive-setup.md)
- [База данных](./docs/04-database.md)
- [Развертывание](./docs/05-deployment.md)
- [Примеры использования](./docs/06-examples.md)

## 🔑 Основные возможности

- ✅ Регистрация и аутентификация пользователей (JWT)
- ✅ Создание и управление альбомами
- ✅ Загрузка фотографий в Google Drive
- ✅ Просмотр фото в режиме галереи
- ✅ Полноэкранный режим (Lightbox)
- ✅ Публичный шаринг альбомов и фото
- ✅ Защита паролем для приватных ссылок
- ✅ Темная/светлая тема
- ✅ Responsive дизайн

## 📁 Структура проекта

```
gallery/
├── frontend/           # React приложение
│   ├── src/
│   │   ├── components/ # React компоненты
│   │   ├── api/        # API клиент
│   │   ├── services/   # Сервисы
│   │   ├── types/      # TypeScript типы
│   │   └── App.tsx     # Главный компонент
│   ├── package.json
│   └── vite.config.ts
│
├── backend/            # FastAPI приложение
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── models/     # SQLAlchemy модели
│   │   ├── schemas/    # Pydantic схемы
│   │   ├── services/   # Бизнес-логика
│   │   └── core/       # Конфигурация
│   ├── alembic/        # Миграции БД
│   ├── requirements.txt
│   ├── main.py
│   ├── .env.example    # Пример конфигурации
│   └── init_db.py      # Инициализация БД
│
├── docs/               # Документация
└── README.md           # Этот файл
```

## 🔐 Безопасность

- JWT токены для аутентификации
- Argon2 для хеширования паролей
- OAuth 2.0 для Google Drive (с пользовательским согласием)
- CORS настройки
- Валидация всех входных данных
- Защита паролем для публичных ссылок

## 📄 Лицензия

MIT License

## 👨‍💻 Разработка

Проект создан с использованием современного стека технологий (по состоянию на июнь 2026).

Для вопросов и предложений создавайте Issues в GitHub репозитории.
