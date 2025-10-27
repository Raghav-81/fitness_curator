"""
API endpoints for workout creator functionality.
Handles clients, workout plans, and plan exercises.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db, Base, engine
from app.models import Client, WorkoutPlan, PlanExercise

# Create tables
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["workout_creator"])

# Pydantic models for API

class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    age: Optional[int] = None
    goals: Optional[str] = None
    trainer_notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    goals: Optional[str] = None
    trainer_notes: Optional[str] = None

class PlanExerciseCreate(BaseModel):
    video_id: int
    day: str
    sets: Optional[int] = None
    reps: Optional[str] = None
    notes: Optional[str] = None
    order_index: int = 0

class WorkoutPlanCreate(BaseModel):
    client_id: int
    plan_name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_template: bool = False
    day_type: str = "day_number"  # "day_number" or "day_of_week"
    number_of_days: Optional[int] = None  # Number of days in split
    weeks_duration: Optional[int] = None  # Number of weeks
    day_labels: Optional[dict] = None  # Custom day labels {"1": "Push Day", "2": "Pull Day"}
    exercises: List[PlanExerciseCreate] = []

class WorkoutPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_template: Optional[bool] = None
    day_type: Optional[str] = None

class ExerciseTrackingUpdate(BaseModel):
    completed: Optional[bool] = None
    weight_logged: Optional[List[float]] = None


# Client endpoints

@router.post("/clients")
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client."""
    # Check if email already exists
    existing = db.query(Client).filter(Client.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client with this email already exists")
    
    new_client = Client(**client.dict())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    
    return new_client.to_dict()

@router.get("/clients")
async def get_clients(db: Session = Depends(get_db)):
    """Get all clients."""
    clients = db.query(Client).order_by(Client.created_at.desc()).all()
    return [client.to_dict() for client in clients]

@router.get("/clients/{client_id}")
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """Get a specific client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.to_dict()

@router.put("/clients/{client_id}")
async def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    """Update a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for key, value in client_update.dict(exclude_unset=True).items():
        setattr(client, key, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    
    return client.to_dict()

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Delete a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    
    return {"message": "Client deleted successfully"}


# Workout Plan endpoints

@router.post("/workout-plans")
async def create_workout_plan(plan: WorkoutPlanCreate, db: Session = Depends(get_db)):
    """Create a new workout plan with exercises."""
    # Verify client exists
    client = db.query(Client).filter(Client.id == plan.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Create plan
    new_plan = WorkoutPlan(
        client_id=plan.client_id,
        plan_name=plan.plan_name,
        description=plan.description,
        start_date=plan.start_date,
        end_date=plan.end_date,
        is_template=plan.is_template,
        day_type=plan.day_type,
        number_of_days=plan.number_of_days,
        weeks_duration=plan.weeks_duration,
        day_labels=plan.day_labels
    )
    
    # Also set title for backward compatibility with old schema
    if hasattr(new_plan, 'title'):
        new_plan.title = plan.plan_name
    
    # Generate share token
    new_plan.generate_share_token()
    
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    # Add exercises
    for exercise_data in plan.exercises:
        exercise = PlanExercise(
            plan_id=new_plan.id,
            **exercise_data.dict()
        )
        db.add(exercise)
    
    db.commit()
    db.refresh(new_plan)
    
    return new_plan.to_dict(include_exercises=True)

@router.get("/workout-plans")
async def get_workout_plans(
    client_id: Optional[int] = None,
    is_template: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all workout plans, optionally filtered by client or template status."""
    query = db.query(WorkoutPlan)
    
    if client_id is not None:
        query = query.filter(WorkoutPlan.client_id == client_id)
    
    if is_template is not None:
        query = query.filter(WorkoutPlan.is_template == is_template)
    
    plans = query.order_by(WorkoutPlan.created_at.desc()).all()
    return [plan.to_dict(include_exercises=False) for plan in plans]

@router.get("/workout-plans/{plan_id}")
async def get_workout_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific workout plan with all exercises."""
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return plan.to_dict(include_exercises=True)

@router.get("/workout-plans/share/{share_token}")
async def get_plan_by_share_token(share_token: str, db: Session = Depends(get_db)):
    """Get a workout plan by its shareable token (for clients)."""
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.share_token == share_token).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return plan.to_dict(include_exercises=True)

@router.put("/workout-plans/{plan_id}")
async def update_workout_plan(
    plan_id: int,
    plan_update: WorkoutPlanCreate,  # Use full plan data including exercises
    db: Session = Depends(get_db)
):
    """Update a workout plan with exercises."""
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    # Update plan fields
    plan.plan_name = plan_update.plan_name
    plan.description = plan_update.description
    plan.start_date = plan_update.start_date
    plan.end_date = plan_update.end_date
    plan.day_type = plan_update.day_type
    plan.is_template = plan_update.is_template
    plan.number_of_days = plan_update.number_of_days
    plan.weeks_duration = plan_update.weeks_duration
    plan.day_labels = plan_update.day_labels
    plan.updated_at = datetime.utcnow()
    
    # Update title for backward compatibility
    if hasattr(plan, 'title'):
        plan.title = plan_update.plan_name
    
    # Delete existing exercises
    db.query(PlanExercise).filter(PlanExercise.plan_id == plan_id).delete()
    
    # Add new exercises
    for exercise_data in plan_update.exercises:
        exercise = PlanExercise(
            plan_id=plan.id,
            **exercise_data.dict()
        )
        db.add(exercise)
    
    db.commit()
    db.refresh(plan)
    
    return plan.to_dict(include_exercises=True)

@router.delete("/workout-plans/{plan_id}")
async def delete_workout_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a workout plan."""
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    db.delete(plan)
    db.commit()
    
    return {"message": "Workout plan deleted successfully"}


# Exercise endpoints

@router.post("/workout-plans/{plan_id}/exercises")
async def add_exercise_to_plan(
    plan_id: int,
    exercise: PlanExerciseCreate,
    db: Session = Depends(get_db)
):
    """Add an exercise to a workout plan."""
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    new_exercise = PlanExercise(
        plan_id=plan_id,
        **exercise.dict()
    )
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)
    
    return new_exercise.to_dict()

@router.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    exercise_update: PlanExerciseCreate,
    db: Session = Depends(get_db)
):
    """Update an exercise in a plan."""
    exercise = db.query(PlanExercise).filter(PlanExercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    for key, value in exercise_update.dict(exclude_unset=True).items():
        setattr(exercise, key, value)
    
    db.commit()
    db.refresh(exercise)
    
    return exercise.to_dict()

@router.delete("/exercises/{exercise_id}")
async def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Delete an exercise from a plan."""
    exercise = db.query(PlanExercise).filter(PlanExercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    db.delete(exercise)
    db.commit()
    
    return {"message": "Exercise deleted successfully"}

@router.patch("/exercises/{exercise_id}/tracking")
async def update_exercise_tracking(
    exercise_id: int,
    tracking: ExerciseTrackingUpdate,
    db: Session = Depends(get_db)
):
    """Update exercise tracking (completion, weight logged) - for client use."""
    exercise = db.query(PlanExercise).filter(PlanExercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if tracking.completed is not None:
        exercise.completed = tracking.completed
    
    if tracking.weight_logged is not None:
        exercise.weight_logged = tracking.weight_logged
    
    db.commit()
    db.refresh(exercise)
    
    return exercise.to_dict()
