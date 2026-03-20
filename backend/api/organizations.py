"""
Organization management API endpoints.

Task 2.3: Organization Management
- Organization CRUD operations
- User-to-organization assignment
- Member management
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
import structlog

from models.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMember,
    AddMemberRequest,
    UpdateMemberRoleRequest,
    SubscriptionTier,
)
from models.user import UserInDB, UserResponse
from api.deps import get_current_user
from utils.database import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["organizations"])


# ============================================================================
# Organization CRUD
# ============================================================================

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Create a new organization.
    
    The creating user becomes the owner and is automatically added as a member.
    New organizations start with a 15-day free trial.
    """
    db = await get_db()
    
    # Check if user already owns an organization
    existing_org = await db.organizations.find_one({"owner_id": current_user.id})
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already owns an organization"
        )
    
    # Create organization document
    org_id = str(ObjectId())
    now = datetime.utcnow()
    trial_expires = now + timedelta(days=15)
    
    org_doc = {
        "_id": org_id,
        "name": org_data.name,
        "description": org_data.description,
        "owner_id": current_user.id,
        "subscription_tier": SubscriptionTier.FREE_TRIAL.value,
        "max_seats": 1,
        "max_scenes": 3,
        "max_storage_gb": 5,
        "trial_expires_at": trial_expires,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.organizations.insert_one(org_doc)
    
    # Add owner as a member with 'owner' role
    member_doc = {
        "_id": str(ObjectId()),
        "organization_id": org_id,
        "user_id": current_user.id,
        "role": "owner",
        "joined_at": now,
    }
    await db.organization_members.insert_one(member_doc)
    
    # Update user's organization_id
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"organization_id": org_id, "updated_at": now}}
    )
    
    logger.info(
        "organization_created",
        organization_id=org_id,
        owner_id=current_user.id,
        name=org_data.name
    )
    
    # Return response with member count
    org_doc["member_count"] = 1
    return OrganizationResponse(**org_doc)


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: UserInDB = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List organizations the current user is a member of.
    """
    db = await get_db()
    
    # Get organizations where user is a member
    memberships = await db.organization_members.find(
        {"user_id": current_user.id}
    ).to_list(length=100)
    
    org_ids = [m["organization_id"] for m in memberships]
    
    if not org_ids:
        return []
    
    # Fetch organizations
    cursor = db.organizations.find({"_id": {"$in": org_ids}}).skip(skip).limit(limit)
    organizations = await cursor.to_list(length=limit)
    
    # Get member counts for each organization
    results = []
    for org in organizations:
        member_count = await db.organization_members.count_documents(
            {"organization_id": org["_id"]}
        )
        org["member_count"] = member_count
        results.append(OrganizationResponse(**org))
    
    return results


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get organization details by ID.
    
    User must be a member of the organization.
    """
    db = await get_db()
    
    # Check membership
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    # Fetch organization
    org = await db.organizations.find_one({"_id": organization_id})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get member count
    member_count = await db.organization_members.count_documents(
        {"organization_id": organization_id}
    )
    org["member_count"] = member_count
    
    return OrganizationResponse(**org)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    org_update: OrganizationUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update organization details.
    
    Only owners and admins can update organization.
    """
    db = await get_db()
    
    # Check membership and role
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    if membership["role"] not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can update organization"
        )
    
    # Build update document
    update_data = {}
    if org_update.name is not None:
        update_data["name"] = org_update.name
    if org_update.description is not None:
        update_data["description"] = org_update.description
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update organization
    result = await db.organizations.update_one(
        {"_id": organization_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Fetch and return updated organization
    org = await db.organizations.find_one({"_id": organization_id})
    member_count = await db.organization_members.count_documents(
        {"organization_id": organization_id}
    )
    org["member_count"] = member_count
    
    logger.info(
        "organization_updated",
        organization_id=organization_id,
        updated_by=current_user.id
    )
    
    return OrganizationResponse(**org)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Delete an organization.
    
    Only the owner can delete an organization.
    This is a soft delete - sets is_active to False.
    """
    db = await get_db()
    
    # SECURITY: First check membership to avoid leaking org existence
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        # Generic error to prevent organization ID probing
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if membership["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete an organization"
        )
    
    # Now safe to fetch org details
    org = await db.organizations.find_one({"_id": organization_id})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Soft delete
    await db.organizations.update_one(
        {"_id": organization_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    logger.info(
        "organization_deleted",
        organization_id=organization_id,
        deleted_by=current_user.id
    )
    
    return None


# ============================================================================
# Member Management
# ============================================================================

@router.get("/{organization_id}/members", response_model=List[dict])
async def list_members(
    organization_id: str,
    current_user: UserInDB = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List organization members.
    
    User must be a member of the organization.
    """
    db = await get_db()
    
    # Check membership
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    # Fetch members
    cursor = db.organization_members.find(
        {"organization_id": organization_id}
    ).skip(skip).limit(limit)
    members = await cursor.to_list(length=limit)
    
    # Enrich with user data
    results = []
    for member in members:
        user = await db.users.find_one({"_id": member["user_id"]})
        if user:
            results.append({
                "id": member["_id"],
                "user_id": member["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": member["role"],
                "joined_at": member["joined_at"],
            })
    
    return results


@router.post("/{organization_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    organization_id: str,
    request: AddMemberRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Add a member to an organization by email.
    
    Only owners and admins can add members.
    The user must already exist in the system.
    """
    db = await get_db()
    
    # Check if current user is owner or admin
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership or membership["role"] not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can add members"
        )
    
    # Check seat limits
    org = await db.organizations.find_one({"_id": organization_id})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    current_member_count = await db.organization_members.count_documents(
        {"organization_id": organization_id}
    )
    
    if current_member_count >= org["max_seats"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached maximum seats ({org['max_seats']})"
        )
    
    # Find user by email
    # SECURITY: Use generic error to prevent email enumeration
    user = await db.users.find_one({"email": request.user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to add member. The user may not exist or may already be a member."
        )
    
    # Check if already a member
    existing = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": user["_id"]
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )
    
    # Validate role
    valid_roles = ["admin", "member", "viewer"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    # Add member
    now = datetime.utcnow()
    member_doc = {
        "_id": str(ObjectId()),
        "organization_id": organization_id,
        "user_id": user["_id"],
        "role": request.role,
        "joined_at": now,
    }
    await db.organization_members.insert_one(member_doc)
    
    # Update user's organization_id if they don't have one
    if not user.get("organization_id"):
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"organization_id": organization_id, "updated_at": now}}
        )
    
    logger.info(
        "member_added",
        organization_id=organization_id,
        user_id=user["_id"],
        role=request.role,
        added_by=current_user.id
    )
    
    return {
        "id": member_doc["_id"],
        "user_id": user["_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": request.role,
        "joined_at": now,
    }


@router.patch("/{organization_id}/members/{user_id}")
async def update_member_role(
    organization_id: str,
    user_id: str,
    request: UpdateMemberRoleRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update a member's role.
    
    Only owners can change roles. Cannot change owner's role.
    """
    db = await get_db()
    
    # Check if current user is owner
    current_membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not current_membership or current_membership["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can change member roles"
        )
    
    # Find target member
    target_membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": user_id
    })
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot change owner's role
    if target_membership["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner's role"
        )
    
    # Validate role
    valid_roles = ["admin", "member", "viewer"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    # Update role
    await db.organization_members.update_one(
        {"_id": target_membership["_id"]},
        {"$set": {"role": request.role}}
    )
    
    logger.info(
        "member_role_updated",
        organization_id=organization_id,
        user_id=user_id,
        new_role=request.role,
        updated_by=current_user.id
    )
    
    return {"message": "Role updated successfully", "role": request.role}


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    organization_id: str,
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Remove a member from an organization.
    
    Owners and admins can remove members (except owners).
    Users can remove themselves.
    """
    db = await get_db()
    
    # Check current user's membership
    current_membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not current_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    # Find target member
    target_membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": user_id
    })
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot remove owner
    if target_membership["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner"
        )
    
    # Check permissions: owner/admin can remove anyone, users can remove themselves
    is_self = user_id == current_user.id
    is_privileged = current_membership["role"] in ["owner", "admin"]
    
    if not is_self and not is_privileged:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can remove other members"
        )
    
    # Remove member
    await db.organization_members.delete_one({"_id": target_membership["_id"]})
    
    # Clear user's organization_id if this was their only org
    other_memberships = await db.organization_members.count_documents(
        {"user_id": user_id}
    )
    
    if other_memberships == 0:
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"organization_id": None, "updated_at": datetime.utcnow()}}
        )
    
    logger.info(
        "member_removed",
        organization_id=organization_id,
        user_id=user_id,
        removed_by=current_user.id
    )
    
    return None


