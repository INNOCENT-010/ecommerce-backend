# app/main.py - UPDATED CORS SECTION
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal, get_db
from app.core.config import settings
from app.api import auth

from app.payments import router as payments_router
from app.api.admin import router as admin_router  
from app.models.models import ProductImage, Order, OrderItem, Product

def init_database():
    from sqlalchemy import inspect, text
    
    print("Initializing database...")
    
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
    
    db = SessionLocal()
    try:
        try:
            db.execute(text("SELECT is_admin FROM users LIMIT 1"))
        except Exception:
            print("Adding is_admin column to users table...")
            db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
        
        try:
            db.execute(text("SELECT download_count FROM products LIMIT 1"))
        except Exception:
            print("Adding download_count column to products table...")
            db.execute(text("ALTER TABLE products ADD COLUMN download_count INTEGER DEFAULT 0"))
        
        try:
            db.execute(text("SELECT original_price FROM products LIMIT 1"))
        except Exception:
            print("Adding original_price column to products table...")
            db.execute(text("ALTER TABLE products ADD COLUMN original_price REAL"))
        
        try:
            db.execute(text("SELECT is_new FROM products LIMIT 1"))
        except Exception:
            print("Adding is_new column to products table...")
            db.execute(text("ALTER TABLE products ADD COLUMN is_new BOOLEAN DEFAULT 1"))
        
        try:
            db.execute(text("SELECT is_sale FROM products LIMIT 1"))
        except Exception:
            print("Adding is_sale column to products table...")
            db.execute(text("ALTER TABLE products ADD COLUMN is_sale BOOLEAN DEFAULT 0"))
        
        db.commit()
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        db.rollback()
    finally:
        db.close()

init_database()

def update_product_stock(db: Session, product_id: str, quantity: int, increase: bool = False):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        if increase:
            product.stock += quantity
        else:
            if product.stock < quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product {product.name} out of stock. Only {product.stock} available"
                )
            product.stock -= quantity
        
        db.commit()
        return product.stock
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating stock: {str(e)}")

app = FastAPI(
    title="Fashion Store API",
    description="E-commerce backend for Next.js frontend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        
        # Railway backend (for API testing)
        "https://skillful-creativity-production.up.railway.app",
        
        # Vercel frontend - ADD YOUR EXACT VERCEL URL HERE
        "https://oh-polly-clone.vercel.app",  # ⬅️ REPLACE WITH YOUR VERCEL URL
        
        # All Vercel deployments (pattern format)
        "https://*.vercel.app",
        
        # Development with IP
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Changed from specific list to "*"
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(payments_router)
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.post("/api/orders/{order_id}/update-stock")
async def update_stock_on_order_completion(
    order_id: int,
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.payment_status == "paid":
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            
            for item in order_items:
                update_product_stock(db, item.product_id, item.quantity, increase=False)
            
            return {"message": "Stock updated successfully", "order_id": order_id}
        else:
            return {"message": "Order not paid yet, stock not updated"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders/{order_id}/cancel-stock")
async def restore_stock_on_order_cancel(
    order_id: int,
    db: Session = Depends(get_db)
):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        for item in order_items:
            update_product_stock(db, item.product_id, item.quantity, increase=True)
        
        return {"message": "Stock restored successfully", "order_id": order_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test-connection")
async def test_connection():
    return {
        "status": "connected",
        "backend": "FastAPI",
        "frontend": "Next.js",
        "timestamp": datetime.now().isoformat(),
        "database": "SQLite",
        "upload_dir": settings.UPLOAD_DIR,
    }

@app.get("/debug/auth-endpoints")
async def debug_auth_endpoints():
    return {
        "admin_login_url": "POST /auth/admin-login",
        "create_first_admin_url": "POST /auth/create-first-admin",
        "test_admin_url": "http://127.0.0.1:8000/auth/create-first-admin",
        "available_endpoints": [
            "/auth/admin-login",
            "/auth/login",
            "/auth/register",
            "/auth/create-first-admin",
            "/auth/check-admin",
            "/auth/me"
        ]
    }

@app.get("/")
async def root():
    return {
        "message": "Fashion Store API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "payments": "/api/payments",
            "admin": "/api/admin"
        }
    }

@app.get("/api")
async def api_root():
    return {
        "message": "Fashion Store API",
        "endpoints": {
            "auth": "/auth",
            "payments": "/api/payments",
            "admin": "/api/admin"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("Fashion Store API Starting...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    print("CORS allowed origins:")
    for origin in [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]:
        print(f"  - {origin}")
    print("=" * 50)

@app.on_event("startup")
async def print_routes():
    from fastapi.routing import APIRoute
    print("\nRegistered routes:")
    print("=" * 50)
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"{route.path} - {list(route.methods)}")
    print("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )