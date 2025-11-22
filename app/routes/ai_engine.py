from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.orm import Order
from app.services.ai_dispatcher import find_best_courier, assign_order_to_courier
from pydantic import BaseModel

router = APIRouter()

class AssignmentRequest(BaseModel):
    order_id: int

@router.post("/recommend")
async def recommend_courier(
    request: AssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    best_courier = await find_best_courier(db, order)
    
    if not best_courier:
        return {"message": "No suitable courier found"}
        
    return {
        "recommended_courier_id": best_courier.id,
        "vehicle_type": best_courier.vehicle_type,
        "rating": best_courier.rating
    }

@router.post("/assign")
async def auto_assign(
    request: AssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    best_courier = await find_best_courier(db, order)
    
    if not best_courier:
        raise HTTPException(status_code=400, detail="No courier available for assignment")
        
    updated_order = await assign_order_to_courier(db, order.id, best_courier.id)
    
    return {
        "status": "assigned",
        "order_id": updated_order.id,
        "courier_id": best_courier.id
    }
