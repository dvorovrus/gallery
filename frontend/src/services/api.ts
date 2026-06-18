import type { Album, AuthTokens, Photo, User, GoogleDriveSettings, GoogleDriveTestResponse, UserInfo } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

let authToken: string | null = localStorage.getItem('auth_token');

export const setAuthToken = (token: string) => {
  authToken = token;
  localStorage.setItem('auth_token', token);
};

export const clearAuthToken = () => {
  authToken = null;
  localStorage.removeItem('auth_token');
};

const getHeaders = () => ({
  'Content-Type': 'application/json',
  ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
});

const getAuthOnlyHeaders = () => ({
  ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
});

const requestJson = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Keep the status-based fallback when the server returns a non-JSON error.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
};

const requestVoid = async (path: string, init: RequestInit = {}): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Keep the status-based fallback when the server returns a non-JSON error.
    }
    throw new Error(message);
  }
};

const requestBlob = async (path: string, init: RequestInit = {}): Promise<Response> => {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Keep the status-based fallback when the server returns a non-JSON error.
    }
    throw new Error(message);
  }
  return response;
};

const triggerBlobDownload = (blob: Blob, filename: string) => {
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
};

const getFilenameFromDisposition = (disposition: string | null) => {
  if (!disposition) return null;

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const basicMatch = disposition.match(/filename="([^"]+)"/i);
  return basicMatch?.[1] || null;
};

// Auth
export const login = async (email: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  if (!response.ok) throw new Error('Login failed');

  const data = (await response.json()) as AuthTokens;
  setAuthToken(data.access_token);
  return data;
};

export const register = async (email: string, password: string) => {
  return requestJson<User>('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
};

// Albums
export const getAlbums = async () => {
  return requestJson<Album[]>('/albums', {
    headers: getHeaders(),
  });
};

export const createAlbum = async (title: string, expirationType: string = 'unlimited') => {
  return requestJson<Album>('/albums', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ title, expiration_type: expirationType }),
  });
};

export const deleteAlbum = async (albumId: number) => {
  return requestVoid(`/albums/${albumId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
};

// Photos
export const getPhotos = async (albumId: number) => {
  return requestJson<Photo[]>(`/albums/${albumId}/photos`, {
    headers: getHeaders(),
  });
};

export const uploadPhoto = async (albumId: number, file: File, caption?: string) => {
  const formData = new FormData();
  formData.append('files', file);
  if (caption) formData.append('caption', caption);

  return requestJson<Photo[]>(`/albums/${albumId}/photos`, {
    method: 'POST',
    headers: {
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });
};

export const uploadPhotos = async (albumId: number, files: File[], caption?: string) => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  if (caption) formData.append('caption', caption);

  return requestJson<Photo[]>(`/albums/${albumId}/photos`, {
    method: 'POST',
    headers: {
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });
};

export const deletePhoto = async (photoId: number) => {
  return requestVoid(`/photos/${photoId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
};

export const batchDeletePhotos = async (photoIds: number[]) => {
  return requestVoid('/photos/batch-delete', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ photo_ids: photoIds }),
  });
};

export const downloadPhoto = async (photoId: number, fallbackName: string) => {
  const response = await requestBlob(`/photos/${photoId}/download`, {
    headers: getAuthOnlyHeaders(),
  });

  const blob = await response.blob();
  const matchedName = getFilenameFromDisposition(response.headers.get('Content-Disposition'));
  triggerBlobDownload(blob, matchedName || fallbackName);
};

export const downloadAlbum = async (albumId: number, fallbackName: string) => {
  const response = await requestBlob(`/albums/${albumId}/download`, {
    headers: getAuthOnlyHeaders(),
  });

  const blob = await response.blob();
  const matchedName = getFilenameFromDisposition(response.headers.get('Content-Disposition'));
  triggerBlobDownload(blob, matchedName || fallbackName);
};

// Settings
export const getSettings = async () => {
  return requestJson<GoogleDriveSettings>('/settings', {
    headers: getHeaders(),
  });
};

export const configureGoogleDrive = async (folderId: string, serviceAccountFile: File) => {
  const formData = new FormData();
  formData.append('folder_id', folderId);
  formData.append('service_account_file', serviceAccountFile);

  const response = await fetch(`${API_BASE_URL}/settings/google-drive`, {
    method: 'POST',
    headers: getAuthOnlyHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to configure Google Drive');
  }

  return response.json();
};

export const testGoogleDriveConnection = async () => {
  return requestJson<GoogleDriveTestResponse>('/settings/google-drive/test', {
    method: 'POST',
    headers: getHeaders(),
  });
};

export const removeGoogleDriveConfig = async () => {
  return requestVoid('/settings/google-drive', {
    method: 'DELETE',
    headers: getHeaders(),
  });
};

// Admin Management
export const getAllUsers = async () => {
  return requestJson<UserInfo[]>('/admins', {
    headers: getHeaders(),
  });
};

export const updateUserRole = async (userId: number, role: string) => {
  return requestJson('/admins/update-role', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ user_id: userId, role }),
  });
};

export const deleteUser = async (userId: number) => {
  return requestVoid(`/admins/${userId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
};
