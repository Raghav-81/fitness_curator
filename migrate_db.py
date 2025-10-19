"""
Database Migration Script
Updates the database schema to match the latest models.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from app.database import Base
from app.config import DATABASE_URL
from app.models import Client, WorkoutPlan, PlanExercise

def migrate_database():
    """Migrate database to latest schema."""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print(f"🔄 Migrating database: {DATABASE_URL}")
    print("=" * 60)
    
    # Check if tables exist
    existing_tables = inspector.get_table_names()
    print(f"📊 Existing tables: {existing_tables}")
    
    with engine.connect() as conn:
        # Migrate workout_plans table
        if 'workout_plans' in existing_tables:
            columns = {col['name']: col for col in inspector.get_columns('workout_plans')}
            print(f"\n📋 workout_plans columns: {list(columns.keys())}")
            
            # Add missing columns
            if 'plan_name' not in columns:
                print("  ➕ Adding plan_name column...")
                conn.execute(text("ALTER TABLE workout_plans ADD COLUMN plan_name VARCHAR(255)"))
                conn.commit()
            
            if 'day_type' not in columns:
                print("  ➕ Adding day_type column...")
                conn.execute(text("ALTER TABLE workout_plans ADD COLUMN day_type VARCHAR(20) DEFAULT 'day_number'"))
                conn.commit()
            
            if 'share_token' not in columns:
                print("  ➕ Adding share_token column...")
                conn.execute(text("ALTER TABLE workout_plans ADD COLUMN share_token VARCHAR(64)"))
                conn.commit()
            
            if 'is_template' not in columns:
                print("  ➕ Adding is_template column...")
                conn.execute(text("ALTER TABLE workout_plans ADD COLUMN is_template BOOLEAN DEFAULT 1"))
                conn.commit()
            
            # Update title column - sync with plan_name and make nullable
            if 'title' in columns:
                print("  🔧 Syncing title with plan_name...")
                # First, update existing records
                conn.execute(text("UPDATE workout_plans SET title = plan_name WHERE plan_name IS NOT NULL AND title IS NULL"))
                conn.commit()
                
                # SQLite doesn't support ALTER COLUMN, so we note it
                print("  🔧 Note: title column exists - synced with plan_name")
                print("  ℹ️  SQLite limitation: Cannot modify column constraints directly")
        
        # Migrate plan_exercises table
        if 'plan_exercises' in existing_tables:
            columns = {col['name']: col for col in inspector.get_columns('plan_exercises')}
            print(f"\n📋 plan_exercises columns: {list(columns.keys())}")
            
            # Add missing columns
            if 'section' not in columns:
                print("  ➕ Adding section column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN section VARCHAR(20)"))
                conn.commit()
            
            if 'time' not in columns:
                print("  ➕ Adding time column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN time INTEGER"))
                conn.commit()
            
            if 'time_unit' not in columns:
                print("  ➕ Adding time_unit column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN time_unit VARCHAR(10)"))
                conn.commit()
            
            if 'is_custom' not in columns:
                print("  ➕ Adding is_custom column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN is_custom BOOLEAN DEFAULT 0"))
                conn.commit()
            
            if 'custom_name' not in columns:
                print("  ➕ Adding custom_name column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN custom_name VARCHAR(255)"))
                conn.commit()
            
            if 'custom_youtube_url' not in columns:
                print("  ➕ Adding custom_youtube_url column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN custom_youtube_url VARCHAR(500)"))
                conn.commit()
            
            if 'custom_equipment' not in columns:
                print("  ➕ Adding custom_equipment column...")
                conn.execute(text("ALTER TABLE plan_exercises ADD COLUMN custom_equipment VARCHAR(255)"))
                conn.commit()
            
            # Make video_id nullable for custom exercises
            print("  🔧 Note: video_id column should be nullable for custom exercises")
    
    print("\n✅ Migration completed successfully!")
    print("=" * 60)
    print("\n🔄 Please restart the application for changes to take effect.")

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
