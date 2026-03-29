"""MongoDB database connection and initialization utilities."""
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid
import structlog

from utils.config import settings

logger = structlog.get_logger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Establish connection to MongoDB."""
        try:
            logger.info("Connecting to MongoDB", url=settings.mongodb_url)
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=100,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.database_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB", database=settings.database_name)
            
        except Exception as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return cls.db


def init_database_sync():
    """
    Initialize MongoDB database with collections and indexes.
    This function uses synchronous PyMongo for setup operations.
    """
    try:
        logger.info("Initializing MongoDB database", url=settings.mongodb_url)
        
        # Connect using synchronous client for initialization
        client = MongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000
        )
        db = client[settings.database_name]
        
        # Test connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB for initialization")
        
        # Define collections to create
        collections = [
            'organizations',
            'organization_members',
            'users',
            'scenes',
            'processing_jobs',
            'scene_tiles',
            'annotations',
            'guided_tours',
            'share_tokens',
            'scene_access_logs',
            'scene_objects'
        ]
        
        # Create collections if they don't exist
        existing_collections = db.list_collection_names()
        for collection_name in collections:
            if collection_name not in existing_collections:
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
        
        # Create indexes
        logger.info("Creating indexes...")
        
        # Organizations collection indexes
        db.organizations.create_index([("name", ASCENDING)])
        db.organizations.create_index([("owner_id", ASCENDING)])
        db.organizations.create_index([("is_active", ASCENDING)])
        db.organizations.create_index([("created_at", DESCENDING)])
        
        # Organization members collection indexes
        db.organization_members.create_index([("organization_id", ASCENDING)])
        db.organization_members.create_index([("user_id", ASCENDING)])
        db.organization_members.create_index(
            [("organization_id", ASCENDING), ("user_id", ASCENDING)],
            unique=True
        )
        db.organization_members.create_index([("role", ASCENDING)])
        
        # Users collection indexes
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("organization_id", ASCENDING)])
        db.users.create_index([("created_at", DESCENDING)])
        
        # Scenes collection indexes
        db.scenes.create_index([("organization_id", ASCENDING)])
        db.scenes.create_index([("user_id", ASCENDING)])
        db.scenes.create_index([("status", ASCENDING)])
        db.scenes.create_index([("scene_id", ASCENDING)], unique=True, sparse=True)
        db.scenes.create_index([("created_at", DESCENDING)])
        db.scenes.create_index([("organization_id", ASCENDING), ("status", ASCENDING)])
        
        # Processing jobs collection indexes
        db.processing_jobs.create_index([("organization_id", ASCENDING)])
        db.processing_jobs.create_index([("scene_id", ASCENDING)])
        db.processing_jobs.create_index([("status", ASCENDING)])
        db.processing_jobs.create_index([("scene_id", ASCENDING), ("status", ASCENDING)])
        db.processing_jobs.create_index([("organization_id", ASCENDING), ("status", ASCENDING)])
        db.processing_jobs.create_index([("created_at", DESCENDING)])
        
        # Scene tiles collection indexes
        db.scene_tiles.create_index([("organization_id", ASCENDING)])
        db.scene_tiles.create_index([("scene_id", ASCENDING)])
        db.scene_tiles.create_index([("tile_id", ASCENDING)])
        db.scene_tiles.create_index([("scene_id", ASCENDING), ("tile_id", ASCENDING)], unique=True)
        db.scene_tiles.create_index([("scene_id", ASCENDING), ("level", ASCENDING)])
        
        # Annotations collection indexes
        db.annotations.create_index([("organization_id", ASCENDING)])
        db.annotations.create_index([("scene_id", ASCENDING)])
        db.annotations.create_index([("user_id", ASCENDING)])
        db.annotations.create_index([("scene_id", ASCENDING), ("created_at", DESCENDING)])
        db.annotations.create_index([("organization_id", ASCENDING), ("scene_id", ASCENDING)])
        db.annotations.create_index([("annotation_type", ASCENDING)])
        
        # Guided tours collection indexes
        db.guided_tours.create_index([("organization_id", ASCENDING)])
        db.guided_tours.create_index([("scene_id", ASCENDING)])
        db.guided_tours.create_index([("user_id", ASCENDING)])
        db.guided_tours.create_index([("organization_id", ASCENDING), ("scene_id", ASCENDING)])
        db.guided_tours.create_index([("created_at", DESCENDING)])
        
        # Share tokens collection indexes
        db.share_tokens.create_index([("organization_id", ASCENDING)])
        db.share_tokens.create_index([("token", ASCENDING)], unique=True)
        db.share_tokens.create_index([("scene_id", ASCENDING)])
        db.share_tokens.create_index([("organization_id", ASCENDING), ("scene_id", ASCENDING)])
        db.share_tokens.create_index([("expires_at", ASCENDING)])
        db.share_tokens.create_index([("created_at", DESCENDING)])
        
        # Scene access logs collection indexes (for audit trails)
        db.scene_access_logs.create_index([("organization_id", ASCENDING)])
        db.scene_access_logs.create_index([("user_id", ASCENDING)])
        db.scene_access_logs.create_index([("resource_type", ASCENDING)])
        db.scene_access_logs.create_index([("resource_id", ASCENDING)])
        db.scene_access_logs.create_index([("action", ASCENDING)])
        db.scene_access_logs.create_index([("accessed_at", DESCENDING)])
        db.scene_access_logs.create_index([("success", ASCENDING)])
        # Composite indexes for common queries
        db.scene_access_logs.create_index([("organization_id", ASCENDING), ("accessed_at", DESCENDING)])
        db.scene_access_logs.create_index([("user_id", ASCENDING), ("accessed_at", DESCENDING)])
        db.scene_access_logs.create_index([("resource_type", ASCENDING), ("resource_id", ASCENDING), ("accessed_at", DESCENDING)])
        # Legacy index for backward compatibility
        db.scene_access_logs.create_index([("scene_id", ASCENDING)])
        db.scene_access_logs.create_index([("scene_id", ASCENDING), ("accessed_at", DESCENDING)])
        
        # Scene objects collection indexes
        db.scene_objects.create_index([("organization_id", ASCENDING)])
        db.scene_objects.create_index([("scene_id", ASCENDING)])
        db.scene_objects.create_index([("object_id", ASCENDING)])
        db.scene_objects.create_index([("scene_id", ASCENDING), ("object_id", ASCENDING)], unique=True)
        db.scene_objects.create_index([("organization_id", ASCENDING), ("scene_id", ASCENDING)])
        db.scene_objects.create_index([("label", ASCENDING)])
        
        logger.info("Successfully created all indexes")
        
        # Close connection
        client.close()
        logger.info("MongoDB initialization completed successfully")
        
        return True
        
    except Exception as e:
        logger.error("Failed to initialize MongoDB", error=str(e))
        raise


async def init_database_async():
    """
    Async wrapper for database initialization.
    Can be called from async contexts.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, init_database_sync)


# Convenience function to get database instance
async def get_db() -> AsyncIOMotorDatabase:
    """Dependency function to get database instance."""
    return Database.get_database()
