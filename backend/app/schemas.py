from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    user_id: Optional[int] = None


# --- Cycle Tracking Schemas ---
class CycleLogCreate(BaseModel):
    date: date
    period_start: Optional[bool] = False
    period_end: Optional[bool] = False
    flow_intensity: Optional[int] = Field(None, ge=1, le=4)
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class CycleLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    period_start: bool
    period_end: bool
    flow_intensity: Optional[int] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CyclePredictions(BaseModel):
    average_cycle_length: int
    predicted_next_period: Optional[str] = None
    ovulation_date: Optional[str] = None
    fertile_window_start: Optional[str] = None
    fertile_window_end: Optional[str] = None
    current_cycle_day: int
    current_phase: str
    phase_description: str


# --- Mood Schemas ---
class MoodLogCreate(BaseModel):
    date: date
    mood: int = Field(..., ge=1, le=5)
    journal: Optional[str] = None


class MoodLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    mood: int
    journal: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WeeklyMoodTrend(BaseModel):
    week_label: str
    average_mood: float
    entries_count: int


class MoodTrendsResponse(BaseModel):
    weekly_trends: List[WeeklyMoodTrend]
    overall_average: float


# --- Fitness Schemas ---
class FitnessLogCreate(BaseModel):
    date: date
    workout_type: str
    duration_minutes: int = Field(..., gt=0)
    notes: Optional[str] = None


class FitnessLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    workout_type: str
    duration_minutes: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutRecommendation(BaseModel):
    title: str
    category: str
    duration: str
    intensity: str
    description: str
    benefits: str


class FitnessRecommendationsResponse(BaseModel):
    cycle_phase: str
    recommendations: List[WorkoutRecommendation]


# --- Health & Chat Schemas ---
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    source: str  # "openai" or "fallback"


class ArticleOut(BaseModel):
    id: int
    title: str
    category: str
    summary: str
    content: str
    myth: Optional[str] = None
    fact: Optional[str] = None


class MythFactOut(BaseModel):
    id: int
    category: str
    myth: str
    fact: str
