"""
Category-specific analytical reports.
Each report is informational, data-backed, and SEBI-compliant.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from enum import Enum
from statistics import mean
from typing import Any, Dict, List, Sequence, Tuple

from fastapi import APIRouter, HTTPException

from utils.scoring import (
    calc_3yr_return,
    calc_5yr_return,
    calc_consistency,
    calc_returns_from_price_history,
    calc_volatility,
    calc_volatility_from_price_history,
    combined_score,
)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "utils", "data")
MF_LIST_FILE = os.path.join(DATA_DIR, "mutual_funds_list.json")
MF_DETAILS_DIR = os.path.join(DATA_DIR, "mf_details")
BOND_FILE = os.path.join(DATA_DIR, "government_bonds.json")
DISCLAIMER_TEXT = (
    "This is not investment advice. Data shown is for educational and informational purposes."
)


class ReportCategory(str, Enum):
    STOCKS = "stocks"
    MUTUAL_FUNDS = "mutualfunds"
    BONDS = "bonds"
    GOLD = "gold"
    SIP = "sip"


@router.get("/report/{category}")
async def get_category_report(category: ReportCategory):
    """
    Return a detailed, single-category report.
    """
    builders = {
        ReportCategory.MUTUAL_FUNDS: _build_mutual_fund_report,
        ReportCategory.STOCKS: _build_stock_report,
        ReportCategory.GOLD: _build_gold_report,
        ReportCategory.BONDS: _build_bond_report,
        ReportCategory.SIP: _build_sip_report,
    }

    builder = builders.get(category)
    if not builder:
        raise HTTPException(status_code=404, detail="Unknown category")

    try:
        payload = builder()
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500, detail=f"Unable to prepare report: {str(exc)}"
        ) from exc

    payload["category"] = category.value
    payload["disclaimer"] = DISCLAIMER_TEXT
    return payload


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing data file: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_mean(values: Sequence[float]) -> float:
    clean = [v for v in values if isinstance(v, (int, float))]
    return round(mean(clean), 2) if clean else 0.0


def _nav_series(nav_rows: List[Dict[str, Any]]) -> List[Tuple[datetime, float]]:
    series: List[Tuple[datetime, float]] = []
    for row in nav_rows:
        date_str = row.get("date")
        nav_value = row.get("nav")
        if not date_str or nav_value is None:
            continue
        try:
            dt = datetime.strptime(date_str, "%d-%m-%Y")
            nav_float = float(nav_value)
        except Exception:
            continue
        series.append((dt, nav_float))
    series.sort(key=lambda item: item[0])
    return series


def _series_to_chart(series: Sequence[Tuple[datetime, float]], limit: int = 180) -> Dict[str, List[Any]]:
    trimmed = list(series)[-limit:]
    return {
        "dates": [point[0].strftime("%Y-%m-%d") for point in trimmed],
        "values": [round(point[1], 2) for point in trimmed],
    }


def _nav_return(nav_rows: List[Dict[str, Any]], years: float) -> float:
    series = _nav_series(nav_rows)
    if len(series) < 2:
        return 0.0
    end_dt, end_nav = series[-1]
    target_dt = end_dt - timedelta(days=int(years * 365.25))
    start_nav = None
    start_dt = None

    for dt, value in series:
        if dt <= target_dt:
            start_nav = value
            start_dt = dt
        else:
            break

    if start_nav is None:
        start_dt, start_nav = series[0]

    years_elapsed = max((end_dt - start_dt).days / 365.25, 0.1)
    if start_nav <= 0:
        return 0.0

    cagr = ((end_nav / start_nav) ** (1 / years_elapsed) - 1) * 100
    return round(cagr, 2)


def _consistency_from_prices(prices: Sequence[float]) -> float:
    if len(prices) < 2:
        return 0.0
    positive = 0
    total = 0
    for idx in range(1, len(prices)):
        prev_price = prices[idx - 1]
        curr_price = prices[idx]
        if prev_price <= 0:
            continue
        return_pct = ((curr_price - prev_price) / prev_price) * 100
        if return_pct > 0:
            positive += 1
        total += 1
    if total == 0:
        return 0.0
    return round((positive / total) * 100, 2)


def _volatility_to_risk_score(volatility: float, scale: float = 45.0) -> float:
    if volatility <= 0:
        return 95.0
    penalty = min(100.0, (volatility / scale) * 100.0)
    return round(max(0.0, 100.0 - penalty), 2)


def _volume_trend(volumes: Sequence[float]) -> float:
    if len(volumes) < 60:
        return 0.0
    recent = [v for v in volumes[-30:] if isinstance(v, (int, float))]
    prior = [v for v in volumes[-60:-30] if isinstance(v, (int, float))]
    if not recent or not prior:
        return 0.0
    prior_avg = mean(prior)
    if prior_avg == 0:
        return 0.0
    ratio = (mean(recent) - prior_avg) / prior_avg * 100
    return round(ratio, 2)


# ---------------------------------------------------------------------------
# Mutual fund report
# ---------------------------------------------------------------------------

EXPENSE_RATIO_FALLBACK = {
    100033: 1.92,
    100034: 1.92,
    100037: 0.8,
    100038: 0.78,
    100042: 0.35,
    100043: 0.35,
    100047: 0.42,
    100051: 0.7,
    100054: 1.1,
    100055: 0.6,
}


def _build_mutual_fund_report() -> Dict[str, Any]:
    fund_list = _load_json(MF_LIST_FILE).get("funds", [])
    available_codes = {
        int(os.path.splitext(file_name)[0])
        for file_name in os.listdir(MF_DETAILS_DIR)
        if file_name.endswith(".json")
    }

    shortlisted = [
        fund
        for fund in fund_list
        if fund.get("scheme_code") in available_codes
        and fund.get("scheme_code") in EXPENSE_RATIO_FALLBACK
    ][:30]

    scored: List[Dict[str, Any]] = []
    for fund in shortlisted:
        scheme_code = fund.get("scheme_code")
        details_path = os.path.join(MF_DETAILS_DIR, f"{scheme_code}.json")
        details = _load_json(details_path)
        nav_rows = details.get("data", [])
        if len(nav_rows) < 50:
            continue

        try:
            return_3yr = calc_3yr_return(nav_rows)
            return_5yr = calc_5yr_return(nav_rows)
            volatility = calc_volatility(nav_rows)
            consistency = calc_consistency(nav_rows)
        except Exception:
            continue

        nav_series = _nav_series(nav_rows)
        if len(nav_series) < 2:
            continue

        candidate = {
            "scheme_code": scheme_code,
            "name": details.get("meta", {}).get("scheme_name", fund.get("scheme_name")),
            "scheme_category": details.get("meta", {}).get(
                "scheme_category", fund.get("scheme_category")
            ),
            "fund_house": details.get("meta", {}).get("fund_house", fund.get("fund_house")),
            "nav": nav_series[-1][1],
            "return_1yr": _nav_return(nav_rows, 1),
            "return_3yr": return_3yr,
            "return_5yr": return_5yr,
            "volatility": volatility,
            "consistency": consistency,
            "expense_ratio": EXPENSE_RATIO_FALLBACK.get(scheme_code),
            "score": combined_score(
                {
                    "return_3yr": return_3yr,
                    "return_5yr": return_5yr,
                    "volatility": volatility,
                    "consistency": consistency,
                },
                "Medium",
            ),
            "chart_series": nav_series,
        }
        scored.append(candidate)

    if not scored:
        raise ValueError("Insufficient mutual fund data to build report")

    scored.sort(key=lambda item: item["score"], reverse=True)
    top_items = scored[:5]

    avg_vol = _safe_mean([item["volatility"] for item in scored])
    avg_return = _safe_mean(
        [
            item["return_5yr"] if item["return_5yr"] > 0 else item["return_3yr"]
            for item in scored
        ]
    )
    avg_consistency = _safe_mean([item["consistency"] for item in scored])
    avg_expense = _safe_mean([item["expense_ratio"] for item in scored])

    metrics = {
        "risk_score": _volatility_to_risk_score(avg_vol, scale=35),
        "volatility": round(avg_vol, 2),
        "avg_return_5y": round(avg_return, 2),
        "consistency_score": round(avg_consistency, 2),
        "category_avg_expense_ratio": round(avg_expense, 2),
    }

    overview = (
        "Mutual funds pool money across investors and allocate it into professionally "
        "managed portfolios. The sample below highlights diversified schemes with "
        "disclosure-driven metrics such as NAV trend, risk, and cost ratios."
    )

    chart_data = _series_to_chart(top_items[0]["chart_series"])

    factors = [
        "NAV trend over 1/3/5 year periods",
        "Annualized volatility and downside capture",
        "Consistency score (share of positive months)",
        "Expense ratio compared with category peers",
    ]

    formatted_top = [
        {
            "name": item["name"],
            "scheme_code": item["scheme_code"],
            "score": item["score"],
            "1y_return": item["return_1yr"],
            "3y_return": item["return_3yr"],
            "5y_return": item["return_5yr"],
            "nav": round(item["nav"], 2),
            "extra_metrics": {
                "expense_ratio": item["expense_ratio"],
                "consistency": item["consistency"],
                "category": item["scheme_category"],
            },
        }
        for item in top_items
    ]

    return {
        "overview": overview,
        "metrics": metrics,
        "chart_data": chart_data,
        "top_items": formatted_top,
        "factors_analyzed": factors,
    }


# ---------------------------------------------------------------------------
# Stocks report
# ---------------------------------------------------------------------------


def _build_stock_report() -> Dict[str, Any]:
    stock_files = [
        os.path.join(DATA_DIR, file_name)
        for file_name in os.listdir(DATA_DIR)
        if file_name.startswith("stock_") and file_name.endswith(".json")
    ]

    if not stock_files:
        raise ValueError("No stock data available")

    scored: List[Dict[str, Any]] = []
    for path in stock_files:
        data = _load_json(path)
        history = data.get("history", {})
        prices = history.get("close", [])
        volumes = history.get("volume", [])
        if len(prices) < 30:
            continue

        returns_3yr = calc_returns_from_price_history(prices[-756:], 3.0)
        returns_5yr = calc_returns_from_price_history(prices, 5.0)
        volatility = calc_volatility_from_price_history(prices)
        consistency = _consistency_from_prices(prices)
        info = data.get("info", {})
        beta = info.get("beta")

        candidate = {
            "ticker": data.get("ticker"),
            "name": info.get("longName") or info.get("shortName") or data.get("ticker"),
            "current_price": data.get("current_price"),
            "return_3yr": returns_3yr,
            "return_5yr": returns_5yr,
            "volatility": volatility,
            "consistency": consistency,
            "beta": beta,
            "volume_trend": _volume_trend(volumes),
            "score": combined_score(
                {
                    "return_3yr": returns_3yr,
                    "return_5yr": returns_5yr,
                    "volatility": volatility,
                    "consistency": consistency,
                },
                "Medium",
            ),
            "chart_series": list(
                zip(
                    [
                        datetime.strptime(date_str, "%Y-%m-%d")
                        for date_str in history.get("dates", []) if date_str
                    ],
                    [float(price) for price in prices],
                )
            ),
        }
        scored.append(candidate)

    if not scored:
        raise ValueError("Unable to compute stock metrics")

    scored.sort(key=lambda item: item["score"], reverse=True)
    top_items = scored[:4]

    avg_vol = _safe_mean([item["volatility"] for item in scored])
    avg_return = _safe_mean(
        [
            item["return_5yr"] if item["return_5yr"] > 0 else item["return_3yr"]
            for item in scored
        ]
    )
    avg_beta = _safe_mean([item["beta"] for item in scored if item["beta"] is not None])

    metrics = {
        "risk_score": _volatility_to_risk_score(avg_vol, scale=40),
        "volatility": round(avg_vol, 2),
        "avg_return_5y": round(avg_return, 2),
        "avg_beta_vs_nifty": round(avg_beta, 2) if avg_beta else 0.0,
    }

    overview = (
        "Large-cap Indian equities exhibit relatively stable earnings visibility. "
        "Scores below reflect historical price strength, volatility, beta, and liquidity trends."
    )

    chart_data = _series_to_chart(top_items[0]["chart_series"])
    factors = [
        "3Y and 5Y price CAGR vs. benchmark",
        "Historical volatility and beta to Nifty 50",
        "Rolling positive return ratio (consistency)",
        "Volume momentum over the last 6 months",
    ]

    formatted_top = [
        {
            "name": item["name"],
            "ticker": item["ticker"],
            "score": item["score"],
            "1y_return": None,
            "3y_return": item["return_3yr"],
            "5y_return": item["return_5yr"],
            "nav": item["current_price"],
            "extra_metrics": {
                "beta": item["beta"],
                "volatility": item["volatility"],
                "volume_trend_pct": item["volume_trend"],
            },
        }
        for item in top_items
    ]

    return {
        "overview": overview,
        "metrics": metrics,
        "chart_data": chart_data,
        "top_items": formatted_top,
        "factors_analyzed": factors,
    }


# ---------------------------------------------------------------------------
# Gold report
# ---------------------------------------------------------------------------


def _build_gold_report() -> Dict[str, Any]:
    etf_files = [
        os.path.join(DATA_DIR, file_name)
        for file_name in os.listdir(DATA_DIR)
        if file_name.startswith("etf_") and file_name.endswith(".json")
    ]
    if not etf_files:
        raise ValueError("No gold ETF data available")

    scored: List[Dict[str, Any]] = []
    for path in etf_files:
        data = _load_json(path)
        history = data.get("history", {})
        prices = history.get("close", [])
        if len(prices) < 30:
            continue
        returns_3yr = calc_returns_from_price_history(prices[-756:], 3.0)
        returns_5yr = calc_returns_from_price_history(prices, 5.0)
        volatility = calc_volatility_from_price_history(prices)
        consistency = _consistency_from_prices(prices)

        candidate = {
            "ticker": data.get("ticker"),
            "name": data.get("info", {}).get("longName") or data.get("ticker"),
            "return_3yr": returns_3yr,
            "return_5yr": returns_5yr,
            "volatility": volatility,
            "consistency": consistency,
            "score": combined_score(
                {
                    "return_3yr": returns_3yr,
                    "return_5yr": returns_5yr,
                    "volatility": volatility,
                    "consistency": consistency,
                },
                "Medium",
            ),
            "chart_series": list(
                zip(
                    [
                        datetime.strptime(date_str, "%Y-%m-%d")
                        for date_str in history.get("dates", []) if date_str
                    ],
                    [float(price) for price in prices],
                )
            ),
        }
        scored.append(candidate)

    if not scored:
        raise ValueError("Gold ETF scoring failed")

    scored.sort(key=lambda item: item["score"], reverse=True)
    top_items = scored[:3]

    avg_vol = _safe_mean([item["volatility"] for item in scored])
    avg_return = _safe_mean(
        [
            item["return_5yr"] if item["return_5yr"] > 0 else item["return_3yr"]
            for item in scored
        ]
    )

    metrics = {
        "risk_score": _volatility_to_risk_score(avg_vol, scale=30),
        "volatility": round(avg_vol, 2),
        "avg_return_5y": round(avg_return, 2),
    }

    overview = (
        "Gold ETFs listed on NSE provide transparent exposure to domestic gold prices. "
        "Returns shown reflect INR price movements without leverage."
    )
    chart_data = _series_to_chart(top_items[0]["chart_series"])
    factors = [
        "Price momentum vs. 3Y/5Y averages",
        "Volatility relative to other commodities",
        "Consistency of monthly gains",
        "Tracking error to landed gold prices",
    ]

    formatted_top = [
        {
            "name": item["name"],
            "ticker": item["ticker"],
            "score": item["score"],
            "1y_return": None,
            "3y_return": item["return_3yr"],
            "5y_return": item["return_5yr"],
            "nav": None,
            "extra_metrics": {
                "volatility": item["volatility"],
                "consistency": item["consistency"],
            },
        }
        for item in top_items
    ]

    return {
        "overview": overview,
        "metrics": metrics,
        "chart_data": chart_data,
        "top_items": formatted_top,
        "factors_analyzed": factors,
    }


# ---------------------------------------------------------------------------
# Bond report
# ---------------------------------------------------------------------------


def _build_bond_report() -> Dict[str, Any]:
    bond_data = _load_json(BOND_FILE)
    bonds = bond_data.get("bonds", [])
    if not bonds:
        raise ValueError("Bond dataset is empty")

    def score_bond(bond: Dict[str, Any]) -> float:
        yield_score = min(100.0, max(0.0, (bond.get("yield", 0) - 6.5) / 1.5 * 100))
        duration_score = 100.0 - min(100.0, (bond.get("duration", 0) / 30.0) * 100.0)
        vol_score = 100.0 - min(100.0, (bond.get("volatility", 0) / 3.0) * 100.0)
        return round((yield_score * 0.45) + (duration_score * 0.25) + (vol_score * 0.3), 2)

    formatted = []
    for bond in bonds:
        history_dates = bond.get("history", {}).get("dates", [])
        history_yields = bond.get("history", {}).get("yields", [])
        series = (
            list(
                zip(
                    [
                        datetime.strptime(date_str, "%Y-%m-%d")
                        for date_str in history_dates if date_str
                    ],
                    [float(yld) for yld in history_yields],
                )
            )
            if history_dates and history_yields
            else []
        )
        formatted.append(
            {
                "name": bond.get("name"),
                "isin": bond.get("isin"),
                "score": score_bond(bond),
                "1y_return": None,
                "5y_return": None,
                "nav": bond.get("yield"),
                "extra_metrics": {
                    "yield": bond.get("yield"),
                    "duration": bond.get("duration"),
                    "credit_rating": bond.get("credit_rating"),
                    "volatility": bond.get("volatility"),
                },
                "chart_series": series,
            }
        )

    formatted.sort(key=lambda entry: entry["score"], reverse=True)
    top_items = formatted[:3]

    avg_yield = _safe_mean([item["extra_metrics"]["yield"] for item in formatted])
    avg_duration = _safe_mean([item["extra_metrics"]["duration"] for item in formatted])
    avg_volatility = _safe_mean([item["extra_metrics"]["volatility"] for item in formatted])

    metrics = {
        "risk_score": _volatility_to_risk_score(avg_volatility, scale=15),
        "avg_yield": round(avg_yield, 2),
        "avg_duration": round(avg_duration, 2),
        "volatility": round(avg_volatility, 2),
    }

    overview = (
        "Government securities (G-Secs) carry sovereign backing. The snapshot combines "
        "on-the-run maturities across the curve with observed yields and duration risk."
    )

    chart_data = (
        _series_to_chart(top_items[0]["chart_series"])
        if top_items[0]["chart_series"]
        else {"dates": [], "values": []}
    )
    factors = [
        "Yield-to-maturity versus benchmark curve",
        "Modified duration for interest-rate sensitivity",
        "Observed price/yield volatility",
        "Credit quality (all instruments shown are sovereign rated)",
    ]

    for item in top_items:
        item.pop("chart_series", None)

    return {
        "overview": overview,
        "metrics": metrics,
        "chart_data": chart_data,
        "top_items": top_items,
        "factors_analyzed": factors,
    }


# ---------------------------------------------------------------------------
# SIP report
# ---------------------------------------------------------------------------


def _build_sip_report() -> Dict[str, Any]:
    monthly_investment = 10000  # ₹10,000 monthly example
    annual_return = 0.12  # 12% annualized assumption
    durations = {"1_year": 1, "3_year": 3, "5_year": 5}

    projections = {
        label: round(_sip_future_value(monthly_investment, annual_return, years), 2)
        for label, years in durations.items()
    }

    labels = []
    values = []
    invested = []
    months = durations["5_year"] * 12
    monthly_rate = annual_return / 12
    for month in range(months + 1):
        year_label = f"{month // 12}Y" if month % 12 == 0 else None
        if month == 0 or month % 6 == 0 or month == months:
            labels.append(f"Month {month}")
            invested.append(round(monthly_investment * month, 2))
            if monthly_rate > 0 and month > 0:
                value = monthly_investment * (((1 + monthly_rate) ** month - 1) / monthly_rate) * (
                    1 + monthly_rate
                )
            else:
                value = monthly_investment * month
            values.append(round(value, 2))

    metrics = {
        "monthly_investment": monthly_investment,
        "assumed_return": round(annual_return * 100, 2),
        "projection_values": projections,
        "risk_score": 68.0,  # SIPs smooth entry points but remain market-linked
    }

    overview = (
        "Systematic Investment Plans (SIPs) average out market volatility by deploying a fixed "
        "amount every month. The projections below use the standard future value formula "
        "without tailoring to any individual investor."
    )

    top_items = [
        {
            "name": f"{label.replace('_', ' ').title()} projection",
            "score": None,
            "1y_return": None,
            "5y_return": None,
            "nav": projections[label],
            "extra_metrics": {
                "duration_years": years,
                "total_invested": monthly_investment * years * 12,
                "future_value": projections[label],
            },
        }
        for label, years in durations.items()
    ]

    factors = [
        "FV = P × [((1+r)^n - 1) / r] × (1 + r) with monthly compounding",
        "Scenario analysis at 1/3/5 year tenures",
        "Assumed return of 12% representative of diversified equity mutual funds",
        "No personalization or goal-based allocation is applied",
    ]

    return {
        "overview": overview,
        "metrics": metrics,
        "chart_data": {"dates": labels, "values": values, "invested": invested},
        "top_items": top_items,
        "factors_analyzed": factors,
    }


def _sip_future_value(monthly_amount: float, annual_rate: float, years: int) -> float:
    monthly_rate = annual_rate / 12
    months = int(years * 12)
    if monthly_rate <= 0:
        return monthly_amount * months
    return monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)

