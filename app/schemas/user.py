# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_admin: bool
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse