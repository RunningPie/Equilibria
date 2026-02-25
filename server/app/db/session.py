from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from app.core.config import settings
from app.core.logging_config import get_loggers
from typing import AsyncGenerator, Optional
from sqlalchemy import select

logger = get_loggers()[0]  # Get system logger

class DatabaseSession:
    '''
    Singleton session manager
    
    mengelola async engine dan session factory, memastikan:
    1. Single DB instance (efisiensi)
    2. Pooling yang terkonfigurasi
    3. Proper cleanup
    '''
    
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        '''
        Get or create engine
        
        Config connection pool:
        - Pool size: 20 (default)
        - max overflow: 10 (default)
        - pool_pre_ping: True (cek koneksi sebelum dipakai)
        - pool_recycly: 3600 (gunakan kembali koneksi setelah 1 jam)
        '''
        
        if cls._engine is None:
            logger.info(
                "Creating new database engine",
                extra={"event_type": "DB_ENGINE_INIT"}
            )
            cls._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.LOG_LEVEL == "DEBUG",  # log hanya di debug mode
                poolclass=AsyncAdaptedQueuePool,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30
            )
            
            logger.info(
                "Database engine created",
                extra={"event_type": "DB_ENGINE_CREATED"}
            )
        return cls._engine
    
    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        '''
        Get or create session factory
        '''
        if cls._session_factory is None:
            logger.info(
                "Creating new session factory",
                extra={"event_type": "DB_SESSION_FACTORY_INIT"}
            )
            cls._session_factory = async_sessionmaker(
                bind=cls.get_engine(),
                expire_on_commit=False,
                class_=AsyncSession
            )
            logger.info(
                "Session factory created",
                extra={"event_type": "DB_SESSION_FACTORY_CREATED"}
            )
        return cls._session_factory
    
    @classmethod
    async def close(cls) -> None:
        '''
        Close engine and cleanup
        '''
        if cls._engine is not None:
            logger.info(
                "Closing database engine",
                extra={"event_type": "DB_ENGINE_CLOSE"}
            )
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info(
                "Database engine closed",
                extra={"event_type": "DB_ENGINE_CLOSED"}
            )
    
# ===== Deps Injection =====
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    '''
    Dependency untuk FastAPI routes
    
    Usage:
    async def some_route(db: AsyncSession = Depends(get_db)):
        ...
    '''
    session_factory = DatabaseSession.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(
                f"Database session error: {str(e)}",
                extra={"event_type": "DB_SESSION_ERROR"}
            )
            raise
        finally:
            await session.close()

# === Helpers ===
async def init_db():
    '''
    Init db connn on startup
    
    Panggil untuk:
    1. pre-warming
    2. validasi koneksi
    3. log status awal
    '''
    try:
        engine = DatabaseSession.get_engine()
        async with engine.connect() as conn:
            await conn.execute(select(1))  # ✅ Gunakan select() dari SQLAlchemy
            await conn.commit()
        logger.info(
            "Database connection initialized successfully",
            extra={"event_type": "DB_CONNECTION_INIT_SUCCESS"}
        )
    except Exception as e:
        logger.error(
            f"Database connection initialization failed: {str(e)}",
            extra={"event_type": "DB_CONNECTION_INIT_ERROR"}
        )
        raise