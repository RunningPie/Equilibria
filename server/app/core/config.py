from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import field_validator
import json

class Settings(BaseSettings):
    # ==== Pengaturan Aplikasi ====
    APP_NAME: str = "Equilibria"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # Opsi: development, staging, production
    PYTHONPATH: str = "/app"
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ==== Pengaturan Koneksi DB ====
    DB_USER: str = "equilibria_user"
    DB_PASSWORD: str = "equilibria_password"
    DB_NAME: str = "equilibria_db"
    DB_HOST: str = "db"
    DB_PORT: str = "5432"
    
    # Fallback: PostgreSQL container vars
    # POSTGRES_USER: str = "equilibria_user"
    # POSTGRES_PASSWORD: str = "equilibria_password"
    # POSTGRES_DB: str = "equilibria_db"

    DATABASE_URL: str = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
    # ==== Pengaturan Keamanan ====
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    SANDBOX_DB_ROLE: str = "sandbox_executor"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Tangani baik format JSON array ['...'] maupun comma-separated '...'"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            # Coba format JSON array terlebih dahulu
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Jika gagal, coba format comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ==== Pengaturan Logging ====
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/app/logs"
    SYSLOG_DIR: str = "/app/logs/syslogs"
    ASSLOG_DIR: str = "/app/logs/asslogs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()