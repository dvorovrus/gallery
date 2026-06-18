from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
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

settings = get_settings()

app = FastAPI(title="Gallery API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(albums.router, prefix="/albums", tags=["albums"])
app.include_router(photos.router, prefix="/photos", tags=["photos"])
app.include_router(photos.router, tags=["photos"])
app.include_router(share.router, prefix="/share", tags=["share"])
app.include_router(admin.router, tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Gallery API"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Handler for Vercel
handler = Mangum(app)
