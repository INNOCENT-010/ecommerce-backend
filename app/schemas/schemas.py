# app/schemas/schemas.py - CORRECTED VERSION
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
    
    @validator('created_at', pre=True)
    def parse_created_at(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str