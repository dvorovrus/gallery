# Gallery - Photo Album Application

Полноценное веб-приложение для управления фотоальбомами с хранением в Google Drive, аутентификацией и публичным шарингом.

🌐 **Live Demo:** https://gallery.fatbox.org

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
│ (Vercel Serverless) │
└──────┬───────┬──────┘
       │       │
       │       ▼
       │   SQLite DB
       │
       ▼
  Google Drive API
       │
       ▼
  Google Drive Storage
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
- **FastAPI 0.136.3** - веб-фреймворк (Serverless)
- **SQLite** - встроенная база данных
- **SQLAlchemy 2.0** - ORM
- **JWT** - аутентификация
- **Google Drive API** - облачное хранилище
- **Mangum** - ASGI adapter для Vercel

### Deployment
- **Vercel** - хостинг и деплой
- **Serverless Functions** - backend API
- **Vercel Edge Network** - CDN

## 🚀 Деплой на Vercel

### 1. Fork репозитория

### 2. Импортируйте проект в Vercel
1. Перейдите на https://vercel.com/new
2. Импортируйте ваш GitHub репозиторий
3. Vercel автоматически определит настройки

### 3. Настройте Environment Variables

В Vercel Dashboard добавьте:

```env
DATABASE_URL=sqlite:////tmp/gallery.db
SECRET_KEY=<сгенерируйте: openssl rand -base64 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
STORAGE_TYPE=google_drive
GOOGLE_CREDENTIALS_PATH=/tmp/service-account.json
CORS_ORIGINS=https://your-domain.com
VITE_API_URL=/api
```

### 4. Настройте автоматический деплой по тегу [deploy]

Деплой происходит автоматически только при коммитах с `[deploy]` в сообщении:

```bash
git add .
git commit -m "[deploy] Ваше сообщение"
git push origin master
```

### 5. Настройте Google Drive через UI

После первого деплоя:
1. Откройте ваше приложение
2. Зарегистрируйтесь (первый пользователь = админ)
3. Нажмите на ⚙️ Settings
4. Следуйте инструкциям для создания Google Service Account
5. Загрузите service-account.json через UI
6. Укажите Google Drive Folder ID
7. Нажмите "Test Connection"

**Инструкции по настройке Google Drive встроены в UI!**

## 🔑 Основные возможности

- ✅ Регистрация и аутентификация пользователей (JWT)
- ✅ Создание и управление альбомами
- ✅ Загрузка фотографий в Google Drive
- ✅ Автоматическая генерация thumbnails
- ✅ Просмотр фото в режиме галереи
- ✅ Полноэкранный режим (Lightbox)
- ✅ Публичный шаринг альбомов и фото
- ✅ Защита паролем для приватных ссылок
- ✅ Автоудаление альбомов по таймеру (7/14/30 дней)
- ✅ Темная/светлая тема
- ✅ Responsive дизайн
- ✅ Админ-панель для настройки Google Drive

## 📁 Структура проекта

```
gallery/
├── api/
│   └── index.py           # Vercel serverless function (FastAPI)
├── frontend/              # React приложение
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── api/           # API клиент
│   │   ├── services/      # Сервисы
│   │   ├── types/         # TypeScript типы
│   │   └── App.tsx        # Главный компонент
│   └── package.json
├── backend/               # FastAPI приложение
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── services/      # Бизнес-логика
│   │   └── core/          # Конфигурация
│   └── alembic/           # Миграции БД
├── package.json           # Root package.json для Vercel
├── requirements.txt       # Python зависимости
└── README.md
```

## 🔐 Безопасность

- JWT токены для аутентификации
- Argon2 для хеширования паролей
- Google Service Account для доступа к Drive
- CORS настройки
- Валидация всех входных данных
- Защита паролем для публичных ссылок
- Credentials хранятся в защищенной БД

## 🛠 Локальная разработка

### Требования
- Node.js 20+
- Python 3.12+

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📄 Лицензия

MIT License

## 👨‍💻 Разработка

Проект создан с использованием современного стека технологий (по состоянию на июнь 2026).

Для вопросов и предложений создавайте Issues в GitHub репозитории.
