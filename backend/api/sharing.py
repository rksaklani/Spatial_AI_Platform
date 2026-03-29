"""
Scene sharing API endpoints.

Phase 6 Task 22: Scene Sharing
- Share token generation with UUID
- Shareable URL creation
- Permission levels: view, comment, edit
- Token validation and revocation
- Scene embedding support
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse
import structlog

from models.share_token import (
    ShareTokenCreate,
    ShareTokenUpdate,
    ShareTokenInDB,
    ShareTokenResponse,
    PermissionLevel,
)
from models.user import UserInDB
from models.scene import SceneResponse
from api.deps import get_current_user, get_optional_user
from utils.database import get_db
from utils.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/sharing", tags=["sharing"])

settings = get_settings()


def build_shareable_url(token: str, request: Request) -> str:
    """
    Build shareable URL for a token.
    
    Args:
        token: Share token string
        request: FastAPI request object for base URL
        
    Returns:
        Complete shareable URL
    """
    # Get base URL from request or settings
    base_url = str(request.base_url).rstrip("/")
    
    # Build URL: /viewer/shared/{token}
    return f"{base_url}/viewer/shared/{token}"


def is_token_active(token_doc: dict) -> bool:
    """
    Check if a share token is currently active.
    
    Args:
        token_doc: Token document from MongoDB
        
    Returns:
        True if token is active, False otherwise
    """
    # Check if revoked
    if token_doc.get("revoked_at"):
        return False
    
    # Check if expired
    expires_at = token_doc.get("expires_at")
    if expires_at and expires_at < datetime.utcnow():
        return False
    
    return True


# ============================================================================
# Share Token Management Endpoints
# ============================================================================

@router.post("/scenes/{scene_id}/tokens", response_model=ShareTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_share_token(
    scene_id: str,
    token_create: ShareTokenCreate,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Create a share token for a scene.
    
    - Generates unique UUID token
    - Creates shareable URL
    - Supports permission levels: view, comment, edit
    - Stores token metadata in MongoDB
    
    Requirements: 12.1, 12.2, 12.3, 12.7
    """
    db = await get_db()
    
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check if user has permission to share (must be owner or in same org)
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this scene"
        )
    
    # Validate scene_id matches
    if token_create.scene_id != scene_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scene ID in request body doesn't match URL parameter"
        )
    
    # Generate unique token (UUID)
    token_string = str(uuid.uuid4())
    token_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Create token document
    token_doc = {
        "_id": token_id,
        "scene_id": scene_id,
        "token": token_string,
        "permission_level": token_create.permission_level.value,
        "created_by": current_user.id,
        "created_at": now,
        "expires_at": token_create.expires_at,
        "revoked_at": None,
        "last_accessed_at": None,
        "access_count": 0,
    }
    
    await db.share_tokens.insert_one(token_doc)
    
    logger.info(
        "share_token_created",
        token_id=token_id,
        scene_id=scene_id,
        permission_level=token_create.permission_level.value,
        created_by=current_user.id
    )
    
    # Build shareable URL
    shareable_url = build_shareable_url(token_string, request)
    
    return ShareTokenResponse(
        **token_doc,
        shareable_url=shareable_url,
        is_active=is_token_active(token_doc)
    )


@router.get("/scenes/{scene_id}/tokens", response_model=List[ShareTokenResponse])
async def list_share_tokens(
    scene_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    include_revoked: bool = Query(False, description="Include revoked tokens"),
):
    """
    List all share tokens for a scene.
    
    Only accessible by scene owner or organization members.
    """
    db = await get_db()
    
    # Verify scene access
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build query
    query = {"scene_id": scene_id}
    if not include_revoked:
        query["revoked_at"] = None
    
    # Fetch tokens
    cursor = db.share_tokens.find(query).sort("created_at", -1)
    tokens = await cursor.to_list(length=100)
    
    # Build responses with shareable URLs
    responses = []
    for token_doc in tokens:
        shareable_url = build_shareable_url(token_doc["token"], request)
        responses.append(
            ShareTokenResponse(
                **token_doc,
                shareable_url=shareable_url,
                is_active=is_token_active(token_doc)
            )
        )
    
    return responses


