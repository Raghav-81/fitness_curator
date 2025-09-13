"""
Workout Plan models for the Workout Video Search System.
Handles workout plans created by trainers for clients, including individual workout sessions.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any

# Importing Base from database module to ensure consistent Base instance
from ..database import Base

class WorkoutPlan(Base):
    """Workout plan created by trainers for clients."""
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    client_id = Column(Integer, ForeignKey("users.id"))
    trainer_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default="draft")  # "draft", "active", "completed", "archived"
    template_id = Column(Integer, ForeignKey("plan_templates.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="assigned_plans")
    trainer = relationship("User", foreign_keys=[trainer_id], back_populates="created_plans")
    template = relationship("PlanTemplate", back_populates="plans")
    workouts = relationship("PlanWorkout", back_populates="plan", cascade="all, delete-orphan")
    sections = relationship("PlanSection", back_populates="plan", cascade="all, delete-orphan")
    
    def to_dict(self, include_details=False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "client_id": self.client_id,
            "trainer_id": self.trainer_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "template_id": self.template_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add relationship data if requested
        if include_details:
            data["client"] = self.client.to_dict() if self.client else None
            data["trainer"] = self.trainer.to_dict() if self.trainer else None
            data["workouts"] = [workout.to_dict() for workout in self.workouts] if self.workouts else []
            data["sections"] = [section.to_dict() for section in self.sections] if self.sections else []
            
        return data


class PlanTemplate(Base):
    """Template for workout plans that trainers can reuse."""
    __tablename__ = "plan_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    trainer_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)  # Whether other trainers can use this template
    structure = Column(JSON, nullable=True)  # Structure of the template (sections, fields)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trainer = relationship("User")
    plans = relationship("WorkoutPlan", back_populates="template")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "trainer_id": self.trainer_id,
            "is_public": self.is_public,
            "structure": self.structure,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PlanSection(Base):
    """Section within a workout plan (e.g., "Week 1", "Nutrition", "Goals")."""
    __tablename__ = "plan_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)  # Order within the plan
    content = Column(Text, nullable=True)  # Rich text content
    content_type = Column(String, default="text")  # text, html, markdown
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = relationship("WorkoutPlan", back_populates="sections")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "content": self.content,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PlanWorkout(Base):
    """Individual workout sessions in a plan."""
    __tablename__ = "plan_workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    video_id = Column(Integer, ForeignKey("workout_videos.id"))
    section_id = Column(Integer, ForeignKey("plan_sections.id"), nullable=True)
    day_number = Column(Integer)
    order_in_day = Column(Integer)
    notes = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    sets = Column(Integer, nullable=True)
    reps = Column(String, nullable=True)  # Could be "12, 10, 8" for different set counts
    intensity = Column(String, nullable=True)  # e.g., "High", "Medium", "Low"
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plan = relationship("WorkoutPlan", back_populates="workouts")
    video = relationship("WorkoutVideoModel", foreign_keys=[video_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = {
            "id": self.id,
            "plan_id": self.plan_id,
            "video_id": self.video_id,
            "section_id": self.section_id,
            "day_number": self.day_number,
            "order_in_day": self.order_in_day,
            "notes": self.notes,
            "duration_minutes": self.duration_minutes,
            "sets": self.sets,
            "reps": self.reps,
            "intensity": self.intensity,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        # Add video data
        if self.video:
            data["video"] = {
                "id": self.video.id,
                "title": self.video.title,
                "category": self.video.category,
                "duration": self.video.duration,
                "video_url": self.video.video_url
            }
            
        return data
