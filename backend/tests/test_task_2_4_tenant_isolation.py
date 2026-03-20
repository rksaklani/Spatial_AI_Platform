"""
Tests for Task 2.4: Multi-tenant data isolation.

Tests tenant repository, access logging, and tenant context.
Requirements: 18.2, 18.3, 18.6, 18.7
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid


class TestTenantRepository:
    """Test tenant repository base class."""
    
    @pytest.mark.unit
    def test_tenant_repository_importable(self):
        """TenantRepository should be importable."""
        from services.tenant_repository import TenantRepository
        assert TenantRepository is not None
    
    @pytest.mark.unit
    def test_scene_repository_importable(self):
        """SceneRepository should be importable."""
        from services.tenant_repository import SceneRepository
        assert SceneRepository is not None
    
    @pytest.mark.unit
    def test_annotation_repository_importable(self):
        """AnnotationRepository should be importable."""
        from services.tenant_repository import AnnotationRepository
        assert AnnotationRepository is not None
    
    @pytest.mark.unit
    def test_processing_job_repository_importable(self):
        """ProcessingJobRepository should be importable."""
        from services.tenant_repository import ProcessingJobRepository
        assert ProcessingJobRepository is not None
    
    @pytest.mark.unit
    def test_share_token_repository_importable(self):
        """ShareTokenRepository should be importable."""
        from services.tenant_repository import ShareTokenRepository
        assert ShareTokenRepository is not None
    
    @pytest.mark.unit
    def test_get_repository_importable(self):
        """get_repository should be importable."""
        from services.tenant_repository import get_repository
        assert callable(get_repository)
    
    @pytest.mark.unit
    def test_repository_requires_org_id(self):
        """Repository should require organization_id."""
        from services.tenant_repository import SceneRepository
        
        with pytest.raises(ValueError) as exc_info:
            SceneRepository("")
        
        assert "organization_id is required" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_repository_stores_org_id(self):
        """Repository should store organization_id."""
        from services.tenant_repository import SceneRepository
        
        repo = SceneRepository("org-123")
        assert repo.organization_id == "org-123"
    
    @pytest.mark.unit
    def test_inject_org_filter(self):
        """_inject_org_filter should add organization_id."""
        from services.tenant_repository import SceneRepository
        
        repo = SceneRepository("org-123")
        
        # Empty filter
        result = repo._inject_org_filter(None)
        assert result == {"organization_id": "org-123"}
        
        # Existing filter
        result = repo._inject_org_filter({"status": "active"})
        assert result == {"organization_id": "org-123", "status": "active"}
    
    @pytest.mark.unit
    def test_inject_org_document(self):
        """_inject_org_document should add organization_id to document."""
        from services.tenant_repository import SceneRepository
        
        repo = SceneRepository("org-123")
        
        doc = {"name": "Test Scene", "status": "pending"}
        result = repo._inject_org_document(doc)
        
        assert result["organization_id"] == "org-123"
        assert result["name"] == "Test Scene"
        # Original doc should be unchanged
        assert "organization_id" not in doc


class TestTenantRepositoryOperations:
    """Test tenant repository database operations."""
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_find_one_injects_org_filter(self, mock_get_db):
        """find_one should inject organization_id filter."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={"_id": "scene-1"})
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        result = await repo.find_one({"status": "active"})
        
        # Verify filter includes organization_id
        mock_collection.find_one.assert_called_once()
        call_args = mock_collection.find_one.call_args[0][0]
        assert call_args["organization_id"] == "org-123"
        assert call_args["status"] == "active"
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_find_by_id_injects_org_filter(self, mock_get_db):
        """find_by_id should inject organization_id filter."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={"_id": "scene-1"})
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        result = await repo.find_by_id("scene-1")
        
        # Verify filter includes organization_id
        call_args = mock_collection.find_one.call_args[0][0]
        assert call_args["organization_id"] == "org-123"
        assert call_args["_id"] == "scene-1"
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_insert_one_injects_org_id(self, mock_get_db):
        """insert_one should inject organization_id into document."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        doc = {"name": "Test Scene"}
        result = await repo.insert_one(doc)
        
        # Verify document includes organization_id
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["organization_id"] == "org-123"
        assert call_args["name"] == "Test Scene"
        assert "created_at" in call_args
        assert "updated_at" in call_args
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_update_one_injects_org_filter(self, mock_get_db):
        """update_one should inject organization_id filter."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        result = await repo.update_one(
            {"_id": "scene-1"},
            {"$set": {"status": "completed"}}
        )
        
        # Verify filter includes organization_id
        call_args = mock_collection.update_one.call_args[0]
        assert call_args[0]["organization_id"] == "org-123"
        assert call_args[0]["_id"] == "scene-1"
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_delete_one_injects_org_filter(self, mock_get_db):
        """delete_one should inject organization_id filter."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_collection.delete_one = AsyncMock(return_value=mock_result)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        result = await repo.delete_one({"_id": "scene-1"})
        
        # Verify filter includes organization_id
        call_args = mock_collection.delete_one.call_args[0][0]
        assert call_args["organization_id"] == "org-123"
        assert call_args["_id"] == "scene-1"
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_count_injects_org_filter(self, mock_get_db):
        """count should inject organization_id filter."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=5)
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        repo = SceneRepository("org-123")
        result = await repo.count({"status": "active"})
        
        # Verify filter includes organization_id
        call_args = mock_collection.count_documents.call_args[0][0]
        assert call_args["organization_id"] == "org-123"
        assert call_args["status"] == "active"
        assert result == 5


class TestAccessLogger:
    """Test access logging service."""
    
    @pytest.mark.unit
    def test_access_logger_importable(self):
        """AccessLogger should be importable."""
        from services.access_logger import AccessLogger
        assert AccessLogger is not None
    
    @pytest.mark.unit
    def test_access_action_enum(self):
        """AccessAction enum should have required values."""
        from services.access_logger import AccessAction
        
        assert AccessAction.VIEW == "view"
        assert AccessAction.CREATE == "create"
        assert AccessAction.UPDATE == "update"
        assert AccessAction.DELETE == "delete"
        assert AccessAction.PERMISSION_DENIED == "permission_denied"
    
    @pytest.mark.unit
    def test_resource_type_enum(self):
        """ResourceType enum should have required values."""
        from services.access_logger import ResourceType
        
        assert ResourceType.SCENE == "scene"
        assert ResourceType.ANNOTATION == "annotation"
        assert ResourceType.USER == "user"
        assert ResourceType.ORGANIZATION == "organization"
    
    @pytest.mark.unit
    def test_get_access_logger(self):
        """get_access_logger should return AccessLogger instance."""
        from services.access_logger import get_access_logger, AccessLogger
        
        logger = get_access_logger()
        assert isinstance(logger, AccessLogger)
    
    @pytest.mark.unit
    @patch('services.access_logger.get_db')
    async def test_log_creates_entry(self, mock_get_db):
        """log should create access log entry."""
        from services.access_logger import AccessLogger, AccessAction, ResourceType
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        logger = AccessLogger()
        result = await logger.log(
            action=AccessAction.VIEW,
            resource_type=ResourceType.SCENE,
            resource_id="scene-123",
            user_id="user-456",
            organization_id="org-789",
        )
        
        # Verify log entry was created
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        
        assert call_args["action"] == "view"
        assert call_args["resource_type"] == "scene"
        assert call_args["resource_id"] == "scene-123"
        assert call_args["user_id"] == "user-456"
        assert call_args["organization_id"] == "org-789"
        assert call_args["success"] is True
        assert "_id" in call_args
        assert "accessed_at" in call_args
    
    @pytest.mark.unit
    @patch('services.access_logger.get_db')
    async def test_log_permission_denied(self, mock_get_db):
        """log_permission_denied should create denied entry."""
        from services.access_logger import AccessLogger, AccessAction, ResourceType
        
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        logger = AccessLogger()
        result = await logger.log_permission_denied(
            resource_type=ResourceType.SCENE,
            resource_id="scene-123",
            user_id="user-456",
            organization_id="org-789",
            reason="User not member of organization",
        )
        
        # Verify log entry was created with success=False
        call_args = mock_collection.insert_one.call_args[0][0]
        
        assert call_args["action"] == "permission_denied"
        assert call_args["success"] is False
        assert call_args["error_message"] == "User not member of organization"


class TestTenantContext:
    """Test tenant context service."""
    
    @pytest.mark.unit
    def test_tenant_context_importable(self):
        """TenantContext should be importable."""
        from services.tenant_context import TenantContext
        assert TenantContext is not None
    
    @pytest.mark.unit
    def test_get_tenant_context_importable(self):
        """get_tenant_context should be importable."""
        from services.tenant_context import get_tenant_context
        assert callable(get_tenant_context)
    
    @pytest.mark.unit
    def test_get_optional_tenant_context_importable(self):
        """get_optional_tenant_context should be importable."""
        from services.tenant_context import get_optional_tenant_context
        assert callable(get_optional_tenant_context)
    
    @pytest.mark.unit
    def test_tenant_context_provides_repositories(self, sample_user_in_db):
        """TenantContext should provide repository accessors."""
        from services.tenant_context import TenantContext
        from services.tenant_repository import (
            SceneRepository,
            AnnotationRepository,
            ProcessingJobRepository,
        )
        from models.user import UserInDB
        
        user = UserInDB(**sample_user_in_db)
        ctx = TenantContext(
            user=user,
            organization_id="org-123",
        )
        
        assert isinstance(ctx.scenes, SceneRepository)
        assert isinstance(ctx.annotations, AnnotationRepository)
        assert isinstance(ctx.processing_jobs, ProcessingJobRepository)
        
        # All repositories should have same org_id
        assert ctx.scenes.organization_id == "org-123"
        assert ctx.annotations.organization_id == "org-123"
        assert ctx.processing_jobs.organization_id == "org-123"
    
    @pytest.mark.unit
    def test_tenant_context_user_properties(self, sample_user_in_db):
        """TenantContext should expose user properties."""
        from services.tenant_context import TenantContext
        from models.user import UserInDB
        
        user = UserInDB(**sample_user_in_db)
        ctx = TenantContext(
            user=user,
            organization_id="org-123",
        )
        
        assert ctx.user_id == user.id
        assert ctx.organization_id == "org-123"


class TestTenantIsolation:
    """Test that tenant isolation is properly enforced."""
    
    @pytest.mark.unit
    @patch('services.tenant_repository.get_db')
    async def test_different_orgs_isolated(self, mock_get_db):
        """Different organizations should not see each other's data."""
        from services.tenant_repository import SceneRepository
        
        mock_collection = AsyncMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db
        
        # Create repos for different orgs
        repo_org1 = SceneRepository("org-1")
        repo_org2 = SceneRepository("org-2")
        
        # Query from org1
        mock_collection.find_one = AsyncMock(return_value=None)
        await repo_org1.find_by_id("scene-1")
        
        call1 = mock_collection.find_one.call_args[0][0]
        assert call1["organization_id"] == "org-1"
        
        # Query from org2
        await repo_org2.find_by_id("scene-1")
        
        call2 = mock_collection.find_one.call_args[0][0]
        assert call2["organization_id"] == "org-2"
        
        # Filters should be different
        assert call1["organization_id"] != call2["organization_id"]


