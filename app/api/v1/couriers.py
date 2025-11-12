"""Couriers API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import security
from app.services.courier_service import CourierService
from app.schemas.courier import *

logger = logging.getLogger(__name__)
router = APIRouter()
security_scheme = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UUID:
    token = credentials.credentials
    payload = security.decode_token(token)
    return UUID(payload["user_id"])

@router.get("/", response_model=CourierListResponse)
async def list_couriers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """List all couriers"""
    try:
        courier_service = CourierService(db)
        couriers = await courier_service.get_available_couriers()
        return CourierListResponse(
            couriers=couriers,
            total=len(couriers),
            page=1,
            page_size=limit
        )
    except Exception as e:
        logger.error(f"List couriers error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list couriers")

@router.get("/{courier_id}", response_model=CourierDetailResponse)
async def get_courier(
    courier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get courier details"""
    try:
        courier_service = CourierService(db)
        return await courier_service.get_courier(courier_id)
    except Exception as e:
        logger.error(f"Get courier error: {str(e)}")
        raise HTTPException(status_code=404, detail="Courier not found")

@router.put("/{courier_id}/location", response_model=dict)
async def update_location(
    courier_id: UUID,
    location: LocationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Update courier location"""
    try:
        courier_service = CourierService(db)
        await courier_service.update_location(courier_id, location)
        return {"message": "Location updated successfully"}
    except Exception as e:
        logger.error(f"Update location error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update location")

@router.put("/{courier_id}/availability", response_model=dict)
async def update_availability(
    courier_id: UUID,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Update courier availability"""
    try:
        courier_service = CourierService(db)
        await courier_service.update_availability(courier_id, is_available)
        return {"message": "Availability updated successfully"}
    except Exception as e:
        logger.error(f"Update availability error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update availability")
