from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Optional, Dict
from datetime import datetime
from app.models.orm import Notification, User
from app.websockets.server import manager

class NotificationService:
    """Service for managing notifications"""
    
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "info",
        data: Optional[Dict] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        # Send real-time notification via WebSocket
        await self._send_websocket_notification(user_id, notification)
        
        return notification
    
    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """Mark notification as read"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.is_read = True
            await db.commit()
            await db.refresh(notification)
        
        return notification
    
    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Mark all notifications as read for a user"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            count += 1
        
        await db.commit()
        return count
    
    async def delete_notification(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Delete a notification"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if notification:
            await db.delete(notification)
            await db.commit()
            return True
        
        return False
    
    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Get count of unread notifications"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        return len(result.scalars().all())
    
    async def send_order_notification(
        self,
        db: AsyncSession,
        user_id: int,
        order_id: int,
        status: str
    ):
        """Send order status notification"""
        titles = {
            "created": "Order Created",
            "assigned": "Courier Assigned",
            "picked_up": "Order Picked Up",
            "in_transit": "On the Way",
            "delivered": "Order Delivered",
            "cancelled": "Order Cancelled"
        }
        
        bodies = {
            "created": f"Your order #{order_id} has been created successfully.",
            "assigned": f"A courier has been assigned to your order #{order_id}.",
            "picked_up": f"Your order #{order_id} has been picked up.",
            "in_transit": f"Your order #{order_id} is on the way!",
            "delivered": f"Your order #{order_id} has been delivered.",
            "cancelled": f"Your order #{order_id} has been cancelled."
        }
        
        title = titles.get(status, "Order Update")
        body = bodies.get(status, f"Order #{order_id} status: {status}")
        
        await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            body=body,
            notification_type="order_update",
            data={"order_id": order_id, "status": status}
        )
    
    async def _send_websocket_notification(
        self,
        user_id: int,
        notification: Notification
    ):
        """Send notification via WebSocket"""
        try:
            await manager.send_personal_message(
                message={
                    "type": "notification",
                    "id": notification.id,
                    "title": notification.title,
                    "body": notification.body,
                    "created_at": str(notification.created_at)
                },
                user_id=str(user_id)
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

notification_service = NotificationService()
