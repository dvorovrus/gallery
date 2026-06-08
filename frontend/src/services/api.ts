const API_BASE_URL = 'http://localhost:8000';

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

  const data = await response.json();
  setAuthToken(data.access_token);
  return data;
};

export const register = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) throw new Error('Registration failed');
  return response.json();
};

// Albums
export const getAlbums = async () => {
  const response = await fetch(`${API_BASE_URL}/albums`, {
    headers: getHeaders(),
  });

  if (!response.ok) throw new Error('Failed to fetch albums');
  return response.json();
};

export const createAlbum = async (title: string) => {
  const response = await fetch(`${API_BASE_URL}/albums`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ title }),
  });

  if (!response.ok) throw new Error('Failed to create album');
  return response.json();
};

export const deleteAlbum = async (albumId: number) => {
  const response = await fetch(`${API_BASE_URL}/albums/${albumId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) throw new Error('Failed to delete album');
};

// Photos
export const getPhotos = async (albumId: number) => {
  const response = await fetch(`${API_BASE_URL}/albums/${albumId}/photos`, {
    headers: getHeaders(),
  });

  if (!response.ok) throw new Error('Failed to fetch photos');
  return response.json();
};

export const uploadPhoto = async (albumId: number, file: File, caption?: string) => {
  const formData = new FormData();
  formData.append('files', file);
  if (caption) formData.append('caption', caption);

  const response = await fetch(`${API_BASE_URL}/albums/${albumId}/photos`, {
    method: 'POST',
    headers: {
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) throw new Error('Failed to upload photo');
  return response.json();
};

export const uploadPhotos = async (albumId: number, files: File[], caption?: string) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  if (caption) formData.append('caption', caption);

  const response = await fetch(`${API_BASE_URL}/albums/${albumId}/photos`, {
    method: 'POST',
    headers: {
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) throw new Error('Failed to upload photos');
  return response.json();
};

export const deletePhoto = async (photoId: number) => {
  const response = await fetch(`${API_BASE_URL}/photos/${photoId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) throw new Error('Failed to delete photo');
};

export const batchDeletePhotos = async (photoIds: number[]) => {
  const response = await fetch(`${API_BASE_URL}/photos/batch-delete`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ photo_ids: photoIds }),
  });

  if (!response.ok) throw new Error('Failed to batch delete photos');
};

export const downloadPhoto = async (photoId: number, fallbackName: string) => {
  const response = await fetch(`${API_BASE_URL}/photos/${photoId}/download`, {
    headers: getAuthOnlyHeaders(),
  });

  if (!response.ok) throw new Error('Failed to download photo');

  const blob = await response.blob();
  const matchedName = getFilenameFromDisposition(response.headers.get('Content-Disposition'));
  triggerBlobDownload(blob, matchedName || fallbackName);
};

export const downloadAlbum = async (albumId: number, fallbackName: string) => {
  const response = await fetch(`${API_BASE_URL}/albums/${albumId}/download`, {
    headers: getAuthOnlyHeaders(),
  });

  if (!response.ok) throw new Error('Failed to download album');

  const blob = await response.blob();
  const matchedName = getFilenameFromDisposition(response.headers.get('Content-Disposition'));
  triggerBlobDownload(blob, matchedName || fallbackName);
};
