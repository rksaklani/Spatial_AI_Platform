"""Guided Tour Model"""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class CameraKeyframe(BaseModel):
    """Camera position and rotation at a specific timestamp"""
    position: List[float] = Field(..., description="Camera position [x, y, z]")
    rotation: List[float] = Field(..., description="Camera rotation as quaternion [x, y, z, w]")
    timestamp: float = Field(..., description="Timestamp in seconds from tour start")

    class Config:
        json_schema_extra = {
            "example": {
                "position": [0.0, 1.5, 5.0],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "timestamp": 0.0
            }
        }


class Narration(BaseModel):
    """Text narration at a specific timestamp"""
    timestamp: float = Field(..., description="Timestamp in seconds from tour start")
    text: str = Field(..., description="Narration text content")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 2.5,
                "text": "This is the main entrance of the building"
            }
        }


class GuidedTourCreate(BaseModel):
    """Schema for creating a new guided tour"""
    name: str = Field(..., description="Tour name")
    camera_path: List[CameraKeyframe] = Field(..., description="Camera keyframes recorded at 10 samples/second")
    narration: List[Narration] = Field(default_factory=list, description="Narration entries")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Building Walkthrough",
                "camera_path": [
                    {
                        "position": [0.0, 1.5, 5.0],
                        "rotation": [0.0, 0.0, 0.0, 1.0],
                        "timestamp": 0.0
                    },
                    {
                        "position": [2.0, 1.5, 5.0],
                        "rotation": [0.0, 0.1, 0.0, 0.995],
                        "timestamp": 0.1
                    }
                ],
                "narration": [
                    {
                        "timestamp": 0.0,
                        "text": "Welcome to the building tour"
                    }
                ]
            }
        }


class GuidedTourInDB(BaseModel):
    """Guided tour as stored in MongoDB"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    scene_id: PyObjectId = Field(..., description="Scene this tour belongs to")
    user_id: PyObjectId = Field(..., description="User who created the tour")
    name: str = Field(..., description="Tour name")
    camera_path: List[CameraKeyframe] = Field(..., description="Camera keyframes")
    narration: List[Narration] = Field(default_factory=list, description="Narration entries")
    duration: float = Field(..., description="Total tour duration in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class GuidedTourResponse(BaseModel):
    """Guided tour response for API"""
    id: str = Field(..., description="Tour ID")
    scene_id: str = Field(..., description="Scene ID")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Tour name")
    camera_path: List[CameraKeyframe] = Field(..., description="Camera keyframes")
    narration: List[Narration] = Field(..., description="Narration entries")
    duration: float = Field(..., description="Total tour duration in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "scene_id": "507f1f77bcf86cd799439012",
                "user_id": "507f1f77bcf86cd799439013",
                "name": "Building Walkthrough",
                "camera_path": [],
                "narration": [],
                "duration": 30.5,
                "created_at": "2024-01-01T00:00:00"
            }
        }
