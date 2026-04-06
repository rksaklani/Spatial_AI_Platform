"""
Progress Service for WebSocket Management

Manages WebSocket connections for real-time progress updates,
handles subscriptions, and broadcasts progress events to connected clients.
"""

import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class ProgressService:
    """
    Service for managing progress WebSocket connections and broadcasts.
    
    Maintains a registry of active WebSocket connections per scene and
    broadcasts progress updates to all subscribers.
    """
    
    def __init__(self):
        """Initialize progress service with empty connection registry."""
        # scene_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("Initialized ProgressService")
    
    async def subscribe_to_scene(
        self,
        scene_id: str,
        websocket: WebSocket
    ) -> None:
        """
        Subscribe a WebSocket connection to scene progress updates.
        
        Args:
            scene_id: Scene UUID
            websocket: WebSocket connection to subscribe
        """
        async with self._lock:
            if scene_id not in self._connections:
                self._connections[scene_id] = set()
            
            self._connections[scene_id].add(websocket)
            
            subscriber_count = len(self._connections[scene_id])
            logger.info(
                f"WebSocket subscribed to scene {scene_id}, "
                f"total subscribers: {subscriber_count}"
            )
    
    async def unsubscribe_from_scene(
        self,
        scene_id: str,
        websocket: WebSocket
    ) -> None:
        """
        Unsubscribe a WebSocket connection from scene progress updates.
        
        Args:
            scene_id: Scene UUID
            websocket: WebSocket connection to unsubscribe
        """
        async with self._lock:
            if scene_id in self._connections:
                self._connections[scene_id].discard(websocket)
                
                # Clean up empty sets
                if not self._connections[scene_id]:
                    del self._connections[scene_id]
                
                subscriber_count = len(self._connections.get(scene_id, set()))
                logger.info(
                    f"WebSocket unsubscribed from scene {scene_id}, "
                    f"remaining subscribers: {subscriber_count}"
                )
    
    async def broadcast_progress(
        self,
        scene_id: str,
        progress_data: dict
    ) -> None:
        """
        Broadcast progress update to all subscribers of a scene.
        
        Args:
            scene_id: Scene UUID
            progress_data: Progress data dictionary to broadcast
        """
        async with self._lock:
            if scene_id not in self._connections:
                logger.debug(f"No subscribers for scene {scene_id}, skipping broadcast")
                return
            
            # Get copy of connections to avoid modification during iteration
            connections = list(self._connections[scene_id])
        
        # Broadcast outside the lock to avoid blocking
        failed_connections = []
        
        for websocket in connections:
            try:
                await websocket.send_json(progress_data)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                failed_connections.append(websocket)
        
        # Remove failed connections
        if failed_connections:
            async with self._lock:
                if scene_id in self._connections:
                    for websocket in failed_connections:
                        self._connections[scene_id].discard(websocket)
                    
                    # Clean up empty sets
                    if not self._connections[scene_id]:
                        del self._connections[scene_id]
            
            logger.info(
                f"Removed {len(failed_connections)} failed connections "
                f"from scene {scene_id}"
            )
        
        successful_count = len(connections) - len(failed_connections)
        logger.debug(
            f"Broadcast to {successful_count} subscribers for scene {scene_id}"
        )
    
    async def get_subscriber_count(self, scene_id: str) -> int:
        """
        Get count of active WebSocket subscribers for a scene.
        
        Args:
            scene_id: Scene UUID
            
        Returns:
            Number of active subscribers
        """
        async with self._lock:
            return len(self._connections.get(scene_id, set()))
    
    async def disconnect_all(self, scene_id: str) -> None:
        """
        Disconnect all WebSocket connections for a scene.
        
        Args:
            scene_id: Scene UUID
        """
        async with self._lock:
            if scene_id in self._connections:
                connections = list(self._connections[scene_id])
                del self._connections[scene_id]
                
                logger.info(
                    f"Disconnecting {len(connections)} subscribers "
                    f"from scene {scene_id}"
                )
        
        # Close connections outside the lock
        for websocket in connections:
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")


# Global progress service instance
_progress_service: ProgressService = None


def get_progress_service() -> ProgressService:
    """
    Get the global progress service instance.
    
    Returns:
        ProgressService singleton instance
    """
    global _progress_service
    
    if _progress_service is None:
        _progress_service = ProgressService()
    
    return _progress_service
