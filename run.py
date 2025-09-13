"""
Fitness Curator - Main entry point
Run this script to start the application
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Run the FastAPI application with uvicorn server"""
    # Get the directory of this file
    root_dir = Path(__file__).parent
    
    # Add the directory to Python path
    import sys
    sys.path.insert(0, str(root_dir))
    
    print("Starting Fitness Curator application...")
    print(f"Root directory: {root_dir}")
    print("Access the application at: http://localhost:8000")
    print("Access the API documentation at: http://localhost:8000/docs")
    
    # Run uvicorn server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
