"""
Email Notification Service (SendGrid Mock)
In production, install: pip install sendgrid
"""
from typing import Dict, Optional, List
from datetime import datetime

class EmailService:
    """Email service using SendGrid (mock implementation)"""
    
    def __init__(self):
        # In production: 
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        # self.sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        self.from_email = "noreply@loop-logistics.com"
        print("📧 Email Service initialized (MOCK MODE)")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> Dict:
        """Send email"""
        
        # MOCK: In production
        # message = Mail(
        #     from_email=from_email or self.from_email,
        #     to_emails=to_email,
        #     subject=subject,
        #     html_content=html_content
        # )
        # response = self.sg.send(message)
        
        print(f"📧 [MOCK] Email sent to: {to_email}")
        print(f"   Subject: {subject}")
        
        return {
            "success": True,
            "message_id": f"mock_email_{datetime.utcnow().timestamp()}",
            "to": to_email,
            "mock": True
        }
    
    async def send_order_confirmation(
        self,
        to_email: str,
        order_id: int,
        order_details: Dict
    ) -> Dict:
        """Send order confirmation email"""
        
        html_content = f"""
        <html>
        <body>
            <h2>Order Confirmation</h2>
            <p>Your order #{order_id} has been confirmed!</p>
            <h3>Details:</h3>
            <ul>
                <li>Pickup: {order_details.get('pickup_address', 'N/A')}</li>
                <li>Delivery: {order_details.get('delivery_address', 'N/A')}</li>
                <li>Price: ${order_details.get('price', 0)}</li>
            </ul>
            <p>Thank you for using LOOP Logistics!</p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Order #{order_id} Confirmed",
            html_content=html_content
        )
    
    async def send_delivery_notification(
        self,
        to_email: str,
        order_id: int,
        status: str
    ) -> Dict:
        """Send delivery status update email"""
        
        status_messages = {
            "assigned": "A courier has been assigned to your order!",
            "picked_up": "Your order has been picked up!",
            "in_transit": "Your order is on the way!",
            "delivered": "Your order has been delivered!",
        }
        
        message = status_messages.get(status, f"Order status: {status}")
        
        html_content = f"""
        <html>
        <body>
            <h2>Order Update</h2>
            <p>{message}</p>
            <p>Order #{order_id}</p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Order #{order_id} Update",
            html_content=html_content
        )
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> Dict:
        """Send welcome email to new users"""
        
        html_content = f"""
        <html>
        <body>
            <h1>Welcome to LOOP Logistics, {user_name}!</h1>
            <p>Thank you for joining us. We're excited to have you on board.</p>
            <h3>Getting Started:</h3>
            <ul>
                <li>Create your first order</li>
                <li>Track deliveries in real-time</li>
                <li>Rate your courier experience</li>
            </ul>
            <p>Need help? Contact support@loop-logistics.com</p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Welcome to LOOP Logistics!",
            html_content=html_content
        )

email_service = EmailService()
