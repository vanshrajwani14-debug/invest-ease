"""
Recommendation route - generates investment recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from routes.ml_placeholder import get_investment_recommendation, generate_explanation
from routes.report import ReportCategory, build_structured_report

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
    report_type: Optional[str] = "full"
    investment_type: Optional[str] = None


EDUCATIONAL_DISCLAIMER = (
    "These are educational insights based on general risk categories, not financial advice."
)

CATEGORY_LABELS = {
    "mutualfunds": "Mutual Funds",
    "stocks": "Stocks",
    "bonds": "Government Bonds",
    "gold": "Gold",
    "sip": "Systematic Investment Plan",
}

SINGLE_REPORT_LIBRARY = {
    "mutualfunds": {
        "label": "Mutual Funds",
        "overview": (
            "Mutual funds pool investor capital into professionally managed portfolios "
            "across equity, debt, or hybrid mandates. They follow SEBI-mandated disclosure "
            "rules and provide diversification even with smaller ticket sizes."
        ),
        "expected_return_range": "9% – 12% annualized over a 5+ year horizon",
        "examples": [
            "Large-cap diversified equity fund",
            "Balanced hybrid allocation fund",
            "Index-tracking passive fund",
        ],
        "pros": [
            "Built-in diversification and liquidity",
            "Professional fund management with daily NAV disclosure",
            "Accessible via SIPs or lumpsum with low entry amounts",
        ],
        "cons": [
            "Market volatility can impact NAV in the short term",
            "Expense ratios reduce net returns",
            "Some categories have exit loads or lock-in periods",
        ],
        "risk_alignment": {
            "LOW": "Opting for large-cap or balanced funds can suit conservative investors seeking steady growth.",
            "MEDIUM": "Multi-cap and hybrid funds align well with balanced risk profiles by mixing equity and debt.",
            "HIGH": "Aggressive equity and sector funds can match higher risk appetites but require longer horizons.",
        },
        "allocation_guidance": {
            "LOW": "20% – 35% of the investable portfolio",
            "MEDIUM": "35% – 55% of the investable portfolio",
            "HIGH": "50% – 70% of the investable portfolio",
        },
    },
    "stocks": {
        "label": "Stocks",
        "overview": (
            "Direct equity investing gives you fractional ownership in listed companies. "
            "Returns depend on earnings growth, sector cycles, and valuation re-ratings."
        ),
        "expected_return_range": "11% – 15% annualized across a full market cycle",
        "examples": [
            "Large-cap banking leader",
            "Top-tier IT services company",
            "Consumer staple blue-chip",
        ],
        "pros": [
            "Highest long-term growth potential among listed assets",
            "Participates directly in corporate earnings and dividends",
            "High liquidity on NSE/BSE for frontline names",
        ],
        "cons": [
            "High day-to-day volatility and drawdowns",
            "Requires continuous tracking of company fundamentals",
            "Concentrated bets carry company-specific risk",
        ],
        "risk_alignment": {
            "LOW": "Pure equity exposure can feel aggressive; consider staggered allocation or ETFs.",
            "MEDIUM": "Core large-cap holdings align with moderate risk tolerance if horizon exceeds 5 years.",
            "HIGH": "Suited for high-risk investors comfortable with volatility in pursuit of compounding.",
        },
        "allocation_guidance": {
            "LOW": "5% – 15% with focus on large caps",
            "MEDIUM": "15% – 30% blended across market caps",
            "HIGH": "30% – 50% with tactical satellite positions",
        },
    },
    "bonds": {
        "label": "Government Bonds",
        "overview": (
            "Government securities (G-Secs) are sovereign-backed instruments that pay periodic "
            "coupons and return principal at maturity. Price movements primarily track interest-rate expectations."
        ),
        "expected_return_range": "6.8% – 7.3% yield to maturity based on current curve",
        "examples": [
            "10-year benchmark central government bond",
            "State development loans",
            "Treasury bill ladder for short tenors",
        ],
        "pros": [
            "Sovereign credit quality with minimal default risk",
            "Predictable coupon cash flows",
            "Useful for laddering liabilities or income needs",
        ],
        "cons": [
            "Bond prices fall when interest rates rise",
            "Long durations lock capital for several years",
            "Lower return ceiling versus equity-linked assets",
        ],
        "risk_alignment": {
            "LOW": "Matches low-risk profiles by prioritizing capital safety and stable income.",
            "MEDIUM": "Acts as a stabilizer and liquidity reserve alongside growth assets.",
            "HIGH": "Provides ballast to offset equity volatility but caps upside.",
        },
        "allocation_guidance": {
            "LOW": "35% – 60% of the portfolio",
            "MEDIUM": "20% – 35% for stability",
            "HIGH": "10% – 20% primarily for diversification",
        },
    },
    "gold": {
        "label": "Gold",
        "overview": (
            "Gold is a real asset hedge that historically offsets inflation spikes and currency weakness. "
            "Indian investors typically access it via Gold ETFs or sovereign gold bonds."
        ),
        "expected_return_range": "6% – 9% CAGR (INR terms) over long periods",
        "examples": [
            "Gold ETF units backed by physical bullion",
            "Sovereign Gold Bonds (SGBs)",
            "Multi-asset funds with gold allocation",
        ],
        "pros": [
            "Acts as a hedge during economic stress",
            "High liquidity through exchange-traded units",
            "Diversifies equity-heavy portfolios",
        ],
        "cons": [
            "No intrinsic cash flows",
            "Can underperform equities for extended phases",
            "Prices influenced by currency and global flows",
        ],
        "risk_alignment": {
            "LOW": "Provides comfort through stability and inflation hedging.",
            "MEDIUM": "Supports diversification when paired with equity and debt.",
            "HIGH": "Serves as a tactical hedge against drawdowns without impacting liquidity.",
        },
        "allocation_guidance": {
            "LOW": "5% – 10% allocation",
            "MEDIUM": "5% – 12% allocation",
            "HIGH": "5% – 15% allocation",
        },
    },
    "sip": {
        "label": "Systematic Investment Plan (SIP)",
        "overview": (
            "SIPs automate periodic investing (usually monthly) into mutual funds. "
            "They enforce discipline, average purchase cost, and align well with salaried cash flows."
        ),
        "expected_return_range": "10% – 12% CAGR assumption for diversified equity SIPs",
        "examples": [
            "Monthly SIP in diversified equity fund",
            "Goal-based SIP ladder (education, retirement)",
            "Step-up SIP that increases contributions annually",
        ],
        "pros": [
            "Rupee-cost averaging reduces timing risk",
            "Flexible contribution amounts and frequencies",
            "Ideal for long-term goal planning",
        ],
        "cons": [
            "Still exposed to market risk; NAVs can fall",
            "Requires commitment across market cycles",
            "Stopping early reduces compounding benefits",
        ],
        "risk_alignment": {
            "LOW": "SIPs in balanced funds help ease into markets gradually.",
            "MEDIUM": "Supports disciplined participation in equities without large lump sums.",
            "HIGH": "Allows aggressive equity exposure while smoothing entry points.",
        },
        "allocation_guidance": {
            "LOW": "Use SIPs for 15% – 25% of deployable surplus",
            "MEDIUM": "Channel 25% – 40% of surplus via SIPs",
            "HIGH": "40% – 60% via SIPs to harness compounding",
        },
    },
}


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
        
        report_type = (user_details.report_type or "full").lower()
        if report_type not in {"full", "single"}:
            raise HTTPException(
                status_code=400,
                detail="report_type must be either 'full' or 'single'"
            )

        investment_type = (user_details.investment_type or "").lower() or None
        if report_type == "single":
            if not investment_type:
                raise HTTPException(
                    status_code=400,
                    detail="investment_type is required when report_type is 'single'"
                )
            if investment_type not in SINGLE_REPORT_LIBRARY:
                raise HTTPException(
                    status_code=400,
                    detail="investment_type must be one of: stocks, mutualfunds, bonds, gold, sip"
                )
            try:
                _ = ReportCategory(investment_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported investment category for detailed report"
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

        payload: Dict[str, Any] = {
            "status": "success",
            "report_type": report_type,
            "recommendations": response
        }

        if report_type == "single" and investment_type:
            category_enum = ReportCategory(investment_type)
            structured_report = build_structured_report(category_enum)
            insights = build_single_investment_summary(
                investment_type,
                user_details.risk_preference
            )
            insights["analytics"] = structured_report
            payload["single_report"] = insights
            payload["selected_category"] = investment_type
        
        return payload
        
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


def build_single_investment_summary(category_key: str, risk_preference: str) -> Dict[str, Any]:
    template = SINGLE_REPORT_LIBRARY.get(category_key)
    if not template:
        raise ValueError(f"Unsupported category for single report: {category_key}")
    
    risk_key = (risk_preference or "Medium").upper()
    if risk_key not in {"LOW", "MEDIUM", "HIGH"}:
        risk_key = "MEDIUM"
    
    insights = {
        "overview": template["overview"],
        "risk_alignment": template["risk_alignment"].get(
            risk_key,
            template["risk_alignment"].get("MEDIUM")
        ),
        "expected_return_range": template["expected_return_range"],
        "examples": template["examples"],
        "pros": template["pros"],
        "cons": template["cons"],
        "suggested_allocation": template["allocation_guidance"].get(
            risk_key,
            template["allocation_guidance"].get("MEDIUM")
        ),
        "disclaimer": EDUCATIONAL_DISCLAIMER,
    }
    
    return {
        "category": category_key,
        "label": CATEGORY_LABELS.get(category_key, category_key.title()),
        "insights": insights
    }
