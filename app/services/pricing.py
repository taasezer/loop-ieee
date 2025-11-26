from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, time, timedelta
from app.models.orm import PricingRule, Order, OrderStatus

async def calculate_order_price(
    db: AsyncSession,
    distance_km: float,
    weather_impact: Optional[float] = None,
    current_time: Optional[datetime] = None
) -> float:
    """
    Calculate order price with advanced factors:
    - Base price + distance
    - Surge pricing (demand-based)  
    - Weather impact
    - Time-based multipliers (peak hours)
    """
    
    # Get active pricing rule
    result = await db.execute(
        select(PricingRule).where(PricingRule.is_active == True).limit(1)
    )
    pricing_rule = result.scalar_one_or_none()
    
    if not pricing_rule:
        # Fallback pricing
        base_price = 10.0
        price_per_km = 2.0
        surge_multiplier = 1.0
    else:
        base_price = pricing_rule.base_price
        price_per_km = pricing_rule.price_per_km
        surge_multiplier = pricing_rule.surge_multiplier
    
    # Base calculation
    base_total = base_price + (distance_km * price_per_km)
    
    # Apply surge pricing
    surge_factor = await calculate_surge_pricing(db, current_time)
    
    # Apply weather impact (0.0 to 1.0, where 1.0 = good weather)
    weather_multiplier = 1.0
    if weather_impact is not None:
        # If weather is bad (low score), increase price
        if weather_impact < 0.5:
            weather_multiplier = 1.0 + (0.5 - weather_impact)  # Up to 1.5x
    
    # Apply time-based multipliers
    time_multiplier = calculate_time_multiplier(current_time or datetime.utcnow())
    
    # Final price
    final_price = base_total * surge_factor * weather_multiplier * time_multiplier * surge_multiplier
    
    return round(final_price, 2)


async def calculate_surge_pricing(
    db: AsyncSession,
    current_time: Optional[datetime] = None
) -> float:
    """
    Calculate surge pricing based on current demand
    Returns multiplier (1.0 = normal, >1.0 = surge)
    """
    
    current_time = current_time or datetime.utcnow()
    
    # Count active orders in last 15 minutes
    recent_time = current_time - timedelta(minutes=15)
    
    result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.created_at >= recent_time,
                Order.status.in_([
                    OrderStatus.CREATED,
                    OrderStatus.ASSIGNED,
                    OrderStatus.PICKED_UP,
                    OrderStatus.IN_TRANSIT
                ])
            )
        )
    )
    active_count = result.scalar() or 0
    
    # Surge thresholds
    if active_count > 50:
        return 2.0  # 2x surge
    elif active_count > 30:
        return 1.5  # 1.5x surge
    elif active_count > 15:
        return 1.3  # 1.3x surge
    elif active_count > 5:
        return 1.1  # 1.1x surge
    else:
        return 1.0  # Normal pricing


def calculate_time_multiplier(current_time: datetime) -> float:
    """
    Calculate time-based multiplier for peak hours
    """
    
    hour = current_time.hour
    
    # Peak hours (7-9 AM, 12-2 PM, 5-8 PM)
    morning_peak = 7 <= hour < 9
    lunch_peak = 12 <= hour < 14
    evening_peak = 17 <= hour < 20
    
    if morning_peak or lunch_peak or evening_peak:
        return 1.2  # 20% increase during peak hours
    
    # Late night (10 PM - 6 AM)
    elif hour >= 22 or hour < 6:
        return 1.3  # 30% increase for late night
    
    return 1.0  # Normal hours


async def apply_promotion_code(
    db: AsyncSession,
    base_price: float,
    promo_code: str
) -> dict:
    """
    Apply promotion code to order
    Returns updated price and discount info
    """
    
    from app.models.orm import PromotionCode
    
    # Get promotion code
    result = await db.execute(
        select(PromotionCode).where(
            and_(
                PromotionCode.code == promo_code.upper(),
                PromotionCode.is_active == True,
                PromotionCode.valid_until >= datetime.utcnow()
            )
        )
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        return {
            "success": False,
            "error": "Invalid or expired promotion code",
            "final_price": base_price,
            "discount": 0
        }
    
    # Check usage limit
    if promo.max_uses and promo.current_uses >= promo.max_uses:
        return {
            "success": False,
            "error": "Promotion code limit reached",
            "final_price": base_price,
            "discount": 0
        }
    
    # Calculate discount
    if promo.discount_type == "percentage":
        discount = base_price * (promo.discount_value / 100)
        if promo.max_discount:
            discount = min(discount, promo.max_discount)
    else:  # fixed amount
        discount = min(promo.discount_value, base_price)
    
    final_price = max(base_price - discount, promo.min_order_amount or 0)
    
    # Increment usage
    promo.current_uses += 1
    await db.commit()
    
    return {
        "success": True,
        "promo_code": promo_code,
        "discount_type": promo.discount_type,
        "discount": round(discount, 2),
        "final_price": round(final_price, 2),
        "original_price": base_price
    }
