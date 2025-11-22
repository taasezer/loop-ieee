"""
SMS Notification Service (Twilio Mock)
In production, install: pip install twilio
"""
from typing import Dict
from datetime import datetime
import random

class SMSService:
    """SMS service using Twilio (mock implementation)"""
    
    def __init__(self):
        # In production:
        # from twilio.rest import Client
        # account_sid = os.environ['TWILIO_ACCOUNT_SID']
        # auth_token = os.environ['TWILIO_AUTH_TOKEN']
        # self.client = Client(account_sid, auth_token)
        # self.from_number = os.environ['TWILIO_PHONE_NUMBER']
        self.from_number = "+1234567890"
        print("📱 SMS Service initialized (MOCK MODE)")
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> Dict:
        """Send SMS message"""
        
        # MOCK: In production
        # message = self.client.messages.create(
        #     body=message,
        #     from_=self.from_number,
        #     to=to_number
        # )
        
        print(f"📱 [MOCK] SMS sent to: {to_number}")
        print(f"   Message: {message[:50]}...")
        
        return {
            "success": True,
            "message_sid": f"mock_sms_{datetime.utcnow().timestamp()}",
            "to": to_number,
            "mock": True
        }
    
    async def send_otp(
        self,
        to_number: str
    ) -> Dict:
        """Send OTP (One-Time Password) for verification"""
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        message = f"Your LOOP Logistics verification code is: {otp}. Valid for 10 minutes."
        
        result = await self.send_sms(to_number, message)
        result["otp"] = otp  # In production, store this in Redis with expiry
        
        return result
    
    async def send_order_update_sms(
        self,
        to_number: str,
        order_id: int,
        status: str
    ) -> Dict:
        """Send order status update via SMS"""
        
        status_messages = {
            "assigned": f"Order #{order_id}: Courier assigned! Track your delivery.",
            "picked_up": f"Order #{order_id}: Package picked up!",
            "in_transit": f"Order #{order_id}: On the way to you!",
            "delivered": f"Order #{order_id}: Delivered! Thank you!",
        }
        
        message = status_messages.get(status, f"Order #{order_id} status: {status}")
        
        return await self.send_sms(to_number, message)
    
    async def send_delivery_eta_sms(
        self,
        to_number: str,
        order_id: int,
        eta_minutes: int
    ) -> Dict:
        """Send ETA update via SMS"""
        
        message = f"Order #{order_id}: Your delivery will arrive in approximately {eta_minutes} minutes."
        
        return await self.send_sms(to_number, message)

sms_service = SMSService()
