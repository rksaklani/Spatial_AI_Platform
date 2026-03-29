#!/usr/bin/env python3
"""
MongoDB connection test script.
This script verifies that MongoDB is accessible and properly configured.
"""
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from utils.config import settings
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)


def test_connection():
    """Test MongoDB connection."""
    try:
        logger.info("Testing MongoDB connection", url=settings.mongodb_url)
        
        # Connect to MongoDB
        client = MongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection with ping
        client.admin.command('ping')
        logger.info("✓ Successfully connected to MongoDB")
        
        # Get database
        db = client[settings.database_name]
        
        # List collections
        collections = db.list_collection_names()
        logger.info(f"✓ Found {len(collections)} collections", collections=collections)
        
        # Check each expected collection
        expected_collections = [
            'organizations',
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
        
        for collection_name in expected_collections:
            if collection_name in collections:
                # Get index information
                indexes = list(db[collection_name].list_indexes())
                logger.info(
                    f"✓ Collection '{collection_name}' exists with {len(indexes)} indexes",
                    collection=collection_name,
                    index_count=len(indexes)
                )
            else:
                logger.warning(
                    f"✗ Collection '{collection_name}' not found",
                    collection=collection_name
                )
        
        # Test write operation
        test_collection = db['_test_collection']
        test_doc = {"test": "data", "timestamp": "2024-01-01"}
        result = test_collection.insert_one(test_doc)
        logger.info("✓ Write test successful", inserted_id=str(result.inserted_id))
        
        # Test read operation
        found_doc = test_collection.find_one({"_id": result.inserted_id})
        if found_doc:
            logger.info("✓ Read test successful")
        else:
            logger.error("✗ Read test failed")
            return False
        
        # Clean up test collection
        test_collection.drop()
        logger.info("✓ Cleanup successful")
        
        # Close connection
        client.close()
        
        logger.info("=" * 60)
        logger.info("MongoDB connection test PASSED")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error("MongoDB connection test FAILED", error=str(e), exc_info=True)
        logger.info("=" * 60)
        logger.info("Troubleshooting tips:")
        logger.info("1. Ensure MongoDB is running: docker-compose up -d mongodb")
        logger.info("2. Check connection URL in .env file")
        logger.info("3. Verify credentials are correct")
        logger.info("=" * 60)
        return False


def main():
    """Main entry point."""
    success = test_connection()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
