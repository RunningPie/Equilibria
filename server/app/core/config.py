from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # ==== Application Settings ====
    APP_NAME: str = "Equilibria"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # Options: development, staging, production
    PYTHONPATH: str = "/app"
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ==== DB Connection Settings ====
    DB_USER: str = "equilibria_user"
    DB_PASSWORD: str = "equilibria_password"
    DB_NAME: str = "equilibria_db"
    
    # Fallback: PostgreSQL container vars
    POSTGRES_USER: str = "equilibria_user"
    POSTGRES_PASSWORD: str = "equilibria_password"
    POSTGRES_DB: str = "equilibria_db"
    
    # Properties turunan   
    @property
    def effective_db_user(self) -> str:
        return self.DB_USER if self.DB_USER != "equilibria_user" else self.POSTGRES_USER
    
    @property
    def effective_db_password(self) -> str:
        return self.DB_PASSWORD if self.DB_PASSWORD != "equilibria_password" else self.POSTGRES_PASSWORD

    @property
    def effective_db_name(self) -> str:
        return self.DB_NAME if self.DB_NAME != "equilibria_db" else self.POSTGRES_DB
    
    DATABASE_URL: str = f"postgresql+asyncpg://{effective_db_user}:{effective_db_password}@db:5432/{effective_db_name}"
        
    # ==== Security Settings ====
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SANDBOX_DB_ROLE: str = "sandbox_executor"
    CORS_ORIGINS: list[str] = ["*"]  # Update with specific origins in production
    
    # ==== Logging Settings ====
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