# app/payments.py - CORRECTED VERSION
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import requests
import hashlib
import hmac
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import csv
import io

from app.core.config import settings
from app.schemas.order import OrderCreate, PaystackInitializeResponse

load_dotenv()

from app.core.database import get_db
from app.models.models import Order, Transaction, OrderItem, Address, User, Product
from app.services.email_service import email_service
from sqlalchemy.orm import joinedload

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_SERVICE_KEY
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_PUBLIC_KEY = settings.PAYSTACK_PUBLIC_KEY
FRONTEND_URL = settings.FRONTEND_URL
PAYSTACK_BASE_URL = "https://api.paystack.co"

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/initialize-debug")
async def initialize_payment_debug(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        
        try:
            parsed_data = json.loads(body_str)
            
            from app.schemas.order import OrderCreate
            from pydantic import ValidationError
            
            try:
                order_data = OrderCreate(**parsed_data)
                return {
                    "success": True,
                    "message": "Schema validation passed",
                    "parsed_data": parsed_data,
                    "validation": "passed"
                }
            except ValidationError as e:
                return {
                    "success": False,
                    "message": "Schema validation failed",
                    "errors": e.errors(),
                    "parsed_data": parsed_data,
                    "validation": "failed"
                }
                
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": "Invalid JSON",
                "error": str(e),
                "raw_body": body_str[:500]
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Debug error",
            "error": str(e)
        }

def generate_order_number():
    timestamp = datetime.now().strftime("%Y%m")
    unique_id = str(uuid.uuid4().int)[:4]
    return f"OH-{timestamp}-{unique_id}"

def verify_paystack_signature(payload: bytes, signature: str) -> bool:
    if not signature or not PAYSTACK_SECRET_KEY:
        return False
    
    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

def parse_datetime(date_string: str):
    if not date_string:
        return None
    try:
        if 'T' in date_string and 'Z' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        elif 'T' in date_string:
            return datetime.fromisoformat(date_string)
        else:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            return None
    except (ValueError, TypeError, AttributeError):
        return None

def update_product_stock_on_order(db: Session, order_id: int):
    try:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        if not order_items:
            return
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            for item in order_items:
                local_product = db.query(Product).filter(Product.id == item.product_id).first()
                if local_product:
                    local_product.stock = max(0, local_product.stock - item.quantity)
            db.commit()
            return
        
        try:
            from supabase import create_client, Client
            
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            for item in order_items:
                try:
                    response = supabase.table("products")\
                        .select("id, name, stock, sku")\
                        .eq("id", str(item.product_id))\
                        .execute()
                    
                    if not response.data or len(response.data) == 0:
                        response = supabase.table("products")\
                            .select("id, name, stock, sku")\
                            .eq("id", item.product_id)\
                            .execute()
                        
                        if not response.data or len(response.data) == 0:
                            continue
                    
                    product_data = response.data[0]
                    current_stock = product_data.get("stock", 0)
                    
                    new_stock = current_stock - item.quantity
                    if new_stock < 0:
                        new_stock = 0
                    
                    supabase.table("products")\
                        .update({
                            "stock": new_stock,
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", str(item.product_id))\
                        .execute()
                    
                    local_product = db.query(Product).filter(Product.id == item.product_id).first()
                    if local_product:
                        local_product.stock = new_stock
                        
                except Exception:
                    continue
            
            db.commit()
            
        except ImportError:
            for item in order_items:
                local_product = db.query(Product).filter(Product.id == item.product_id).first()
                if local_product:
                    local_product.stock = max(0, local_product.stock - item.quantity)
            db.commit()
        except Exception:
            for item in order_items:
                local_product = db.query(Product).filter(Product.id == item.product_id).first()
                if local_product:
                    local_product.stock = max(0, local_product.stock - item.quantity)
            db.commit()
            
    except Exception:
        db.rollback()

@router.get("/transactions")
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Transaction)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for transaction in transactions:
            transaction_dict = {
                "id": transaction.id,
                "order_id": transaction.order_id,
                "reference": transaction.reference,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "status": transaction.status,
                "gateway_response": transaction.gateway_response,
                "channel": transaction.channel,
                "customer_email": transaction.customer_email,
                "customer_id": transaction.customer_id,
                "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
            }
            
            order = db.query(Order).filter(Order.id == transaction.order_id).first()
            if order:
                transaction_dict["order"] = {
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "total_amount": order.total_amount
                }
            
            result.append(transaction_dict)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )

