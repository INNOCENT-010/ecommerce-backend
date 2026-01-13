# app/models/models.py
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# ==================== CATEGORY MODEL ====================
class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


# ==================== USER MODEL ====================
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # ADDED: Phone number field
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")


# ==================== PRODUCT MODEL ====================
class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_active = Column(Boolean, default=True)
    is_new = Column(Boolean, default=True)
    is_sale = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


# ==================== PRODUCT IMAGE MODEL ====================
class ProductImage(Base):
    __tablename__ = "product-images"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="images")


# ==================== ADDRESS MODEL ====================
class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False, default="Nigeria")
    postal_code = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="shipping_address")


# ==================== CART ITEM MODEL ====================
class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


# ==================== ORDER MODEL (UPDATED FOR PAYSTACK) ====================
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    shipping_address_id = Column(Integer, ForeignKey("addresses.id"))
    
    # Order identification
    order_number = Column(String, unique=True, index=True, nullable=False)  # Custom order number like OH-202412-0001
    
    # Status fields
    status = Column(String, default="pending")  # pending, processing, shipped, delivered, cancelled
    payment_status = Column(String, default="pending")  # pending, paid, failed, refunded, partially_paid
    
    # Amount and currency
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="NGN")
    
    # Payment information
    payment_method = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True, unique=True, index=True)  # Paystack reference
    
    # Paystack specific fields
    paystack_authorization_url = Column(String, nullable=True)
    paystack_access_code = Column(String, nullable=True)
    paystack_transaction_id = Column(String, nullable=True)
    paystack_customer_email = Column(String, nullable=True)
    
    # Customer information (for guest checkout)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    
    # Additional order data stored as JSON
    order_data = Column(JSON, nullable=True)  # Store cart items, billing address, etc.
    
    # Timestamps
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    shipping_address = relationship("Address", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="order", cascade="all, delete-orphan")


# ==================== ORDER ITEM MODEL ====================
class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Additional product details at time of purchase
    product_name = Column(String, nullable=True)
    product_sku = Column(String, nullable=True)
    product_image = Column(String, nullable=True)
    
    # Product attributes
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ==================== TRANSACTION MODEL (NEW FOR PAYSTACK) ====================
class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    
    # Transaction reference
    reference = Column(String, unique=True, index=True, nullable=False)  # Paystack reference
    
    # Amount and currency
    amount = Column(Float, nullable=False)  # Amount in Naira (not kobo)
    currency = Column(String, default="NGN")
    
    # Status information
    status = Column(String, nullable=False)  # success, failed, abandoned, reversed
    gateway_response = Column(String, nullable=True)
    channel = Column(String, nullable=True)  # card, bank_transfer, ussd, etc.
    
    # Customer information
    customer_email = Column(String, nullable=False)
    customer_id = Column(String, nullable=True)  # Paystack customer ID
    
    # Technical details
    ip_address = Column(String, nullable=True)
    authorization_code = Column(String, nullable=True)
    card_last4 = Column(String, nullable=True)
    card_type = Column(String, nullable=True)
    bank = Column(String, nullable=True)
    
    # Timestamps
    transaction_date = Column(DateTime(timezone=True), nullable=True)  # When transaction occurred
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    order = relationship("Order", back_populates="transactions")