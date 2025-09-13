"""
Database models and schema for the Workout Video Search System.
Uses SQLAlchemy with SQLite for simple, file-based storage.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from .config import DATABASE_URL, BASE_DIR
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WorkoutVideoModel(Base):
    """Database model for workout videos."""
    __tablename__ = "workout_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    original_title = Column(String, default="")
    file_path = Column(String, nullable=True)
    video_url = Column(String, nullable=True)  # Google Drive or video URL
    duration = Column(Integer, nullable=True)  # in seconds
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # List of tags
    keywords = Column(JSON, default=list)  # List of keywords for search
    equipment_needed = Column(JSON, default=list)  # List of equipment
    difficulty_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "original_title": self.original_title,
            "file_path": self.file_path,
            "video_url": self.video_url,
            "duration": self.duration,
            "description": self.description,
            "tags": self.tags if self.tags else [],
            "keywords": self.keywords if self.keywords else [],
            "equipment_needed": self.equipment_needed if self.equipment_needed else [],
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SearchCacheModel(Base):
    """Database model for caching search indices."""
    __tablename__ = "search_cache"
    
    id = Column(Integer, primary_key=True)
    cache_type = Column(String, nullable=False, index=True)  # tfidf, keyword, etc.
    cache_data = Column(Text, nullable=False)  # JSON serialized data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    """Database management utilities."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
        
    def migrate_from_json(self, json_file_path: str) -> int:
        """Migrate existing JSON data to database."""
        from .models import VideoDatabase  # Import existing model
        
        # Load existing JSON data
        json_path = Path(json_file_path)
        if not json_path.exists():
            return 0
            
        # Load the old database
        old_db = VideoDatabase.load_from_file(str(json_path))
        
        # Create database session
        session = self.get_session()
        migrated_count = 0
        
        try:
            for video in old_db.videos:
                # Check if video already exists
                existing = session.query(WorkoutVideoModel).filter(
                    WorkoutVideoModel.title == video.title,
                    WorkoutVideoModel.category == video.category
                ).first()
                
                if not existing:
                    # Create new database video
                    db_video = WorkoutVideoModel(
                        title=video.title,
                        category=video.category,
                        original_title=video.original_title,
                        file_path=video.file_path,
                        duration=video.duration,
                        description=video.description,
                        tags=video.tags if video.tags else [],
                        keywords=video.keywords if video.keywords else [],
                        equipment_needed=video.equipment_needed if video.equipment_needed else [],
                        difficulty_level=video.difficulty_level,
                        created_at=video.created_at,
                        updated_at=video.updated_at
                    )
                    session.add(db_video)
                    migrated_count += 1
            
            session.commit()
            return migrated_count
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_videos(self) -> List[WorkoutVideoModel]:
        """Get all videos from database."""
        session = self.get_session()
        try:
            return session.query(WorkoutVideoModel).all()
        finally:
            session.close()
    
    def get_video_by_id(self, video_id: int) -> Optional[WorkoutVideoModel]:
        """Get a specific video by ID."""
        session = self.get_session()
        try:
            return session.query(WorkoutVideoModel).filter(WorkoutVideoModel.id == video_id).first()
        finally:
            session.close()
    
    def search_videos(self, query: str, category: Optional[str] = None, limit: int = 50) -> List[WorkoutVideoModel]:
        """Basic database search (will be enhanced by search engine)."""
        session = self.get_session()
        try:
            db_query = session.query(WorkoutVideoModel)
            
            if query:
                # Basic text search in title and description
                search_filter = f"%{query.lower()}%"
                db_query = db_query.filter(
                    WorkoutVideoModel.title.ilike(search_filter) |
                    WorkoutVideoModel.description.ilike(search_filter)
                )
            
            if category:
                db_query = db_query.filter(WorkoutVideoModel.category == category)
            
            return db_query.limit(limit).all()
        finally:
            session.close()
    
    def add_video(self, video_data: Dict[str, Any]) -> WorkoutVideoModel:
        """Add a new video to the database."""
        session = self.get_session()
        try:
            video = WorkoutVideoModel(**video_data)
            session.add(video)
            session.commit()
            session.refresh(video)  # Get the ID
            return video
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_video(self, video_id: int, video_data: Dict[str, Any]) -> Optional[WorkoutVideoModel]:
        """Update an existing video."""
        session = self.get_session()
        try:
            video = session.query(WorkoutVideoModel).filter(WorkoutVideoModel.id == video_id).first()
            if video:
                for key, value in video_data.items():
                    setattr(video, key, value)
                video.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(video)
            return video
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_video(self, video_id: int) -> bool:
        """Delete a video from the database."""
        session = self.get_session()
        try:
            video = session.query(WorkoutVideoModel).filter(WorkoutVideoModel.id == video_id).first()
            if video:
                session.delete(video)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        session = self.get_session()
        try:
            result = session.query(WorkoutVideoModel.category).distinct().all()
            return [r[0] for r in result]
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self.get_session()
        try:
            total_videos = session.query(WorkoutVideoModel).count()
            categories = self.get_categories()
            
            # Count videos per category
            category_counts = {}
            for category in categories:
                count = session.query(WorkoutVideoModel).filter(
                    WorkoutVideoModel.category == category
                ).count()
                category_counts[category] = count
            
            return {
                "total_videos": total_videos,
                "total_categories": len(categories),
                "categories": categories,
                "category_counts": category_counts
            }
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()

def get_database():
    """Get the database manager instance."""
    return db_manager

def get_db():
    """Get a database session. This is used as a dependency in FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize the database and create tables."""
    db_manager.create_tables()
