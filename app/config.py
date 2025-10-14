"""
Configuration settings for the Fitness Curator application.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
APP_DIR = Path(__file__).parent

# Database
# Prefer explicit DB path if provided, else fall back to project DB
DEFAULT_DB_PATH = str(BASE_DIR / "workout_videos.db")
EXTERNAL_DB_PATH = "/home/streamoid/Desktop/Raghav/Personal/data/workout_videos.db"

# If the external DB exists, use it by default unless DATABASE_URL is set
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    if os.path.exists(EXTERNAL_DB_PATH):
        # Absolute sqlite path requires four slashes
        DATABASE_URL = f"sqlite:////{EXTERNAL_DB_PATH}"
    else:
        DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

print(f"Using database: {DATABASE_URL}")

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_database.sqlite3")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Application settings
APP_NAME = "Fitness Curator"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "Intelligent fitness system with workout video search and trainer-client support"

# File paths
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for dir_path in [STATIC_DIR, TEMPLATES_DIR, DATA_DIR, LOG_DIR]:
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / "app.log"
