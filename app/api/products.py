from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import shutil
import os
from datetime import datetime

from app.core.database import get_db
from app.models.models import Product, Category, ProductImage, User
from app.core.security import get_current_user, require_admin

router = APIRouter()

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def serialize_product(product: Product):
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "original_price": product.original_price,
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "filepath": f"/static/uploads/{img.filename}",
                "is_primary": img.is_primary
            }
            for img in product.images
        ],
        "category": {
            "id": product.category.id,
            "name": product.category.name
        } if product.category else None,
        "category_id": product.category_id,
        "stock": product.stock,
        "is_new": product.is_new,
        "is_sale": product.is_sale,
        "download_count": product.download_count,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }

@router.get("/", response_model=List[dict])
async def list_products(
    category_id: int = Query(None),
    skip: int = 0,
    limit: int = 20,
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%"))
        )

    products = query.offset(skip).limit(limit).all()
    return [serialize_product(p) for p in products]

@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return serialize_product(product)

@router.post("/{product_id}/download")
async def increment_download_count(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.download_count += 1
    db.commit()
    
    return {
        "message": "Download count incremented",
        "download_count": product.download_count
    }

@router.post("/")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    stock: int = Form(0),
    original_price: Optional[float] = Form(None),
    is_new: bool = Form(True),
    is_sale: bool = Form(False),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    product = Product(
        name=name,
        description=description,
        price=price,
        original_price=original_price,
        category_id=category_id,
        stock=stock,
        is_new=is_new,
        is_sale=is_sale
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    uploaded_images = []
    for index, image_file in enumerate(images):
        if image_file.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(image_file.filename).suffix
            unique_filename = f"{product.id}_{timestamp}_{index}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            
            product_image = ProductImage(
                filename=unique_filename,
                filepath=str(file_path),
                product_id=product.id,
                is_primary=(index == 0)
            )
            db.add(product_image)
            uploaded_images.append(product_image)
    
    db.commit()
    
    return serialize_product(product)

@router.post("/{product_id}/upload-images")
async def upload_product_images(
    product_id: int,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    uploaded_images = []
    for index, image_file in enumerate(images):
        if image_file.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(image_file.filename).suffix
            unique_filename = f"{product.id}_{timestamp}_{index}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            
            product_image = ProductImage(
                filename=unique_filename,
                filepath=str(file_path),
                product_id=product.id,
                is_primary=False
            )
            db.add(product_image)
            uploaded_images.append(product_image)
    
    db.commit()
    
    return {
        "message": f"{len(uploaded_images)} images uploaded successfully",
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "filepath": f"/static/uploads/{img.filename}"
            }
            for img in uploaded_images
        ]
    }

@router.put("/{product_id}")
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    original_price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    category_id: Optional[int] = Form(None),
    is_new: Optional[bool] = Form(None),
    is_sale: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if original_price is not None:
        product.original_price = original_price
    if stock is not None:
        product.stock = stock
    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        product.category_id = category_id
    if is_new is not None:
        product.is_new = is_new
    if is_sale is not None:
        product.is_sale = is_sale
    
    db.commit()
    db.refresh(product)
    
    return serialize_product(product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    
    return {"message": "Product deleted successfully"}

@router.get("/admin/stats/downloads")
async def get_download_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    from sqlalchemy import func
    
    top_downloads = (
        db.query(Product)
        .order_by(Product.download_count.desc())
        .limit(10)
        .all()
    )
    
    total_downloads = db.query(func.sum(Product.download_count)).scalar() or 0
    
    return {
        "total_downloads": total_downloads,
        "top_downloaded": [
            {
                "id": p.id,
                "name": p.name,
                "download_count": p.download_count,
                "category": p.category.name if p.category else "Uncategorized"
            }
            for p in top_downloads
        ]
    }