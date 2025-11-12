"""Helper utility functions"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string

def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(3).upper()
    return f"ORD-{timestamp}-{random_part}"

def generate_tracking_number() -> str:
    """Generate tracking number"""
    return f"TRK-{secrets.token_hex(8).upper()}"

def format_phone_number(phone: str) -> str:
    """Format phone number to E.164 format"""
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    if not digits.startswith('+'):
        digits = '+' + digits
    return digits

def calculate_eta(distance_km: float, avg_speed_kmh: float = 30) -> datetime:
    """Calculate estimated time of arrival"""
    hours = distance_km / avg_speed_kmh
    return datetime.utcnow() + timedelta(hours=hours)

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data (e.g., phone, email)"""
    if len(data) <= visible_chars:
        return data
    return data[:visible_chars] + '*' * (len(data) - visible_chars)

def generate_random_code(length: int = 6) -> str:
    """Generate random alphanumeric code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
