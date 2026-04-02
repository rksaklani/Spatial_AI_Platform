"""
Password-Protected Sharing API endpoints
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
import structlog

from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db
from utils.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["protected-sharing"])

settings = get_settings()


class ProtectedShareCreate(BaseModel):
    """Request model for creating password-protected share"""
    password: str
    expires_in_days: int = 7


class ProtectedShareResponse(BaseModel):
    """Response model for protected share"""
    share_id: str
    share_url: str
    expires_at: str


class ProtectedShareAccess(BaseModel):
    """Request model for accessing protected share"""
    password: str


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/scenes/{scene_id}/share/protected", response_model=ProtectedShareResponse)
async def create_protected_share(
    scene_id: str,
    share_data: ProtectedShareCreate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a password-protected share link for a scene
    
    - Generates unique share ID
    - Hashes password for security
    - Sets expiration date
    - Returns shareable URL
    """
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Generate share ID
    share_id = str(uuid.uuid4())
    
    # Hash password
    password_hash = hash_password(share_data.password)
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)
    
    # Store protected share
    await db.protected_shares.insert_one({
        "_id": share_id,
        "scene_id": scene_id,
        "organization_id": current_user.organization_id,
        "created_by": current_user.id,
        "password_hash": password_hash,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "access_count": 0,
    })
    
    # Build share URL
    share_url = f"{settings.frontend_url}/protected/{share_id}"
    
    logger.info(
        "protected_share_created",
        share_id=share_id,
        scene_id=scene_id,
        user_id=current_user.id,
        expires_at=expires_at.isoformat()
    )
    
    return ProtectedShareResponse(
        share_id=share_id,
        share_url=share_url,
        expires_at=expires_at.isoformat()
    )


@router.post("/protected-shares/{share_id}/access")
async def access_protected_share(
    share_id: str,
    access_data: ProtectedShareAccess,
    db = Depends(get_db)
):
    """
    Verify password and grant access to protected share
    
    - Validates password
    - Checks expiration
    - Increments access counter
    - Returns scene data if valid
    """
    # Find protected share
    protected_share = await db.protected_shares.find_one({"_id": share_id})
    
    if not protected_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check expiration
    if protected_share["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Verify password
    password_hash = hash_password(access_data.password)
    if password_hash != protected_share["password_hash"]:
        # Log failed attempt
        await db.protected_shares.update_one(
            {"_id": share_id},
            {"$inc": {"failed_attempts": 1}}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Increment access counter
    await db.protected_shares.update_one(
        {"_id": share_id},
        {
            "$inc": {"access_count": 1},
            "$set": {"last_accessed_at": datetime.utcnow()}
        }
    )
    
    # Get scene data
    scene = await db.scenes.find_one({"_id": protected_share["scene_id"]})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    logger.info(
        "protected_share_accessed",
        share_id=share_id,
        scene_id=protected_share["scene_id"]
    )
    
    return {
        "scene_id": scene["_id"],
        "scene_name": scene.get("name", "Untitled"),
        "access_granted": True
    }


@router.delete("/protected-shares/{share_id}")
async def revoke_protected_share(
    share_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Revoke a protected share link
    
    - Verifies ownership
    - Deletes share record
    """
    # Find protected share
    protected_share = await db.protected_shares.find_one({
        "_id": share_id,
        "organization_id": current_user.organization_id
    })
    
    if not protected_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Delete share
    await db.protected_shares.delete_one({"_id": share_id})
    
    logger.info(
        "protected_share_revoked",
        share_id=share_id,
        user_id=current_user.id
    )
    
    return {"message": "Protected share revoked successfully"}


@router.get("/protected-shares/scene/{scene_id}")
async def list_protected_shares(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all protected shares for a scene
    """
    # Verify scene access
    scene = await db.scenes.find_one({
        "_id": scene_id,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Get protected shares
    cursor = db.protected_shares.find({
        "scene_id": scene_id,
        "organization_id": current_user.organization_id
    }).sort("created_at", -1)
    
    shares = await cursor.to_list(length=None)
    
    # Filter out expired shares and format response
    active_shares = []
    for share in shares:
        if share["expires_at"] > datetime.utcnow():
            active_shares.append({
                "share_id": share["_id"],
                "created_at": share["created_at"].isoformat(),
                "expires_at": share["expires_at"].isoformat(),
                "access_count": share.get("access_count", 0),
                "share_url": f"{settings.frontend_url}/protected/{share['_id']}"
            })
    
    return {"shares": active_shares}
