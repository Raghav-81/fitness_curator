"""
FastAPI backend for Fitness Curator - Video Search Module Only.
Provides REST API endpoints for video management and search.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path
import logging

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import database models and utilities
from app.database import DatabaseManager, WorkoutVideoModel, init_database
from app.search_engine_db import DatabaseSearchEngine
from app.utils import extract_keywords, extract_equipment_from_title, normalize_category

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fitness Curator - Video Search",
    description="Intelligent workout video search system with TF-IDF, keyword, and fuzzy matching",
    version="1.0.0"
)

# Get the current file's directory
current_dir = Path(__file__).parent.parent

# Set up templates
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# Mount static files for the web frontend
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_database()
db_manager = DatabaseManager()
search_engine = DatabaseSearchEngine(db_manager)

# Pydantic models for API
class VideoCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    duration: Optional[int] = None
    tags: List[str] = []
    difficulty_level: Optional[str] = None

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    duration: Optional[int] = None
    tags: List[str] = []
    difficulty_level: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = 10
    min_score: float = 0.0

class BulkVideoCreate(BaseModel):
    videos: List[VideoCreate]

# API Routes

@app.get("/")
async def root(request: Request):
    """Root endpoint - serves the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {"message": "Fitness Curator Video Search API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}

# Video Management Endpoints

@app.get("/api/videos", response_model=List[Dict[str, Any]])
async def get_all_videos():
    """Get all videos."""
    try:
        videos = db_manager.get_all_videos()
        return [video.to_dict() for video in videos]
    except Exception as e:
        logging.error(f"Error getting videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to get videos")

@app.get("/api/videos/{video_id}")
async def get_video(video_id: int):
    """Get a specific video by ID."""
    video = db_manager.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video.to_dict()

@app.post("/api/videos")
async def create_video(video: VideoCreate):
    """Create a new video."""
    try:
        # Extract keywords and equipment automatically
        keywords = extract_keywords(video.title, video.category)
        equipment = extract_equipment_from_title(video.title)
        
        video_data = {
            "title": video.title,
            "category": normalize_category(video.category),
            "description": video.description,
            "file_path": video.file_path,
            "duration": video.duration,
            "tags": video.tags,
            "keywords": keywords,
            "equipment_needed": equipment,
            "difficulty_level": video.difficulty_level,
            "original_title": video.title
        }
        
        new_video = db_manager.add_video(video_data)
        
        # Refresh search indices
        search_engine.refresh_indices()
        
        return new_video.to_dict()
    except Exception as e:
        logging.error(f"Error creating video: {e}")
        raise HTTPException(status_code=500, detail="Failed to create video")

@app.put("/api/videos/{video_id}")
async def update_video(video_id: int, video: VideoUpdate):
    """Update an existing video."""
    try:
        # Get current video
        current_video = db_manager.get_video_by_id(video_id)
        if not current_video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Prepare update data
        update_data = {}
        if video.title is not None:
            update_data["title"] = video.title
            update_data["keywords"] = extract_keywords(video.title, video.category or current_video.category)
            update_data["equipment_needed"] = extract_equipment_from_title(video.title)
        
        if video.category is not None:
            update_data["category"] = normalize_category(video.category)
            
        if video.description is not None:
            update_data["description"] = video.description
            
        if video.file_path is not None:
            update_data["file_path"] = video.file_path
            
        if video.duration is not None:
            update_data["duration"] = video.duration
            
        if video.tags is not None:
            update_data["tags"] = video.tags
            
        if video.difficulty_level is not None:
            update_data["difficulty_level"] = video.difficulty_level
        
        updated_video = db_manager.update_video(video_id, update_data)
        
        # Refresh search indices
        search_engine.refresh_indices()
        
        return updated_video.to_dict()
    except Exception as e:
        logging.error(f"Error updating video: {e}")
        raise HTTPException(status_code=500, detail="Failed to update video")

@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: int):
    """Delete a video."""
    try:
        success = db_manager.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Refresh search indices
        search_engine.refresh_indices()
        
        return {"message": "Video deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete video")

# Bulk Operations

@app.post("/api/videos/bulk")
async def create_videos_bulk(videos: BulkVideoCreate):
    """Create multiple videos at once."""
    try:
        created_videos = []
        for video_data in videos.videos:
            # Extract keywords and equipment
            keywords = extract_keywords(video_data.title, video_data.category)
            equipment = extract_equipment_from_title(video_data.title)
            
            video_dict = {
                "title": video_data.title,
                "category": normalize_category(video_data.category),
                "description": video_data.description,
                "file_path": video_data.file_path,
                "duration": video_data.duration,
                "tags": video_data.tags,
                "keywords": keywords,
                "equipment_needed": equipment,
                "difficulty_level": video_data.difficulty_level,
                "original_title": video_data.title
            }
            
            new_video = db_manager.add_video(video_dict)
            created_videos.append(new_video.to_dict())
        
        # Refresh search indices once after all additions
        search_engine.refresh_indices()
        
        return {
            "message": f"Successfully created {len(created_videos)} videos",
            "videos": created_videos
        }
    except Exception as e:
        logging.error(f"Error in bulk create: {e}")
        raise HTTPException(status_code=500, detail="Failed to create videos")

# Search Endpoints

@app.post("/api/search")
async def search_videos(search_request: SearchRequest):
    """Search for videos using the advanced search engine."""
    try:
        results = search_engine.search(
            query=search_request.query,
            category_filter=search_request.category,
            top_k=search_request.top_k,
            min_score=search_request.min_score
        )
        
        return {
            "query": search_request.query,
            "total_results": len(results),
            "results": [
                {
                    "video": result.video.to_dict(),
                    "score": result.score,
                    "method": result.method,
                    "match_details": result.match_details
                }
                for result in results
            ]
        }
    except Exception as e:
        logging.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/search/suggestions/{partial_query}")
async def get_search_suggestions(partial_query: str, max_suggestions: int = 5):
    """Get search suggestions based on partial query."""
    try:
        suggestions = search_engine.get_search_suggestions(partial_query, max_suggestions)
        return {"suggestions": suggestions}
    except Exception as e:
        logging.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

# Category Management

@app.get("/api/categories")
async def get_categories():
    """Get all available categories."""
    try:
        categories = db_manager.get_categories()
        return {"categories": categories}
    except Exception as e:
        logging.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")

# Statistics

@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        db_stats = db_manager.get_stats()
        search_stats = search_engine.get_stats()
        
        return {
            "database": db_stats,
            "search_engine": search_stats,
            "system": {
                "api_version": "1.0.0",
                "database_type": "SQLite"
            }
        }
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

# Data Migration

@app.post("/api/migrate")
async def migrate_from_json():
    """Migrate data from existing JSON database."""
    try:
        json_path = Path(__file__).parent.parent / "data" / "workout_videos.json"
        migrated_count = db_manager.migrate_from_json(str(json_path))
        
        # Refresh search indices after migration
        search_engine.refresh_indices()
        
        return {
            "message": f"Successfully migrated {migrated_count} videos from JSON to database",
            "migrated_count": migrated_count
        }
    except Exception as e:
        logging.error(f"Error in migration: {e}")
        raise HTTPException(status_code=500, detail="Migration failed")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