@router.get("/transactions/stats")
async def get_transaction_stats(db: Session = Depends(get_db)):
    try:
        total_transactions = db.query(Transaction).count()
        
        successful_transactions = db.query(Transaction).filter(Transaction.status == 'success').count()
        pending_transactions = db.query(Transaction).filter(Transaction.status == 'pending').count()
        failed_transactions = db.query(Transaction).filter(Transaction.status == 'failed').count()
        
        successful_payments = db.query(Transaction).filter(Transaction.status == 'success').all()
        total_revenue = sum(payment.amount for payment in successful_payments)
        
        today = datetime.now().date()
        today_transactions = db.query(Transaction).filter(
            db.func.date(Transaction.created_at) == today
        ).count()
        
        today_successful = db.query(Transaction).filter(
            db.func.date(Transaction.created_at) == today,
            Transaction.status == 'success'
        ).all()
        today_revenue = sum(payment.amount for payment in today_successful)
        
        return {
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "pending_transactions": pending_transactions,
            "failed_transactions": failed_transactions,
            "total_revenue": total_revenue,
            "today_transactions": today_transactions,
            "today_revenue": today_revenue,
            "success_rate": (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction statistics: {str(e)}"
        )

@router.get("/export")
async def export_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Transaction)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.created_at <= end_dt)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        transactions = query.order_by(Transaction.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Transaction ID', 'Reference', 'Order ID', 'Order Number', 'Customer Email',
            'Customer Name', 'Amount', 'Currency', 'Status', 'Gateway Response',
            'Payment Channel', 'Transaction Date', 'Paid At', 'Created At'
        ])
        
        for transaction in transactions:
            order = db.query(Order).filter(Order.id == transaction.order_id).first()
            order_number = order.order_number if order else "N/A"
            customer_name = order.customer_name if order else "N/A"
            
            writer.writerow([
                transaction.id,
                transaction.reference,
                transaction.order_id,
                order_number,
                transaction.customer_email,
                customer_name,
                transaction.amount,
                transaction.currency,
                transaction.status,
                transaction.gateway_response or "",
                transaction.channel or "",
                transaction.transaction_date.isoformat() if transaction.transaction_date else "",
                transaction.paid_at.isoformat() if transaction.paid_at else "",
                transaction.created_at.isoformat() if transaction.created_at else ""
            ])
        
        output.seek(0)
        
        filename = "transactions_export"
        if start_date and end_date:
            start_str = start_date.split('T')[0]
            end_str = end_date.split('T')[0]
            filename = f"transactions_{start_str}_to_{end_str}.csv"
        else:
            filename = f"transactions_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export transactions: {str(e)}"
        )

