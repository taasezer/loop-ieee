"""Weather data update tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.weather_update.update_weather_cache")
def update_weather_cache():
    """Update weather data cache - runs hourly"""
    logger.info("Updating weather cache")
    return {"status": "success"}
