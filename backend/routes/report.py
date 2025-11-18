"""
Report route - generates downloadable PDF recommendation report
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from routes.ml_placeholder import get_investment_recommendation, generate_explanation
from routes.recommend import (
    format_fund_recommendations,
    format_etf_recommendations,
    format_stock_recommendations,
)

router = APIRouter()


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


