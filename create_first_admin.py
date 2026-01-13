# create_admin.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import User
import hashlib

def create_admin_user():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@bloomg.com").first()
        
        if admin:
            print(f"✅ Admin already exists: {admin.email}")
            # Make sure they're admin
            admin.is_admin = True
            db.commit()
            print("✅ Admin privileges confirmed")
            return admin
        
        # Create new admin user
        hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
        
        admin_user = User(
            email="admin@bloomg.com",
            hashed_password=hashed_password,
            full_name="Admin User",
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@bloomg.com")
        print(f"   Password: admin123")
        print(f"   ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()