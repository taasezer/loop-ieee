from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_engine import ai_engine

router = APIRouter()

class AssignmentRequest(BaseModel):
    order_id: str

class OptimizeRouteRequest(BaseModel):
    courier_id: str

@router.post("/recommend")
async def recommend_courier(request: AssignmentRequest):
    """Get AI recommendation for best courier"""
    result = await ai_engine.find_best_courier(request.order_id)

    if not result:
        raise HTTPException(status_code=404, detail="Could not find suitable courier")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@router.post("/assign")
async def auto_assign(request: AssignmentRequest):
    """Automatically assign best courier to order"""
    result = await ai_engine.auto_assign_courier(request.order_id)

    if not result:
        raise HTTPException(status_code=400, detail="Assignment failed")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Assignment failed"))

    return result

@router.post("/optimize-route")
async def optimize_courier_route(request: OptimizeRouteRequest):
    """Optimize delivery route for courier with multiple orders"""
    result = await ai_engine.optimize_route_for_courier(request.courier_id)

    if not result:
        raise HTTPException(status_code=404, detail="Could not optimize route")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@router.get("/analytics/assignments")
async def get_assignment_analytics():
    """Get analytics on AI assignment performance"""
    from app.database import supabase_admin

    try:
        assignments = supabase_admin.table("assignment_history") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(100) \
            .execute()

        if not assignments.data:
            return {
                "total_assignments": 0,
                "average_score": 0,
                "ai_assignments": 0,
                "manual_assignments": 0
            }

        scores = [a["assignment_score"] for a in assignments.data if a.get("assignment_score")]
        ai_count = len([a for a in assignments.data if a.get("assigned_by") == "ai"])
        manual_count = len([a for a in assignments.data if a.get("assigned_by") == "manual"])

        return {
            "total_assignments": len(assignments.data),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "ai_assignments": ai_count,
            "manual_assignments": manual_count,
            "average_distance": sum(a.get("distance_to_pickup", 0) for a in assignments.data) / len(assignments.data),
            "average_time": sum(a.get("estimated_time", 0) for a in assignments.data) / len(assignments.data)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch analytics: {str(e)}")
