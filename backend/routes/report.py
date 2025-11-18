"""
Category-specific analytical reports and downloadable PDF summaries.
All outputs remain informational, data-backed, and SEBI-compliant.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from statistics import mean
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from routes.ml_placeholder import get_investment_recommendation, generate_explanation
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
    try:
        payload = build_structured_report(category)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500, detail=f"Unable to prepare report: {str(exc)}"
        ) from exc

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


CATEGORY_BUILDERS: Dict[ReportCategory, Callable[[], Dict[str, Any]]] = {
    ReportCategory.MUTUAL_FUNDS: _build_mutual_fund_report,
    ReportCategory.STOCKS: _build_stock_report,
    ReportCategory.GOLD: _build_gold_report,
    ReportCategory.BONDS: _build_bond_report,
    ReportCategory.SIP: _build_sip_report,
}


def build_structured_report(category: ReportCategory) -> Dict[str, Any]:
    builder = CATEGORY_BUILDERS.get(category)
    if not builder:
        raise ValueError(f"Unsupported report category: {category}")
    payload = builder()
    payload["category"] = category.value
    payload["disclaimer"] = DISCLAIMER_TEXT
    return payload


@router.get("/api/recommend/report")
async def generate_recommendation_report(
    age: int = Query(..., ge=18, le=100),
    investment_amount: float = Query(..., gt=0),
    risk_preference: str = Query(..., min_length=3),
    monthly_income: Optional[float] = Query(None),
    income_param: Optional[float] = Query(None, alias="income"),
    savings: Optional[float] = Query(None),
    time_horizon: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    financial_goals: Optional[str] = Query(None),
    goals_param: Optional[str] = Query(None, alias="goals"),
    monthly_expenses: Optional[float] = Query(None),
    expenses_param: Optional[float] = Query(None, alias="expenses"),
):
    """
    Generate a PDF report for the investment recommendations.
    """
    normalized_risk = risk_preference.capitalize()
    if normalized_risk not in {"Low", "Medium", "High"}:
        raise HTTPException(
            status_code=400,
            detail="risk_preference must be one of: Low, Medium, High",
        )

    user_data = {
        "age": age,
        "investment_amount": investment_amount,
        "risk_preference": normalized_risk,
        "monthly_income": monthly_income if monthly_income is not None else income_param,
        "savings": savings,
        "time_horizon": time_horizon,
        "experience_level": experience_level,
        "financial_goals": financial_goals or goals_param,
        "monthly_expenses": monthly_expenses
        if monthly_expenses is not None
        else expenses_param,
    }

    try:
        raw_recommendations = get_investment_recommendation(user_data)
        explanation = generate_explanation(raw_recommendations, user_data)

        formatted_recommendations = {
            "equity": format_fund_recommendations(raw_recommendations.get("equity", [])),
            "debt": format_fund_recommendations(raw_recommendations.get("debt", [])),
            "hybrid": format_fund_recommendations(raw_recommendations.get("hybrid", [])),
            "gold": format_etf_recommendations(raw_recommendations.get("gold", [])),
            "stocks": format_stock_recommendations(raw_recommendations.get("stocks", [])),
        }

        pdf_buffer = _build_pdf_report(
            user_data=user_data,
            recommendations=formatted_recommendations,
            explanation=explanation,
        )

        headers = {
            "Content-Disposition": 'attachment; filename="recommendation_report.pdf"'
        }
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate report: {exc}",
        ) from exc


def format_fund_recommendations(funds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
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
            "score": fund.get("score", 0.0),
        })
    return formatted


def format_etf_recommendations(etfs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
    for etf in etfs:
        formatted.append({
            "name": etf.get("name", ""),
            "ticker": etf.get("ticker", ""),
            "current_price": etf.get("current_price", 0.0),
            "return_3yr": etf.get("return_3yr", 0.0),
            "return_5yr": etf.get("return_5yr", 0.0),
            "volatility": etf.get("volatility", 0.0),
            "consistency": etf.get("consistency", 0.0),
            "score": etf.get("score", 0.0),
        })
    return formatted


def format_stock_recommendations(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
    for stock in stocks:
        formatted.append({
            "name": stock.get("name", ""),
            "ticker": stock.get("ticker", ""),
            "current_price": stock.get("current_price", 0.0),
            "return_3yr": stock.get("return_3yr", 0.0),
            "return_5yr": stock.get("return_5yr", 0.0),
            "volatility": stock.get("volatility", 0.0),
            "consistency": stock.get("consistency", 0.0),
            "score": stock.get("score", 0.0),
        })
    return formatted


def _build_pdf_report(
    user_data: Dict[str, Any],
    recommendations: Dict[str, List[Dict[str, Any]]],
    explanation: str,
) -> BytesIO:
    """
    Generate the PDF report using ReportLab.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 0.8 * inch
    usable_width = width - (2 * margin)
    y_position = height - margin

    def ensure_space(current_y: float, needed: float) -> float:
        nonlocal pdf
        if current_y - needed <= margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            current_y = height - margin
        return current_y

    def draw_wrapped_text(
        text: str, font: str, size: int, line_height: int, y: float
    ) -> float:
        pdf.setFont(font, size)
        lines = _wrap_text(text, usable_width, pdf, size, font)
        for line in lines:
            y = ensure_space(y, line_height)
            pdf.drawString(margin, y, line)
            y -= line_height
        return y

    # Title
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.drawString(margin, y_position, "Investment Recommendation Report")
    y_position -= 24

    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.gray)
    pdf.drawString(margin, y_position, f"Generated on {datetime.now().strftime('%d %B %Y, %H:%M')}")
    y_position -= 30

    # User summary
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y_position, "User Profile Summary")
    y_position -= 18

    summary_lines = _build_user_summary(user_data)
    for label, value in summary_lines:
        y_position = ensure_space(y_position, 14)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, y_position, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(margin + 120, y_position, value)
        y_position -= 14

    y_position -= 6
    pdf.line(margin, y_position, width - margin, y_position)
    y_position -= 20

    # Recommendations
    section_titles = {
        "equity": "Equity Funds",
        "debt": "Debt Funds",
        "hybrid": "Hybrid Funds",
        "gold": "Gold ETFs",
        "stocks": "Stocks",
    }

    for key, title in section_titles.items():
        assets = recommendations.get(key, [])
        if not assets:
            continue

        y_position = ensure_space(y_position, 20)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.drawString(margin, y_position, title)
        y_position -= 16

        for asset in assets:
            y_position = _draw_asset_block(
                pdf=pdf,
                asset=asset,
                margin=margin,
                usable_width=usable_width,
                y_position=y_position,
                page_height=height,
            )

        y_position -= 8

    # Explanation
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.HexColor("#111827"))
    y_position = ensure_space(y_position, 20)
    pdf.drawString(margin, y_position, "Strategy Explanation")
    y_position -= 18

    y_position = draw_wrapped_text(
        explanation or "An explanation was not provided by the engine.",
        font="Helvetica",
        size=10,
        line_height=14,
        y=y_position,
    )

    # Disclaimer in footer
    footer_text = (
        "This is not investment advice. The results shown are automated, data-based "
        "evaluations. Please consult a SEBI-registered investment advisor before making "
        "investment decisions."
    )
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.HexColor("#6B7280"))
    y_position = ensure_space(y_position, 40)
    lines = _wrap_text(footer_text, usable_width, pdf, 9, "Helvetica-Oblique")
    for line in lines:
        pdf.drawString(margin, y_position, line)
        y_position -= 12

    pdf.save()
    buffer.seek(0)
    return buffer