# ============================================================================
# Current User's Organization Context
# ============================================================================

@router.get("/me/current", response_model=Optional[OrganizationResponse])
async def get_current_organization(
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get the current user's active organization.
    
    Returns the organization set in the user's organization_id field.
    """
    db = await get_db()
    
    if not current_user.organization_id:
        return None
    
    org = await db.organizations.find_one({"_id": current_user.organization_id})
    if not org:
        return None
    
    member_count = await db.organization_members.count_documents(
        {"organization_id": org["_id"]}
    )
    org["member_count"] = member_count
    
    return OrganizationResponse(**org)


@router.post("/me/switch/{organization_id}", response_model=OrganizationResponse)
async def switch_organization(
    organization_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Switch the current user's active organization.
    
    User must be a member of the target organization.
    """
    db = await get_db()
    
    # Check membership
    membership = await db.organization_members.find_one({
        "organization_id": organization_id,
        "user_id": current_user.id
    })
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    # Update user's organization_id
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"organization_id": organization_id, "updated_at": datetime.utcnow()}}
    )
    
    # Fetch organization
    org = await db.organizations.find_one({"_id": organization_id})
    member_count = await db.organization_members.count_documents(
        {"organization_id": organization_id}
    )
    org["member_count"] = member_count
    
    logger.info(
        "organization_switched",
        user_id=current_user.id,
        organization_id=organization_id
    )
    
    return OrganizationResponse(**org)
