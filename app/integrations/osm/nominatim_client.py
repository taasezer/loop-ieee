"""
OpenStreetMap Nominatim geocoding client
"""

import httpx
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class NominatimClient:
    """Nominatim geocoding service client"""
    
    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org"):
        self.base_url = base_url
        self.headers = {
            "User-Agent": "LOOP-Logistics/1.0"
        }
    
    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates
        
        Args:
            address: Address string to geocode
            
        Returns:
            Dictionary with latitude, longitude, and display_name
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        result = results[0]
                        return {
                            "latitude": float(result["lat"]),
                            "longitude": float(result["lon"]),
                            "display_name": result["display_name"],
                            "place_id": result.get("place_id"),
                            "osm_type": result.get("osm_type"),
                            "osm_id": result.get("osm_id")
                        }
                
                logger.warning(f"Geocoding failed for address: {address}")
                return None
        
        except Exception as e:
            logger.error(f"Geocoding error: {str(e)}")
            return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Convert coordinates to address
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with address components
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/reverse",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "json"
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "display_name": result.get("display_name"),
                        "address": result.get("address", {}),
                        "place_id": result.get("place_id"),
                        "osm_type": result.get("osm_type"),
                        "osm_id": result.get("osm_id")
                    }
                
                logger.warning(f"Reverse geocoding failed for: {latitude}, {longitude}")
                return None
        
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            return None
    
    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1000,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for nearby places
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters
            limit: Maximum number of results
            
        Returns:
            List of nearby places
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "json",
                        "limit": limit
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return []
        
        except Exception as e:
            logger.error(f"Nearby search error: {str(e)}")
            return []


# Singleton instance
nominatim_client = NominatimClient()
