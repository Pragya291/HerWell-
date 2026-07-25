from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from ..database import get_db
from ..models import User, FitnessLog, CycleLog
from ..schemas import FitnessLogCreate, FitnessLogOut, FitnessRecommendationsResponse
from ..auth import get_current_user
from ..utils import calculate_cycle_predictions, get_phase_workout_recommendations

router = APIRouter(prefix="/api/fitness", tags=["Fitness Guidance"])


@router.post("/log", response_model=FitnessLogOut, status_code=status.HTTP_201_CREATED)
def log_fitness_activity(
    activity: FitnessLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a workout session."""
    new_log = FitnessLog(
        user_id=current_user.id,
        date=activity.date,
        workout_type=activity.workout_type,
        duration_minutes=activity.duration_minutes,
        notes=activity.notes
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/logs", response_model=List[FitnessLogOut])
def get_fitness_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workout history for current user."""
    query = db.query(FitnessLog).filter(FitnessLog.user_id == current_user.id)

    if start_date:
        query = query.filter(FitnessLog.date >= start_date)
    if end_date:
        query = query.filter(FitnessLog.date <= end_date)

    logs = query.order_by(FitnessLog.date.desc()).all()
    return logs


@router.get("/recommendations", response_model=FitnessRecommendationsResponse)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch workout recommendations tailored to current cycle phase."""
    cycle_logs = db.query(CycleLog).filter(
        CycleLog.user_id == current_user.id
    ).order_by(CycleLog.date.asc()).all()

    predictions = calculate_cycle_predictions(cycle_logs)
    current_phase = predictions["current_phase"]
    recommendations = get_phase_workout_recommendations(current_phase)

    return {
        "cycle_phase": current_phase,
        "recommendations": recommendations
    }
