# app/core/security.py - WITH ADMIN FUNCTION
from datetime import datetime, timedelta
from typing import Union
from jose import JWTError, jwt
import hashlib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User

security = HTTPBearer()

# ==================== SHA256 HASHING (MATCHES YOUR DATABASE) ====================
def hash_password(password: str) -> str:
    """SHA256 hash - matches what's in your database"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify SHA256 hash"""
    return hash_password(plain_password) == hashed_password

# ==================== JWT ====================
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Union[dict, None]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

# ==================== DEPENDENCIES ====================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    # Accept either email or user_id as subject
    user_identifier = payload.get("sub")
    user_id = payload.get("user_id")
    
    user = None
    if user_identifier and "@" in user_identifier:
        user = db.query(User).filter(User.email == user_identifier, User.is_active == True).first()
    elif user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise credentials_exception
    return user

# ✅ ADD THIS FUNCTION FOR ADMIN ACCESS
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin access"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
