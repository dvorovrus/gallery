from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Setup Google Service Account credentials from environment variable
google_creds = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
if google_creds:
    try:
        # Write credentials to /tmp for Google API client
        with open('/tmp/service-account.json', 'w') as f:
            f.write(google_creds)
        # Update environment to point to the temp file
        os.environ['GOOGLE_CREDENTIALS_PATH'] = '/tmp/service-account.json'
    except Exception as e:
        print(f"Warning: Failed to setup Google credentials: {e}")

from app.api import auth, albums, photos, share, admin
from app.core.config import get_settings
from app.core.database import Base, engine
from sqlalchemy import inspect, text

settings = get_settings()
Base.metadata.create_all(bind=engine)


def ensure_schema_updates():
    inspector = inspect(engine)

    if "photos" in inspector.get_table_names():
        photo_columns = {column["name"] for column in inspector.get_columns("photos")}
        if "thumbnail_file_id" not in photo_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE photos ADD COLUMN thumbnail_file_id VARCHAR"))


ensure_schema_updates()

app = FastAPI(title="Gallery API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for direct FastAPI paths and Vercel /api rewrites.
app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(photos.router)
app.include_router(share.router)
app.include_router(admin.router)
app.include_router(auth.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(photos.router, prefix="/api")
app.include_router(share.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Gallery API"}

@app.get("/healthz")
@app.get("/api/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/geo")
def geo(request: Request):
    country = request.headers.get("x-vercel-ip-country") or request.headers.get("cf-ipcountry")
    return {"country": country.upper() if country else None}
