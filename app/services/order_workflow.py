from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.orm import Order, OrderStatus, Courier
from app.services.notifications import notification_service

class OrderWorkflowService:
    """Service for managing order state transitions and workflow"""
    
    # Valid state transitions
    STATE_TRANSITIONS = {
        OrderStatus.CREATED: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
        OrderStatus.ASSIGNED: [OrderStatus.PICKED_UP, OrderStatus.CANCELLED],
        OrderStatus.PICKED_UP: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
        OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
        OrderStatus.DELIVERED: [],  # Terminal state
        OrderStatus.CANCELLED: []   # Terminal state
    }
    
    async def validate_transition(
        self,
        current_status: str,
        new_status: str
    ) -> bool:
        """Validate if status transition is allowed"""
        current_enum = OrderStatus(current_status)
        new_enum = OrderStatus(new_status)
        
        allowed_transitions = self.STATE_TRANSITIONS.get(current_enum, [])
        return new_enum in allowed_transitions
    
    async def update_order_status(
        self,
        db: AsyncSession,
        order_id: int,
        new_status: str,
        user_id: Optional[int] = None
    ) -> Dict:
        """Update order status with validation and notifications"""
        # Get order
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Validate transition
        is_valid = await self.validate_transition(order.status, new_status)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid transition from {order.status} to {new_status}"
            }
        
        # Update status
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        # Mark as completed if delivered
        if new_status == OrderStatus.DELIVERED:
            order.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(order)
        
        # Send notification to customer
        await notification_service.send_order_notification(
            db=db,
            user_id=order.customer_id,
            order_id=order.id,
            status=new_status
        )
        
        # If courier is assigned, notify courier too
        if order.courier_id:
            courier_result = await db.execute(
                select(Courier).where(Courier.id == order.courier_id)
            )
            courier = courier_result.scalar_one_or_none()
            if courier:
                await notification_service.create_notification(
                    db=db,
                    user_id=courier.user_id,
                    title=f"Order #{order.id} Status Update",
                    body=f"Order status changed from {old_status} to {new_status}"
                )
        
        return {
            "success": True,
            "order_id": order.id,
            "old_status": old_status,
            "new_status": new_status
        }
    
    async def cancel_order(
        self,
        db: AsyncSession,
        order_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> Dict:
        """Cancel an order"""
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Check if order can be cancelled
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return {
                "success": False,
                "error": f"Cannot cancel order with status {order.status}"
            }
        
        # Update to cancelled
        return await self.update_order_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.CANCELLED,
            user_id=user_id
        )
    
    async def assign_courier(
        self,
        db: AsyncSession,
        order_id: int,
        courier_id: int
    ) -> Dict:
        """Assign courier to order"""
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order.status != OrderStatus.CREATED:
            return {
                "success": False,
                "error": f"Can only assign courier to CREATED orders"
            }
        
        # Check courier exists
        courier_result = await db.execute(select(Courier).where(Courier.id == courier_id))
        courier = courier_result.scalar_one_or_none()
        
        if not courier:
            return {"success": False, "error": "Courier not found"}
        
        # Assign courier
        order.courier_id = courier_id
        order.status = OrderStatus.ASSIGNED
        await db.commit()
        
        # Notify customer
        await notification_service.send_order_notification(
            db=db,
            user_id=order.customer_id,
            order_id=order.id,
            status=OrderStatus.ASSIGNED
        )
        
        # Notify courier
        await notification_service.create_notification(
            db=db,
            user_id=courier.user_id,
            title="New Order Assigned",
            body=f"Order #{order.id} has been assigned to you"
        )
        
        return {
            "success": True,
            "order_id": order.id,
            "courier_id": courier_id
        }
    
    async def get_active_orders(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        courier_id: Optional[int] = None
    ) -> List[Order]:
        """Get active (non-terminal) orders"""
        query = select(Order).where(
            Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
        )
        
        if user_id:
            query = query.where(Order.customer_id == user_id)
        
        if courier_id:
            query = query.where(Order.courier_id == courier_id)
        
        result = await db.execute(query.order_by(Order.created_at.desc()))
        return result.scalars().all()

order_workflow_service = OrderWorkflowService()
