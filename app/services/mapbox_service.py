"""
LOOP Lojistik Platformu - Mapbox Service
Harita, rota planlama ve GPS takibi servisi
"""

import httpx
from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger
import json

from core.config import settings
from utils.geo_utils import calculate_distance, format_coordinates


class RouteData(BaseModel):
    """Rota verisi modeli"""
    distance_km: float
    duration_minutes: float
    geometry: str  # GeoJSON LineString
    waypoints: List[Tuple[float, float]]
    instructions: List[Dict[str, Any]]
    traffic_info: Optional[Dict[str, Any]] = None


class GeocodeResult(BaseModel):
    """Geocoding sonucu"""
    latitude: float
    longitude: float
    formatted_address: str
    place_id: str
    confidence: float


class MapboxService:
    """Mapbox API servisi"""
    
    BASE_URL = "https://api.mapbox.com"
    
    def __init__(self):
        self.access_token = settings.MAPBOX_ACCESS_TOKEN
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "LOOP-Lojistik-Platformu/1.0"}
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
        profile: str = "driving",
        alternatives: bool = False,
        traffic: bool = True
    ) -> Optional[RouteData]:
        """
        İki nokta arası rota hesapla
        
        Args:
            origin: (lat, lng) başlangıç noktası
            destination: (lat, lng) varış noktası
            waypoints: Ara duraklar
            profile: Rota tipi (driving, walking, cycling)
            alternatives: Alternatif rotalar dahil mi?
            traffic: Trafik verisi kullanılsın mı?
        
        Returns:
            RouteData objesi veya None
        """
        try:
            # Koordinatları formatla (Mapbox: lng,lat formatı)
            coords = f"{origin[1]},{origin[0]}"
            
            if waypoints:
                for wp in waypoints:
                    coords += f";{wp[1]},{wp[0]}"
            
            coords += f";{destination[1]},{destination[0]}"
            
            url = f"{self.BASE_URL}/directions/v5/mapbox/{profile}/{coords}"
            
            params = {
                "access_token": self.access_token,
                "alternatives": "true" if alternatives else "false",
                "geometries": "geojson",
                "overview": "full",
                "steps": "true",
                "traffic": "true" if traffic else "false",
                "language": "tr"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("routes"):
                logger.error("Mapbox'tan rota alınamadı")
                return None
            
            # En iyi rotayı seç
            route = data["routes"][0]
            
            # Rota verisini oluştur
            route_data = RouteData(
                distance_km=route["distance"] / 1000,  # metre -> kilometre
                duration_minutes=route["duration"] / 60,  # saniye -> dakika
                geometry=json.dumps(route["geometry"]),
                waypoints=[origin] + (waypoints or []) + [destination],
                instructions=self._extract_instructions(route),
                traffic_info=route.get("traffic")
            )
            
            logger.info(f"Rota hesaplandı: {route_data.distance_km:.2f}km, {route_data.duration_minutes:.1f}dk")
            return route_data
            
        except httpx.HTTPError as e:
            logger.error(f"Mapbox API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Rota hesaplama hatası: {e}")
            return None
    
    async def get_matrix_distances(
        self,
        locations: List[Tuple[float, float]],
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Çoklu lokasyonlar arası mesafe ve süre matrisi
        
        Args:
            locations: [(lat, lng), ...] lokasyon listesi
            profile: Rota tipi
        
        Returns:
            Mesafe ve süre matrisi
        """
        try:
            if len(locations) < 2:
                logger.error("En az 2 lokasyon gerekli")
                return None
            
            # Lokasyonları formatla
            coords = ";".join([f"{lng},{lat}" for lat, lng in locations])
            
            url = f"{self.BASE_URL}/directions-matrix/v1/mapbox/{profile}/{coords}"
            
            params = {
                "access_token": self.access_token,
                "sources": "all",
                "destinations": "all"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "distances": data.get("durations", []),  # süreler (saniye)
                "durations": data.get("durations", []),   # mesafeler (metre)
                "destinations": data.get("destinations", []),
                "sources": data.get("sources", [])
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Matrix API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Mesafe matrisi hesaplama hatası: {e}")
            return None
    
    async def geocode_address(self, address: str) -> Optional[GeocodeResult]:
        """
        Adresi koordinata çevir (geocoding)
        
        Args:
            address: Adres metni
        
        Returns:
            GeocodeResult veya None
        """
        try:
            url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{address}.json"
            
            params = {
                "access_token": self.access_token,
                "country": "tr",  # Türkiye
                "language": "tr",
                "limit": 1,
                "types": "address,poi"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("features"):
                logger.warning(f"Adres bulunamadı: {address}")
                return None
            
            feature = data["features"][0]
            coords = feature["geometry"]["coordinates"]
            
            return GeocodeResult(
                latitude=coords[1],  # Mapbox: [lng, lat]
                longitude=coords[0],
                formatted_address=feature["place_name"],
                place_id=feature["id"],
                confidence=feature.get("relevance", 0.5)
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Geocoding API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Geocoding hatası: {e}")
            return None
    
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Koordinatı adrese çevir (reverse geocoding)
        
        Args:
            lat: Enlem
            lng: Boylam
        
        Returns:
            Formatlanmış adres veya None
        """
        try:
            url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{lng},{lat}.json"
            
            params = {
                "access_token": self.access_token,
                "language": "tr",
                "types": "address"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("features"):
                return None
            
            return data["features"][0]["place_name"]
            
        except httpx.HTTPError as e:
            logger.error(f"Reverse geocoding API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Reverse geocoding hatası: {e}")
            return None
    
    async def get_traffic_info(self, bbox: Tuple[float, float, float, float]) -> Optional[Dict]:
        """
        Trafik durumu bilgisi al
        
        Args:
            bbox: (sw_lng, sw_lat, ne_lng, ne_lat) bounding box
        
        Returns:
            Trafik verisi
        """
        try:
            url = f"{self.BASE_URL}/traffic/v1/incidents/{','.join(map(str, bbox))}.json"
            
            params = {
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Traffic API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Trafik bilgisi alma hatası: {e}")
            return None
    
    def _extract_instructions(self, route: Dict) -> List[Dict[str, Any]]:
        """Rota talimatlarını çıkar"""
        instructions = []
        
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                instructions.append({
                    "instruction": step.get("maneuver", {}).get("instruction", ""),
                    "type": step.get("maneuver", {}).get("type", ""),
                    "distance": step.get("distance", 0),
                    "duration": step.get("duration", 0),
                    "location": step.get("maneuver", {}).get("location", [])
                })
        
        return instructions
    
    async def optimize_route(
        self,
        origin: Tuple[float, float],
        destinations: List[Tuple[float, float]],
        profile: str = "driving"
    ) -> Optional[List[Tuple[float, float]]]:
        """
        En optimal rota sıralamasını hesapla (Traveling Salesman Problem)
        
        Args:
            origin: Başlangıç noktası
            destinations: Ziyaret edilecek noktalar
            profile: Rota tipi
        
        Returns:
            Optimize edilmiş rota sıralaması
        """
        try:
            # Tüm lokasyonlar arası mesafe matrisini al
            all_locations = [origin] + destinations
            matrix = await self.get_matrix_distances(all_locations, profile)
            
            if not matrix:
                return None
            
            # Basit en yakın komşu algoritması ile rota optimizasyonu
            # Gerçek üretimde daha karmaşık algoritmalar kullanılmalı
            optimized_route = self._optimize_with_nearest_neighbor(matrix, len(destinations))
            
            return [all_locations[i] for i in optimized_route]
            
        except Exception as e:
            logger.error(f"Rota optimizasyon hatası: {e}")
            return None
    
    def _optimize_with_nearest_neighbor(self, matrix: Dict, num_destinations: int) -> List[int]:
        """En yakın komşu algoritması ile rota optimizasyonu"""
        if not matrix.get("durations"):
            return list(range(num_destinations + 1))
        
        durations = matrix["durations"]
        n = len(durations)
        
        if n <= 1:
            return [0]
        
        visited = [False] * n
        route = [0]  # Başlangıç noktası
        visited[0] = True
        
        for _ in range(n - 1):
            current = route[-1]
            nearest = None
            min_distance = float('inf')
            
            for i in range(n):
                if not visited[i] and durations[current][i] < min_distance:
                    min_distance = durations[current][i]
                    nearest = i
            
            if nearest is not None:
                route.append(nearest)
                visited[nearest] = True
        
        return route
    
    async def get_isochrone(
        self,
        location: Tuple[float, float],
        time_minutes: List[int] = [5, 10, 15],
        profile: str = "driving"
    ) -> Optional[Dict]:
        """
        Belirli sürede ulaşılabilir alanları hesapla (izochron)
        
        Args:
            location: Merkez nokta
            time_minutes: Süreler (dakika)
            profile: Rota tipi
        
        Returns:
            İzochron geometrileri
        """
        try:
            lng, lat = location[1], location[0]
            contours = ",".join(map(str, time_minutes))
            
            url = f"{self.BASE_URL}/isochrone/v1/mapbox/{profile}/{lng},{lat}"
            
            params = {
                "access_token": self.access_token,
                "contours_minutes": contours,
                "polygons": "true"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Isochrone API hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"İzochron hesaplama hatası: {e}")
            return None