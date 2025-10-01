#!/usr/bin/env python3
"""
Database setup script for MD-Linked-Secrets
Run this script to create all necessary database tables and indexes.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from app.core.database import engine
    from app.models import Base
    from sqlalchemy import text
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def setup_database():
        """Create all database tables and indexes"""
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully!")
            
            # Create additional indexes for better performance
            logger.info("Creating additional indexes...")
            with engine.connect() as conn:
                # Index for faster variable lookups
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_env_vars_linked_to 
                    ON env_vars(linked_to) 
                    WHERE linked_to IS NOT NULL;
                """))
                
                # Index for faster concatenated variable lookups
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_env_vars_concat_parts 
                    ON env_vars(concat_parts) 
                    WHERE concat_parts IS NOT NULL;
                """))
                
                # Index for export lookups by project
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_env_exports_project_id 
                    ON env_exports(project_id);
                """))
                
                # Index for git-related queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_env_exports_git_branch 
                    ON env_exports(git_branch) 
                    WHERE git_branch IS NOT NULL;
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_env_exports_is_git_repo 
                    ON env_exports(is_git_repo);
                """))
                
                conn.commit()
                logger.info("✅ Additional indexes created successfully!")
            
            logger.info("🎉 Database setup completed successfully!")
            logger.info("You can now start the application with:")
            logger.info("  pm2 start ecosystem.config.js")
            logger.info("  or")
            logger.info("  python -m uvicorn backend.main:app --reload --port 8088")
            
        except Exception as e:
            logger.error(f"❌ Error setting up database: {e}")
            sys.exit(1)

    if __name__ == "__main__":
        setup_database()

except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure you have installed all dependencies:")
    print("  pip install -r backend/requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