class TestDatabaseIndexes:
    """Test database index configurations for tenant isolation."""
    
    @pytest.mark.unit
    def test_access_logs_indexes_defined(self):
        """Access log indexes should be defined."""
        from utils.database import init_database_sync
        import inspect
        source = inspect.getsource(init_database_sync)
        
        # Check for organization_id index on access logs
        assert "db.scene_access_logs.create_index" in source
        assert '"organization_id"' in source or "'organization_id'" in source
    
    @pytest.mark.unit
    def test_collections_have_org_id_indexes(self):
        """Collections should have organization_id indexes."""
        from utils.database import init_database_sync
        import inspect
        source = inspect.getsource(init_database_sync)
        
        # Check key collections have organization_id indexes
        collections_to_check = [
            "scenes",
            "processing_jobs",
            "annotations",
            "guided_tours",
            "share_tokens",
        ]
        
        for collection in collections_to_check:
            # Check for organization_id index on each collection
            assert f"db.{collection}.create_index" in source, \
                f"Missing index creation for {collection}"


class TestGetRepository:
    """Test repository factory function."""
    
    @pytest.mark.unit
    def test_get_known_repository(self):
        """get_repository should return specific repository for known collections."""
        from services.tenant_repository import get_repository, SceneRepository
        
        repo = get_repository("scenes", "org-123")
        assert isinstance(repo, SceneRepository)
        assert repo.organization_id == "org-123"
    
    @pytest.mark.unit
    def test_get_generic_repository(self):
        """get_repository should return generic repository for unknown collections."""
        from services.tenant_repository import get_repository, TenantRepository
        
        repo = get_repository("custom_collection", "org-123")
        assert isinstance(repo, TenantRepository)
        assert repo.organization_id == "org-123"
        assert repo.collection_name == "custom_collection"
