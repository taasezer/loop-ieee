from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.weather_service import weather_service

router = APIRouter()

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float

class ForecastRequest(BaseModel):
    latitude: float
    longitude: float
    hours: int = 24

@router.post("/current")
async def get_current_weather(request: WeatherRequest):
    """Get current weather conditions for a location"""
    result = await weather_service.get_current_weather(request.latitude, request.longitude)
    if not result:
        raise HTTPException(status_code=404, detail="Weather data not available")
    return result

@router.post("/forecast")
async def get_forecast(request: ForecastRequest):
    """Get weather forecast for specified hours"""
    result = await weather_service.get_weather_forecast(
        request.latitude,
        request.longitude,
        request.hours
    )
    if not result:
        raise HTTPException(status_code=404, detail="Forecast data not available")
    return result

@router.post("/impact")
async def calculate_weather_impact(request: WeatherRequest):
    """Calculate weather impact score for delivery operations"""
    weather = await weather_service.get_current_weather(request.latitude, request.longitude)
    if not weather:
        raise HTTPException(status_code=404, detail="Weather data not available")

    impact_score = weather_service.calculate_weather_impact(weather)

    return {
        "weather_conditions": weather,
        "impact_score": impact_score,
        "recommendation": (
            "Excellent conditions" if impact_score > 0.8 else
            "Good conditions" if impact_score > 0.6 else
            "Fair conditions - caution advised" if impact_score > 0.4 else
            "Poor conditions - delays expected"
        )
    }
