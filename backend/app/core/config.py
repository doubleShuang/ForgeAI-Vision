import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "YOLOv8 Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "play.min.io")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_MODELS: str = "models"
    MINIO_BUCKET_MEDIA: str = "media"
    USE_LOCAL_STORAGE: bool = os.getenv("USE_LOCAL_STORAGE", "True").lower() == "true" # Fallback for demo
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure upload dirs exist if using local storage
if settings.USE_LOCAL_STORAGE:
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "models"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "media"), exist_ok=True)
