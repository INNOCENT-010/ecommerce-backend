# app/api/orders.py - COMPLETE CORRECTED VERSION
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.models import Order, OrderItem, Product, User, Address 
from app.schemas.schemas import (
    OrderResponse, 
    OrderCreate, 
    CartItem, 
    GuestOrderCreate, 
    GuestShippingAddress, 
    GuestOrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus
)
from app.core.security import get_current_user

router = APIRouter()

@router.post("/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(
        (Address.id == order_data.delivery_address_id) &
        (Address.user_id == current_user.id)
    ).first()
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found")
    
    total_amount = 0
    order_items_data = []
    
    for cart_item in order_data.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {cart_item.product_id} not found")
        
        if product.stock < cart_item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
        
        item_total = product.price * cart_item.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product_id": product.id,
            "quantity": cart_item.quantity,
            "price": product.price,
            "product_name": product.name
        })
    
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    db_order = Order(
        user_id=current_user.id,
        order_number=order_number,
        total_amount=total_amount,
        status=OrderStatus.PENDING.value,
        payment_method=order_data.payment_method.value if order_data.payment_method else None,
        delivery_address_id=order_data.delivery_address_id,
        payment_status=PaymentStatus.PENDING.value
    )
    
    db.add(db_order)
    db.flush()
    
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)
        
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.post("/guest/create")
async def create_guest_order(
    order_data: GuestOrderCreate,
    db: Session = Depends(get_db)
):
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
    
    order_number = f"GST-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    guest_user = db.query(User).filter(User.email == order_data.shipping_address.email).first()
    
    if not guest_user:
        guest_user = User(
            email=order_data.shipping_address.email,
            full_name=order_data.shipping_address.full_name,
            is_active=True,
            is_admin=False
        )
        db.add(guest_user)
        db.flush()
    
    guest_address = Address(
        user_id=guest_user.id,
        street=order_data.shipping_address.street,
        city=order_data.shipping_address.city,
        state=order_data.shipping_address.state,
        country=order_data.shipping_address.country,
        postal_code=order_data.shipping_address.postal_code,
        is_default=True
    )
    db.add(guest_address)
    db.flush()
    
    db_order = Order(
        user_id=guest_user.id,
        order_number=order_number,
        total_amount=order_data.total_amount,
        status=OrderStatus.PENDING.value,
        payment_method=order_data.payment_method.value,
        delivery_address_id=guest_address.id,
        payment_status=PaymentStatus.PENDING.value
    )
    
    db.add(db_order)
    db.flush()
    
    for item in order_data.items:
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(order_item)
        
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity
    
    db.commit()
    db.refresh(db_order)
    
    return {
        "success": True,
        "order": {
            "id": db_order.id,
            "order_number": order_number,
            "total_amount": db_order.total_amount,
            "status": db_order.status,
            "payment_method": db_order.payment_method,
            "created_at": db_order.created_at.isoformat() if db_order.created_at else None
        }
    }

@router.get("/", response_model=List[OrderResponse])
async def list_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        (Order.id == order_id) &
        (Order.user_id == current_user.id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.post("/{order_id}/initiate-payment")
async def initiate_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        (Order.id == order_id) &
        (Order.user_id == current_user.id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Order cannot be paid")
    
    payment_method = order.payment_method
    
    try:
        if payment_method == PaymentMethod.PAYSTACK.value:
            return {
                "type": "paystack",
                "authorization_url": f"https://paystack.com/pay/mock-{order.order_number}",
                "reference": f"PSK-{order.order_number}",
                "amount": order.total_amount,
                "currency": "NGN"
            }
        
        elif payment_method == PaymentMethod.BANK_TRANSFER.value:
            return {
                "type": "bank_transfer",
                "bank_name": "First Bank",
                "account_name": "Fashion Store Ltd",
                "account_number": "1234567890",
                "amount": order.total_amount,
                "currency": "NGN",
                "reference": f"BANK-{order.order_number}"
            }
        
        elif payment_method == PaymentMethod.CASH_ON_DELIVERY.value:
            order.status = OrderStatus.PROCESSING.value
            db.commit()
            
            return {
                "type": "cash_on_delivery",
                "message": "Order placed successfully. Pay on delivery.",
                "order_status": order.status
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/guest/{order_id}/initiate-payment")
async def initiate_guest_payment(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Order cannot be paid")
    
    address = db.query(Address).filter(Address.id == order.delivery_address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    user = db.query(User).filter(User.id == address.user_id).first()
    
    payment_method = order.payment_method
    
    try:
        if payment_method == PaymentMethod.PAYSTACK.value:
            return {
                "type": "paystack",
                "authorization_url": f"https://paystack.com/pay/mock-{order.order_number}",
                "reference": f"PSK-{order.order_number}",
                "amount": order.total_amount,
                "currency": "NGN"
            }
        
        elif payment_method == PaymentMethod.BANK_TRANSFER.value:
            return {
                "type": "bank_transfer",
                "bank_name": "First Bank",
                "account_name": "Fashion Store Ltd",
                "account_number": "1234567890",
                "amount": order.total_amount,
                "currency": "NGN",
                "reference": f"BANK-{order.order_number}"
            }
        
        elif payment_method == PaymentMethod.CASH_ON_DELIVERY.value:
            order.status = OrderStatus.PROCESSING.value
            db.commit()
            
            return {
                "type": "cash_on_delivery",
                "message": "Order placed successfully. Pay on delivery.",
                "order_status": order.status
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/confirm-payment")
async def confirm_payment(
    order_id: int,
    payment_ref: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        (Order.id == order_id) &
        (Order.user_id == current_user.id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        order.status = OrderStatus.PAID.value
        order.payment_status = PaymentStatus.PAID.value
        order.payment_reference = payment_ref
        db.commit()
        
        return {"message": "Payment confirmed", "order_status": order.status}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/guest/{order_id}/confirm-payment")
async def confirm_guest_payment(
    order_id: int,
    payment_ref: str,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        order.status = OrderStatus.PAID.value
        order.payment_status = PaymentStatus.PAID.value
        order.payment_reference = payment_ref
        db.commit()
        
        return {"message": "Payment confirmed", "order_status": order.status}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))