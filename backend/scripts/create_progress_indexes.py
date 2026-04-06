"""
Create MongoDB indexes for progress tracking performance.

This script creates indexes on the processing_jobs collection to optimize
progress queries and scene job lookups.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from utils.config import settings


async def create_indexes():
    """Create MongoDB indexes for processing_jobs collection."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    try:
        print("Creating indexes on processing_jobs collection...")
        
        # Index on scene_id for fast scene job lookups
        await db.processing_jobs.create_index([("scene_id", 1)])
        print("✓ Created index on scene_id")
        
        # Compound index on status and updated_at for active job queries
        await db.processing_jobs.create_index([("status", 1), ("updated_at", -1)])
        print("✓ Created compound index on (status, updated_at)")
        
        # Compound index on scene_id and created_at for scene job history
        await db.processing_jobs.create_index([("scene_id", 1), ("created_at", -1)])
        print("✓ Created compound index on (scene_id, created_at)")
        
        print("\nAll indexes created successfully!")
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
