# Примеры использования

## Обзор

В этом документе представлены практические примеры использования Gallery API для различных сценариев.

## Содержание

- [Базовые операции](#базовые-операции)
- [Работа с альбомами](#работа-с-альбомами)
- [Загрузка и управление фото](#загрузка-и-управление-фото)
- [Публичный шаринг](#публичный-шаринг)
- [Frontend интеграция](#frontend-интеграция)
- [Продвинутые сценарии](#продвинутые-сценарии)

---

## Базовые операции

### Пример 1: Регистрация и вход

```javascript
// JavaScript / Fetch API
async function registerAndLogin() {
  // 1. Регистрация
  const registerResponse = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'user@example.com',
      password: 'SecurePass123!'
    })
  });

  if (!registerResponse.ok) {
    const error = await registerResponse.json();
    throw new Error(error.detail);
  }

  const user = await registerResponse.json();
  console.log('User registered:', user);

  // 2. Вход
  const formData = new URLSearchParams();
  formData.append('username', 'user@example.com');
  formData.append('password', 'SecurePass123!');

  const loginResponse = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData
  });

  const { access_token } = await loginResponse.json();
  
  // Сохранить токен
  localStorage.setItem('access_token', access_token);
  
  return access_token;
}

// Использование
registerAndLogin()
  .then(token => console.log('Logged in!', token))
  .catch(err => console.error('Error:', err));
```

### Пример 2: Python клиент

```python
import requests

class GalleryClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def register(self, email, password):
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return self.token

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_albums(self):
        response = requests.get(
            f"{self.base_url}/albums",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Использование
client = GalleryClient()
client.register("user@example.com", "password123")
client.login("user@example.com", "password123")
albums = client.get_albums()
print(f"Found {len(albums)} albums")
```

---

## Работа с альбомами

### Пример 3: Создание альбома

```javascript
async function createAlbum(title) {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/albums', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ title })
  });

  if (!response.ok) {
    throw new Error('Failed to create album');
  }

  return await response.json();
}

// Использование
createAlbum('Отпуск 2026').then(album => {
  console.log('Album created:', album);
  // { id: 1, title: "Отпуск 2026", user_id: 1, ... }
});
```

### Пример 4: Получение списка альбомов с количеством фото

```javascript
async function getAlbumsWithPhotoCounts() {
  const token = localStorage.getItem('access_token');

  // Получить все альбомы
  const albumsResponse = await fetch('http://localhost:8000/albums', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const albums = await albumsResponse.json();

  // Для каждого альбома получить количество фото
  const albumsWithCounts = await Promise.all(
    albums.map(async (album) => {
      const photosResponse = await fetch(
        `http://localhost:8000/albums/${album.id}/photos`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const photos = await photosResponse.json();

      return {
        ...album,
        photoCount: photos.length
      };
    })
  );

  return albumsWithCounts;
}

// Использование
getAlbumsWithPhotoCounts().then(albums => {
  albums.forEach(album => {
    console.log(`${album.title}: ${album.photoCount} photos`);
  });
});
```

### Пример 5: Удаление альбома

```javascript
async function deleteAlbum(albumId) {
  const token = localStorage.getItem('access_token');

  const confirmed = confirm(
    'Вы уверены? Все фотографии в альбоме будут удалены.'
  );

  if (!confirmed) return;

  const response = await fetch(`http://localhost:8000/albums/${albumId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (response.status === 204) {
    console.log('Album deleted successfully');
    return true;
  }

  throw new Error('Failed to delete album');
}
```

---

## Загрузка и управление фото

### Пример 6: Загрузка одного фото

```javascript
async function uploadPhoto(albumId, file, caption = '') {
  const token = localStorage.getItem('access_token');

  const formData = new FormData();
  formData.append('files', file);
  if (caption) {
    formData.append('caption', caption);
  }

  const response = await fetch(
    `http://localhost:8000/albums/${albumId}/photos`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    }
  );

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return await response.json();
}

// Использование с input file
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const albumId = 1;

  try {
    const photos = await uploadPhoto(albumId, file, 'Красивый закат');
    console.log('Photo uploaded:', photos[0]);
  } catch (error) {
    console.error('Upload error:', error);
  }
});
```

### Пример 7: Загрузка нескольких фото с прогрессом

```javascript
async function uploadMultiplePhotos(albumId, files, onProgress) {
  const token = localStorage.getItem('access_token');

  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        onProgress(percentComplete);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status === 201) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error('Upload failed'));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Network error')));

    xhr.open('POST', `http://localhost:8000/albums/${albumId}/photos`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.send(formData);
  });
}

// Использование
const files = Array.from(document.getElementById('multiFileInput').files);
uploadMultiplePhotos(1, files, (progress) => {
  console.log(`Upload progress: ${progress.toFixed(1)}%`);
  document.getElementById('progressBar').style.width = `${progress}%`;
}).then(photos => {
  console.log(`Successfully uploaded ${photos.length} photos`);
});
```

### Пример 8: Получение фото с кэшированием

```javascript
class PhotoCache {
  constructor() {
    this.cache = new Map();
  }

