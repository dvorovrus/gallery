export interface Album {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  is_public: boolean;
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
