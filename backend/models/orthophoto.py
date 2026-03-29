"""
Orthophoto model for georeferenced aerial imagery.

Supports GeoTIFF, JPEG2000, and ECW formats.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class OrthophotoFormat(str, Enum):
    """Supported orthophoto formats."""
    GEOTIFF = "geotiff"
    JPEG2000 = "jpeg2000"
    ECW = "ecw"


class OrthophotoInDB(BaseModel):
    """Orthophoto stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str = Field(..., description="Scene identifier")
    organization_id: str = Field(..., description="Organization identifier")
    user_id: str = Field(..., description="User who uploaded the orthophoto")
    
    # File info
    name: str = Field(..., description="Orthophoto name")
    original_filename: str = Field(..., description="Original filename")
    format: OrthophotoFormat = Field(..., description="File format")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="MinIO path to orthophoto file")
    
    # Image dimensions
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    
    # Georeferencing
    epsg_code: Optional[int] = Field(None, description="EPSG code")
    wkt: Optional[str] = Field(None, description="Well-Known Text coordinate system")
    proj_string: Optional[str] = Field(None, description="PROJ string")
    
    # Geotransform: [origin_x, pixel_width, rotation_x, origin_y, rotation_y, pixel_height]
    geotransform: List[float] = Field(..., description="GDAL geotransform parameters")
    
    # Ground control points (if available)
    ground_control_points: List[dict] = Field(default_factory=list)
    
    # Bounding box in geographic coordinates
    bbox_min_lon: float = Field(..., description="Minimum longitude")
    bbox_min_lat: float = Field(..., description="Minimum latitude")
    bbox_max_lon: float = Field(..., description="Maximum longitude")
    bbox_max_lat: float = Field(..., description="Maximum latitude")
    
    # Display settings
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity (0-1)")
    visible: bool = Field(default=True, description="Visibility toggle")
    layer_order: int = Field(default=0, description="Layer ordering (higher = on top)")
    
    # Tiling info (for large orthophotos)
    is_tiled: bool = Field(default=False, description="Whether orthophoto is tiled")
    tile_size: Optional[int] = Field(None, description="Tile size in pixels")
    tiles_path: Optional[str] = Field(None, description="MinIO path to tiles directory")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class OrthophotoCreate(BaseModel):
    """Schema for creating an orthophoto."""
    scene_id: str
    name: str
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    visible: bool = True
    layer_order: int = 0


class OrthophotoUpdate(BaseModel):
    """Schema for updating orthophoto settings."""
    name: Optional[str] = None
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    visible: Optional[bool] = None
    layer_order: Optional[int] = None


class OrthophotoResponse(BaseModel):
    """Response model for orthophoto data."""
    id: str = Field(alias="_id")
    scene_id: str
    name: str
    original_filename: str
    format: str
    file_size_bytes: int
    width: int
    height: int
    epsg_code: Optional[int] = None
    bbox_min_lon: float
    bbox_min_lat: float
    bbox_max_lon: float
    bbox_max_lat: float
    opacity: float
    visible: bool
    layer_order: int
    is_tiled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class OrthophotoListResponse(BaseModel):
    """Response model for orthophoto list."""
    items: List[OrthophotoResponse]
    total: int
