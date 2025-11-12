import httpx
import os
from typing import Dict, List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY", "")
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    
    async def send_push_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Dict = None
    ) -> Dict:
        """Send push notification via Firebase FCM"""
        if not self.fcm_server_key:
            logger.warning("FCM server key not configured")
            return {"success": False, "error": "FCM not configured"}
        
        try:
            payload = {
                "registration_ids": device_tokens,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default"
                },
                "data": data or {},
                "priority": "high"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers={
                        "Authorization": f"key={self.fcm_server_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                result = response.json()
                logger.info(f"Push notification sent: {result}")
                return {
                    "success": result.get("success", 0) > 0,
                    "results": result
                }
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        html_content: str = None
    ) -> Dict:
        """Send email via SendGrid"""
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured")
            return {"success": False, "error": "SendGrid not configured"}
        
        try:
            payload = {
                "personalizations": [{
                    "to": [{"email": to_email}],
                    "subject": subject
                }],
                "from": {"email": "noreply@loop-logistics.com", "name": "LOOP Logistics"},
                "content": [
                    {"type": "text/plain", "value": content}
                ]
            }
            
            if html_content:
                payload["content"].append({"type": "text/html", "value": html_content})
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                success = response.status_code == 202
                logger.info(f"Email sent: {success}")
                return {"success": success}
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict:
        """Send SMS via Twilio"""
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("Twilio credentials not configured")
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            from_phone = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json",
                    data={
                        "From": from_phone,
                        "To": to_phone,
                        "Body": message
                    },
                    auth=(self.twilio_account_sid, self.twilio_auth_token)
                )
                
                success = response.status_code in [200, 201]
                logger.info(f"SMS sent: {success}")
                return {"success": success, "data": response.json()}
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_order_notification(
        self,
        user_id: str,
        order_id: str,
        notification_type: str,
        channels: List[str] = None
    ):
        """Send multi-channel notification for order events"""
        # This would fetch user details and send via requested channels
        # Implementation depends on database queries
        logger.info(f"Order notification: {notification_type} for order {order_id}")
        pass

notification_service = NotificationService()
