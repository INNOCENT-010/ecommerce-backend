from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer
from typing import Optional

SECRET_KEY = "test-secret-change-this"  # Same as NEXTAUTH_SECRET
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_jwt(token: str = Header(..., alias="Authorization")):
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    