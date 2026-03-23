"""
Annotation model for scene annotations.

Represents user-created annotations including comments, measurements,
markers, and defects with photo attachments.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    """Type of annotation."""
    COMMENT = "comment"
    MEASUREMENT = "measurement"
    MARKER = "marker"
    DEFECT = "defect"


class DefectCategory(str, Enum):
    """Category of defect annotation."""
    CRACK = "crack"
    DAMAGE = "damage"
    CORROSION = "corrosion"
    WATER_DAMAGE = "water_damage"
    STRUCTURAL_ISSUE = "structural_issue"
    CUSTOM = "custom"


class SeverityLevel(str, Enum):
    """Severity level for defect annotations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Position3D(BaseModel):
    """3D position in scene coordinates."""
    x: float
    y: float
    z: float


class MeasurementData(BaseModel):
    """Measurement-specific data."""
    measurement_type: str = Field(..., description="Type: distance, area, volume")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit: m, m2, m3, etc.")
    points: List[Position3D] = Field(default_factory=list, description="Measurement points")


class DefectData(BaseModel):
    """Defect-specific data."""
    category: DefectCategory
    severity: SeverityLevel = SeverityLevel.MEDIUM
    custom_category: Optional[str] = None
    photo_paths: List[str] = Field(default_factory=list, description="MinIO paths to defect photos")


class AnnotationBase(BaseModel):
    """Base annotation properties."""
    annotation_type: AnnotationType
    position: Position3D
    content: str = Field(..., min_length=1, max_length=5000)


class AnnotationCreate(AnnotationBase):
    """Schema for creating a new annotation."""
    measurement_data: Optional[MeasurementData] = None
    defect_data: Optional[DefectData] = None
    metadata: Optional[Dict[str, Any]] = None


class AnnotationUpdate(BaseModel):
    """Schema for updating an annotation."""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    position: Optional[Position3D] = None
    measurement_data: Optional[MeasurementData] = None
    defect_data: Optional[DefectData] = None
    metadata: Optional[Dict[str, Any]] = None


class AnnotationInDB(AnnotationBase):
    """Internal annotation model stored in MongoDB."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    user_id: str
    user_name: str  # Cached for display
    
    # Type-specific data
    measurement_data: Optional[MeasurementData] = None
    defect_data: Optional[DefectData] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class AnnotationResponse(AnnotationBase):
    """Response model for annotation data."""
    id: str = Field(alias="_id")
    scene_id: str
    organization_id: str
    user_id: str
    user_name: str
    measurement_data: Optional[MeasurementData] = None
    defect_data: Optional[DefectData] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class AnnotationListResponse(BaseModel):
    """Response model for annotation list."""
    items: List[AnnotationResponse]
    total: int
