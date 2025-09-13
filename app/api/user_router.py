"""
User management API endpoints for the Workout Video Search System.
Handles CRUD operations for users and trainer-client relationships.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

import sys
from pathlib import Path
import logging

from app.auth import get_db, get_current_active_user
from app.models.user import User, ClientTrainerRelationship

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["users"], prefix="/users")

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    user_type: str
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    specializations: Optional[str] = None
    years_experience: Optional[int] = None
    fitness_goals: Optional[str] = None
    health_conditions: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    user_type: str
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Trainer specific fields
    specializations: Optional[str] = None
    years_experience: Optional[int] = None
    
    # Client specific fields
    fitness_goals: Optional[str] = None
    health_conditions: Optional[str] = None
    
    class Config:
        orm_mode = True

class RelationshipCreate(BaseModel):
    client_id: int
    
class RelationshipResponse(BaseModel):
    id: int
    client_id: int
    trainer_id: int
    status: str
    
    class Config:
        orm_mode = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    
    class Config:
        orm_mode = True

# Endpoints
@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile."""
    # Update user fields
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=UserListResponse)
async def read_users(
    user_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a list of users with optional filtering."""
    # Start with base query
    query = db.query(User)
    
    # Apply filters
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Get results
    users = query.all()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page
    }

# Trainer-client relationship endpoints
@router.post("/trainer/clients", response_model=RelationshipResponse)
async def create_client_relationship(
    relationship: RelationshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new trainer-client relationship."""
    # Check if current user is a trainer
    if current_user.user_type != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can create client relationships"
        )
    
    # Check if client exists
    client = db.query(User).filter(
        User.id == relationship.client_id,
        User.user_type == "client"
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check if relationship already exists
    existing_relationship = db.query(ClientTrainerRelationship).filter(
        ClientTrainerRelationship.client_id == relationship.client_id,
        ClientTrainerRelationship.trainer_id == current_user.id
    ).first()
    
    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship already exists"
        )
    
    # Create new relationship
    new_relationship = ClientTrainerRelationship(
        client_id=relationship.client_id,
        trainer_id=current_user.id
    )
    
    db.add(new_relationship)
    db.commit()
    db.refresh(new_relationship)
    
    return new_relationship

@router.get("/trainer/clients", response_model=UserListResponse)
async def read_trainer_clients(
    status: Optional[str] = "active",
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a list of trainer's clients."""
    # Check if current user is a trainer
    if current_user.user_type != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can access client lists"
        )
    
    # Get client IDs from relationships
    relationship_query = db.query(ClientTrainerRelationship.client_id).filter(
        ClientTrainerRelationship.trainer_id == current_user.id
    )
    
    if status:
        relationship_query = relationship_query.filter(
            ClientTrainerRelationship.status == status
        )
    
    client_ids = [r.client_id for r in relationship_query.all()]
    
    # Get clients
    query = db.query(User).filter(
        User.id.in_(client_ids)
    )
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Get results
    clients = query.all()
    
    return {
        "users": clients,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/client/trainers", response_model=UserListResponse)
async def read_client_trainers(
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a list of client's trainers."""
    # Check if current user is a client
    if current_user.user_type != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can access trainer lists"
        )
    
    # Get trainer IDs from relationships
    relationship_query = db.query(ClientTrainerRelationship.trainer_id).filter(
        ClientTrainerRelationship.client_id == current_user.id
    )
    
    if status:
        relationship_query = relationship_query.filter(
            ClientTrainerRelationship.status == status
        )
    
    trainer_ids = [r.trainer_id for r in relationship_query.all()]
    
    # Get trainers
    trainers = db.query(User).filter(User.id.in_(trainer_ids)).all()
    
    return {
        "users": trainers,
        "total": len(trainers),
        "page": 1,
        "per_page": len(trainers)
    }
