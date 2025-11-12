from fastapi import APIRouter, HTTPException, Depends
from services.pricing_service import pricing_service
from utils.auth import require_role
from pydantic import BaseModel
from typing import Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class PriceCalculationRequest(BaseModel):
    distance_km: float
    duration_minutes: float
    priority: str = "normal"
    pickup_location: Dict[str, float] = None
    currency: str = "USD"

class EarningsCalculationRequest(BaseModel):
    order_price: float
    commission_rate: float = 0.20

@router.post("/calculate")
async def calculate_price(request: PriceCalculationRequest):
    """Calculate delivery price"""
    try:
        pricing = await pricing_service.calculate_price(
            distance_km=request.distance_km,
            duration_minutes=request.duration_minutes,
            priority=request.priority,
            pickup_location=request.pickup_location,
            currency=request.currency
        )
        return pricing
    except Exception as e:
        logger.error(f"Price calculation error: {e}")
        raise HTTPException(status_code=500, detail="Price calculation failed")

@router.post("/earnings")
async def calculate_courier_earnings(request: EarningsCalculationRequest):
    """Calculate courier earnings"""
    try:
        earnings = pricing_service.calculate_courier_earnings(
            order_price=request.order_price,
            commission_rate=request.commission_rate
        )
        return earnings
    except Exception as e:
        logger.error(f"Earnings calculation error: {e}")
        raise HTTPException(status_code=500, detail="Earnings calculation failed")

@router.get("/rules")
async def get_pricing_rules(current_user: dict = Depends(require_role(["admin"]))):
    """Get current pricing rules"""
    try:
        return {
            "base_price": pricing_service.base_price,
            "price_per_km": pricing_service.price_per_km,
            "price_per_minute": pricing_service.price_per_minute,
            "priority_multipliers": pricing_service.priority_multipliers,
            "peak_hours": pricing_service.peak_hours,
            "peak_multiplier": pricing_service.peak_multiplier
        }
    except Exception as e:
        logger.error(f"Get pricing rules error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pricing rules")
