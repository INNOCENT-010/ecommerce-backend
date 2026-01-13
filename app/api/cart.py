#/api/cart.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import CartItem, Product, User
from app.schemas.schemas import CartItemBase, CartItemResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=List[CartItemResponse])
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    return cart_items

@router.post("/add")
async def add_to_cart(
    item: CartItemBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cart_item = db.query(CartItem).filter(
        (CartItem.user_id == current_user.id) &
        (CartItem.product_id == item.product_id)
    ).first()
    
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)
    
    db.commit()
    return {"message": "Item added to cart"}

@router.put("/{cart_item_id}")
async def update_cart_item(
    cart_item_id: int,
    item: CartItemBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(CartItem).filter(
        (CartItem.id == cart_item_id) &
        (CartItem.user_id == current_user.id)
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cart_item.quantity = item.quantity
    db.commit()
    
    return {"message": "Cart item updated"}

@router.delete("/{cart_item_id}")
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(CartItem).filter(
        (CartItem.id == cart_item_id) &
        (CartItem.user_id == current_user.id)
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": "Item removed from cart"}

@router.delete("/")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": "Cart cleared"}