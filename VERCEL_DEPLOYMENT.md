# Vercel Deployment Guide

## Автоматический деплой по тегу [deploy]

Проект настроен для автоматического деплоя на Vercel при коммитах с тегом `[deploy]` в сообщении.

## Предварительные требования

1. Аккаунт на Vercel
2. GitHub репозиторий подключен к Vercel
3. Google Drive Service Account credentials (настраивается через UI после деплоя)

## Быстрый старт

### 1. Импортируйте проект в Vercel

1. Перейдите на https://vercel.com/new
2. Импортируйте ваш GitHub репозиторий
3. Vercel автоматически определит настройки
4. Нажмите "Deploy"

### 2. Настройте Environment Variables

В Vercel Dashboard → Settings → Environment Variables добавьте:

```
DATABASE_URL=sqlite:////tmp/gallery.db
SECRET_KEY=<сгенерируйте случайный ключ>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
STORAGE_TYPE=google_drive
GOOGLE_CREDENTIALS_PATH=/tmp/service-account.json
CORS_ORIGINS=https://your-domain.com
VITE_API_URL=/api
```

**Генерация SECRET_KEY:**
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### 3. Настройте Custom Domain (опционально)

В Vercel Dashboard → Settings → Domains:
1. Добавьте ваш домен
2. Настройте DNS:
   - CNAME запись: `your-subdomain` → `cname.vercel-dns.com`
   - Или A запись на IP предоставленный Vercel

### 4. Автоматический деплой

Для деплоя новых изменений используйте тег `[deploy]`:

```bash
git add .
git commit -m "[deploy] Описание изменений"
git push origin master
```

Vercel автоматически:
- Обнаружит коммит с `[deploy]`
- Соберет frontend
- Задеплоит serverless functions
- Обновит production

## Первый запуск приложения

После успешного деплоя:

1. **Откройте ваше приложение**
2. **Зарегистрируйтесь** (первый пользователь становится админом)
3. **Нажмите на ⚙️ Settings** в правом верхнем углу
4. **Настройте Google Drive:**

### Google Drive Setup через UI

В Settings вы найдете пошаговую инструкцию:

**Шаг 1: Создание Service Account**
- Откройте [Google Cloud Console](https://console.cloud.google.com/)
- Создайте проект
- Включите Google Drive API
- Создайте Service Account
- Скачайте JSON ключ

**Шаг 2: Настройка Google Drive**
- Создайте папку в Google Drive
- Поделитесь папкой с email Service Account (из JSON файла)
- Дайте права "Editor"
- Скопируйте Folder ID из URL

**Шаг 3: Загрузка в UI**
- Загрузите service-account.json через веб-интерфейс
- Вставьте Google Drive Folder ID
- Нажмите "Save Configuration"
- Нажмите "Test Connection" для проверки

✅ Готово! Фотографии будут сохраняться на Google Drive.

## Архитектура на Vercel

```
Internet
    ↓
Vercel Edge Network (CDN)
    ↓
    ├─→ Frontend (Static) - /
    └─→ Backend API (Serverless) - /api/*
            ↓
        Google Drive API
            ↓
        Google Drive Storage
```

### Особенности Vercel Deployment

**База данных:**
- SQLite в `/tmp/` (временное хранилище)
- Сбрасывается при каждом деплое
- Используется только для сессий и настроек

**Фотографии:**
- Постоянное хранение в Google Drive
- Настраивается через админ-панель UI

**Serverless Functions:**
- Автоматическое масштабирование
- Холодный старт ~1-2 секунды
- Максимальное время выполнения: 10 сек (Hobby), 60 сек (Pro)

## Ограничения Vercel (Hobby Plan)

- Максимальное время выполнения функции: 10 секунд
- Максимальный размер загружаемого файла: 4.5 MB
- Для больших файлов рекомендуется Pro план (100 MB лимит)

## Troubleshooting

### "Function timeout"
- Загрузка больших файлов может занять время
- Рассмотрите upgrade до Pro плана
- Оптимизируйте обработку изображений

### "Google Drive API error"
- Проверьте правильность service-account.json
- Убедитесь что папка расшарена на Service Account email
- Используйте "Test Connection" в Settings

### Деплой не запускается
- Убедитесь что в коммите есть тег `[deploy]`
- Проверьте что репозиторий подключен к Vercel
- Проверьте логи в Vercel Dashboard

## Production Checklist

- [ ] Проект импортирован в Vercel
- [ ] Environment variables настроены
- [ ] Custom domain добавлен (опционально)
- [ ] SSL сертификат активен (автоматически)
- [ ] Первый пользователь зарегистрирован
- [ ] Google Drive настроен через Settings UI
- [ ] Протестирована загрузка фотографий
- [ ] Протестирован публичный шаринг

## Полезные команды Vercel CLI

```bash
# Установить Vercel CLI
npm i -g vercel

# Залогиниться
vercel login

# Связать проект
vercel link

# Посмотреть логи
vercel logs

# Список деплоев
vercel ls

# Список environment variables
vercel env ls
```

## Мониторинг

- Vercel Dashboard: https://vercel.com/dashboard
- Deployment logs доступны для каждого деплоя
- Автоматические уведомления о статусе деплоя

---

**Готово!** Ваше приложение готово к production использованию на Vercel.
