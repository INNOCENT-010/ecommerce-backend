// Authentication Helper Functions

function saveToken(token) {
    localStorage.setItem('access_token', token);
    updateAuthUI();
}

function getToken() {
    return localStorage.getItem('access_token');
}

function logout() {
    localStorage.removeItem('access_token');
    updateAuthUI();
    window.location.href = '/';
}

function isAuthenticated() {
    return !!getToken();
}

function updateAuthUI() {
    const token = getToken();
    const authLink = document.getElementById('auth-link');
    const logoutLink = document.getElementById('logout-link');
    
    if (token) {
        if (authLink) authLink.style.display = 'none';
        if (logoutLink) logoutLink.style.display = 'block';
        updateCartCount();
    } else {
        if (authLink) authLink.style.display = 'block';
        if (logoutLink) logoutLink.style.display = 'none';
    }
}

async function updateCartCount() {
    const token = getToken();
    if (!token) return;
    
    try {
        const cart = await getCart(token);
        const count = cart.items ? cart.items.length : 0;
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = count;
        }
    } catch (error) {
        console.error('Error updating cart count:', error);
    }
}

// Initialize auth UI on page load
document.addEventListener('DOMContentLoaded', function() {
    updateAuthUI();
});

// Helper function to check if token is valid
async function validateToken() {
    const token = getToken();
    if (!token) return false;
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        return response.ok;
    } catch {
        return false;
    }
}

// Require authentication
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
    }
}
