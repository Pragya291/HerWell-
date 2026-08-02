from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, CycleLog, MoodLog, WellnessLog
from ..schemas import ArticleOut, MythFactOut, AIHealthSummary
from ..auth import get_current_user
from ..utils import get_health_articles, get_myth_cards, generate_ai_health_summary

router = APIRouter(prefix="/api/health", tags=["Health Library & Summary"])


@router.get("/summary", response_model=AIHealthSummary)
def get_ai_health_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve AI-generated daily health summary & metrics for dashboard header."""
    cycle_logs = db.query(CycleLog).filter(CycleLog.user_id == current_user.id).all()
    mood_logs = db.query(MoodLog).filter(MoodLog.user_id == current_user.id).all()

    from datetime import date
    wellness_log = db.query(WellnessLog).filter(
        WellnessLog.user_id == current_user.id,
        WellnessLog.date == date.today()
    ).first()

    summary = generate_ai_health_summary(
        user_email=current_user.email,
        cycle_logs=cycle_logs,
        mood_logs=mood_logs,
        wellness_log=wellness_log
    )
    return summary


@router.get("/articles", response_model=List[ArticleOut])
def list_articles():
    """Retrieve all health library articles."""
    return get_health_articles()


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: int):
    """Retrieve a single health article by ID."""
    articles = get_health_articles()
    article = next((a for a in articles if a["id"] == article_id), None)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found."
        )
    return article


@router.get("/myths", response_model=List[MythFactOut])
def list_myths():
    """Retrieve all myth vs fact interactive cards."""
    return get_myth_cards()
