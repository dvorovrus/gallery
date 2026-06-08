# Quick Start Guide

## Первый запуск проекта

### 1. Клонирование проекта
```bash
cd D:\project\gallery
```

### 2. Backend Setup

#### Создать и активировать venv
```bash
cd backend

# Создать виртуальное окружение
python -m venv venv

# Активировать (ОБЯЗАТЕЛЬНО!)
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# В командной строке должно появиться (venv)
```

#### Установить зависимости
```bash
# Убедитесь, что venv активирован!
pip install -r requirements.txt
```

#### Настроить окружение
```bash
# Скопировать пример
copy .env.example .env

# Отредактировать .env:
# - DATABASE_URL (PostgreSQL)
# - SECRET_KEY (генерировать: openssl rand -hex 32)
# - GOOGLE_DRIVE_FOLDER_ID
# - Поместить service-account.json в backend/
```

#### Создать базу данных
```bash
# Создать PostgreSQL БД
createdb gallery

# Применить миграции (venv должен быть активирован!)
alembic upgrade head
```

### 3. Frontend Setup

```bash
# Открыть новый терминал
cd frontend

# Установить зависимости
npm install
```

### 4. Запуск

#### Terminal 1: Backend
```bash
cd backend

# Активировать venv (если еще не активирован)
venv\Scripts\activate

# Запустить FastAPI
uvicorn main:app --reload

# Вывод: INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Terminal 2: Frontend
```bash
cd frontend

# Запустить Vite dev server
npm run dev

# Вывод: Local: http://localhost:5173/
```

### 5. Открыть в браузере

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Важные команды

### Backend (всегда из venv!)

```bash
# Активировать venv
cd backend
venv\Scripts\activate

# Создать миграцию
alembic revision -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Запустить сервер
uvicorn main:app --reload

# Запустить с другим портом
uvicorn main:app --reload --port 8001

# Деактивировать venv
deactivate
```

### Frontend

```bash
cd frontend

# Dev server
npm run dev

# Build production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Troubleshooting

### "uvicorn: command not found"
❌ **Проблема:** venv не активирован
✅ **Решение:** `cd backend && venv\Scripts\activate`

### "ModuleNotFoundError: No module named 'fastapi'"
❌ **Проблема:** Зависимости не установлены или не в venv
✅ **Решение:** 
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### "alembic: command not found"
❌ **Проблема:** venv не активирован
✅ **Решение:** `venv\Scripts\activate` перед запуском alembic

### Port 8000 already in use
❌ **Проблема:** Backend уже запущен
✅ **Решение:** 
- Найти процесс: `netstat -ano | findstr :8000`
- Убить процесс: `taskkill /PID <pid> /F`
- Или запустить на другом порту: `uvicorn main:app --port 8001`

## Полезные ссылки

- [README.md](../README.md) - Обзор проекта
- [docs/](../docs/) - Полная документация
- [docs/03-google-drive-setup.md](../docs/03-google-drive-setup.md) - Настройка Google Drive

## Ежедневная работа

```bash
# 1. Открыть проект
cd D:\project\gallery

# 2. Terminal 1: Backend
cd backend
venv\Scripts\activate
uvicorn main:app --reload

# 3. Terminal 2: Frontend
cd frontend
npm run dev

# 4. Кодить! 🎉
```

**Важно:** ВСЕГДА активируйте venv перед работой с Python!
