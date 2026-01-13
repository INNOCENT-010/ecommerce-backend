from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./fashion.db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    
    PAYSTACK_SECRET_KEY: Optional[str] = None
    PAYSTACK_PUBLIC_KEY: Optional[str] = None
    PAYSTACK_CALLBACK_URL: Optional[str] = "http://localhost:3000/order-confirmation"
    
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    
    FRONTEND_URL: str = "http://localhost:3000"
    UPLOAD_DIR: str = "app/static/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()

if settings.SECRET_KEY == "your-secret-key-change-in-production":
    import secrets
    settings.SECRET_KEY = secrets.token_urlsafe(32)