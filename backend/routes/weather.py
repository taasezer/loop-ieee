from fastapi import APIRouter, HTTPException
from services.weather_service import weather_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/current")
async def get_current_weather(latitude: float, longitude: float):
    """Get current weather conditions"""
    try:
        weather = await weather_service.get_current_weather(latitude, longitude)
        return weather
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")

@router.get("/forecast")
async def get_forecast(latitude: float, longitude: float, days: int = 5):
    """Get weather forecast"""
    try:
        forecast = await weather_service.get_forecast(latitude, longitude, days)
        return forecast
    except Exception as e:
        logger.error(f"Forecast fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch forecast data")

@router.get("/impact")
async def get_weather_impact(latitude: float, longitude: float):
    """Get weather impact factor for pricing"""
    try:
        weather = await weather_service.get_current_weather(latitude, longitude)
        impact = weather_service.calculate_weather_impact(weather)
        return {
            "weather": weather,
            "impact_factor": impact,
            "impact_percentage": round((impact - 1.0) * 100, 1)
        }
    except Exception as e:
        logger.error(f"Weather impact calculation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate weather impact")
