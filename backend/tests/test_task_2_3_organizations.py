"""
Tests for Task 2.3: Organization Management.

Tests organization models, API endpoints, and middleware.
Requirements: 18.1, 18.2
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid


class TestOrganizationModels:
    """Test organization model definitions."""
    
    @pytest.mark.unit
    def test_subscription_tier_enum(self):
        """SubscriptionTier enum should have all tiers."""
        from models.organization import SubscriptionTier
        
        assert SubscriptionTier.FREE_TRIAL == "free_trial"
        assert SubscriptionTier.STARTER == "starter"
        assert SubscriptionTier.PROFESSIONAL == "professional"
        assert SubscriptionTier.ENTERPRISE == "enterprise"
    
    @pytest.mark.unit
    def test_organization_base_importable(self):
        """OrganizationBase model should be importable."""
        from models.organization import OrganizationBase
        assert OrganizationBase is not None
    
    @pytest.mark.unit
    def test_organization_create_importable(self):
        """OrganizationCreate model should be importable."""
        from models.organization import OrganizationCreate
        assert OrganizationCreate is not None
    
    @pytest.mark.unit
    def test_organization_update_importable(self):
        """OrganizationUpdate model should be importable."""
        from models.organization import OrganizationUpdate
        assert OrganizationUpdate is not None
    
    @pytest.mark.unit
    def test_organization_in_db_importable(self):
        """OrganizationInDB model should be importable."""
        from models.organization import OrganizationInDB
        assert OrganizationInDB is not None
    
    @pytest.mark.unit
    def test_organization_response_importable(self):
        """OrganizationResponse model should be importable."""
        from models.organization import OrganizationResponse
        assert OrganizationResponse is not None
    
    @pytest.mark.unit
    def test_organization_member_importable(self):
        """OrganizationMember model should be importable."""
        from models.organization import OrganizationMember
        assert OrganizationMember is not None
    
    @pytest.mark.unit
    def test_organization_create_validation(self):
        """OrganizationCreate should validate name."""
        from models.organization import OrganizationCreate
        from pydantic import ValidationError
        
        # Valid organization
        org = OrganizationCreate(name="Test Org", description="A test organization")
        assert org.name == "Test Org"
        assert org.description == "A test organization"
        
        # Invalid - name too short
        with pytest.raises(ValidationError):
            OrganizationCreate(name="")
    
    @pytest.mark.unit
    def test_organization_in_db_structure(self):
        """OrganizationInDB should have all required fields."""
        from models.organization import OrganizationInDB, SubscriptionTier
        
        now = datetime.utcnow()
        org = OrganizationInDB(
            _id="test-org-id",
            name="Test Org",
            owner_id="test-user-id",
            subscription_tier=SubscriptionTier.FREE_TRIAL,
            max_seats=1,
            max_scenes=3,
            max_storage_gb=5,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        
        assert org.id == "test-org-id"
        assert org.name == "Test Org"
        assert org.owner_id == "test-user-id"
        assert org.subscription_tier == SubscriptionTier.FREE_TRIAL.value
        assert org.max_seats == 1


class TestOrganizationRouter:
    """Test organization API router."""
    
    @pytest.mark.unit
    def test_org_router_importable(self):
        """Organization router should be importable."""
        from api.organizations import router
        assert router is not None
    
    @pytest.mark.unit
    def test_create_org_endpoint_exists(self):
        """Create organization endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations" in routes  # POST /organizations
    
    @pytest.mark.unit
    def test_list_orgs_endpoint_exists(self):
        """List organizations endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations" in routes  # GET /organizations
    
    @pytest.mark.unit
    def test_get_org_endpoint_exists(self):
        """Get organization endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations/{organization_id}" in routes
    
    @pytest.mark.unit
    def test_members_endpoint_exists(self):
        """Members endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations/{organization_id}/members" in routes
    
    @pytest.mark.unit
    def test_current_org_endpoint_exists(self):
        """Current organization endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations/me/current" in routes
    
    @pytest.mark.unit
    def test_switch_org_endpoint_exists(self):
        """Switch organization endpoint should exist."""
        from api.organizations import router
        routes = [r.path for r in router.routes]
        assert "/organizations/me/switch/{organization_id}" in routes


