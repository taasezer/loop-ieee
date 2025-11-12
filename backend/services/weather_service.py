import httpx
import os
from typing import Dict
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = timedelta(hours=1)
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        return f"{lat:.2f},{lon:.2f}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        if cache_key in self.cache:
            cached_time = self.cache[cache_key].get("cached_at")
            if cached_time and datetime.now(timezone.utc) - cached_time < self.cache_duration:
                return True
        return False
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """Get current weather for location"""
        cache_key = self._get_cache_key(latitude, longitude)
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached weather for {cache_key}")
            return self.cache[cache_key]["data"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    weather_data = {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "weather": data["weather"][0]["main"],
                        "description": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"],
                        "clouds": data["clouds"]["all"],
                        "visibility": data.get("visibility", 10000),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = {
                        "data": weather_data,
                        "cached_at": datetime.now(timezone.utc)
                    }
                    
                    return weather_data
                else:
                    logger.error(f"Weather API error: {response.status_code}")
                    return self._get_default_weather()
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            return self._get_default_weather()
    
    async def get_forecast(self, latitude: float, longitude: float, days: int = 5) -> Dict:
        """Get weather forecast"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "city": data["city"]["name"],
                        "forecasts": [
                            {
                                "timestamp": item["dt_txt"],
                                "temperature": item["main"]["temp"],
                                "weather": item["weather"][0]["main"],
                                "description": item["weather"][0]["description"],
                                "wind_speed": item["wind"]["speed"],
                                "rain_probability": item.get("pop", 0) * 100
                            }
                            for item in data["list"]
                        ]
                    }
                return {"forecasts": []}
        except Exception as e:
            logger.error(f"Forecast service error: {e}")
            return {"forecasts": []}
    
    def _get_default_weather(self) -> Dict:
        """Return default weather when API fails"""
        return {
            "temperature": 20,
            "feels_like": 20,
            "humidity": 50,
            "pressure": 1013,
            "weather": "Clear",
            "description": "clear sky",
            "wind_speed": 5,
            "clouds": 0,
            "visibility": 10000,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Default weather data - API unavailable"
        }
    
    def calculate_weather_impact(self, weather_data: Dict) -> float:
        """Calculate weather impact factor for pricing (1.0 = normal, >1.0 = bad weather)"""
        impact = 1.0
        
        # Rain/Snow impact
        if weather_data["weather"] in ["Rain", "Drizzle"]:
            impact += 0.2
        elif weather_data["weather"] in ["Snow", "Thunderstorm"]:
            impact += 0.4
        
        # Wind impact
        if weather_data["wind_speed"] > 10:
            impact += 0.1
        
        # Visibility impact
        if weather_data["visibility"] < 5000:
            impact += 0.15
        
        return min(impact, 2.0)  # Cap at 2x

weather_service = WeatherService()
