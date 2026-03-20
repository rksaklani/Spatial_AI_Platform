from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user properties visible everywhere."""
    email: EmailStr
    full_name: str
    organization_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""
    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    """Internal user model including MongoDB `_id` and hashed password."""
    # We represent MongoDB's '_id' as 'id' in pydantic using str
    id: str = Field(alias="_id", default_factory=str)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(UserBase):
    """Model returned to clients to exclude sensitive fields like passwords."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
