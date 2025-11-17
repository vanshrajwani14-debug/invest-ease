"""
Scoring functions for mutual funds, ETFs, and stocks
Calculates returns, volatility, consistency, and combined scores
"""

import statistics
from typing import Dict, List, Optional
from datetime import datetime, timedelta


def calc_3yr_return(nav_data: List[Dict]) -> float:
    """
    Calculate 3-year return percentage from NAV history
    nav_data: List of dicts with 'date' and 'nav' keys
    Returns annualized return percentage
    """
    if not nav_data or len(nav_data) < 2:
        return 0.0
    
    # Sort by date (oldest first)
    sorted_data = sorted(nav_data, key=lambda x: x.get('date', ''))
    
    # Get NAV from 3 years ago (approximately)
    # If we don't have exactly 3 years, use available data
    start_nav = None
    end_nav = None
    
    if len(sorted_data) >= 1:
        end_nav = float(sorted_data[-1].get('nav', 0))
    
    # Try to find NAV from ~3 years ago (1095 days)
    three_years_ago = datetime.now() - timedelta(days=1095)
    
    for entry in sorted_data:
        try:
            entry_date = datetime.strptime(entry.get('date', ''), '%d-%m-%Y')
            if entry_date <= three_years_ago:
                start_nav = float(entry.get('nav', 0))
        except:
            # If date parsing fails, use first entry
            if start_nav is None:
                start_nav = float(entry.get('nav', 0))
    
    # If we couldn't find 3-year-old data, use first available
    if start_nav is None and len(sorted_data) > 0:
        start_nav = float(sorted_data[0].get('nav', 0))
    
    if start_nav is None or end_nav is None or start_nav == 0:
        return 0.0
    
    # Calculate annualized return
    # CAGR = ((End Value / Start Value) ^ (1/years)) - 1
    years = 3.0
    if len(sorted_data) > 1:
        try:
            first_date = datetime.strptime(sorted_data[0].get('date', ''), '%d-%m-%Y')
            last_date = datetime.strptime(sorted_data[-1].get('date', ''), '%d-%m-%Y')
            years = (last_date - first_date).days / 365.25
            if years < 0.1:  # Less than 1 month
                years = 3.0
        except:
            pass
    
    if years < 0.1:
        return 0.0
    
    cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
    return round(cagr, 2)


def calc_5yr_return(nav_data: List[Dict]) -> float:
    """
    Calculate 5-year return percentage from NAV history
    nav_data: List of dicts with 'date' and 'nav' keys
    Returns annualized return percentage
    """
    if not nav_data or len(nav_data) < 2:
        return 0.0
    
    # Sort by date (oldest first)
    sorted_data = sorted(nav_data, key=lambda x: x.get('date', ''))
    
    start_nav = None
    end_nav = None
    
    if len(sorted_data) >= 1:
        end_nav = float(sorted_data[-1].get('nav', 0))
    
    # Try to find NAV from ~5 years ago (1825 days)
    five_years_ago = datetime.now() - timedelta(days=1825)
    
    for entry in sorted_data:
        try:
            entry_date = datetime.strptime(entry.get('date', ''), '%d-%m-%Y')
            if entry_date <= five_years_ago:
                start_nav = float(entry.get('nav', 0))
        except:
            if start_nav is None:
                start_nav = float(entry.get('nav', 0))
    
    if start_nav is None and len(sorted_data) > 0:
        start_nav = float(sorted_data[0].get('nav', 0))
    
    if start_nav is None or end_nav is None or start_nav == 0:
        return 0.0
    
    # Calculate annualized return
    years = 5.0
    if len(sorted_data) > 1:
        try:
            first_date = datetime.strptime(sorted_data[0].get('date', ''), '%d-%m-%Y')
            last_date = datetime.strptime(sorted_data[-1].get('date', ''), '%d-%m-%Y')
            years = (last_date - first_date).days / 365.25
            if years < 0.1:
                years = 5.0
        except:
            pass
    
    if years < 0.1:
        return 0.0
    
    cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
    return round(cagr, 2)


def calc_volatility(nav_data: List[Dict]) -> float:
    """
    Calculate volatility (standard deviation of returns) from NAV history
    nav_data: List of dicts with 'date' and 'nav' keys
    Returns volatility as percentage
    """
    if not nav_data or len(nav_data) < 2:
        return 0.0
    
    # Sort by date
    sorted_data = sorted(nav_data, key=lambda x: x.get('date', ''))
    
    # Calculate daily returns
    returns = []
    for i in range(1, len(sorted_data)):
        try:
            prev_nav = float(sorted_data[i-1].get('nav', 0))
            curr_nav = float(sorted_data[i].get('nav', 0))
            if prev_nav > 0:
                daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
                returns.append(daily_return)
        except:
            continue
    
    if len(returns) < 2:
        return 0.0
    
    # Calculate standard deviation
    # Annualize by multiplying by sqrt(252) for daily data
    std_dev = statistics.stdev(returns) if len(returns) > 1 else 0.0
    annualized_volatility = std_dev * (252 ** 0.5)
    
    return round(annualized_volatility, 2)


