"""
Celery application configuration
"""

from celery import Celery
from celery.schedules import crontab
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "loop",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.currency_update",
        "app.tasks.weather_update",
        "app.tasks.analytics_jobs",
        "app.tasks.notification_jobs",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    # Update currency rates daily at 2 AM
    "update-currency-rates": {
        "task": "app.tasks.currency_update.update_exchange_rates",
        "schedule": crontab(hour=2, minute=0),
    },
    # Update weather data every hour
    "update-weather-data": {
        "task": "app.tasks.weather_update.update_weather_cache",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Generate daily analytics at 1 AM
    "generate-daily-analytics": {
        "task": "app.tasks.analytics_jobs.generate_daily_report",
        "schedule": crontab(hour=1, minute=0),
    },
    # Process pending notifications every 5 minutes
    "process-pending-notifications": {
        "task": "app.tasks.notification_jobs.process_pending_notifications",
        "schedule": crontab(minute="*/5"),
    },
}

logger.info("Celery app configured successfully")
