# Fashion Store - E-Commerce Application

A complete fashion e-commerce platform built with FastAPI, PostgreSQL, and modern web technologies.

## Features

✨ **Core Features**
- User Authentication with JWT
- Product Catalog with Categories & Filtering
- Shopping Cart Management
- Checkout System
- Order Management with Order History
- Payment Integration (Stripe, Bank Transfer)
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
- Stripe - Payment processing

**Frontend**
- HTML5 / CSS3 / JavaScript
- Bootstrap 5 - Responsive design
- Jinja2 - Template engine

## Project Structure

```
app/
├── api/                 # API routes
│   ├── auth.py         # Authentication endpoints
│   ├── products.py     # Product endpoints
│   ├── categories.py   # Category endpoints
│   ├── cart.py         # Shopping cart endpoints
│   ├── orders.py       # Order endpoints
│   └── addresses.py    # Address management
├── core/               # Core utilities
│   ├── config.py       # Configuration
│   ├── database.py     # Database setup
│   └── security.py     # Security utilities
├── models/             # Database models
│   └── models.py       # SQLAlchemy models
├── schemas/            # Pydantic schemas
│   └── schemas.py      # Data validation schemas
├── services/           # Business logic
│   ├── email_service.py    # Email handling
│   └── payment_service.py  # Payment processing
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── products.html  # Products listing
│   ├── product_detail.html
│   ├── cart.html      # Shopping cart
│   ├── checkout.html  # Checkout process
│   ├── payment.html   # Payment page
│   ├── order_detail.html
│   ├── orders.html    # Order history
│   ├── login.html     # Login page
│   ├── register.html  # Registration page
│   └── admin.html     # Admin dashboard
├── static/            # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js     # API client
│       └── auth.js    # Auth utilities
└── main.py           # Application entry point
```

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

### 5. Setup PostgreSQL Database

**Create database:**
```sql
CREATE DATABASE fashion_store;
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
- Stripe API keys (get from Stripe dashboard)
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

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fashion_store

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_API_KEY=sk_test_your_key
STRIPE_PUBLIC_KEY=pk_test_your_key

# Email (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@fashionstore.com

# App
APP_NAME=Fashion Store
DEBUG=True
```

### Generate Secret Key

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Products
- `GET /api/products/` - List products (with filtering)
- `GET /api/products/{id}` - Get product details
- `POST /api/products/` - Create product (admin)
- `PUT /api/products/{id}` - Update product (admin)
- `POST /api/products/{id}/upload-image` - Upload product image

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category (admin)
- `GET /api/categories/{id}` - Get category

### Shopping Cart
- `GET /api/cart/` - Get user's cart
- `POST /api/cart/add-item` - Add item to cart
- `PUT /api/cart/update-item/{id}` - Update item quantity
- `DELETE /api/cart/remove-item/{id}` - Remove from cart
- `DELETE /api/cart/clear` - Clear entire cart

### Orders
- `POST /api/orders/create` - Create order
- `GET /api/orders/` - Get user's orders
- `GET /api/orders/{id}` - Get order details
- `POST /api/orders/{id}/initiate-payment` - Start payment
- `POST /api/orders/{id}/confirm-payment` - Confirm payment

### Addresses
- `GET /api/addresses/` - Get user's addresses
- `POST /api/addresses/` - Add address
- `GET /api/addresses/{id}` - Get address
- `PUT /api/addresses/{id}` - Update address
- `DELETE /api/addresses/{id}` - Delete address

## Frontend Pages

- **Home** - `/` - Landing page with featured products
- **Products** - `/products` - Product listing with filters
- **Product Detail** - `/product/{id}` - Single product view
- **Cart** - `/cart` - Shopping cart
- **Checkout** - `/checkout` - Order creation & address selection
- **Payment** - `/payment/{id}` - Payment processing
- **Orders** - `/orders` - Order history
- **Order Detail** - `/order/{id}` - Order details
- **Admin** - `/admin` - Admin dashboard
- **Login** - `/login` - User login
- **Register** - `/register` - User registration

## Usage Examples

### Register & Login

```javascript
// Register
const registerResponse = await fetch('/api/auth/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        full_name: 'John Doe',
        email: 'john@example.com',
        password: 'securepass123'
    })
});

// Login
const loginResponse = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'john@example.com',
        password: 'securepass123'
    })
});

const token = (await loginResponse.json()).access_token;
localStorage.setItem('access_token', token);
```

### Add to Cart

```javascript
const addResponse = await fetch('/api/cart/add-item', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        product_id: 1,
        quantity: 2
    })
});
```

### Create Order

```javascript
const orderResponse = await fetch('/api/orders/create', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        payment_method: 'bank_transfer',
        delivery_address_id: 1
    })
});
```

## Payment Integration

### Stripe Setup
1. Get API keys from [Stripe Dashboard](https://dashboard.stripe.com)
2. Add to `.env`
3. Stripe public key in payment.html

### Bank Transfer (Nigeria)
- Reference number auto-generated
- Account details displayed to user
- Manual verification required

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

## Development Tips

1. **Database Migrations** - Use Alembic for production migrations
2. **Testing** - Add pytest for unit testing
3. **Caching** - Use Redis for cart/session caching
4. **Logging** - Configure logging for debugging
5. **Security** - Use HTTPS in production, update SECRET_KEY

## Troubleshooting

**Database Connection Error**
```bash
# Verify PostgreSQL is running
# Check DATABASE_URL in .env
# Test connection: psql -U user -d fashion_store
```

**Stripe Errors**
- Verify API keys in .env
- Check Stripe account status
- Ensure amount is in correct format (cents)

**Email Not Sending**
- Enable Less Secure Apps (if using Gmail)
- Verify SMTP credentials
- Check firewall/email filters

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Implement CSRF protection
- [ ] Add input validation
- [ ] Update dependencies regularly
- [ ] Use strong password requirements

## Future Enhancements

- [ ] Payment gateway for Visa/bank transfers
- [ ] Email verification
- [ ] Wishlist/favorites
- [ ] Product reviews & ratings
- [ ] Coupon/discount system
- [ ] Inventory notifications
- [ ] SMS notifications
- [ ] Analytics dashboard
- [ ] Mobile app
- [ ] Real-time notifications

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check logs for error messages

## License

This project is provided as-is for educational and development purposes.

---

**Happy Building! 🚀**
