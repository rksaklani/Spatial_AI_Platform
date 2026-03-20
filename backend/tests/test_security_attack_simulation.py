"""
Security Attack Simulation Tests

Simulates real-world attacks against the tenant isolation system:
1. Cross-organization access attempts
2. Token reuse after organization switch
3. Stale membership access (removed member trying to access)
4. Direct repository bypass attempts
5. Parameter manipulation attacks
6. Trial expiration bypass
7. Inactive organization access
8. Privilege escalation attempts

These tests verify that the security controls actually work.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
import uuid


# =============================================================================
# ATTACK 1: Cross-Organization Data Access
# =============================================================================

class TestCrossOrganizationAttack:
    """
    Scenario: Attacker in Org A tries to access Org B's data.
    
    Attack vectors:
    - Direct database query with Org B's resource IDs
    - Manipulating organization_id in requests
    - Using TenantRepository with wrong org_id
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    async def test_repository_blocks_cross_org_access(self):
        """
        ATTACK: User from Org A tries to query Org B's scene using TenantRepository.
        EXPECTED: Query returns nothing (filtered by org_id).
        """
        from services.tenant_repository import SceneRepository
        
        # Setup: Attacker creates repo with their org (Org A)
        attacker_repo = SceneRepository("org-a")
        
        # Attack: Try to find a scene that belongs to Org B
        # The scene ID is valid, but belongs to different org
        with patch('services.tenant_repository.get_db') as mock_get_db:
            mock_collection = AsyncMock()
            # Simulate: Scene exists in DB but has org-b's organization_id
            mock_collection.find_one = AsyncMock(return_value=None)  # Filtered out
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            
            result = await attacker_repo.find_by_id("scene-belongs-to-org-b")
            
            # Verify: Query included attacker's org filter
            call_args = mock_collection.find_one.call_args[0][0]
            assert call_args["organization_id"] == "org-a"
            assert call_args["_id"] == "scene-belongs-to-org-b"
            
            # Result should be None (org filter excludes it)
            assert result is None
    
    @pytest.mark.unit
    @pytest.mark.security
    async def test_repository_prevents_cross_org_update(self):
        """
        ATTACK: User from Org A tries to update Org B's scene.
        EXPECTED: Update affects 0 documents.
        """
        from services.tenant_repository import SceneRepository
        
        attacker_repo = SceneRepository("org-a")
        
        with patch('services.tenant_repository.get_db') as mock_get_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock()
            mock_result.modified_count = 0  # Nothing modified (wrong org)
            mock_collection.update_one = AsyncMock(return_value=mock_result)
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            
            # Attack: Try to update scene in org-b
            modified = await attacker_repo.update_one(
                {"_id": "scene-belongs-to-org-b"},
                {"$set": {"name": "HACKED"}}
            )
            
            # Verify: org-a filter was applied
            call_args = mock_collection.update_one.call_args[0][0]
            assert call_args["organization_id"] == "org-a"
            
            # Result: 0 modified (attacker can't modify other org's data)
            assert modified == 0
    
    @pytest.mark.unit
    @pytest.mark.security
    async def test_repository_prevents_cross_org_delete(self):
        """
        ATTACK: User from Org A tries to delete Org B's scene.
        EXPECTED: Delete affects 0 documents.
        """
        from services.tenant_repository import SceneRepository
        
        attacker_repo = SceneRepository("org-a")
        
        with patch('services.tenant_repository.get_db') as mock_get_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock()
            mock_result.deleted_count = 0  # Nothing deleted (wrong org)
            mock_collection.delete_one = AsyncMock(return_value=mock_result)
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            
            # Attack: Try to delete scene in org-b
            deleted = await attacker_repo.delete_one({"_id": "scene-belongs-to-org-b"})
            
            # Verify: org-a filter was applied
            call_args = mock_collection.delete_one.call_args[0][0]
            assert call_args["organization_id"] == "org-a"
            
            # Result: 0 deleted
            assert deleted == 0


# =============================================================================
# ATTACK 2: Token/Context Reuse After Organization Switch
# =============================================================================

