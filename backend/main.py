from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

# Import routers
from routes import recommend, compare, sip, feedback

app = FastAPI(title="InvestEase API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(recommend.router)
app.include_router(compare.router)
app.include_router(sip.router)
app.include_router(feedback.router)

# Pydantic models (kept for backward compatibility if needed)
class UserDetails(BaseModel):
    age: int
    investment_amount: float
    risk_preference: str
    monthly_income: Optional[float] = None
    savings: Optional[float] = None
    time_horizon: Optional[str] = None
    investment_experience: Optional[str] = None
    financial_goals: Optional[str] = None
    monthly_expenses: Optional[float] = None

class SIPCalculation(BaseModel):
    monthly_amount: float
    expected_return: float
    time_period: float

# Root route
@app.get("/")
async def root():
    return {"message": "InvestEase API is running"}

# PDF report route (placeholder - not modified per requirements)
@app.get("/api/report/pdf")
async def generate_pdf_report():
    """
    TODO: Implement PDF generation using reportlab or similar
    Currently returns placeholder response
    """
    return {
        "status": "success",
        "message": "PDF generation feature coming soon",
        "download_url": None
    }

# ML prediction route (placeholder - not modified per requirements)
@app.post("/api/ml/predict")
async def ml_prediction(user_details: UserDetails):
    """
    TODO: Implement ML model for investment prediction
    This would include risk assessment, return prediction, etc.
    """
    return {
        "status": "success",
        "message": "ML prediction feature coming soon",
        "prediction": None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
