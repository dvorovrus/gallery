export interface Album {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  is_public: boolean;
  expiration_type: 'unlimited' | '7_days' | '14_days' | '30_days';
  expires_at: string | null;
  auto_delete_scheduled: boolean;
}

export interface Photo {
  id: number;
  album_id: number;
  drive_file_id: string;
  filename: string;
  caption: string | null;
  created_at: string;
  fullUrl?: string;
  thumbnailUrl?: string;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface ShareLink {
  id: number;
  album_id: number;
  token: string;
  password_required: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

export interface GoogleDriveSettings {
  google_drive_configured: boolean;
  google_drive_folder_id: string | null;
}

export interface GoogleDriveTestResponse {
  success: boolean;
  message: string;
  folder_name?: string;
  folder_id?: string;
  can_edit?: boolean;
}

export interface UserInfo {
  id: number;
  email: string;
  role: string;
  created_at: string;
}
