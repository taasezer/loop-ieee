from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services.weather_service import weather_service
from typing import Optional

router = APIRouter()

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    courier_id: Optional[int] = None

@router.post("/current")
async def get_current_weather(request: WeatherRequest):
    """Get current weather conditions for a location"""
    weather_data = await weather_service.get_current_weather(
        request.latitude, 
        request.longitude
    )
    
    if not weather_data:
        # Return mock data if API fails
        return {
            "latitude": request.latitude,
            "longitude": request.longitude,
            "condition": "Clear",
            "description": "clear sky",
            "temperature": 22.5,
            "humidity": 45,
            "wind_speed": 12.0
        }
    
    return {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "condition": weather_data["weather"],
        "description": weather_data["description"],
        "temperature": weather_data["temperature"],
        "feels_like": weather_data["feels_like"],
        "humidity": weather_data["humidity"],
        "wind_speed": weather_data["wind_speed"],
        "visibility": weather_data["visibility"],
        "rain": weather_data["rain"],
        "snow": weather_data["snow"]
    }

@router.post("/impact")
async def calculate_weather_impact(
    request: WeatherRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate weather impact on delivery operations.
    Returns detailed impact score and recommendations.
    Used by n8n weather alert workflow.
    """
    # Get current weather data
    weather_data = await weather_service.get_current_weather(
        request.latitude,
        request.longitude
    )
    
    if not weather_data:
        # Return safe defaults if API fails
        return {
            "impact_score": 1.0,
            "severity": "none",
            "condition": "Unknown",
            "description": "Weather data unavailable",
            "recommendation": "Weather service unavailable. Proceed with caution.",
            "weather_conditions": {
                "temperature": None,
                "wind_speed": None,
                "rain": None,
                "snow": None,
                "visibility": None
            },
            "alert_required": False
        }
    
    # Calculate impact score
    impact_score = weather_service.calculate_weather_impact(weather_data)
    
    # Determine severity and recommendation
    severity = "none"
    recommendation = "Good conditions for delivery"
    alert_required = False
    
    if impact_score < 0.3:
        severity = "critical"
        recommendation = "DANGER: Severe weather conditions. Consider suspending deliveries."
        alert_required = True
    elif impact_score < 0.5:
        severity = "high"
        recommendation = "WARNING: Poor weather conditions. Proceed with extreme caution."
        alert_required = True
    elif impact_score < 0.7:
        severity = "moderate"
        recommendation = "CAUTION: Moderate weather impact. Drive carefully."
        alert_required = True
    elif impact_score < 0.85:
        severity = "low"
        recommendation = "Minor weather impact. Stay alert."
        alert_required = False
    
    # Build detailed response
    response = {
        "impact_score": round(impact_score, 2),
        "severity": severity,
        "condition": weather_data["weather"],
        "description": weather_data["description"],
        "recommendation": recommendation,
        "weather_conditions": {
            "temperature": weather_data["temperature"],
            "feels_like": weather_data["feels_like"],
            "wind_speed": weather_data["wind_speed"],
            "rain": weather_data["rain"],
            "snow": weather_data["snow"],
            "visibility": weather_data["visibility"],
            "humidity": weather_data["humidity"]
        },
        "alert_required": alert_required,
        "location": weather_data.get("location", "Unknown")
    }
    
    # Add courier info if provided
    if request.courier_id:
        response["courier_id"] = request.courier_id
    
    # Add specific warnings
    warnings = []
    if weather_data["rain"] > 5:
        warnings.append("Heavy rain: Reduced visibility and slippery roads")
    if weather_data["snow"] > 0:
        warnings.append("Snow: Dangerous driving conditions")
    if weather_data["wind_speed"] > 30:
        warnings.append("High winds: Risk for motorcycles and bikes")
    if weather_data["visibility"] < 1:
        warnings.append("Very low visibility: Extreme caution required")
    if weather_data["temperature"] < 0:
        warnings.append("Freezing temperature: Ice on roads possible")
    
    if warnings:
        response["warnings"] = warnings
    
    return response

