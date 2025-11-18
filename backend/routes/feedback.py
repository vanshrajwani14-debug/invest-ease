from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum
from uuid import uuid4
from datetime import datetime
import json
import os


class FeedbackCategory(str, Enum):
    BUG = "Bug"
    FEATURE = "Feature Request"
    USABILITY = "Usability Issue"
    GENERAL = "General Feedback"
    OTHER = "Other"


class FeedbackCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    category: FeedbackCategory
    rating: int = Field(..., ge=1, le=5)
    message: str = Field(..., min_length=5)
    contactConsent: bool = False


class FeedbackEntry(FeedbackCreate):
    id: str
    createdAt: str


class FeedbackListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[FeedbackEntry]


router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")


def load_feedback() -> List[FeedbackEntry]:
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [FeedbackEntry(**item) for item in data]
    except Exception:
        return []


def save_feedback(entries: List[FeedbackEntry]) -> None:
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump([entry.dict() for entry in entries], f, ensure_ascii=False, indent=2)


@router.post("/api/feedback", response_model=FeedbackEntry)
async def submit_feedback(payload: FeedbackCreate):
    feedback_entries = load_feedback()

    entry = FeedbackEntry(
        id=str(uuid4()),
        name=payload.name,
        email=payload.email,
        category=payload.category,
        rating=payload.rating,
        message=payload.message.strip(),
        contactConsent=payload.contactConsent,
        createdAt=datetime.utcnow().isoformat() + "Z",
    )

    feedback_entries.append(entry)

    try:
        save_feedback(feedback_entries)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to save feedback") from exc

    return entry


@router.get("/api/feedback", response_model=FeedbackListResponse)
async def list_feedback(page: int = Query(default=1, ge=1), limit: int = Query(default=10, ge=1, le=50)):
    feedback_entries = load_feedback()
    total = len(feedback_entries)
    # newest first
    sorted_entries = list(reversed(feedback_entries))
    start = (page - 1) * limit
    end = start + limit
    paginated = sorted_entries[start:end]

    return FeedbackListResponse(
        total=total,
        page=page,
        limit=limit,
        data=paginated
    )

