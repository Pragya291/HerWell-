from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from ..database import get_db
from ..models import User, CycleLog
from ..schemas import CycleLogCreate, CycleLogOut, CyclePredictions
from ..auth import get_current_user
from ..utils import calculate_cycle_predictions

router = APIRouter(prefix="/api/cycle", tags=["Period Tracker"])


@router.post("/log", response_model=CycleLogOut, status_code=status.HTTP_201_CREATED)
def log_cycle_entry(
    entry: CycleLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log or update a daily cycle entry for the current user."""
    existing_log = db.query(CycleLog).filter(
        CycleLog.user_id == current_user.id,
        CycleLog.date == entry.date
    ).first()

    if existing_log:
        # Update existing log for that date
        existing_log.period_start = entry.period_start if entry.period_start is not None else existing_log.period_start
        existing_log.period_end = entry.period_end if entry.period_end is not None else existing_log.period_end
        existing_log.flow_intensity = entry.flow_intensity
        existing_log.symptoms = entry.symptoms
        existing_log.notes = entry.notes
        db.commit()
        db.refresh(existing_log)
        return existing_log

    # Create new cycle log
    new_log = CycleLog(
        user_id=current_user.id,
        date=entry.date,
        period_start=entry.period_start or False,
        period_end=entry.period_end or False,
        flow_intensity=entry.flow_intensity,
        symptoms=entry.symptoms,
        notes=entry.notes
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/logs", response_model=List[CycleLogOut])
def get_cycle_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch cycle logs for the authenticated user in date range."""
    query = db.query(CycleLog).filter(CycleLog.user_id == current_user.id)

    if start_date:
        query = query.filter(CycleLog.date >= start_date)
    if end_date:
        query = query.filter(CycleLog.date <= end_date)

    logs = query.order_by(CycleLog.date.asc()).all()
    return logs


@router.get("/predictions", response_model=CyclePredictions)
def get_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate and return cycle predictions based on user's history."""
    logs = db.query(CycleLog).filter(
        CycleLog.user_id == current_user.id
    ).order_by(CycleLog.date.asc()).all()

    predictions = calculate_cycle_predictions(logs)
    return predictions
