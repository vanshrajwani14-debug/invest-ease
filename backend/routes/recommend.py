"""
Recommendation route - generates investment recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from routes.ml_placeholder import get_investment_recommendation, generate_explanation

router = APIRouter()


class UserDetails(BaseModel):
    # Mandatory inputs
    age: int
    investment_amount: float
    risk_preference: str  # Low / Medium / High
    
    # Optional inputs
    monthly_income: Optional[float] = None
    savings: Optional[float] = None
    time_horizon: Optional[str] = None
    experience_level: Optional[str] = None
    financial_goals: Optional[str] = None
    monthly_expenses: Optional[float] = None


@router.post("/api/recommend")
async def get_recommendation(user_details: UserDetails):
    """
    Generate investment recommendations based on user profile
    Returns recommendations for equity, debt, hybrid, gold ETFs, and stocks
    """
    try:
        # Validate mandatory inputs
        if user_details.risk_preference not in ["Low", "Medium", "High"]:
            raise HTTPException(
                status_code=400,
                detail="risk_preference must be one of: Low, Medium, High"
            )
        
        if user_details.age < 18 or user_details.age > 100:
            raise HTTPException(
                status_code=400,
                detail="age must be between 18 and 100"
            )
        
        if user_details.investment_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="investment_amount must be greater than 0"
            )
        
        # Convert to dict
        user_data = user_details.dict()
        
        # Get recommendations from ML engine
        recommendations = get_investment_recommendation(user_data)
        
        # Generate explanation
        explanation = generate_explanation(recommendations, user_data)
        
        # Format response
        response = {
            "equity": format_fund_recommendations(recommendations.get("equity", [])),
            "debt": format_fund_recommendations(recommendations.get("debt", [])),
            "hybrid": format_fund_recommendations(recommendations.get("hybrid", [])),
            "gold": format_etf_recommendations(recommendations.get("gold", [])),
            "stocks": format_stock_recommendations(recommendations.get("stocks", [])),
            "explanation": explanation
        }
        
        return {
            "status": "success",
            "recommendations": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


def format_fund_recommendations(funds: list) -> list:
    """
    Format mutual fund recommendations for response
    """
    formatted = []
    for fund in funds:
        formatted.append({
            "name": fund.get("scheme_name", ""),
            "scheme_code": fund.get("scheme_code", ""),
            "fund_house": fund.get("fund_house", ""),
            "scheme_type": fund.get("scheme_type", ""),
            "scheme_category": fund.get("scheme_category", ""),
            "nav": fund.get("nav", 0.0),
            "return_3yr": fund.get("return_3yr", 0.0),
            "return_5yr": fund.get("return_5yr", 0.0),
            "volatility": fund.get("volatility", 0.0),
            "consistency": fund.get("consistency", 0.0),
            "score": fund.get("score", 0.0)
        })
    return formatted


def format_etf_recommendations(etfs: list) -> list:
    """
    Format ETF recommendations for response
    """
    formatted = []
    for etf in etfs:
        formatted.append({
            "name": etf.get("name", ""),
            "ticker": etf.get("ticker", ""),
            "current_price": etf.get("current_price", 0.0),
            "return_3yr": etf.get("return_3yr", 0.0),
            "return_5yr": etf.get("return_5yr", 0.0),
            "volatility": etf.get("volatility", 0.0),
            "consistency": etf.get("consistency", 0.0),
            "score": etf.get("score", 0.0)
        })
    return formatted


def format_stock_recommendations(stocks: list) -> list:
    """
    Format stock recommendations for response
    """
    formatted = []
    for stock in stocks:
        formatted.append({
            "name": stock.get("name", ""),
            "ticker": stock.get("ticker", ""),
            "current_price": stock.get("current_price", 0.0),
            "return_3yr": stock.get("return_3yr", 0.0),
            "return_5yr": stock.get("return_5yr", 0.0),
            "volatility": stock.get("volatility", 0.0),
            "consistency": stock.get("consistency", 0.0),
            "score": stock.get("score", 0.0)
        })
    return formatted
