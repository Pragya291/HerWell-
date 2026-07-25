from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from ..database import get_db
from ..models import User, MoodLog
from ..schemas import MoodLogCreate, MoodLogOut, MoodTrendsResponse
from ..auth import get_current_user
from ..utils import calculate_mood_trends

router = APIRouter(prefix="/api/mood", tags=["Mental Wellness"])


@router.post("/log", response_model=MoodLogOut, status_code=status.HTTP_201_CREATED)
def log_mood_entry(
    entry: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log or update daily mood and journal entry."""
    existing_log = db.query(MoodLog).filter(
        MoodLog.user_id == current_user.id,
        MoodLog.date == entry.date
    ).first()

    if existing_log:
        existing_log.mood = entry.mood
        existing_log.journal = entry.journal
        db.commit()
        db.refresh(existing_log)
        return existing_log

    new_log = MoodLog(
        user_id=current_user.id,
        date=entry.date,
        mood=entry.mood,
        journal=entry.journal
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/logs", response_model=List[MoodLogOut])
def get_mood_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch mood history within optional date range."""
    query = db.query(MoodLog).filter(MoodLog.user_id == current_user.id)

    if start_date:
        query = query.filter(MoodLog.date >= start_date)
    if end_date:
        query = query.filter(MoodLog.date <= end_date)

    logs = query.order_by(MoodLog.date.asc()).all()
    return logs


@router.get("/trends", response_model=MoodTrendsResponse)
def get_mood_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregate weekly average mood for the past 4 weeks."""
    logs = db.query(MoodLog).filter(MoodLog.user_id == current_user.id).all()
    trends = calculate_mood_trends(logs)
    return trends
