"""
Orders API endpoints - Full Implementation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import security
from app.core.exceptions import *
from app.services.order_service import OrderService
from app.schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    OrderDetailResponse,
    OrderListResponse,
    OrderCancelRequest,
    ProofOfDeliveryRequest
)
from app.models.order import OrderStatus

logger = logging.getLogger(__name__)

router = APIRouter()
security_scheme = HTTPBearer()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    """Get current user ID from token"""
    try:
        token = credentials.credentials
        payload = security.decode_token(token)
        return UUID(payload["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post("/", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new order
    
    Creates a new delivery order with pickup and delivery details.
    The order will be automatically assigned to an available courier.
    """
    try:
        order_service = OrderService(db)
        return await order_service.create_order(request, current_user_id)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get order details by ID
    """
    try:
        order_service = OrderService(db)
        return await order_service.get_order(order_id)
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    List orders for current user
    """
    try:
        order_service = OrderService(db)
        orders = await order_service.get_customer_orders(current_user_id, skip, limit)
        
        # Get total count
        from app.repositories.order_repository import OrderRepository
        order_repo = OrderRepository(db)
        total = await order_repo.count({"customer_id": current_user_id})
        
        return OrderListResponse(
            orders=orders,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
    except Exception as e:
        logger.error(f"List orders error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list orders"
        )


@router.put("/{order_id}/status", response_model=OrderDetailResponse)
async def update_order_status(
    order_id: UUID,
    new_status: OrderStatus,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update order status
    
    Only couriers and admins can update order status.
    """
    try:
        order_service = OrderService(db)
        return await order_service.update_order_status(order_id, new_status)
    except (ResourceNotFoundException, OrderException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update order status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


@router.post("/{order_id}/cancel", response_model=OrderDetailResponse)
async def cancel_order(
    order_id: UUID,
    request: OrderCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Cancel an order
    """
    try:
        order_service = OrderService(db)
        return await order_service.cancel_order(
            order_id,
            request.cancellation_reason,
            request.cancelled_by
        )
    except (ResourceNotFoundException, OrderException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Cancel order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


@router.post("/{order_id}/proof-of-delivery", response_model=dict)
async def submit_proof_of_delivery(
    order_id: UUID,
    request: ProofOfDeliveryRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Submit proof of delivery (signature, photo, notes)
    """
    try:
        from app.repositories.order_repository import OrderRepository
        
        order_repo = OrderRepository(db)
        order = await order_repo.get_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Update proof of delivery
        proof_data = {
            "signature": request.signature,
            "photo": request.photo,
            "notes": request.notes,
            "submitted_at": str(datetime.utcnow())
        }
        
        await order_repo.update(order_id, {"proof_of_delivery": proof_data})
        await db.commit()
        
        return {
            "message": "Proof of delivery submitted successfully",
            "order_id": order_id
        }
    
    except Exception as e:
        logger.error(f"Submit proof of delivery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit proof of delivery"
        )


@router.get("/{order_id}/track", response_model=dict)
async def track_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time tracking information for an order
    """
    try:
        from app.repositories.order_repository import OrderRepository
        from app.repositories.location_repository import LocationRepository
        
        order_repo = OrderRepository(db)
        location_repo = LocationRepository(db)
        
        order = await order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        tracking_info = {
            "order_id": order_id,
            "order_number": order.order_number,
            "status": order.status,
            "courier_id": order.courier_id,
            "pickup_address": order.pickup_address,
            "delivery_address": order.delivery_address,
            "estimated_delivery_time": order.scheduled_delivery_time
        }
        
        # Get courier location if assigned
        if order.courier_id:
            latest_location = await location_repo.get_latest_location(order.courier_id)
            if latest_location:
                tracking_info["courier_location"] = {
                    "latitude": latest_location.latitude,
                    "longitude": latest_location.longitude,
                    "last_updated": latest_location.recorded_at
                }
        
        return tracking_info
    
    except Exception as e:
        logger.error(f"Track order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track order"
        )
