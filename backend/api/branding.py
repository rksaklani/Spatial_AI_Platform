"""
White-Label Branding API

Allows organizations to customize platform appearance
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import uuid

from api.deps import get_current_user
from models.user import UserInDB
from utils.database import get_db
from utils.config import settings
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/branding", tags=["branding"])


class BrandingConfig(BaseModel):
    """Branding configuration model"""
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    company_name: str
    tagline: Optional[str] = None
    primary_color: str = "#3b82f6"
    secondary_color: str = "#1e40af"
    accent_color: str = "#06b6d4"
    custom_domain: Optional[str] = None
    hide_powered_by: bool = False
    custom_css: Optional[str] = None


@router.get("/config", response_model=BrandingConfig)
async def get_branding_config(
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get organization's branding configuration
    """
    org = await db.organizations.find_one({
        "_id": current_user.organization_id
    })
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    branding = org.get("branding", {})
    
    return BrandingConfig(
        logo_url=branding.get("logo_url"),
        favicon_url=branding.get("favicon_url"),
        company_name=branding.get("company_name", org.get("name", "")),
        tagline=branding.get("tagline"),
        primary_color=branding.get("primary_color", "#3b82f6"),
        secondary_color=branding.get("secondary_color", "#1e40af"),
        accent_color=branding.get("accent_color", "#06b6d4"),
        custom_domain=branding.get("custom_domain"),
        hide_powered_by=branding.get("hide_powered_by", False),
        custom_css=branding.get("custom_css"),
    )


@router.put("/config")
async def update_branding_config(
    config: BrandingConfig,
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Update organization's branding configuration
    
    Requires admin role
    """
    # Check if user is admin
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update branding configuration"
        )
    
    # Update organization branding
    await db.organizations.update_one(
        {"_id": current_user.organization_id},
        {
            "$set": {
                "branding": config.dict(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(
        "branding_config_updated",
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )
    
    return {"message": "Branding configuration updated successfully"}


@router.post("/upload/logo")
async def upload_logo(
    logo: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload organization logo
    
    Accepts: PNG, JPG, SVG
    Max size: 2MB
    """
    # Check if user is admin
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload branding assets"
        )
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/svg+xml"]
    if logo.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PNG, JPG, SVG"
        )
    
    # Validate file size (2MB)
    content = await logo.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Max size: 2MB"
        )
    
    # Generate unique filename
    ext = os.path.splitext(logo.filename)[1]
    filename = f"{current_user.organization_id}_logo_{uuid.uuid4()}{ext}"
    
    # Save file
    upload_dir = os.path.join(settings.storage_path, "branding")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate URL
    logo_url = f"/static/branding/{filename}"
    
    logger.info(
        "logo_uploaded",
        organization_id=current_user.organization_id,
        filename=filename
    )
    
    return {"url": logo_url}


@router.post("/upload/favicon")
async def upload_favicon(
    favicon: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload organization favicon
    
    Accepts: ICO, PNG
    Recommended: 32x32px
    """
    # Check if user is admin
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload branding assets"
        )
    
    # Validate file type
    allowed_types = ["image/x-icon", "image/png"]
    if favicon.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: ICO, PNG"
        )
    
    # Validate file size (500KB)
    content = await favicon.read()
    if len(content) > 500 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Max size: 500KB"
        )
    
    # Generate unique filename
    ext = os.path.splitext(favicon.filename)[1]
    filename = f"{current_user.organization_id}_favicon_{uuid.uuid4()}{ext}"
    
    # Save file
    upload_dir = os.path.join(settings.storage_path, "branding")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate URL
    favicon_url = f"/static/branding/{filename}"
    
    logger.info(
        "favicon_uploaded",
        organization_id=current_user.organization_id,
        filename=filename
    )
    
    return {"url": favicon_url}


@router.get("/public/{organization_id}")
async def get_public_branding(
    organization_id: str,
    db = Depends(get_db)
):
    """
    Get public branding configuration for an organization
    
    Used for public pages (login, signup, public viewer)
    """
    org = await db.organizations.find_one({"_id": organization_id})
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    branding = org.get("branding", {})
    
    # Return only public-safe branding info
    return {
        "logo_url": branding.get("logo_url"),
        "favicon_url": branding.get("favicon_url"),
        "company_name": branding.get("company_name", org.get("name", "")),
        "tagline": branding.get("tagline"),
        "primary_color": branding.get("primary_color", "#3b82f6"),
        "secondary_color": branding.get("secondary_color", "#1e40af"),
        "accent_color": branding.get("accent_color", "#06b6d4"),
        "hide_powered_by": branding.get("hide_powered_by", False),
    }
