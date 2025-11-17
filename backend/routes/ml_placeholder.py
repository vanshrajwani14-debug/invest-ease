"""
ML-based recommendation engine for investment recommendations
Uses data_fetcher and scoring utilities to generate real recommendations
"""

from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_fetcher import (
    fetch_mutual_funds,
    fetch_scheme_details,
    fetch_etf_history,
    fetch_stock_history,
    categorize_fund
)
from utils.scoring import (
    calc_3yr_return,
    calc_5yr_return,
    calc_volatility,
    calc_consistency,
    calc_returns_from_price_history,
    calc_volatility_from_price_history,
    combined_score
)


def get_investment_recommendation(user_data: Dict) -> Dict:
    """
    Generate investment recommendations based on user profile
    Returns recommendations for equity, debt, hybrid, gold ETFs, and stocks
    """
    risk_preference = user_data.get("risk_preference", "Medium")
    age = user_data.get("age", 30)
    investment_amount = user_data.get("investment_amount", 100000)
    
    # Fetch mutual funds data
    print("Fetching mutual funds data...")
    all_funds = fetch_mutual_funds(limit=200)
    
    # Categorize funds
    equity_funds = []
    debt_funds = []
    hybrid_funds = []
    gold_etfs = []
    
    for fund in all_funds:
        category = categorize_fund(fund)
        if category == "equity":
            equity_funds.append(fund)
        elif category == "debt":
            debt_funds.append(fund)
        elif category == "hybrid":
            hybrid_funds.append(fund)
        elif category == "gold_etf":
            gold_etfs.append(fund)
    
    # Score and rank funds in each category
    equity_scored = score_and_rank_funds(equity_funds, risk_preference, limit=10)
    debt_scored = score_and_rank_funds(debt_funds, risk_preference, limit=10)
    hybrid_scored = score_and_rank_funds(hybrid_funds, risk_preference, limit=10)
    
    # Fetch and score gold ETFs
    gold_etf_tickers = ["GOLDBEES.NS", "GOLDSHARE.NS", "GOLDMANIPHYSICAL.NS"]
    gold_scored = score_etfs(gold_etf_tickers, risk_preference)
    
    # Fetch and score blue-chip stocks
    stock_tickers = ["HDFCBANK.NS", "INFY.NS", "TCS.NS", "RELIANCE.NS", "ICICIBANK.NS"]
    stocks_scored = score_stocks(stock_tickers, risk_preference)
    
    # Select top 3 from each category
    recommendations = {
        "equity": equity_scored[:3],
        "debt": debt_scored[:3],
        "hybrid": hybrid_scored[:3],
        "gold": gold_scored[:3] if len(gold_scored) > 0 else [],
        "stocks": stocks_scored[:2] if len(stocks_scored) > 0 else []  # 1-2 stocks as requested
    }
    
    return recommendations


def score_and_rank_funds(funds: List[Dict], risk_preference: str, limit: int = 10) -> List[Dict]:
    """
    Score and rank mutual funds based on historical performance
    """
    scored_funds = []
    
    for fund in funds[:limit * 2]:  # Check more funds to get better results
        scheme_code = fund.get("scheme_code")
        if not scheme_code:
            continue
        
        try:
            # Fetch scheme details
            scheme_details = fetch_scheme_details(scheme_code)
            if not scheme_details or "data" not in scheme_details:
                continue
            
            nav_data = scheme_details.get("data", [])
            if len(nav_data) < 10:  # Need sufficient data
                continue
            
            # Calculate metrics
            return_3yr = calc_3yr_return(nav_data)
            return_5yr = calc_5yr_return(nav_data)
            volatility = calc_volatility(nav_data)
            consistency = calc_consistency(nav_data)
            
            # Skip funds with invalid data
            if return_3yr == 0 and return_5yr == 0:
                continue
            
            # Create candidate dict
            candidate = {
                "scheme_code": scheme_code,
                "scheme_name": fund.get("scheme_name", ""),
                "fund_house": fund.get("fund_house", ""),
                "scheme_type": fund.get("scheme_type", ""),
                "scheme_category": fund.get("scheme_category", ""),
                "nav": fund.get("nav", 0.0),
                "return_3yr": return_3yr,
                "return_5yr": return_5yr,
                "volatility": volatility,
                "consistency": consistency
            }
            
            # Calculate combined score
            candidate["score"] = combined_score(candidate, risk_preference)
            
            scored_funds.append(candidate)
            
        except Exception as e:
            print(f"Error scoring fund {scheme_code}: {e}")
            continue
    
    # Sort by score (descending)
    scored_funds.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return scored_funds