  async getPhoto(photoId) {
    // Проверить кэш
    if (this.cache.has(photoId)) {
      return this.cache.get(photoId);
    }

    // Загрузить с сервера
    const response = await fetch(`http://localhost:8000/photos/${photoId}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    // Сохранить в кэш
    this.cache.set(photoId, url);

    return url;
  }

  clearCache() {
    this.cache.forEach(url => URL.revokeObjectURL(url));
    this.cache.clear();
  }
}

// Использование
const photoCache = new PhotoCache();

async function displayPhoto(photoId) {
  const url = await photoCache.getPhoto(photoId);
  document.getElementById('photoImg').src = url;
}
```

### Пример 9: Удаление фото

```javascript
async function deletePhoto(photoId) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`http://localhost:8000/photos/${photoId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  return response.status === 204;
}
```

---

## Публичный шаринг

### Пример 10: Создание публичной ссылки

```javascript
async function shareAlbum(albumId, password = null) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(
    `http://localhost:8000/albums/${albumId}/share`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ password })
    }
  );

  const share = await response.json();
  const shareUrl = `${window.location.origin}/share/${share.token}`;

  return {
    url: shareUrl,
    token: share.token,
    passwordRequired: share.password_required
  };
}

// Использование
shareAlbum(1, 'secret123').then(share => {
  console.log('Share URL:', share.url);
  // Копировать в буфер обмена
  navigator.clipboard.writeText(share.url);
});
```

### Пример 11: Просмотр публичного альбома

```javascript
async function viewSharedAlbum(token, password = null) {
  const url = new URL(`http://localhost:8000/share/${token}`);
  if (password) {
    url.searchParams.append('password', password);
  }

  const response = await fetch(url);

  if (response.status === 401) {
    // Требуется пароль
    const password = prompt('Введите пароль для доступа к альбому:');
    if (password) {
      return viewSharedAlbum(token, password);
    }
    throw new Error('Password required');
  }

  if (!response.ok) {
    throw new Error('Failed to load shared album');
  }

  const { album, photos } = await response.json();

  return { album, photos };
}

// Использование
const token = new URLSearchParams(window.location.search).get('token');
viewSharedAlbum(token).then(({ album, photos }) => {
  console.log(`Album: ${album.title}`);
  console.log(`Photos: ${photos.length}`);
  
  // Отобразить фото
  photos.forEach(photo => {
    const img = document.createElement('img');
    img.src = `http://localhost:8000/photos/${photo.id}`;
    document.getElementById('gallery').appendChild(img);
  });
});
```

---

## Frontend интеграция

### Пример 12: React Hook для альбомов

```typescript
// useAlbums.ts
import { useState, useEffect } from 'react';
import { albumsAPI } from '@/api/client';
import type { Album } from '@/types';

