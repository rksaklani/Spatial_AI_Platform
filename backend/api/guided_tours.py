"""Guided Tours API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models.guided_tour import (
    GuidedTourCreate,
    GuidedTourInDB,
    GuidedTourResponse,
    CameraKeyframe
)
from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db

router = APIRouter(prefix="/api/v1/scenes/{scene_id}/tours", tags=["guided_tours"])


@router.post("", response_model=GuidedTourResponse, status_code=status.HTTP_201_CREATED)
async def create_guided_tour(
    scene_id: str,
    tour_data: GuidedTourCreate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new guided tour for a scene.
    
    Records camera positions at 10 samples/second with optional text narration.
    Stores tour data to MongoDB guided_tours collection.
    
    Requirements: 15.1, 15.2, 15.3
    """
    # Validate scene exists and user has access
    scene_oid = ObjectId(scene_id)
    scene = await db.scenes.find_one({
        "_id": scene_oid,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found or access denied"
        )
    
    # Calculate tour duration from camera path
    if not tour_data.camera_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Camera path cannot be empty"
        )
    
    duration = max(keyframe.timestamp for keyframe in tour_data.camera_path)
    
    # Create tour document
    tour_doc = GuidedTourInDB(
        scene_id=scene_oid,
        user_id=current_user.id,
        name=tour_data.name,
        camera_path=tour_data.camera_path,
        narration=tour_data.narration,
        duration=duration,
        created_at=datetime.utcnow()
    )
    
    # Insert into database
    result = await db.guided_tours.insert_one(tour_doc.dict(by_alias=True, exclude={"id"}))
    tour_doc.id = result.inserted_id
    
    # Return response
    return GuidedTourResponse(
        id=str(tour_doc.id),
        scene_id=str(tour_doc.scene_id),
        user_id=str(tour_doc.user_id),
        name=tour_doc.name,
        camera_path=tour_doc.camera_path,
        narration=tour_doc.narration,
        duration=tour_doc.duration,
        created_at=tour_doc.created_at
    )


@router.get("", response_model=List[GuidedTourResponse])
async def list_guided_tours(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all guided tours for a scene.
    
    Returns tours created by any user with access to the scene.
    """
    # Validate scene exists and user has access
    scene_oid = ObjectId(scene_id)
    scene = await db.scenes.find_one({
        "_id": scene_oid,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found or access denied"
        )
    
    # Find all tours for this scene
    cursor = db.guided_tours.find({"scene_id": scene_oid})
    tours = await cursor.to_list(length=100)
    
    # Convert to response format
    return [
        GuidedTourResponse(
            id=str(tour["_id"]),
            scene_id=str(tour["scene_id"]),
            user_id=str(tour["user_id"]),
            name=tour["name"],
            camera_path=[CameraKeyframe(**kf) for kf in tour["camera_path"]],
            narration=tour.get("narration", []),
            duration=tour["duration"],
            created_at=tour["created_at"]
        )
        for tour in tours
    ]


@router.get("/{tour_id}", response_model=GuidedTourResponse)
async def get_guided_tour(
    scene_id: str,
    tour_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get a specific guided tour by ID.
    
    Returns tour details including camera path and narration.
    """
    # Validate scene exists and user has access
    scene_oid = ObjectId(scene_id)
    scene = await db.scenes.find_one({
        "_id": scene_oid,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found or access denied"
        )
    
    # Find tour
    tour_oid = ObjectId(tour_id)
    tour = await db.guided_tours.find_one({
        "_id": tour_oid,
        "scene_id": scene_oid
    })
    
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guided tour not found"
        )
    
    # Return response
    return GuidedTourResponse(
        id=str(tour["_id"]),
        scene_id=str(tour["scene_id"]),
        user_id=str(tour["user_id"]),
        name=tour["name"],
        camera_path=[CameraKeyframe(**kf) for kf in tour["camera_path"]],
        narration=tour.get("narration", []),
        duration=tour["duration"],
        created_at=tour["created_at"]
    )


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guided_tour(
    scene_id: str,
    tour_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete a guided tour.
    
    Only the tour creator or organization admin can delete tours.
    """
    # Validate scene exists and user has access
    scene_oid = ObjectId(scene_id)
    scene = await db.scenes.find_one({
        "_id": scene_oid,
        "organization_id": current_user.organization_id
    })
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found or access denied"
        )
    
    # Find tour
    tour_oid = ObjectId(tour_id)
    tour = await db.guided_tours.find_one({
        "_id": tour_oid,
        "scene_id": scene_oid
    })
    
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guided tour not found"
        )
    
    # Check if user is tour creator
    if str(tour["user_id"]) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the tour creator can delete this tour"
        )
    
    # Delete tour
    await db.guided_tours.delete_one({"_id": tour_oid})
    
    return None


# ============================================================================
# Public Tour Access via Share Token
# ============================================================================

@router.get("/shared/{token}/tours", response_model=List[GuidedTourResponse])
async def list_tours_by_share_token(
    token: str,
    db = Depends(get_db)
):
    """
    List guided tours for a scene accessed via share token.
    
    Public endpoint - no authentication required.
    Allows tours to be shared via Share_Tokens.
    
    Requirements: 15.7
    """
    # Validate share token
    share_token = await db.share_tokens.find_one({"token": token})
    
    if not share_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid share token"
        )
    
    # Check if token is active (not revoked and not expired)
    if share_token.get("revoked_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has been revoked"
        )
    
    if share_token.get("expires_at") and share_token["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has expired"
        )
    
    # Get scene ID from token
    scene_id = share_token["scene_id"]
    
    # Find all tours for this scene
    cursor = db.guided_tours.find({"scene_id": ObjectId(scene_id)})
    tours = await cursor.to_list(length=100)
    
    # Convert to response format
    return [
        GuidedTourResponse(
            id=str(tour["_id"]),
            scene_id=str(tour["scene_id"]),
            user_id=str(tour["user_id"]),
            name=tour["name"],
            camera_path=[CameraKeyframe(**kf) for kf in tour["camera_path"]],
            narration=tour.get("narration", []),
            duration=tour["duration"],
            created_at=tour["created_at"]
        )
        for tour in tours
    ]


@router.get("/shared/{token}/tours/{tour_id}", response_model=GuidedTourResponse)
async def get_tour_by_share_token(
    token: str,
    tour_id: str,
    db = Depends(get_db)
):
    """
    Get a specific guided tour via share token.
    
    Public endpoint - no authentication required.
    Includes tour in shareable URLs.
    
    Requirements: 15.7
    """
    # Validate share token
    share_token = await db.share_tokens.find_one({"token": token})
    
    if not share_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid share token"
        )
    
    # Check if token is active
    if share_token.get("revoked_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has been revoked"
        )
    
    if share_token.get("expires_at") and share_token["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has expired"
        )
    
    # Get scene ID from token
    scene_id = share_token["scene_id"]
    
    # Find tour
    tour_oid = ObjectId(tour_id)
    tour = await db.guided_tours.find_one({
        "_id": tour_oid,
        "scene_id": ObjectId(scene_id)
    })
    
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guided tour not found"
        )
    
    # Return response
    return GuidedTourResponse(
        id=str(tour["_id"]),
        scene_id=str(tour["scene_id"]),
        user_id=str(tour["user_id"]),
        name=tour["name"],
        camera_path=[CameraKeyframe(**kf) for kf in tour["camera_path"]],
        narration=tour.get("narration", []),
        duration=tour["duration"],
        created_at=tour["created_at"]
    )
