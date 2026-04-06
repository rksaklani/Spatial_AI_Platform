"""
Annotation management API endpoints.

Phase 6 Task 23: Scene Annotations
- Create annotations with 3D position, type, content
- Support types: comment, measurement, marker, defect
- Calculate measurements (distance, area)
- Edit and delete annotations
- Defect annotations with photo attachments
"""

import uuid
import math
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
import structlog

from models.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationInDB,
    AnnotationResponse,
    AnnotationListResponse,
    AnnotationType,
    DefectCategory,
    SeverityLevel,
    Position3D,
    MeasurementData,
)
from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db
from utils.minio_client import get_minio_client
from services.coordinate_transformer import coordinate_transformer
from models.geospatial import GeospatialCoordinates

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/scenes/{scene_id}/annotations", tags=["annotations"])


def calculate_distance(p1: Position3D, p2: Position3D, scene_georeferencing=None) -> float:
    """
    Calculate distance between two 3D points.
    Uses geodetic calculations if scene is georeferenced, otherwise Euclidean.
    
    Args:
        p1: First point
        p2: Second point
        scene_georeferencing: Optional scene georeferencing data
        
    Returns:
        Distance in meters
    """
    # If scene is georeferenced and has coordinate data, use geodetic calculation
    if scene_georeferencing and scene_georeferencing.get('is_georeferenced'):
        try:
            # Transform scene coordinates to geospatial coordinates
            # This is simplified - in production would use transformation matrix
            origin = scene_georeferencing.get('origin_coordinates')
            if origin:
                # Create geospatial coordinates for both points
                # Note: This is a simplified transformation
                coord1 = GeospatialCoordinates(
                    latitude=origin['latitude'] + p1.y / 111320.0,  # Approximate degrees
                    longitude=origin['longitude'] + p1.x / (111320.0 * math.cos(math.radians(origin['latitude']))),
                    altitude=origin.get('altitude', 0) + p1.z if origin.get('altitude') else p1.z
                )
                coord2 = GeospatialCoordinates(
                    latitude=origin['latitude'] + p2.y / 111320.0,
                    longitude=origin['longitude'] + p2.x / (111320.0 * math.cos(math.radians(origin['latitude']))),
                    altitude=origin.get('altitude', 0) + p2.z if origin.get('altitude') else p2.z
                )
                
                # Use geodetic distance calculation
                return coordinate_transformer.calculate_geodetic_distance(coord1, coord2)
        except Exception as e:
            logger.warning("Failed to calculate geodetic distance, falling back to Euclidean", error=str(e))
    
    # Fall back to Euclidean distance
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def calculate_polygon_area(points: List[Position3D]) -> float:
    """
    Calculate area of a polygon defined by 3D points.
    Uses projection onto best-fit plane and Shoelace formula.
    
    Args:
        points: List of polygon vertices
        
    Returns:
        Area in square meters
    """
    if len(points) < 3:
        return 0.0
    
    # For simplicity, project onto XY plane
    # In production, would compute best-fit plane
    n = len(points)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    
    return abs(area) / 2.0


def calculate_slope(p1: Position3D, p2: Position3D) -> dict:
    """
    Calculate slope between two 3D points.
    
    Args:
        p1: First point (start)
        p2: Second point (end)
        
    Returns:
        Dictionary with slope_percent, slope_degrees, horizontal_distance, vertical_distance
    """
    # Calculate horizontal distance (XY plane)
    horizontal_distance = math.sqrt(
        (p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2
    )
    
    # Calculate vertical distance (Z axis)
    vertical_distance = p2.z - p1.z
    
    # Avoid division by zero
    if horizontal_distance == 0:
        return {
            "slope_percent": 0.0,
            "slope_degrees": 90.0 if vertical_distance != 0 else 0.0,
            "horizontal_distance": 0.0,
            "vertical_distance": vertical_distance
        }
    
    # Calculate slope as percentage
    slope_percent = (vertical_distance / horizontal_distance) * 100
    
    # Calculate slope in degrees
    slope_degrees = math.degrees(math.atan(vertical_distance / horizontal_distance))
    
    return {
        "slope_percent": slope_percent,
        "slope_degrees": slope_degrees,
        "horizontal_distance": horizontal_distance,
        "vertical_distance": vertical_distance
    }


def calculate_volume(points: List[Position3D]) -> dict:
    """
    Calculate volume using bounding box method.
    
    Args:
        points: List of points defining the volume
        
    Returns:
        Dictionary with volume, width, depth, height
    """
    if len(points) < 4:
        return {
            "volume": 0.0,
            "width": 0.0,
            "depth": 0.0,
            "height": 0.0
        }
    
    # Extract coordinates
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    zs = [p.z for p in points]
    
    # Calculate bounding box dimensions
    width = max(xs) - min(xs)
    depth = max(ys) - min(ys)
    height = max(zs) - min(zs)
    
    # Calculate volume
    volume = width * depth * height
    
    return {
        "volume": volume,
        "width": width,
        "depth": depth,
        "height": height
    }


async def verify_scene_access(scene_id: str, organization_id: str, db) -> dict:
    """
    Verify user has access to scene.
    
    Returns:
        Scene document
        
    Raises:
        HTTPException if scene not found or access denied
    """
    scene = await db.scenes.find_one({"_id": scene_id})
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    if scene["organization_id"] != organization_id:
        # Check if scene is public
        if not scene.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this scene"
            )
    
    return scene


