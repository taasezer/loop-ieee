"""Payment schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class PaymentIntentRequest(BaseModel):
    order_id: UUID
    amount: float
    currency: str = "USD"

class PaymentResponse(BaseModel):
    transaction_id: UUID
    status: str
    amount: float
    gateway: str
    
    class Config:
        from_attributes = True
