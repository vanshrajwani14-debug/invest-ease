"""
Data fetcher for mutual funds, ETFs, and stocks
Uses MFAPI (https://api.mfapi.in/mf) for mutual funds
Uses yfinance for ETFs and stocks
"""

import requests
import yfinance as yf
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache file paths
MF_LIST_CACHE = os.path.join(CACHE_DIR, "mutual_funds_list.json")
MF_DETAILS_CACHE_DIR = os.path.join(CACHE_DIR, "mf_details")
os.makedirs(MF_DETAILS_CACHE_DIR, exist_ok=True)

# Cache duration (in hours)
CACHE_DURATION_HOURS = 24


def _is_cache_valid(cache_file: str) -> bool:
    """Check if cache file exists and is still valid"""
    if not os.path.exists(cache_file):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return (datetime.now() - file_time).total_seconds() < (CACHE_DURATION_HOURS * 3600)


def _load_cache(cache_file: str) -> Optional[Dict]:
    """Load data from cache file"""
    if _is_cache_valid(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache {cache_file}: {e}")
    return None


def _save_cache(cache_file: str, data: Dict):
    """Save data to cache file"""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache {cache_file}: {e}")


def fetch_mutual_funds(limit: int = 200) -> List[Dict]:
    """
    Fetch top mutual fund schemes from MFAPI
    Returns list of fund metadata
    """
    cache_file = MF_LIST_CACHE
    
    # Try loading from cache
    cached_data = _load_cache(cache_file)
    if cached_data:
        return cached_data.get("funds", [])[:limit]
    
    try:
        # Fetch from MFAPI
        # TODO: MFAPI doesn't have a direct list endpoint, so we iterate through scheme codes
        # This approach may be slow. Consider:
        # - Using a predefined list of popular scheme codes
        # - Implementing parallel requests with rate limiting
        # - Caching scheme code ranges that are known to contain valid funds
        
        funds = []
        # Common scheme code ranges for Indian mutual funds
        # Most schemes are in 100000-200000 range
        scheme_codes = list(range(100000, 100000 + limit))
        
        print(f"Fetching mutual funds data from MFAPI...")
        successful_fetches = 0
        
        for scheme_code in scheme_codes:
            if successful_fetches >= limit:
                break
                
            try:
                url = f"https://api.mfapi.in/mf/{scheme_code}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if "meta" in data and "scheme_name" in data["meta"]:
                        fund_info = {
                            "scheme_code": scheme_code,
                            "scheme_name": data["meta"].get("scheme_name", ""),
                            "fund_house": data["meta"].get("fund_house", ""),
                            "scheme_type": data["meta"].get("scheme_type", ""),
                            "scheme_category": data["meta"].get("scheme_category", ""),
                            "nav": data["meta"].get("nav", 0.0) if "meta" in data else 0.0
                        }
                        funds.append(fund_info)
                        successful_fetches += 1
                        
                        # Rate limiting
                        time.sleep(0.1)
                        
            except Exception as e:
                # Skip invalid scheme codes
                continue
        
        # Cache the results
        _save_cache(cache_file, {"funds": funds, "fetched_at": datetime.now().isoformat()})
        
        print(f"Fetched {len(funds)} mutual funds")
        return funds
        
    except Exception as e:
        print(f"Error fetching mutual funds: {e}")
        # Return empty list on error
        return []


def fetch_scheme_details(scheme_code: int) -> Optional[Dict]:
    """
    Fetch NAV history for a specific mutual fund scheme
    Returns scheme details with historical NAV data
    """
    cache_file = os.path.join(MF_DETAILS_CACHE_DIR, f"{scheme_code}.json")
    
    # Try loading from cache
    cached_data = _load_cache(cache_file)
    if cached_data:
        return cached_data
    
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            scheme_details = {
                "scheme_code": scheme_code,
                "meta": data.get("meta", {}),
                "data": data.get("data", [])  # Historical NAV data
            }
            
            # Cache the results
            _save_cache(cache_file, scheme_details)
            
            return scheme_details
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching scheme details for {scheme_code}: {e}")
        return None


def fetch_etf_history(ticker: str, period: str = "5y") -> Optional[Dict]:
    """
    Fetch historical data for ETFs using yfinance
    ticker: ETF ticker symbol (e.g., "GOLDBEES.NS" for Gold ETF)
    period: Time period (1y, 3y, 5y, max)
    """
    cache_file = os.path.join(CACHE_DIR, f"etf_{ticker.replace('.', '_')}.json")
    
    # Try loading from cache
    cached_data = _load_cache(cache_file)
    if cached_data:
        return cached_data
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return None
        
        # Convert to dict format
        etf_data = {
            "ticker": ticker,
            "info": stock.info if hasattr(stock, 'info') else {},
            "history": {
                "dates": hist.index.strftime("%Y-%m-%d").tolist(),
                "close": hist["Close"].tolist(),
                "open": hist["Open"].tolist(),
                "high": hist["High"].tolist(),
                "low": hist["Low"].tolist(),
                "volume": hist["Volume"].tolist()
            },
            "current_price": float(hist["Close"].iloc[-1]) if len(hist) > 0 else 0.0
        }
        
        # Cache the results
        _save_cache(cache_file, etf_data)
        
        return etf_data
        
    except Exception as e:
        print(f"Error fetching ETF history for {ticker}: {e}")
        return None


def fetch_stock_history(ticker: str, period: str = "5y") -> Optional[Dict]:
    """
    Fetch historical data for stocks using yfinance
    ticker: Stock ticker symbol (e.g., "HDFCBANK.NS", "INFY.NS", "TCS.NS")
    period: Time period (1y, 3y, 5y, max)
    """
    cache_file = os.path.join(CACHE_DIR, f"stock_{ticker.replace('.', '_')}.json")
    
    # Try loading from cache
    cached_data = _load_cache(cache_file)
    if cached_data:
        return cached_data
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return None
        
        # Convert to dict format
        stock_data = {
            "ticker": ticker,
            "info": stock.info if hasattr(stock, 'info') else {},
            "history": {
                "dates": hist.index.strftime("%Y-%m-%d").tolist(),
                "close": hist["Close"].tolist(),
                "open": hist["Open"].tolist(),
                "high": hist["High"].tolist(),
                "low": hist["Low"].tolist(),
                "volume": hist["Volume"].tolist()
            },
            "current_price": float(hist["Close"].iloc[-1]) if len(hist) > 0 else 0.0
        }
        
        # Cache the results
        _save_cache(cache_file, stock_data)
        
        return stock_data
        
    except Exception as e:
        print(f"Error fetching stock history for {ticker}: {e}")
        return None


def categorize_fund(fund: Dict) -> str:
    """
    Categorize a mutual fund into equity, debt, hybrid, or gold_etf
    """
    scheme_type = fund.get("scheme_type", "").upper()
    scheme_category = fund.get("scheme_category", "").upper()
    scheme_name = fund.get("scheme_name", "").upper()
    
    # Gold ETFs
    if "GOLD" in scheme_name or "GOLDBEES" in scheme_name:
        return "gold_etf"
    
    # Equity funds
    if any(keyword in scheme_type or keyword in scheme_category for keyword in 
           ["EQUITY", "ELSS", "SMALL", "MID", "LARGE", "MULTI", "FOCUSED"]):
        return "equity"
    
    # Debt funds
    if any(keyword in scheme_type or keyword in scheme_category for keyword in 
           ["DEBT", "LIQUID", "ULTRA", "SHORT", "LONG", "GILT", "CREDIT", "CORPORATE"]):
        return "debt"
    
    # Hybrid funds
    if any(keyword in scheme_type or keyword in scheme_category for keyword in 
           ["HYBRID", "BALANCED", "ARBITRAGE", "AGGRESSIVE", "CONSERVATIVE"]):
        return "hybrid"
    
    # Default to equity if unclear
    return "equity"

