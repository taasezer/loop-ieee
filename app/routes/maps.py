from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from typing import List, Optional

router = APIRouter()

class Location(BaseModel):
    latitude: float
    longitude: float

class RouteRequest(BaseModel):
    origin: Location
    destination: Location

class RouteResponse(BaseModel):
    distance_km: float
    duration_mins: float
    geometry: str # Polyline string

@router.post("/route", response_model=RouteResponse)
async def get_route(request: RouteRequest):
    # Using OSRM public API for demo purposes. In prod, use self-hosted OSRM or Mapbox.
    # OSRM format: {longitude},{latitude};{longitude},{latitude}
    url = f"http://router.project-osrm.org/route/v1/driving/{request.origin.longitude},{request.origin.latitude};{request.destination.longitude},{request.destination.latitude}?overview=full"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] != "Ok":
                raise HTTPException(status_code=400, detail="Could not calculate route")
            
            route = data["routes"][0]
            distance_km = route["distance"] / 1000
            duration_mins = route["duration"] / 60
            geometry = route["geometry"]
            
            return RouteResponse(
                distance_km=round(distance_km, 2),
                duration_mins=round(duration_mins, 2),
                geometry=geometry
            )
        except Exception as e:
            # Fallback or error handling
            print(f"Routing error: {e}")
            raise HTTPException(status_code=503, detail="Routing service unavailable")

@router.get("/geocode")
async def geocode(address: str):
    # Using Nominatim (OpenStreetMap)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "LoopLogistics/1.0"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            
            if not data:
                raise HTTPException(status_code=404, detail="Address not found")
            
            return {
                "latitude": float(data[0]["lat"]),
                "longitude": float(data[0]["lon"]),
                "display_name": data[0]["display_name"]
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
