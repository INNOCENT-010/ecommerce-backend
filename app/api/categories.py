from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Category
from app.schemas.schemas import CategoryCreate, CategoryResponse 

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Category).filter(
        Category.name == category.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    db_category = Category(
        name=category.name,
        description=category.description
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category