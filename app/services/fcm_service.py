"""
FCM Push Notification Service (Simplified Mock)
In production, install: pip install firebase-admin
"""
from typing import List, Dict, Optional
from datetime import datetime

import os
import firebase_admin
from firebase_admin import credentials, messaging

class FCMService:
    """Firebase Cloud Messaging service"""
    
    def __init__(self):
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
        if cred_path and os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.is_initialized = True
                print("📱 FCM Service initialized (PRODUCTION MODE)")
            except Exception as e:
                self.is_initialized = False
                print(f"📱 FCM Service init failed: {e}. Falling back to MOCK MODE.")
        else:
            self.is_initialized = False
            print("📱 FCM Service initialized (MOCK MODE - Missing Credentials)")
    
    async def send_push_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """Send push notification to a device"""
        
        if self.is_initialized:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    token=device_token
                )
                response = messaging.send(message)
                return {
                    "success": True,
                    "message_id": response,
                    "device_token": device_token,
                    "mock": False
                }
            except Exception as e:
                print(f"📱 Error sending push notification: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "mock": False
                }
        else:
            print(f"📱 [MOCK] Push notification sent to {device_token[:20]}...")
            print(f"   Title: {title}")
            print(f"   Body: {body}")
            return {
                "success": True,
                "message_id": f"mock_fcm_{datetime.utcnow().timestamp()}",
                "device_token": device_token,
                "mock": True
            }
    
    async def send_multicast(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """Send push notification to multiple devices"""
        
        if self.is_initialized:
            try:
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    tokens=device_tokens
                )
                response = messaging.send_multicast(message)
                return {
                    "success": True,
                    "success_count": response.success_count,
                    "failure_count": response.failure_count,
                    "mock": False
                }
            except Exception as e:
                print(f"📱 Error sending multicast: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "mock": False
                }
        else:
            print(f"📱 [MOCK] Multicast to {len(device_tokens)} devices")
            print(f"   Title: {title}")
            return {
                "success": True,
                "success_count": len(device_tokens),
                "failure_count": 0,
                "mock": True
            }
    
    async def subscribe_to_topic(
        self,
        device_tokens: List[str],
        topic: str
    ) -> Dict:
        """Subscribe devices to a topic"""
        
        if self.is_initialized:
            try:
                response = messaging.subscribe_to_topic(device_tokens, topic)
                return {
                    "success": True,
                    "topic": topic,
                    "success_count": response.success_count,
                    "mock": False
                }
            except Exception as e:
                print(f"📱 Error subscribing to topic: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "mock": False
                }
        else:
            print(f"📱 [MOCK] Subscribed {len(device_tokens)} devices to topic: {topic}")
            return {
                "success": True,
                "topic": topic,
                "mock": True
            }
    
    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """Send notification to all subscribers of a topic"""
        
        if self.is_initialized:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    topic=topic
                )
                response = messaging.send(message)
                return {
                    "success": True,
                    "message_id": response,
                    "topic": topic,
                    "mock": False
                }
            except Exception as e:
                print(f"📱 Error sending to topic: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "mock": False
                }
        else:
            print(f"📱 [MOCK] Topic broadcast: {topic}")
            print(f"   Title: {title}")
            return {
                "success": True,
                "topic": topic,
                "mock": True
            }

fcm_service = FCMService()
