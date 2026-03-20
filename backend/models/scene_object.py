"""
Scene object model for semantic scene analysis.

Represents detected and classified objects in 3D scenes,
including segmentation masks, classifications, and scene graph relationships.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ObjectCategory(str, Enum):
    """Semantic object categories."""
    # Structural
    WALL = "wall"
    FLOOR = "floor"
    CEILING = "ceiling"
    DOOR = "door"
    WINDOW = "window"
    STAIRS = "stairs"
    
    # Furniture
    CHAIR = "chair"
    TABLE = "table"
    SOFA = "sofa"
    BED = "bed"
    DESK = "desk"
    CABINET = "cabinet"
    SHELF = "shelf"
    
    # Objects
    LAMP = "lamp"
    PLANT = "plant"
    ARTWORK = "artwork"
    APPLIANCE = "appliance"
    ELECTRONICS = "electronics"
    
    # People/Animals
    PERSON = "person"
    ANIMAL = "animal"
    
    # Vehicles
    VEHICLE = "vehicle"
    
    # Outdoor
    TREE = "tree"
    BUILDING = "building"
    ROAD = "road"
    
    # Generic
    OBJECT = "object"
    UNKNOWN = "unknown"


class ObjectBoundingBox3D(BaseModel):
    """3D oriented bounding box for an object."""
    center_x: float
    center_y: float
    center_z: float
    width: float   # X extent
    height: float  # Y extent
    depth: float   # Z extent
    rotation_x: float = 0.0  # Euler angles in radians
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    
    @property
    def volume(self) -> float:
        """Calculate volume of bounding box."""
        return self.width * self.height * self.depth
    
    @property
    def min_point(self) -> tuple:
        """Get minimum corner (ignoring rotation)."""
        return (
            self.center_x - self.width / 2,
            self.center_y - self.height / 2,
            self.center_z - self.depth / 2,
        )
    
    @property
    def max_point(self) -> tuple:
        """Get maximum corner (ignoring rotation)."""
        return (
            self.center_x + self.width / 2,
            self.center_y + self.height / 2,
            self.center_z + self.depth / 2,
        )


class SegmentationMask(BaseModel):
    """2D segmentation mask reference for an object."""
    frame_index: int
    mask_path: str  # MinIO path to mask image
    confidence: float
    area_pixels: int


class SceneObjectInDB(BaseModel):
    """Scene object stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    
    # Classification
    category: ObjectCategory
    label: str  # Human-readable label
    confidence: float  # Classification confidence 0-1
    
    # Alternative classifications
    alternative_labels: List[Dict[str, float]] = Field(default_factory=list)
    
    # 3D geometry
    bounding_box: ObjectBoundingBox3D
    centroid: tuple  # (x, y, z)
    
    # Segmentation masks (per frame)
    masks: List[SegmentationMask] = Field(default_factory=list)
    
    # Scene graph relationships
    parent_object_id: Optional[str] = None  # e.g., table contains objects
    child_object_ids: List[str] = Field(default_factory=list)
    
    # Spatial relationships
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    # e.g., [{"relation": "on_top_of", "target_id": "obj_123"}, ...]
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict)
    # e.g., {"color": "brown", "material": "wood", "is_movable": True}
    
    # Gaussian indices (which Gaussians belong to this object)
    gaussian_indices: List[int] = Field(default_factory=list)
    gaussian_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class SceneObjectResponse(BaseModel):
    """Response model for scene object."""
    id: str = Field(alias="_id")
    scene_id: str
    category: str
    label: str
    confidence: float
    bounding_box: ObjectBoundingBox3D
    centroid: tuple
    gaussian_count: int
    parent_object_id: Optional[str] = None
    child_object_ids: List[str] = []
    properties: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


class SceneGraph(BaseModel):
    """Hierarchical scene graph representation."""
    scene_id: str
    root_objects: List[str]  # Top-level object IDs
    object_count: int
    category_counts: Dict[str, int]
    relationships: List[Dict[str, Any]]
    
    # Spatial statistics
    scene_bounds: Dict[str, float]
    scene_center: tuple
    total_gaussian_count: int


class ObjectDetectionResult(BaseModel):
    """Result from SAM + CLIP object detection."""
    frame_index: int
    detections: List[Dict[str, Any]]
    # Each detection: {mask, bbox, category, confidence, embedding}


class ClassificationRequest(BaseModel):
    """Request to classify detected segments."""
    scene_id: str
    frame_indices: Optional[List[int]] = None
    min_confidence: float = 0.5
    categories: Optional[List[str]] = None  # Filter to specific categories
