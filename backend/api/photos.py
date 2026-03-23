"""
Photo management API endpoints for gigapixel photo inspector.

Task 28.1: Photo Upload Endpoint
- Accept JPEG, PNG, TIFF up to 500 megapixels
- Extract EXIF metadata (GPS, camera orientation)
- Store photos to MinIO
- Requirements: 26.1, 26.2
"""

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
import structlog
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from models.photo import (
    PhotoCreate,
    PhotoUpdate,
    PhotoInDB,
    PhotoResponse,
    PhotoListResponse,
    PhotoFormat,
    EXIFMetadata,
    GPSCoordinates,
    CameraOrientation,
    PhotoAlignment,
)
from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db
from utils.minio_client import get_minio_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/photos", tags=["photos"])

# Allowed photo formats and max size
ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
ALLOWED_PHOTO_MIMETYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
}
MAX_PHOTO_MEGAPIXELS = 500  # 500 megapixels
MAX_PHOTO_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB for safety


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()


def determine_photo_format(filename: str, content_type: Optional[str]) -> Optional[PhotoFormat]:
    """Determine photo format from filename and content type."""
    ext = get_file_extension(filename)
    
    if ext in {".jpg", ".jpeg"}:
        return PhotoFormat.JPEG
    elif ext == ".png":
        return PhotoFormat.PNG
    elif ext in {".tiff", ".tif"}:
        return PhotoFormat.TIFF
    
    # Try content type
    if content_type:
        if "jpeg" in content_type:
            return PhotoFormat.JPEG
        elif "png" in content_type:
            return PhotoFormat.PNG
        elif "tiff" in content_type:
            return PhotoFormat.TIFF
    
    return None


def extract_gps_coordinates(gps_info: dict) -> Optional[GPSCoordinates]:
    """
    Extract GPS coordinates from EXIF GPS info.
    
    Args:
        gps_info: Dictionary of GPS EXIF tags
        
    Returns:
        GPSCoordinates or None if GPS data is incomplete
    """
    try:
        # Get latitude
        if 2 not in gps_info or 1 not in gps_info:  # GPSLatitude, GPSLatitudeRef
            return None
        
        lat = gps_info[2]
        lat_ref = gps_info[1]
        
        # Convert to decimal degrees
        latitude = float(lat[0]) + float(lat[1]) / 60 + float(lat[2]) / 3600
        if lat_ref == 'S':
            latitude = -latitude
        
        # Get longitude
        if 4 not in gps_info or 3 not in gps_info:  # GPSLongitude, GPSLongitudeRef
            return None
        
        lon = gps_info[4]
        lon_ref = gps_info[3]
        
        # Convert to decimal degrees
        longitude = float(lon[0]) + float(lon[1]) / 60 + float(lon[2]) / 3600
        if lon_ref == 'W':
            longitude = -longitude
        
        # Get altitude (optional)
        altitude = None
        if 6 in gps_info:  # GPSAltitude
            altitude = float(gps_info[6])
            if 5 in gps_info and gps_info[5] == 1:  # GPSAltitudeRef (below sea level)
                altitude = -altitude
        
        return GPSCoordinates(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude
        )
    except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
        logger.warning("gps_extraction_failed", error=str(e))
        return None


