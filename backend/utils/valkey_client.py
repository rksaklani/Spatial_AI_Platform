"""
Valkey client with connection pooling for caching and session management.

This module provides a singleton Valkey client with connection pooling,
supporting caching operations, session management, and job queue functionality.
"""

import json
import logging
from typing import Any, Optional, Union

from datetime import timedelta

import valkey
from valkey.connection import ConnectionPool
from valkey.exceptions import ValkeyError, ConnectionError, TimeoutError

from utils.config import settings

logger = logging.getLogger(__name__)


class ValkeyClient:
    """
    Valkey client with connection pooling and caching utilities.
    
    Provides methods for:
    - Basic key-value operations
    - Caching with TTL
    - Session management
    - Tile caching
    - Scene metadata caching
    """
    
    _instance: Optional['ValkeyClient'] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[valkey.Valkey] = None
    
    def __new__(cls):
        """Singleton pattern to ensure single connection pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Valkey client with connection pool."""
        if self._client is None:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with configuration."""
        try:
            # Create connection pool
            self._pool = ConnectionPool(
                host=settings.valkey_host,
                port=settings.valkey_port,
                db=settings.valkey_db,
                password=settings.valkey_password if hasattr(settings, 'valkey_password') else None,
                max_connections=settings.valkey_max_connections,
                socket_timeout=settings.valkey_socket_timeout,
                socket_connect_timeout=settings.valkey_connect_timeout,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
                health_check_interval=30,
                decode_responses=False,  # We'll handle encoding/decoding
            )
            
            # Create client from pool
            self._client = valkey.Valkey(connection_pool=self._pool)
            
            # Test connection
            self._client.ping()
            logger.info(
                f"Valkey connection pool initialized: "
                f"{settings.valkey_host}:{settings.valkey_port} "
                f"(max_connections={settings.valkey_max_connections})"
            )
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Valkey: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Valkey client: {e}")
            raise
    
    @property
    def client(self) -> valkey.Valkey:
        """Get the Valkey client instance."""
        if self._client is None:
            self._initialize_pool()
        return self._client
    
    def ping(self) -> bool:
        """
        Test connection to Valkey.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            return self.client.ping()
        except ValkeyError as e:
            logger.error(f"Valkey ping failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[bytes]:
        """
        Get value by key.
        
        Args:
            key: Cache key
            
        Returns:
            Value as bytes or None if not found
        """
        try:
            return self.client.get(key)
        except ValkeyError as e:
            logger.error(f"Error getting key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Union[str, bytes],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set key-value pair with optional TTL.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except ValkeyError as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        try:
            return self.client.delete(*keys)
        except ValkeyError as e:
            logger.error(f"Error deleting keys: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """
        Check if keys exist.
        
        Args:
            keys: Keys to check
            
        Returns:
            int: Number of keys that exist
        """
        try:
            return self.client.exists(*keys)
        except ValkeyError as e:
            logger.error(f"Error checking key existence: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            return self.client.expire(key, ttl)
        except ValkeyError as e:
            logger.error(f"Error setting expiration for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Cache key
            
        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except ValkeyError as e:
            logger.error(f"Error getting TTL for key '{key}': {e}")
            return -2
    
    # JSON caching utilities
    
    def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value by key.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized JSON value or None
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
            return None
        except (ValkeyError, json.JSONDecodeError) as e:
            logger.error(f"Error getting JSON key '{key}': {e}")
            return None
    
    def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to serialize and store
            ttl: Time to live in seconds (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, ttl)
        except (ValkeyError, TypeError) as e:
            logger.error(f"Error setting JSON key '{key}': {e}")
            return False
    
    # Scene-specific caching methods
    
    def cache_tile(
        self,
        scene_id: str,
        tile_id: str,
        tile_data: bytes,
        ttl: int = 3600
    ) -> bool:
        """
        Cache a scene tile.
        
        Args:
            scene_id: Scene identifier
            tile_id: Tile identifier
            tile_data: Binary tile data
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful
        """
        key = f"tile:{scene_id}:{tile_id}"
        return self.set(key, tile_data, ttl)
    
    def get_tile(self, scene_id: str, tile_id: str) -> Optional[bytes]:
        """
        Get cached tile data.
        
        Args:
            scene_id: Scene identifier
            tile_id: Tile identifier
            
        Returns:
            Binary tile data or None
        """
        key = f"tile:{scene_id}:{tile_id}"
        return self.get(key)
    
    def cache_scene_metadata(
        self,
        scene_id: str,
        metadata: dict,
        ttl: int = 300
    ) -> bool:
        """
        Cache scene metadata.
        
        Args:
            scene_id: Scene identifier
            metadata: Scene metadata dictionary
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            bool: True if successful
        """
        key = f"scene:metadata:{scene_id}"
        return self.set_json(key, metadata, ttl)
    
    def get_scene_metadata(self, scene_id: str) -> Optional[dict]:
        """
        Get cached scene metadata.
        
        Args:
            scene_id: Scene identifier
            
        Returns:
            Scene metadata dictionary or None
        """
        key = f"scene:metadata:{scene_id}"
        return self.get_json(key)
    
    # Session management
    
    def create_session(
        self,
        scene_id: str,
        user_id: str,
        session_data: dict,
        ttl: int = 3600
    ) -> bool:
        """
        Create a user session for a scene.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            session_data: Session data dictionary
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful
        """
        key = f"session:{scene_id}:{user_id}"
        return self.set_json(key, session_data, ttl)
    
    def get_session(self, scene_id: str, user_id: str) -> Optional[dict]:
        """
        Get user session data.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            
        Returns:
            Session data dictionary or None
        """
        key = f"session:{scene_id}:{user_id}"
        return self.get_json(key)
    
    def delete_session(self, scene_id: str, user_id: str) -> bool:
        """
        Delete user session.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            
        Returns:
            bool: True if successful
        """
        key = f"session:{scene_id}:{user_id}"
        return self.delete(key) > 0
    
    def get_active_sessions(self, scene_id: str) -> list:
        """
        Get all active sessions for a scene.
        
        Args:
            scene_id: Scene identifier
            
        Returns:
            List of user IDs with active sessions
        """
        try:
            pattern = f"session:{scene_id}:*"
            keys = self.client.keys(pattern)
            # Extract user IDs from keys
            user_ids = [
                key.decode('utf-8').split(':')[-1]
                for key in keys
            ]
            return user_ids
        except ValkeyError as e:
            logger.error(f"Error getting active sessions for scene '{scene_id}': {e}")
            return []
    
    # Health and statistics
    
    def get_info(self, section: Optional[str] = None) -> dict:
        """
        Get Valkey server information.
        
        Args:
            section: Optional section name (e.g. 'memory', 'persistence', 'replication')
            
        Returns:
            dict: Server information
        """
        try:
            if section:
                return self.client.info(section)
            return self.client.info()
        except ValkeyError as e:
            logger.error(f"Error getting Valkey info: {e}")
            return {}
    
    def get_memory_stats(self) -> dict:
        """
        Get memory usage statistics.
        
        Returns:
            dict: Memory statistics
        """
        try:
            info = self.client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'maxmemory': info.get('maxmemory', 0),
                'maxmemory_human': info.get('maxmemory_human', '0B'),
                'maxmemory_policy': info.get('maxmemory_policy', 'unknown'),
            }
        except ValkeyError as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}
    
    def flush_db(self) -> bool:
        """
        Flush current database (use with caution!).
        
        Returns:
            bool: True if successful
        """
        try:
            return self.client.flushdb()
        except ValkeyError as e:
            logger.error(f"Error flushing database: {e}")
            return False
    def blacklist_token(self, jti: str, expire_seconds: int = 3600 * 24 * 7) -> bool:
        """Adds a JWT token ID to the blacklist until it naturally expires."""
        if not self.client:
            return False
            
        try:
            return self.client.setex(f"blacklist:{jti}", expire_seconds, "1")
        except ValkeyError as e:
            logger.error(f"Error blacklisting token: {e}")
            return False

    async def blacklist_token_async(self, jti: str, expire_seconds: int = 3600 * 24 * 7) -> bool:
        """Async wrapper for blacklist_token."""
        return self.blacklist_token(jti, expire_seconds)

    def is_token_blacklisted(self, jti: str) -> bool:
        """Checks if a JWT token ID is currently blacklisted."""
        if not self.client:
            return False
            
        try:
            val = self.client.get(f"blacklist:{jti}")
            return val is not None
        except ValkeyError as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    async def is_token_blacklisted_async(self, jti: str) -> bool:
        """Async wrapper for is_token_blacklisted."""
        return self.is_token_blacklisted(jti)

    def close(self):
        """Close connection pool."""
        if self._pool:
            self._pool.disconnect()
            logger.info("Valkey connection pool closed")


# Global instance (lazy initialization)
_valkey_client: Optional[ValkeyClient] = None


# Convenience functions
def get_valkey_client() -> ValkeyClient:
    """Get the global Valkey client instance (lazy initialization)."""
    global _valkey_client
    if _valkey_client is None:
        _valkey_client = ValkeyClient()
    return _valkey_client
