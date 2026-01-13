# /schemas/admin.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OrderItemPreview(BaseModel):
    name: str
    quantity: int
    size: Optional[str] = None
    color: Optional[str] = None
    price: float
    image: Optional[str] = None

class EnhancedOrder(BaseModel):
    id: int
    order_number: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    total_amount: float
    currency: str
    status: str
    payment_status: str
    payment_method: str
    created_at: str
    paid_at: Optional[str]
    items_count: int
    total_quantity: int
    has_size: bool
    has_color: bool
    size_variants: List[str]
    color_variants: List[str]
    shipping_location: str
    shipping_state: str
    shipping_city: str
    items_preview: List[OrderItemPreview]
    notes: Optional[str]
    
    class Config:
        from_attributes = True

class OrderSummary(BaseModel):
    id: int
    order_number: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    total_amount: float
    status: str
    payment_status: str
    created_at: str
    items_count: int
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_users: int
    total_products: int
    orders_by_status: Dict[str, int]
    recent_orders: int
    currency: str
    
    class Config:
        from_attributes = True

class PaginatedOrders(BaseModel):
    orders: List[EnhancedOrder]
    pagination: Dict[str, Any]