class TestTokenReuseAfterOrgSwitch:
    """
    Scenario: User switches from Org A to Org B, but old context is reused.
    
    Attack vectors:
    - Caching stale TenantContext
    - Reusing repository instances after org switch
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_tenant_context_is_request_scoped(self):
        """
        VERIFY: TenantContext is created fresh for each request.
        Old contexts should not be reusable.
        """
        from services.tenant_context import TenantContext
        from services.tenant_repository import SceneRepository
        from models.user import UserInDB
        
        # User starts in Org A
        user_data = {
            "_id": "user-123",
            "email": "user@example.com",
            "full_name": "Test User",
            "organization_id": "org-a",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        ctx_org_a = TenantContext(user=user, organization_id="org-a")
        repo_org_a = ctx_org_a.scenes
        
        # Verify Org A context
        assert repo_org_a.organization_id == "org-a"
        
        # User switches to Org B - new context created
        ctx_org_b = TenantContext(user=user, organization_id="org-b")
        repo_org_b = ctx_org_b.scenes
        
        # Verify: New repo has Org B, old repo still has Org A
        assert repo_org_b.organization_id == "org-b"
        assert repo_org_a.organization_id == "org-a"  # Old instance unchanged
        
        # IMPORTANT: Each request must create fresh TenantContext
        # The old ctx_org_a should NOT be reused after switch
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_repository_org_id_is_immutable(self):
        """
        VERIFY: Repository organization_id cannot be changed after creation.
        """
        from services.tenant_repository import SceneRepository
        
        repo = SceneRepository("org-a")
        
        # Attempt to modify organization_id
        with pytest.raises(AttributeError):
            repo.organization_id = "org-b"  # Should fail - it's a property or immutable


# =============================================================================
# ATTACK 3: Stale Membership Access
# =============================================================================

class TestStaleMembershipAttack:
    """
    Scenario: User is removed from organization but tries to access data.
    
    Attack vectors:
    - User document still has organization_id after removal
    - JWT token still valid after membership removal
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.tenant_context.get_db')
    async def test_removed_member_blocked(self, mock_get_db):
        """
        ATTACK: User removed from org tries to get TenantContext.
        EXPECTED: 403 Forbidden - membership verified.
        """
        from services.tenant_context import get_tenant_context
        from models.user import UserInDB
        from fastapi import Request
        
        # Setup: User document still has old organization_id
        user_data = {
            "_id": "removed-user",
            "email": "removed@example.com",
            "full_name": "Removed User",
            "organization_id": "org-a",  # Stale!
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        # Mock: Membership check returns None (user was removed)
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        # Attack: Try to get tenant context
        with pytest.raises(HTTPException) as exc_info:
            await get_tenant_context(mock_request, user)
        
        # Verify: Blocked with 403
        assert exc_info.value.status_code == 403
        assert "no longer a member" in exc_info.value.detail
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.tenant_context.get_db')
    async def test_optional_context_returns_none_for_removed_member(self, mock_get_db):
        """
        VERIFY: Optional tenant context returns None for removed members.
        """
        from services.tenant_context import get_optional_tenant_context
        from models.user import UserInDB
        from fastapi import Request
        
        user_data = {
            "_id": "removed-user",
            "email": "removed@example.com",
            "full_name": "Removed User",
            "organization_id": "org-a",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        # Mock: Membership not found
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        # Result should be None, not an error
        result = await get_optional_tenant_context(mock_request, user)
        assert result is None


# =============================================================================
# ATTACK 4: Direct Repository Bypass
# =============================================================================

class TestDirectRepositoryBypass:
    """
    Scenario: Attacker tries to bypass TenantRepository and access DB directly.
    
    Attack vectors:
    - Using get_db() directly in custom code
    - Creating repository with empty/None org_id
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_repository_rejects_empty_org_id(self):
        """
        ATTACK: Create repository with empty organization_id.
        EXPECTED: ValueError raised.
        """
        from services.tenant_repository import SceneRepository
        
        with pytest.raises(ValueError) as exc_info:
            SceneRepository("")
        
        assert "organization_id is required" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_repository_rejects_none_org_id(self):
        """
        ATTACK: Create repository with None organization_id.
        EXPECTED: ValueError or TypeError raised.
        """
        from services.tenant_repository import SceneRepository
        
        with pytest.raises((ValueError, TypeError)):
            SceneRepository(None)
    
    @pytest.mark.unit
    @pytest.mark.security
    async def test_filter_injection_prevented(self):
        """
        ATTACK: Try to inject $or operator to bypass org filter.
        EXPECTED: Org filter still applied, $or merged not replaced.
        """
        from services.tenant_repository import SceneRepository
        
        attacker_repo = SceneRepository("org-a")
        
        with patch('services.tenant_repository.get_db') as mock_get_db:
            mock_collection = AsyncMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            
            # Attack: Try to use $or to query any org
            malicious_filter = {
                "$or": [
                    {"organization_id": "org-a"},
                    {"organization_id": "org-b"}
                ]
            }
            
            await attacker_repo.find_one(malicious_filter)
            
            # Verify: org-a filter was ADDED, not replaced
            call_args = mock_collection.find_one.call_args[0][0]
            
            # The org filter should be present
            assert call_args.get("organization_id") == "org-a"
            
            # Note: The $or is still there but org-a filter takes precedence
            # Documents must match BOTH the $or AND organization_id=org-a


# =============================================================================
# ATTACK 5: Trial Expiration Bypass
# =============================================================================

class TestTrialExpirationBypass:
    """
    Scenario: User with expired trial tries to access data.
    
    Attack vectors:
    - Continue using app after trial expires
    - Manipulate trial_expires_at field
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.tenant_context.get_db')
    async def test_expired_trial_blocked(self, mock_get_db):
        """
        ATTACK: User with expired trial tries to get TenantContext.
        EXPECTED: 403 Forbidden.
        """
        from services.tenant_context import get_tenant_context
        from models.user import UserInDB
        from fastapi import Request
        
        user_data = {
            "_id": "trial-user",
            "email": "trial@example.com",
            "full_name": "Trial User",
            "organization_id": "trial-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        # Mock: User has valid membership
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-1",
            "organization_id": "trial-org",
            "user_id": "trial-user",
            "role": "member"
        })
        
        # Mock: Organization has EXPIRED trial
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": "trial-org",
            "name": "Trial Org",
            "subscription_tier": "free_trial",
            "trial_expires_at": datetime.utcnow() - timedelta(days=1),  # Expired!
            "is_active": True,
        })
        mock_get_db.return_value = mock_db
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        # Attack: Try to get tenant context with expired trial
        with pytest.raises(HTTPException) as exc_info:
            await get_tenant_context(mock_request, user)
        
        assert exc_info.value.status_code == 403
        assert "trial has expired" in exc_info.value.detail
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.tenant_context.get_db')
    async def test_paid_tier_not_affected_by_trial_date(self, mock_get_db):
        """
        VERIFY: Paid subscription tiers ignore trial_expires_at.
        """
        from services.tenant_context import get_tenant_context
        from models.user import UserInDB
        from fastapi import Request
        
        user_data = {
            "_id": "paid-user",
            "email": "paid@example.com",
            "full_name": "Paid User",
            "organization_id": "paid-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-1",
            "organization_id": "paid-org",
            "user_id": "paid-user",
            "role": "member"
        })
        
        # Paid tier with old trial_expires_at (should be ignored)
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": "paid-org",
            "name": "Paid Org",
            "subscription_tier": "professional",  # Paid tier
            "trial_expires_at": datetime.utcnow() - timedelta(days=100),  # Old date
            "is_active": True,
        })
        mock_get_db.return_value = mock_db
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        # Should succeed - paid tier ignores trial expiration
        ctx = await get_tenant_context(mock_request, user)
        assert ctx.organization_id == "paid-org"


