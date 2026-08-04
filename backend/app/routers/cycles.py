from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import secrets
from typing import List, Optional

from ..database import get_db
from ..models import User, CycleLog, ShareLink
from ..schemas import (
    CycleLogCreate, CycleLogOut, CyclePredictions, 
    ShareLinkCreate, ShareLinkOut, SharedCycleData
)
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
        existing_log.cramps_severity = entry.cramps_severity
        existing_log.headache_severity = entry.headache_severity
        existing_log.acne_severity = entry.acne_severity
        existing_log.breast_tenderness_severity = entry.breast_tenderness_severity
        existing_log.hair_loss_severity = entry.hair_loss_severity
        existing_log.hirsutism_severity = entry.hirsutism_severity
        existing_log.ovulation_test_result = entry.ovulation_test_result
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
        cramps_severity=entry.cramps_severity,
        headache_severity=entry.headache_severity,
        acne_severity=entry.acne_severity,
        breast_tenderness_severity=entry.breast_tenderness_severity,
        hair_loss_severity=entry.hair_loss_severity,
        hirsutism_severity=entry.hirsutism_severity,
        ovulation_test_result=entry.ovulation_test_result,
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
    """Calculate and return cycle predictions based on user's history and active tracking mode."""
    logs = db.query(CycleLog).filter(
        CycleLog.user_id == current_user.id
    ).order_by(CycleLog.date.asc()).all()

    predictions = calculate_cycle_predictions(
        logs,
        tracking_mode=getattr(current_user, "tracking_mode", "regular"),
        custom_cycle_length=getattr(current_user, "custom_cycle_length", None)
    )
    return predictions


@router.post("/share", response_model=ShareLinkOut)
def create_share_link(
    config: ShareLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a secure, time-limited link to share fertile window and low energy days."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=config.hours_valid)
    
    new_share = ShareLink(
        user_id=current_user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    
    share_url = f"/share.html?token={token}"
    
    return ShareLinkOut(
        share_url=share_url,
        expires_at=expires_at
    )


@router.get("/share/view", response_model=SharedCycleData)
def view_shared_cycle_data(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Public view endpoint for shared cycle information, secured by time-limited token."""
    share_record = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not share_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared link is invalid or has been revoked."
        )
        
    if share_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Shared link has expired."
        )
        
    logs = db.query(CycleLog).filter(
        CycleLog.user_id == share_record.user_id
    ).order_by(CycleLog.date.asc()).all()
    
    user = db.query(User).filter(User.id == share_record.user_id).first()
    user_mode = user.tracking_mode if user else "regular"
    user_custom_len = user.custom_cycle_length if user else None

    predictions = calculate_cycle_predictions(logs, tracking_mode=user_mode, custom_cycle_length=user_custom_len)
    
    today = date.today()
    low_energy_days = []
    
    start_logs = sorted(
        [log for log in logs if getattr(log, "period_start", False)],
        key=lambda x: x.date
    )
    
    if start_logs:
        last_period_start = start_logs[-1].date
    else:
        last_period_start = today - timedelta(days=14)
        
    # Menstrual phase days (first 5 days of current cycle)
    for i in range(5):
        d = last_period_start + timedelta(days=i)
        low_energy_days.append(d.isoformat())
        
    # Late Luteal phase days (last 4 days before next period)
    predicted_next_period_str = predictions.get("predicted_next_period")
    if predicted_next_period_str:
        try:
            predicted_next_period = date.fromisoformat(predicted_next_period_str)
            for i in range(1, 5):
                d = predicted_next_period - timedelta(days=i)
                low_energy_days.append(d.isoformat())
        except Exception:
            pass
            
    low_energy_days = sorted(list(set(low_energy_days)))
    
    current_phase = predictions.get("current_phase", "Follicular")
    if current_phase == "Menstrual":
        tips = [
            "Your partner is in their Menstrual Phase. Estrogen and progesterone are at their lowest.",
            "💡 How to support: Help out extra with physical chores so they can rest.",
            "🍵 Comfort ideas: Prepare a hot water bottle for cramps, bring them warm herbal tea, or plan a relaxing evening."
        ]
    elif current_phase == "Follicular":
        tips = [
            "Your partner is in their Follicular Phase. Estrogen is rising, and their energy is climbing!",
            "💡 How to support: They might have high creativity and drive. Engage with their plans.",
            "🏃‍♀️ Date ideas: Plan an outdoor walk, try a new restaurant, or start a collaborative project together."
        ]
    elif current_phase == "Ovulatory":
        tips = [
            "Your partner is in their Ovulatory Phase. Energy, stamina, and social desire are at their highest.",
            "💡 How to support: Share in their social vibe. Great time for deep conversations and outings.",
            "✨ Date ideas: Plan a social gathering, attend a concert, or take on a fun challenge together."
        ]
    else:  # Luteal
        tips = [
            "Your partner is in their Luteal Phase. Progesterone is rising then dropping, meaning energy is winding down.",
            "💡 How to support: Be extra patient, listen to their feelings, and avoid planning too many high-energy events.",
            "🏡 Comfort ideas: Encourage self-care, cook a nutritious meal at home, and foster a quiet, cozy space."
        ]
        
    return SharedCycleData(
        fertile_window_start=predictions.get("fertile_window_start"),
        fertile_window_end=predictions.get("fertile_window_end"),
        ovulation_date=predictions.get("ovulation_date"),
        current_phase=current_phase,
        low_energy_days=low_energy_days,
        partner_tips=tips
    )

