from fastapi import APIRouter, HTTPException
from services.map_service import map_service
from pydantic import BaseModel
from typing import List, Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class RouteRequest(BaseModel):
    start: Dict[str, float]  # {"latitude": x, "longitude": y}
    end: Dict[str, float]

class MultiStopRouteRequest(BaseModel):
    waypoints: List[Dict[str, float]]

class DistanceMatrixRequest(BaseModel):
    origins: List[Dict[str, float]]
    destinations: List[Dict[str, float]]

@router.get("/geocode")
async def geocode(address: str):
    """Convert address to coordinates"""
    try:
        result = await map_service.geocode_address(address)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        raise HTTPException(status_code=500, detail="Geocoding failed")

@router.get("/reverse-geocode")
async def reverse_geocode(latitude: float, longitude: float):
    """Convert coordinates to address"""
    try:
        result = await map_service.reverse_geocode(latitude, longitude)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        raise HTTPException(status_code=500, detail="Reverse geocoding failed")

@router.post("/route")
async def calculate_route(request: RouteRequest):
    """Calculate route between two points"""
    try:
        result = await map_service.calculate_route(request.start, request.end)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route calculation error: {e}")
        raise HTTPException(status_code=500, detail="Route calculation failed")

@router.post("/optimize-route")
async def optimize_multi_stop_route(request: MultiStopRouteRequest):
    """Optimize route with multiple stops"""
    try:
        result = await map_service.optimize_multi_stop_route(request.waypoints)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route optimization error: {e}")
        raise HTTPException(status_code=500, detail="Route optimization failed")

@router.post("/distance-matrix")
async def get_distance_matrix(request: DistanceMatrixRequest):
    """Calculate distance matrix between multiple points"""
    try:
        result = await map_service.get_distance_matrix(request.origins, request.destinations)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Distance matrix error: {e}")
        raise HTTPException(status_code=500, detail="Distance matrix calculation failed")
