"""OpenWeatherMap API client"""
import httpx
from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class OpenWeatherClient:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather for coordinates"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "weather": data["weather"][0]["main"],
                        "description": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"],
                        "clouds": data["clouds"]["all"]
                    }
                return None
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return None
    
    def is_bad_weather(self, weather_data: Dict[str, Any]) -> bool:
        """Check if weather conditions are bad for delivery"""
        if not weather_data:
            return False
        bad_conditions = ["Rain", "Snow", "Thunderstorm", "Drizzle"]
        return weather_data.get("weather") in bad_conditions or weather_data.get("wind_speed", 0) > 15

openweather_client = OpenWeatherClient()
