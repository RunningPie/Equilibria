"""
Database Session Management
Technical Specifications v2 - Section 3.1
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text  # <--- TAMBAHKAN IMPORT INI!
from app.core.config import settings
from app.core.logging_config import get_loggers

system_logger, _ = get_loggers()

# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI routes to get database session.
    Ensures proper session cleanup after each request.
    """
    db = AsyncSessionLocal()
    try:
        yield db
        await db.commit()
    except Exception as e:
        await db.rollback()
        system_logger.error(
            f"Database session error: {str(e)}",
            extra={"event_type": "DB_SESSION_ERROR"}
        )
        raise
    finally:
        await db.close()


async def init_db():
    """
    Initialize database connection on startup.
    Technical Specifications v2 - Section 3.1
    """
    try:
        async with engine.connect() as conn:
            # TAMBAHKAN text() wrapper untuk raw SQL
            await conn.execute(text("SELECT 1"))
            await conn.commit()  # Pastikan commit untuk async
        
        system_logger.info(
            "Database connection initialized successfully",
            extra={"event_type": "DB_INIT_SUCCESS"}
        )
    except Exception as e:
        system_logger.error(
            f"Database connection failed: {str(e)}",
            extra={"event_type": "DB_INIT_FAILED"}
        )
        raise