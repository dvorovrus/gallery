# База данных

## Обзор

Gallery использует **PostgreSQL 15+** в качестве реляционной базы данных для хранения метаданных пользователей, альбомов, фотографий и публичных ссылок.

Сами файлы изображений хранятся в Google Drive, а в БД хранятся только:
- ID файлов в Drive
- Метаданные (имена, подписи, даты)
- Связи между сущностями

## Схема базы данных

```sql
-- Пользователи
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- Альбомы
CREATE TABLE albums (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255) NULL
);

CREATE INDEX idx_albums_user_id ON albums(user_id);

-- Фотографии
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    drive_file_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    caption TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_photos_album_id ON photos(album_id);
CREATE INDEX idx_photos_drive_file_id ON photos(drive_file_id);

-- Публичные ссылки
CREATE TABLE shares (
    id SERIAL PRIMARY KEY,
    album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shares_token ON shares(token);
CREATE INDEX idx_shares_album_id ON shares(album_id);
```

## Описание таблиц

### users

Хранит информацию о зарегистрированных пользователях.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | Первичный ключ |
| email | VARCHAR(255) | Email пользователя (уникальный) |
| password_hash | VARCHAR(255) | Хеш пароля (bcrypt) |
| created_at | TIMESTAMP | Дата регистрации |

**Индексы:**
- PRIMARY KEY на `id`
- UNIQUE INDEX на `email`

**Связи:**
- `users` → `albums` (1:N, ON DELETE CASCADE)

### albums

Хранит альбомы пользователей.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | Первичный ключ |
| user_id | INTEGER | FK на users.id |
| title | VARCHAR(255) | Название альбома |
| created_at | TIMESTAMP | Дата создания |
| is_public | BOOLEAN | Флаг публичности (не используется в MVP) |
| password_hash | VARCHAR(255) | Хеш пароля для альбома (не используется в MVP) |

**Индексы:**
- PRIMARY KEY на `id`
- INDEX на `user_id`

**Связи:**
- `albums` ← `users` (N:1)
- `albums` → `photos` (1:N, ON DELETE CASCADE)
- `albums` → `shares` (1:N, ON DELETE CASCADE)

### photos

Хранит метаданные фотографий.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | Первичный ключ |
| album_id | INTEGER | FK на albums.id |
| drive_file_id | VARCHAR(255) | ID файла в Google Drive |
| filename | VARCHAR(255) | Оригинальное имя файла |
| caption | TEXT | Подпись к фото (опционально) |
| created_at | TIMESTAMP | Дата загрузки |

**Индексы:**
- PRIMARY KEY на `id`
- INDEX на `album_id`
- INDEX на `drive_file_id`

**Связи:**
- `photos` ← `albums` (N:1)

**Примечания:**
- Сам файл изображения хранится в Google Drive
- `drive_file_id` используется для получения файла через Drive API
- При удалении альбома все фото удаляются каскадно

### shares

Хранит публичные ссылки для шаринга альбомов.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | Первичный ключ |
| album_id | INTEGER | FK на albums.id |
| token | VARCHAR(255) | Уникальный токен для ссылки |
| password_hash | VARCHAR(255) | Хеш пароля (опционально) |
| expires_at | TIMESTAMP | Дата истечения (опционально) |
| created_at | TIMESTAMP | Дата создания ссылки |

**Индексы:**
- PRIMARY KEY на `id`
- UNIQUE INDEX на `token`
- INDEX на `album_id`

**Связи:**
- `shares` ← `albums` (N:1)

## ER-диаграмма

```
┌─────────────────────┐
│       users         │
│─────────────────────│
│ PK  id              │
│ UNQ email           │
│     password_hash   │
│     created_at      │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐
│      albums         │
│─────────────────────│
│ PK  id              │
│ FK  user_id         │
│     title           │
│     created_at      │
│     is_public       │
│     password_hash   │
└──────┬──────────┬───┘
       │          │
       │ 1:N      │ 1:N
       │          │
       ▼          ▼
┌──────────┐  ┌──────────┐
│  photos  │  │  shares  │
│──────────│  │──────────│
│ PK id    │  │ PK id    │
│ FK album │  │ FK album │
│    _id   │  │    _id   │
│ drive_   │  │ UNQ token│
│ file_id  │  │ password │
│ filename │  │ _hash    │
│ caption  │  │ expires  │
│ created  │  │ _at      │
│ _at      │  │ created  │
└──────────┘  │ _at      │
              └──────────┘
```

