import os
import httpx
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional
from dotenv import load_dotenv

from ..database import get_db
from ..models import User, WellnessLog, MoodLog, CycleLog
from ..schemas import (
    WellnessLogCreate, WellnessLogOut,
    ChatMessage, ChatResponse, APIKeyConfig, APIKeyStatus,
    GamificationResponse, CommunityPulseResponse
)
from ..auth import get_current_user
from ..utils import (
    calculate_wellness_score, generate_fallback_chat_reply,
    calculate_cycle_predictions
)

load_dotenv()

router = APIRouter(prefix="/api/wellness", tags=["Wellness & Chatbot"])

# Global runtime API configuration
RUNTIME_API_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "groq"),
    "api_key": os.getenv("GROQ_API_KEY", "") if os.getenv("GROQ_API_KEY", "") != "gsk_your_groq_api_key_here" else os.getenv("OPENAI_API_KEY", "")
}


def get_current_api_config():
    """Fetch latest runtime or environment API key config."""
    load_dotenv(override=True)
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if provider == "groq" and groq_key and groq_key != "gsk_your_groq_api_key_here":
        return {"provider": "groq", "api_key": groq_key}
    elif openai_key and openai_key != "your_openai_api_key_here":
        return {"provider": "openai", "api_key": openai_key}
    return RUNTIME_API_CONFIG


@router.get("/config-api", response_model=APIKeyStatus)
def get_api_key_status():
    """Return status of active LLM API connection (OpenAI / Groq / Fallback)."""
    config = get_current_api_config()
    api_key = config["api_key"]
    provider = config["provider"]

    if api_key and not api_key.startswith("your_") and not api_key.startswith("gsk_your_") and len(api_key.strip()) > 5:
        model_name = "llama-3.3-70b-versatile" if provider == "groq" else "gpt-3.5-turbo"
        return APIKeyStatus(
            is_connected=True,
            provider=provider.capitalize(),
            model=model_name,
            message=f"Live {provider.capitalize()} API Key configured."
        )
    return APIKeyStatus(
        is_connected=False,
        provider="Fallback Engine",
        model="Intelligent RAG Engine",
        message="Running on built-in empathetic RAG engine. Connect an API key for live LLM completions."
    )


@router.post("/config-api", response_model=APIKeyStatus)
def configure_api_key(config: APIKeyConfig):
    """Test and save external LLM API Key (OpenAI / Groq)."""
    key = config.api_key.strip()
    provider = (config.provider or "openai").lower()

    if not key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Key cannot be empty.")

    try:
        import openai
        if provider == "groq":
            client = openai.OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            model_name = "llama-3.3-70b-versatile"
        else:
            client = openai.OpenAI(api_key=key)
            model_name = "gpt-3.5-turbo"

        # Simple verification ping
        client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )

        RUNTIME_API_CONFIG["api_key"] = key
        RUNTIME_API_CONFIG["provider"] = provider

        # Optionally update .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "a") as f:
                f.write(f"\nOPENAI_API_KEY={key}\n" if provider == "openai" else f"\nGROQ_API_KEY={key}\n")

        return APIKeyStatus(
            is_connected=True,
            provider=provider.capitalize(),
            model=model_name,
            message=f"Successfully connected to {provider.capitalize()} API!"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API Connection Test Failed: {str(e)}"
        )


def call_llm_completion(provider: str, api_key: str, messages: list) -> str:
    """Call OpenAI or Groq API via requests HTTP with robust fallback handling."""
    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
    else:
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-3.5-turbo"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 350,
        "temperature": 0.7
    }

    resp = httpx.post(url, headers=headers, json=payload, timeout=12.0)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        data = resp.json() if resp.headers.get("content-type") == "application/json" else {}
        err_msg = data.get("error", {}).get("message", resp.text)
        err_code = data.get("error", {}).get("code", "")
        if "credit_balance_exhausted" in str(err_msg) or err_code == "insufficient_quota":
            raise HTTPException(
                status_code=402,
                detail="OpenAI Account Quota Exhausted (0 credits remaining). Please add credits at platform.openai.com or switch to Groq (Free)."
            )
        raise HTTPException(status_code=400, detail=f"LLM API Error ({resp.status_code}): {err_msg}")


