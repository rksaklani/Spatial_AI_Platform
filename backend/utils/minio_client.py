"""
MinIO client utility for object storage operations.

This module provides a configured MinIO client and utilities for bucket management,
file upload/download, and access policy configuration.
"""

import os
from typing import Optional, List, BinaryIO
from minio import Minio
from minio.error import S3Error
import structlog

logger = structlog.get_logger(__name__)


class MinIOClient:
    """MinIO client wrapper for object storage operations."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: bool = False
    ):
        """
        Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint (default: from env MINIO_ENDPOINT)
            access_key: MinIO access key (default: from env MINIO_ACCESS_KEY)
            secret_key: MinIO secret key (default: from env MINIO_SECRET_KEY)
            secure: Use HTTPS connection (default: from env MINIO_SECURE)
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.secure = secure or os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        logger.info(
            "MinIO client initialized",
            endpoint=self.endpoint,
            secure=self.secure
        )
    
    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create a bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create
            
        Returns:
            True if bucket was created or already exists, False on error
        """
        try:
            if self.client.bucket_exists(bucket_name):
                logger.info("Bucket already exists", bucket=bucket_name)
                return True
            
            self.client.make_bucket(bucket_name)
            logger.info("Bucket created successfully", bucket=bucket_name)
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to create bucket",
                bucket=bucket_name,
                error=str(e)
            )
            return False
    
    def create_buckets(self, bucket_names: List[str]) -> dict:
        """
        Create multiple buckets.
        
        Args:
            bucket_names: List of bucket names to create
            
        Returns:
            Dictionary with bucket names as keys and success status as values
        """
        results = {}
        for bucket_name in bucket_names:
            results[bucket_name] = self.create_bucket(bucket_name)
        return results
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to MinIO.
        
        Args:
            bucket_name: Target bucket name
            object_name: Object name in bucket (path)
            file_path: Local file path to upload
            content_type: MIME type of the file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(
                "File uploaded successfully",
                bucket=bucket_name,
                object=object_name,
                file=file_path
            )
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to upload file",
                bucket=bucket_name,
                object=object_name,
                error=str(e)
            )
            return False
    
    def upload_data(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload data from a file-like object to MinIO.
        
        Args:
            bucket_name: Target bucket name
            object_name: Object name in bucket (path)
            data: File-like object containing data
            length: Length of data in bytes
            content_type: MIME type of the data
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                data,
                length,
                content_type=content_type
            )
            logger.info(
                "Data uploaded successfully",
                bucket=bucket_name,
                object=object_name,
                size=length
            )
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to upload data",
                bucket=bucket_name,
                object=object_name,
                error=str(e)
            )
            return False
    
    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> bool:
        """
        Download a file from MinIO.
        
        Args:
            bucket_name: Source bucket name
            object_name: Object name in bucket (path)
            file_path: Local file path to save to
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            self.client.fget_object(
                bucket_name,
                object_name,
                file_path
            )
            logger.info(
                "File downloaded successfully",
                bucket=bucket_name,
                object=object_name,
                file=file_path
            )
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to download file",
                bucket=bucket_name,
                object=object_name,
                error=str(e)
            )
            return False
    
    def get_object(self, bucket_name: str, object_name: str):
        """
        Get an object from MinIO as a stream.
        
        Args:
            bucket_name: Source bucket name
            object_name: Object name in bucket (path)
            
        Returns:
            Response object with data stream, or None on error
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            logger.info(
                "Object retrieved successfully",
                bucket=bucket_name,
                object=object_name
            )
            return response
            
        except S3Error as e:
            logger.error(
                "Failed to get object",
                bucket=bucket_name,
                object=object_name,
                error=str(e)
            )
            return None
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete an object from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name in bucket (path)
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(
                "Object deleted successfully",
                bucket=bucket_name,
                object=object_name
            )
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to delete object",
                bucket=bucket_name,
                object=object_name,
                error=str(e)
            )
            return False
    
    def list_objects(self, bucket_name: str, prefix: Optional[str] = None):
        """
        List objects in a bucket.
        
        Args:
            bucket_name: Bucket name
            prefix: Filter objects by prefix
            
        Returns:
            Iterator of object information
        """
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=True
            )
            return objects
            
        except S3Error as e:
            logger.error(
                "Failed to list objects",
                bucket=bucket_name,
                prefix=prefix,
                error=str(e)
            )
            return []
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        Args:
            bucket_name: Bucket name to check
            
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(
                "Failed to check bucket existence",
                bucket=bucket_name,
                error=str(e)
            )
            return False
    
    def is_connected(self) -> bool:
        """
        Check if MinIO connection is healthy.
        
        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            # Try to list buckets as a health check
            self.client.list_buckets()
            return True
        except S3Error as e:
            logger.error("MinIO connection check failed", error=str(e))
            return False
        except Exception as e:
            logger.error("MinIO connection check failed", error=str(e))
            return False
    
    def set_bucket_policy(self, bucket_name: str, policy: str) -> bool:
        """
        Set bucket policy.
        
        Args:
            bucket_name: Bucket name
            policy: Policy JSON string
            
        Returns:
            True if policy set successfully, False otherwise
        """
        try:
            self.client.set_bucket_policy(bucket_name, policy)
            logger.info(
                "Bucket policy set successfully",
                bucket=bucket_name
            )
            return True
            
        except S3Error as e:
            logger.error(
                "Failed to set bucket policy",
                bucket=bucket_name,
                error=str(e)
            )
            return False


# Global MinIO client instance
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """
    Get or create the global MinIO client instance.
    
    Returns:
        MinIOClient instance
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client


def initialize_buckets() -> dict:
    """
    Initialize all required buckets for the platform.
    
    Creates the following buckets:
    - videos: Store uploaded video files
    - frames: Store extracted video frames
    - depth: Store depth maps
    - scenes: Store reconstructed 3D scenes and tiles
    - reports: Store generated PDF reports
    
    Returns:
        Dictionary with bucket names as keys and creation status as values
    """
    client = get_minio_client()
    
    required_buckets = [
        "videos",
        "frames",
        "depth",
        "scenes",
        "reports"
    ]
    
    logger.info("Initializing MinIO buckets", buckets=required_buckets)
    results = client.create_buckets(required_buckets)
    
    # Log summary
    success_count = sum(1 for success in results.values() if success)
    logger.info(
        "Bucket initialization complete",
        total=len(required_buckets),
        successful=success_count,
        failed=len(required_buckets) - success_count
    )
    
    return results
