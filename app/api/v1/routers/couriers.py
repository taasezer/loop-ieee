"""
LOOP Lojistik Platformu - Kurye API Router
Kurye yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from geoalchemy2.functions import ST_DistanceSphere, ST_MakePoint
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from models.courier import Courier, CourierStatus, VehicleType
from models.order import Order, OrderStatus
from schemas.courier import (
    CourierCreate, CourierUpdate, CourierResponse, 
    CourierListResponse, CourierLocationUpdate
)
from services.courier_service import CourierService
from utils.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=CourierListResponse)
async def get_couriers(
    skip: int = Query(0, ge=0, description="Kaç kayıt atla"),
    limit: int = Query(100, ge=1, le=1000, description="Kaç kayıt getir"),
    status: Optional[CourierStatus] = Query(None, description="Duruma göre filtrele"),
    vehicle_type: Optional[VehicleType] = Query(None, description="Araç tipine göre filtrele"),
    db: AsyncSession = Depends(get_db)
):
    """Tüm kuryeleri getir (sayfalama ve filtreleme ile)"""
    
    # Base query
    query = select(Courier)
    
    # Filtreleri uygula
    filters = []
    if status:
        filters.append(Courier.status == status)
    if vehicle_type:
        filters.append(Courier.vehicle_type == vehicle_type)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Sayfalama
    query = query.offset(skip).limit(limit)
    
    # Sonuçları getir
    result = await db.execute(query)
    couriers = result.scalars().all()
    
    # Toplam sayı için count query
    count_query = select(Courier)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return CourierListResponse(
        data=list(couriers),
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/nearby", response_model=List[CourierResponse])
async def get_nearby_couriers(
    lat: float = Query(..., description="Enlem"),
    lng: float = Query(..., description="Boylam"),
    radius_km: float = Query(5.0, ge=0.1, le=50.0, description="Yarıçap (km)"),
    status: Optional[CourierStatus] = Query(CourierStatus.AVAILABLE, description="Kurye durumu"),
    limit: int = Query(20, ge=1, le=100, description="Max sonuç sayısı"),
    db: AsyncSession = Depends(get_db)
):
    """Belirli bir konuma en yakın kuryeleri getir"""
    
    # PostGIS ile uzaklık hesaplama
    point = ST_MakePoint(lng, lat)
    radius_meters = radius_km * 1000
    
    query = (
        select(Courier)
        .where(
            and_(
                Courier.current_location.isnot(None),
                ST_DistanceSphere(Courier.current_location, point) <= radius_meters,
                Courier.status == status if status else True
            )
        )
        .order_by(ST_DistanceSphere(Courier.current_location, point))
        .limit(limit)
    )
    
    result = await db.execute(query)
    couriers = result.scalars().all()
    
    return [CourierResponse.from_orm(courier) for courier in couriers]


@router.get("/{courier_id}", response_model=CourierResponse)
async def get_courier(
    courier_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Belirli bir kuryeyi getir"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    return CourierResponse.from_orm(courier)


@router.post("/", response_model=CourierResponse, status_code=status.HTTP_201_CREATED)
async def create_courier(
    courier_data: CourierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Yeni kurye oluştur"""
    
    # Telefon numarası kontrolü
    existing_courier = await db.execute(
        select(Courier).where(Courier.phone == courier_data.phone)
    )
    if existing_courier.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu telefon numarası zaten kullanılıyor"
        )
    
    # Email kontrolü (varsa)
    if courier_data.email:
        existing_email = await db.execute(
            select(Courier).where(Courier.email == courier_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kullanılıyor"
            )
    
    # Yeni kurye oluştur
    new_courier = Courier(**courier_data.dict())
    db.add(new_courier)
    await db.commit()
    await db.refresh(new_courier)
    
    return CourierResponse.from_orm(new_courier)


@router.put("/{courier_id}", response_model=CourierResponse)
async def update_courier(
    courier_id: UUID,
    courier_data: CourierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Kurye bilgilerini güncelle"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    # Güncelleme verilerini uygula
    update_data = courier_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(courier, field, value)
    
    await db.commit()
    await db.refresh(courier)
    
    return CourierResponse.from_orm(courier)


@router.patch("/{courier_id}/location", response_model=CourierResponse)
async def update_courier_location(
    courier_id: UUID,
    location_data: CourierLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Kurye konumunu güncelle (GPS tracking)"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    # Konum güncelle
    courier.current_location = f"POINT({location_data.longitude} {location_data.latitude})"
    courier.last_active_at = func.now()
    
    await db.commit()
    await db.refresh(courier)
    
    return CourierResponse.from_orm(courier)


@router.patch("/{courier_id}/status", response_model=CourierResponse)
async def update_courier_status(
    courier_id: UUID,
    status: CourierStatus,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Kurye durumunu güncelle"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    courier.status = status
    if status == CourierStatus.AVAILABLE:
        courier.last_active_at = func.now()
    
    await db.commit()
    await db.refresh(courier)
    
    return CourierResponse.from_orm(courier)


@router.delete("/{courier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_courier(
    courier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Kurye sil (soft delete)"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    # Aktif siparişi varsa silme
    active_orders = await db.execute(
        select(Order).where(
            and_(
                Order.assigned_courier_id == courier_id,
                Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT])
            )
        )
    )
    
    if active_orders.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktif siparişi olan kurye silinemez"
        )
    
    # Soft delete - status'ü offline yap
    courier.status = CourierStatus.OFFLINE
    await db.commit()
    
    return None


@router.get("/{courier_id}/performance")
async def get_courier_performance(
    courier_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Kurye performans istatistikleri"""
    
    courier = await db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurye bulunamadı"
        )
    
    # Son 30 günün teslimat istatistikleri
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_orders = await db.execute(
        select(Order).where(
            and_(
                Order.assigned_courier_id == courier_id,
                Order.created_at >= thirty_days_ago,
                Order.status == OrderStatus.DELIVERED
            )
        )
    )
    
    delivered_orders = recent_orders.scalars().all()
    
    return {
        "courier_id": courier_id,
        "name": courier.name,
        "rating": courier.rating,
        "total_deliveries": courier.total_deliveries,
        "total_distance_km": courier.total_distance_km,
        "recent_deliveries_count": len(delivered_orders),
        "average_rating": courier.rating,
        "current_status": courier.status.value,
        "vehicle_type": courier.vehicle_type.value
    }