def calc_consistency(nav_data: List[Dict]) -> float:
    """
    Calculate consistency score (0-100) based on positive return periods
    Higher score = more consistent positive returns
    """
    if not nav_data or len(nav_data) < 2:
        return 0.0
    
    # Sort by date
    sorted_data = sorted(nav_data, key=lambda x: x.get('date', ''))
    
    # Calculate monthly returns (approximate)
    monthly_returns = []
    prev_nav = None
    prev_date = None
    
    for entry in sorted_data:
        try:
            curr_nav = float(entry.get('nav', 0))
            curr_date = datetime.strptime(entry.get('date', ''), '%d-%m-%Y')
            
            if prev_nav is not None and prev_nav > 0:
                # Check if this is approximately a month later
                if prev_date is None or (curr_date - prev_date).days >= 25:
                    monthly_return = ((curr_nav - prev_nav) / prev_nav) * 100
                    monthly_returns.append(monthly_return)
            
            prev_nav = curr_nav
            prev_date = curr_date
        except:
            continue
    
    if len(monthly_returns) == 0:
        return 0.0
    
    # Consistency = percentage of positive months
    positive_months = sum(1 for r in monthly_returns if r > 0)
    consistency_score = (positive_months / len(monthly_returns)) * 100
    
    return round(consistency_score, 2)


def calc_returns_from_price_history(price_history: List[float], period_years: float = 3.0) -> float:
    """
    Calculate returns from price history (for stocks/ETFs)
    price_history: List of closing prices
    period_years: Period for return calculation
    Returns annualized return percentage
    """
    if not price_history or len(price_history) < 2:
        return 0.0
    
    start_price = price_history[0]
    end_price = price_history[-1]
    
    if start_price == 0:
        return 0.0
    
    # Calculate CAGR
    years = period_years
    if len(price_history) > 1:
        # Approximate years based on data points (assuming daily data)
        years = min(period_years, len(price_history) / 252.0)
        if years < 0.1:
            years = period_years
    
    cagr = ((end_price / start_price) ** (1 / years) - 1) * 100
    return round(cagr, 2)


def calc_volatility_from_price_history(price_history: List[float]) -> float:
    """
    Calculate volatility from price history (for stocks/ETFs)
    price_history: List of closing prices
    Returns annualized volatility as percentage
    """
    if not price_history or len(price_history) < 2:
        return 0.0
    
    # Calculate daily returns
    returns = []
    for i in range(1, len(price_history)):
        if price_history[i-1] > 0:
            daily_return = ((price_history[i] - price_history[i-1]) / price_history[i-1]) * 100
            returns.append(daily_return)
    
    if len(returns) < 2:
        return 0.0
    
    # Calculate standard deviation and annualize
    std_dev = statistics.stdev(returns) if len(returns) > 1 else 0.0
    annualized_volatility = std_dev * (252 ** 0.5)
    
    return round(annualized_volatility, 2)


def combined_score(candidate: Dict, risk_preference: str) -> float:
    """
    Calculate combined score for a fund/stock based on risk preference
    candidate: Dict with fund/stock data including returns, volatility, consistency
    risk_preference: "Low", "Medium", or "High"
    
    Returns score (0-100), higher is better
    """
    # Extract metrics
    return_3yr = candidate.get("return_3yr", 0.0)
    return_5yr = candidate.get("return_5yr", 0.0)
    volatility = candidate.get("volatility", 0.0)
    consistency = candidate.get("consistency", 0.0)
    
    # Use 5-year return if available, else 3-year
    avg_return = return_5yr if return_5yr > 0 else return_3yr
    
    # Normalize metrics to 0-100 scale
    # Returns: assume 0-25% range maps to 0-100
    return_score = min(100, max(0, (avg_return / 25.0) * 100))
    
    # Volatility: lower is better, assume 0-50% range
    # For low risk: heavily penalize high volatility
    # For high risk: less penalty for volatility
    if risk_preference.upper() == "LOW":
        volatility_penalty = min(100, (volatility / 20.0) * 100)  # Penalize more
    elif risk_preference.upper() == "MEDIUM":
        volatility_penalty = min(100, (volatility / 30.0) * 100)
    else:  # HIGH
        volatility_penalty = min(100, (volatility / 40.0) * 100)  # Penalize less
    
    volatility_score = 100 - volatility_penalty
    
    # Consistency: already 0-100
    consistency_score = consistency
    
    # Weighted combination based on risk preference
    if risk_preference.upper() == "LOW":
        # Low risk: prioritize consistency and low volatility
        score = (return_score * 0.3) + (volatility_score * 0.4) + (consistency_score * 0.3)
    elif risk_preference.upper() == "MEDIUM":
        # Medium risk: balanced
        score = (return_score * 0.4) + (volatility_score * 0.3) + (consistency_score * 0.3)
    else:  # HIGH
        # High risk: prioritize returns
        score = (return_score * 0.5) + (volatility_score * 0.2) + (consistency_score * 0.3)
    
    return round(score, 2)