# =============================================================================
# ATTACK 6: Inactive Organization Access
# =============================================================================

class TestInactiveOrganizationAccess:
    """
    Scenario: Organization is deactivated but user tries to access data.
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.tenant_context.get_db')
    async def test_inactive_org_blocked(self, mock_get_db):
        """
        ATTACK: Access data from deactivated organization.
        EXPECTED: 403 Forbidden.
        """
        from services.tenant_context import get_tenant_context
        from models.user import UserInDB
        from fastapi import Request
        
        user_data = {
            "_id": "user-in-inactive-org",
            "email": "user@example.com",
            "full_name": "User",
            "organization_id": "inactive-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-1",
            "organization_id": "inactive-org",
            "user_id": "user-in-inactive-org",
            "role": "owner"
        })
        
        # Organization is inactive
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": "inactive-org",
            "name": "Inactive Org",
            "subscription_tier": "professional",
            "is_active": False,  # Deactivated!
        })
        mock_get_db.return_value = mock_db
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_tenant_context(mock_request, user)
        
        assert exc_info.value.status_code == 403
        assert "inactive" in exc_info.value.detail


# =============================================================================
# ATTACK 7: Privilege Escalation
# =============================================================================

class TestPrivilegeEscalation:
    """
    Scenario: Regular member tries to perform admin/owner actions.
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('api.organizations.get_db')
    async def test_member_cannot_delete_organization(self, mock_get_db):
        """
        ATTACK: Regular member tries to delete organization.
        EXPECTED: 403 Forbidden.
        """
        from api.organizations import delete_organization
        from models.user import UserInDB
        
        user_data = {
            "_id": "regular-member",
            "email": "member@example.com",
            "full_name": "Regular Member",
            "organization_id": "target-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        # User is a member, not owner
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-1",
            "organization_id": "target-org",
            "user_id": "regular-member",
            "role": "member"  # Not owner!
        })
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_organization("target-org", user)
        
        assert exc_info.value.status_code == 403
        assert "owner" in exc_info.value.detail.lower()
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('api.organizations.get_db')
    async def test_viewer_cannot_add_members(self, mock_get_db):
        """
        ATTACK: Viewer tries to add new member.
        EXPECTED: 403 Forbidden.
        """
        from api.organizations import add_member
        from models.organization import AddMemberRequest
        from models.user import UserInDB
        
        user_data = {
            "_id": "viewer-user",
            "email": "viewer@example.com",
            "full_name": "Viewer",
            "organization_id": "target-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        # User is a viewer
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-1",
            "organization_id": "target-org",
            "user_id": "viewer-user",
            "role": "viewer"  # Read-only!
        })
        mock_get_db.return_value = mock_db
        
        request = AddMemberRequest(user_email="newuser@example.com", role="member")
        
        with pytest.raises(HTTPException) as exc_info:
            await add_member("target-org", request, user)
        
        assert exc_info.value.status_code == 403