def extract_exif_metadata(image: Image.Image) -> Optional[EXIFMetadata]:
    """
    Extract EXIF metadata from PIL Image.
    
    Args:
        image: PIL Image object
        
    Returns:
        EXIFMetadata or None if no EXIF data
    """
    try:
        exif_data = image.getexif()
        if not exif_data:
            # Return basic metadata without EXIF
            width, height = image.size
            megapixels = (width * height) / 1_000_000
            return EXIFMetadata(width=width, height=height, megapixels=megapixels)
        
        # Build metadata dict
        metadata = {}
        
        # Extract standard EXIF tags
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            metadata[tag_name] = value
        
        # Extract GPS info
        gps_coords = None
        if 'GPSInfo' in metadata:
            gps_info = {}
            for key, val in metadata['GPSInfo'].items():
                gps_tag = GPSTAGS.get(key, key)
                gps_info[key] = val
            gps_coords = extract_gps_coordinates(gps_info)
        
        # Get image dimensions
        width, height = image.size
        megapixels = (width * height) / 1_000_000
        
        # Parse capture datetime
        capture_datetime = None
        if 'DateTime' in metadata or 'DateTimeOriginal' in metadata:
            dt_str = metadata.get('DateTimeOriginal') or metadata.get('DateTime')
            try:
                capture_datetime = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
        
        # Extract camera info
        camera_make = metadata.get('Make')
        camera_model = metadata.get('Model')
        lens_model = metadata.get('LensModel')
        
        # Extract exposure settings
        focal_length = None
        if 'FocalLength' in metadata:
            fl = metadata['FocalLength']
            if isinstance(fl, tuple):
                focal_length = float(fl[0]) / float(fl[1]) if fl[1] != 0 else None
            else:
                focal_length = float(fl)
        
        aperture = None
        if 'FNumber' in metadata:
            fn = metadata['FNumber']
            if isinstance(fn, tuple):
                aperture = float(fn[0]) / float(fn[1]) if fn[1] != 0 else None
            else:
                aperture = float(fn)
        
        iso = metadata.get('ISOSpeedRatings')
        if isinstance(iso, (list, tuple)):
            iso = iso[0] if iso else None
        
        shutter_speed = None
        if 'ExposureTime' in metadata:
            et = metadata['ExposureTime']
            if isinstance(et, tuple):
                shutter_speed = f"1/{int(et[1]/et[0])}" if et[0] != 0 else None
            else:
                shutter_speed = str(et)
        
        return EXIFMetadata(
            camera_make=camera_make,
            camera_model=camera_model,
            lens_model=lens_model,
            focal_length=focal_length,
            aperture=aperture,
            iso=iso,
            shutter_speed=shutter_speed,
            capture_datetime=capture_datetime,
            gps=gps_coords,
            orientation=None,  # Camera orientation not typically in EXIF
            width=width,
            height=height,
            megapixels=megapixels
        )
    except Exception as e:
        logger.error("exif_extraction_failed", error=str(e))
        # Return basic metadata
        width, height = image.size
        megapixels = (width * height) / 1_000_000
        return EXIFMetadata(width=width, height=height, megapixels=megapixels)


