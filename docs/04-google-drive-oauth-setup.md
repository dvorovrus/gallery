# Настройка Google Drive через OAuth 2.0 (Бесплатный вариант)

## Обзор

Этот метод использует **ваш личный Google аккаунт** вместо Service Account, что позволяет бесплатно хранить фото на вашем Google Drive (15 ГБ бесплатно).

**Преимущества:**
- ✅ Полностью бесплатно (15 ГБ)
- ✅ Не нужен Google Workspace
- ✅ Простая настройка

**Ограничения:**
- ⚠️ Все фото хранятся на вашем личном аккаунте
- ⚠️ Лимит 15 ГБ (~5000 фото по 3 МБ)
- ⚠️ Подходит для MVP и малых проектов

---

## Шаг 1: Создание OAuth 2.0 Credentials

### 1.1 Перейдите в Google Cloud Console

[https://console.cloud.google.com/](https://console.cloud.google.com/)

Выберите существующий проект или создайте новый.

### 1.2 Включите Google Drive API

1. Перейдите: **APIs & Services** → **Library**
2. Найдите "Google Drive API"
3. Нажмите **"Enable"**

### 1.3 Настройка OAuth Consent Screen

Если OAuth Consent Screen еще не настроен, вы увидите сообщение:
_"Google Auth Platform not configured yet"_

1. Перейдите: **APIs & Services** → **OAuth consent screen** (или нажмите **"Get started"** в разделе Branding)
2. Откроется страница **"Project configuration"** с пошаговым мастером

#### Шаг 1: App Information

Заполните форму:
- **App name:** `Photo Gallery` (название приложения, которое увидят пользователи)
- **User support email:** выберите ваш email из выпадающего списка
- Нажмите **"Next"**

#### Шаг 2: Audience

Выберите тип аудитории:

**Варианты:**
- **Internal** — только для пользователей внутри вашей организации (требуется Google Workspace)
- **External** — доступно любому пользователю с Google аккаунтом (✅ выберите этот вариант)

**Выберите: External**

После выбора **External** приложение запустится в тестовом режиме. Вы сможете добавить себя в список тест-пользователей на следующих шагах.

- Нажмите **"Next"**

#### Шаг 3: Contact Information

Введите контактные данные разработчика:

- **Email addresses:** введите ваш Gmail адрес (обязательное поле)
  - Можно указать несколько адресов через запятую
  - Этот email Google будет использовать для связи по вопросам приложения

- Нажмите **"Next"**

#### Шаг 4: Finish

На последнем шаге нужно принять условия:

1. Установите галочку: **"I agree to the Google API Services: User Data Policy"**
2. Нажмите **"Continue"**
3. Нажмите **"Create"**

После создания вы увидите страницу **OAuth Overview** с сообщением:
✅ _"OAuth configuration created!"_

Теперь OAuth Consent Screen настроен, и вы можете создавать OAuth Client ID.

### 1.4 Добавьте Scopes

1. Нажмите **"Add or Remove Scopes"**
2. Найдите и добавьте:
   ```
   https://www.googleapis.com/auth/drive.file
   ```
   (Доступ только к файлам, созданным приложением)
3. Нажмите **"Update"** → **"Save and Continue"**

### 1.5 Добавьте Test Users

Поскольку приложение в режиме "Testing", нужно добавить ваш email:

1. Нажмите **"Add Users"**
2. Введите ваш Gmail адрес
3. Нажмите **"Add"** → **"Save and Continue"**

### 1.6 Создайте OAuth Client ID

После создания OAuth Consent Screen вернитесь на страницу **OAuth Overview** и нажмите **"Create OAuth client"**.

#### Шаг 1: Выберите тип приложения

На странице **"Create OAuth client ID"** выберите тип приложения:

**Application type:** откройте выпадающий список и выберите:
- **Web application** — если ваш backend работает как веб-сервер (FastAPI/Flask)
- **Desktop app** — если запускаете OAuth flow локально

Для этого проекта рекомендуется выбрать **Web application**, так как backend работает через uvicorn.

#### Шаг 2: Настройте Web application

После выбора **Web application** появятся дополнительные поля:

**Name:**
Впишите: `Photo Gallery Web`

**Authorized JavaScript origins:**
Нажмите **"+ Add URI"** и добавьте:
```
https://gallery.fatbox.org
```

**Authorized redirect URIs:**
Нажмите **"+ Add URI"** и добавьте:
```
https://gallery.fatbox.org/api/settings/google-drive/oauth/callback
```

⚠️ **Важно:** 
- Используйте точный домен вашего приложения
- Обязательно используйте **https://** (не http://)
- Redirect URI должен совпадать с endpoint в вашем backend
- Домены будут автоматически добавлены в OAuth consent screen как authorized domains

#### Шаг 3: Создайте клиент

Нажмите **"Create"** в нижней части страницы.

⚠️ **Примечание:** Изменения могут вступить в силу через 5 минут - несколько часов.

---

## Шаг 1.7: Добавьте Test Users

После создания OAuth Client вы увидите ошибку при попытке авторизации:

```
Ошибка 403: access_denied
Мы пока не проверили приложение "fatbox.org"
```

Это происходит потому, что OAuth consent screen находится в режиме **Testing**, и только добавленные тест-пользователи могут авторизоваться.

### Как добавить Test Users:

1. В левом меню перейдите: **Google Auth Platform** → **Audience**
2. На странице **Audience** прокрутите вниз до раздела **"Test users"**
3. Нажмите **"+ Add users"**
4. Откроется боковая панель **"Add users"** справа
5. В текстовое поле введите Gmail адреса пользователей (по одному на строку):
   ```
   your-email@gmail.com
   another-user@gmail.com
   ```
6. Счетчик покажет: `0 / 100` (максимум 100 пользователей)
7. Нажмите **"Save"**

⚠️ **Важно:**
- **Publishing status: Testing** — только тест-пользователи могут авторизоваться
- **OAuth user cap:** максимум 100 тест-пользователей
- Счетчик считается на протяжении всей жизни приложения
- Для публичного доступа нажмите **"Publish app"** (требует верификации Google)

### 1.7 Скачайте credentials

После создания появится окно с Client ID и Secret.

1. Нажмите **"Download JSON"**
2. Переименуйте файл в `oauth_credentials.json`
3. Переместите в папку `backend/`:
   ```
   gallery/backend/oauth_credentials.json
   ```

**⚠️ ВАЖНО:** Файл содержит секретные данные. НЕ коммитьте в Git!

---

## Шаг 2: Создание корневой папки на Google Drive

1. Откройте [Google Drive](https://drive.google.com)
2. Создайте папку: **"PhotoGalleryStorage"**
3. Скопируйте ID папки из URL:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                           ^^^^^^^^^^^^^^^^^^^^
                                           Это ID папки
   ```

---

## Шаг 3: Настройка Backend

Обновите файл `backend/.env`:

```env
# Storage
STORAGE_TYPE=google_drive_oauth

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
```

Замените `1a2b3c4d5e6f7g8h9i0j` на ID вашей папки.

---

## Шаг 4: Первый запуск (OAuth Flow)

### 4.1 Запустите backend

```bash
cd backend
uvicorn main:app --reload
```

При первом запуске откроется браузер с запросом авторизации.

### 4.2 Авторизуйтесь

1. Выберите ваш Google аккаунт
2. Google покажет предупреждение "Google hasn't verified this app"
   - Нажмите **"Advanced"**
   - Нажмите **"Go to Photo Gallery (unsafe)"**
3. Разрешите доступ к Google Drive
4. Нажмите **"Allow"**

### 4.3 Токены сохранены

В папке `backend/` появится файл `token.json`:

```
backend/
├── oauth_credentials.json  (OAuth секреты)
└── token.json             (Access & refresh токены)
```

**⚠️ ВАЖНО:** Оба файла добавлены в `.gitignore`.

---

## Шаг 5: Проверка работы

### Тест: Загрузка фото

1. Откройте приложение: http://localhost:5173
2. Войдите в систему
3. Создайте альбом
4. Загрузите фото

### Проверка в Google Drive

Откройте папку `PhotoGalleryStorage` на вашем Drive:

```
PhotoGalleryStorage/
├── album_1/
│   ├── uuid_photo1.jpg
│   └── uuid_photo2.jpg
└── album_2/
    └── uuid_photo3.jpg
```

---

## Структура хранилища

**Упрощенная структура (без папок пользователей):**

```
PhotoGalleryStorage/
├── album_1/    ← Все альбомы в одной корневой папке
├── album_2/
├── album_3/
└── album_N/
```

Связь "пользователь → альбом" хранится в базе данных PostgreSQL/SQLite.

---

## Автоматическое обновление токенов

Google OAuth токены действительны **1 час**.

Сервис автоматически обновляет их с помощью `refresh_token`:

```python
if self.creds.expired and self.creds.refresh_token:
    self.creds.refresh(Request())
```

**Refresh token** действителен бессрочно (пока не отозвали доступ).

---

## Квоты и лимиты

### Бесплатный план Google Drive:

- **Storage:** 15 ГБ (общий с Gmail и Google Photos)
- **API Queries:** 1,000,000,000 queries/day
- **Upload:** 750 GB/day

### Примерные расчеты:

| Размер фото | Кол-во фото в 15 ГБ |
|-------------|---------------------|
| 1 МБ        | ~15,000             |
| 3 МБ        | ~5,000              |
| 5 МБ        | ~3,000              |

---

## Безопасность

### ✅ Правильно:

- OAuth credentials только на сервере
- `oauth_credentials.json` и `token.json` в `.gitignore`
- Scope ограничен: `drive.file` (только файлы приложения)
- Фото не публичные

### ❌ Неправильно:

- ❌ Публичные ссылки на файлы Drive
- ❌ OAuth credentials в коде
- ❌ Scope `drive` (полный доступ ко всему Drive)

---

## Troubleshooting

### Ошибка: "File oauth_credentials.json not found"

**Решение:**
1. Проверьте наличие файла в `backend/oauth_credentials.json`
2. Убедитесь, что скачали его из Google Cloud Console
3. Переименуйте из `client_secret_*.json` в `oauth_credentials.json`

### Ошибка: "invalid_grant"

**Причина:** Токены устарели или отозваны

**Решение:**
1. Удалите `backend/token.json`
2. Перезапустите backend
3. Пройдите OAuth flow заново

### Ошибка: "Access blocked: This app's request is invalid"

**Причина:** Не настроен OAuth Consent Screen

**Решение:**
1. Вернитесь к Шагу 1.3
2. Заполните все обязательные поля
3. Добавьте ваш email в Test Users

### Предупреждение: "Google hasn't verified this app"

**Это нормально для личных приложений!**

Нажмите "Advanced" → "Go to Photo Gallery (unsafe)"

Для production нужно:
1. Верифицировать приложение в Google
2. Или перейти на Service Account + Shared Drive

---

## Миграция с Service Account

Если вы уже настроили Service Account (из `03-google-drive-setup.md`):

### Что меняется:

| Service Account | OAuth 2.0 |
|----------------|-----------|
| `service-account.json` | `oauth_credentials.json` + `token.json` |
| 15 ГБ Service Account (нет) | 15 ГБ личный Drive |
| Работает с Shared Drive | Работает с личным Drive |
| Не требует браузера | Требует первую авторизацию |

### Шаги миграции:

1. Измените `.env`: `STORAGE_TYPE=google_drive_oauth`
2. Скачайте OAuth credentials (Шаг 1)
3. Создайте новую папку на личном Drive (Шаг 2)
4. Запустите backend и авторизуйтесь (Шаг 4)

**Фото не мигрируют автоматически** — старые файлы останутся в Service Account папке.

---

## Когда пора переходить на платное хранилище?

Переходите на AWS S3 / Cloudflare R2 / Backblaze B2, если:

- ✅ Фото занимают > 10 ГБ
- ✅ Более 100 активных пользователей
- ✅ Нужен production SLA
- ✅ Нужна CDN для быстрой загрузки

Для MVP и тестирования OAuth + Google Drive — **отличный бесплатный старт**.

---

## Полезные ссылки

- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API Scopes](https://developers.google.com/drive/api/guides/api-specific-auth)
