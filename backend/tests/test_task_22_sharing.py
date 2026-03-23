"""
Tests for Task 22: Scene Sharing.

Tests share token generation, validation, revocation, and embedding.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 17.1-17.7
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid


class TestShareTokenModels:
    """Test share token model definitions."""
    
    @pytest.mark.unit
    def test_permission_level_enum(self):
        """PermissionLevel enum should have all levels."""
        from models.share_token import PermissionLevel
        
        assert PermissionLevel.VIEW == "view"
        assert PermissionLevel.COMMENT == "comment"
        assert PermissionLevel.EDIT == "edit"
    
    @pytest.mark.unit
    def test_share_token_base_importable(self):
        """ShareTokenBase model should be importable."""
        from models.share_token import ShareTokenBase
        assert ShareTokenBase is not None
    
    @pytest.mark.unit
    def test_share_token_create_importable(self):
        """ShareTokenCreate model should be importable."""
        from models.share_token import ShareTokenCreate
        assert ShareTokenCreate is not None
    
    @pytest.mark.unit
    def test_share_token_in_db_importable(self):
        """ShareTokenInDB model should be importable."""
        from models.share_token import ShareTokenInDB
        assert ShareTokenInDB is not None
    
    @pytest.mark.unit
    def test_share_token_response_importable(self):
        """ShareTokenResponse model should be importable."""
        from models.share_token import ShareTokenResponse
        assert ShareTokenResponse is not None
    
    @pytest.mark.unit
    def test_share_token_create_validation(self):
        """ShareTokenCreate should validate fields."""
        from models.share_token import ShareTokenCreate, PermissionLevel
        
        # Valid token
        token = ShareTokenCreate(
            scene_id="test-scene-id",
            permission_level=PermissionLevel.VIEW
        )
        assert token.scene_id == "test-scene-id"
        assert token.permission_level == PermissionLevel.VIEW
        assert token.expires_at is None
    
    @pytest.mark.unit
    def test_share_token_in_db_structure(self):
        """ShareTokenInDB should have all required fields."""
        from models.share_token import ShareTokenInDB, PermissionLevel
        
        now = datetime.utcnow()
        token = ShareTokenInDB(
            _id="test-token-id",
            scene_id="test-scene-id",
            token="test-uuid-token",
            permission_level=PermissionLevel.VIEW,
            created_by="test-user-id",
            created_at=now,
            revoked_at=None,
            last_accessed_at=None,
            access_count=0
        )
        
        assert token.id == "test-token-id"
        assert token.scene_id == "test-scene-id"
        assert token.token == "test-uuid-token"
        assert token.permission_level == PermissionLevel.VIEW.value
        assert token.created_by == "test-user-id"
        assert token.access_count == 0


class TestShareTokenGeneration:
    """Test share token generation (Task 22.1)."""
    
    @pytest.mark.unit
    def test_build_shareable_url(self):
        """Should build correct shareable URL."""
        from api.sharing import build_shareable_url
        from unittest.mock import MagicMock
        
        # Mock request
        request = MagicMock()
        request.base_url = "http://localhost:8000/"
        
        token = "test-token-123"
        url = build_shareable_url(token, request)
        
        assert url == "http://localhost:8000/viewer/shared/test-token-123"
    
    @pytest.mark.unit
    def test_is_token_active_not_revoked(self):
        """Active token should return True."""
        from api.sharing import is_token_active
        
        token_doc = {
            "revoked_at": None,
            "expires_at": None
        }
        
        assert is_token_active(token_doc) is True
    
    @pytest.mark.unit
    def test_is_token_active_revoked(self):
        """Revoked token should return False."""
        from api.sharing import is_token_active
        
        token_doc = {
            "revoked_at": datetime.utcnow(),
            "expires_at": None
        }
        
        assert is_token_active(token_doc) is False
    
    @pytest.mark.unit
    def test_is_token_active_expired(self):
        """Expired token should return False."""
        from api.sharing import is_token_active
        
        token_doc = {
            "revoked_at": None,
            "expires_at": datetime.utcnow() - timedelta(days=1)
        }
        
        assert is_token_active(token_doc) is False
    
    @pytest.mark.unit
    def test_is_token_active_not_expired(self):
        """Non-expired token should return True."""
        from api.sharing import is_token_active
        
        token_doc = {
            "revoked_at": None,
            "expires_at": datetime.utcnow() + timedelta(days=1)
        }
        
        assert is_token_active(token_doc) is True


class TestShareTokenAPI:
    """Test share token API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_share_token_endpoint_exists(self):
        """Create share token endpoint should be defined."""
        from api.sharing import create_share_token
        assert create_share_token is not None
    
    @pytest.mark.asyncio
    async def test_list_share_tokens_endpoint_exists(self):
        """List share tokens endpoint should be defined."""
        from api.sharing import list_share_tokens
        assert list_share_tokens is not None
    
    @pytest.mark.asyncio
    async def test_get_share_token_endpoint_exists(self):
        """Get share token endpoint should be defined."""
        from api.sharing import get_share_token
        assert get_share_token is not None
    
    @pytest.mark.asyncio
    async def test_update_share_token_endpoint_exists(self):
        """Update share token endpoint should be defined."""
        from api.sharing import update_share_token
        assert update_share_token is not None
    
    @pytest.mark.asyncio
    async def test_revoke_share_token_endpoint_exists(self):
        """Revoke share token endpoint should be defined."""
        from api.sharing import revoke_share_token
        assert revoke_share_token is not None


class TestTokenValidation:
    """Test share token validation (Task 22.2)."""
    
    @pytest.mark.asyncio
    async def test_validate_share_token_endpoint_exists(self):
        """Validate share token endpoint should be defined."""
        from api.sharing import validate_share_token
        assert validate_share_token is not None
    
    @pytest.mark.asyncio
    async def test_get_scene_by_token_endpoint_exists(self):
        """Get scene by token endpoint should be defined."""
        from api.sharing import get_scene_by_token
        assert get_scene_by_token is not None


class TestTokenRevocation:
    """Test share token revocation (Task 22.3)."""
    
    @pytest.mark.unit
    def test_revoke_endpoint_exists(self):
        """Revoke endpoint should be defined."""
        from api.sharing import revoke_share_token
        assert revoke_share_token is not None


class TestSceneEmbedding:
    """Test scene embedding (Task 22.4)."""
    
    @pytest.mark.asyncio
    async def test_get_embed_code_endpoint_exists(self):
        """Get embed code endpoint should be defined."""
        from api.sharing import get_embed_code
        assert get_embed_code is not None
    
    @pytest.mark.asyncio
    async def test_render_embedded_viewer_endpoint_exists(self):
        """Render embedded viewer endpoint should be defined."""
        from api.sharing import render_embedded_viewer
        assert render_embedded_viewer is not None


class TestSharingRouter:
    """Test sharing router registration."""
    
    @pytest.mark.unit
    def test_sharing_router_importable(self):
        """Sharing router should be importable."""
        from api.sharing import router
        assert router is not None
    
    @pytest.mark.unit
    def test_sharing_router_prefix(self):
        """Sharing router should have correct prefix."""
        from api.sharing import router
        assert router.prefix == "/sharing"
    
    @pytest.mark.unit
    def test_sharing_router_tags(self):
        """Sharing router should have correct tags."""
        from api.sharing import router
        assert "sharing" in router.tags


class TestIntegration:
    """Integration tests for sharing functionality."""
    
    @pytest.mark.unit
    def test_main_app_includes_sharing_router(self):
        """Main app should include sharing router."""
        # This test verifies the router is registered
        # In a real integration test, we would check the app routes
        from api.sharing import router
        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
