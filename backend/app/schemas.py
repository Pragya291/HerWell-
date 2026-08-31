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


class UserProfileUpdate(BaseModel):
    tracking_mode: Optional[str] = Field("regular", description="Tracking mode: regular, pcos_pcod, irregular, perimenopause, ttc")
    custom_cycle_length: Optional[int] = Field(None, ge=15, le=120, description="Optional custom expected cycle length baseline")


class UserOut(BaseModel):
    id: int
    email: str
    tracking_mode: str = "regular"
    custom_cycle_length: Optional[int] = None
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
    cramps_severity: Optional[int] = Field(None, ge=1, le=3)
    headache_severity: Optional[int] = Field(None, ge=1, le=3)
    acne_severity: Optional[int] = Field(None, ge=1, le=3)
    breast_tenderness_severity: Optional[int] = Field(None, ge=1, le=3)
    hair_loss_severity: Optional[int] = Field(None, ge=1, le=3)
    hirsutism_severity: Optional[int] = Field(None, ge=1, le=3)
    ovulation_test_result: Optional[str] = Field(None, description="negative, positive, lh_surge")
    notes: Optional[str] = None


class CycleLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    period_start: bool
    period_end: bool
    flow_intensity: Optional[int] = None
    symptoms: Optional[str] = None
    cramps_severity: Optional[int] = None
    headache_severity: Optional[int] = None
    acne_severity: Optional[int] = None
    breast_tenderness_severity: Optional[int] = None
    hair_loss_severity: Optional[int] = None
    hirsutism_severity: Optional[int] = None
    ovulation_test_result: Optional[str] = None
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
    deviation: int = 0
    deviation_message: Optional[str] = None
    tracking_mode: str = "regular"
    prediction_confidence: str = "High"
    pcos_insights: List[str] = []



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
    user_context: Optional[dict] = Field(None, description="Optional current cycle phase, tracking mode, mood, and wellness score context")
    history: Optional[List[dict]] = Field(default=[], description="List of previous conversation turns: [{role: 'user'|'assistant', content: str}]")


class ArticleCitation(BaseModel):
    id: int
    title: str
    category: str
    summary: str


class ChatResponse(BaseModel):
    response: str
    source: str  # "openai", "groq", "rag_fallback", or "fallback"
    article_citation: Optional[ArticleCitation] = None


class APIKeyConfig(BaseModel):
    api_key: str = Field(..., description="API Key for OpenAI, Groq, or Gemini")
    provider: Optional[str] = Field("openai", description="openai, groq, gemini")


class APIKeyStatus(BaseModel):
    is_connected: bool
    provider: str
    model: str
    message: str


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


class AIHealthSummary(BaseModel):
    wellness_score: int
    ai_health_score: int
    sleep_quality: str
    stress_level: str
    hydration: str
    greeting: str
    bullets: List[str]
    ai_recommendation: str


# --- Wellness Score Calculator Schemas ---
class WellnessLogCreate(BaseModel):
    date: date
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    hydration_liters: float = Field(..., ge=0.0, le=10.0)
    exercise_minutes: int = Field(..., ge=0, le=300)
    stress_level: str
    mood_score: int = Field(..., ge=1, le=5)


class WellnessLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    sleep_hours: float
    hydration_liters: float
    exercise_minutes: int
    stress_level: str
    mood_score: int
    wellness_score: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Partner Sharing Schemas ---
class ShareLinkCreate(BaseModel):
    hours_valid: int = Field(48, ge=1, le=168)  # up to 7 days


class ShareLinkOut(BaseModel):
    share_url: str
    expires_at: datetime


class SharedCycleData(BaseModel):
    fertile_window_start: Optional[str] = None
    fertile_window_end: Optional[str] = None
    ovulation_date: Optional[str] = None
    current_phase: str
    low_energy_days: List[str]
    partner_tips: List[str]


# --- Gamification & Community Pulse Schemas ---
class BadgeStatus(BaseModel):
    unlocked: bool
    progress: int
    target: int
    current_streak: int


class GamificationResponse(BaseModel):
    mood_streak: BadgeStatus
    hydration_streak: BadgeStatus


class CommunityPulseResponse(BaseModel):
    percentage: int
    phase: str
    message: str
    pulse_type: str


# --- Fertility & TTC Schemas ---
class BBTLogCreate(BaseModel):
    date: date
    temperature: float = Field(..., ge=34.0, le=42.0)
    unit: str = Field("°C", description="°C or °F")
    note: Optional[str] = None


class BBTLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    temperature: float
    unit: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LHTestLogCreate(BaseModel):
    date: date
    time: Optional[str] = None
    result: str = Field(..., description="low, rising, surge, not_recorded")
    value: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None


class LHTestLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    time: Optional[str] = None
    result: str
    value: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CervicalMucusLogCreate(BaseModel):
    date: date
    type: str = Field(..., description="dry, sticky, creamy, watery, egg_white, not_observed")
    note: Optional[str] = None


class CervicalMucusLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    type: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PregnancyTestLogCreate(BaseModel):
    date: date
    result: str = Field(..., description="negative, positive, unclear")
    note: Optional[str] = None


class PregnancyTestLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    result: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FertilityOverview(BaseModel):
    current_cycle_day: int
    cycle_length: int
    current_phase: str
    estimated_fertile_window: str
    estimated_ovulation_date: str
    days_until_fertile_window: int
    days_since_period_start: int
    status_badge: str
    bbt_pattern_shift: Optional[dict] = None
    sufficient_data: bool = True


class FertilitySignalSummary(BaseModel):
    bbt_status: str
    lh_status: str
    cervical_mucus_status: str
    cycle_data_status: str
    estimated_fertility_status: str
    disclaimer: str


class FertilityCalendarEvent(BaseModel):
    date: str
    is_period: bool = False
    is_fertile_window: bool = False
    is_ovulation: bool = False
    has_bbt: bool = False
    bbt_temp: Optional[float] = None
    has_lh: bool = False
    lh_result: Optional[str] = None
    has_mucus: bool = False
    mucus_type: Optional[str] = None
    has_pregnancy_test: bool = False
    pregnancy_result: Optional[str] = None


class TTCInsightItem(BaseModel):
    icon: str
    title: str
    description: str
    category: str


class TTCInsightsResponse(BaseModel):
    insights: List[TTCInsightItem]
    sufficient_data: bool = True





