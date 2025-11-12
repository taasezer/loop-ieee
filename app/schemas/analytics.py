"""Analytics schemas"""
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime

class DashboardStatsResponse(BaseModel):
    total_orders: int
    active_orders: int
    total_revenue: float
    active_couriers: int
    average_delivery_time: float

class RevenueAnalyticsResponse(BaseModel):
    daily_revenue: List[Dict[str, Any]]
    weekly_revenue: float
    monthly_revenue: float
    
class PerformanceMetricsResponse(BaseModel):
    delivery_success_rate: float
    average_rating: float
    on_time_delivery_rate: float
