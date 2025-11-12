"""
OSRM (Open Source Routing Machine) client for route calculation
"""

import httpx
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class OSRMClient:
    """OSRM routing service client"""
    
    def __init__(self, base_url: str = "http://router.project-osrm.org"):
        self.base_url = base_url
    
    async def calculate_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate route between two points
        
        Args:
            start: (longitude, latitude) tuple for start point
            end: (longitude, latitude) tuple for end point
            profile: Routing profile (driving, walking, cycling)
            
        Returns:
            Route information with distance, duration, and geometry
        """
        try:
            start_lon, start_lat = start
            end_lon, end_lat = end
            
            coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/route/v1/{profile}/{coordinates}",
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        
                        return {
                            "distance_meters": route["distance"],
                            "distance_km": route["distance"] / 1000,
                            "duration_seconds": route["duration"],
                            "duration_minutes": route["duration"] / 60,
                            "geometry": route["geometry"],
                            "steps": route.get("legs", [{}])[0].get("steps", []),
                            "waypoints": data.get("waypoints", [])
                        }
                
                logger.warning(f"Route calculation failed: {start} -> {end}")
                return None
        
        except Exception as e:
            logger.error(f"OSRM route calculation error: {str(e)}")
            return None
    
    async def calculate_matrix(
        self,
        sources: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate distance/duration matrix between multiple points
        
        Args:
            sources: List of (longitude, latitude) tuples for source points
            destinations: List of (longitude, latitude) tuples for destination points
            profile: Routing profile
            
        Returns:
            Distance and duration matrices
        """
        try:
            # Combine all coordinates
            all_coords = sources + destinations
            coordinates = ";".join([f"{lon},{lat}" for lon, lat in all_coords])
            
            # Source and destination indices
            source_indices = ";".join([str(i) for i in range(len(sources))])
            dest_indices = ";".join([str(i + len(sources)) for i in range(len(destinations))])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/table/v1/{profile}/{coordinates}",
                    params={
                        "sources": source_indices,
                        "destinations": dest_indices
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok":
                        return {
                            "durations": data.get("durations", []),
                            "distances": data.get("distances", []),
                            "sources": data.get("sources", []),
                            "destinations": data.get("destinations", [])
                        }
                
                return None
        
        except Exception as e:
            logger.error(f"OSRM matrix calculation error: {str(e)}")
            return None
    
    async def optimize_route(
        self,
        waypoints: List[Tuple[float, float]],
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize route through multiple waypoints (TSP solver)
        
        Args:
            waypoints: List of (longitude, latitude) tuples
            profile: Routing profile
            
        Returns:
            Optimized route with waypoint order
        """
        try:
            coordinates = ";".join([f"{lon},{lat}" for lon, lat in waypoints])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/trip/v1/{profile}/{coordinates}",
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true"
                    },
                    timeout=20.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok" and data.get("trips"):
                        trip = data["trips"][0]
                        
                        return {
                            "distance_meters": trip["distance"],
                            "distance_km": trip["distance"] / 1000,
                            "duration_seconds": trip["duration"],
                            "duration_minutes": trip["duration"] / 60,
                            "geometry": trip["geometry"],
                            "waypoint_order": [wp["waypoint_index"] for wp in data.get("waypoints", [])],
                            "waypoints": data.get("waypoints", [])
                        }
                
                return None
        
        except Exception as e:
            logger.error(f"OSRM route optimization error: {str(e)}")
            return None
    
    async def match_route(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Match GPS coordinates to road network
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Routing profile
            
        Returns:
            Matched route on road network
        """
        try:
            coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/match/v1/{profile}/{coords_str}",
                    params={
                        "overview": "full",
                        "geometries": "geojson"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok" and data.get("matchings"):
                        matching = data["matchings"][0]
                        
                        return {
                            "distance_meters": matching["distance"],
                            "distance_km": matching["distance"] / 1000,
                            "duration_seconds": matching["duration"],
                            "duration_minutes": matching["duration"] / 60,
                            "geometry": matching["geometry"],
                            "confidence": matching.get("confidence", 0)
                        }
                
                return None
        
        except Exception as e:
            logger.error(f"OSRM route matching error: {str(e)}")
            return None


# Singleton instance
osrm_client = OSRMClient()
