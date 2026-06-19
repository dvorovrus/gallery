import logging
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)

_INSECURE_SECRET_PLACEHOLDER = "dev-secret-key-change-this"


class Settings(BaseSettings):
    # Runtime environment
    ENVIRONMENT: str = "development"  # "development" or "production"

    # Database
    DATABASE_URL: str = "sqlite:///./gallery.db"
    TURSO_AUTH_TOKEN: str = ""

    # JWT
    SECRET_KEY: str = _INSECURE_SECRET_PLACEHOLDER
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Storage
    STORAGE_TYPE: str = "google_drive"  # "local", "google_drive" or "google_drive_oauth"

    # Google Drive (optional, только если STORAGE_TYPE="google_drive" или "google_drive_oauth")
    GOOGLE_CREDENTIALS_PATH: str = ""
    GOOGLE_DRIVE_FOLDER_ID: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Vercel Cron / internal endpoints shared secret.
    # When set, cron-triggered cleanup requires header X-Cron-Secret: <value>.
    CRON_SECRET: str = ""

    # Lifetime (minutes) of signed media-access tokens used to authorize
    # binary photo/thumbnail downloads (e.g. inside <img src>).
    MEDIA_TOKEN_EXPIRE_MINUTES: int = 120

    # Upload limits
    MAX_PHOTO_UPLOAD_BYTES: int = 30 * 1024 * 1024  # 30 MiB per file

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        is_default = self.SECRET_KEY == _INSECURE_SECRET_PLACEHOLDER
        is_weak = (
            len(self.SECRET_KEY) < 32
            or self.SECRET_KEY.startswith(("dev-", "change", "changeme", "secret"))
        )
        if self.ENVIRONMENT == "production":
            if is_default:
                raise ValueError(
                    "SECRET_KEY must be set to a strong random value in production "
                    "(generate with: openssl rand -base64 32)."
                )
            if is_weak:
                raise ValueError(
                    "SECRET_KEY is too weak for production: use at least 32 random characters."
                )
        elif is_default or is_weak:
            logger.warning(
                "SECRET_KEY is using a weak/default value — JWTs are insecure. "
                "Set a strong SECRET_KEY before exposing the service."
            )
        return self

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
