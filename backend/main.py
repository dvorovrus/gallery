from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import Base, engine
from app.api import auth, albums, photos, share
from app.services.scheduler import album_scheduler

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup: Start the scheduler
    album_scheduler.start()
    yield
    # Shutdown: Stop the scheduler
    album_scheduler.shutdown()


app = FastAPI(
    title="Gallery API",
    description="API for photo gallery application with Google Drive storage",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(photos.router)
app.include_router(share.router)

@app.get("/")
def root():
    return {
        "message": "Gallery API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