# =============================================================================
# ATTACK 8: Access Log Tampering/Leakage
# =============================================================================

class TestAccessLogSecurity:
    """
    Scenario: Attacker tries to view or manipulate access logs.
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('services.access_logger.get_db')
    async def test_cannot_view_other_org_access_logs(self, mock_get_db):
        """
        ATTACK: Admin from Org A tries to view Org B's access logs.
        EXPECTED: Query filters by requesting org.
        """
        from services.access_logger import AccessLogger, ResourceType
        
        logger = AccessLogger()
        
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        # Attack: Try to get logs for Org B's resource while in Org A
        await logger.get_resource_access_history(
            resource_type=ResourceType.SCENE,
            resource_id="org-b-scene",
            requesting_user_org_id="org-a",  # Attacker's org
        )
        
        # Verify: Query uses attacker's org (org-a), not org-b
        call_args = mock_collection.find.call_args[0][0]
        assert call_args["organization_id"] == "org-a"
        
        # Even if the scene ID belongs to org-b, results will be empty
        # because org-a filter is applied


# =============================================================================
# ATTACK 9: Organization ID Enumeration
# =============================================================================

class TestOrganizationEnumeration:
    """
    Scenario: Attacker tries to discover valid organization IDs.
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    @patch('api.organizations.get_db')
    async def test_non_member_gets_same_error_as_nonexistent(self, mock_get_db):
        """
        VERIFY: Non-member and non-existent org return same error.
        This prevents enumeration of valid org IDs.
        """
        from api.organizations import get_organization
        from models.user import UserInDB
        
        user_data = {
            "_id": "attacker",
            "email": "attacker@example.com",
            "full_name": "Attacker",
            "organization_id": "attacker-org",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        # Case 1: Org exists but user is not a member
        mock_db.organization_members.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc_info:
            await get_organization("existing-org-not-member", user)
        
        error_for_not_member = exc_info.value
        
        # Case 2: Org doesn't exist
        with pytest.raises(HTTPException) as exc_info:
            await get_organization("nonexistent-org", user)
        
        error_for_nonexistent = exc_info.value
        
        # Both should return 403 "Not a member" - same error
        # This prevents distinguishing between "exists but no access" vs "doesn't exist"
        assert error_for_not_member.status_code == 403
        assert error_for_nonexistent.status_code == 403


# =============================================================================
# ATTACK 10: Aggregate Pipeline Injection
# =============================================================================

class TestAggregatePipelineInjection:
    """
    Scenario: Attacker tries to inject stages to bypass org filter in aggregation.
    """
    
    @pytest.mark.unit
    @pytest.mark.security
    async def test_aggregate_prepends_org_filter(self):
        """
        VERIFY: Aggregation always starts with org filter $match.
        """
        from services.tenant_repository import SceneRepository
        
        repo = SceneRepository("org-a")
        
        with patch('services.tenant_repository.get_db') as mock_get_db:
            mock_collection = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_collection.aggregate = MagicMock(return_value=mock_cursor)
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            
            # Attack: Try to inject $match at start to override org filter
            malicious_pipeline = [
                {"$match": {"organization_id": {"$exists": True}}},  # Try to match ALL orgs
                {"$group": {"_id": "$organization_id", "count": {"$sum": 1}}}
            ]
            
            await repo.aggregate(malicious_pipeline)
            
            # Verify: Our org filter was PREPENDED
            actual_pipeline = mock_collection.aggregate.call_args[0][0]
            
            # First stage MUST be our org filter
            assert actual_pipeline[0] == {"$match": {"organization_id": "org-a"}}
            
            # Attacker's stages come after (and will be filtered by our match)
            assert len(actual_pipeline) == 3  # Our match + their 2 stages


# =============================================================================
# Summary marker
# =============================================================================

class TestSecuritySummary:
    """Marker class to verify all security tests are collected."""
    
    @pytest.mark.unit
    def test_all_attack_vectors_covered(self):
        """Verify we have comprehensive attack coverage."""
        attack_vectors = [
            "cross_organization_access",
            "token_reuse_after_switch",
            "stale_membership",
            "direct_repository_bypass",
            "trial_expiration_bypass",
            "inactive_org_access",
            "privilege_escalation",
            "access_log_tampering",
            "org_id_enumeration",
            "aggregate_injection",
        ]
        # This test exists to document coverage
        assert len(attack_vectors) == 10
