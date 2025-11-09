import httpx
from typing import Dict, Optional
from app.config import settings

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Get current weather conditions for a location"""
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
                response.raise_for_status()
                data = response.json()

                return {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "weather": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "wind_direction": data["wind"].get("deg", 0),
                    "visibility": data.get("visibility", 10000) / 1000,
                    "clouds": data["clouds"]["all"],
                    "rain": data.get("rain", {}).get("1h", 0),
                    "snow": data.get("snow", {}).get("1h", 0),
                    "location": data["name"]
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    async def get_weather_forecast(self, latitude: float, longitude: float, hours: int = 24) -> Optional[Dict]:
        """Get weather forecast for next X hours"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": min(hours // 3, 40)
                    }
                )
                response.raise_for_status()
                data = response.json()

                forecasts = []
                for item in data["list"]:
                    forecasts.append({
                        "timestamp": item["dt"],
                        "datetime": item["dt_txt"],
                        "temperature": item["main"]["temp"],
                        "weather": item["weather"][0]["main"],
                        "description": item["weather"][0]["description"],
                        "wind_speed": item["wind"]["speed"],
                        "rain_probability": item.get("pop", 0) * 100,
                        "rain_volume": item.get("rain", {}).get("3h", 0)
                    })

                return {
                    "location": data["city"]["name"],
                    "forecasts": forecasts
                }
        except Exception as e:
            print(f"Weather forecast error: {e}")
            return None

    def calculate_weather_impact(self, weather_data: Dict) -> float:
        """
        Calculate weather impact score for delivery (0.0 to 1.0)
        Lower score means worse conditions for delivery
        """
        score = 1.0

        if weather_data["rain"] > 0:
            score -= min(weather_data["rain"] * 0.1, 0.3)

        if weather_data["snow"] > 0:
            score -= min(weather_data["snow"] * 0.15, 0.4)

        if weather_data["wind_speed"] > 20:
            score -= 0.2
        elif weather_data["wind_speed"] > 30:
            score -= 0.4

        if weather_data["visibility"] < 1:
            score -= 0.3
        elif weather_data["visibility"] < 5:
            score -= 0.1

        if weather_data["temperature"] < 0 or weather_data["temperature"] > 40:
            score -= 0.15

        return max(0.0, min(1.0, score))

weather_service = WeatherService()
