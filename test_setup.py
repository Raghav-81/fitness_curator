"""
Diagnostic script to test the database setup and core functionality
of the Fitness Curator application.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import configuration
from app.config import DATABASE_URL, BASE_DIR

print("Step 1: Configuration Check")
print(f"BASE_DIR: {BASE_DIR}")
print(f"DATABASE_URL: {DATABASE_URL}")
print(f"Current directory: {current_dir}")
print("Configuration check complete!\n")

# Test database setup
print("Step 2: Database Setup")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("Database connection established!")
print(f"Engine: {engine}")
print("Database setup complete!\n")

# Test model creation
print("Step 3: Model Creation")
from app.models.user import User, ClientTrainerRelationship
from app.models.plan import WorkoutPlan, PlanTemplate, PlanSection, PlanWorkout
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Create all tables
print("Creating tables...")
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print("Tables created successfully!\n")

# Test database session
print("Step 4: Database Session")
db = SessionLocal()
try:
    # Check if we can query users
    users = db.query(User).all()
    print(f"Found {len(users)} users in the database")
    
    # Check if we can create a user
    test_user = User(
        email="test@example.com",
        hashed_password="test_hash",
        full_name="Test User",
        user_type="client"
    )
    db.add(test_user)
    db.commit()
    print("Test user created successfully!")
    
    # Query the user back
    queried_user = db.query(User).filter(User.email == "test@example.com").first()
    print(f"Retrieved user: {queried_user.full_name} ({queried_user.email})")
    
    # Clean up
    db.delete(queried_user)
    db.commit()
    print("Test user removed successfully!")
    
finally:
    db.close()

print("Database session test complete!\n")

print("All diagnostic tests passed! Your setup is working correctly.")
