"""
Scene model for 3D scene management.

Represents a 3D scene created from video or 3D file upload,
tracking processing status, metadata, and organization ownership.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from models.geospatial import SceneGeoreferencing


class SceneStatus(str, Enum):
    """Scene processing status."""
    UPLOADED = "uploaded"
    EXTRACTING_FRAMES = "extracting_frames"
    ESTIMATING_POSES = "estimating_poses"
    GENERATING_DEPTH = "generating_depth"
    RECONSTRUCTING = "reconstructing"
    TILING = "tiling"
    READY = "ready"
    FAILED = "failed"


class SceneType(str, Enum):
    """Type of scene source."""
    VIDEO = "video"
    IMAGES = "images"  # Photo batch upload
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"
    IMPORT = "import"  # Imported 3D files


class VideoMetadata(BaseModel):
    """Metadata for video source."""
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None


class ProcessingMetrics(BaseModel):
    """Processing pipeline metrics."""
    frame_count: int = 0
    valid_frame_count: int = 0
    depth_map_count: int = 0
    camera_count: int = 0
    point_count: int = 0
    tile_count: int = 0
    processing_time_seconds: float = 0.0


class CameraBoundary(BaseModel):
    """3D bounding box for camera movement limits."""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float


class CameraConfiguration(BaseModel):
    """Camera limits and configuration for scene viewing."""
    # Boundary limits
    boundary: Optional[CameraBoundary] = None
    boundary_enabled: bool = False
    
    # Zoom limits
    min_zoom_distance: float = 0.1
    max_zoom_distance: float = 1000.0
    
    # Axis locks
    lock_x_axis: bool = False
    lock_y_axis: bool = False
    lock_z_axis: bool = False
    
    # Default camera position
    default_position: Optional[List[float]] = None  # [x, y, z]
    default_target: Optional[List[float]] = None  # [x, y, z]
    
    # Rotation control
    rotation_enabled: bool = True
    
    # Boundary indicators
    show_boundary_indicators: bool = True


class SceneBase(BaseModel):
    """Base scene properties."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SceneCreate(SceneBase):
    """Schema for creating a new scene (via upload)."""
    pass


class SceneUpdate(BaseModel):
    """Schema for updating scene metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class SceneInDB(SceneBase):
    """Internal scene model stored in MongoDB."""
    id: str = Field(alias="_id")
    organization_id: str
    owner_id: str
    
    # Source info
    source_type: SceneType = SceneType.VIDEO
    source_format: Optional[str] = None  # File extension: glb, gltf, obj, ply, etc.
    original_filename: str
    file_size_bytes: int
    mime_type: str
    
    # Storage paths (MinIO keys)
    source_path: str  # videos/{org_id}/{scene_id}/original.{ext}
    frames_path: Optional[str] = None  # frames/{scene_id}/
    depth_path: Optional[str] = None  # depth/{scene_id}/
    sparse_path: Optional[str] = None  # scenes/{scene_id}/sparse/
    tiles_path: Optional[str] = None  # scenes/{scene_id}/tiles/
    
    # Processing status
    status: SceneStatus = SceneStatus.UPLOADED
    status_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    video_metadata: Optional[VideoMetadata] = None
    processing_metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics)
    georeferencing: Optional[SceneGeoreferencing] = None
    camera_config: Optional[CameraConfiguration] = None
    
    # Visibility
    is_public: bool = False
    thumbnail_path: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class SceneResponse(SceneBase):
    """Response model for scene data."""
    id: str = Field(alias="_id")
    organization_id: str
    owner_id: str
    source_type: str
    source_format: Optional[str] = None
    original_filename: str
    file_size_bytes: int
    status: str
    status_message: Optional[str] = None
    error_message: Optional[str] = None
    video_metadata: Optional[VideoMetadata] = None
    processing_metrics: ProcessingMetrics
    georeferencing: Optional[SceneGeoreferencing] = None
    camera_config: Optional[CameraConfiguration] = None
    is_public: bool
    thumbnail_url: Optional[str] = None
    file_url: Optional[str] = None  # Direct download URL for imported 3D files
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class SceneListResponse(BaseModel):
    """Response model for scene list with pagination."""
    items: List[SceneResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
