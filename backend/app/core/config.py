from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./gallery.db"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Storage
    STORAGE_TYPE: str = "google_drive"  # "local", "google_drive" or "google_drive_oauth"

    # Google Drive (optional, только если STORAGE_TYPE="google_drive" или "google_drive_oauth")
    GOOGLE_CREDENTIALS_PATH: str = ""
    GOOGLE_DRIVE_FOLDER_ID: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
