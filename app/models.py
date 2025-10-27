"""
Database models for workout creator functionality.
Includes Client, WorkoutPlan, and PlanExercise models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

from app.database import Base


class Client(Base):
    """Client model for storing trainer's client information."""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    goals = Column(Text, nullable=True)
    trainer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workout_plans = relationship("WorkoutPlan", back_populates="client", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "age": self.age,
            "goals": self.goals,
            "trainer_notes": self.trainer_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class WorkoutPlan(Base):
    """Workout plan model for storing trainer-created workout plans."""
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Legacy column for backward compatibility
    plan_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_template = Column(Boolean, default=False)  # Can be saved as reusable template
    share_token = Column(String(64), unique=True, index=True, nullable=True)  # For shareable links
    day_type = Column(String(20), default="day_number")  # "day_number" or "day_of_week"
    
    # Enhanced split configuration
    number_of_days = Column(Integer, nullable=True)  # Number of days in split (e.g., 3 for 3-day split)
    weeks_duration = Column(Integer, nullable=True)  # Number of weeks to follow the plan
    day_labels = Column(JSON, nullable=True)  # Custom day labels: {"1": "Push Day", "2": "Pull Day", "3": "Leg Day"}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="workout_plans")
    exercises = relationship("PlanExercise", back_populates="plan", cascade="all, delete-orphan", order_by="PlanExercise.order_index")
    
    def generate_share_token(self):
        """Generate a unique shareable token for this plan."""
        self.share_token = secrets.token_urlsafe(32)
        return self.share_token
    
    def to_dict(self, include_exercises=False):
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.name if self.client else None,
            "plan_name": self.plan_name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_template": self.is_template,
            "share_token": self.share_token,
            "day_type": self.day_type,
            "number_of_days": self.number_of_days,
            "weeks_duration": self.weeks_duration,
            "day_labels": self.day_labels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_exercises:
            data["exercises"] = [ex.to_dict() for ex in self.exercises]
        
        return data


class PlanExercise(Base):
    """Individual exercise within a workout plan."""
    __tablename__ = "plan_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("workout_videos.id"), nullable=True, index=True)  # Nullable for custom exercises
    
    # Exercise details
    section = Column(String(20), nullable=True)  # "warmup", "main", or "cooldown"
    day = Column(String(50), nullable=False)  # Can be "Monday", "Day 1", etc.
    sets = Column(Integer, nullable=True)
    reps = Column(String(50), nullable=True)  # String to allow "10-12" or "AMRAP"
    time = Column(Integer, nullable=True)  # Hold time in seconds/minutes
    time_unit = Column(String(10), nullable=True)  # "sec" or "min"
    notes = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)  # For ordering exercises within a day
    
    # Custom exercise fields
    is_custom = Column(Boolean, default=False)
    custom_name = Column(String(255), nullable=True)
    custom_youtube_url = Column(String(500), nullable=True)
    custom_equipment = Column(String(255), nullable=True)
    
    # Client tracking fields (for when client uses the plan)
    completed = Column(Boolean, default=False)
    weight_logged = Column(JSON, nullable=True)  # Store array of weights for each set
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plan = relationship("WorkoutPlan", back_populates="exercises")
    video = relationship("WorkoutVideoModel")
    
    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "video_id": self.video_id,
            "video": self.video.to_dict() if self.video else None,
            "section": self.section,
            "day": self.day,
            "sets": self.sets,
            "reps": self.reps,
            "time": self.time,
            "time_unit": self.time_unit,
            "notes": self.notes,
            "order_index": self.order_index,
            "is_custom": self.is_custom,
            "custom_name": self.custom_name,
            "custom_youtube_url": self.custom_youtube_url,
            "custom_equipment": self.custom_equipment,
            "completed": self.completed,
            "weight_logged": self.weight_logged,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
