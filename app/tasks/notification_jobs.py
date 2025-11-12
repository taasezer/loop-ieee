"""Notification processing tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.notification_jobs.process_pending_notifications")
def process_pending_notifications():
    """Process pending notifications"""
    logger.info("Processing pending notifications")
    return {"status": "success"}
