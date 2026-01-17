# app/services/email_service.py - UPDATED FOR PORT 587 WITH STARTTLS
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from jinja2 import Template

# Import your settings
from app.core.config import settings  # Adjust import path as needed

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Use settings instead of os.getenv()
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT  # This will be 587
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME
        self.from_email = settings.SMTP_FROM_EMAIL
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Email will not be sent.")
                print(f"⚠️ SMTP credentials missing. Would send email to {to_email} with subject: {subject}")
                return False
            
            print(f"📧 Attempting to send email via {self.smtp_host}:{self.smtp_port}...")
            print(f"  To: {to_email}")
            print(f"  From: {self.from_name} <{self.from_email}>")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Handle different ports - ONLY CHANGED THIS SECTION
            if self.smtp_port == 465:
                # Keep existing SSL logic for port 465
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    print(f"🔐 Using SSL encryption (port 465)...")
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            elif self.smtp_port == 587:
                # NEW: Port 587 with STARTTLS
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    print(f"🔐 Using STARTTLS (port 587)...")
                    server.ehlo()  # Identify ourselves to the SMTP server
                    server.starttls()  # Upgrade to secure connection
                    server.ehlo()  # Re-identify ourselves after TLS
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Fallback for other ports
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    print(f"🔐 Using port {self.smtp_port}...")
                    if self.smtp_port == 25 or self.smtp_port == 2525:
                        # Some services use unencrypted or alternative ports
                        server.login(self.smtp_user, self.smtp_password)
                    else:
                        # Try STARTTLS if available
                        try:
                            server.starttls()
                            server.login(self.smtp_user, self.smtp_password)
                        except:
                            # Fallback to plain login if STARTTLS fails
                            server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    # KEEP ALL EXISTING METHODS EXACTLY AS THEY ARE
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """Send verification code email"""
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
        
        text_template = """
        Verification Code - BLOOM&G
        
        Hello,
        
        You requested a verification code to sign in to BLOOM&G.
        
        Your 6-digit verification code is:
        
        {{ code }}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        For security reasons, do not share this code with anyone.
        
        Best regards,
        The BLOOM&G Team
        
        ©️ 2024 BLOOM&G Store. All rights reserved.
        123 Fashion Street, Lagos, Nigeria
        Need help? Contact us at support@bloomg.com
        """
        
        template_data = {
            'code': code
        }
        
        html_content = Template(html_template).render(**template_data)
        text_content = Template(text_template).render(**template_data)
        
        subject = f"Your BLOOM&G Verification Code: {code}"
        
        # Print for debugging
        print(f"📧 Sending verification code to {to_email}: {code}")
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_order_confirmation(
        self,
        to_email: str,
        order_data: Dict[str, Any],
        customer_name: str
    ) -> bool:
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
                    font-size: 14px;
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
        
        text_template = """
        Order Confirmation - BLOOM&G
        
        Hi {{ customer_name }},
        
        Your order has been confirmed and is being processed.
        
        Order Details:
        --------------
        Order Number: {{ order_number }}
        Date: {{ order_date }}
        Status: {{ status }}
        Payment: {{ payment_status }}
        
        Shipping Address:
        {{ shipping_address }}
        
        Order Items:
        {% for item in items %}
        - {{ item.name }} (x{{ item.quantity }}) - ₦{{ "%.2f"|format(item.price * item.quantity) }}
        {% endfor %}
        
        Total Amount: ₦{{ "%.2f"|format(total_amount) }}
        
        Track your order: {{ track_order_url }}
        
        If you have any questions, please contact our support team at support@bloomg.com
        
        Best regards,
        The BLOOM&G Team
        
        ©️ 2024 BLOOM&G Store. All rights reserved.
        123 Fashion Street, Lagos, Nigeria
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
            'track_order_url': f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/orders/{order_data.get('order_number', '')}"
        }
        
        html_content = Template(html_template).render(**template_data)
        text_content = Template(text_template).render(**template_data)
        
        subject = f"Order Confirmation #{order_data.get('order_number', '')} - BLOOM&G"
        return self.send_email(to_email, subject, html_content, text_content)

email_service = EmailService()