"""
Photo model for gigapixel photo inspector.

Represents high-resolution photos attached to scenes with EXIF metadata,
GPS coordinates, and alignment information for synchronized viewing.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PhotoFormat(str, Enum):
    """Supported photo formats."""
    JPEG = "jpeg"
    PNG = "png"
    TIFF = "tiff"


class GPSCoordinates(BaseModel):
    """GPS coordinates from EXIF data."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None  # meters above sea level
    accuracy: Optional[float] = None  # meters


class CameraOrientation(BaseModel):
    """Camera orientation from EXIF data."""
    yaw: Optional[float] = None  # degrees, 0-360
    pitch: Optional[float] = None  # degrees, -90 to 90
    roll: Optional[float] = None  # degrees, -180 to 180


class EXIFMetadata(BaseModel):
    """EXIF metadata extracted from photo."""
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[float] = None  # mm
    aperture: Optional[float] = None  # f-number
    iso: Optional[int] = None
    shutter_speed: Optional[str] = None
    capture_datetime: Optional[datetime] = None
    gps: Optional[GPSCoordinates] = None
    orientation: Optional[CameraOrientation] = None
    width: int
    height: int
    megapixels: float


class PhotoAlignment(BaseModel):
    """Photo alignment with 3D scene."""
    position_3d: List[float] = Field(..., min_length=3, max_length=3)  # [x, y, z]
    rotation_3d: Optional[List[float]] = Field(None, min_length=4, max_length=4)  # quaternion [x, y, z, w]
    is_aligned: bool = False
    alignment_method: Optional[str] = None  # "gps", "manual", "automatic"
    alignment_confidence: Optional[float] = Field(None, ge=0, le=1)


class PhotoBase(BaseModel):
    """Base photo properties."""
    filename: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PhotoCreate(PhotoBase):
    """Schema for creating a new photo."""
    pass


class PhotoUpdate(BaseModel):
    """Schema for updating photo metadata."""
    description: Optional[str] = None
    alignment: Optional[PhotoAlignment] = None


class PhotoInDB(PhotoBase):
    """Internal photo model stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    uploader_id: str
    
    # File info
    format: PhotoFormat
    file_size_bytes: int
    mime_type: str
    
    # Storage paths (MinIO keys)
    original_path: str  # photos/{org_id}/{scene_id}/{photo_id}/original.{ext}
    thumbnail_path: Optional[str] = None  # photos/{org_id}/{scene_id}/{photo_id}/thumbnail.jpg
    tiles_path: Optional[str] = None  # photos/{org_id}/{scene_id}/{photo_id}/tiles/
    
    # EXIF metadata
    exif: Optional[EXIFMetadata] = None
    
    # Scene alignment
    alignment: Optional[PhotoAlignment] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class PhotoResponse(PhotoBase):
    """Response model for photo data."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    uploader_id: str
    format: str
    file_size_bytes: int
    exif: Optional[EXIFMetadata] = None
    alignment: Optional[PhotoAlignment] = None
    original_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class PhotoListResponse(BaseModel):
    """Response model for photo list."""
    items: List[PhotoResponse]
    total: int