class TestOrganizationMiddleware:
    """Test organization context middleware."""
    
    @pytest.mark.unit
    def test_middleware_importable(self):
        """OrganizationContextMiddleware should be importable."""
        from middleware.organization import OrganizationContextMiddleware
        assert OrganizationContextMiddleware is not None
    
    @pytest.mark.unit
    def test_get_organization_context_importable(self):
        """get_organization_context should be importable."""
        from middleware.organization import get_organization_context
        assert callable(get_organization_context)
    
    @pytest.mark.unit
    def test_require_organization_importable(self):
        """require_organization should be importable."""
        from middleware.organization import require_organization
        assert callable(require_organization)
    
    @pytest.mark.unit
    def test_get_user_org_role_importable(self):
        """get_user_org_role should be importable."""
        from middleware.organization import get_user_org_role
        assert callable(get_user_org_role)
    
    @pytest.mark.unit
    def test_require_org_role_importable(self):
        """require_org_role should be importable."""
        from middleware.organization import require_org_role
        assert callable(require_org_role)
    
    @pytest.mark.unit
    def test_get_org_id_from_request_importable(self):
        """get_org_id_from_request should be importable."""
        from middleware.organization import get_org_id_from_request
        assert callable(get_org_id_from_request)


class TestOrganizationAPI:
    """Test organization API functionality with mocks."""
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_create_organization(self, mock_get_db, sample_user_in_db):
        """Should create organization successfully."""
        from api.organizations import create_organization
        from models.organization import OrganizationCreate
        from models.user import UserInDB
        
        # Setup mock
        mock_db = AsyncMock()
        mock_db.organizations.find_one = AsyncMock(return_value=None)
        mock_db.organizations.insert_one = AsyncMock()
        mock_db.organization_members.insert_one = AsyncMock()
        mock_db.users.update_one = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Create user
        user = UserInDB(**sample_user_in_db)
        
        # Create organization
        org_data = OrganizationCreate(name="Test Organization")
        result = await create_organization(org_data, user)
        
        assert result.name == "Test Organization"
        assert result.owner_id == user.id
        assert result.subscription_tier == "free_trial"
        assert result.max_seats == 1
        assert result.member_count == 1
        
        # Verify database calls
        mock_db.organizations.insert_one.assert_called_once()
        mock_db.organization_members.insert_one.assert_called_once()
        mock_db.users.update_one.assert_called_once()
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_create_organization_already_owns(self, mock_get_db, sample_user_in_db):
        """Should reject if user already owns an organization."""
        from api.organizations import create_organization
        from models.organization import OrganizationCreate
        from models.user import UserInDB
        from fastapi import HTTPException
        
        # Setup mock - user already has org
        mock_db = AsyncMock()
        mock_db.organizations.find_one = AsyncMock(return_value={"_id": "existing-org"})
        mock_get_db.return_value = mock_db
        
        user = UserInDB(**sample_user_in_db)
        org_data = OrganizationCreate(name="Test Organization")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_organization(org_data, user)
        
        assert exc_info.value.status_code == 400
        assert "already owns" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_get_organization_as_member(self, mock_get_db, sample_user_in_db):
        """Should get organization if user is a member."""
        from api.organizations import get_organization
        from models.user import UserInDB
        from datetime import datetime
        
        org_id = "test-org-id"
        now = datetime.utcnow()
        
        # Setup mock
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-id",
            "organization_id": org_id,
            "user_id": sample_user_in_db["_id"],
            "role": "member"
        })
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": org_id,
            "name": "Test Org",
            "description": None,
            "owner_id": "owner-id",
            "subscription_tier": "free_trial",
            "max_seats": 1,
            "max_scenes": 3,
            "max_storage_gb": 5,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        })
        mock_db.organization_members.count_documents = AsyncMock(return_value=2)
        mock_get_db.return_value = mock_db
        
        user = UserInDB(**sample_user_in_db)
        result = await get_organization(org_id, user)
        
        assert result.id == org_id
        assert result.name == "Test Org"
        assert result.member_count == 2
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_get_organization_not_member(self, mock_get_db, sample_user_in_db):
        """Should reject if user is not a member."""
        from api.organizations import get_organization
        from models.user import UserInDB
        from fastapi import HTTPException
        
        # Setup mock - not a member
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        user = UserInDB(**sample_user_in_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_organization("org-id", user)
        
        assert exc_info.value.status_code == 403
        assert "Not a member" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_add_member_success(self, mock_get_db, sample_user_in_db):
        """Should add member successfully."""
        from api.organizations import add_member
        from models.organization import AddMemberRequest
        from models.user import UserInDB
        from datetime import datetime
        
        org_id = "test-org-id"
        now = datetime.utcnow()
        
        # Current user is admin
        current_user = UserInDB(**sample_user_in_db)
        
        # New user to add
        new_user = {
            "_id": "new-user-id",
            "email": "new@example.com",
            "full_name": "New User"
        }
        
        # Setup mock
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(side_effect=[
            # First call - current user membership
            {"_id": "member-id", "organization_id": org_id, "user_id": current_user.id, "role": "admin"},
            # Second call - check if new user is already member
            None
        ])
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": org_id,
            "max_seats": 10
        })
        mock_db.organization_members.count_documents = AsyncMock(return_value=2)
        mock_db.users.find_one = AsyncMock(return_value=new_user)
        mock_db.organization_members.insert_one = AsyncMock()
        mock_db.users.update_one = AsyncMock()
        mock_get_db.return_value = mock_db
        
        request = AddMemberRequest(user_email="new@example.com", role="member")
        result = await add_member(org_id, request, current_user)
        
        assert result["email"] == "new@example.com"
        assert result["role"] == "member"
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_add_member_seat_limit(self, mock_get_db, sample_user_in_db):
        """Should reject if seat limit reached."""
        from api.organizations import add_member
        from models.organization import AddMemberRequest
        from models.user import UserInDB
        from fastapi import HTTPException
        
        org_id = "test-org-id"
        current_user = UserInDB(**sample_user_in_db)
        
        # Setup mock - at seat limit
        mock_db = AsyncMock()
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-id", "organization_id": org_id, "user_id": current_user.id, "role": "owner"
        })
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": org_id,
            "max_seats": 1  # Only 1 seat
        })
        mock_db.organization_members.count_documents = AsyncMock(return_value=1)  # Already full
        mock_get_db.return_value = mock_db
        
        request = AddMemberRequest(user_email="new@example.com", role="member")
        
        with pytest.raises(HTTPException) as exc_info:
            await add_member(org_id, request, current_user)
        
        assert exc_info.value.status_code == 400
        assert "maximum seats" in exc_info.value.detail


class TestDatabaseIndexes:
    """Test database index configurations for organizations."""
    
    @pytest.mark.unit
    def test_database_has_org_members_collection(self):
        """organization_members should be in collections list."""
        from utils.database import init_database_sync
        # Check the function exists and the collection is defined
        import inspect
        source = inspect.getsource(init_database_sync)
        assert "'organization_members'" in source
    
    @pytest.mark.unit
    def test_database_org_indexes_defined(self):
        """Organization indexes should be defined."""
        from utils.database import init_database_sync
        import inspect
        source = inspect.getsource(init_database_sync)
        
        # Check organization indexes
        assert "db.organizations.create_index" in source
        assert "db.organization_members.create_index" in source
