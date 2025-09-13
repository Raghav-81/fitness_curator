"""
Authentication API endpoints for the Workout Video Search System.
Handles user registration, login, and Google OAuth2 authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
import logging

from google.oauth2 import id_token
from google.auth.transport import requests

from app.models.user import User
from app.database import get_db
from app.auth import (
    authenticate_user, 
    authenticate_google_user, 
    create_access_token, 
    get_password_hash,
    get_current_user,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["authentication"], prefix="/auth")

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_type: str
    email: str
    full_name: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    user_type: str = "client"  # Default to client

class SimulatedUser(BaseModel):
    email: EmailStr
    full_name: str

class GoogleAuthRequest(BaseModel):
    token: str
    user_type: Optional[str] = "client"
    simulated_user: Optional[SimulatedUser] = None # For demo purposes

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    user_type: str
    profile_image: Optional[str] = None

# Endpoints
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    # Check if user exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        user_type=user_data.user_type
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "user_type": db_user.user_type,
        "email": db_user.email,
        "full_name": db_user.full_name
    }

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username (email) and password."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_type": user.user_type,
        "email": user.email,
        "full_name": user.full_name
    }

@router.post("/google", response_model=Token)
async def google_login(
    google_auth: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """Login or register with a Google OAuth2 token (with simulation support)."""
    user = None
    try:
        if google_auth.simulated_user:
            # --- SIMULATED FLOW ---
            # For demo purposes, we accept user data directly
            simulated_data = google_auth.simulated_user
            user = db.query(User).filter(User.email == simulated_data.email).first()
            if not user:
                # Create a new user if they don't exist
                user = User(
                    email=simulated_data.email,
                    full_name=simulated_data.full_name,
                    user_type=google_auth.user_type,
                    hashed_password=get_password_hash(os.urandom(24).hex()) # Secure random password
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        else:
            # --- REAL GOOGLE AUTH FLOW ---
            user = await authenticate_google_user(db, google_auth.token, google_auth.user_type)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not authenticate user",
            )
        
        # If user type was provided during registration, ensure it's set
        if google_auth.user_type and user.user_type != google_auth.user_type:
            user.user_type = google_auth.user_type
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "user_type": user.user_type,
            "email": user.email,
            "full_name": user.full_name
        }
    except Exception as e:
        logger.error(f"Google authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type,
        "profile_image": current_user.profile_image
    }
