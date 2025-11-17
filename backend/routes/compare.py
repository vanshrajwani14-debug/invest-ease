"""
Compare route - returns metrics for top investment options
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from routes.ml_placeholder import get_investment_recommendation
from utils.data_fetcher import fetch_scheme_details, fetch_etf_history, fetch_stock_history

router = APIRouter()


@router.get("/api/compare")
async def compare_plans(risk_preference: str = "Medium"):
    """
    Compare top 3 investment plans/funds
    Returns metrics: returns, volatility, AUM, expense ratio
    """
    try:
        if risk_preference not in ["Low", "Medium", "High"]:
            raise HTTPException(
                status_code=400,
                detail="risk_preference must be one of: Low, Medium, High"
            )
        
        # Get recommendations
        user_data = {
            "risk_preference": risk_preference,
            "age": 30,  # Default age for comparison
            "investment_amount": 100000  # Default amount
        }
        
        recommendations = get_investment_recommendation(user_data)
        
        # Get top 3 from each category and fetch detailed metrics
        comparison_data = []
        
        # Equity funds
        for fund in recommendations.get("equity", [])[:3]:
            metrics = get_fund_metrics(fund)
            if metrics:
                comparison_data.append({
                    "category": "Equity Mutual Fund",
                    "name": fund.get("scheme_name", ""),
                    "fund_house": fund.get("fund_house", ""),
                    **metrics
                })
        
        # Debt funds
        for fund in recommendations.get("debt", [])[:3]:
            metrics = get_fund_metrics(fund)
            if metrics:
                comparison_data.append({
                    "category": "Debt Mutual Fund",
                    "name": fund.get("scheme_name", ""),
                    "fund_house": fund.get("fund_house", ""),
                    **metrics
                })
        
        # Hybrid funds
        for fund in recommendations.get("hybrid", [])[:3]:
            metrics = get_fund_metrics(fund)
            if metrics:
                comparison_data.append({
                    "category": "Hybrid Mutual Fund",
                    "name": fund.get("scheme_name", ""),
                    "fund_house": fund.get("fund_house", ""),
                    **metrics
                })
        
        # Gold ETFs
        for etf in recommendations.get("gold", [])[:3]:
            metrics = get_etf_metrics(etf)
            if metrics:
                comparison_data.append({
                    "category": "Gold ETF",
                    "name": etf.get("name", ""),
                    "fund_house": "ETF",
                    **metrics
                })
        
        # Stocks
        for stock in recommendations.get("stocks", [])[:2]:
            metrics = get_stock_metrics(stock)
            if metrics:
                comparison_data.append({
                    "category": "Blue-Chip Stock",
                    "name": stock.get("name", ""),
                    "fund_house": "Stock",
                    **metrics
                })
        
        return {
            "status": "success",
            "plans": comparison_data[:9]  # Top 9 total (3 from each main category)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing plans: {str(e)}"
        )


def get_fund_metrics(fund: Dict) -> Optional[Dict]:
    """
    Get detailed metrics for a mutual fund
    Returns: returns, volatility, AUM, expense_ratio
    """
    try:
        scheme_code = fund.get("scheme_code")
        if not scheme_code:
            return None
        
        # Fetch scheme details
        scheme_details = fetch_scheme_details(scheme_code)
        if not scheme_details:
            return None
        
        meta = scheme_details.get("meta", {})
        nav_data = scheme_details.get("data", [])
        
        # Extract metrics
        returns_3yr = fund.get("return_3yr", 0.0)
        returns_5yr = fund.get("return_5yr", 0.0)
        volatility = fund.get("volatility", 0.0)
        
        # AUM and expense ratio from meta (if available)
        # Note: MFAPI may not always provide these, so we'll use defaults
        aum = meta.get("fund_house", "")  # Placeholder - AUM not always in API
        expense_ratio = 0.0  # Placeholder - expense ratio not in MFAPI
        
        # Try to get AUM from scheme name or use default
        # TODO: Enhance with additional data sources for AUM and expense ratio
        
        return {
            "returns_3yr": returns_3yr,
            "returns_5yr": returns_5yr,
            "volatility": volatility,
            "aum": "N/A",  # AUM not available in MFAPI
            "expense_ratio": "N/A",  # Expense ratio not available in MFAPI
            "nav": fund.get("nav", 0.0),
            "scheme_code": scheme_code
        }
        
    except Exception as e:
        print(f"Error getting fund metrics: {e}")
        return None


def get_etf_metrics(etf: Dict) -> Optional[Dict]:
    """
    Get detailed metrics for an ETF
    """
    try:
        ticker = etf.get("ticker")
        if not ticker:
            return None
        
        etf_data = fetch_etf_history(ticker, period="5y")
        if not etf_data:
            return None
        
        info = etf_data.get("info", {})
        
        return {
            "returns_3yr": etf.get("return_3yr", 0.0),
            "returns_5yr": etf.get("return_5yr", 0.0),
            "volatility": etf.get("volatility", 0.0),
            "aum": info.get("totalAssets", "N/A"),
            "expense_ratio": info.get("annualReportExpenseRatio", "N/A"),
            "nav": etf.get("current_price", 0.0),
            "ticker": ticker
        }
        
    except Exception as e:
        print(f"Error getting ETF metrics: {e}")
        return None


def get_stock_metrics(stock: Dict) -> Optional[Dict]:
    """
    Get detailed metrics for a stock
    """
    try:
        ticker = stock.get("ticker")
        if not ticker:
            return None
        
        stock_data = fetch_stock_history(ticker, period="5y")
        if not stock_data:
            return None
        
        info = stock_data.get("info", {})
        
        return {
            "returns_3yr": stock.get("return_3yr", 0.0),
            "returns_5yr": stock.get("return_5yr", 0.0),
            "volatility": stock.get("volatility", 0.0),
            "aum": "N/A",  # Not applicable for stocks
            "expense_ratio": "N/A",  # Not applicable for stocks
            "nav": stock.get("current_price", 0.0),
            "ticker": ticker,
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A")
        }
        
    except Exception as e:
        print(f"Error getting stock metrics: {e}")
        return None
