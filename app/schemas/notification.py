"""Notification schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class NotificationCreateRequest(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str
    data: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
