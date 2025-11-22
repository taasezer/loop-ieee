from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/current")
async def get_current_weather(request: WeatherRequest):
    # Mock weather data
    return {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "condition": "Clear",
        "temperature": 22.5,
        "humidity": 45,
        "wind_speed": 12.0
    }

@router.post("/impact")
async def calculate_weather_impact(request: WeatherRequest):
    return {
        "impact_score": 1.0, # 1.0 = No impact (good weather)
        "condition": "Clear",
        "recommendation": "Good conditions for delivery"
    }
