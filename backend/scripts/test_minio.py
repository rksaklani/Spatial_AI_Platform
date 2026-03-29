"""
MinIO verification script.

This script verifies that MinIO is properly configured and all buckets
are accessible.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.minio_client import get_minio_client
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger(__name__)


def verify_bucket(client, bucket_name: str) -> bool:
    """
    Verify that a bucket exists and is accessible.
    
    Args:
        client: MinIOClient instance
        bucket_name: Bucket to verify
        
    Returns:
        True if bucket exists and is accessible, False otherwise
    """
    try:
        exists = client.bucket_exists(bucket_name)
        
        if exists:
            logger.info("✓ Bucket verified", bucket=bucket_name)
            
            # Try to list objects (even if empty)
            objects = list(client.list_objects(bucket_name))
            logger.info(
                "  Bucket accessible",
                bucket=bucket_name,
                object_count=len(objects)
            )
            return True
        else:
            logger.error("✗ Bucket does not exist", bucket=bucket_name)
            return False
            
    except Exception as e:
        logger.error(
            "✗ Failed to verify bucket",
            bucket=bucket_name,
            error=str(e)
        )
        return False


def main():
    """Main verification function."""
    logger.info("Starting MinIO verification")
    
    # Get MinIO client
    try:
        client = get_minio_client()
        logger.info("MinIO client connected successfully")
    except Exception as e:
        logger.error("Failed to connect to MinIO", error=str(e))
        return 1
    
    # Required buckets
    required_buckets = [
        "videos",
        "frames",
        "depth",
        "scenes",
        "reports"
    ]
    
    logger.info("Verifying required buckets", count=len(required_buckets))
    
    # Verify each bucket
    results = {}
    for bucket_name in required_buckets:
        results[bucket_name] = verify_bucket(client, bucket_name)
    
    # Summary
    all_verified = all(results.values())
    success_count = sum(1 for success in results.values() if success)
    
    logger.info(
        "Verification complete",
        total=len(required_buckets),
        successful=success_count,
        failed=len(required_buckets) - success_count
    )
    
    if all_verified:
        logger.info("✓ All buckets verified successfully")
        return 0
    else:
        failed_buckets = [name for name, success in results.items() if not success]
        logger.error("✗ Some buckets failed verification", failed=failed_buckets)
        return 1


if __name__ == "__main__":
    sys.exit(main())
