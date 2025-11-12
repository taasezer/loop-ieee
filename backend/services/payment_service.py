import httpx
import os
from typing import Dict
import logging
from datetime import datetime, timezone
from database import db

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_api_url = "https://api.stripe.com/v1"
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        customer_id: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Create a Stripe payment intent"""
        if not self.stripe_secret_key:
            logger.warning("Stripe secret key not configured")
            return {"success": False, "error": "Stripe not configured"}
        
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            payload = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "metadata": metadata or {}
            }
            
            if customer_id:
                payload["customer"] = customer_id
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.stripe_api_url}/payment_intents",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {self.stripe_secret_key}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "payment_intent_id": data["id"],
                        "client_secret": data["client_secret"],
                        "amount": amount,
                        "currency": currency,
                        "status": data["status"]
                    }
                else:
                    logger.error(f"Stripe error: {response.text}")
                    return {"success": False, "error": "Payment intent creation failed"}
        except Exception as e:
            logger.error(f"Payment service error: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_payout(
        self,
        courier_id: str,
        amount: float,
        currency: str = "usd"
    ) -> Dict:
        """Process payout to courier"""
        try:
            # In production, this would create actual Stripe transfers
            # For now, just log the payout
            logger.info(f"Processing payout: {amount} {currency} to courier {courier_id}")
            
            return {
                "success": True,
                "payout_id": f"po_{datetime.now(timezone.utc).timestamp()}",
                "amount": amount,
                "currency": currency,
                "courier_id": courier_id,
                "status": "pending"
            }
        except Exception as e:
            logger.error(f"Payout error: {e}")
            return {"success": False, "error": str(e)}
    
    async def record_cash_payment(self, order_id: str, amount: float) -> Dict:
        """Record a cash on delivery payment"""
        try:
            transaction = {
                "order_id": order_id,
                "amount": amount,
                "payment_method": "cash",
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await db.payment_transactions.insert_one(transaction)
            
            return {
                "success": True,
                "transaction": transaction
            }
        except Exception as e:
            logger.error(f"Cash payment recording error: {e}")
            return {"success": False, "error": str(e)}

payment_service = PaymentService()
