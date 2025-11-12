"""Data formatting utilities"""
from datetime import datetime
from typing import Any, Dict

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "TRY": "₺"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"

def format_distance(distance_km: float) -> str:
    """Format distance"""
    if distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    return f"{distance_km:.1f}km"

def format_duration(minutes: float) -> str:
    """Format duration"""
    if minutes < 60:
        return f"{int(minutes)} min"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}min"

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime"""
    return dt.strftime(format)
