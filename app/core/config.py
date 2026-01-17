from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fashion.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "https://ecommerce-frontend-2c9n.vercel.app"
    ]
    
    # Paystack
    PAYSTACK_SECRET_KEY: Optional[str] = os.getenv("PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY: Optional[str] = os.getenv("PAYSTACK_PUBLIC_KEY")
    PAYSTACK_CALLBACK_URL: Optional[str] = os.getenv("PAYSTACK_CALLBACK_URL", "http://localhost:3000/order-confirmation")
    
    # Email - USING YOUR RAILWAY VARIABLES
    SMTP_USER: str = os.getenv("SMTP_USER", "ruthlessbyt@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "hello@bloomg.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "BLOOM G WOMEN")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "app/static/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    # Supabase
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()

# Generate secure secret if not set
if settings.SECRET_KEY == "your-secret-key-change-in-production":
    import secrets
    settings.SECRET_KEY = secrets.token_urlsafe(32)