@router.get("/transactions/{transaction_id}")
async def get_transaction_details(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        order = db.query(Order).filter(Order.id == transaction.order_id).first()
        order_details = None
        if order:
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            
            order_details = {
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "customer_phone": order.customer_phone,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "items": [
                    {
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "price": item.price,
                        "product_id": item.product_id
                    }
                    for item in order_items
                ]
            }
        
        return {
            "transaction": {
                "id": transaction.id,
                "reference": transaction.reference,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "status": transaction.status,
                "gateway_response": transaction.gateway_response,
                "channel": transaction.channel,
                "customer_email": transaction.customer_email,
                "customer_id": transaction.customer_id,
                "ip_address": transaction.ip_address,
                "authorization_code": transaction.authorization_code,
                "card_last4": transaction.card_last4,
                "card_type": transaction.card_type,
                "bank": transaction.bank,
                "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None
            },
            "order": order_details
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction details: {str(e)}"
        )

@router.post("/initialize", response_model=PaystackInitializeResponse)
async def initialize_payment(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        if not PAYSTACK_SECRET_KEY or not PAYSTACK_PUBLIC_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Paystack configuration missing"
            )
        
        order_number = generate_order_number()
        
        shipping_address = Address(
            street=order_data.shipping_address["street"],
            city=order_data.shipping_address["city"],
            state=order_data.shipping_address["state"],
            country=order_data.shipping_address.get("country", "Nigeria"),
            postal_code=order_data.shipping_address.get("postal_code", ""),
            is_default=False
        )
        
        user = db.query(User).filter(User.email == order_data.email).first()
        if user:
            shipping_address.user_id = user.id
        
        db.add(shipping_address)
        db.flush()
        
        order = Order(
            order_number=order_number,
            customer_email=order_data.email,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            total_amount=order_data.total_amount,
            currency=order_data.currency,
            shipping_address_id=shipping_address.id,
            status="pending",
            payment_status="pending",
            notes=order_data.notes,
            order_data={
                "cart_items": [item.dict() for item in order_data.cart_items],
                "billing_address": order_data.billing_address.dict() if order_data.billing_address else None
            }
        )
        
        if user:
            order.user_id = user.id
        
        db.add(order)
        db.flush()
        
        for cart_item in order_data.cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.price,
                product_name=cart_item.name,
                product_sku=cart_item.sku,
                product_image=cart_item.image,
                size=cart_item.size,
                color=cart_item.color
            )
            db.add(order_item)
        
        amount_in_kobo = int(order_data.total_amount * 100)
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        reference = f"{order_number}_{uuid.uuid4().hex[:8]}"
        payload = {
            "email": order_data.email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": f"{FRONTEND_URL}/order-confirmation",
            "metadata": {
                "order_number": order_number,
                "order_id": order.id,
                "customer_name": order_data.customer_name or "",
            }
        }
        
        response = requests.post(
            f"{PAYSTACK_BASE_URL}/transaction/initialize",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        paystack_response = response.json()
        
        if not paystack_response.get("status"):
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=paystack_response.get("message", "Payment initialization failed")
            )
        
        data = paystack_response["data"]
        order.payment_reference = data["reference"]
        order.paystack_authorization_url = data["authorization_url"]
        order.paystack_access_code = data["access_code"]
        order.paystack_customer_email = order_data.email
        
        db.commit()
        
        result = {
            "success": True,
            "message": "Payment initialized successfully",
            "data": {
                "authorization_url": data["authorization_url"],
                "access_code": data["access_code"],
                "reference": data["reference"],
                "order_number": order_number,
                "public_key": PAYSTACK_PUBLIC_KEY,
                "order_id": order.id
            }
        }
        
        result["authorization_url"] = data["authorization_url"]
        
        return result
        
    except requests.exceptions.RequestException as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service unavailable: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )

