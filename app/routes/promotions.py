from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models.orm import User, UserRole
from app.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

# Admin authorization
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

class PromotionCodeCreate(BaseModel):
    code: str
    discount_type: str  # "percentage" or "fixed"
    discount_value: float
    max_discount: float = None
    min_order_amount: float = 0
    max_uses: int = None
    valid_until: datetime

class PromotionCodeResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    is_active: bool
    current_uses: int
    max_uses: int
    valid_until: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=PromotionCodeResponse)
async def create_promotion_code(
    promo_in: PromotionCodeCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new promotion code (admin only)"""
    
    from app.models.orm import PromotionCode
    
    # Check if code already exists
    result = await db.execute(
        select(PromotionCode).where(PromotionCode.code == promo_in.code.upper())
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Promotion code already exists")
    
    new_promo = PromotionCode(
        code=promo_in.code.upper(),
        discount_type=promo_in.discount_type,
        discount_value=promo_in.discount_value,
        max_discount=promo_in.max_discount,
        min_order_amount=promo_in.min_order_amount,
        max_uses=promo_in.max_uses,
        valid_until=promo_in.valid_until,
        is_active=True,
        current_uses=0
    )
    
    db.add(new_promo)
    await db.commit()
    await db.refresh(new_promo)
    
    return PromotionCodeResponse(
        id=new_promo.id,
        code=new_promo.code,
        discount_type=new_promo.discount_type,
        discount_value=new_promo.discount_value,
        is_active=new_promo.is_active,
        current_uses=new_promo.current_uses,
        max_uses=new_promo.max_uses or 0,
        valid_until=str(new_promo.valid_until)
    )

@router.get("/", response_model=List[PromotionCodeResponse])
async def get_promotion_codes(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all promotion codes (admin only)"""
    
    from app.models.orm import PromotionCode
    
    result = await db.execute(select(PromotionCode))
    promos = result.scalars().all()
    
    return [
        PromotionCodeResponse(
            id=p.id,
            code=p.code,
            discount_type=p.discount_type,
            discount_value=p.discount_value,
            is_active=p.is_active,
            current_uses=p.current_uses,
            max_uses=p.max_uses or 0,
            valid_until=str(p.valid_until)
        ) for p in promos
    ]

@router.post("/validate")
async def validate_promotion_code(
    code: str,
    order_amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate promotion code and calculate discount"""
    
    from app.services.pricing import apply_promotion_code
    
    result = await apply_promotion_code(
        db=db,
        base_price=order_amount,
        promo_code=code
    )
    
    return result

@router.delete("/{code}")
async def deactivate_promotion_code(
    code: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate promotion code (admin only)"""
    
    from app.models.orm import PromotionCode
    
    result = await db.execute(
        select(PromotionCode).where(PromotionCode.code == code.upper())
    )
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion code not found")
    
    promo.is_active = False
    await db.commit()
    
    return {"message": f"Promotion code {code} deactivated"}
