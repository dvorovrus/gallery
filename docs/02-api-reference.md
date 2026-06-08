# API Reference

## Базовая информация

**Base URL:** `http://localhost:8000`

**Формат данных:** JSON

**Аутентификация:** JWT Bearer Token

**Заголовки:**
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

---

## Аутентификация

### POST /auth/register

Регистрация нового пользователя.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-06-08T10:30:00.000Z"
}
```

**Errors:**
- `400` - Email already registered
- `422` - Validation error

---

### POST /auth/login

Вход в систему, получение JWT токена.

**Request:** `application/x-www-form-urlencoded`
```
username=user@example.com
password=securepassword123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token payload:**
```json
{
  "user_id": 1,
  "exp": 1749820800
}
```

**Token lifetime:** 7 дней (10080 минут)

**Errors:**
- `401` - Incorrect email or password

---

### GET /auth/me

Получение информации о текущем пользователе.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2026-06-08T10:30:00.000Z"
}
```

**Errors:**
- `401` - Invalid or expired token

---

## Альбомы

### GET /albums

Получить список всех альбомов пользователя.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "title": "Отпуск 2026",
    "created_at": "2026-06-01T12:00:00.000Z",
    "is_public": false
  },
  {
    "id": 2,
    "user_id": 1,
    "title": "Свадьба",
    "created_at": "2026-05-15T18:30:00.000Z",
    "is_public": false
  }
]
```

---

### POST /albums

Создать новый альбом.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "title": "Новый альбом"
}
```

**Response:** `201 Created`
```json
{
  "id": 3,
  "user_id": 1,
  "title": "Новый альбом",
  "created_at": "2026-06-08T10:45:00.000Z",
  "is_public": false
}
```

**Errors:**
- `401` - Unauthorized
- `422` - Validation error (empty title)

---

### DELETE /albums/{album_id}

Удалить альбом и все его фотографии.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Side effects:**
- Удаляются все фото из альбома (каскадное удаление)
- Фото удаляются из Google Drive
- Удаляются все ссылки для шаринга

**Errors:**
- `401` - Unauthorized
- `404` - Album not found

---

## Фотографии

### GET /albums/{album_id}/photos

Получить список всех фото в альбоме.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "album_id": 1,
    "drive_file_id": "1ABCxyz123...",
    "filename": "sunset.jpg",
    "caption": "Закат на море",
    "created_at": "2026-06-01T14:20:00.000Z"
  },
  {
    "id": 2,
    "album_id": 1,
    "drive_file_id": "1DEFabc456...",
    "filename": "beach.jpg",
    "caption": "Пляж",
    "created_at": "2026-06-01T15:00:00.000Z"
  }
]
```

**Errors:**
- `401` - Unauthorized
- `404` - Album not found

---

### POST /albums/{album_id}/photos

Загрузить фотографии в альбом.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:** `multipart/form-data`
```
files: [File, File, ...]  # Multiple files
caption: "Описание фото"   # Optional
```

**Пример curl:**
```bash
curl -X POST http://localhost:8000/albums/1/photos \
  -H "Authorization: Bearer <token>" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "caption=Летние фото"
```

**Response:** `201 Created`
```json
[
  {
    "id": 3,
    "album_id": 1,
    "drive_file_id": "1GHIjkl789...",
    "filename": "photo1.jpg",
    "caption": "Летние фото",
    "created_at": "2026-06-08T11:00:00.000Z"
  },
  {
    "id": 4,
    "album_id": 1,
    "drive_file_id": "1MNOpqr012...",
    "filename": "photo2.jpg",
    "caption": "Летние фото",
    "created_at": "2026-06-08T11:00:05.000Z"
  }
]
```

**Процесс загрузки:**
1. Файлы сохраняются временно на сервере
2. Загружаются в Google Drive (в папку альбома)
3. Метаданные сохраняются в PostgreSQL
4. Временные файлы удаляются

**Errors:**
- `401` - Unauthorized
- `404` - Album not found
- `413` - File too large
- `415` - Unsupported media type

---

### GET /photos/{photo_id}

Получить изображение (streaming).

**Response:** `200 OK`
```
Content-Type: image/jpeg
[Binary data stream]
```

**Использование:**
```html
<img src="http://localhost:8000/photos/1" alt="Photo" />
```

