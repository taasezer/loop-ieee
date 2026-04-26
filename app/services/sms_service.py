"""
SMS Notification Service (Twilio Mock)
In production, install: pip install twilio
"""
from typing import Dict
from datetime import datetime
import random

import os
from twilio.rest import Client

class SMSService:
    """SMS service using Twilio"""
    
    def __init__(self):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_PHONE_NUMBER', "+1234567890")
        
        if account_sid and auth_token:
            self.client = Client(account_sid, auth_token)
            print("📱 SMS Service initialized (PRODUCTION MODE)")
        else:
            self.client = None
            print("📱 SMS Service initialized (MOCK MODE - Missing Credentials)")
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> Dict:
        """Send SMS message"""
        
        if self.client:
            try:
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
                return {
                    "success": True,
                    "message_sid": message_obj.sid,
                    "to": to_number,
                    "mock": False
                }
            except Exception as e:
                print(f"📱 Error sending SMS: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "mock": False
                }
        else:
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