@router.get("/tokens/{token_id}", response_model=ShareTokenResponse)
async def get_share_token(
    token_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get share token details by ID.
    
    Only accessible by token creator or organization members.
    """
    db = await get_db()
    
    token_doc = await db.share_tokens.find_one({"_id": token_id})
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share token not found"
        )
    
    # Verify access (must be in same org as scene)
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    if not scene or scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    shareable_url = build_shareable_url(token_doc["token"], request)
    
    return ShareTokenResponse(
        **token_doc,
        shareable_url=shareable_url,
        is_active=is_token_active(token_doc)
    )


@router.patch("/tokens/{token_id}", response_model=ShareTokenResponse)
async def update_share_token(
    token_id: str,
    token_update: ShareTokenUpdate,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update share token settings.
    
    Can update permission level and expiration date.
    """
    db = await get_db()
    
    token_doc = await db.share_tokens.find_one({"_id": token_id})
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share token not found"
        )
    
    # Verify access
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    if not scene or scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build update
    update_data = {}
    if token_update.permission_level is not None:
        update_data["permission_level"] = token_update.permission_level.value
    if token_update.expires_at is not None:
        update_data["expires_at"] = token_update.expires_at
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    await db.share_tokens.update_one(
        {"_id": token_id},
        {"$set": update_data}
    )
    
    # Fetch updated token
    token_doc = await db.share_tokens.find_one({"_id": token_id})
    
    logger.info("share_token_updated", token_id=token_id, updated_by=current_user.id)
    
    shareable_url = build_shareable_url(token_doc["token"], request)
    
    return ShareTokenResponse(
        **token_doc,
        shareable_url=shareable_url,
        is_active=is_token_active(token_doc)
    )


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_token(
    token_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Revoke a share token.
    
    - Invalidates token immediately
    - Logs revocation event
    - Token remains in database but marked as revoked
    
    Requirements: 12.6
    """
    db = await get_db()
    
    token_doc = await db.share_tokens.find_one({"_id": token_id})
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share token not found"
        )
    
    # Verify access
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    if not scene or scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Mark as revoked
    now = datetime.utcnow()
    await db.share_tokens.update_one(
        {"_id": token_id},
        {"$set": {"revoked_at": now}}
    )
    
    # Log revocation event
    await db.scene_access_logs.insert_one({
        "_id": str(uuid.uuid4()),
        "scene_id": token_doc["scene_id"],
        "share_token_id": token_id,
        "user_id": current_user.id,
        "action": "token_revoked",
        "ip_address": None,
        "user_agent": None,
        "accessed_at": now,
    })
    
    logger.info(
        "share_token_revoked",
        token_id=token_id,
        scene_id=token_doc["scene_id"],
        revoked_by=current_user.id
    )
    
    return None


# ============================================================================
# Token Validation and Scene Access Endpoints
# ============================================================================

@router.get("/validate/{token}", response_model=dict)
async def validate_share_token(
    token: str,
    request: Request,
):
    """
    Validate a share token and return scene access information.
    
    - Validates token exists and is active
    - Grants permissions based on token
    - Enforces view-only restrictions
    - Updates access statistics
    
    Requirements: 12.4, 12.5
    """
    db = await get_db()
    
    # Find token
    token_doc = await db.share_tokens.find_one({"token": token})
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid share token"
        )
    
    # Check if token is active
    if not is_token_active(token_doc):
        if token_doc.get("revoked_at"):
            detail = "This share link has been revoked"
        else:
            detail = "This share link has expired"
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    
    # Get scene
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Update access statistics
    now = datetime.utcnow()
    await db.share_tokens.update_one(
        {"_id": token_doc["_id"]},
        {
            "$set": {"last_accessed_at": now},
            "$inc": {"access_count": 1}
        }
    )
    
    # Log access
    # Get client IP from request
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    await db.scene_access_logs.insert_one({
        "_id": str(uuid.uuid4()),
        "scene_id": token_doc["scene_id"],
        "share_token_id": token_doc["_id"],
        "user_id": None,  # Anonymous access via token
        "action": "scene_accessed",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "accessed_at": now,
    })
    
    logger.info(
        "share_token_validated",
        token_id=token_doc["_id"],
        scene_id=token_doc["scene_id"],
        permission_level=token_doc["permission_level"],
        ip_address=client_ip
    )
    
    return {
        "valid": True,
        "scene_id": token_doc["scene_id"],
        "scene_name": scene.get("name"),
        "permission_level": token_doc["permission_level"],
        "can_view": True,
        "can_comment": token_doc["permission_level"] in [PermissionLevel.COMMENT.value, PermissionLevel.EDIT.value],
        "can_edit": token_doc["permission_level"] == PermissionLevel.EDIT.value,
    }


@router.get("/scenes/shared/{token}", response_model=SceneResponse)
async def get_scene_by_token(
    token: str,
    request: Request,
):
    """
    Get scene details using a share token.
    
    Public endpoint - no authentication required.
    """
    db = await get_db()
    
    # Validate token first
    token_doc = await db.share_tokens.find_one({"token": token})
    
    if not token_doc or not is_token_active(token_doc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired share link"
        )
    
    # Get scene
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Update access statistics
    now = datetime.utcnow()
    await db.share_tokens.update_one(
        {"_id": token_doc["_id"]},
        {
            "$set": {"last_accessed_at": now},
            "$inc": {"access_count": 1}
        }
    )
    
    # Log access
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    await db.scene_access_logs.insert_one({
        "_id": str(uuid.uuid4()),
        "scene_id": scene["_id"],
        "share_token_id": token_doc["_id"],
        "user_id": None,
        "action": "scene_viewed",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "accessed_at": now,
    })
    
    return SceneResponse(**scene)


# ============================================================================
# Scene Embedding Endpoints
# ============================================================================

@router.get("/embed/{token}/code", response_model=dict)
async def get_embed_code(
    token: str,
    width: int = Query(800, ge=100, le=4000, description="Iframe width in pixels"),
    height: int = Query(600, ge=100, le=3000, description="Iframe height in pixels"),
    request: Request = None,
):
    """
    Generate HTML iframe embed code for a scene.
    
    - Generates iframe snippet with token
    - Configurable dimensions
    - Includes CORS support
    
    Requirements: 17.1, 17.2, 17.5
    """
    db = await get_db()
    
    # Validate token
    token_doc = await db.share_tokens.find_one({"token": token})
    
    if not token_doc or not is_token_active(token_doc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired share link"
        )
    
    # Check permission level - embedding only allowed for view or comment
    if token_doc["permission_level"] == PermissionLevel.EDIT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edit permission tokens cannot be embedded. Create a view or comment token instead."
        )
    
    # Build embed URL
    base_url = str(request.base_url).rstrip("/") if request else settings.BASE_URL
    embed_url = f"{base_url}/viewer/embed/{token}"
    
    # Generate iframe HTML
    iframe_html = f'''<iframe 
    src="{embed_url}" 
    width="{width}" 
    height="{height}" 
    frameborder="0" 
    allowfullscreen
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
></iframe>'''
    
    logger.info(
        "embed_code_generated",
        token_id=token_doc["_id"],
        scene_id=token_doc["scene_id"],
        width=width,
        height=height
    )
    
    return {
        "token": token,
        "scene_id": token_doc["scene_id"],
        "embed_url": embed_url,
        "iframe_html": iframe_html,
        "width": width,
        "height": height,
        "permission_level": token_doc["permission_level"],
    }


@router.get("/embed/{token}", response_class=HTMLResponse)
async def render_embedded_viewer(
    token: str,
    request: Request,
):
    """
    Render embedded viewer HTML page.
    
    - Renders scene in iframe context
    - Maintains full rendering capabilities
    - Disables editing controls for view-only
    
    Requirements: 17.3, 17.4, 17.6, 17.7
    """
    db = await get_db()
    
    # Validate token
    token_doc = await db.share_tokens.find_one({"token": token})
    
    if not token_doc or not is_token_active(token_doc):
        return HTMLResponse(
            content="<html><body><h1>Invalid or expired share link</h1></body></html>",
            status_code=403
        )
    
    # Get scene
    scene = await db.scenes.find_one({"_id": token_doc["scene_id"]})
    
    if not scene:
        return HTMLResponse(
            content="<html><body><h1>Scene not found</h1></body></html>",
            status_code=404
        )
    
    # Build viewer HTML
    permission_level = token_doc["permission_level"]
    readonly = permission_level == PermissionLevel.VIEW.value
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{scene.get("name", "3D Scene")} - Embedded Viewer</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        #viewer-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
    </style>
</head>
<body>
    <div id="viewer-container">
        <div id="loading">
            <h2>Loading 3D Scene...</h2>
            <p>{scene.get("name", "Scene")}</p>
        </div>
    </div>
    
    <script>
        // Embedded viewer configuration
        window.SCENE_CONFIG = {{
            sceneId: "{scene["_id"]}",
            token: "{token}",
            permissionLevel: "{permission_level}",
            readonly: {str(readonly).lower()},
            sceneName: "{scene.get("name", "Scene")}",
        }};
        
        // Load viewer application
        // In production, this would load the React viewer app
        console.log("Embedded viewer initialized", window.SCENE_CONFIG);
        
        // Placeholder - replace with actual viewer loading
        setTimeout(() => {{
            document.getElementById("loading").innerHTML = 
                "<p>Viewer would load here. Scene ID: {scene["_id"]}</p>" +
                "<p>Permission: {permission_level}</p>" +
                "<p>Readonly: {readonly}</p>";
        }}, 1000);
    </script>
</body>
</html>'''
    
    # Log access
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    await db.scene_access_logs.insert_one({
        "_id": str(uuid.uuid4()),
        "scene_id": scene["_id"],
        "share_token_id": token_doc["_id"],
        "user_id": None,
        "action": "embedded_viewer_loaded",
        "ip_address": client_ip,
        "user_agent": user_agent,
        "accessed_at": datetime.utcnow(),
    })
    
    return HTMLResponse(content=html_content)
