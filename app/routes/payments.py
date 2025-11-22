from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.orm import Order, PaymentTransaction, User
from app.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    currency: str = "TRY"
    payment_method_id: str # Stripe payment method ID

@router.post("/process")
async def process_payment(
    payment_in: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Mock Payment Processing (Stripe/Iyzico)
    # In prod: use stripe.PaymentIntent.create(...)
    
    # Verify order belongs to user
    order = await db.get(Order, payment_in.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Simulate success
    transaction = PaymentTransaction(
        order_id=payment_in.order_id,
        amount=payment_in.amount,
        currency=payment_in.currency,
        status="success",
        provider_transaction_id="mock_txn_12345"
    )
    
    db.add(transaction)
    await db.commit()
    
    return {"status": "success", "transaction_id": "mock_txn_12345"}
