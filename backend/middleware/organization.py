"""
Organization context middleware.

Task 2.3: Organization Management
Provides organization context for multi-tenant operations.
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from functools import wraps
import structlog

from models.organization import OrganizationInDB
from models.user import UserInDB
from api.deps import get_current_user
from utils.database import get_db

logger = structlog.get_logger(__name__)


async def get_organization_context(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> Optional[OrganizationInDB]:
    """
    Dependency that provides organization context for the current request.
    
    Returns the user's active organization if they have one.
    Validates that the organization exists and is active.
    
    Usage:
        @router.get("/items")
        async def list_items(org: OrganizationInDB = Depends(get_organization_context)):
            # org.id contains the organization_id for filtering
            pass
    """
    if not current_user.organization_id:
        return None
    
    db = await get_db()
    org = await db.organizations.find_one({"_id": current_user.organization_id})
    
    if not org:
        logger.warning(
            "organization_not_found",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        return None
    
    if not org.get("is_active", True):
        logger.warning(
            "organization_inactive",
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        return None
    
    # Store in request state for access in other parts of the request
    request.state.organization_id = org["_id"]
    request.state.organization = org
    
    return OrganizationInDB(**org)


async def require_organization(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> OrganizationInDB:
    """
    Dependency that requires an active organization context.
    
    Raises 403 if user doesn't have an active organization.
    
    Usage:
        @router.post("/scenes")
        async def create_scene(org: OrganizationInDB = Depends(require_organization)):
            # Guaranteed to have org context
            pass
    """
    org = await get_organization_context(request, current_user)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization required for this operation"
        )
    
    return org


async def get_user_org_role(
    current_user: UserInDB = Depends(get_current_user),
) -> Optional[str]:
    """
    Get the current user's role in their active organization.
    
    Returns: 'owner', 'admin', 'member', 'viewer', or None
    """
    if not current_user.organization_id:
        return None
    
    db = await get_db()
    membership = await db.organization_members.find_one({
        "organization_id": current_user.organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        return None
    
    return membership.get("role")


def require_org_role(*allowed_roles: str):
    """
    Decorator/dependency factory that requires specific organization roles.
    
    Usage:
        @router.delete("/scenes/{scene_id}")
        async def delete_scene(
            scene_id: str,
            _: None = Depends(require_org_role("owner", "admin"))
        ):
            pass
    """
    async def role_checker(
        current_user: UserInDB = Depends(get_current_user),
    ):
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization membership required"
            )
        
        db = await get_db()
        membership = await db.organization_members.find_one({
            "organization_id": current_user.organization_id,
            "user_id": current_user.id
        })
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization"
            )
        
        role = membership.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return None
    
    return role_checker


class OrganizationContextMiddleware:
    """
    ASGI middleware that injects organization context into request state.
    
    This middleware runs early in the request lifecycle and makes
    organization context available without requiring authentication.
    
    For authenticated routes, use the get_organization_context dependency instead.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Initialize organization context as None
            # Will be populated by get_organization_context dependency if user is authenticated
            if "state" not in scope:
                scope["state"] = {}
            scope["state"]["organization_id"] = None
            scope["state"]["organization"] = None
        
        await self.app(scope, receive, send)


def get_org_id_from_request(request: Request) -> Optional[str]:
    """
    Utility function to get organization_id from request state.
    
    Use this in service functions that receive the request object.
    """
    return getattr(request.state, "organization_id", None)


def get_org_from_request(request: Request) -> Optional[dict]:
    """
    Utility function to get full organization from request state.
    
    Use this in service functions that receive the request object.
    """
    return getattr(request.state, "organization", None)
