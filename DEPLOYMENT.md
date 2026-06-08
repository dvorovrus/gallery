# Gallery Application - Deployment Guide

## 📋 Подготовка к деплою

Проект полностью подготовлен для развертывания на сервере 149.202.61.227 с использованием Docker и Traefik.

### Структура файлов для деплоя:

```
gallery/
├── backend/
│   ├── Dockerfile              ✓ Создан
│   ├── .dockerignore           ✓ Создан
│   ├── .env.prod.example       ✓ Создан
│   └── .env.prod               ⚠ Требуется создать
├── frontend/
│   ├── Dockerfile              ✓ Создан
│   ├── nginx.conf              ✓ Создан
│   └── .dockerignore           ✓ Создан
├── docker-compose.yml          ✓ Создан
├── .env.example                ✓ Создан
├── .env                        ⚠ Требуется создать
├── deploy.sh                   ✓ Создан (Linux/Mac)
└── deploy.bat                  ✓ Создан (Windows)
```

## 🔧 Шаги для деплоя

### 1. Создайте файлы окружения

#### Корневой `.env`
```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите:
- `DOMAIN` - ваш домен (например, `gallery.fatbox.org`)
- `POSTGRES_USER` - пользователь PostgreSQL
- `POSTGRES_PASSWORD` - **сильный** пароль для PostgreSQL
- `POSTGRES_DB` - имя базы данных

#### Backend `.env.prod`
```bash
cp backend/.env.prod.example backend/.env.prod
```

Отредактируйте `backend/.env.prod` и укажите:
- `DATABASE_URL` - строка подключения к PostgreSQL (используйте данные из корневого .env)
- `SECRET_KEY` - **случайный** секретный ключ (минимум 32 символа)
- `CORS_ORIGINS` - ваш домен с https://
- Остальные параметры по необходимости

**Генерация SECRET_KEY:**
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### 2. Проверьте API endpoint в frontend

Убедитесь, что в `frontend/src/api/client.ts` или аналогичном файле указан правильный базовый URL для API:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
```

Traefik будет маршрутизировать запросы к `/api/*` на backend автоматически.

### 3. Запустите деплой

#### На Windows:
```cmd
deploy.bat
```

#### На Linux/Mac:
```bash
chmod +x deploy.sh
./deploy.sh
```

Скрипт выполнит:
1. Проверку наличия файлов окружения
2. Подключение к серверу
3. Создание директории `/opt/gallery`
4. Копирование файлов на сервер
5. Сборку Docker образов
6. Запуск контейнеров
7. Применение миграций базы данных

### 4. Проверка деплоя

После завершения скрипта проверьте статус контейнеров:

```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose ps'
```

Просмотр логов:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose logs -f'
```

## 🌐 Настройка DNS

Добавьте A-запись для вашего домена, указывающую на IP сервера:

```
gallery.fatbox.org  A  149.202.61.227
```

Traefik автоматически получит SSL-сертификат от Let's Encrypt.

## 🔒 Безопасность

**ВАЖНО!** Убедитесь, что:

- ✅ `.env` и `.env.prod` добавлены в `.gitignore`
- ✅ Используются сильные пароли для PostgreSQL
- ✅ `SECRET_KEY` уникален и случаен
- ✅ CORS настроен только на ваш домен
- ✅ Файлы `.env` **НЕ** коммитятся в Git

## 📦 Архитектура деплоя

```
Internet
    ↓
Traefik (порты 80, 443)
    ↓
    ├─→ Frontend (nginx) - https://gallery.fatbox.org/
    └─→ Backend (FastAPI) - https://gallery.fatbox.org/api/*
            ↓
        PostgreSQL (внутренняя сеть)
```

### Сети Docker:

- `public-traefik` - внешняя сеть для Traefik (должна существовать)
- `infra-postgres-private` - сеть для PostgreSQL (может использоваться существующий или создается отдельный)
- `gallery-internal` - внутренняя сеть приложения

## 🔄 Обновление приложения

Для обновления приложения просто запустите скрипт деплоя заново:

```bash
./deploy.sh  # или deploy.bat
```

Скрипт:
- Скопирует новые файлы
- Пересоберет образы
- Перезапустит контейнеры без простоя

## 🛠 Полезные команды

### Перезапуск сервисов:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose restart'
```

### Остановка:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose down'
```

### Запуск:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose up -d'
```

### Просмотр логов конкретного сервиса:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose logs -f backend'
```

### Выполнение миграций вручную:
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose exec backend alembic upgrade head'
```

### Создание первого пользователя (если нужно):
```bash
ssh -i ~/.ssh/id_ed25519 ai-bot@149.202.61.227 'cd /opt/gallery && docker compose exec backend python -c "from app.core.database import SessionLocal; from app.models.user import User; from app.core.security import get_password_hash; db=SessionLocal(); user=User(email=\"admin@example.com\", username=\"admin\", hashed_password=get_password_hash(\"changeme\")); db.add(user); db.commit(); print(\"User created\")"'
```

## 📊 Мониторинг

Приложение включает healthcheck endpoints:

- Backend: `https://your-domain.com/healthz`
- Traefik Dashboard: `https://traefik-domain.com` (если настроен)

## ❌ Решение проблем

### Ошибка подключения к PostgreSQL

Проверьте, что сеть `infra-postgres-private` существует или используйте отдельную БД для проекта.

### Ошибка "network not found"

Создайте недостающие внешние сети:
```bash
docker network create public-traefik
docker network create infra-postgres-private
```

### SSL сертификат не получен

Проверьте:
- DNS правильно настроен
- Порты 80 и 443 открыты
- Traefik работает корректно

## 📝 Checklist перед деплоем

- [ ] Создан файл `.env` с актуальными данными
- [ ] Создан файл `backend/.env.prod` с безопасными паролями
- [ ] SECRET_KEY сгенерирован случайным образом
- [ ] DOMAIN указан правильно
- [ ] DNS настроен на IP сервера
- [ ] Проверено, что .env файлы в .gitignore
- [ ] Frontend API endpoint настроен корректно

---

**Готово!** Ваше приложение готово к деплою.
