"""Collaboration service for real-time scene collaboration via WebSocket."""
import json
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict
import structlog

from utils.valkey_client import get_valkey_client

logger = structlog.get_logger(__name__)


@dataclass
class UserSession:
    """Represents a user session in a collaborative scene."""
    user_id: str
    user_name: str
    scene_id: str
    joined_at: float
    last_heartbeat: float
    cursor_position: Optional[tuple] = None  # (x, y, z)


class CollaborationService:
    """Service for managing real-time collaboration sessions."""
    
    def __init__(self):
        self.valkey = get_valkey_client()
        self.active_connections: Dict[str, Set[object]] = {}  # scene_id -> set of websockets
        self.session_ttl = 3600  # 1 hour
        self.heartbeat_interval = 30  # 30 seconds
    
    def _get_session_key(self, scene_id: str, user_id: str) -> str:
        """Generate Redis key for user session."""
        return f"session:{scene_id}:{user_id}"
    
    def _get_scene_users_key(self, scene_id: str) -> str:
        """Generate Redis key for scene users set."""
        return f"scene:users:{scene_id}"
    
    async def join_scene(
        self,
        scene_id: str,
        user_id: str,
        user_name: str,
        websocket: object
    ) -> UserSession:
        """
        Add a user to a collaborative scene session.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            user_name: User display name
            websocket: WebSocket connection object
            
        Returns:
            UserSession object
        """
        current_time = time.time()
        
        # Create session
        session = UserSession(
            user_id=user_id,
            user_name=user_name,
            scene_id=scene_id,
            joined_at=current_time,
            last_heartbeat=current_time
        )
        
        # Store session in Valkey
        session_key = self._get_session_key(scene_id, user_id)
        session_data = asdict(session)
        self.valkey.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        # Add user to scene users set
        scene_users_key = self._get_scene_users_key(scene_id)
        self.valkey.sadd(scene_users_key, user_id)
        self.valkey.expire(scene_users_key, self.session_ttl)
        
        # Track WebSocket connection
        if scene_id not in self.active_connections:
            self.active_connections[scene_id] = set()
        self.active_connections[scene_id].add(websocket)
        
        logger.info(
            "user_joined_scene",
            scene_id=scene_id,
            user_id=user_id,
            user_name=user_name
        )
        
        return session
    
    async def leave_scene(
        self,
        scene_id: str,
        user_id: str,
        websocket: object
    ):
        """
        Remove a user from a collaborative scene session.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            websocket: WebSocket connection object
        """
        # Remove session from Valkey
        session_key = self._get_session_key(scene_id, user_id)
        self.valkey.delete(session_key)
        
        # Remove user from scene users set
        scene_users_key = self._get_scene_users_key(scene_id)
        self.valkey.srem(scene_users_key, user_id)
        
        # Remove WebSocket connection
        if scene_id in self.active_connections:
            self.active_connections[scene_id].discard(websocket)
            if not self.active_connections[scene_id]:
                del self.active_connections[scene_id]
        
        logger.info(
            "user_left_scene",
            scene_id=scene_id,
            user_id=user_id
        )
    
    async def update_heartbeat(self, scene_id: str, user_id: str):
        """
        Update user session heartbeat timestamp.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
        """
        session_key = self._get_session_key(scene_id, user_id)
        session_data = self.valkey.get(session_key)
        
        if session_data:
            session = json.loads(session_data)
            session['last_heartbeat'] = time.time()
            self.valkey.setex(
                session_key,
                self.session_ttl,
                json.dumps(session)
            )
    
    async def update_cursor_position(
        self,
        scene_id: str,
        user_id: str,
        position: tuple
    ):
        """
        Update user cursor position in 3D scene.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            position: (x, y, z) tuple
        """
        session_key = self._get_session_key(scene_id, user_id)
        session_data = self.valkey.get(session_key)
        
        if session_data:
            session = json.loads(session_data)
            session['cursor_position'] = position
            self.valkey.setex(
                session_key,
                self.session_ttl,
                json.dumps(session)
            )
    
    async def get_active_users(self, scene_id: str) -> list:
        """
        Get list of active users in a scene.
        
        Args:
            scene_id: Scene identifier
            
        Returns:
            List of UserSession dictionaries
        """
        scene_users_key = self._get_scene_users_key(scene_id)
        user_ids = self.valkey.smembers(scene_users_key)
        
        active_users = []
        for user_id in user_ids:
            session_key = self._get_session_key(scene_id, user_id.decode('utf-8'))
            session_data = self.valkey.get(session_key)
            if session_data:
                active_users.append(json.loads(session_data))
        
        return active_users
    
    async def get_user_count(self, scene_id: str) -> int:
        """
        Get count of active users in a scene.
        
        Args:
            scene_id: Scene identifier
            
        Returns:
            Number of active users
        """
        scene_users_key = self._get_scene_users_key(scene_id)
        return self.valkey.scard(scene_users_key)
    
    async def broadcast_to_scene(
        self,
        scene_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """
        Broadcast a message to all users in a scene.
        
        Args:
            scene_id: Scene identifier
            message: Message dictionary to broadcast
            exclude_user: Optional user_id to exclude from broadcast
        """
        if scene_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.active_connections[scene_id]:
            try:
                # Check if this websocket should be excluded
                if exclude_user and hasattr(websocket, 'user_id'):
                    if websocket.user_id == exclude_user:
                        continue
                
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(
                    "failed_to_send_message",
                    scene_id=scene_id,
                    error=str(e)
                )
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.active_connections[scene_id].discard(ws)
    
    async def restore_session(
        self,
        scene_id: str,
        user_id: str
    ) -> Optional[dict]:
        """
        Restore a user session after reconnection.
        
        Args:
            scene_id: Scene identifier
            user_id: User identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        session_key = self._get_session_key(scene_id, user_id)
        session_data = self.valkey.get(session_key)
        
        if session_data:
            session = json.loads(session_data)
            # Update heartbeat on reconnection
            session['last_heartbeat'] = time.time()
            self.valkey.setex(
                session_key,
                self.session_ttl,
                json.dumps(session)
            )
            logger.info(
                "session_restored",
                scene_id=scene_id,
                user_id=user_id
            )
            return session
        
        return None


# Global collaboration service instance
collaboration_service = CollaborationService()
