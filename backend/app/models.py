from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cycle_logs = relationship("CycleLog", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    fitness_logs = relationship("FitnessLog", back_populates="user", cascade="all, delete-orphan")
    wellness_logs = relationship("WellnessLog", back_populates="user", cascade="all, delete-orphan")


class CycleLog(Base):
    """Menstrual and reproductive cycle tracking log entry."""
    __tablename__ = "cycle_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    period_start = Column(Boolean, default=False)
    period_end = Column(Boolean, default=False)
    flow_intensity = Column(Integer, nullable=True)  # 1=Spotting, 2=Light, 3=Medium, 4=Heavy
    symptoms = Column(String, nullable=True)  # Comma-separated: "cramps,headache,bloating"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="cycle_logs")


class MoodLog(Base):
    """Mental wellness mood log entry."""
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    mood = Column(Integer, nullable=False)  # 1=Very Sad to 5=Very Happy
    journal = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="mood_logs")


class FitnessLog(Base):
    """Personalized fitness log entry."""
    __tablename__ = "fitness_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    workout_type = Column(String, nullable=False)  # e.g., "Yoga", "HIIT", "Walking"
    duration_minutes = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="fitness_logs")


class WellnessLog(Base):
    """Daily wellness calculation log entry."""
    __tablename__ = "wellness_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    sleep_hours = Column(Float, nullable=False)
    hydration_liters = Column(Float, nullable=False)
    exercise_minutes = Column(Integer, nullable=False)
    stress_level = Column(String, nullable=False)  # "low", "medium", "high"
    mood_score = Column(Integer, nullable=False)  # 1 to 5
    wellness_score = Column(Integer, nullable=False)  # calculated 0-100
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="wellness_logs")
