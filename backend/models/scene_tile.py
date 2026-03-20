"""
Scene tile model for hierarchical 3D scene storage.

Supports octree-based spatial tiling for efficient streaming
of large Gaussian Splatting scenes (up to 1B Gaussians).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class LODLevel(str, Enum):
    """Level of Detail levels."""
    HIGH = "high"      # 100% Gaussians
    MEDIUM = "medium"  # 50% Gaussians
    LOW = "low"        # 20% Gaussians


class BoundingBox(BaseModel):
    """3D axis-aligned bounding box."""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float
    
    @property
    def center(self) -> tuple:
        """Get center point of bounding box."""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        )
    
    @property
    def size(self) -> tuple:
        """Get size (width, height, depth) of bounding box."""
        return (
            self.max_x - self.min_x,
            self.max_y - self.min_y,
            self.max_z - self.min_z,
        )
    
    def contains_point(self, x: float, y: float, z: float) -> bool:
        """Check if point is inside bounding box."""
        return (
            self.min_x <= x <= self.max_x and
            self.min_y <= y <= self.max_y and
            self.min_z <= z <= self.max_z
        )
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects another."""
        return (
            self.min_x <= other.max_x and self.max_x >= other.min_x and
            self.min_y <= other.max_y and self.max_y >= other.min_y and
            self.min_z <= other.max_z and self.max_z >= other.min_z
        )


class SceneTileInDB(BaseModel):
    """Scene tile stored in MongoDB."""
    id: str = Field(alias="_id")  # L{level}_X{x}_Y{y}_Z{z}_{lod}
    scene_id: str
    organization_id: str
    
    # Octree position
    level: int  # Octree depth level (0 = root)
    x: int  # X index at this level
    y: int  # Y index at this level
    z: int  # Z index at this level
    lod: LODLevel = LODLevel.HIGH
    
    # Spatial bounds
    bounding_box: BoundingBox
    
    # Content info
    gaussian_count: int
    file_size_bytes: int
    
    # Storage
    file_path: str  # MinIO path: scenes/{sceneId}/tiles/{level}/{x}_{y}_{z}_{lod}.ply
    
    # Parent/child relationships
    parent_tile_id: Optional[str] = None
    child_tile_ids: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class SceneTileResponse(BaseModel):
    """Response model for scene tile."""
    id: str = Field(alias="_id")
    scene_id: str
    level: int
    x: int
    y: int
    z: int
    lod: str
    bounding_box: BoundingBox
    gaussian_count: int
    file_size_bytes: int
    file_path: str
    
    class Config:
        populate_by_name = True


class TileRequest(BaseModel):
    """Request for tiles within a view frustum."""
    scene_id: str
    camera_position: tuple  # (x, y, z)
    camera_direction: tuple  # (x, y, z) normalized
    fov_degrees: float = 60.0
    max_distance: float = 100.0
    lod_bias: float = 1.0  # Higher = prefer lower LOD


class TileHierarchy(BaseModel):
    """Hierarchical tile structure for a scene."""
    scene_id: str
    root_bounding_box: BoundingBox
    total_tiles: int
    total_gaussians: int
    max_level: int
    tiles_per_level: Dict[int, int]
