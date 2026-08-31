from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, CycleLog, BBTLog, LHTestLog, CervicalMucusLog, PregnancyTestLog
from ..schemas import (
    BBTLogCreate, BBTLogOut,
    LHTestLogCreate, LHTestLogOut,
    CervicalMucusLogCreate, CervicalMucusLogOut,
    PregnancyTestLogCreate, PregnancyTestLogOut,
    FertilityOverview, FertilitySignalSummary, FertilityCalendarEvent,
    TTCInsightItem, TTCInsightsResponse
)
from ..auth import get_current_user
from ..utils import calculate_cycle_predictions, detect_bbt_ovulation_pattern, aggregate_fertility_signals

router = APIRouter(prefix="/api/fertility", tags=["Fertility & TTC Intelligence"])


@router.get("/overview", response_model=FertilityOverview)
def get_fertility_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve fertility overview metrics, estimated fertile window, and BBT ovulation shift detection."""
    cycle_logs = db.query(CycleLog).filter(CycleLog.user_id == current_user.id).all()
    bbt_logs = db.query(BBTLog).filter(BBTLog.user_id == current_user.id).all()
    lh_logs = db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id).all()
    mucus_logs = db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id).all()

    predictions = calculate_cycle_predictions(
        logs=cycle_logs,
        tracking_mode=current_user.tracking_mode,
        custom_cycle_length=current_user.custom_cycle_length
    )

    today = date.today()
    cycle_len = predictions["average_cycle_length"]
    current_day = predictions["current_cycle_day"]
    current_phase = predictions["current_phase"]

    # Calculate estimated fertile window strings
    fw_start_dt = datetime.fromisoformat(predictions["fertile_window_start"]).date() if predictions.get("fertile_window_start") else today
    fw_end_dt = datetime.fromisoformat(predictions["fertile_window_end"]).date() if predictions.get("fertile_window_end") else today
    ov_dt = datetime.fromisoformat(predictions["ovulation_date"]).date() if predictions.get("ovulation_date") else today

    fertile_window_str = f"{fw_start_dt.strftime('%b %d')} – {fw_end_dt.strftime('%b %d')}"
    ovulation_str = ov_dt.strftime("%b %d")

    days_until_fw = (fw_start_dt - today).days
    if days_until_fw < 0:
        days_until_fw = 0

    start_logs = sorted([log for log in cycle_logs if log.period_start], key=lambda x: x.date)
    last_start = start_logs[-1].date if start_logs else (today - timedelta(days=14))
    days_since_period = (today - last_start).days

    # Status badge determination
    if fw_start_dt <= today <= fw_end_dt:
        status_badge = "🟢 Peak fertile window"
    elif 0 < (fw_start_dt - today).days <= 4:
        status_badge = f"🟢 Approaching fertile window in {(fw_start_dt - today).days} days"
    elif current_phase == "Luteal":
        status_badge = "🟡 Post-ovulatory / Luteal phase"
    else:
        status_badge = "🔵 Pre-fertile window phase"

    bbt_pattern = detect_bbt_ovulation_pattern(bbt_logs, last_period_start=last_start)

    sufficient = len(cycle_logs) > 0 or len(bbt_logs) > 0 or len(lh_logs) > 0 or len(mucus_logs) > 0

    return {
        "current_cycle_day": current_day,
        "cycle_length": cycle_len,
        "current_phase": current_phase,
        "estimated_fertile_window": fertile_window_str,
        "estimated_ovulation_date": ovulation_str,
        "days_until_fertile_window": days_until_fw,
        "days_since_period_start": days_since_period,
        "status_badge": status_badge,
        "bbt_pattern_shift": bbt_pattern,
        "sufficient_data": sufficient
    }


@router.get("/signals", response_model=FertilitySignalSummary)
def get_fertility_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve aggregated fertility signal summary."""
    cycle_logs = db.query(CycleLog).filter(CycleLog.user_id == current_user.id).all()
    bbt_logs = db.query(BBTLog).filter(BBTLog.user_id == current_user.id).all()
    lh_logs = db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id).all()
    mucus_logs = db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id).all()

    predictions = calculate_cycle_predictions(
        logs=cycle_logs,
        tracking_mode=current_user.tracking_mode,
        custom_cycle_length=current_user.custom_cycle_length
    )

    return aggregate_fertility_signals(cycle_logs, bbt_logs, lh_logs, mucus_logs, predictions)


