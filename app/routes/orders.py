from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.orm import Order, User, OrderStatus, UserRole
from app.dependencies import get_current_user
from app.services.pricing import calculate_order_price
from pydantic import BaseModel
from app.services.order_workflow import order_workflow_service
from app.services.maps_service import maps_service
from app.middleware.rate_limit import limiter
from fastapi import Request
import secrets
import string
import html

def generate_tracking_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return "LOOP-" + "".join(secrets.choice(chars) for _ in range(length))

router = APIRouter()

class OrderCreate(BaseModel):
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float
    distance_km: float # In a real app, this would be calculated server-side via OSRM
    customer_note: Optional[str] = None
    supplier_code: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    status: str
    price: float
    pickup_address: str
    delivery_address: str
    tracking_code: Optional[str] = None
    customer_note: Optional[str] = None
    supplier_company: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify distance server-side
    verified_distance = order_in.distance_km
    distance_data = maps_service.calculate_distance_duration(
        origin=(order_in.pickup_latitude, order_in.pickup_longitude),
        destination=(order_in.delivery_latitude, order_in.delivery_longitude)
    )
    if distance_data:
        verified_distance = distance_data['distance_km']
        
    # Calculate price
    price = await calculate_order_price(db, verified_distance)
    
    supplier_id = None
    supplier_company = None
    if order_in.supplier_code:
        supplier_result = await db.execute(select(User).where(User.supplier_code == order_in.supplier_code.upper()))
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            raise HTTPException(status_code=404, detail="Tedarikçi kodu geçersiz.")
        supplier_id = supplier.id
        supplier_company = supplier.company_name
    
    new_order = Order(
        customer_id=current_user.id,
        pickup_address=order_in.pickup_address,
        pickup_latitude=order_in.pickup_latitude,
        pickup_longitude=order_in.pickup_longitude,
        delivery_address=order_in.delivery_address,
        delivery_latitude=order_in.delivery_latitude,
        delivery_longitude=order_in.delivery_longitude,
        distance_km=verified_distance,
        price=price,
        tracking_code=generate_tracking_code(),
        customer_note=html.escape(order_in.customer_note) if order_in.customer_note else None,
        supplier_id=supplier_id,
        status=OrderStatus.CREATED
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    return OrderResponse(
        id=new_order.id,
        status=new_order.status,
        price=new_order.price,
        pickup_address=new_order.pickup_address,
        delivery_address=new_order.delivery_address,
        tracking_code=new_order.tracking_code,
        customer_note=new_order.customer_note,
        supplier_company=supplier_company,
        created_at=str(new_order.created_at)
    )

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == UserRole.SUPPLIER:
        result = await db.execute(select(Order).options(selectinload(Order.supplier)).where(Order.supplier_id == current_user.id))
    else:
        result = await db.execute(select(Order).options(selectinload(Order.supplier)).where(Order.customer_id == current_user.id))
    orders = result.scalars().all()
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            price=o.price,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            tracking_code=o.tracking_code,
            supplier_company=o.supplier.company_name if o.supplier else None,
            created_at=str(o.created_at)
        ) for o in orders
    ]

@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active (non-completed) orders for current user"""
    if current_user.role == UserRole.SUPPLIER:
        query = select(Order).options(selectinload(Order.supplier)).where(
            Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED]),
            Order.supplier_id == current_user.id
        )
        result = await db.execute(query.order_by(Order.created_at.desc()))
        orders = result.scalars().all()
    else:
        orders = await order_workflow_service.get_active_orders(
            db=db,
            user_id=current_user.id
        )
    
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            price=o.price,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            tracking_code=o.tracking_code,
            supplier_company=o.supplier.company_name if o.supplier else None,
            created_at=str(o.created_at)
        ) for o in orders
    ]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).options(selectinload(Order.supplier)).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.customer_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
         raise HTTPException(status_code=403, detail="Not authorized")

    return OrderResponse(
        id=order.id,
        status=order.status,
        price=order.price,
        pickup_address=order.pickup_address,
        delivery_address=order.delivery_address,
        tracking_code=order.tracking_code,
        customer_note=order.customer_note,
        created_at=str(order.created_at)
    )

class PublicTrackingResponse(BaseModel):
    tracking_code: str
    status: str
    delivery_area: str
    courier_name: Optional[str] = None
    customer_note: Optional[str] = None
    
@router.get("/track/{code}", response_model=PublicTrackingResponse)
@limiter.limit("10/minute")
async def track_order_public(code: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Public endpoint to track an order without authentication. Masks PII."""
    result = await db.execute(select(Order).where(Order.tracking_code == code))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Geçersiz takip kodu")
        
    # Masking the exact delivery address to just the general area for security
    masked_address = order.delivery_address.split(',')[0] + " (Gizli Adres)" if order.delivery_address else "Bilinmiyor"
    
    courier_name = None
    if order.courier_id:
        result_courier = await db.execute(select(User).where(User.id == order.courier_id)) # Not optimal, but gets user
        courier_user = result_courier.scalar_one_or_none()
        if courier_user:
            courier_name = courier_user.full_name.split()[0] + " ***"

    return PublicTrackingResponse(
        tracking_code=order.tracking_code,
        status=order.status,
        delivery_area=masked_address,
        courier_name=courier_name,
        customer_note=order.customer_note
    )

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an order"""
    # Verify order belongs to user
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Cancel order
    cancel_result = await order_workflow_service.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        reason=reason
    )
    
    if not cancel_result["success"]:
        raise HTTPException(status_code=400, detail=cancel_result["error"])
    
    return {"message": "Order cancelled successfully", **cancel_result}

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=new_status,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Status updated successfully", **result}
