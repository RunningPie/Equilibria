"""
Application Configuration Module
Technical Specifications v2 - Section 1.3, 2, 8
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All secrets must be set via environment, never hardcoded.
    """
    
    # ===========================================
    # PYDANTIC CONFIG
    # ===========================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # <--- TAMBAHKAN INI: Ignore extra env vars
    )
    
    # ===========================================
    # DATABASE CONFIGURATION
    # ===========================================
    DATABASE_URL: str
    DB_USER: str = "equilibria_user"
    DB_PASSWORD: str = "secure_password"
    DB_NAME: str = "equilibria_db"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    
    # ===========================================
    # SECURITY CONFIGURATION
    # ===========================================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"  # <--- Nama field harus match dengan env var prefix
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ===========================================
    # SANDBOX CONFIGURATION
    # ===========================================
    SANDBOX_DB_ROLE: str = "sandbox_executor"
    SANDBOX_QUERY_TIMEOUT: int = 5000  # milliseconds
    
    # ===========================================
    # LOGGING CONFIGURATION
    # ===========================================
    LOG_DIR: str = "/app/logs"
    SYSLOG_DIR: str = "/app/logs/syslogs"
    ASSLOG_DIR: str = "/app/logs/asslogs"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ===========================================
    # ALGORITHM CONFIGURATION
    # ===========================================
    ELO_K_FACTOR_INITIAL: int = 32
    ELO_K_FACTOR_MID: int = 24
    ELO_K_FACTOR_LATE: int = 16
    ELO_K_FACTOR_THRESHOLD_1: int = 10
    ELO_K_FACTOR_THRESHOLD_2: int = 25
    
    STAGNATION_EPSILON: float = 0.05
    STAGNATION_WINDOW_SIZE: int = 5
    
    COHENS_D_THRESHOLD: float = 0.5
    
    # ===========================================
    # PEER REVIEW CONFIGURATION
    # ===========================================
    PEER_REVIEW_TIMEOUT_HOURS: int = 24
    MIN_FEEDBACK_LENGTH: int = 15
    
    # ===========================================
    # APPLICATION CONFIGURATION
    # ===========================================
    APP_NAME: str = "Equilibria"
    APP_VERSION: str = "2.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # <--- Ganti APP_ENV jadi ENVIRONMENT
    
    # ===========================================
    # CORS CONFIGURATION
    # ===========================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://equilibria.vercel.app",
    ]
    
    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver."""
        if not self.DATABASE_URL.startswith("postgresql+asyncpg"):
            return self.DATABASE_URL.replace(
                "postgresql://", 
                "postgresql+asyncpg://"
            )
        return self.DATABASE_URL


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings