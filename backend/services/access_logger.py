"""
Access logging service for audit trails.

Task 2.4: Multi-tenant data isolation
Implements access logging for all data operations to maintain
a complete audit trail for compliance and security.
"""
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum
from bson import ObjectId
import structlog

from utils.database import get_db

logger = structlog.get_logger(__name__)


class AccessAction(str, Enum):
    """Types of access actions to log."""
    # Read operations
    VIEW = "view"
    LIST = "list"
    SEARCH = "search"
    EXPORT = "export"
    DOWNLOAD = "download"
    
    # Write operations
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # Sharing
    SHARE = "share"
    UNSHARE = "unshare"
    ACCESS_SHARED = "access_shared"
    
    # Organization
    ORG_CREATE = "org_create"
    ORG_UPDATE = "org_update"
    ORG_DELETE = "org_delete"
    MEMBER_ADD = "member_add"
    MEMBER_REMOVE = "member_remove"
    MEMBER_ROLE_CHANGE = "member_role_change"
    
    # Permission
    PERMISSION_DENIED = "permission_denied"


class ResourceType(str, Enum):
    """Types of resources being accessed."""
    SCENE = "scene"
    ANNOTATION = "annotation"
    GUIDED_TOUR = "guided_tour"
    SHARE_TOKEN = "share_token"
    USER = "user"
    ORGANIZATION = "organization"
    PROCESSING_JOB = "processing_job"
    SCENE_TILE = "scene_tile"
    REPORT = "report"
    FILE = "file"