## Миграции (Alembic)

### Установка

```bash
cd backend
pip install alembic
```

### Инициализация

```bash
alembic init alembic
```

### Создание миграции

```bash
alembic revision -m "create initial tables"
```

### Применение миграций

```bash
# Apply all migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback all
alembic downgrade base
```

### История миграций

```bash
alembic history
alembic current
```

### Первая миграция (Initial Schema)

Создайте файл `alembic/versions/001_initial.py`:

```python
"""create initial tables

Revision ID: 001
Create Date: 2026-06-08 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # Albums table
    op.create_table(
        'albums',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_albums_user_id', 'albums', ['user_id'])

    # Photos table
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('album_id', sa.Integer(), nullable=False),
        sa.Column('drive_file_id', sa.String(255), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_photos_album_id', 'photos', ['album_id'])
    op.create_index('idx_photos_drive_file_id', 'photos', ['drive_file_id'])

    # Shares table
    op.create_table(
        'shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('album_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_shares_token', 'shares', ['token'], unique=True)
    op.create_index('idx_shares_album_id', 'shares', ['album_id'])

def downgrade():
    op.drop_table('shares')
    op.drop_table('photos')
    op.drop_table('albums')
    op.drop_table('users')
```

## Настройка подключения

### 1. Установка PostgreSQL

**Windows:**
```bash
# Скачайте с https://www.postgresql.org/download/windows/
# Или через Chocolatey:
choco install postgresql
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Создание базы данных

```bash
# Войти в PostgreSQL
psql -U postgres

# Создать базу
CREATE DATABASE gallery;

# Создать пользователя
CREATE USER gallery_user WITH PASSWORD 'your_password';

# Выдать права
GRANT ALL PRIVILEGES ON DATABASE gallery TO gallery_user;

# Выйти
\q
```

### 3. Настройка .env

```bash
DATABASE_URL=postgresql://gallery_user:your_password@localhost:5432/gallery
```

### 4. Проверка подключения

```bash
psql -U gallery_user -d gallery -h localhost
```

### 5. Применение миграций (из venv)

```bash
cd backend

# Активировать venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Применить миграции
alembic upgrade head
```

## SQL запросы для администрирования

### Посмотреть все таблицы

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Количество записей в каждой таблице

```sql
SELECT 
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'albums', COUNT(*) FROM albums
UNION ALL
SELECT 'photos', COUNT(*) FROM photos
UNION ALL
SELECT 'shares', COUNT(*) FROM shares;
```

### Топ пользователей по количеству фото

```sql
SELECT 
    u.email,
    COUNT(DISTINCT a.id) as album_count,
    COUNT(p.id) as photo_count
FROM users u
LEFT JOIN albums a ON a.user_id = u.id
LEFT JOIN photos p ON p.album_id = a.id
GROUP BY u.id, u.email
ORDER BY photo_count DESC
LIMIT 10;
```

### Альбомы с количеством фото

```sql
SELECT 
    a.id,
    a.title,
    u.email as owner,
    COUNT(p.id) as photo_count,
    a.created_at
FROM albums a
JOIN users u ON u.id = a.user_id
LEFT JOIN photos p ON p.album_id = a.id
GROUP BY a.id, a.title, u.email, a.created_at
ORDER BY photo_count DESC;
```

### Публичные ссылки с паролями

```sql
SELECT 
    s.token,
    a.title as album,
    u.email as owner,
    CASE WHEN s.password_hash IS NOT NULL THEN 'Yes' ELSE 'No' END as has_password,
    s.expires_at,
    s.created_at