export function useAlbums() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAlbums = async () => {
    try {
      setLoading(true);
      const response = await albumsAPI.getAll();
      setAlbums(response.data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  const createAlbum = async (title: string) => {
    const response = await albumsAPI.create(title);
    setAlbums([...albums, response.data]);
    return response.data;
  };

  const deleteAlbum = async (id: string) => {
    await albumsAPI.delete(id);
    setAlbums(albums.filter(a => a.id !== id));
  };

  useEffect(() => {
    fetchAlbums();
  }, []);

  return {
    albums,
    loading,
    error,
    createAlbum,
    deleteAlbum,
    refresh: fetchAlbums
  };
}

// Использование в компоненте
function AlbumList() {
  const { albums, loading, createAlbum, deleteAlbum } = useAlbums();

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {albums.map(album => (
        <div key={album.id}>
          <h3>{album.title}</h3>
          <button onClick={() => deleteAlbum(album.id)}>Delete</button>
        </div>
      ))}
      <button onClick={() => createAlbum('New Album')}>
        Create Album
      </button>
    </div>
  );
}
```

### Пример 13: Компонент загрузки фото

```typescript
// PhotoUploader.tsx
import { useState } from 'react';
import { photosAPI } from '@/api/client';

interface PhotoUploaderProps {
  albumId: string;
  onUploadComplete: () => void;
}

export function PhotoUploader({ albumId, onUploadComplete }: PhotoUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setUploading(true);
    setProgress(0);

    try {
      await photosAPI.upload(albumId, files);
      setProgress(100);
      onUploadComplete();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    } finally {
      setUploading(false);
      e.target.value = ''; // Reset input
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileChange}
        disabled={uploading}
      />
      {uploading && (
        <div className="progress-bar">
          <div style={{ width: `${progress}%` }}>{progress}%</div>
        </div>
      )}
    </div>
  );
}
```

---

## Продвинутые сценарии

### Пример 14: Batch операции

```javascript
// Массовое удаление фото
async function deleteMultiplePhotos(photoIds) {
  const token = localStorage.getItem('access_token');

  const promises = photoIds.map(id =>
    fetch(`http://localhost:8000/photos/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
  );

  const results = await Promise.allSettled(promises);

  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  return { succeeded, failed };
}

// Использование
deleteMultiplePhotos([1, 2, 3, 4, 5]).then(({ succeeded, failed }) => {
  console.log(`Deleted: ${succeeded}, Failed: ${failed}`);
});
```

### Пример 15: Сжатие изображений перед загрузкой

```javascript
async function compressImage(file, maxWidth = 1920, quality = 0.8) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        if (width > maxWidth) {
          height *= maxWidth / width;
          width = maxWidth;
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            resolve(new File([blob], file.name, {
              type: 'image/jpeg',
              lastModified: Date.now()
            }));
          },
          'image/jpeg',
          quality
        );
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// Использование
async function uploadWithCompression(albumId, file) {
  const compressed = await compressImage(file);
  console.log(`Original: ${file.size}, Compressed: ${compressed.size}`);
  return uploadPhoto(albumId, compressed);
}
```

### Пример 16: Infinite scroll для фото галереи

```javascript
class InfinitePhotoGallery {
  constructor(albumId, container) {
    this.albumId = albumId;
    this.container = container;
    this.photos = [];
    this.page = 0;
    this.pageSize = 20;
    this.loading = false;
    this.hasMore = true;

    this.setupScrollListener();
    this.loadMore();
  }

  setupScrollListener() {
    window.addEventListener('scroll', () => {
      if (this.loading || !this.hasMore) return;

      const scrollTop = window.pageYOffset;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;

      if (scrollTop + windowHeight >= documentHeight - 500) {
        this.loadMore();
      }
    });
  }

  async loadMore() {
    if (this.loading || !this.hasMore) return;

    this.loading = true;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/albums/${this.albumId}/photos`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const allPhotos = await response.json();

      const start = this.page * this.pageSize;
      const end = start + this.pageSize;
      const newPhotos = allPhotos.slice(start, end);

      if (newPhotos.length === 0) {
        this.hasMore = false;
        return;
      }

      this.photos.push(...newPhotos);
      this.renderPhotos(newPhotos);
      this.page++;

      if (end >= allPhotos.length) {
        this.hasMore = false;
      }
    } finally {
      this.loading = false;
    }
  }

  renderPhotos(photos) {
    photos.forEach(photo => {
      const img = document.createElement('img');
      img.src = `http://localhost:8000/photos/${photo.id}`;
      img.alt = photo.caption;
      img.loading = 'lazy';
      this.container.appendChild(img);
    });
  }
}

// Использование
const gallery = new InfinitePhotoGallery(1, document.getElementById('gallery'));
```

### Пример 17: Автоматическое обновление токена

```javascript
class AuthManager {
  constructor() {
    this.token = localStorage.getItem('access_token');
    this.refreshing = false;
  }

  async request(url, options = {}) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.token}`
    };

    let response = await fetch(url, options);

    if (response.status === 401) {
      // Token expired, refresh it
      await this.refreshToken();

      // Retry request
      options.headers['Authorization'] = `Bearer ${this.token}`;
      response = await fetch(url, options);
    }

    return response;
  }

  async refreshToken() {
    if (this.refreshing) {
      await this.refreshing;
      return;
    }

    this.refreshing = (async () => {
      const email = localStorage.getItem('user_email');
      const password = prompt('Session expired. Please re-enter your password:');

      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      const { access_token } = await response.json();
      this.token = access_token;
      localStorage.setItem('access_token', access_token);
    })();

    await this.refreshing;
    this.refreshing = false;
  }
}

// Использование
const authManager = new AuthManager();

async function getAlbums() {
  const response = await authManager.request('http://localhost:8000/albums');
  return response.json();
}
```

---

## Тестирование

### Пример 18: Unit тесты (Jest)

```javascript
// api.test.js
import { albumsAPI } from './client';

describe('Albums API', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  test('should fetch all albums', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 1, title: 'Album 1' },
          { id: 2, title: 'Album 2' }
        ])
      })
    );

    const response = await albumsAPI.getAll();
    expect(response.data).toHaveLength(2);
    expect(response.data[0].title).toBe('Album 1');
  });

  test('should create album', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ id: 3, title: 'New Album' })
      })
    );

    const response = await albumsAPI.create('New Album');
    expect(response.data.title).toBe('New Album');
  });
});
```

---

## Заключение

Эти примеры покрывают основные сценарии использования Gallery API. Для более сложных случаев обратитесь к:

- [API Reference](./02-api-reference.md) - полная документация API
- [Архитектура](./01-architecture.md) - общая архитектура системы
- Swagger UI: http://localhost:8000/docs - интерактивная документация
