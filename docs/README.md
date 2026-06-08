# Gallery Project - Documentation Index

Добро пожаловать в документацию проекта Gallery!

## 📚 Документы

### Основные документы

1. **[Архитектура системы](./01-architecture.md)**
   - Общая схема приложения
   - Компоненты и их взаимодействие
   - Поток данных
   - Масштабирование

2. **[API Reference](./02-api-reference.md)**
   - Полный список endpoints
   - Примеры запросов и ответов
   - Коды ошибок
   - Аутентификация

3. **[База данных](./04-database.md)**
   - Схема базы данных
   - Миграции с Alembic
   - SQL запросы для администрирования
   - Backup и восстановление

4. **[Настройка Google Drive OAuth](./04-google-drive-oauth-setup.md)**
   - Создание OAuth credentials
   - Настройка Google Drive API
   - Безопасность
   - Troubleshooting

5. **[Развертывание](./05-deployment.md)**
   - Локальное развертывание
   - Docker Compose
   - Production рекомендации

6. **[Примеры использования](./06-examples.md)**
   - JavaScript/TypeScript примеры
   - Python клиент
   - React интеграция
   - Продвинутые сценарии

## 🚀 Быстрый старт

### 1. Установка

```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. Настройка

Создайте `backend/.env` на основе `.env.example`:

```env
# База данных (SQLite)
DATABASE_URL=sqlite:///./gallery.db

# JWT секретный ключ
SECRET_KEY=your-secret-key-here

# Тип хранилища
STORAGE_TYPE=local  # или google_drive_oauth

# CORS
CORS_ORIGINS=http://localhost:5173
```

### 3. База данных

```bash
cd backend
alembic upgrade head
# или
python init_db.py
```

### 4. Запуск

```bash
# Backend
cd backend
venv\Scripts\activate  # Windows (source venv/bin/activate на Linux/macOS)
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

Откройте http://localhost:5173

## 📖 Изучение проекта

### Для разработчиков frontend:

1. Начните с [API Reference](./02-api-reference.md)
2. Посмотрите [Примеры использования](./06-examples.md)
3. Изучите `frontend/src/api/client.ts`

### Для разработчиков backend:

1. Начните с [Архитектуры](./01-architecture.md)
2. Изучите [Базу данных](./04-database.md)
3. Посмотрите `backend/app/api/` endpoints

### Для DevOps:

1. Начните с [Развертывания](./05-deployment.md)
2. Настройте [Google Drive](./03-google-drive-setup.md)
3. Изучите Docker Compose / Kubernetes конфиги

## 🔧 Технологии

### Frontend
- React 19.2.6
- TypeScript 5.7
- Vite 8.0.10
- Tailwind CSS 4.1
- Lucide React

### Backend
- FastAPI 0.136.3
- Python 3.12+
- SQLite (или PostgreSQL для production)
- SQLAlchemy 2.0
- Google Drive API (опционально)

### Storage Options
- Local File Storage (по умолчанию)
- Google Drive OAuth 2.0 (опционально)

## 📝 Структура проекта

```
gallery/
├── frontend/           # React приложение
│   ├── src/
│   │   ├── components/
│   │   ├── api/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
│
├── backend/            # FastAPI приложение
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── core/
│   ├── alembic/
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py
│
├── docs/               # Документация
│   ├── 01-architecture.md
│   ├── 02-api-reference.md
│   ├── 04-database.md
│   ├── 04-google-drive-oauth-setup.md
│   ├── 05-deployment.md
│   └── 06-examples.md
│
└── README.md           # Обзор проекта
```

## 🔗 Полезные ссылки

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 💡 Советы

### При разработке:

- Используйте `--reload` для автоматической перезагрузки
- Проверяйте логи в консоли
- Используйте Swagger UI для тестирования API

### При возникновении проблем:

1. Проверьте логи в консоли backend/frontend
2. Проверьте переменные окружения в `.env`
3. Убедитесь, что venv активирован для backend
4. Проверьте Google Drive credentials (если используется)

### Для production:

- Используйте HTTPS
- Настройте CORS правильно
- Смените SQLite на PostgreSQL
- Регулярные backups БД
- Мониторинг и логирование

## 🤝 Контрибьютинг

При внесении изменений:

1. Обновите соответствующую документацию
2. Добавьте примеры использования
3. Запустите тесты
4. Создайте Pull Request

## 📄 Лицензия

MIT License

---

**Последнее обновление:** 2026-06-08

**Версия:** 1.0.0