FROM shares s
JOIN albums a ON a.id = s.album_id
JOIN users u ON u.id = a.user_id
ORDER BY s.created_at DESC;
```

### Удаление старых неиспользуемых альбомов

```sql
-- Альбомы без фото, созданные более 30 дней назад
DELETE FROM albums
WHERE id IN (
    SELECT a.id 
    FROM albums a
    LEFT JOIN photos p ON p.album_id = a.id
    WHERE p.id IS NULL 
    AND a.created_at < NOW() - INTERVAL '30 days'
);
```

## Backup и восстановление

### Создание backup

```bash
# Full backup
pg_dump -U gallery_user -d gallery > backup_$(date +%Y%m%d).sql

# Только схема
pg_dump -U gallery_user -d gallery --schema-only > schema.sql

# Только данные
pg_dump -U gallery_user -d gallery --data-only > data.sql

# Compressed backup
pg_dump -U gallery_user -d gallery -Fc -f backup.dump
```

### Восстановление

```bash
# Из SQL файла
psql -U gallery_user -d gallery < backup_20260608.sql

# Из compressed backup
pg_restore -U gallery_user -d gallery backup.dump

# Восстановление в новую базу
createdb -U postgres gallery_new
pg_restore -U gallery_user -d gallery_new backup.dump
```

### Автоматический backup (cron)

```bash
# Создать скрипт backup.sh
cat > /opt/gallery/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/gallery/backups"
pg_dump -U gallery_user -d gallery -Fc -f "$BACKUP_DIR/gallery_$DATE.dump"
# Удалить backups старше 7 дней
find "$BACKUP_DIR" -name "gallery_*.dump" -mtime +7 -delete
EOF

chmod +x /opt/gallery/backup.sh

# Добавить в cron (каждый день в 3:00)
crontab -e
0 3 * * * /opt/gallery/backup.sh
```

## Мониторинг производительности

### Медленные запросы

```sql
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Размер таблиц

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Активные соединения

```sql
SELECT 
    datname,
    count(*) as connections
FROM pg_stat_activity
GROUP BY datname;
```

## Оптимизация

### Индексы

Уже созданы в схеме:
- `users.email` (UNIQUE)
- `albums.user_id`
- `photos.album_id`
- `photos.drive_file_id`
- `shares.token` (UNIQUE)
- `shares.album_id`

### VACUUM и ANALYZE

```sql
-- Очистка и оптимизация
VACUUM ANALYZE;

-- Для конкретной таблицы
VACUUM ANALYZE photos;

-- Автоматический vacuum (уже включен по умолчанию в PostgreSQL)
```

### Connection Pooling

Для production рекомендуется использовать **PgBouncer**:

```bash
# Установка
sudo apt install pgbouncer

# Конфигурация /etc/pgbouncer/pgbouncer.ini
[databases]
gallery = host=localhost port=5432 dbname=gallery

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

В `.env` изменить:
```
DATABASE_URL=postgresql://gallery_user:password@localhost:6432/gallery
```

## Troubleshooting

### Ошибка: "could not connect to server"

```bash
# Проверить статус PostgreSQL
sudo systemctl status postgresql

# Запустить
sudo systemctl start postgresql
```

### Ошибка: "password authentication failed"

```bash
# Сбросить пароль
sudo -u postgres psql
ALTER USER gallery_user WITH PASSWORD 'new_password';
```

### Ошибка: "too many connections"

```sql
-- Посмотреть лимит
SHOW max_connections;

-- Увеличить в postgresql.conf
max_connections = 200

-- Перезапустить PostgreSQL
sudo systemctl restart postgresql
```

## Безопасность

### 1. Использовать SSL

```bash
# В .env
DATABASE_URL=postgresql://user:pass@host:5432/gallery?sslmode=require
```

### 2. Ограничить доступ

```bash
# /etc/postgresql/15/main/pg_hba.conf
# Разрешить только localhost
host    gallery    gallery_user    127.0.0.1/32    md5
```

### 3. Регулярные backups

Настроить автоматические backups (см. выше)

### 4. Мониторинг

- Логировать медленные запросы
- Мониторить размер БД
- Отслеживать количество соединений

## Заключение

PostgreSQL база данных в Gallery хранит только метаданные - сами файлы в Google Drive. Это обеспечивает:

- ✅ Быстрые запросы к метаданным
- ✅ Надежные ACID-транзакции
- ✅ Простые backup/restore
- ✅ Масштабируемость через репликацию
- ✅ Полный контроль над структурой данных
