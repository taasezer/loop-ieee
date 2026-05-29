from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.orm import Order, User, OrderStatus, UserRole, Courier, VehicleType
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
    cargo_type: Optional[str] = None
    cargo_weight: Optional[float] = None

class OrderResponse(BaseModel):
    id: int
    status: str
    price: float
    pickup_address: str
    delivery_address: str
    tracking_code: Optional[str] = None
    customer_note: Optional[str] = None
    cargo_type: Optional[str] = None
    cargo_weight: Optional[float] = None
    supplier_company: Optional[str] = None
    supplier_code: Optional[str] = None
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
    assigned_supplier_code = None
    
    if order_in.supplier_code:
        supplier_result = await db.execute(select(User).where(User.supplier_code == order_in.supplier_code.upper()))
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            raise HTTPException(status_code=404, detail="Tedarikçi kodu geçersiz.")
        supplier_id = supplier.id
        supplier_company = supplier.company_name
        assigned_supplier_code = supplier.supplier_code
    else:
        # Assign random supplier
        from sqlalchemy.sql.expression import func
        supplier_result = await db.execute(select(User).where(User.role == UserRole.SUPPLIER).order_by(func.random()).limit(1))
        random_supplier = supplier_result.scalar_one_or_none()
        if random_supplier:
            supplier_id = random_supplier.id
            supplier_company = random_supplier.company_name
            assigned_supplier_code = random_supplier.supplier_code
    
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
        cargo_type=order_in.cargo_type,
        cargo_weight=order_in.cargo_weight,
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
        cargo_type=new_order.cargo_type,
        cargo_weight=new_order.cargo_weight,
        supplier_company=supplier_company,
        supplier_code=assigned_supplier_code,
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
            cargo_type=o.cargo_type,
            cargo_weight=o.cargo_weight,
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
            cargo_type=o.cargo_type,
            cargo_weight=o.cargo_weight,
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
        cargo_type=order.cargo_type,
        cargo_weight=order.cargo_weight,
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
    """Update order status (admin/dispatcher or supplier for own orders)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER, UserRole.SUPPLIER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # If supplier, verify ownership
    if current_user.role == UserRole.SUPPLIER:
        check_result = await db.execute(select(Order).where(Order.id == order_id))
        check_order = check_result.scalar_one_or_none()
        if not check_order or check_order.supplier_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this order")
            
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=new_status,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Status updated successfully", **result}

import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class CourierRecommendation(BaseModel):
    courier_id: int
    courier_name: str
    vehicle_type: str
    distance_km: float
    rating: float

class AssignCourierRequest(BaseModel):
    courier_id: int

@router.get("/{order_id}/recommend-couriers", response_model=List[CourierRecommendation])
async def recommend_couriers(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Suggest couriers based on distance and cargo weight constraints."""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Not authorized to recommend couriers")
        
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != OrderStatus.CREATED:
        raise HTTPException(status_code=400, detail="Only CREATED orders can be assigned")
        
    # Get active/online couriers
    query = select(Courier).options(selectinload(Courier.user)).where(Courier.is_online == True)
    
    # If supplier, only recommend their own couriers
    if current_user.role == UserRole.SUPPLIER:
        query = query.where(Courier.supplier_id == current_user.id)
        
    couriers_result = await db.execute(query)
    couriers = couriers_result.scalars().all()
    
    recommendations = []
    weight = order.cargo_weight or 0.0
    
    for courier in couriers:
        # Weight Constraint Logic: If > 10kg, only CAR or VAN
        if weight > 10.0 and courier.vehicle_type not in [VehicleType.CAR, VehicleType.VAN]:
            continue
            
        dist = haversine(order.pickup_latitude, order.pickup_longitude, courier.current_latitude, courier.current_longitude)
        
        recommendations.append(CourierRecommendation(
            courier_id=courier.id,
            courier_name=courier.user.full_name if courier.user else "Bilinmeyen",
            vehicle_type=courier.vehicle_type,
            distance_km=round(dist, 2),
            rating=courier.rating or 5.0
        ))
        
    # Sort by distance
    recommendations.sort(key=lambda x: x.distance_km)
    
    # Return top 5
    return recommendations[:5]

@router.post("/{order_id}/assign-courier")
async def assign_courier(
    order_id: int,
    request: AssignCourierRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a specific courier to an order (Supplier Action)"""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Not authorized to assign couriers")
        
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != OrderStatus.CREATED:
        raise HTTPException(status_code=400, detail="Order is already assigned or in progress")
        
    # Verify the courier exists
    courier_result = await db.execute(select(Courier).where(Courier.id == request.courier_id))
    courier = courier_result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
        
    # Perform Assignment
    order.courier_id = courier.id
    order.status = OrderStatus.ASSIGNED
    await db.commit()
    
    return {"message": "Courier assigned successfully", "order_id": order.id, "courier_id": courier.id}
