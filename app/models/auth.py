# app/models/auth.py
from pydantic import BaseModel
from typing import Optional

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None