def _draw_asset_block(
    pdf: canvas.Canvas,
    asset: Dict[str, Any],
    margin: float,
    usable_width: float,
    y_position: float,
    page_height: float,
) -> float:
    """
    Render a single asset entry block in the PDF.
    """
    line_height = 12

    def ensure_block_space(current_y: float, required: float) -> float:
        if current_y - required <= margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            return page_height - margin
        return current_y

    y_position = ensure_block_space(y_position, 60)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.drawString(margin, y_position, asset.get("name") or asset.get("scheme_name", ""))
    y_position -= line_height

    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.HexColor("#1F2937"))
    returns_text = "Returns (3Y / 5Y): "
    ret_3 = _format_percentage(asset.get("return_3yr"))
    ret_5 = _format_percentage(asset.get("return_5yr"))
    pdf.drawString(margin, y_position, f"{returns_text}{ret_3} / {ret_5}")
    y_position -= line_height

    volatility = _format_percentage(asset.get("volatility"))
    consistency = _format_percentage(asset.get("consistency"))
    score = (
        f"{asset.get('score'):.2f}"
        if isinstance(asset.get("score"), (int, float))
        else str(asset.get("score") or "N/A")
    )
    pdf.drawString(
        margin,
        y_position,
        f"Volatility: {volatility}   Consistency: {consistency}   Score: {score}",
    )
    y_position -= line_height

    pdf.setFillColor(colors.HexColor("#D1D5DB"))
    pdf.rect(margin, y_position, usable_width, 0.5, fill=1, stroke=0)
    y_position -= 6

    return y_position


def _wrap_text(
    text: str, usable_width: float, pdf: canvas.Canvas, font_size: int, font_name: str
) -> List[str]:
    """
    Wrap text manually based on ReportLab's string width.
    """
    if not text:
        return []

    words = text.split()
    lines: List[str] = []
    current_line: List[str] = []

    for word in words:
        tentative = " ".join(current_line + [word])
        if pdf.stringWidth(tentative, font_name, font_size) <= usable_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def _build_user_summary(user_data: Dict[str, Any]) -> List[List[str]]:
    """
    Prepare key-value lines summarizing user input.
    """
    summary = [
        ["Age", f"{user_data['age']} years"],
        [
            "Investment Amount",
            f"₹{user_data['investment_amount']:,.0f}",
        ],
        ["Risk Preference", user_data["risk_preference"]],
    ]

    optional_fields = {
        "Monthly Income": user_data.get("monthly_income"),
        "Savings": user_data.get("savings"),
        "Time Horizon": user_data.get("time_horizon"),
        "Experience Level": user_data.get("experience_level"),
        "Financial Goals": user_data.get("financial_goals"),
        "Monthly Expenses": user_data.get("monthly_expenses"),
    }

    for label, value in optional_fields.items():
        if value is None or value == "":
            continue
        if isinstance(value, (int, float)):
            summary.append([label, f"₹{value:,.0f}"])
        else:
            summary.append([label, str(value)])

    return summary


def _format_percentage(value: Optional[Any]) -> str:
    """
    Format percentage values safely.
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)
