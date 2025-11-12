"""
Order service
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
import secrets
import logging

from app.models.order import Order, OrderStatus, OrderType
from app.repositories.order_repository import OrderRepository
from app.repositories.courier_repository import CourierRepository
from app.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    OrderException
)
from app.schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    OrderDetailResponse
)

logger = logging.getLogger(__name__)


class OrderService:
    """Order management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.courier_repo = CourierRepository(db)
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(3).upper()
        return f"ORD-{timestamp}-{random_part}"
    
    async def create_order(self, request: OrderCreateRequest, customer_id: UUID) -> OrderDetailResponse:
        """Create a new order"""
        logger.info(f"Creating order for customer: {customer_id}")
        
        # Calculate distance (simplified - would use map service in production)
        distance_km = self._calculate_distance(
            request.pickup_latitude,
            request.pickup_longitude,
            request.delivery_latitude,
            request.delivery_longitude
        )
        
        # Calculate pricing
        pricing = await self._calculate_pricing(distance_km, request.order_type)
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Create order data
        order_data = {
            "order_number": order_number,
            "customer_id": customer_id,
            "order_type": request.order_type,
            "status": OrderStatus.CREATED,
            
            # Pickup
            "pickup_address": request.pickup_address,
            "pickup_latitude": request.pickup_latitude,
            "pickup_longitude": request.pickup_longitude,
            "pickup_contact_name": request.pickup_contact_name,
            "pickup_contact_phone": request.pickup_contact_phone,
            "pickup_instructions": request.pickup_instructions,
            
            # Delivery
            "delivery_address": request.delivery_address,
            "delivery_latitude": request.delivery_latitude,
            "delivery_longitude": request.delivery_longitude,
            "delivery_contact_name": request.delivery_contact_name,
            "delivery_contact_phone": request.delivery_contact_phone,
            "delivery_instructions": request.delivery_instructions,
            
            # Package
            "package_description": request.package_description,
            "package_weight": request.package_weight,
            "package_dimensions": request.package_dimensions,
            "package_value": request.package_value,
            "fragile": request.fragile,
            
            # Distance and pricing
            "distance_km": distance_km,
            "base_price": pricing["base_price"],
            "distance_price": pricing["distance_price"],
            "surge_multiplier": pricing["surge_multiplier"],
            "weather_multiplier": pricing["weather_multiplier"],
            "total_price": pricing["total_price"],
            "platform_commission": pricing["platform_commission"],
            "courier_earnings": pricing["courier_earnings"],
            
            # Payment
            "payment_method": request.payment_method,
            "payment_status": "pending",
            
            # Scheduling
            "scheduled_pickup_time": request.scheduled_pickup_time,
            "scheduled_delivery_time": request.scheduled_delivery_time,
            
            # Notes
            "customer_notes": request.customer_notes,
            "promo_code": request.promo_code
        }
        
        order = await self.order_repo.create(order_data)
        
        # Update status to pending assignment
        await self.order_repo.update(order.id, {"status": OrderStatus.PENDING_ASSIGNMENT})
        
        await self.db.commit()
        
        logger.info(f"Order created successfully: {order.id}")
        
        # TODO: Trigger courier assignment
        # await self.assign_courier(order.id)
        
        return OrderDetailResponse.from_orm(order)
    
    async def get_order(self, order_id: UUID) -> OrderDetailResponse:
        """Get order by ID"""
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order")
        return OrderDetailResponse.from_orm(order)
    
    async def update_order_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        courier_id: Optional[UUID] = None
    ) -> OrderDetailResponse:
        """Update order status"""
        logger.info(f"Updating order {order_id} status to {new_status}")
        
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order")
        
        # Validate status transition
        if not self._is_valid_status_transition(order.status, new_status):
            raise OrderException(f"Invalid status transition from {order.status} to {new_status}")
        
        update_data = {"status": new_status}
        
        # Update timestamps based on status
        if new_status == OrderStatus.ASSIGNED:
            update_data["assigned_at"] = datetime.utcnow()
            if courier_id:
                update_data["courier_id"] = courier_id
        
        elif new_status == OrderStatus.ACCEPTED:
            update_data["accepted_at"] = datetime.utcnow()
        
        elif new_status == OrderStatus.PICKED_UP:
            update_data["picked_up_at"] = datetime.utcnow()
        
        elif new_status == OrderStatus.DELIVERED:
            update_data["delivered_at"] = datetime.utcnow()
            update_data["payment_status"] = "completed"
        
        elif new_status == OrderStatus.CANCELLED:
            update_data["cancelled_at"] = datetime.utcnow()
        
        updated_order = await self.order_repo.update(order_id, update_data)
        await self.db.commit()
        
        logger.info(f"Order status updated successfully: {order_id}")
        
        # TODO: Send notifications
        
        return OrderDetailResponse.from_orm(updated_order)
    
    async def cancel_order(
        self,
        order_id: UUID,
        reason: str,
        cancelled_by: str
    ) -> OrderDetailResponse:
        """Cancel an order"""
        logger.info(f"Cancelling order: {order_id}")
        
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order")
        
        if not order.can_be_cancelled:
            raise OrderException("Order cannot be cancelled at this stage")
        
        update_data = {
            "status": OrderStatus.CANCELLED,
            "cancelled_at": datetime.utcnow(),
            "cancellation_reason": reason,
            "cancelled_by": cancelled_by
        }
        
        updated_order = await self.order_repo.update(order_id, update_data)
        await self.db.commit()
        
        logger.info(f"Order cancelled successfully: {order_id}")
        
        return OrderDetailResponse.from_orm(updated_order)
    
    async def get_customer_orders(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderResponse]:
        """Get customer's orders"""
        orders = await self.order_repo.get_by_customer(customer_id, skip, limit)
        return [OrderResponse.from_orm(order) for order in orders]
    
    async def get_courier_orders(
        self,
        courier_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderResponse]:
        """Get courier's orders"""
        orders = await self.order_repo.get_by_courier(courier_id, skip, limit)
        return [OrderResponse.from_orm(order) for order in orders]
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (Haversine formula)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def _calculate_pricing(self, distance_km: float, order_type: OrderType) -> dict:
        """Calculate order pricing"""
        # Simplified pricing - would use pricing service in production
        base_price = 10.0
        price_per_km = 2.5
        
        if order_type == OrderType.EXPRESS:
            base_price *= 1.5
        
        distance_price = distance_km * price_per_km
        surge_multiplier = 1.0  # Would calculate based on demand
        weather_multiplier = 1.0  # Would get from weather service
        
        subtotal = (base_price + distance_price) * surge_multiplier * weather_multiplier
        platform_commission = subtotal * 0.2  # 20% commission
        courier_earnings = subtotal - platform_commission
        
        return {
            "base_price": base_price,
            "distance_price": distance_price,
            "surge_multiplier": surge_multiplier,
            "weather_multiplier": weather_multiplier,
            "total_price": subtotal,
            "platform_commission": platform_commission,
            "courier_earnings": courier_earnings
        }
    
    def _is_valid_status_transition(self, current: OrderStatus, new: OrderStatus) -> bool:
        """Validate status transition"""
        valid_transitions = {
            OrderStatus.CREATED: [OrderStatus.PENDING_ASSIGNMENT, OrderStatus.CANCELLED],
            OrderStatus.PENDING_ASSIGNMENT: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
            OrderStatus.ASSIGNED: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.PICKED_UP, OrderStatus.CANCELLED],
            OrderStatus.PICKED_UP: [OrderStatus.IN_TRANSIT],
            OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.FAILED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
            OrderStatus.FAILED: []
        }
        
        return new in valid_transitions.get(current, [])
