"""WebSocket API for real-time scene collaboration."""
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from bson import ObjectId
import structlog

from models.user import UserResponse
from services.collaboration import collaboration_service
from utils.database import Database
from api.deps import get_current_user_ws

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.websocket("/scenes/{scene_id}/collaborate")
async def collaborate_on_scene(
    websocket: WebSocket,
    scene_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time scene collaboration.
    
    Handles:
    - User presence (join/leave events)
    - Cursor position updates
    - Annotation synchronization
    - Real-time messaging
    
    Protocol:
    - Client sends: {"type": "join", "user_id": "...", "user_name": "..."}
    - Client sends: {"type": "heartbeat"}
    - Client sends: {"type": "cursor_move", "position": [x, y, z]}
    - Client sends: {"type": "annotation_create", "annotation": {...}}
    - Client sends: {"type": "annotation_update", "annotation_id": "...", "changes": {...}}
    - Client sends: {"type": "annotation_delete", "annotation_id": "..."}
    
    - Server sends: {"type": "user_joined", "user_id": "...", "user_name": "..."}
    - Server sends: {"type": "user_left", "user_id": "..."}
    - Server sends: {"type": "cursor_update", "user_id": "...", "position": [x, y, z]}
    - Server sends: {"type": "annotation_created", "annotation": {...}}
    - Server sends: {"type": "annotation_updated", "annotation_id": "...", "changes": {...}}
    - Server sends: {"type": "annotation_deleted", "annotation_id": "..."}
    - Server sends: {"type": "active_users", "users": [...]}
    - Server sends: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    
    user_id = None
    user_name = None
    session_joined = False
    
    try:
        # Verify scene exists
        db = Database.get_db()
        scene = await db.scenes.find_one({"_id": scene_id})
        if not scene:
            await websocket.send_json({
                "type": "error",
                "message": "Scene not found"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Check concurrent user limit (50 users per scene)
        user_count = await collaboration_service.get_user_count(scene_id)
        if user_count >= 50:
            await websocket.send_json({
                "type": "error",
                "message": "Scene has reached maximum concurrent users (50)"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "join":
                # User joining the scene
                user_id = message.get("user_id")
                user_name = message.get("user_name", "Anonymous")
                
                if not user_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "user_id is required"
                    })
                    continue
                
                # Store user_id on websocket for exclusion in broadcasts
                websocket.user_id = user_id
                
                # Join the scene
                session = await collaboration_service.join_scene(
                    scene_id=scene_id,
                    user_id=user_id,
                    user_name=user_name,
                    websocket=websocket
                )
                session_joined = True
                
                # Send active users list to the joining user
                active_users = await collaboration_service.get_active_users(scene_id)
                await websocket.send_json({
                    "type": "active_users",
                    "users": active_users
                })
                
                # Broadcast user joined event to others
                await collaboration_service.broadcast_to_scene(
                    scene_id=scene_id,
                    message={
                        "type": "user_joined",
                        "user_id": user_id,
                        "user_name": user_name
                    },
                    exclude_user=user_id
                )
                
                logger.info(
                    "websocket_user_joined",
                    scene_id=scene_id,
                    user_id=user_id,
                    user_name=user_name
                )
            
            elif message_type == "heartbeat":
                # Update heartbeat timestamp
                if user_id:
                    await collaboration_service.update_heartbeat(scene_id, user_id)
            
            elif message_type == "cursor_move":
                # Update cursor position
                if user_id:
                    position = message.get("position")
                    if position and len(position) == 3:
                        await collaboration_service.update_cursor_position(
                            scene_id=scene_id,
                            user_id=user_id,
                            position=tuple(position)
                        )
                        
                        # Broadcast cursor update to others
                        await collaboration_service.broadcast_to_scene(
                            scene_id=scene_id,
                            message={
                                "type": "cursor_update",
                                "user_id": user_id,
                                "position": position
                            },
                            exclude_user=user_id
                        )
            
            elif message_type == "annotation_create":
                # Broadcast annotation creation
                annotation = message.get("annotation")
                if annotation:
                    await collaboration_service.broadcast_to_scene(
                        scene_id=scene_id,
                        message={
                            "type": "annotation_created",
                            "annotation": annotation
                        },
                        exclude_user=user_id
                    )
                    
                    logger.info(
                        "annotation_created_broadcast",
                        scene_id=scene_id,
                        user_id=user_id,
                        annotation_id=annotation.get("id")
                    )
            
            elif message_type == "annotation_update":
                # Broadcast annotation update
                annotation_id = message.get("annotation_id")
                changes = message.get("changes")
                if annotation_id and changes:
                    await collaboration_service.broadcast_to_scene(
                        scene_id=scene_id,
                        message={
                            "type": "annotation_updated",
                            "annotation_id": annotation_id,
                            "changes": changes
                        },
                        exclude_user=user_id
                    )
                    
                    logger.info(
                        "annotation_updated_broadcast",
                        scene_id=scene_id,
                        user_id=user_id,
                        annotation_id=annotation_id
                    )
            
            elif message_type == "annotation_delete":
                # Broadcast annotation deletion
                annotation_id = message.get("annotation_id")
                if annotation_id:
                    await collaboration_service.broadcast_to_scene(
                        scene_id=scene_id,
                        message={
                            "type": "annotation_deleted",
                            "annotation_id": annotation_id
                        },
                        exclude_user=user_id
                    )
                    
                    logger.info(
                        "annotation_deleted_broadcast",
                        scene_id=scene_id,
                        user_id=user_id,
                        annotation_id=annotation_id
                    )
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            scene_id=scene_id,
            user_id=user_id
        )
    
    except Exception as e:
        logger.error(
            "websocket_error",
            scene_id=scene_id,
            user_id=user_id,
            error=str(e),
            exc_info=e
        )
    
    finally:
        # Clean up on disconnect
        if session_joined and user_id:
            await collaboration_service.leave_scene(
                scene_id=scene_id,
                user_id=user_id,
                websocket=websocket
            )
            
            # Broadcast user left event
            await collaboration_service.broadcast_to_scene(
                scene_id=scene_id,
                message={
                    "type": "user_left",
                    "user_id": user_id
                }
            )


@router.get("/scenes/{scene_id}/active-users")
async def get_active_users(
    scene_id: str,
    current_user: UserResponse = Depends(get_current_user_ws)
):
    """
    Get list of active users in a scene.
    
    Args:
        scene_id: Scene identifier
        current_user: Authenticated user
        
    Returns:
        List of active user sessions
    """
    # Verify scene exists and user has access
    db = Database.get_db()
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    active_users = await collaboration_service.get_active_users(scene_id)
    
    return {
        "scene_id": scene_id,
        "active_users": active_users,
        "count": len(active_users)
    }
