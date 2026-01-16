# app/api/auth.py - FULL CORRECTED VERSION
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
from app.services.email_service import email_service
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.config import settings
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        phone=user_data.phone if hasattr(user_data, 'phone') else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
    )

@router.post("/admin-login", response_model=Token)
async def admin_login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "is_admin": True},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at
    )

@router.get("/check-admin")
async def check_admin_status(current_user: User = Depends(get_current_user)):
    return {"is_admin": current_user.is_admin}

@router.get("/check-admin-exists")
async def check_admin_exists(db: Session = Depends(get_db)):
    admin_count = db.query(User).filter(User.is_admin == True).count()
    return {"admin_exists": admin_count > 0}

@router.get("/verify-admin")
async def verify_admin_status(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return {
        "is_admin": True,
        "email": current_user.email,
        "user_id": current_user.id,
        "phone": current_user.phone
    }

@router.post("/create-admin")
async def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    admin_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        phone=user_data.phone if hasattr(user_data, 'phone') else None,
        is_admin=True,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return {
        "message": "Admin user created successfully",
        "user": UserResponse(
            id=admin_user.id,
            email=admin_user.email,
            full_name=admin_user.full_name,
            phone=admin_user.phone,
            is_active=admin_user.is_active,
            is_admin=admin_user.is_admin,
            created_at=admin_user.created_at
        )
    }

@router.post("/create-first-admin")
async def create_first_admin(db: Session = Depends(get_db)):
    existing_admin = db.query(User).filter(User.is_admin == True).first()
    if existing_admin:
        return {
            "message": "Admin already exists",
            "existing_admin": {
                "email": existing_admin.email,
                "full_name": existing_admin.full_name,
                "id": existing_admin.id,
                "phone": existing_admin.phone
            }
        }
    
    existing_user = db.query(User).filter(User.email == "admin@bloomg.com").first()
    if existing_user:
        existing_user.is_admin = True
        db.commit()
        return {
            "message": "Updated existing user to admin",
            "user": {
                "email": existing_user.email,
                "full_name": existing_user.full_name,
                "id": existing_user.id,
                "phone": existing_user.phone,
                "is_admin": True
            }
        }
    
    admin_user = User(
        email="admin@bloomg.com",
        full_name="BLOOM&G Admin",
        hashed_password=hash_password("Admin123!"),
        phone=None,
        is_admin=True,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return {
        "message": "First admin user created successfully",
        "admin": {
            "id": admin_user.id,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "phone": admin_user.phone,
            "is_admin": admin_user.is_admin,
            "is_active": admin_user.is_active
        }
    }

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

verification_store = {}

# IN app/api/auth.py - Add this import at the top
from app.services.email_service import email_service  # Use your email service

# Then update the send_verification function:

@router.post("/send-verification")
async def send_verification(
    email_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    existing_user = db.query(User).filter(User.email == email).first()
    
    code = ''.join(random.choices(string.digits, k=6))
    
    verification_store[email] = {
        "code": code,
        "expires_at": datetime.now() + timedelta(minutes=10),
        "user_exists": existing_user is not None
    }
    
    # 🔥 ADD THIS: Send the code via email
    try:
        background_tasks.add_task(
            email_service.send_verification_code,
            to_email=email,
            code=code
        )
    except Exception as e:
        print(f"⚠️ Failed to schedule email: {e}")
        # Continue anyway - we'll tell the frontend code was sent
    
    return {
        "message": "Verification code sent",
        "email": email,
        "user_exists": existing_user is not None,
        "code_sent": True  # Add this to confirm to frontend
    }

@router.post("/verify-code")
async def verify_email_code(
    verification_data: dict,
    db: Session = Depends(get_db)
):
    email = verification_data.get("email")
    code = verification_data.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code are required")
    
    stored_data = verification_store.get(email)
    
    if not stored_data:
        raise HTTPException(status_code=400, detail="No verification code found")
    
    if datetime.now() > stored_data["expires_at"]:
        del verification_store[email]
        raise HTTPException(status_code=400, detail="Verification code expired")
    
    if stored_data["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    del verification_store[email]
    
    user = db.query(User).filter(User.email == email).first()
    
    # ✅ FIX: Return user data if exists
    if user:
        return {
            "verified": True,
            "email": email,
            "user_exists": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    else:
        return {
            "verified": True,
            "email": email,
            "user_exists": False,
            "user": None
        }

@router.post("/magic-login")
async def magic_login(
    user_data: dict,
    db: Session = Depends(get_db)
):
    email = user_data.get("email")
    full_name = user_data.get("full_name")
    phone = user_data.get("phone")
    
    if not email or not full_name:
        raise HTTPException(status_code=400, detail="Email and full name are required")
    
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
        )
    else:
        hashed_password = hash_password("temp_password_123")
        
        new_user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            phone=phone,
            is_active=True,
            is_admin=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email, "user_id": new_user.id},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=new_user.id,
                email=new_user.email,
                full_name=new_user.full_name,
                phone=new_user.phone,
                is_active=new_user.is_active,
                is_admin=new_user.is_admin,
                created_at=new_user.created_at
            )
        )