# --- BBT Log Endpoints ---
@router.get("/bbt", response_model=List[BBTLogOut])
def get_bbt_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all BBT log entries for authenticated user."""
    return db.query(BBTLog).filter(BBTLog.user_id == current_user.id).order_by(BBTLog.date.asc()).all()


@router.post("/bbt", response_model=BBTLogOut, status_code=status.HTTP_201_CREATED)
def create_or_update_bbt_log(
    payload: BBTLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update BBT entry for a specific date."""
    existing = db.query(BBTLog).filter(BBTLog.user_id == current_user.id, BBTLog.date == payload.date).first()
    if existing:
        existing.temperature = payload.temperature
        existing.unit = payload.unit
        existing.note = payload.note
        db.commit()
        db.refresh(existing)
        return existing

    new_log = BBTLog(
        user_id=current_user.id,
        date=payload.date,
        temperature=payload.temperature,
        unit=payload.unit,
        note=payload.note
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.put("/bbt/{bbt_id}", response_model=BBTLogOut)
def update_bbt_log(
    bbt_id: int,
    payload: BBTLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing BBT log entry by ID."""
    log = db.query(BBTLog).filter(BBTLog.id == bbt_id, BBTLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="BBT entry not found.")
    log.date = payload.date
    log.temperature = payload.temperature
    log.unit = payload.unit
    log.note = payload.note
    db.commit()
    db.refresh(log)
    return log


@router.delete("/bbt/{bbt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bbt_log(
    bbt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a BBT log entry by ID."""
    log = db.query(BBTLog).filter(BBTLog.id == bbt_id, BBTLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="BBT entry not found.")
    db.delete(log)
    db.commit()
    return None


# --- LH Test Endpoints ---
@router.get("/lh", response_model=List[LHTestLogOut])
def get_lh_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all LH test entries for authenticated user."""
    return db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id).order_by(LHTestLog.date.asc()).all()


@router.post("/lh", response_model=LHTestLogOut, status_code=status.HTTP_201_CREATED)
def create_lh_log(
    payload: LHTestLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log an LH ovulation test result."""
    existing = db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id, LHTestLog.date == payload.date).first()
    if existing:
        existing.result = payload.result
        existing.time = payload.time
        existing.value = payload.value
        existing.note = payload.note
        db.commit()
        db.refresh(existing)
        return existing

    new_log = LHTestLog(
        user_id=current_user.id,
        date=payload.date,
        time=payload.time,
        result=payload.result,
        value=payload.value,
        note=payload.note
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.delete("/lh/{lh_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lh_log(
    lh_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an LH test entry by ID."""
    log = db.query(LHTestLog).filter(LHTestLog.id == lh_id, LHTestLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="LH test entry not found.")
    db.delete(log)
    db.commit()
    return None


# --- Cervical Mucus Endpoints ---
@router.get("/cervical-mucus", response_model=List[CervicalMucusLogOut])
def get_cervical_mucus_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all cervical mucus log entries for authenticated user."""
    return db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id).order_by(CervicalMucusLog.date.asc()).all()


@router.post("/cervical-mucus", response_model=CervicalMucusLogOut, status_code=status.HTTP_201_CREATED)
def create_cervical_mucus_log(
    payload: CervicalMucusLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a cervical mucus observation."""
    existing = db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id, CervicalMucusLog.date == payload.date).first()
    if existing:
        existing.type = payload.type
        existing.note = payload.note
        db.commit()
        db.refresh(existing)
        return existing

    new_log = CervicalMucusLog(
        user_id=current_user.id,
        date=payload.date,
        type=payload.type,
        note=payload.note
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.delete("/cervical-mucus/{cm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cervical_mucus_log(
    cm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a cervical mucus log entry by ID."""
    log = db.query(CervicalMucusLog).filter(CervicalMucusLog.id == cm_id, CervicalMucusLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Cervical mucus entry not found.")
    db.delete(log)
    db.commit()
    return None


# --- Pregnancy Test Endpoints ---
@router.get("/pregnancy-test", response_model=List[PregnancyTestLogOut])
def get_pregnancy_test_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pregnancy test entries for authenticated user."""
    return db.query(PregnancyTestLog).filter(PregnancyTestLog.user_id == current_user.id).order_by(PregnancyTestLog.date.asc()).all()


@router.post("/pregnancy-test", response_model=PregnancyTestLogOut, status_code=status.HTTP_201_CREATED)
def create_pregnancy_test_log(
    payload: PregnancyTestLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a pregnancy test result."""
    existing = db.query(PregnancyTestLog).filter(PregnancyTestLog.user_id == current_user.id, PregnancyTestLog.date == payload.date).first()
    if existing:
        existing.result = payload.result
        existing.note = payload.note
        db.commit()
        db.refresh(existing)
        return existing

    new_log = PregnancyTestLog(
        user_id=current_user.id,
        date=payload.date,
        result=payload.result,
        note=payload.note
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.delete("/pregnancy-test/{pt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pregnancy_test_log(
    pt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a pregnancy test log entry by ID."""
    log = db.query(PregnancyTestLog).filter(PregnancyTestLog.id == pt_id, PregnancyTestLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Pregnancy test entry not found.")
    db.delete(log)
    db.commit()
    return None


# --- Calendar & Insights ---
@router.get("/calendar", response_model=List[FertilityCalendarEvent])
def get_fertility_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve month fertility calendar events combining period, fertile window, ovulation, BBT, LH, and Mucus."""
    cycle_logs = db.query(CycleLog).filter(CycleLog.user_id == current_user.id).all()
    bbt_logs = db.query(BBTLog).filter(BBTLog.user_id == current_user.id).all()
    lh_logs = db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id).all()
    mucus_logs = db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id).all()
    preg_logs = db.query(PregnancyTestLog).filter(PregnancyTestLog.user_id == current_user.id).all()

    predictions = calculate_cycle_predictions(
        logs=cycle_logs,
        tracking_mode=current_user.tracking_mode,
        custom_cycle_length=current_user.custom_cycle_length
    )

    fw_start = datetime.fromisoformat(predictions["fertile_window_start"]).date() if predictions.get("fertile_window_start") else None
    fw_end = datetime.fromisoformat(predictions["fertile_window_end"]).date() if predictions.get("fertile_window_end") else None
    ov_date = datetime.fromisoformat(predictions["ovulation_date"]).date() if predictions.get("ovulation_date") else None

    # Map logs by date string
    bbt_dict = {b.date.isoformat(): b for b in bbt_logs}
    lh_dict = {l.date.isoformat(): l for l in lh_logs}
    cm_dict = {c.date.isoformat(): c for c in mucus_logs}
    pt_dict = {p.date.isoformat(): p for p in preg_logs}
    period_dates = {c.date.isoformat() for c in cycle_logs if c.period_start or c.flow_intensity}

    events = []
    today = date.today()
    # Generate 60-day calendar range around today
    start_range = today - timedelta(days=30)
    end_range = today + timedelta(days=30)

    curr = start_range
    while curr <= end_range:
        d_str = curr.isoformat()
        is_p = d_str in period_dates
        is_fw = bool(fw_start and fw_end and fw_start <= curr <= fw_end)
        is_ov = bool(ov_date and curr == ov_date)

        bbt = bbt_dict.get(d_str)
        lh = lh_dict.get(d_str)
        cm = cm_dict.get(d_str)
        pt = pt_dict.get(d_str)

        events.append({
            "date": d_str,
            "is_period": is_p,
            "is_fertile_window": is_fw,
            "is_ovulation": is_ov,
            "has_bbt": bbt is not None,
            "bbt_temp": bbt.temperature if bbt else None,
            "has_lh": lh is not None,
            "lh_result": lh.result if lh else None,
            "has_mucus": cm is not None,
            "mucus_type": cm.type if cm else None,
            "has_pregnancy_test": pt is not None,
            "pregnancy_result": pt.result if pt else None
        })
        curr += timedelta(days=1)

    return events


@router.get("/insights", response_model=TTCInsightsResponse)
def get_ttc_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve personalized TTC smart insight cards."""
    cycle_logs = db.query(CycleLog).filter(CycleLog.user_id == current_user.id).all()
    bbt_logs = db.query(BBTLog).filter(BBTLog.user_id == current_user.id).all()
    lh_logs = db.query(LHTestLog).filter(LHTestLog.user_id == current_user.id).all()
    mucus_logs = db.query(CervicalMucusLog).filter(CervicalMucusLog.user_id == current_user.id).all()

    predictions = calculate_cycle_predictions(
        logs=cycle_logs,
        tracking_mode=current_user.tracking_mode,
        custom_cycle_length=current_user.custom_cycle_length
    )

    insights = []

    # 1. BBT Insight
    bbt_pattern = detect_bbt_ovulation_pattern(bbt_logs)
    if bbt_pattern["detected"]:
        insights.append({
            "icon": "🌡️",
            "title": "BBT Pattern Shift Detected",
            "description": bbt_pattern["message"],
            "category": "BBT Pattern"
        })
    elif bbt_logs:
        insights.append({
            "icon": "🌡️",
            "title": "BBT Baseline Tracking",
            "description": "Your recent temperature data is being tracked. Keep logging daily morning temps to help identify post-ovulatory patterns.",
            "category": "BBT Pattern"
        })

    # 2. LH Status Insight
    surge_log = next((l for l in sorted(lh_logs, key=lambda x: x.date, reverse=True) if l.result == "surge"), None)
    if surge_log:
        insights.append({
            "icon": "🧪",
            "title": "LH Surge Logged",
            "description": f"An LH surge was logged on {surge_log.date}. An LH surge typically precedes ovulation by 24–36 hours.",
            "category": "LH Status"
        })
    elif lh_logs:
        insights.append({
            "icon": "🧪",
            "title": "LH Monitoring",
            "description": f"Latest LH result recorded as '{lh_logs[-1].result.capitalize()}'. Continue daily testing near your estimated fertile window.",
            "category": "LH Status"
        })

    # 3. Cervical Mucus Insight
    fertile_mucus = next((m for m in sorted(mucus_logs, key=lambda x: x.date, reverse=True) if m.type in ["watery", "egg_white"]), None)
    if fertile_mucus:
        type_name = fertile_mucus.type.replace('_', '-').capitalize()
        insights.append({
            "icon": "💧",
            "title": "Fertile-Type Cervical Mucus",
            "description": f"You recorded a {type_name} mucus observation on {fertile_mucus.date}, consistent with peak fertile window conditions.",
            "category": "Cervical Mucus"
        })

    # 4. Cycle Pattern Insight
    avg_len = predictions["average_cycle_length"]
    insights.append({
        "icon": "📅",
        "title": "Cycle Baseline Pattern",
        "description": f"Your recent cycles have averaged approximately {avg_len} days.",
        "category": "Cycle Pattern"
    })

    sufficient = len(cycle_logs) > 0 or len(bbt_logs) > 0 or len(lh_logs) > 0 or len(mucus_logs) > 0

    return {
        "insights": insights,
        "sufficient_data": sufficient
    }
