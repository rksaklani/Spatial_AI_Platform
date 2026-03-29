#!/usr/bin/env python3
"""
MongoDB initialization script.
This script creates the database, collections, and indexes.
Run this script after MongoDB is deployed.
"""
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import init_database_sync
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


def main():
    """Main entry point for MongoDB initialization."""
    try:
        logger.info("Starting MongoDB initialization...")
        init_database_sync()
        logger.info("MongoDB initialization completed successfully!")
        return 0
    except Exception as e:
        logger.error("MongoDB initialization failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
