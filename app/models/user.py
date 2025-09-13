"""
User models for the Workout Video Search System.
Handles user authentication, profiles, and relationships between trainers and clients.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any

# Importing Base from database module to ensure consistent Base instance
from ..database import Base

class User(Base):
    """User model for authentication and profiles."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    google_id = Column(String, unique=True, nullable=True)  # For Google authentication
    hashed_password = Column(String, nullable=True)  # Nullable for social login
    full_name = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # "admin", "trainer", or "client"
    profile_image = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Trainer-specific fields
    specializations = Column(String, nullable=True)
    years_experience = Column(Integer, nullable=True)
    
    # Client-specific fields
    fitness_goals = Column(String, nullable=True)
    health_conditions = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # For trainers: clients they manage
    clients = relationship(
        "User", 
        secondary="client_trainer_relationships",
        primaryjoin="and_(User.id==ClientTrainerRelationship.trainer_id, User.user_type=='trainer')",
        secondaryjoin="and_(User.id==ClientTrainerRelationship.client_id, User.user_type=='client')",
        backref="trainers"
    )
    
    # Plans created by trainer
    created_plans = relationship("WorkoutPlan", foreign_keys="WorkoutPlan.trainer_id", back_populates="trainer")
    
    # Plans assigned to client
    assigned_plans = relationship("WorkoutPlan", foreign_keys="WorkoutPlan.client_id", back_populates="client")
    
    def to_dict(self, include_relationships=False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "user_type": self.user_type,
            "profile_image": self.profile_image,
            "bio": self.bio,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add type-specific fields
        if self.user_type == "trainer":
            data.update({
                "specializations": self.specializations,
                "years_experience": self.years_experience,
            })
        elif self.user_type == "client":
            data.update({
                "fitness_goals": self.fitness_goals,
                "health_conditions": self.health_conditions,
            })
            
        # Add relationship data if requested
        if include_relationships:
            if self.user_type == "trainer":
                data["clients"] = [
                    {"id": client.id, "full_name": client.full_name, "email": client.email}
                    for client in self.clients
                ]
            elif self.user_type == "client":
                data["trainers"] = [
                    {"id": trainer.id, "full_name": trainer.full_name, "email": trainer.email}
                    for trainer in self.trainers
                ]
                
        return data


class ClientTrainerRelationship(Base):
    """Mapping between clients and their trainers."""
    __tablename__ = "client_trainer_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")  # "active", "pending", "archived"
    created_at = Column(DateTime, default=datetime.utcnow)
