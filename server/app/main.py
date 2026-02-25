"""
Equilibria Backend - FastAPI Entry Point
Technical Specifications v2 - Section 1.3, 7
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.logging_config import get_loggers, setup_logging
from app.db.session import init_db

# Initialize logging on startup
system_logger, assessment_logger = get_loggers()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.
    """
    # Startup
    system_logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={
            "event_type": "APP_STARTUP",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
    )
    
    # Initialize database
    await init_db()
    
    system_logger.info(
        "Application startup complete",
        extra={"event_type": "APP_STARTUP_COMPLETE"}
    )
    
    yield
    
    # Shutdown
    system_logger.info(
        "Application shutting down",
        extra={"event_type": "APP_SHUTDOWN"}
    )


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Collaborative Adaptive Assessment System with Overpersonalization Mitigation",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration (Technical Specs Section 2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
from app.api import api_router
app.include_router(api_router, prefix="/api", tags=["API"])

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Technical Specifications v2 - Section 7.2
    """
    system_logger.debug(
        "Health check requested",
        extra={"event_type": "HEALTH_CHECK"}
    )
    return {
        "status": "healthy",
        "service": "equilibria-backend",
        "version": settings.APP_VERSION
    }


# Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to Equilibria API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "specifications": "Technical Specifications v2.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )