export interface Album {
  id: string;
  name: string;
  user_id: number;
  created_at: string;
  is_public: boolean;
}

export interface Photo {
  id: string;
  album_id: string;
  drive_file_id: string;
  filename: string;
  caption: string;
  date: string;
  url?: string;
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
  id: string;
  album_id: string;
  token: string;
  password_required: boolean;
  expires_at: string | null;
  created_at: string;
}