@router.get("/verify/{reference}")
async def verify_payment(
    reference: str,
    db: Session = Depends(get_db)
):
    try:
        if not PAYSTACK_SECRET_KEY:
            return {
                "success": False,
                "message": "Payment configuration error",
                "data": None
            }
        
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=headers,
            timeout=30
        )
        
        paystack_response = response.json()
        
        if not paystack_response.get("status"):
            return {
                "success": False,
                "message": paystack_response.get("message", "Verification failed"),
                "data": None
            }
        
        data = paystack_response["data"]
        
        order = db.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.payment_reference == reference).first()
        
        if not order:
            return {
                "success": False,
                "message": "Order not found for this payment reference",
                "data": None
            }
        
        # FIXED: Removed commas that were creating tuples
        if data["status"] == "success":
            order.status = "processing"
            order.payment_status = "paid"
            order.paystack_transaction_id = data["id"]
            order.paid_at = datetime.now()
            
            update_product_stock_on_order(db, order.id)
            
        elif data["status"] == "failed":
            order.payment_status = "failed"
        elif data["status"] == "abandoned":
            order.payment_status = "pending"
        
        transaction = db.query(Transaction).filter(Transaction.reference == reference).first()
        if not transaction:
            transaction_date = parse_datetime(data.get("transaction_date"))
            paid_at = parse_datetime(data.get("paid_at"))
            
            transaction = Transaction(
                order_id=order.id,
                reference=reference,
                amount=data["amount"] / 100,
                currency=data["currency"],
                status=data["status"],
                gateway_response=data["gateway_response"],
                channel=data.get("channel"),
                customer_email=data["customer"]["email"],
                customer_id=data["customer"].get("id"),
                ip_address=data.get("ip_address"),
                authorization_code=data.get("authorization", {}).get("authorization_code"),
                card_last4=data.get("authorization", {}).get("last4"),
                card_type=data.get("authorization", {}).get("card_type"),
                bank=data.get("authorization", {}).get("bank"),
                transaction_date=transaction_date,
                paid_at=paid_at
            )
            db.add(transaction)
        else:
            transaction.status = data["status"]
            transaction.gateway_response = data["gateway_response"]
            
            if data.get("paid_at"):
                paid_at = parse_datetime(data.get("paid_at"))
                if paid_at:
                    transaction.paid_at = paid_at
        
        db.commit()
        
        paid_at_iso = None
        if transaction.paid_at:
            paid_at_iso = transaction.paid_at.isoformat()
        
        return {
            "success": data["status"] == "success",
            "message": data["gateway_response"],
            "data": {
                "order_number": order.order_number,
                "order_id": order.id,
                "status": order.status,
                "payment_status": order.payment_status,
                "amount": transaction.amount,
                "paid_at": paid_at_iso,
                "reference": reference
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Payment verification failed: {str(e)}",
            "data": None
        }

@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        signature = request.headers.get("x-paystack-signature")
        body = await request.body()
        
        if not verify_paystack_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        payload = json.loads(body)
        event = payload.get("event")
        data = payload.get("data")
        
        if event == "charge.success":
            background_tasks.add_task(handle_successful_payment, data, db)
            return JSONResponse(content={"status": "success", "message": "Webhook received"})
        elif event == "charge.failed":
            background_tasks.add_task(handle_failed_payment, data, db)
            return JSONResponse(content={"status": "success", "message": "Webhook received"})
        
        return JSONResponse(content={"status": "ignored", "message": "Event not handled"})
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

def handle_successful_payment(data: Dict[str, Any], db: Session):
    try:
        reference = data.get("reference")
        
        order = db.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.payment_reference == reference).first()
        
        if not order:
            return
        
        # FIXED: Removed commas that were creating tuples
        order.status = "processing"
        order.payment_status = "paid"
        order.paystack_transaction_id = data.get("id")
        order.paid_at = datetime.now()
        
        update_product_stock_on_order(db, order.id)
        
        transaction_date = parse_datetime(data.get("transaction_date"))
        paid_at = parse_datetime(data.get("paid_at"))
        
        transaction = Transaction(
            order_id=order.id,
            reference=reference,
            amount=data.get("amount", 0) / 100,
            currency=data.get("currency", "NGN"),
            status="success",
            gateway_response=data.get("gateway_response"),
            channel=data.get("channel"),
            customer_email=data.get("customer", {}).get("email"),
            customer_id=data.get("customer", {}).get("id"),
            ip_address=data.get("ip_address"),
            authorization_code=data.get("authorization", {}).get("authorization_code"),
            card_last4=data.get("authorization", {}).get("last4"),
            card_type=data.get("authorization", {}).get("card_type"),
            bank=data.get("authorization", {}).get("bank"),
            transaction_date=transaction_date,
            paid_at=paid_at
        )
        
        db.add(transaction)
        db.commit()
        
        try:
            shipping_address = db.query(Address).filter(Address.id == order.shipping_address_id).first()
            shipping_address_str = ""
            if shipping_address:
                shipping_address_str = f"{shipping_address.street}, {shipping_address.city}, {shipping_address.state}, {shipping_address.country} - {shipping_address.postal_code}"
            
            order_items = []
            if order.items:
                for item in order.items:
                    order_items.append({
                        'name': item.product_name,
                        'quantity': item.quantity,
                        'price': item.price
                    })
            
            order_data = {
                'order_number': order.order_number,
                'order_date': order.created_at.strftime('%B %d, %Y') if order.created_at else datetime.now().strftime('%B %d, %Y'),
                'status': order.status,
                'payment_status': order.payment_status,
                'shipping_address': shipping_address_str,
                'items': order_items,
                'total_amount': order.total_amount
            }
            
            email_service.send_order_confirmation(
                to_email=order.customer_email,
                order_data=order_data,
                customer_name=order.customer_name or "Customer"
            )
                
        except Exception:
            pass
        
    except Exception:
        db.rollback()

