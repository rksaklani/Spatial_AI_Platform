"""
Tenant context service for multi-tenant operations.

Task 2.4: Multi-tenant data isolation
Provides dependencies for injecting tenant-aware repositories
into API endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
import structlog

from models.user import UserInDB
from models.organization import OrganizationInDB
from api.deps import get_current_user
from services.tenant_repository import (
    TenantRepository,
    SceneRepository,
    ProcessingJobRepository,
    AnnotationRepository,
    GuidedTourRepository,
    ShareTokenRepository,
    SceneObjectRepository,
    SceneTileRepository,
    get_repository,
)
from services.access_logger import AccessLogger, get_access_logger
from utils.database import get_db

logger = structlog.get_logger(__name__)


class TenantContext:
    """
    Context object containing tenant information and repositories.
    
    Provides convenient access to organization-scoped repositories
    and logging utilities.
    """
    
    def __init__(
        self,
        user: UserInDB,
        organization_id: str,
        organization: Optional[dict] = None,
        request: Optional[Request] = None,
    ):
        self.user = user
        self.organization_id = organization_id
        self.organization = organization
        self.request = request
        self._access_logger = get_access_logger()
    
    @property
    def user_id(self) -> str:
        """Get the current user's ID."""
        return self.user.id
    
    @property
    def client_ip(self) -> Optional[str]:
        """Get the client's IP address from the request."""
        if self.request and self.request.client:
            return self.request.client.host
        return None
    
    @property
    def user_agent(self) -> Optional[str]:
        """Get the client's user agent from the request."""
        if self.request:
            return self.request.headers.get("user-agent")
        return None
    
    # Repository accessors
    @property
    def scenes(self) -> SceneRepository:
        """Get tenant-scoped scene repository."""
        return SceneRepository(self.organization_id)
    
    @property
    def processing_jobs(self) -> ProcessingJobRepository:
        """Get tenant-scoped processing job repository."""
        return ProcessingJobRepository(self.organization_id)
    
    @property
    def annotations(self) -> AnnotationRepository:
        """Get tenant-scoped annotation repository."""
        return AnnotationRepository(self.organization_id)
    
    @property
    def guided_tours(self) -> GuidedTourRepository:
        """Get tenant-scoped guided tour repository."""
        return GuidedTourRepository(self.organization_id)
    
    @property
    def share_tokens(self) -> ShareTokenRepository:
        """Get tenant-scoped share token repository."""
        return ShareTokenRepository(self.organization_id)
    
    @property
    def scene_objects(self) -> SceneObjectRepository:
        """Get tenant-scoped scene object repository."""
        return SceneObjectRepository(self.organization_id)
    
    @property
    def scene_tiles(self) -> SceneTileRepository:
        """Get tenant-scoped scene tile repository."""
        return SceneTileRepository(self.organization_id)
    
    def get_repository(self, collection_name: str) -> TenantRepository:
        """Get a tenant-scoped repository for any collection."""
        return get_repository(collection_name, self.organization_id)
    
    @property
    def access_logger(self) -> AccessLogger:
        """Get the access logger."""
        return self._access_logger


