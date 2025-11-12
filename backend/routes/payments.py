from fastapi import APIRouter, HTTPException, Depends
from services.payment_service import payment_service
from utils.auth import get_current_user, require_role
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class PaymentIntentRequest(BaseModel):
    amount: float
    currency: str = "usd"
    order_id: str

class CashPaymentRequest(BaseModel):
    order_id: str
    amount: float

@router.post("/create-intent")
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe payment intent"""
    try:
        result = await payment_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=current_user["sub"],
            metadata={"order_id": request.order_id}
        )
        return result
    except Exception as e:
        logger.error(f"Create payment intent error: {e}")
        raise HTTPException(status_code=500, detail="Payment intent creation failed")

@router.post("/cash")
async def record_cash_payment(
    request: CashPaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Record cash on delivery payment"""
    try:
        result = await payment_service.record_cash_payment(request.order_id, request.amount)
        return result
    except Exception as e:
        logger.error(f"Cash payment recording error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record cash payment")

@router.post("/payout/{courier_id}")
async def process_courier_payout(
    courier_id: str,
    amount: float,
    currency: str = "usd",
    current_user: dict = Depends(require_role(["admin"]))
):
    """Process payout to courier"""
    try:
        result = await payment_service.process_payout(courier_id, amount, currency)
        return result
    except Exception as e:
        logger.error(f"Payout error: {e}")
        raise HTTPException(status_code=500, detail="Payout processing failed")
