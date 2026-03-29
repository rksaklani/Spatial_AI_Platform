"""
Share token model for scene sharing.

Represents a shareable link token that grants access to a scene
with specific permission levels.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for shared scenes."""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


class ShareTokenBase(BaseModel):
    """Base share token properties."""
    scene_id: str
    permission_level: PermissionLevel = PermissionLevel.VIEW
    expires_at: Optional[datetime] = None


class ShareTokenCreate(ShareTokenBase):
    """Schema for creating a new share token."""
    pass


class ShareTokenInDB(ShareTokenBase):
    """Internal share token model stored in MongoDB."""
    id: str = Field(alias="_id")
    token: str  # Unique token string (UUID)
    created_by: str  # User ID who created the token
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class ShareTokenResponse(BaseModel):
    """Response model for share token data."""
    id: str = Field(alias="_id")
    scene_id: str
    token: str
    permission_level: str
    shareable_url: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    is_active: bool
    
    class Config:
        populate_by_name = True


class ShareTokenUpdate(BaseModel):
    """Schema for updating share token."""
    permission_level: Optional[PermissionLevel] = None
    expires_at: Optional[datetime] = None
