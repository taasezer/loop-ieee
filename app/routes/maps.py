from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.maps_service import maps_service

router = APIRouter()

class GeocodeRequest(BaseModel):
    address: str

class ReverseGeocodeRequest(BaseModel):
    latitude: float
    longitude: float

class DistanceRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    mode: str = "driving"

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    waypoints: Optional[List[dict]] = None
    optimize: bool = True

@router.post("/geocode")
async def geocode_address(request: GeocodeRequest):
    """Convert address to GPS coordinates"""
    result = maps_service.geocode_address(request.address)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")
    return result

@router.post("/reverse-geocode")
async def reverse_geocode(request: ReverseGeocodeRequest):
    """Convert GPS coordinates to address"""
    result = maps_service.reverse_geocode(request.latitude, request.longitude)
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"address": result}

@router.post("/distance")
async def calculate_distance(request: DistanceRequest):
    """Calculate distance and duration between two points"""
    origin = (request.origin_lat, request.origin_lng)
    destination = (request.destination_lat, request.destination_lng)

    result = maps_service.calculate_distance_duration(origin, destination, request.mode)
    if not result:
        raise HTTPException(status_code=400, detail="Could not calculate distance")
    return result

@router.post("/route")
async def get_route(request: RouteRequest):
    """Get optimized route with turn-by-turn directions"""
    origin = (request.origin_lat, request.origin_lng)
    destination = (request.destination_lat, request.destination_lng)

    waypoints = None
    if request.waypoints:
        waypoints = [(w['lat'], w['lng']) for w in request.waypoints]

    result = maps_service.get_route(origin, destination, waypoints, request.optimize)
    if not result:
        raise HTTPException(status_code=400, detail="Could not calculate route")
    return result
