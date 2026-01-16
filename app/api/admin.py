# /api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import Order, OrderItem, User, Transaction, Product, Address
from app.core.security import get_current_admin_user
from app.schemas.admin import OrderSummary, DashboardStats

router = APIRouter(tags=["admin"])

@router.get("/orders", response_model=List[OrderSummary])
async def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    orders = db.query(Order).order_by(desc(Order.created_at)).all()
    
    order_summaries = []
    for order in orders:
        items_count = db.query(func.count(OrderItem.id)).filter(
            OrderItem.order_id == order.id
        ).scalar() or 0
        
        order_summaries.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or "Guest",
            "customer_email": order.customer_email or "",
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat(),
            "items_count": items_count
        })
    
    return order_summaries

@router.get("/orders/enhanced")
async def get_enhanced_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    query = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.shipping_address)
    )
    
    if status and status != "all":
        query = query.filter(Order.status == status)
    
    if payment_status and payment_status != "all":
        query = query.filter(Order.payment_status == payment_status)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Order.created_at >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Order.created_at <= end_dt)
        except:
            pass
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_number.ilike(search_term),
                Order.customer_name.ilike(search_term),
                Order.customer_email.ilike(search_term),
                Order.customer_phone.ilike(search_term)
            )
        )
    
    total = query.count()
    offset = (page - 1) * limit
    
    orders = query.order_by(desc(Order.created_at)).offset(offset).limit(limit).all()
    
    enhanced_orders = []
    for order in orders:
        has_size = False
        has_color = False
        size_variants = []
        color_variants = []
        items_preview = []
        total_quantity = 0
        
        for item in order.items:
            total_quantity += item.quantity
            
            if item.size:
                has_size = True
                if item.size not in size_variants:
                    size_variants.append(item.size)
            
            if item.color:
                has_color = True
                if item.color not in color_variants:
                    color_variants.append(item.color)
            
            if len(items_preview) < 2:
                items_preview.append({
                    "name": item.product_name,
                    "quantity": item.quantity,
                    "size": item.size,
                    "color": item.color,
                    "price": item.price,
                    "image": item.product_image
                })
        
        shipping_location = "N/A"
        shipping_state = "N/A"
        shipping_city = "N/A"
        
        if order.shipping_address:
            shipping_location = f"{order.shipping_address.city}, {order.shipping_address.state}"
            shipping_state = order.shipping_address.state
            shipping_city = order.shipping_address.city
        
        transaction = db.query(Transaction).filter(
            Transaction.order_id == order.id
        ).first()
        
        payment_method = "Card" if transaction and transaction.channel == "card" else "Other"
        
        enhanced_orders.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or "Guest",
            "customer_email": order.customer_email or "",
            "customer_phone": order.customer_phone or "",
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "payment_status": order.payment_status,
            "payment_method": payment_method,
            "created_at": order.created_at.isoformat(),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "items_count": len(order.items),
            "total_quantity": total_quantity,
            "has_size": has_size,
            "has_color": has_color,
            "size_variants": size_variants,
            "color_variants": color_variants,
            "shipping_location": shipping_location,
            "shipping_state": shipping_state,
            "shipping_city": shipping_city,
            "items_preview": items_preview,
            "notes": order.notes
        })
    
    return {
        "orders": enhanced_orders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@router.get("/orders/{order_id}")
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    order = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.shipping_address)
    ).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    transaction = db.query(Transaction).filter(
        Transaction.order_id == order_id
    ).first()
    
    items_with_details = []
    for item in order.items:
        item_data = {
            "id": item.id,
            "product_name": item.product_name,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price,
            "size": item.size,
            "color": item.color,
            "image": item.product_image,
            "sku": item.product_sku,
            "subtotal": item.quantity * item.price
        }
        
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                item_data["current_stock"] = product.stock
                item_data["is_active"] = product.is_active
        
        items_with_details.append(item_data)
    
    shipping_address = None
    if order.shipping_address:
        shipping_address = {
            "street": order.shipping_address.street,
            "city": order.shipping_address.city,
            "state": order.shipping_address.state,
            "country": order.shipping_address.country,
            "postal_code": order.shipping_address.postal_code,
            "full_address": f"{order.shipping_address.street}, {order.shipping_address.city}, {order.shipping_address.state}, {order.shipping_address.country} - {order.shipping_address.postal_code}"
        }
    
    transaction_details = None
    if transaction:
        transaction_details = {
            "reference": transaction.reference,
            "amount": transaction.amount,
            "status": transaction.status,
            "gateway_response": transaction.gateway_response,
            "channel": transaction.channel,
            "card_last4": transaction.card_last4,
            "card_type": transaction.card_type,
            "bank": transaction.bank,
            "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None
        }
    
    summary = {
        "items_count": len(order.items),
        "total_quantity": sum(item.quantity for item in order.items),
        "has_size": any(item.size for item in order.items),
        "has_color": any(item.color for item in order.items),
        "size_variants": list(set(item.size for item in order.items if item.size)),
        "color_variants": list(set(item.color for item in order.items if item.color))
    }
    
    return {
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or "Guest",
            "customer_email": order.customer_email or "",
            "customer_phone": order.customer_phone or "",
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "payment_status": order.payment_status,
            "shipping_address": shipping_address,
            "notes": order.notes,
            "created_at": order.created_at.isoformat(),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "order_data": order.order_data
        },
        "items": items_with_details,
        "transaction": transaction_details,
        "summary": summary
    }

@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    new_status = status_update.get("status")
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = new_status
    db.commit()
    
    return {"success": True, "message": f"Order status updated to {new_status}"}

@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.payment_status == "paid"
    ).scalar() or 0
    
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == "pending"
    ).scalar() or 0
    
    processing_orders = db.query(func.count(Order.id)).filter(
        Order.status == "processing"
    ).scalar() or 0
    
    shipped_orders = db.query(func.count(Order.id)).filter(
        Order.status == "shipped"
    ).scalar() or 0
    
    delivered_orders = db.query(func.count(Order.id)).filter(
        Order.status == "delivered"
    ).scalar() or 0
    
    cancelled_orders = db.query(func.count(Order.id)).filter(
        Order.status == "cancelled"
    ).scalar() or 0
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_orders = db.query(func.count(Order.id)).filter(
        Order.created_at >= seven_days_ago
    ).scalar() or 0
    
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_users": total_users,
        "total_products": total_products,
        "orders_by_status": {
            "pending": pending_orders,
            "processing": processing_orders,
            "shipped": shipped_orders,
            "delivered": delivered_orders,
            "cancelled": cancelled_orders
        },
        "recent_orders": recent_orders,
        "currency": "NGN"
    }

@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    users = db.query(User).order_by(desc(User.created_at)).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "order_count": db.query(func.count(Order.id)).filter(
                Order.user_id == user.id
            ).scalar() or 0
        }
        for user in users
    ]

@router.get("/products")
async def get_all_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    products = db.query(Product).order_by(desc(Product.created_at)).all()
    
    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "original_price": product.original_price,
            "stock": product.stock,
            "is_active": product.is_active,
            "is_new": product.is_new,
            "is_sale": product.is_sale,
            "created_at": product.created_at.isoformat(),
            "category": product.category.name if product.category else "Uncategorized"
        }
        for product in products
    ]