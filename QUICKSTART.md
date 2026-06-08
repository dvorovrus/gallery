# Quick Start Guide

## Первый запуск проекта

### 1. Клонирование проекта
```bash
git clone https://github.com/dvorovrus/gallery.git
cd gallery
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
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/macOS

# Отредактировать .env:
# - DATABASE_URL=sqlite:///./gallery.db
# - SECRET_KEY (генерировать: python -c "import secrets; print(secrets.token_hex(32))")
# - STORAGE_TYPE=local (или google_drive_oauth для Google Drive)
# - Опционально: настроить Google Drive OAuth
```

#### Создать базу данных
```bash
# SQLite БД создается автоматически
# Применить миграции (venv должен быть активирован!)
alembic upgrade head

# Или использовать init_db.py
python init_db.py
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

- [README.md](./README.md) - Обзор проекта
- [docs/](./docs/) - Полная документация
- [docs/04-google-drive-oauth-setup.md](./docs/04-google-drive-oauth-setup.md) - Настройка Google Drive OAuth

## Ежедневная работа

```bash
# 1. Открыть проект
cd gallery

# 2. Terminal 1: Backend
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
uvicorn main:app --reload

# 3. Terminal 2: Frontend
cd frontend
npm run dev

# 4. Кодить! 🎉
```

**Важно:** ВСЕГДА активируйте venv перед работой с Python!
