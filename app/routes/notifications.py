from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.models.orm import User, Notification
from app.dependencies import get_current_user
from app.services.notifications import notification_service
from pydantic import BaseModel

router = APIRouter()

class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    is_read: bool
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's notifications"""
    notifications = await notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    
    return [
        NotificationResponse(
            id=n.id,
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            created_at=str(n.created_at)
        ) for n in notifications
    ]

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications"""
    count = await notification_service.get_unread_count(
        db=db,
        user_id=current_user.id
    )
    return {"unread_count": count}

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read"""
    notification = await notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    count = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    
    return {"message": f"Marked {count} notifications as read"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete notification"""
    success = await notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}
