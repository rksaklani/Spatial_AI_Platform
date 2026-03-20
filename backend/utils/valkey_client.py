"""
Valkey client with connection pooling for caching and session management.

This module provides a singleton Valkey client with connection pooling,
supporting caching operations, session management, and job queue functionality.

Note: Valkey is Redis-protocol compatible. We use the valkey-py library which
works seamlessly with Valkey servers.
"""

import json
import logging
import time
from typing import Any, Optional, Union
from functools import wraps

from datetime import timedelta

import valkey
from valkey.connection import ConnectionPool
from valkey.exceptions import ValkeyError, ConnectionError, TimeoutError

from utils.config import settings

logger = logging.getLogger(__name__)

# Connection retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 0.5  # seconds, exponential backoff


def with_retry(max_retries: int = MAX_RETRIES, delay_base: float = RETRY_DELAY_BASE):
    """
    Decorator for retrying Valkey operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_base: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = delay_base * (2 ** attempt)
                        logger.warning(
                            f"Valkey operation failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay}s: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Valkey operation failed after {max_retries + 1} attempts: {e}")
                except ValkeyError as e:
                    # Non-connection errors should not be retried
                    logger.error(f"Valkey error (non-retryable): {e}")
                    raise
            raise last_error
        return wrapper
    return decorator


class ValkeyClient:
    """
    Valkey client with connection pooling and caching utilities.
    
    Provides methods for:
    - Basic key-value operations
    - Caching with TTL
    - Session management
    - Tile caching
    - Scene metadata caching
    - Token blacklisting for auth
    """
    
    _instance: Optional['ValkeyClient'] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[valkey.Valkey] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern to ensure single connection pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Valkey client with connection pool."""
        if not self._initialized:
            self._initialize_pool()
            ValkeyClient._initialized = True
    
    def _initialize_pool(self):
        """
        Initialize connection pool with configuration.
        
        Note: socket_keepalive_options removed for cross-platform compatibility
        (Windows does not support TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT).
        """
        try:
            # Create connection pool
            # Using minimal options for maximum compatibility
            self._pool = ConnectionPool(
                host=settings.valkey_host,
                port=settings.valkey_port,
                db=settings.valkey_db,
                password=settings.valkey_password if hasattr(settings, 'valkey_password') and settings.valkey_password else None,
                max_connections=settings.valkey_max_connections,
                socket_timeout=settings.valkey_socket_timeout,
                socket_connect_timeout=settings.valkey_connect_timeout,
                socket_keepalive=True,  # Enable keepalive without custom options
                health_check_interval=30,
                decode_responses=False,  # We'll handle encoding/decoding
                retry_on_timeout=True,  # Auto-retry on timeout
            )
            
            # Create client from pool
            self._client = valkey.Valkey(connection_pool=self._pool)
            
            # Test connection with retry
            self._test_connection_with_retry()
            
            logger.info(
                f"Valkey connection pool initialized: "
                f"{settings.valkey_host}:{settings.valkey_port} "
                f"(max_connections={settings.valkey_max_connections})"
            )
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Valkey: {e}")
            # Don't raise - allow graceful degradation
            self._client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Valkey client: {e}")
            self._client = None
    
    def _test_connection_with_retry(self, max_attempts: int = 3):
        """Test connection with retry logic."""
        for attempt in range(max_attempts):
            try:
                self._client.ping()
                return True
            except (ConnectionError, TimeoutError) as e:
                if attempt < max_attempts - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(f"Valkey ping failed (attempt {attempt + 1}), retrying in {delay}s")
                    time.sleep(delay)
                else:
                    raise
        return False
    
    def _ensure_connected(self) -> bool:
        """
        Ensure client is connected, attempt reconnection if needed.
        
        Returns:
            bool: True if connected, False if unable to connect
        """
        if self._client is None:
            try:
                self._initialize_pool()
            except Exception:
                return False
        return self._client is not None
    
    @property
    def client(self) -> Optional[valkey.Valkey]:
        """Get the Valkey client instance."""
        if not self._ensure_connected():
            return None
        return self._client
    
    def ping(self) -> bool:
        """
        Test connection to Valkey.
        
        Returns:
            bool: True if connection is successful
        """
        if not self._ensure_connected():
            return False
        try:
            return self._client.ping()
        except ValkeyError as e:
            logger.error(f"Valkey ping failed: {e}")
            return False
    
    @with_retry()
    def get(self, key: str) -> Optional[bytes]:
        """
        Get value by key.
        
        Args:
            key: Cache key
            
        Returns:
            Value as bytes or None if not found
        """
        if not self._ensure_connected():
            return None
        try:
            return self._client.get(key)
        except ValkeyError as e:
            logger.error(f"Error getting key '{key}': {e}")
            return None
    
    @with_retry()
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
        if not self._ensure_connected():
            return False
        try:
            if ttl:
                return self._client.setex(key, ttl, value)
            else:
                return self._client.set(key, value)
        except ValkeyError as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False
    
    @with_retry()
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            keys: Keys to delete
            
        Returns:
            int: Number of keys deleted
        """
        if not self._ensure_connected():
            return 0
        try:
            return self._client.delete(*keys)
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
        if not self._ensure_connected():
            return 0
        try:
            return self._client.exists(*keys)
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
        if not self._ensure_connected():
            return False
        try:
            return self._client.expire(key, ttl)
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
        if not self._ensure_connected():
            return -2
        try:
            return self._client.ttl(key)
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
        if not self._ensure_connected():
            return None
        try:
            value = self._client.get(key)
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
    
    # Token blacklist operations (critical for auth)
    
    @with_retry()
    def blacklist_token(self, jti: str, expire_seconds: int = 3600 * 24 * 7) -> bool:
        """
        Add a JWT token ID to the blacklist until it naturally expires.
        
        Args:
            jti: JWT ID (unique token identifier)
            expire_seconds: Time until blacklist entry expires (default: 7 days)
            
        Returns:
            bool: True if successfully blacklisted
        """
        if not self._ensure_connected():
            logger.warning(f"Cannot blacklist token {jti}: Valkey unavailable")
            return False
        
        try:
            result = self._client.setex(f"blacklist:{jti}", expire_seconds, "1")
            if result:
                logger.info(f"Token blacklisted: {jti[:8]}...")
            return bool(result)
        except ValkeyError as e:
            logger.error(f"Error blacklisting token {jti}: {e}")
            return False

    async def blacklist_token_async(self, jti: str, expire_seconds: int = 3600 * 24 * 7) -> bool:
        """Async wrapper for blacklist_token."""
        return self.blacklist_token(jti, expire_seconds)

    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if a JWT token ID is currently blacklisted.
        
        Args:
            jti: JWT ID to check
            
        Returns:
            bool: True if blacklisted, False otherwise
        """
        if not self._ensure_connected():
            # Fail-safe: if we can't check, assume not blacklisted
            # This is a trade-off: availability over security during outages
            logger.warning(f"Cannot check blacklist for {jti}: Valkey unavailable")
            return False
        
        try:
            val = self._client.get(f"blacklist:{jti}")
            return val is not None
        except ValkeyError as e:
            logger.error(f"Error checking token blacklist for {jti}: {e}")
            return False

    async def is_token_blacklisted_async(self, jti: str) -> bool:
        """Async wrapper for is_token_blacklisted."""
        return self.is_token_blacklisted(jti)
    
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
        if not self._ensure_connected():
            return []
        try:
            pattern = f"session:{scene_id}:*"
            keys = self._client.keys(pattern)
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
        if not self._ensure_connected():
            return {}
        try:
            if section:
                return self._client.info(section)
            return self._client.info()
        except ValkeyError as e:
            logger.error(f"Error getting Valkey info: {e}")
            return {}
    
    def get_memory_stats(self) -> dict:
        """
        Get memory usage statistics.
        
        Returns:
            dict: Memory statistics
        """
        if not self._ensure_connected():
            return {}
        try:
            info = self._client.info('memory')
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
        if not self._ensure_connected():
            return False
        try:
            return self._client.flushdb()
        except ValkeyError as e:
            logger.error(f"Error flushing database: {e}")
            return False

    def close(self):
        """Close connection pool."""
        if self._pool:
            try:
                self._pool.disconnect()
                logger.info("Valkey connection pool closed")
            except Exception as e:
                logger.error(f"Error closing Valkey connection pool: {e}")
        self._client = None
        ValkeyClient._initialized = False


# Global instance (lazy initialization)
_valkey_client: Optional[ValkeyClient] = None


def get_valkey_client() -> ValkeyClient:
    """Get the global Valkey client instance (lazy initialization)."""
    global _valkey_client
    if _valkey_client is None:
        _valkey_client = ValkeyClient()
    return _valkey_client


def reset_valkey_client():
    """Reset the global Valkey client (useful for testing)."""
    global _valkey_client
    if _valkey_client:
        _valkey_client.close()
    _valkey_client = None
    ValkeyClient._instance = None
    ValkeyClient._initialized = False
