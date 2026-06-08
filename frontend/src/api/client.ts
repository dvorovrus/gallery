import axios from 'axios';
import type { Album, Photo, User, AuthTokens, ShareLink } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: (email: string, password: string) =>
    api.post<User>('/auth/register', { email, password }),

  login: (email: string, password: string) =>
    api.post<AuthTokens>('/auth/login', {
      username: email,
      password
    }, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),

  getCurrentUser: () => api.get<User>('/auth/me'),
};

// Albums API
export const albumsAPI = {
  getAll: () => api.get<Album[]>('/albums'),

  create: (name: string) => api.post<Album>('/albums', { title: name }),

  delete: (id: string) => api.delete(`/albums/${id}`),
};

// Photos API
export const photosAPI = {
  getByAlbum: (albumId: string) =>
    api.get<Photo[]>(`/albums/${albumId}/photos`),

  upload: (albumId: string, files: File[], caption?: string, date?: string) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (caption) formData.append('caption', caption);
    if (date) formData.append('date', date);

    return api.post<Photo[]>(`/albums/${albumId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: (photoId: string) => api.delete(`/photos/${photoId}`),

  getUrl: (photoId: string) => `${API_BASE_URL}/photos/${photoId}`,
};

// Share API
export const shareAPI = {
  createAlbumShare: (albumId: string, password?: string) =>
    api.post<ShareLink>(`/albums/${albumId}/share`, { password }),

  createPhotoShare: (photoId: string, password?: string) =>
    api.post<ShareLink>(`/photos/${photoId}/share`, { password }),

  getSharedAlbum: (token: string, password?: string) =>
    api.get<{ album: Album; photos: Photo[] }>(`/share/${token}`, {
      params: { password },
    }),
};

export default api;
