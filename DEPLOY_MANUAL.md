# Инструкция по деплою Gallery Application

## ✅ Что уже подготовлено:

1. **Docker конфигурация:**
   - `backend/Dockerfile` - готов
   - `frontend/Dockerfile` - готов  
   - `docker-compose.yml` - готов
   - `frontend/nginx.conf` - готов

2. **Environment файлы с правильными настройками:**
   - `.env` - домен `gallery.fatbox.org`, PostgreSQL пароль
   - `backend/.env.prod` - DATABASE_URL, SECRET_KEY, CORS

3. **API endpoint настроен:**
   - Frontend использует `/api` для production
   - Traefik будет маршрутизировать запросы

## 📋 Шаги для деплоя от пользователя deploy:

### 1. Подключитесь к серверу

```bash
ssh deploy@149.202.61.227
```

### 2. Создайте директорию проекта

```bash
mkdir -p /opt/gallery
cd /opt/gallery
```

### 3. Скопируйте файлы проекта на сервер

С **локальной машины** выполните:

```powershell
# Создайте архив (Windows)
cd D:\project\gallery
tar -czf gallery-deploy.tar.gz --exclude=node_modules --exclude=venv --exclude=__pycache__ --exclude=*.pyc --exclude=dist --exclude=build --exclude=.git --exclude=gallery.db --exclude=uploads --exclude=token.json --exclude=oauth_credentials.json .

# Скопируйте на сервер
scp gallery-deploy.tar.gz deploy@149.202.61.227:/opt/gallery/

# Удалите локальный архив
del gallery-deploy.tar.gz
```

### 4. Распакуйте архив на сервере

```bash
cd /opt/gallery
tar -xzf gallery-deploy.tar.gz
rm gallery-deploy.tar.gz
```

### 5. Проверьте файлы окружения

Убедитесь, что файлы `.env` и `backend/.env.prod` на месте:

```bash
ls -la .env
ls -la backend/.env.prod
```

### 6. Соберите Docker образы

```bash
cd /opt/gallery
docker-compose build
```

Это займёт несколько минут. Будут собраны:
- Frontend (React + nginx)
- Backend (FastAPI + Python 3.12)
- PostgreSQL будет загружен готовый образ

### 7. Запустите контейнеры

```bash
docker-compose up -d
```

Эта команда запустит все сервисы в фоновом режиме:
- `gallery-frontend` - фронтенд на nginx
- `gallery-backend` - бэкенд FastAPI
- `gallery-postgres` - база данных PostgreSQL

### 8. Проверьте статус контейнеров

```bash
docker-compose ps
```

Все контейнеры должны быть в статусе "Up".

### 9. Примените миграции базы данных

```bash
docker-compose exec backend alembic upgrade head
```

Эта команда создаст все необходимые таблицы в PostgreSQL.

### 10. Проверьте логи

```bash
# Все логи
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend

# Только postgres
docker-compose logs -f postgres
```

Нажмите `Ctrl+C` чтобы выйти из просмотра логов.

## 🌐 Доступ к приложению

После успешного деплоя приложение будет доступно по адресу:

**https://gallery.fatbox.org**

Traefik автоматически:
- Получит SSL-сертификат от Let's Encrypt
- Настроит редирект с HTTP на HTTPS
- Будет маршрутизировать запросы:
  - `/` → frontend
  - `/api/*` → backend

## ✅ Проверка работоспособности

### Backend health check:
```bash
curl https://gallery.fatbox.org/healthz
```

Должен вернуть: `{"status":"ok"}`

### API документация:
- **Swagger UI:** https://gallery.fatbox.org/docs
- **ReDoc:** https://gallery.fatbox.org/redoc

### Frontend:
Откройте https://gallery.fatbox.org в браузере

## 🔧 Полезные команды

### Перезапуск сервисов:
```bash
cd /opt/gallery
docker-compose restart
```

### Остановка:
```bash
docker-compose down
```

### Остановка с удалением volumes (⚠️ УДАЛИТ БАЗУ ДАННЫХ):
```bash
docker-compose down -v
```

### Обновление приложения:
```bash
cd /opt/gallery
docker-compose down
# Скопируйте новые файлы (повторите шаг 3-4)
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Просмотр использования ресурсов:
```bash
docker stats
```

### Просмотр логов с временными метками:
```bash
docker-compose logs -f --timestamps
```

### Выполнение команды внутри контейнера:
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# PostgreSQL CLI
docker-compose exec postgres psql -U gallery_user -d gallery_db
```

## 🔐 Создание первого пользователя

После деплоя создайте первого пользователя через API:

```bash
curl -X POST https://gallery.fatbox.org/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "your-secure-password"
  }'
```

Или через интерфейс регистрации на сайте.

## 📊 Структура сети Docker

```
public-traefik (внешняя)
  ├─ frontend
  └─ backend
  
gallery-internal (внутренняя)
  ├─ frontend
  ├─ backend
  └─ postgres
  
infra-postgres-private (внешняя)
  ├─ backend
  └─ postgres
```

## 🐛 Решение проблем

### Контейнеры не запускаются

Проверьте логи:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### База данных не доступна

Проверьте, что postgres контейнер запущен:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

Проверьте healthcheck:
```bash
docker-compose exec postgres pg_isready -U gallery_user
```

### Ошибки миграции

Попробуйте сбросить базу и накатить миграции заново:
```bash
docker-compose down -v
docker-compose up -d
sleep 10
docker-compose exec backend alembic upgrade head
```

### Frontend показывает ошибки API

Проверьте CORS настройки в `backend/.env.prod`:
```bash
cat backend/.env.prod | grep CORS
```

Должно быть: `CORS_ORIGINS=https://gallery.fatbox.org,http://localhost:5173`

### SSL сертификат не выдаётся

Проверьте:
1. DNS настроен правильно: `dig gallery.fatbox.org`
2. Traefik работает: `docker ps | grep traefik`
3. Порты 80 и 443 открыты: `sudo netstat -tlnp | grep -E ':(80|443)'`

## 📝 Важные файлы

```
/opt/gallery/
├── .env                    # Основные переменные (домен, PostgreSQL)
├── backend/.env.prod       # Backend конфигурация (SECRET_KEY, DATABASE_URL)
├── docker-compose.yml      # Orchestration конфигурация
├── backend/Dockerfile      # Backend образ
├── frontend/Dockerfile     # Frontend образ
└── frontend/nginx.conf     # Nginx конфигурация для SPA
```

## 🎉 Готово!

После выполнения всех шагов приложение будет доступно по адресу:
**https://gallery.fatbox.org**

---

**Время деплоя:** ~5-10 минут (в зависимости от скорости сборки)
**Требования:** Docker, docker-compose, доступ к пользователю deploy
