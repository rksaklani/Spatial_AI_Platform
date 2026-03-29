"""
MinIO initialization script.

This script initializes MinIO by creating required buckets and testing
upload/download operations.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.minio_client import get_minio_client, initialize_buckets
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


def test_upload_download(client, bucket_name: str) -> bool:
    """
    Test upload and download operations on a bucket.
    
    Args:
        client: MinIOClient instance
        bucket_name: Bucket to test
        
    Returns:
        True if test successful, False otherwise
    """
    logger.info("Testing upload/download", bucket=bucket_name)
    
    # Create a temporary test file
    test_content = b"MinIO test file content - Hello from Spatial AI Platform!"
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name
    
    try:
        # Test upload
        object_name = "test/test_file.txt"
        logger.info("Uploading test file", object=object_name)
        
        upload_success = client.upload_file(
            bucket_name,
            object_name,
            temp_file_path,
            content_type="text/plain"
        )
        
        if not upload_success:
            logger.error("Upload test failed", bucket=bucket_name)
            return False
        
        logger.info("Upload test successful", bucket=bucket_name)
        
        # Test download
        download_path = temp_file_path + ".downloaded"
        logger.info("Downloading test file", object=object_name)
        
        download_success = client.download_file(
            bucket_name,
            object_name,
            download_path
        )
        
        if not download_success:
            logger.error("Download test failed", bucket=bucket_name)
            return False
        
        # Verify content
        with open(download_path, 'rb') as f:
            downloaded_content = f.read()
        
        if downloaded_content != test_content:
            logger.error(
                "Content verification failed",
                bucket=bucket_name,
                expected_size=len(test_content),
                actual_size=len(downloaded_content)
            )
            return False
        
        logger.info("Download and verification successful", bucket=bucket_name)
        
        # Clean up test object
        client.delete_object(bucket_name, object_name)
        logger.info("Test object cleaned up", object=object_name)
        
        # Clean up local files
        os.unlink(temp_file_path)
        os.unlink(download_path)
        
        return True
        
    except Exception as e:
        logger.error(
            "Test failed with exception",
            bucket=bucket_name,
            error=str(e)
        )
        return False
    finally:
        # Ensure temp file is cleaned up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def main():
    """Main initialization function."""
    logger.info("Starting MinIO initialization")
    
    # Get MinIO client
    try:
        client = get_minio_client()
        logger.info("MinIO client created successfully")
    except Exception as e:
        logger.error("Failed to create MinIO client", error=str(e))
        return 1
    
    # Initialize buckets
    logger.info("Creating required buckets")
    results = initialize_buckets()
    
    # Check if all buckets were created successfully
    all_success = all(results.values())
    
    if not all_success:
        failed_buckets = [name for name, success in results.items() if not success]
        logger.error(
            "Some buckets failed to create",
            failed=failed_buckets
        )
        return 1
    
    logger.info("All buckets created successfully")
    
    # Test upload/download operations on each bucket
    logger.info("Testing upload/download operations")
    test_results = {}
    
    for bucket_name in results.keys():
        test_results[bucket_name] = test_upload_download(client, bucket_name)
    
    # Summary
    all_tests_passed = all(test_results.values())
    
    if all_tests_passed:
        logger.info(
            "✓ MinIO initialization complete - All tests passed",
            buckets=list(results.keys())
        )
        return 0
    else:
        failed_tests = [name for name, success in test_results.items() if not success]
        logger.error(
            "✗ Some tests failed",
            failed=failed_tests
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
