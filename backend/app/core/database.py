from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import os

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("libsql://"):
    turso_auth_token = os.environ.get("TURSO_AUTH_TOKEN") or settings.TURSO_AUTH_TOKEN
    turso_host = SQLALCHEMY_DATABASE_URL.removeprefix("libsql://").rstrip("/")
    SQLALCHEMY_DATABASE_URL = f"sqlite+libsql://{turso_host}/?secure=true"
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "auth_token": turso_auth_token,
    }
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