# ============================================================================
# Annotation CRUD Endpoints
# ============================================================================

@router.post("", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    scene_id: str,
    annotation: AnnotationCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Create a new annotation on a scene.
    
    Supports annotation types:
    - comment: Text comment at a 3D position
    - measurement: Distance or area measurement
    - marker: Simple position marker
    - defect: Defect marking with category and severity
    
    For measurement annotations, automatically calculates:
    - Distance between two points
    - Area of polygon (3+ points)
    """
    db = await get_db()
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    # Verify scene access
    scene = await verify_scene_access(scene_id, current_user.organization_id, db)
    
    # Generate annotation ID
    annotation_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Get scene georeferencing for geodetic calculations
    scene_georeferencing = scene.get('georeferencing')
    
    # Process measurement data if provided
    measurement_data = annotation.measurement_data
    if annotation.annotation_type == AnnotationType.MEASUREMENT and measurement_data:
        # Auto-calculate measurement value if not provided
        if measurement_data.measurement_type == "distance" and len(measurement_data.points) >= 2:
            if measurement_data.value == 0.0:
                measurement_data.value = calculate_distance(
                    measurement_data.points[0],
                    measurement_data.points[1],
                    scene_georeferencing
                )
                measurement_data.unit = "m"
        
        elif measurement_data.measurement_type == "area" and len(measurement_data.points) >= 3:
            if measurement_data.value == 0.0:
                measurement_data.value = calculate_polygon_area(measurement_data.points)
                measurement_data.unit = "m²"
        
        elif measurement_data.measurement_type == "slope" and len(measurement_data.points) == 2:
            # Calculate slope
            slope_data = calculate_slope(measurement_data.points[0], measurement_data.points[1])
            measurement_data.value = slope_data["slope_percent"]
            measurement_data.unit = "%"
            # Store additional slope data in metadata
            if not annotation.metadata:
                annotation.metadata = {}
            annotation.metadata.update(slope_data)
        
        elif measurement_data.measurement_type == "volume" and len(measurement_data.points) >= 4:
            # Calculate volume
            volume_data = calculate_volume(measurement_data.points)
            measurement_data.value = volume_data["volume"]
            measurement_data.unit = "m³"
            # Store additional volume data in metadata
            if not annotation.metadata:
                annotation.metadata = {}
            annotation.metadata.update(volume_data)
    
    # Create annotation document
    annotation_doc = {
        "_id": annotation_id,
        "scene_id": scene_id,
        "organization_id": current_user.organization_id,
        "user_id": current_user.id,
        "user_name": current_user.name,
        "annotation_type": annotation.annotation_type.value,
        "position": annotation.position.model_dump(),
        "content": annotation.content,
        "measurement_data": measurement_data.model_dump() if measurement_data else None,
        "defect_data": annotation.defect_data.model_dump() if annotation.defect_data else None,
        "metadata": annotation.metadata or {},
        "created_at": now,
        "updated_at": now,
    }
    
    await db.annotations.insert_one(annotation_doc)
    
    logger.info(
        "annotation_created",
        annotation_id=annotation_id,
        scene_id=scene_id,
        annotation_type=annotation.annotation_type.value,
        user_id=current_user.id
    )
    
    return AnnotationResponse(**annotation_doc)


@router.get("", response_model=AnnotationListResponse)
async def list_annotations(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    annotation_type: Optional[str] = Query(None, description="Filter by annotation type"),
    defect_category: Optional[str] = Query(None, description="Filter by defect category"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
):
    """
    List all annotations for a scene.
    
    Supports filtering by:
    - annotation_type: comment, measurement, marker, defect
    - defect_category: crack, damage, corrosion, etc.
    - severity: low, medium, high, critical
    """
    db = await get_db()
    
    if not current_user.organization_id:
        return AnnotationListResponse(items=[], total=0)
    
    # Verify scene access
    await verify_scene_access(scene_id, current_user.organization_id, db)
    
    # Build query
    query = {"scene_id": scene_id}
    
    if annotation_type:
        query["annotation_type"] = annotation_type
    
    if defect_category:
        query["defect_data.category"] = defect_category
    
    if severity:
        query["defect_data.severity"] = severity
    
    # Get total count
    total = await db.annotations.count_documents(query)
    
    # Fetch annotations
    cursor = db.annotations.find(query).sort("created_at", -1)
    annotations = await cursor.to_list(length=1000)
    
    items = [AnnotationResponse(**a) for a in annotations]
    
    return AnnotationListResponse(items=items, total=total)


@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    scene_id: str,
    annotation_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get annotation details by ID.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    # Verify scene access
    await verify_scene_access(scene_id, current_user.organization_id, db)
    
    annotation = await db.annotations.find_one({
        "_id": annotation_id,
        "scene_id": scene_id
    })
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    return AnnotationResponse(**annotation)


@router.patch("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    scene_id: str,
    annotation_id: str,
    annotation_update: AnnotationUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update an annotation.
    
    Users can only edit their own annotations.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    # Verify scene access
    await verify_scene_access(scene_id, current_user.organization_id, db)
    
    annotation = await db.annotations.find_one({
        "_id": annotation_id,
        "scene_id": scene_id
    })
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Check ownership
    if annotation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own annotations"
        )
    
    # Build update
    update_data = {}
    
    if annotation_update.content is not None:
        update_data["content"] = annotation_update.content
    
    if annotation_update.position is not None:
        update_data["position"] = annotation_update.position.model_dump()
    
    if annotation_update.measurement_data is not None:
        update_data["measurement_data"] = annotation_update.measurement_data.model_dump()
    
    if annotation_update.defect_data is not None:
        update_data["defect_data"] = annotation_update.defect_data.model_dump()
    
    if annotation_update.metadata is not None:
        update_data["metadata"] = annotation_update.metadata
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.annotations.update_one(
        {"_id": annotation_id},
        {"$set": update_data}
    )
    
    # Fetch updated annotation
    annotation = await db.annotations.find_one({"_id": annotation_id})
    
    logger.info(
        "annotation_updated",
        annotation_id=annotation_id,
        scene_id=scene_id,
        user_id=current_user.id
    )
    
    return AnnotationResponse(**annotation)


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    scene_id: str,
    annotation_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Delete an annotation.
    
    Users can only delete their own annotations.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    # Verify scene access
    await verify_scene_access(scene_id, current_user.organization_id, db)
    
    annotation = await db.annotations.find_one({
        "_id": annotation_id,
        "scene_id": scene_id
    })
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Check ownership
    if annotation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own annotations"
        )
    
    # Delete defect photos from MinIO if present
    if annotation.get("defect_data") and annotation["defect_data"].get("photo_paths"):
        try:
            minio = get_minio_client()
            for photo_path in annotation["defect_data"]["photo_paths"]:
                # photo_path format: defects/{scene_id}/{annotation_id}/{filename}
                parts = photo_path.split("/", 1)
                if len(parts) == 2:
                    bucket, key = parts[0], parts[1]
                    minio.client.remove_object(bucket, key)
        except Exception as e:
            logger.warning(
                "defect_photo_delete_failed",
                annotation_id=annotation_id,
                error=str(e)
            )
    
    # Delete annotation
    await db.annotations.delete_one({"_id": annotation_id})
    
    logger.info(
        "annotation_deleted",
        annotation_id=annotation_id,
        scene_id=scene_id,
        user_id=current_user.id
    )
    
    return None


# ============================================================================
# Defect Photo Upload
# ============================================================================

@router.post("/{annotation_id}/photos", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_defect_photo(
    scene_id: str,
    annotation_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Upload a photo attachment for a defect annotation.
    
    Supports JPEG, PNG formats up to 50MB.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    # Verify scene access
    await verify_scene_access(scene_id, current_user.organization_id, db)
    
    # Get annotation
    annotation = await db.annotations.find_one({
        "_id": annotation_id,
        "scene_id": scene_id
    })
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Verify it's a defect annotation
    if annotation["annotation_type"] != AnnotationType.DEFECT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo uploads only supported for defect annotations"
        )
    
    # Check ownership
    if annotation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload photos to your own annotations"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    allowed_types = {"image/jpeg", "image/png", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file
    file_content = await file.read()
    file_size = len(file_content)
    
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 50MB"
        )
    
    # Generate photo ID and path
    photo_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1].lower()
    photo_path = f"defects/{scene_id}/{annotation_id}/{photo_id}.{ext}"
    
    # Upload to MinIO
    try:
        minio = get_minio_client()
        
        # Ensure bucket exists
        if not minio.bucket_exists("defects"):
            minio.create_bucket("defects")
        
        # Upload file
        from io import BytesIO
        file_stream = BytesIO(file_content)
        
        minio.client.put_object(
            bucket_name="defects",
            object_name=f"{scene_id}/{annotation_id}/{photo_id}.{ext}",
            data=file_stream,
            length=file_size,
            content_type=file.content_type
        )
        
        logger.info(
            "defect_photo_uploaded",
            annotation_id=annotation_id,
            photo_path=photo_path,
            size_bytes=file_size
        )
    except Exception as e:
        logger.error("minio_upload_failed", annotation_id=annotation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store photo"
        )
    
    # Update annotation with photo path
    await db.annotations.update_one(
        {"_id": annotation_id},
        {
            "$push": {"defect_data.photo_paths": photo_path},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "photo_id": photo_id,
        "photo_path": photo_path,
        "message": "Photo uploaded successfully"
    }