def score_etfs(etf_tickers: List[str], risk_preference: str) -> List[Dict]:
    """
    Score and rank gold ETFs
    """
    scored_etfs = []
    
    for ticker in etf_tickers:
        try:
            etf_data = fetch_etf_history(ticker, period="5y")
            if not etf_data or "history" not in etf_data:
                continue
            
            price_history = etf_data["history"].get("close", [])
            if len(price_history) < 10:
                continue
            
            # Calculate metrics
            return_3yr = calc_returns_from_price_history(price_history[-756:], 3.0)  # ~3 years
            return_5yr = calc_returns_from_price_history(price_history, 5.0)
            volatility = calc_volatility_from_price_history(price_history)
            
            # For ETFs, consistency is based on positive return periods
            returns = []
            for i in range(1, len(price_history)):
                if price_history[i-1] > 0:
                    ret = ((price_history[i] - price_history[i-1]) / price_history[i-1]) * 100
                    returns.append(ret)
            
            positive_periods = sum(1 for r in returns if r > 0) if returns else 0
            consistency = (positive_periods / len(returns) * 100) if returns else 0
            
            candidate = {
                "ticker": ticker,
                "name": etf_data.get("info", {}).get("longName", ticker),
                "current_price": etf_data.get("current_price", 0.0),
                "return_3yr": return_3yr,
                "return_5yr": return_5yr,
                "volatility": volatility,
                "consistency": round(consistency, 2)
            }
            
            candidate["score"] = combined_score(candidate, risk_preference)
            scored_etfs.append(candidate)
            
        except Exception as e:
            print(f"Error scoring ETF {ticker}: {e}")
            continue
    
    # Sort by score
    scored_etfs.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return scored_etfs


def score_stocks(stock_tickers: List[str], risk_preference: str) -> List[Dict]:
    """
    Score and rank blue-chip stocks
    """
    scored_stocks = []
    
    for ticker in stock_tickers:
        try:
            stock_data = fetch_stock_history(ticker, period="5y")
            if not stock_data or "history" not in stock_data:
                continue
            
            price_history = stock_data["history"].get("close", [])
            if len(price_history) < 10:
                continue
            
            # Calculate metrics
            return_3yr = calc_returns_from_price_history(price_history[-756:], 3.0)
            return_5yr = calc_returns_from_price_history(price_history, 5.0)
            volatility = calc_volatility_from_price_history(price_history)
            
            # Consistency for stocks
            returns = []
            for i in range(1, len(price_history)):
                if price_history[i-1] > 0:
                    ret = ((price_history[i] - price_history[i-1]) / price_history[i-1]) * 100
                    returns.append(ret)
            
            positive_periods = sum(1 for r in returns if r > 0) if returns else 0
            consistency = (positive_periods / len(returns) * 100) if returns else 0
            
            candidate = {
                "ticker": ticker,
                "name": stock_data.get("info", {}).get("longName", ticker),
                "current_price": stock_data.get("current_price", 0.0),
                "return_3yr": return_3yr,
                "return_5yr": return_5yr,
                "volatility": volatility,
                "consistency": round(consistency, 2)
            }
            
            candidate["score"] = combined_score(candidate, risk_preference)
            scored_stocks.append(candidate)
            
        except Exception as e:
            print(f"Error scoring stock {ticker}: {e}")
            continue
    
    # Sort by score
    scored_stocks.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return scored_stocks


def generate_explanation(recommendations: Dict, user_data: Dict) -> str:
    """
    Generate explanation for the recommendations
    """
    risk_preference = user_data.get("risk_preference", "Medium")
    age = user_data.get("age", 30)
    investment_amount = user_data.get("investment_amount", 100000)
    
    explanation_parts = []
    
    if risk_preference.upper() == "LOW":
        explanation_parts.append(
            f"Based on your low risk preference, we've selected conservative investments "
            f"focusing on capital preservation and steady returns."
        )
    elif risk_preference.upper() == "MEDIUM":
        explanation_parts.append(
            f"Given your medium risk tolerance, we've balanced your portfolio between "
            f"growth-oriented equity funds and stable debt instruments."
        )
    else:
        explanation_parts.append(
            f"With your high risk tolerance, we've selected aggressive growth investments "
            f"that offer higher return potential over the long term."
        )
    
    if age < 30:
        explanation_parts.append(
            "Your young age allows for a longer investment horizon, enabling you to "
            "benefit from compounding returns."
        )
    elif age > 50:
        explanation_parts.append(
            "Given your age, we've included stable debt and hybrid funds to protect "
            "your capital while still providing growth opportunities."
        )
    
    # Add category-specific explanations
    if recommendations.get("equity"):
        explanation_parts.append(
            f"The equity mutual funds selected have shown strong historical performance "
            f"with good risk-adjusted returns."
        )
    
    if recommendations.get("debt"):
        explanation_parts.append(
            "Debt funds provide stability and regular income, serving as a buffer "
            "against market volatility."
        )
    
    if recommendations.get("gold"):
        explanation_parts.append(
            "Gold ETFs are included as a hedge against inflation and economic uncertainty."
        )
    
    if recommendations.get("stocks"):
        explanation_parts.append(
            "The selected blue-chip stocks are established companies with strong "
            "fundamentals and consistent dividend history."
        )
    
    return " ".join(explanation_parts)
