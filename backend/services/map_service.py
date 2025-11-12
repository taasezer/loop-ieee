import httpx
import os
from typing import Dict, List, Optional
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MapService:
    def __init__(self):
        self.mapbox_token = os.getenv("MAPBOX_ACCESS_TOKEN", "")
        self.osrm_url = os.getenv("OSRM_URL", "http://router.project-osrm.org")
        self.nominatim_url = "https://nominatim.openstreetmap.org"
    
    async def geocode_address(self, address: str) -> Dict:
        """Convert address to coordinates using Nominatim"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_url}/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1
                    },
                    headers={"User-Agent": "LOOP-Logistics/1.0"}
                )
                data = response.json()
                if data:
                    return {
                        "latitude": float(data[0]["lat"]),
                        "longitude": float(data[0]["lon"]),
                        "display_name": data[0]["display_name"]
                    }
                raise HTTPException(status_code=404, detail="Address not found")
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            raise HTTPException(status_code=500, detail="Geocoding service error")
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """Convert coordinates to address using Nominatim"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_url}/reverse",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "json"
                    },
                    headers={"User-Agent": "LOOP-Logistics/1.0"}
                )
                data = response.json()
                return {
                    "address": data.get("display_name", ""),
                    "city": data.get("address", {}).get("city", ""),
                    "country": data.get("address", {}).get("country", "")
                }
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            raise HTTPException(status_code=500, detail="Reverse geocoding error")
    
    async def calculate_route(self, start: Dict[str, float], end: Dict[str, float]) -> Dict:
        """Calculate route using OSRM"""
        try:
            coordinates = f"{start['longitude']},{start['latitude']};{end['longitude']},{end['latitude']}"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.osrm_url}/route/v1/driving/{coordinates}",
                    params={"overview": "full", "geometries": "geojson"}
                )
                data = response.json()
                
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    return {
                        "distance": route["distance"] / 1000,  # Convert to km
                        "duration": route["duration"] / 60,  # Convert to minutes
                        "geometry": route["geometry"],
                        "steps": route.get("legs", [{}])[0].get("steps", [])
                    }
                raise HTTPException(status_code=404, detail="Route not found")
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            raise HTTPException(status_code=500, detail="Route calculation error")
    
    async def optimize_multi_stop_route(self, waypoints: List[Dict[str, float]]) -> Dict:
        """Optimize route with multiple stops using OSRM"""
        try:
            coordinates = ";".join([f"{wp['longitude']},{wp['latitude']}" for wp in waypoints])
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.osrm_url}/trip/v1/driving/{coordinates}",
                    params={"overview": "full", "geometries": "geojson"}
                )
                data = response.json()
                
                if data.get("code") == "Ok":
                    return {
                        "optimized_order": data.get("waypoints", []),
                        "total_distance": sum([trip["distance"] for trip in data.get("trips", [])]) / 1000,
                        "total_duration": sum([trip["duration"] for trip in data.get("trips", [])]) / 60,
                        "trips": data.get("trips", [])
                    }
                raise HTTPException(status_code=404, detail="Could not optimize route")
        except Exception as e:
            logger.error(f"Route optimization error: {e}")
            raise HTTPException(status_code=500, detail="Route optimization error")
    
    async def get_distance_matrix(self, origins: List[Dict], destinations: List[Dict]) -> Dict:
        """Calculate distance matrix between multiple points"""
        try:
            # Combine all coordinates
            all_coords = origins + destinations
            coordinates = ";".join([f"{c['longitude']},{c['latitude']}" for c in all_coords])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.osrm_url}/table/v1/driving/{coordinates}",
                    params={"sources": ";".join([str(i) for i in range(len(origins))])}
                )
                data = response.json()
                
                if data.get("code") == "Ok":
                    return {
                        "distances": data.get("distances", []),
                        "durations": data.get("durations", [])
                    }
                raise HTTPException(status_code=500, detail="Distance matrix calculation failed")
        except Exception as e:
            logger.error(f"Distance matrix error: {e}")
            raise HTTPException(status_code=500, detail="Distance matrix error")

map_service = MapService()
