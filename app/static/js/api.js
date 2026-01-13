// API Helper Functions

const API_BASE_URL = '/api';

// Authentication functions
async function login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });
    return response.json();
}

async function register(fullName, email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            full_name: fullName,
            email,
            password
        })
    });
    return response.json();
}

// Get current user
async function getCurrentUser(token) {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

// Cart functions
async function getCart(token) {
    const response = await fetch(`${API_BASE_URL}/cart/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function addToCart(productId, quantity, token) {
    const response = await fetch(`${API_BASE_URL}/cart/add-item`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ product_id: productId, quantity })
    });
    return response.json();
}

async function updateCartItem(itemId, quantity, token) {
    const response = await fetch(`${API_BASE_URL}/cart/update-item/${itemId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ product_id: 0, quantity })
    });
    return response.json();
}

async function removeFromCart(itemId, token) {
    const response = await fetch(`${API_BASE_URL}/cart/remove-item/${itemId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

// Product functions
async function getProducts(categoryId = null, search = null, skip = 0, limit = 20) {
    let url = `${API_BASE_URL}/products/?`;
    if (categoryId) url += `category_id=${categoryId}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    url += `skip=${skip}&limit=${limit}`;
    
    const response = await fetch(url);
    return response.json();
}

async function getProduct(productId) {
    const response = await fetch(`${API_BASE_URL}/products/${productId}`);
    return response.json();
}

// Order functions
async function createOrder(paymentMethod, deliveryAddressId, token) {
    const response = await fetch(`${API_BASE_URL}/orders/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            payment_method: paymentMethod,
            delivery_address_id: deliveryAddressId
        })
    });
    return response.json();
}

async function getOrders(token) {
    const response = await fetch(`${API_BASE_URL}/orders/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function getOrder(orderId, token) {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

// Address functions
async function getAddresses(token) {
    const response = await fetch(`${API_BASE_URL}/addresses/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function addAddress(addressData, token) {
    const response = await fetch(`${API_BASE_URL}/addresses/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(addressData)
    });
    return response.json();
}

// Category functions
async function getCategories() {
    const response = await fetch(`${API_BASE_URL}/categories/`);
    return response.json();
}

// Payment functions
async function initiatePayment(orderId, token) {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}/initiate-payment`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function confirmPayment(orderId, paymentRef, token) {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}/confirm-payment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ payment_ref: paymentRef })
    });
    return response.json();
}