def validate_photo_file(filename: str, content_type: Optional[str], image: Image.Image) -> tuple[bool, str]:
    """
    Validate photo file format and size.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check extension
    ext = get_file_extension(filename)
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        return False, f"Invalid file format. Allowed: {', '.join(ALLOWED_PHOTO_EXTENSIONS)}"
    
    # Check MIME type if provided
    if content_type and content_type not in ALLOWED_PHOTO_MIMETYPES:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type not in ALLOWED_PHOTO_MIMETYPES:
            return False, f"Invalid content type: {content_type}"
    
    # Check megapixels
    width, height = image.size
    megapixels = (width * height) / 1_000_000
    
    if megapixels > MAX_PHOTO_MEGAPIXELS:
        return False, f"Photo too large. Maximum: {MAX_PHOTO_MEGAPIXELS} megapixels (got {megapixels:.1f}MP)"
    
    return True, ""


# ============================================================================
# Photo CRUD Endpoints
# ============================================================================

@router.post("/scenes/{scene_id}/photos", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    scene_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Upload a photo to a scene.
    
    - Accepts JPEG, PNG, TIFF formats
    - Maximum size: 500 megapixels
    - Extracts EXIF metadata including GPS coordinates
    - Stores photo in MinIO
    - Creates photo metadata in MongoDB
    
    Requirements: 26.1, 26.2
    """
    db = await get_db()
    
    # Verify scene exists and user has access
    scene = await db.scenes.find_one({"_id": scene_id})
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    if scene["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scene"
        )
    
    organization_id = scene["organization_id"]
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum: {MAX_PHOTO_SIZE_BYTES / (1024**3):.1f}GB"
        )
    
    # Load image with PIL
    try:
        image = Image.open(BytesIO(file_content))
    except Exception as e:
        logger.error("image_load_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # Validate photo
    is_valid, error_msg = validate_photo_file(file.filename, file.content_type, image)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Determine format
    photo_format = determine_photo_format(file.filename, file.content_type)
    if not photo_format:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine photo format"
        )
    
    # Extract EXIF metadata
    exif_metadata = extract_exif_metadata(image)
    
    # Generate photo ID
    photo_id = str(uuid.uuid4())
    ext = get_file_extension(file.filename)
    
    # Determine storage path
    original_path = f"photos/{organization_id}/{scene_id}/{photo_id}/original{ext}"
    
    # Upload to MinIO
    try:
        minio = get_minio_client()
        
        # Ensure bucket exists
        if not minio.bucket_exists("photos"):
            minio.create_bucket("photos")
        
        # Upload file
        file_stream = BytesIO(file_content)
        
        minio.client.put_object(
            bucket_name="photos",
            object_name=f"{organization_id}/{scene_id}/{photo_id}/original{ext}",
            data=file_stream,
            length=file_size,
            content_type=file.content_type or "image/jpeg"
        )
        
        logger.info(
            "photo_uploaded_to_minio",
            photo_id=photo_id,
            scene_id=scene_id,
            path=original_path,
            size_bytes=file_size
        )
    except Exception as e:
        logger.error("minio_upload_failed", photo_id=photo_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store photo file"
        )
    
    # Create initial alignment if GPS data is available
    alignment = None
    if exif_metadata and exif_metadata.gps:
        # For now, just mark that GPS is available
        # Actual 3D alignment will be done in task 28.2
        alignment = PhotoAlignment(
            position_3d=[0.0, 0.0, 0.0],  # Placeholder
            is_aligned=False,
            alignment_method="gps",
            alignment_confidence=0.0
        )
    
    # Create photo document
    now = datetime.utcnow()
    
    photo_doc = {
        "_id": photo_id,
        "scene_id": scene_id,
        "organization_id": organization_id,
        "uploader_id": current_user.id,
        "filename": file.filename,
        "description": description,
        "format": photo_format.value,
        "file_size_bytes": file_size,
        "mime_type": file.content_type or "image/jpeg",
        "original_path": original_path,
        "thumbnail_path": None,
        "tiles_path": None,
        "exif": exif_metadata.model_dump() if exif_metadata else None,
        "alignment": alignment.model_dump() if alignment else None,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.photos.insert_one(photo_doc)
    
    logger.info(
        "photo_created",
        photo_id=photo_id,
        scene_id=scene_id,
        organization_id=organization_id,
        uploader_id=current_user.id,
        filename=file.filename,
        megapixels=exif_metadata.megapixels if exif_metadata else 0
    )
    
    return PhotoResponse(**photo_doc)


@router.get("/scenes/{scene_id}/photos", response_model=PhotoListResponse)
async def list_photos(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    List all photos for a scene.
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
        if not scene.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this scene"
            )
    
    # Fetch photos
    cursor = db.photos.find({"scene_id": scene_id}).sort("created_at", -1)
    photos = await cursor.to_list(length=1000)
    
    items = [PhotoResponse(**p) for p in photos]
    
    return PhotoListResponse(items=items, total=len(items))


@router.get("/photos/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get photo details by ID.
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check organization access
    if photo["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    return PhotoResponse(**photo)


@router.patch("/photos/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    photo_id: str,
    photo_update: PhotoUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update photo metadata.
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    if photo["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    # Build update
    update_data = {}
    if photo_update.description is not None:
        update_data["description"] = photo_update.description
    if photo_update.alignment is not None:
        update_data["alignment"] = photo_update.alignment.model_dump()
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.photos.update_one(
        {"_id": photo_id},
        {"$set": update_data}
    )
    
    # Fetch updated photo
    photo = await db.photos.find_one({"_id": photo_id})
    
    logger.info("photo_updated", photo_id=photo_id, updated_by=current_user.id)
    
    return PhotoResponse(**photo)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Delete a photo and all associated data.
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check ownership
    if photo["uploader_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the photo uploader can delete it"
        )
    
    # Delete from MinIO
    try:
        minio = get_minio_client()
        organization_id = photo["organization_id"]
        scene_id = photo["scene_id"]
        
        # Delete all photo files
        objects = minio.client.list_objects(
            "photos",
            prefix=f"{organization_id}/{scene_id}/{photo_id}/",
            recursive=True
        )
        for obj in objects:
            minio.client.remove_object("photos", obj.object_name)
            
    except Exception as e:
        logger.error("minio_delete_failed", photo_id=photo_id, error=str(e))
        # Continue with MongoDB deletion even if MinIO cleanup fails
    
    # Delete photo document
    await db.photos.delete_one({"_id": photo_id})
    
    logger.info("photo_deleted", photo_id=photo_id, deleted_by=current_user.id)
    
    return None


# ============================================================================
# Photo Alignment Endpoints
# ============================================================================

@router.post("/photos/{photo_id}/align", response_model=PhotoResponse)
async def align_photo_with_scene(
    photo_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Align photo with 3D scene using GPS coordinates.
    
    - Uses GPS metadata from EXIF to position photo in 3D space
    - Displays photo markers at capture locations
    
    Requirements: 26.3, 26.4
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    if photo["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    # Check if photo has GPS data
    exif = photo.get("exif")
    if not exif or not exif.get("gps"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo does not have GPS metadata"
        )
    
    gps = exif["gps"]
    
    # Get scene to check if it has geospatial data
    scene = await db.scenes.find_one({"_id": photo["scene_id"]})
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # For now, use a simple conversion from GPS to local 3D coordinates
    # In a real implementation, this would use the scene's coordinate system
    # and proper geospatial transformations
    
    # Simple approach: Use GPS as relative coordinates
    # Latitude -> Y, Longitude -> X, Altitude -> Z
    latitude = gps["latitude"]
    longitude = gps["longitude"]
    altitude = gps.get("altitude", 0.0) or 0.0
    
    # Convert to local coordinates (simplified)
    # In production, this would use proper coordinate transformation
    # based on the scene's origin and coordinate system
    position_3d = [
        longitude * 111320.0,  # Rough meters per degree longitude at equator
        altitude,
        latitude * 110540.0,   # Rough meters per degree latitude
    ]
    
    # Create alignment
    alignment = PhotoAlignment(
        position_3d=position_3d,
        rotation_3d=None,  # Camera orientation not implemented yet
        is_aligned=True,
        alignment_method="gps",
        alignment_confidence=0.8  # High confidence for GPS alignment
    )
    
    # Update photo
    await db.photos.update_one(
        {"_id": photo_id},
        {
            "$set": {
                "alignment": alignment.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Fetch updated photo
    photo = await db.photos.find_one({"_id": photo_id})
    
    logger.info(
        "photo_aligned",
        photo_id=photo_id,
        method="gps",
        position=position_3d
    )
    
    return PhotoResponse(**photo)


@router.post("/photos/{photo_id}/align/manual", response_model=PhotoResponse)
async def align_photo_manually(
    photo_id: str,
    position_3d: List[float] = Query(..., min_length=3, max_length=3),
    rotation_3d: Optional[List[float]] = Query(None, min_length=4, max_length=4),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Manually align photo with 3D scene.
    
    - Allows user to specify exact 3D position and rotation
    - Useful when GPS data is unavailable or inaccurate
    
    Requirements: 26.3, 26.4
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    if photo["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    # Create alignment
    alignment = PhotoAlignment(
        position_3d=position_3d,
        rotation_3d=rotation_3d,
        is_aligned=True,
        alignment_method="manual",
        alignment_confidence=1.0  # User-specified, so full confidence
    )
    
    # Update photo
    await db.photos.update_one(
        {"_id": photo_id},
        {
            "$set": {
                "alignment": alignment.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Fetch updated photo
    photo = await db.photos.find_one({"_id": photo_id})
    
    logger.info(
        "photo_aligned",
        photo_id=photo_id,
        method="manual",
        position=position_3d
    )
    
    return PhotoResponse(**photo)


@router.get("/scenes/{scene_id}/photo-markers", response_model=List[dict])
async def get_photo_markers(
    scene_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get photo markers for display in 3D scene.
    
    Returns list of photo positions and metadata for rendering markers.
    
    Requirements: 26.4
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
        if not scene.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this scene"
            )
    
    # Fetch aligned photos
    cursor = db.photos.find({
        "scene_id": scene_id,
        "alignment.is_aligned": True
    })
    photos = await cursor.to_list(length=1000)
    
    # Build marker list
    markers = []
    for photo in photos:
        alignment = photo.get("alignment")
        if alignment and alignment.get("is_aligned"):
            markers.append({
                "photo_id": photo["_id"],
                "filename": photo["filename"],
                "position": alignment["position_3d"],
                "rotation": alignment.get("rotation_3d"),
                "thumbnail_url": photo.get("thumbnail_url"),
                "megapixels": photo.get("exif", {}).get("megapixels", 0),
                "capture_datetime": photo.get("exif", {}).get("capture_datetime"),
            })
    
    return markers


@router.get("/photos/{photo_id}/download")
async def download_photo(
    photo_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Download photo file.
    
    Returns the original photo file for viewing.
    """
    db = await get_db()
    
    photo = await db.photos.find_one({"_id": photo_id})
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    if photo["organization_id"] != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    # Get photo from MinIO
    try:
        minio = get_minio_client()
        organization_id = photo["organization_id"]
        scene_id = photo["scene_id"]
        
        # Extract path components
        original_path = photo["original_path"]
        # Format: photos/{org_id}/{scene_id}/{photo_id}/original.{ext}
        path_parts = original_path.split("/", 1)
        if len(path_parts) == 2:
            object_name = path_parts[1]
        else:
            object_name = original_path
        
        # Get object from MinIO
        response = minio.client.get_object("photos", object_name)
        
        # Stream response
        return StreamingResponse(
            response.stream(),
            media_type=photo["mime_type"],
            headers={
                "Content-Disposition": f'inline; filename="{photo["filename"]}"'
            }
        )
    except Exception as e:
        logger.error("photo_download_failed", photo_id=photo_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download photo"
        )


