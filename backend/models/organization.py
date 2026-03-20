"""Organization model for multi-tenancy support."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    FREE_TRIAL = "free_trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrganizationBase(BaseModel):
    """Base organization properties."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class OrganizationInDB(OrganizationBase):
    """Internal organization model stored in MongoDB."""
    id: str = Field(alias="_id")
    owner_id: str  # User ID who created the organization
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE_TRIAL
    max_seats: int = 1
    max_scenes: int = 3
    max_storage_gb: int = 5
    trial_expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class OrganizationResponse(OrganizationBase):
    """Response model for organization data."""
    id: str = Field(alias="_id")
    owner_id: str
    subscription_tier: str
    max_seats: int
    max_scenes: int
    max_storage_gb: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    
    class Config:
        populate_by_name = True


class OrganizationMember(BaseModel):
    """Organization membership record."""
    id: str = Field(alias="_id")
    organization_id: str
    user_id: str
    role: str = "member"  # owner, admin, member, viewer
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class AddMemberRequest(BaseModel):
    """Request to add a member to an organization."""
    user_email: str
    role: str = "member"


class UpdateMemberRoleRequest(BaseModel):
    """Request to update a member's role."""
    role: str
