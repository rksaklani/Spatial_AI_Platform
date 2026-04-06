"""
Progress WebSocket API endpoints.

Provides real-time progress updates for training jobs via WebSocket connections.
"""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import HTTPException
from jose import jwt, JWTError
from pydantic import ValidationError
import structlog

from models.user import UserInDB
from models.token import TokenPayload
from services.progress_service import get_progress_service
from utils.database import get_db
from utils.config import settings
from utils.valkey_client import ValkeyClient

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/progress", tags=["progress"])


async def authenticate_websocket(token: str) -> Optional[UserInDB]:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        UserInDB if authenticated, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
        
        # Check blacklist
        valkey = ValkeyClient()
        if valkey.is_token_blacklisted(token_data.jti):
            return None
        
        db = await get_db()
        user = await db.users.find_one({"_id": token_data.sub})
        
        if not user:
            return None
        
        return UserInDB(**user)
        
    except (JWTError, ValidationError, Exception) as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None


async def verify_scene_access(scene_id: str, user: UserInDB) -> bool:
    """
    Verify user has access to scene.
    
    Args:
        scene_id: Scene UUID
        user: Authenticated user
        
    Returns:
        True if user has access, False otherwise
    """
    try:
        db = await get_db()
        scene = await db.scenes.find_one({"_id": scene_id})
        
        if not scene:
            return False
        
        return scene.get("organization_id") == user.organization_id
        
    except Exception as e:
        logger.error(f"Error verifying scene access: {e}")
        return False


@router.websocket("/scenes/{scene_id}")
async def progress_websocket(
    websocket: WebSocket,
    scene_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time progress updates.
    
    Clients connect with JWT token in query parameter and receive
    progress updates as JSON messages.
    
    Message types:
    - progress_update: Training progress update
    - training_complete: Training finished successfully
    - training_failed: Training failed with error
    - error: Connection or authentication error
    """
    # Authenticate
    user = await authenticate_websocket(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket authentication failed for scene {scene_id}")
        return
    
    # Verify scene access
    has_access = await verify_scene_access(scene_id, user)
    if not has_access:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            f"User {user.id} denied access to scene {scene_id} via WebSocket"
        )
        return
    
    # Accept connection
    await websocket.accept()
    logger.info(
        f"WebSocket connected for scene {scene_id}, user {user.id}"
    )
    
    # Subscribe to progress updates
    progress_service = get_progress_service()
    await progress_service.subscribe_to_scene(scene_id, websocket)
    
    # Heartbeat tracking
    last_heartbeat = asyncio.get_event_loop().time()
    heartbeat_timeout = 60.0  # 60 seconds
    
    try:
        while True:
            # Wait for message with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0
                )
                
                # Parse message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "heartbeat":
                        # Update heartbeat timestamp
                        last_heartbeat = asyncio.get_event_loop().time()
                        logger.debug(f"Heartbeat received from scene {scene_id}")
                    
                    elif message_type == "subscribe":
                        # Already subscribed, just acknowledge
                        await websocket.send_json({
                            "type": "subscribed",
                            "scene_id": scene_id
                        })
                    
                    else:
                        # Unknown message type
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        })
                
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
            
            except asyncio.TimeoutError:
                # Check heartbeat timeout
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat > heartbeat_timeout:
                    logger.info(
                        f"WebSocket heartbeat timeout for scene {scene_id}"
                    )
                    break
                
                # Continue waiting
                continue
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for scene {scene_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for scene {scene_id}: {e}")
    
    finally:
        # Unsubscribe from progress updates
        await progress_service.unsubscribe_from_scene(scene_id, websocket)
        logger.info(f"WebSocket cleanup complete for scene {scene_id}")