async def get_tenant_context(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> TenantContext:
    """
    Dependency that provides tenant context for multi-tenant operations.
    
    Requires the user to have an active organization. If the user
    doesn't have an organization, raises 403 Forbidden.
    
    Usage:
        @router.get("/scenes")
        async def list_scenes(ctx: TenantContext = Depends(get_tenant_context)):
            scenes = await ctx.scenes.find_many({"status": "completed"})
            return scenes
    """
    from datetime import datetime
    
    if not current_user.organization_id:
        logger.warning(
            "tenant_context_missing_org",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization required. Please create or join an organization."
        )
    
    db = await get_db()
    
    # SECURITY: Verify user is still a member (membership could have been removed)
    membership = await db.organization_members.find_one({
        "organization_id": current_user.organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        # Auto-fix: Create membership if user has organization_id but no membership record
        # This can happen if the membership record was accidentally deleted
        logger.warning(
            "tenant_context_membership_missing_auto_fix",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Create the missing membership record
        from datetime import datetime
        member_doc = {
            "organization_id": current_user.organization_id,
            "user_id": current_user.id,
            "role": "member",  # Default role
            "joined_at": datetime.utcnow(),
        }
        await db.organization_members.insert_one(member_doc)
        membership = member_doc
        
        logger.info(
            "tenant_context_membership_created",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
    
    # Fetch organization details
    org = await db.organizations.find_one({"_id": current_user.organization_id})
    
    if not org:
        # Auto-fix: Create default organization if user has organization_id but org doesn't exist
        logger.warning(
            "tenant_context_org_not_found_auto_fix",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Create a default organization
        from datetime import datetime, timedelta
        org_doc = {
            "_id": current_user.organization_id,
            "name": f"{current_user.email.split('@')[0]}'s Organization",
            "slug": current_user.organization_id[:8],
            "owner_id": current_user.id,
            "subscription_tier": "free_trial",
            "trial_expires_at": datetime.utcnow() + timedelta(days=30),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "max_seats": 5,
            "max_scenes": 10,
            "max_storage_gb": 50,
            "settings": {
                "max_scenes": 10,
                "max_storage_gb": 50,
                "max_users": 5,
            },
        }
        await db.organizations.insert_one(org_doc)
        org = org_doc
        
        logger.info(
            "tenant_context_org_created",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
    
    if not org.get("is_active", True):
        logger.warning(
            "tenant_context_org_inactive",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive. Please contact support."
        )
    
    # SECURITY: Check trial expiration
    trial_expires = org.get("trial_expires_at")
    subscription_tier = org.get("subscription_tier", "free_trial")
    
    if subscription_tier == "free_trial" and trial_expires:
        if isinstance(trial_expires, datetime) and trial_expires < datetime.utcnow():
            logger.warning(
                "tenant_context_trial_expired",
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                trial_expires_at=trial_expires.isoformat()
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your free trial has expired. Please upgrade to continue."
            )
    
    # Store in request state for access logging
    request.state.organization_id = org["_id"]
    request.state.user_id = current_user.id
    request.state.user_role = membership.get("role")
    
    return TenantContext(
        user=current_user,
        organization_id=org["_id"],
        organization=org,
        request=request,
    )


async def get_optional_tenant_context(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> Optional[TenantContext]:
    """
    Dependency that provides optional tenant context.
    
    Returns TenantContext if user has an organization, None otherwise.
    Use this for endpoints that can work with or without organization context.
    
    Usage:
        @router.get("/profile")
        async def get_profile(ctx: Optional[TenantContext] = Depends(get_optional_tenant_context)):
            if ctx:
                # User has organization context
                pass
            else:
                # User doesn't have organization
                pass
    """
    from datetime import datetime
    
    if not current_user.organization_id:
        return None
    
    db = await get_db()
    
    # SECURITY: Verify user is still a member
    membership = await db.organization_members.find_one({
        "organization_id": current_user.organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        return None
    
    org = await db.organizations.find_one({"_id": current_user.organization_id})
    
    if not org or not org.get("is_active", True):
        return None
    
    # Check trial expiration
    trial_expires = org.get("trial_expires_at")
    subscription_tier = org.get("subscription_tier", "free_trial")
    
    if subscription_tier == "free_trial" and trial_expires:
        if isinstance(trial_expires, datetime) and trial_expires < datetime.utcnow():
            return None
    
    request.state.organization_id = org["_id"]
    request.state.user_id = current_user.id
    request.state.user_role = membership.get("role")
    
    return TenantContext(
        user=current_user,
        organization_id=org["_id"],
        organization=org,
        request=request,
    )


# ============================================================================
# Specialized Repository Dependencies
# ============================================================================

async def get_scene_repository(
    ctx: TenantContext = Depends(get_tenant_context),
) -> SceneRepository:
    """Dependency to get tenant-scoped scene repository."""
    return ctx.scenes


async def get_annotation_repository(
    ctx: TenantContext = Depends(get_tenant_context),
) -> AnnotationRepository:
    """Dependency to get tenant-scoped annotation repository."""
    return ctx.annotations


async def get_processing_job_repository(
    ctx: TenantContext = Depends(get_tenant_context),
) -> ProcessingJobRepository:
    """Dependency to get tenant-scoped processing job repository."""
    return ctx.processing_jobs


async def get_share_token_repository(
    ctx: TenantContext = Depends(get_tenant_context),
) -> ShareTokenRepository:
    """Dependency to get tenant-scoped share token repository."""
    return ctx.share_tokens
