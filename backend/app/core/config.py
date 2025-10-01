from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql://localhost:5432/md_linked_secrets"
    
    # Security settings
    secret_key: str = "your-secret-key-change-this-in-production"
    encryption_key: str = "your-encryption-key-change-this-in-production"
    
    # API settings
    api_v1_str: str = "/api/v1"
    project_name: str = "MD-Linked-Secrets"
    version: str = "1.0.0"
    
    # CORS settings
    backend_cors_origins: list[str] = ["http://localhost:3030", "http://localhost:8080", "http://localhost:8088"]
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Create settings instance
settings = Settings()


# Database configuration
DATABASE_CONFIG = {
    "url": settings.database_url,
    "echo": settings.debug,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 300,
} 