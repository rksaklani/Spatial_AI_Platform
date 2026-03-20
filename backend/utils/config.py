"""Configuration management using environment variables."""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "spatial_ai_platform"
    
    # Valkey/Redis
    valkey_host: str = "localhost"
    valkey_port: int = 6379
    valkey_db: int = 0
    valkey_password: Optional[str] = None
    valkey_max_connections: int = 50
    valkey_socket_timeout: int = 5
    valkey_connect_timeout: int = 5
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Celery
    celery_broker_url: str = "valkey://localhost:6379/0"
    celery_result_backend: str = "valkey://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
