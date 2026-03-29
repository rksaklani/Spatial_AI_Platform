"""
Orthophoto management API endpoints.

Handles upload, georeferencing, and display of orthophotos.
Supports GeoTIFF, JPEG2000, and ECW formats.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import structlog
import os

from api.deps import get_current_user
from utils.database import get_db
from models.user import UserInDB
from models.orthophoto import (
    OrthophotoCreate,
    OrthophotoUpdate,
    OrthophotoResponse,
    OrthophotoListResponse,
    OrthophotoInDB,
    OrthophotoFormat,
)
from utils.minio_client import get_minio_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/orthophotos", tags=["orthophotos"])


# Supported file extensions
SUPPORTED_FORMATS = {
    ".tif": OrthophotoFormat.GEOTIFF,
    ".tiff": OrthophotoFormat.GEOTIFF,
    ".jp2": OrthophotoFormat.JPEG2000,
    ".j2k": OrthophotoFormat.JPEG2000,
    ".ecw": OrthophotoFormat.ECW,
}

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_DIMENSION = 10000  # 10,000 pixels


def validate_orthophoto_format(filename: str) -> OrthophotoFormat:
    """
    Validate orthophoto file format.
    
    Args:
        filename: Original filename
        
    Returns:
        OrthophotoFormat enum
        
    Raises:
        ValueError: If format is not supported
    """
    ext = os.path.splitext(filename.lower())[1]
    
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {ext}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"
        )
    
    return SUPPORTED_FORMATS[ext]


async def parse_georeferencing(file_path: str, format: OrthophotoFormat) -> dict:
    """
    Parse georeferencing metadata from orthophoto file.
    
    This is a placeholder - in production, would use GDAL to read:
    - Coordinate system (EPSG, WKT, PROJ)
    - Geotransform parameters
    - Ground control points
    - Bounding box
    
    Args:
        file_path: Path to orthophoto file
        format: Orthophoto format
        
    Returns:
        Dictionary with georeferencing metadata
    """
    # Placeholder implementation
    # In production, use GDAL:
    # from osgeo import gdal
    # dataset = gdal.Open(file_path)
    # geotransform = dataset.GetGeoTransform()
    # projection = dataset.GetProjection()
    # etc.
    
    return {
        "epsg_code": 4326,  # WGS84
        "wkt": None,
        "proj_string": None,
        "geotransform": [0.0, 1.0, 0.0, 0.0, 0.0, -1.0],  # Placeholder
        "ground_control_points": [],
        "bbox_min_lon": -180.0,
        "bbox_min_lat": -90.0,
        "bbox_max_lon": 180.0,
        "bbox_max_lat": 90.0,
        "width": 1024,
        "height": 1024,
    }


async def tile_orthophoto(file_path: str, tile_size: int = 256) -> str:
    """
    Tile large orthophoto for progressive loading.
    
    This is a placeholder - in production, would use GDAL to:
    - Split orthophoto into tiles
    - Generate multiple zoom levels
    - Store tiles in MinIO
    
    Args:
        file_path: Path to orthophoto file
        tile_size: Tile size in pixels
        
    Returns:
        Path to tiles directory in MinIO
    """
    # Placeholder implementation
    # In production, use GDAL:
    # gdal2tiles.py or custom tiling logic
    
    return f"orthophotos/tiles/{ObjectId()}"


@router.post("/upload", response_model=OrthophotoResponse)
async def upload_orthophoto(
    scene_id: str,
    name: str,
    file: UploadFile = File(...),
    opacity: float = 1.0,
    visible: bool = True,
    layer_order: int = 0,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Upload an orthophoto and parse georeferencing metadata.
    
    Accepts GeoTIFF, JPEG2000, and ECW formats.
    Automatically parses coordinate system and ground control points.
    Tiles large orthophotos (>10,000x10,000 pixels).
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
    
    # Validate file format
    try:
        format = validate_orthophoto_format(file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)} MB"
        )
    
    # Generate orthophoto ID
    orthophoto_id = str(ObjectId())
    
    # Store file to MinIO
    minio_client = get_minio_client()
    file_path = f"orthophotos/{current_user.organization_id}/{scene_id}/{orthophoto_id}/{file.filename}"
    
    try:
        minio_client.put_object(
            "spatial-ai-platform",
            file_path,
            content,
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.error("Failed to upload orthophoto to MinIO", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload orthophoto"
        )
    
    # Parse georeferencing metadata
    # Note: In production, would download file temporarily and use GDAL
    georef = await parse_georeferencing(file_path, format)
    
    # Check if tiling is needed
    is_tiled = False
    tiles_path = None
    if georef["width"] > MAX_DIMENSION or georef["height"] > MAX_DIMENSION:
        is_tiled = True
        tiles_path = await tile_orthophoto(file_path)
    
    # Create orthophoto document
    orthophoto_doc = OrthophotoInDB(
        _id=orthophoto_id,
        scene_id=scene_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        name=name,
        original_filename=file.filename,
        format=format,
        file_size_bytes=file_size,
        file_path=file_path,
        width=georef["width"],
        height=georef["height"],
        epsg_code=georef["epsg_code"],
        wkt=georef["wkt"],
        proj_string=georef["proj_string"],
        geotransform=georef["geotransform"],
        ground_control_points=georef["ground_control_points"],
        bbox_min_lon=georef["bbox_min_lon"],
        bbox_min_lat=georef["bbox_min_lat"],
        bbox_max_lon=georef["bbox_max_lon"],
        bbox_max_lat=georef["bbox_max_lat"],
        opacity=opacity,
        visible=visible,
        layer_order=layer_order,
        is_tiled=is_tiled,
        tiles_path=tiles_path,
    )
    
    await db.orthophotos.insert_one(orthophoto_doc.dict(by_alias=True))
    
    logger.info(
        "orthophoto_uploaded",
        orthophoto_id=orthophoto_id,
        scene_id=scene_id,
        filename=file.filename,
        size_bytes=file_size
    )
    
    return OrthophotoResponse(**orthophoto_doc.dict(by_alias=True))


@router.get("/scenes/{scene_id}", response_model=OrthophotoListResponse)
async def list_scene_orthophotos(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """List all orthophotos for a scene."""
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
    
    # Get orthophotos
    cursor = db.orthophotos.find({
        "scene_id": scene_id,
        "organization_id": current_user.organization_id
    }).sort("layer_order", 1)
    
    orthophotos = await cursor.to_list(length=None)
    
    return OrthophotoListResponse(
        items=[OrthophotoResponse(**op) for op in orthophotos],
        total=len(orthophotos)
    )


@router.get("/{orthophoto_id}", response_model=OrthophotoResponse)
async def get_orthophoto(
    orthophoto_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get orthophoto details."""
    orthophoto = await db.orthophotos.find_one({"_id": orthophoto_id})
    
    if not orthophoto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orthophoto not found"
        )
    
    # Verify access
    if orthophoto["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return OrthophotoResponse(**orthophoto)


@router.put("/{orthophoto_id}", response_model=OrthophotoResponse)
async def update_orthophoto(
    orthophoto_id: str,
    update: OrthophotoUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Update orthophoto settings.
    
    Allows updating:
    - Name
    - Opacity (0-1)
    - Visibility toggle
    - Layer order
    """
    orthophoto = await db.orthophotos.find_one({"_id": orthophoto_id})
    
    if not orthophoto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orthophoto not found"
        )
    
    # Verify access
    if orthophoto["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.orthophotos.update_one(
        {"_id": orthophoto_id},
        {"$set": update_data}
    )
    
    # Get updated orthophoto
    updated = await db.orthophotos.find_one({"_id": orthophoto_id})
    
    return OrthophotoResponse(**updated)


@router.delete("/{orthophoto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_orthophoto(
    orthophoto_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db),
):
    """Delete an orthophoto."""
    orthophoto = await db.orthophotos.find_one({"_id": orthophoto_id})
    
    if not orthophoto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orthophoto not found"
        )
    
    # Verify access
    if orthophoto["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete from MinIO
    minio_client = get_minio_client()
    try:
        minio_client.remove_object("spatial-ai-platform", orthophoto["file_path"])
        
        # Delete tiles if tiled
        if orthophoto.get("is_tiled") and orthophoto.get("tiles_path"):
            # Would need to list and delete all tiles
            pass
    except Exception as e:
        logger.error("Failed to delete orthophoto from MinIO", error=str(e))
    
    # Delete from database
    await db.orthophotos.delete_one({"_id": orthophoto_id})
    
    logger.info("orthophoto_deleted", orthophoto_id=orthophoto_id)
