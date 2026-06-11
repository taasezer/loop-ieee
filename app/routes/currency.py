from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import httpx

router = APIRouter()

class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

@router.post("/convert")
async def convert_currency(request: ConvertRequest):
    # Real conversion using open.er-api.com
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://open.er-api.com/v6/latest/{request.from_currency}")
            response.raise_for_status()
            data = response.json()
            
            rates = data.get("rates", {})
            if request.to_currency not in rates:
                raise HTTPException(status_code=400, detail=f"Currency {request.to_currency} not supported")
                
            rate = rates[request.to_currency]
            converted_amount = request.amount * rate
            
            return {
                "from": request.from_currency,
                "to": request.to_currency,
                "amount": request.amount,
                "result": round(converted_amount, 2),
                "rate": round(rate, 4)
            }
    except Exception as e:
        # Fallback to mock if API fails
        print(f"Currency API error: {e}")
        rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "TRY": 32.5,
            "GBP": 0.79
        }
        if request.from_currency not in rates or request.to_currency not in rates:
            raise HTTPException(status_code=400, detail="Currency not supported")
            
        base_amount = request.amount / rates[request.from_currency]
        converted_amount = base_amount * rates[request.to_currency]
    
    return {
        "from": request.from_currency,
        "to": request.to_currency,
        "amount": request.amount,
        "result": round(converted_amount, 2),
        "rate": round(rates[request.to_currency] / rates[request.from_currency], 4)
    }

@router.get("/popular")
async def get_popular_currencies():
    return ["USD", "EUR", "TRY", "GBP", "JPY"]
