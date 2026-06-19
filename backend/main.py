from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import Base, engine
from app.api import auth, albums, photos, share, admin
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

# Include routers. Routes монтируются дважды — без префикса и с /api —
# чтобы локальная разработка (vite proxy) и production (vercel: только /api/*
# направляется в функцию) были консистентны. См. src/index.py.
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
@app.get("/api")
def root():
    return {
        "message": "Gallery API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
@app.get("/healthz")
@app.get("/api/health")
@app.get("/api/healthz")
def health_check():
    return {"status": "healthy"}


@app.get("/api/geo")
@app.get("/geo")
def geo(request: Request):
    country = request.headers.get("x-vercel-ip-country") or request.headers.get("cf-ipcountry")
    return {"country": country.upper() if country else None}