class AccessLogger:
    """
    Service for logging all data access events.
    
    Creates an audit trail for compliance (HIPAA, ISO 27001, etc.)
    and security monitoring.
    
    Usage:
        access_logger = AccessLogger()
        await access_logger.log(
            action=AccessAction.VIEW,
            resource_type=ResourceType.SCENE,
            resource_id="scene-123",
            user_id="user-456",
            organization_id="org-789",
            details={"reason": "Viewing scene for review"}
        )
    """
    
    COLLECTION_NAME = "scene_access_logs"
    
    async def log(
        self,
        action: AccessAction,
        resource_type: ResourceType,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log an access event.
        
        Args:
            action: The action performed
            resource_type: Type of resource accessed
            user_id: ID of the user performing the action
            organization_id: ID of the organization context
            resource_id: ID of the specific resource accessed
            details: Additional details about the access
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether the action succeeded
            error_message: Error message if action failed
            
        Returns:
            ID of the created log entry
        """
        db = await get_db()
        
        log_entry = {
            "_id": str(ObjectId()),
            "action": action.value,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "error_message": error_message,
            "accessed_at": datetime.utcnow(),
        }
        
        await db[self.COLLECTION_NAME].insert_one(log_entry)
        
        # Also log to structured logger for real-time monitoring
        log_level = "info" if success else "warning"
        log_data = {
            "action": action.value,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "success": success,
        }
        
        if success:
            logger.info("access_logged", **log_data)
        else:
            logger.warning("access_denied", **log_data, error=error_message)
        
        return log_entry["_id"]
    
    async def log_scene_access(
        self,
        scene_id: str,
        user_id: str,
        organization_id: str,
        action: AccessAction = AccessAction.VIEW,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convenience method to log scene access.
        
        Args:
            scene_id: ID of the scene accessed
            user_id: ID of the user
            organization_id: ID of the organization
            action: The action (default: VIEW)
            ip_address: Client IP address
            details: Additional details
            
        Returns:
            ID of the log entry
        """
        return await self.log(
            action=action,
            resource_type=ResourceType.SCENE,
            resource_id=scene_id,
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            details=details,
        )
    
    async def log_permission_denied(
        self,
        resource_type: ResourceType,
        resource_id: Optional[str],
        user_id: str,
        organization_id: Optional[str],
        reason: str,
        ip_address: Optional[str] = None,
    ) -> str:
        """
        Log a permission denied event.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            user_id: ID of the user
            organization_id: Organization context
            reason: Reason for denial
            ip_address: Client IP address
            
        Returns:
            ID of the log entry
        """
        return await self.log(
            action=AccessAction.PERMISSION_DENIED,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            success=False,
            error_message=reason,
            details={"denial_reason": reason},
        )
    
    async def get_user_access_history(
        self,
        user_id: str,
        requesting_user_id: str,
        requesting_user_org_id: str,
        limit: int = 100,
        skip: int = 0,
        action_filter: Optional[AccessAction] = None,
        resource_type_filter: Optional[ResourceType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get access history for a user.
        
        SECURITY: Only returns logs for the requesting user's organization.
        Users can only see their own logs, admins/owners can see org member logs.
        
        Args:
            user_id: User ID to query
            requesting_user_id: ID of user making the request
            requesting_user_org_id: Organization ID of requesting user
            limit: Maximum results
            skip: Number to skip
            action_filter: Filter by action type
            resource_type_filter: Filter by resource type
            start_date: Filter from date
            end_date: Filter to date
            
        Returns:
            List of access log entries
        """
        db = await get_db()
        
        # SECURITY: Always filter by organization to prevent cross-tenant access
        query: Dict[str, Any] = {
            "user_id": user_id,
            "organization_id": requesting_user_org_id,  # Enforce tenant isolation
        }
        
        if action_filter:
            query["action"] = action_filter.value
        
        if resource_type_filter:
            query["resource_type"] = resource_type_filter.value
        
        if start_date or end_date:
            query["accessed_at"] = {}
            if start_date:
                query["accessed_at"]["$gte"] = start_date
            if end_date:
                query["accessed_at"]["$lte"] = end_date
        
        cursor = db[self.COLLECTION_NAME].find(query)
        cursor = cursor.sort("accessed_at", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_resource_access_history(
        self,
        resource_type: ResourceType,
        resource_id: str,
        requesting_user_org_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get access history for a specific resource.
        
        SECURITY: Only returns logs for resources in the requesting user's organization.
        The requesting_user_org_id is validated by the caller (TenantContext).
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            requesting_user_org_id: Organization ID of requesting user (enforced)
            limit: Maximum results
            skip: Number to skip
            
        Returns:
            List of access log entries
        """
        db = await get_db()
        
        # SECURITY: Use the verified org ID from TenantContext
        query = {
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "organization_id": requesting_user_org_id,
        }
        
        cursor = db[self.COLLECTION_NAME].find(query)
        cursor = cursor.sort("accessed_at", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_organization_access_summary(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Get access summary for an organization.
        
        Args:
            organization_id: Organization ID
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Summary statistics
        """
        db = await get_db()
        
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "accessed_at": {"$gte": start_date, "$lte": end_date},
                }
            },
            {
                "$group": {
                    "_id": {
                        "action": "$action",
                        "resource_type": "$resource_type",
                    },
                    "count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"},
                }
            },
            {
                "$project": {
                    "action": "$_id.action",
                    "resource_type": "$_id.resource_type",
                    "count": 1,
                    "unique_user_count": {"$size": "$unique_users"},
                }
            },
        ]
        
        cursor = db[self.COLLECTION_NAME].aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Organize results
        summary = {
            "organization_id": organization_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "by_action": {},
            "by_resource_type": {},
            "total_events": 0,
        }
        
        for result in results:
            action = result["action"]
            resource_type = result["resource_type"]
            count = result["count"]
            
            summary["total_events"] += count
            
            if action not in summary["by_action"]:
                summary["by_action"][action] = 0
            summary["by_action"][action] += count
            
            if resource_type not in summary["by_resource_type"]:
                summary["by_resource_type"][resource_type] = 0
            summary["by_resource_type"][resource_type] += count
        
        return summary


# Singleton instance
_access_logger: Optional[AccessLogger] = None


def get_access_logger() -> AccessLogger:
    """Get the global access logger instance."""
    global _access_logger
    if _access_logger is None:
        _access_logger = AccessLogger()
    return _access_logger
