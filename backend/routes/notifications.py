from fastapi import APIRouter, HTTPException, Depends
from services.notification_service import notification_service
from utils.auth import get_current_user, require_role
from pydantic import BaseModel
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class PushNotificationRequest(BaseModel):
    device_tokens: List[str]
    title: str
    body: str
    data: dict = {}

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    content: str
    html_content: str = None

class SMSRequest(BaseModel):
    to_phone: str
    message: str

@router.post("/push")
async def send_push(
    request: PushNotificationRequest,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Send push notification"""
    try:
        result = await notification_service.send_push_notification(
            device_tokens=request.device_tokens,
            title=request.title,
            body=request.body,
            data=request.data
        )
        return result
    except Exception as e:
        logger.error(f"Push notification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send push notification")

@router.post("/email")
async def send_email(
    request: EmailRequest,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Send email"""
    try:
        result = await notification_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            content=request.content,
            html_content=request.html_content
        )
        return result
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

@router.post("/sms")
async def send_sms(
    request: SMSRequest,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Send SMS"""
    try:
        result = await notification_service.send_sms(
            to_phone=request.to_phone,
            message=request.message
        )
        return result
    except Exception as e:
        logger.error(f"SMS sending error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")
