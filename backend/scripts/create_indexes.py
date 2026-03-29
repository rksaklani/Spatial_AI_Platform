"""
Create database indexes for optimal query performance.
Run this script once to create all necessary indexes.

Usage:
    python backend/scripts/create_indexes.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import get_db
import structlog

logger = structlog.get_logger(__name__)


async def create_indexes():
    """Create all necessary database indexes for optimal performance."""
    
    # Initialize database connection
    from utils.database import Database
    await Database.connect()
    
    db = await get_db()
    
    # Users collection indexes
    logger.info("Creating indexes for users collection...")
    
    # Email index (unique) - critical for fast login
    await db.users.create_index("email", unique=True)
    logger.info("✓ Created unique index on users.email")
    
    # Active users index - for filtering
    await db.users.create_index("is_active")
    logger.info("✓ Created index on users.is_active")
    
    # Created at index - for sorting
    await db.users.create_index("created_at")
    logger.info("✓ Created index on users.created_at")
    
    # Scenes collection indexes
    logger.info("Creating indexes for scenes collection...")
    
    # Organization ID index - for tenant isolation
    await db.scenes.create_index("organization_id")
    logger.info("✓ Created index on scenes.organization_id")
    
    # Status index - for filtering
    await db.scenes.create_index("status")
    logger.info("✓ Created index on scenes.status")
    
    # Created at index - for sorting
    await db.scenes.create_index("created_at")
    logger.info("✓ Created index on scenes.created_at")
    
    # Compound index for organization + status queries
    await db.scenes.create_index([("organization_id", 1), ("status", 1)])
    logger.info("✓ Created compound index on scenes.organization_id + status")
    
    # Photos collection indexes
    logger.info("Creating indexes for photos collection...")
    
    # Scene ID index - for fetching photos by scene
    await db.photos.create_index("scene_id")
    logger.info("✓ Created index on photos.scene_id")
    
    # Aligned status index - for filtering
    await db.photos.create_index("aligned")
    logger.info("✓ Created index on photos.aligned")
    
    # Annotations collection indexes
    logger.info("Creating indexes for annotations collection...")
    
    # Scene ID index
    await db.annotations.create_index("scene_id")
    logger.info("✓ Created index on annotations.scene_id")
    
    # User ID index
    await db.annotations.create_index("user_id")
    logger.info("✓ Created index on annotations.user_id")
    
    # Organizations collection indexes
    logger.info("Creating indexes for organizations collection...")
    
    # Name index (unique)
    await db.organizations.create_index("name", unique=True)
    logger.info("✓ Created unique index on organizations.name")
    
    # Processing jobs collection indexes
    logger.info("Creating indexes for processing_jobs collection...")
    
    # Scene ID index
    await db.processing_jobs.create_index("scene_id")
    logger.info("✓ Created index on processing_jobs.scene_id")
    
    # Status index
    await db.processing_jobs.create_index("status")
    logger.info("✓ Created index on processing_jobs.status")
    
    # Compound index for scene + status queries
    await db.processing_jobs.create_index([("scene_id", 1), ("status", 1)])
    logger.info("✓ Created compound index on processing_jobs.scene_id + status")
    
    logger.info("✅ All indexes created successfully!")
    
    # List all indexes for verification
    logger.info("\nVerifying indexes...")
    for collection_name in ["users", "scenes", "photos", "annotations", "organizations", "processing_jobs"]:
        collection = db[collection_name]
        indexes = await collection.index_information()
        logger.info(f"{collection_name} indexes:", indexes=list(indexes.keys()))
    
    # Disconnect from database
    from utils.database import Database
    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(create_indexes())