**Процесс:**
1. Backend получает `drive_file_id` из БД
2. Запрашивает файл из Google Drive
3. Стримит байты напрямую клиенту

**Errors:**
- `404` - Photo not found
- `500` - Failed to retrieve from Google Drive

---

### DELETE /photos/{photo_id}

Удалить фотографию.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Side effects:**
- Удаляется файл из Google Drive
- Удаляется запись из БД

**Errors:**
- `401` - Unauthorized
- `404` - Photo not found

---

## Публичный шаринг

### POST /albums/{album_id}/share

Создать публичную ссылку для альбома.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "password": "secret123"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "album_id": 1,
  "token": "xY9k2LmP8QrT5vWz",
  "password_required": true,
  "expires_at": null,
  "created_at": "2026-06-08T11:15:00.000Z"
}
```

**Использование:**
```
https://gallery.app/share/xY9k2LmP8QrT5vWz
```

**Errors:**
- `401` - Unauthorized
- `404` - Album not found

---

### GET /share/{token}

Просмотр альбома по публичной ссылке.

**Query Parameters:**
```
password: string  // Required if share has password
```

**Request:**
```
GET /share/xY9k2LmP8QrT5vWz?password=secret123
```

**Response:** `200 OK`
```json
{
  "album": {
    "id": 1,
    "user_id": 1,
    "title": "Отпуск 2026",
    "created_at": "2026-06-01T12:00:00.000Z",
    "is_public": false
  },
  "photos": [
    {
      "id": 1,
      "album_id": 1,
      "drive_file_id": "1ABCxyz123...",
      "filename": "sunset.jpg",
      "caption": "Закат на море",
      "created_at": "2026-06-01T14:20:00.000Z"
    }
  ]
}
```

**Errors:**
- `404` - Share link not found
- `401` - Incorrect password (if required)

---

## Коды ответов

| Код | Значение | Описание |
|-----|----------|----------|
| 200 | OK | Успешный запрос |
| 201 | Created | Ресурс создан |
| 204 | No Content | Успешное удаление |
| 400 | Bad Request | Некорректные данные |
| 401 | Unauthorized | Не авторизован или неверный токен |
| 404 | Not Found | Ресурс не найден |
| 413 | Payload Too Large | Файл слишком большой |
| 415 | Unsupported Media Type | Неподдерживаемый тип файла |
| 422 | Unprocessable Entity | Ошибка валидации |
| 500 | Internal Server Error | Внутренняя ошибка сервера |

---

## Примеры использования

### Полный flow регистрации и загрузки фото

```javascript
// 1. Регистрация
const registerResponse = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const user = await registerResponse.json();

// 2. Вход
const formData = new URLSearchParams();
formData.append('username', 'user@example.com');
formData.append('password', 'password123');

const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData
});
const { access_token } = await loginResponse.json();

// 3. Создание альбома
const albumResponse = await fetch('http://localhost:8000/albums', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({ title: 'Мой альбом' })
});
const album = await albumResponse.json();

// 4. Загрузка фото
const photoFormData = new FormData();
photoFormData.append('files', fileInput.files[0]);
photoFormData.append('files', fileInput.files[1]);
photoFormData.append('caption', 'Отличные фото');

const uploadResponse = await fetch(`http://localhost:8000/albums/${album.id}/photos`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: photoFormData
});
const photos = await uploadResponse.json();

// 5. Создание публичной ссылки
const shareResponse = await fetch(`http://localhost:8000/albums/${album.id}/share`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({ password: 'secret' })
});
const share = await shareResponse.json();

console.log(`Share link: https://gallery.app/share/${share.token}`);
```

---

## Rate Limiting

В текущей версии rate limiting не реализован. 

**Рекомендуется добавить в production:**
- 5 запросов/секунду на пользователя
- 100 запросов/час для регистрации/логина
- Специальные лимиты для upload endpoints

---

## Пагинация

В текущей версии пагинация не реализована. Все запросы возвращают полный список.

**Для production рекомендуется:**
```
GET /albums?page=1&limit=20
GET /albums/{id}/photos?page=2&limit=50
```

---

## WebSocket / Real-time

В текущей версии не поддерживается.

**Возможные расширения:**
- Уведомления о завершении загрузки
- Real-time прогресс загрузки
- Уведомления о новых share links

---

## API Documentation

Интерактивная документация доступна после запуска сервера:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
