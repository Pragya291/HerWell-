import os
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from dotenv import load_dotenv

from ..database import get_db
from ..models import User, WellnessLog
from ..schemas import (
    WellnessLogCreate, WellnessLogOut,
    ChatMessage, ChatResponse
)
from ..auth import get_current_user
from ..utils import calculate_wellness_score, generate_fallback_chat_reply

load_dotenv()

router = APIRouter(prefix="/api/wellness", tags=["Wellness & Chatbot"])


@router.post("/log", response_model=WellnessLogOut, status_code=status.HTTP_201_CREATED)
def log_wellness_entry(
    entry: WellnessLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log or update daily wellness metrics and calculate wellness score."""
    score = calculate_wellness_score(
        sleep=entry.sleep_hours,
        hydration=entry.hydration_liters,
        exercise=entry.exercise_minutes,
        stress=entry.stress_level,
        mood=entry.mood_score
    )

    existing_log = db.query(WellnessLog).filter(
        WellnessLog.user_id == current_user.id,
        WellnessLog.date == entry.date
    ).first()

    if existing_log:
        existing_log.sleep_hours = entry.sleep_hours
        existing_log.hydration_liters = entry.hydration_liters
        existing_log.exercise_minutes = entry.exercise_minutes
        existing_log.stress_level = entry.stress_level
        existing_log.mood_score = entry.mood_score
        existing_log.wellness_score = score
        db.commit()
        db.refresh(existing_log)
        return existing_log

    new_log = WellnessLog(
        user_id=current_user.id,
        date=entry.date,
        sleep_hours=entry.sleep_hours,
        hydration_liters=entry.hydration_liters,
        exercise_minutes=entry.exercise_minutes,
        stress_level=entry.stress_level,
        mood_score=entry.mood_score,
        wellness_score=score
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/logs", response_model=List[WellnessLogOut])
def get_wellness_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch wellness log history within optional date range."""
    query = db.query(WellnessLog).filter(WellnessLog.user_id == current_user.id)

    if start_date:
        query = query.filter(WellnessLog.date >= start_date)
    if end_date:
        query = query.filter(WellnessLog.date <= end_date)

    logs = query.order_by(WellnessLog.date.asc()).all()
    return logs


@router.post("/chat", response_model=ChatResponse)
def chat_with_vera(payload: ChatMessage):
    """
    Proxy endpoint for Vera AI Chatbot companion.
    Uses OpenAI gpt-3.5-turbo if OPENAI_API_KEY is configured.
    Seamlessly falls back to an intelligent rule-based empathetic engine.
    """
    user_message = payload.message.strip()
    api_key = os.getenv("OPENAI_API_KEY")

    system_prompt = (
        "You are Vera, a supportive wellness companion for women. "
        "Provide empathy, CBT-based journaling prompts, breathing exercises, and positive affirmations. "
        "Never give medical diagnoses. If the user is in crisis, provide a helpline number."
    )

    if api_key and api_key != "your_openai_api_key_here":
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=350,
                temperature=0.7,
            )
            response_text = completion.choices[0].message.content
            return {"response": response_text, "source": "openai"}
        except Exception as e:
            fallback_text = generate_fallback_chat_reply(user_message)
            return {"response": fallback_text, "source": "fallback"}
    else:
        fallback_text = generate_fallback_chat_reply(user_message)
        return {"response": fallback_text, "source": "fallback"}
