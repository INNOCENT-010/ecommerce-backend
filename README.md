# Fashion Store - E-Commerce Application

A complete fashion e-commerce platform built with FastAPI, PostgreSQL, and modern web technologies.

## Features

✨ **Core Features**
- User Authentication with JWT
- Product Catalog with Categories & Filtering
- Shopping Cart Management
- Checkout System
- Order Management with Order History
- Payment Integration (Paystack, Stripe)
- Email Notifications
- Admin Dashboard
- Product Image Upload
- Responsive HTML Frontend

## Tech Stack

**Backend**
- FastAPI - Modern Python web framework
- PostgreSQL - Relational database
- SQLAlchemy - ORM
- Pydantic - Data validation
- JWT - Authentication

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 12+
- pip (Python package manager)

### 2. Clone/Create Project

```bash
cd "c:\Users\USER\OneDrive\Documents\oh polly clone"
```

### 3. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

You'll also need to install Jinja2 for templates:
```bash
pip install jinja2
```


**Update .env file:**
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```
DATABASE_URL=postgresql://user:password@localhost:5432/fashion_store
```

### 6. Set Environment Variables

Update `.env` with:
- Database URL
- Secret key (generate one: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Paystack keys (get from Stripe dashboard)
- Email credentials (SMTP)

### 7. Initialize Database

The database tables are created automatically when the app starts (via SQLAlchemy).

### 8. Run Application

```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or:
```bash
python main.py
```

Access the application:
- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc




## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user


### Orders
- `POST /api/orders/create` - Create order
- `GET /api/orders/` - Get user's orders
- `GET /api/orders/{id}` - Get order details
- `POST /api/orders/{id}/initiate-payment` - Start payment
- `POST /api/orders/{id}/confirm-payment` - Confirm payment


### Register & Login

## Email Setup

### Gmail Configuration
1. Enable 2-Factor Authentication
2. Create App Password
3. Use App Password in SMTP_PASSWORD

## Admin Dashboard

Access at `/admin` to:
- Add/Edit Products
- Manage Categories
- Add Product Images
- View Orders
- Monitor inventory

## Database Models

### User
- Email, name, password (hashed)
- Active status
- Multiple addresses
- Multiple orders

### Product
- Name, description, price
- Stock quantity
- Category
- Multiple images
- Order history

### Cart/CartItem
- Per-user shopping cart
- Items with quantity tracking
- Auto-save functionality

### Order/OrderItem
- Order number (auto-generated)
- Status (pending, paid, processing, shipped, delivered)
- Payment method & reference
- Items with prices at purchase time

### Address
- Street, city, state, country, postal code
- Default address flag
- Per-user



**Happy Building! 🚀**
