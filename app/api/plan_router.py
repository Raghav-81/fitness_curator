"""
Workout Plan API endpoints for the Workout Video Search System.
Handles CRUD operations for workout plans, templates, and sections.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

import sys
from pathlib import Path as FilePath
import logging
import json

from app.auth import get_db, get_current_active_user
from app.models.user import User
from app.models.plan import WorkoutPlan, PlanTemplate, PlanSection, PlanWorkout

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["plans"], prefix="/plans")

# Pydantic models
class PlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    template_id: Optional[int] = None
    notes: Optional[str] = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class PlanSectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = None
    content: Optional[str] = None
    content_type: Optional[str] = "text"

class PlanSectionCreate(PlanSectionBase):
    pass

class PlanSectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    content: Optional[str] = None
    content_type: Optional[str] = None

class PlanWorkoutBase(BaseModel):
    video_id: int
    section_id: Optional[int] = None
    day_number: int
    order_in_day: int = 0
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    intensity: Optional[str] = None

class PlanWorkoutCreate(PlanWorkoutBase):
    pass

class PlanWorkoutUpdate(BaseModel):
    section_id: Optional[int] = None
    day_number: Optional[int] = None
    order_in_day: Optional[int] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    intensity: Optional[str] = None
    completed: Optional[bool] = None
    completed_at: Optional[datetime] = None

class PlanResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    client_id: int
    trainer_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    template_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PlanDetailResponse(PlanResponse):
    client: Optional[Dict[str, Any]] = None
    trainer: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    workouts: Optional[List[Dict[str, Any]]] = None

class PlanListResponse(BaseModel):
    plans: List[PlanResponse]
    total: int
    page: int
    per_page: int

# Endpoints
@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new workout plan."""
    # Ensure user is a trainer
    if current_user.user_type != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can create workout plans"
        )
    
    # Check if client exists
    client = db.query(User).filter(
        User.id == plan.client_id,
        User.user_type == "client"
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Create the plan
    new_plan = WorkoutPlan(
        title=plan.title,
        description=plan.description,
        client_id=plan.client_id,
        trainer_id=current_user.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        template_id=plan.template_id,
        notes=plan.notes
    )
    
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    return new_plan

@router.get("/{plan_id}", response_model=PlanDetailResponse)
async def read_plan(
    plan_id: int = Path(..., gt=0),
    include_details: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific workout plan by ID."""
    # Get the plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    # Check if user has access to this plan
    if current_user.id != plan.trainer_id and current_user.id != plan.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this plan"
        )
    
    # Return plan with details
    return plan.to_dict(include_details=include_details)

@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_data: PlanUpdate,
    plan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a workout plan."""
    # Get the plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    # Check if user has access to update this plan
    if current_user.id != plan.trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trainer can update this plan"
        )
    
    # Update plan fields
    for key, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, key, value)
    
    # Update timestamp
    plan.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(plan)
    
    return plan

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a workout plan."""
    # Get the plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    # Check if user has access to delete this plan
    if current_user.id != plan.trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trainer can delete this plan"
        )
    
    # Delete the plan
    db.delete(plan)
    db.commit()
    
    return None

@router.get("/", response_model=PlanListResponse)
async def read_plans(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a list of workout plans."""
    # Start with base query
    query = db.query(WorkoutPlan)
    
    # Filter based on user type
    if current_user.user_type == "trainer":
        # Trainers can see their created plans
        query = query.filter(WorkoutPlan.trainer_id == current_user.id)
    elif current_user.user_type == "client":
        # Clients can see plans assigned to them
        query = query.filter(WorkoutPlan.client_id == current_user.id)
    else:
        # Admin can see all plans
        pass
    
    # Apply additional filters
    if client_id:
        query = query.filter(WorkoutPlan.client_id == client_id)
    
    if status:
        query = query.filter(WorkoutPlan.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Get results
    plans = query.all()
    
    return {
        "plans": plans,
        "total": total,
        "page": page,
        "per_page": per_page
    }

# Plan sections
@router.post("/{plan_id}/sections", status_code=status.HTTP_201_CREATED)
async def create_plan_section(
    section: PlanSectionCreate,
    plan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new section in a workout plan."""
    # Get the plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    # Check if user has access to update this plan
    if current_user.id != plan.trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trainer can add sections to this plan"
        )
    
    # Create the section
    new_section = PlanSection(
        plan_id=plan_id,
        title=section.title,
        description=section.description,
        order=section.order,
        content=section.content,
        content_type=section.content_type
    )
    
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    
    return new_section

# Plan workouts
@router.post("/{plan_id}/workouts", status_code=status.HTTP_201_CREATED)
async def create_plan_workout(
    workout: PlanWorkoutCreate,
    plan_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a workout to a plan."""
    # Get the plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    # Check if user has access to update this plan
    if current_user.id != plan.trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trainer can add workouts to this plan"
        )
    
    # Create the workout
    new_workout = PlanWorkout(
        plan_id=plan_id,
        video_id=workout.video_id,
        section_id=workout.section_id,
        day_number=workout.day_number,
        order_in_day=workout.order_in_day,
        notes=workout.notes,
        duration_minutes=workout.duration_minutes,
        sets=workout.sets,
        reps=workout.reps,
        intensity=workout.intensity
    )
    
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    
    return new_workout

@router.put("/{plan_id}/workouts/{workout_id}")
async def update_plan_workout(
    workout_data: PlanWorkoutUpdate,
    plan_id: int = Path(..., gt=0),
    workout_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a workout in a plan."""
    # Get the plan and workout
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found"
        )
    
    workout = db.query(PlanWorkout).filter(
        PlanWorkout.id == workout_id,
        PlanWorkout.plan_id == plan_id
    ).first()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found in this plan"
        )
    
    # Check if user has access to update this plan
    if current_user.id != plan.trainer_id and current_user.id != plan.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to update this workout"
        )
    
    # Clients can only update completion status
    if current_user.id == plan.client_id:
        allowed_fields = ['completed', 'completed_at']
        update_data = {k: v for k, v in workout_data.dict(exclude_unset=True).items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clients can only update completion status"
            )
    else:
        # Trainer can update all fields
        update_data = workout_data.dict(exclude_unset=True)
    
    # Update workout fields
    for key, value in update_data.items():
        setattr(workout, key, value)
    
    # If marking as completed, set completed_at timestamp
    if update_data.get('completed') is True and not workout.completed_at:
        workout.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workout)
    
    return workout
