"""
SIP Calculator route - calculates SIP returns and projection curve
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from utils.calculations import calculate_sip_future_value

router = APIRouter()


class SIPCalculation(BaseModel):
    monthly_amount: float
    expected_return: float  # Annual return percentage
    time_period: float  # Years


@router.post("/api/sip/calc")
async def calculate_sip(sip_data: SIPCalculation):
    """
    Calculate SIP returns and generate projection curve
    Returns future value, total invested, returns, and monthly projection data
    """
    try:
        # Validate inputs
        if sip_data.monthly_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="monthly_amount must be greater than 0"
            )
        
        if sip_data.expected_return < 0 or sip_data.expected_return > 100:
            raise HTTPException(
                status_code=400,
                detail="expected_return must be between 0 and 100"
            )
        
        if sip_data.time_period <= 0:
            raise HTTPException(
                status_code=400,
                detail="time_period must be greater than 0"
            )
        
        monthly_amount = sip_data.monthly_amount
        annual_return = sip_data.expected_return
        years = sip_data.time_period
        
        # Calculate SIP returns
        monthly_return = annual_return / 12 / 100
        total_months = int(years * 12)
        
        # Future Value calculation (SIP formula)
        # FV = P * [((1 + r)^n - 1) / r] * (1 + r)
        # where P = monthly payment, r = monthly rate, n = number of months
        if monthly_return > 0:
            future_value = monthly_amount * (((1 + monthly_return) ** total_months - 1) / monthly_return) * (1 + monthly_return)
        else:
            # If return is 0, just sum the payments
            future_value = monthly_amount * total_months
        
        total_invested = monthly_amount * total_months
        total_returns = future_value - total_invested
        
        # Generate projection curve (monthly data points)
        projection_curve = generate_projection_curve(
            monthly_amount,
            monthly_return,
            total_months
        )
        
        return {
            "status": "success",
            "calculation": {
                "future_value": round(future_value, 2),
                "total_invested": round(total_invested, 2),
                "total_returns": round(total_returns, 2),
                "return_percentage": round((total_returns / total_invested * 100) if total_invested > 0 else 0, 2),
                "monthly_amount": monthly_amount,
                "annual_return": annual_return,
                "time_period": years,
                "total_months": total_months
            },
            "projection_curve": projection_curve
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating SIP: {str(e)}"
        )


def generate_projection_curve(monthly_amount: float, monthly_return: float, total_months: int) -> List[Dict]:
    """
    Generate monthly projection curve for SIP
    Returns list of {month, invested, value, returns} for each month
    """
    curve = []
    current_value = 0.0
    total_invested = 0.0
    
    # Generate data points (can be sampled for large periods)
    # For periods > 60 months, sample every 3 months
    step = 1 if total_months <= 60 else 3
    
    for month in range(0, total_months + 1, step):
        if month == 0:
            # Initial state
            curve.append({
                "month": 0,
                "invested": 0.0,
                "value": 0.0,
                "returns": 0.0
            })
        else:
            # Calculate value at this month
            # First, add the monthly investment
            total_invested = monthly_amount * month
            
            # Then calculate the accumulated value
            if monthly_return > 0:
                # FV = P * [((1 + r)^month - 1) / r] * (1 + r)
                current_value = monthly_amount * (((1 + monthly_return) ** month - 1) / monthly_return) * (1 + monthly_return)
            else:
                current_value = total_invested
            
            returns = current_value - total_invested
            
            curve.append({
                "month": month,
                "invested": round(total_invested, 2),
                "value": round(current_value, 2),
                "returns": round(returns, 2)
            })
    
    # Always include the final month
    if total_months % step != 0:
        total_invested = monthly_amount * total_months
        if monthly_return > 0:
            current_value = monthly_amount * (((1 + monthly_return) ** total_months - 1) / monthly_return) * (1 + monthly_return)
        else:
            current_value = total_invested
        
        returns = current_value - total_invested
        
        curve.append({
            "month": total_months,
            "invested": round(total_invested, 2),
            "value": round(current_value, 2),
            "returns": round(returns, 2)
        })
    
    return curve