def handle_failed_payment(data: Dict[str, Any], db: Session):
    try:
        reference = data.get("reference")
        
        order = db.query(Order).filter(Order.payment_reference == reference).first()
        if not order:
            return
        
        order.payment_status = "failed"
        
        transaction_date = parse_datetime(data.get("transaction_date"))
        
        transaction = Transaction(
            order_id=order.id,
            reference=reference,
            amount=data.get("amount", 0) / 100,
            currency=data.get("currency", "NGN"),
            status="failed",
            gateway_response=data.get("gateway_response"),
            channel=data.get("channel"),
            customer_email=data.get("customer", {}).get("email"),
            transaction_date=transaction_date
        )
        
        db.add(transaction)
        db.commit()
        
    except Exception:
        db.rollback()

@router.get("/order/{order_number}")
async def get_order(
    order_number: str,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.get("/user/{user_id}/orders")
async def get_user_orders(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        orders = db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for order in orders:
            items_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()
            
            shipping_address = db.query(Address).filter(Address.id == order.shipping_address_id).first()
            shipping_info = "Not available"
            if shipping_address:
                shipping_info = f"{shipping_address.city}, {shipping_address.state}"
            
            result.append({
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "status": order.status,
                "payment_status": order.payment_status,
                "shipping_info": shipping_info,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "items_count": items_count
            })
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user orders: {str(e)}"
        )

@router.post("/send-order-email")
async def send_order_email(
    request_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        order_number = request_data.get("order_number")
        email = request_data.get("email")
        customer_name = request_data.get("customer_name", "Customer")
        
        if not order_number or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order number and email are required"
            )
        
        order = db.query(Order).filter(Order.order_number == order_number).first()
        
        if not order:
            order_data = {
                'order_number': order_number,
                'order_date': datetime.now().strftime('%B %d, %Y'),
                'status': 'Processing',
                'payment_status': 'Paid',
                'shipping_address': 'Address will be confirmed shortly',
                'items': [{'name': 'Your Order', 'quantity': 1, 'price': request_data.get('total_amount', 0)}],
                'total_amount': request_data.get('total_amount', 0)
            }
        else:
            shipping_address = db.query(Address).filter(Address.id == order.shipping_address_id).first()
            shipping_address_str = ""
            if shipping_address:
                shipping_address_str = f"{shipping_address.street}, {shipping_address.city}, {shipping_address.state}, {shipping_address.country}"
            
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            
            order_data = {
                'order_number': order.order_number,
                'order_date': order.created_at.strftime('%B %d, %Y') if order.created_at else datetime.now().strftime('%B %d, %Y'),
                'status': order.status,
                'payment_status': order.payment_status,
                'shipping_address': shipping_address_str,
                'items': [
                    {
                        'name': item.product_name,
                        'quantity': item.quantity,
                        'price': float(item.price)
                    }
                    for item in order_items
                ],
                'total_amount': float(order.total_amount)
            }
        
        background_tasks.add_task(
            email_service.send_order_confirmation,
            to_email=email,
            order_data=order_data,
            customer_name=customer_name
        )
        
        return {
            "success": True,
            "message": "Order confirmation email sent",
            "order_number": order_number
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send order email: {str(e)}"
        )

# Debug endpoint to check revenue issues
@router.get("/debug/revenue-check")
async def debug_revenue_check(db: Session = Depends(get_db)):
    """Debug endpoint to check revenue calculation"""
    # Get all paid orders
    paid_orders = db.query(Order).filter(Order.payment_status == "paid").all()
    
    # Get all orders with their payment status
    all_orders = db.query(Order).all()
    
    paid_details = []
    for order in paid_orders:
        paid_details.append({
            "order_number": order.order_number,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        })
    
    # Get successful transactions
    successful_transactions = db.query(Transaction).filter(Transaction.status == "success").all()
    
    return {
        "total_paid_orders": len(paid_orders),
        "total_revenue_from_orders": sum(order.total_amount for order in paid_orders),
        "total_successful_transactions": len(successful_transactions),
        "total_revenue_from_transactions": sum(t.amount for t in successful_transactions),
        "all_orders_count": len(all_orders),
        "payment_status_breakdown": {
            "paid": len([o for o in all_orders if o.payment_status == "paid"]),
            "pending": len([o for o in all_orders if o.payment_status == "pending"]),
            "failed": len([o for o in all_orders if o.payment_status == "failed"])
        },
        "paid_orders_details": paid_details
    }
