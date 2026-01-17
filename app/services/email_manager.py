import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self):
        # Try to import Resend, fallback to SMTP
        try:
            import resend
            resend.api_key = os.getenv("RESEND_API_KEY")
            if resend.api_key:
                self.use_resend = True
                self.from_email = f"BLOOM G WOMEN <{os.getenv('SMTP_FROM_EMAIL', 'hello@bloomg.com')}>"
                print("✅ Using Resend for emails")
            else:
                self.use_resend = False
                print("⚠️ Resend API key not found, falling back to SMTP")
        except ImportError:
            self.use_resend = False
            print("⚠️ Resend not installed, falling back to SMTP")
    
    def send_resend_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using Resend API"""
        try:
            import resend
            
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            print(f"✅ Resend: Email sent! ID: {response['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Resend failed: {e}")
            return False
    
    def send_smtp_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Fallback to your existing SMTP service"""
        try:
            # Import your existing email service
            from app.services.email_service import email_service as smtp_service
            return smtp_service.send_email(to_email, subject, html_content, None)
        except Exception as e:
            print(f"❌ SMTP failed: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Main email sending method - tries Resend first, then SMTP"""
        if self.use_resend:
            success = self.send_resend_email(to_email, subject, html_content)
            if success:
                return True
        
        # Fallback to SMTP
        return self.send_smtp_email(to_email, subject, html_content)
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """Send verification code email - using your existing template"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Code - BLOOM&G</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .logo {
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .content {
                    padding: 40px;
                }
                .code-box {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px 0;
                    text-align: center;
                    border: 2px dashed #667eea;
                }
                .verification-code {
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    letter-spacing: 8px;
                    margin: 20px 0;
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    color: #666;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">BLOOM&G</div>
                    <h1>Your Verification Code</h1>
                    <p>Use this code to complete your sign in</p>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    <p>You requested a verification code to sign in to BLOOM&G.</p>
                    
                    <div class="code-box">
                        <p>Your 6-digit verification code is:</p>
                        <div class="verification-code">{{ code }}</div>
                        <p>This code will expire in 10 minutes.</p>
                    </div>
                    
                    <p>If you didn't request this code, please ignore this email.</p>
                    <p>For security reasons, do not share this code with anyone.</p>
                    
                    <p>Best regards,<br>The BLOOM&G Team</p>
                </div>
                
                <div class="footer">
                    <p>©️ 2024 BLOOM&G Store. All rights reserved.</p>
                    <p>123 Fashion Street, Lagos, Nigeria</p>
                    <p>Need help? Contact us at support@bloomg.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template_data = {'code': code}
        html_content = Template(html_template).render(**template_data)
        subject = f"Your BLOOM&G Verification Code: {code}"
        
        print(f"📧 Sending verification code to {to_email}: {code}")
        return self.send_email(to_email, subject, html_content)
    
    def send_order_confirmation(
        self,
        to_email: str,
        order_data: Dict[str, Any],
        customer_name: str
    ) -> bool:
        """Send order confirmation - using your existing template"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Order Confirmation - BLOOM&G</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .logo {
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .content {
                    padding: 40px;
                }
                .order-info {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }
                .order-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                .total {
                    font-size: 18px;
                    font-weight: bold;
                    color: #667eea;
                    text-align: right;
                    margin-top: 20px;
                }
                .button {
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    color: #666;
                    font-size: 14px
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">BLOOM&G</div>
                    <h1>Order Confirmed! 🎉</h1>
                    <p>Thank you for your purchase!</p>
                </div>
                
                <div class="content">
                    <p>Hi <strong>{{ customer_name }}</strong>,</p>
                    <p>Your order has been confirmed and is being processed. Here are your order details:</p>
                    
                    <div class="order-info">
                        <h3>Order #{{ order_number }}</h3>
                        <p><strong>Date:</strong> {{ order_date }}</p>
                        <p><strong>Status:</strong> {{ status }}</p>
                        <p><strong>Payment:</strong> {{ payment_status }}</p>
                        
                        <h4>Shipping Address:</h4>
                        <p>{{ shipping_address }}</p>
                        
                        <h4>Order Items:</h4>
                        {% for item in items %}
                        <div class="order-item">
                            <div>
                                <strong>{{ item.name }}</strong><br>
                                <small>Quantity: {{ item.quantity }}</small>
                            </div>
                            <div>₦{{ "%.2f"|format(item.price * item.quantity) }}</div>
                        </div>
                        {% endfor %}
                        
                        <div class="total">
                            Total: ₦{{ "%.2f"|format(total_amount) }}
                        </div>
                    </div>
                    
                    <p>You can track your order using this link:</p>
                    <a href="{{ track_order_url }}" class="button">Track Your Order</a>
                    
                    <p>If you have any questions, please contact our support team at support@bloomg.com</p>
                    
                    <p>Best regards,<br>The BLOOM&G Team</p>
                </div>
                
                <div class="footer">
                    <p>©️ 2024 BLOOM&G Store. All rights reserved.</p>
                    <p>123 Fashion Street, Lagos, Nigeria</p>
                    <p>Need help? Contact us at support@bloomg.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template_data = {
            'customer_name': customer_name,
            'order_number': order_data.get('order_number', ''),
            'order_date': order_data.get('order_date', datetime.now().strftime('%B %d, %Y')),
            'status': order_data.get('status', 'Processing'),
            'payment_status': order_data.get('payment_status', 'Paid'),
            'shipping_address': order_data.get('shipping_address', ''),
            'items': order_data.get('items', []),
            'total_amount': order_data.get('total_amount', 0),
            'track_order_url': f"{os.getenv('FRONTEND_URL', 'https://ecommerce-frontend-ic8e.vercel.app')}/orders/{order_data.get('order_number', '')}"
        }
        
        html_content = Template(html_template).render(**template_data)
        subject = f"Order Confirmation #{order_data.get('order_number', '')} - BLOOM&G"
        
        return self.send_email(to_email, subject, html_content)

# Create instance
email_manager = EmailManager()