@router.get("/config-api", response_model=APIKeyStatus)
def get_api_key_status():
    """Return status of active LLM API connection (OpenAI / Groq / Fallback)."""
    api_key = RUNTIME_API_CONFIG["api_key"] or os.getenv("OPENAI_API_KEY", "")
    provider = RUNTIME_API_CONFIG["provider"]

    if api_key and api_key != "your_openai_api_key_here" and len(api_key.strip()) > 5:
        model_name = "llama-3.3-70b-versatile" if provider == "groq" else "gpt-3.5-turbo"
        return APIKeyStatus(
            is_connected=True,
            provider=provider.capitalize(),
            model=model_name,
            message=f"Live {provider.capitalize()} API Key configured."
        )
    return APIKeyStatus(
        is_connected=False,
        provider="Fallback Engine",
        model="Intelligent RAG Engine",
        message="Running on built-in empathetic RAG engine. Connect an API key for live LLM completions."
    )


@router.post("/config-api", response_model=APIKeyStatus)
def configure_api_key(config: APIKeyConfig):
    """Test and save external LLM API Key (OpenAI / Groq)."""
    key = config.api_key.strip()
    provider = (config.provider or "openai").lower()

    if not key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Key cannot be empty.")

    try:
        test_messages = [{"role": "user", "content": "ping"}]
        call_llm_completion(provider, key, test_messages)

        RUNTIME_API_CONFIG["api_key"] = key
        RUNTIME_API_CONFIG["provider"] = provider

        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "a") as f:
                f.write(f"\nOPENAI_API_KEY={key}\n" if provider == "openai" else f"\nGROQ_API_KEY={key}\n")

        return APIKeyStatus(
            is_connected=True,
            provider=provider.capitalize(),
            model="llama-3.3-70b-versatile" if provider == "groq" else "gpt-3.5-turbo",
            message=f"Successfully connected to {provider.capitalize()} API!"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API Connection Test Failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
def chat_with_vera(payload: ChatMessage):
    """
    Proxy endpoint for Vera AI Chatbot companion.
    Connects to live OpenAI / Groq LLMs if configured, seamlessly falling back to local RAG engine.
    """
    user_message = payload.message.strip()
    user_context = payload.user_context
    history = payload.history or []

    config = get_current_api_config()
    api_key = config["api_key"]
    provider = config["provider"]

    ctx_str = ""
    if user_context:
        ctx_str = f" [User Context: Cycle Phase={user_context.get('current_phase')}, Day={user_context.get('current_cycle_day')}, Mode={user_context.get('tracking_mode')}]"

    system_prompt = (
        "You are Vera, a supportive wellness companion for women."
        f"{ctx_str} Provide empathy, CBT-based journaling prompts, breathing exercises, and positive affirmations. "
        "Never give medical diagnoses. If the user is in crisis, provide a helpline number."
    )

    if api_key and api_key != "your_openai_api_key_here" and len(api_key.strip()) > 5:
        try:
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for turn in history[-6:]:
                formatted_messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
            formatted_messages.append({"role": "user", "content": user_message})

            response_text = call_llm_completion(provider, api_key, formatted_messages)
            return {"response": response_text, "source": provider, "article_citation": None}
        except Exception as e:
            reply_dict = generate_fallback_chat_reply(user_message, user_context=user_context, history=history)
            return reply_dict
    else:
        reply_dict = generate_fallback_chat_reply(user_message, user_context=user_context, history=history)
        return reply_dict


@router.post("/log", response_model=WellnessLogOut, status_code=status.HTTP_201_CREATED)
def log_wellness_entry(
    entry: WellnessLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log or update daily wellness log and calculate score."""
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
    """Fetch wellness history within optional date range."""
    query = db.query(WellnessLog).filter(WellnessLog.user_id == current_user.id)

    if start_date:
        query = query.filter(WellnessLog.date >= start_date)
    if end_date:
        query = query.filter(WellnessLog.date <= end_date)

    logs = query.order_by(WellnessLog.date.asc()).all()
    return logs
