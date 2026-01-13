# app/schemas/order.py - CORRECTED VERSION
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class CartItemSchema(BaseModel):
    product_id: Union[int, str]
    name: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    size: Optional[str] = None
    color: Optional[str] = None
    image: Optional[str] = None
    sku: Optional[str] = None
    
    @validator('product_id', pre=True)
    def convert_product_id(cls, v):
        if isinstance(v, str) and v.isdigit():
            try:
                return int(v)
            except ValueError:
                return v
        return v

class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[Union[int, str]]
    product_name: Optional[str]
    quantity: int
    price: float
    subtotal: float
    size: Optional[str] = None
    color: Optional[str] = None
    product_image: Optional[str] = None
    product_sku: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    cart_items: List[CartItemSchema] = Field(..., min_items=1)
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    email: EmailStr
    total_amount: float = Field(..., gt=0)
    currency: str = Field(default="NGN")
    customer_name: str
    customer_phone: str
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_email: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    total_amount: float
    currency: str
    status: str
    payment_status: str
    payment_reference: Optional[str]
    paystack_authorization_url: Optional[str] = None
    items: List[OrderItemResponse]
    shipping_address: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaystackInitializeResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaymentVerification(BaseModel):
    reference: str
    order_number: str