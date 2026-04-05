"""
Equilibria Backend - FastAPI Entry Point
Spesifikasi Teknis v2 - Bagian 1.3, 7
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.logging_config import get_loggers, setup_logging
from app.db.session import init_db

# Inisialisasi logging pada startup
system_logger, assessment_logger = get_loggers()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manajer siklus hidup aplikasi untuk startup/shutdown events.
    """
    # Startup
    system_logger.info(
        f"Memulai {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={
            "event_type": "APP_STARTUP",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
    )
    
    # Inisialisasi database
    await init_db()
    
    system_logger.info(
        "Proses startup aplikasi selesai",
        extra={"event_type": "APP_STARTUP_COMPLETE"}
    )
    
    yield
    
    # Shutdown
    system_logger.info(
        "Aplikasi sedang shutdown",
        extra={"event_type": "APP_SHUTDOWN"}
    )


# Buat aplikasi FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Sistem Penilaian Adaptif Kolaboratif dengan Mitigasi Overpersonalisasi",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Konfigurasi CORS (Spesifikasi Teknis Bagian 2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
from app.api.router import api_router
app.include_router(api_router, prefix="/api", tags=["API"])

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint health check untuk monitoring.
    Spesifikasi Teknis v2 - Bagian 7.2
    """
    system_logger.debug(
        "Permintaan health check",
        extra={"event_type": "HEALTH_CHECK"}
    )
    return {
        "status": "sehat",
        "service": "equilibria-backend",
        "version": settings.APP_VERSION
    }


# Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint root dengan info API.
    """
    return {
        "message": "Selamat datang di Equilibria API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "spesifikasi": "Spesifikasi Teknis v2.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )