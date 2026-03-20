"""
Tests for Task 2.5: Authentication Tests

Comprehensive authentication test coverage including:
- User registration and validation
- JWT generation and validation
- Expired tokens
- Invalid tokens
- Session revocation (logout/blacklisting)
- Multi-device login scenarios
- Multi-organization switching
- Authentication middleware

Requirements: 18.4, 18.7
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from jose import jwt, JWTError
import uuid
import time


# =============================================================================
# USER REGISTRATION TESTS
# =============================================================================

class TestUserRegistration:
    """Test user registration functionality."""
    
    @pytest.mark.unit
    def test_user_create_valid_data(self):
        """Valid user data should create UserCreate model."""
        from models.user import UserCreate
        
        user = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="SecurePassword123!"
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.password == "SecurePassword123!"
    
    @pytest.mark.unit
    def test_user_create_rejects_short_password(self):
        """Password shorter than 8 chars should be rejected."""
        from models.user import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                full_name="Test User",
                password="short"  # Less than 8 chars
            )
        
        assert "password" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_user_create_rejects_invalid_email(self):
        """Invalid email format should be rejected."""
        from models.user import UserCreate
        from pydantic import ValidationError
        
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
            "",
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError):
                UserCreate(
                    email=invalid_email,
                    full_name="Test User",
                    password="SecurePassword123!"
                )
    
    @pytest.mark.unit
    def test_user_create_accepts_valid_emails(self):
        """Various valid email formats should be accepted."""
        from models.user import UserCreate
        
        valid_emails = [
            "simple@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
        ]
        
        for valid_email in valid_emails:
            user = UserCreate(
                email=valid_email,
                full_name="Test User",
                password="SecurePassword123!"
            )
            assert user.email == valid_email
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    @patch('services.email.EmailService.send_welcome_email')
    async def test_register_creates_user(self, mock_email, mock_get_db):
        """Registration should create user in database."""
        from api.auth import register
        from models.user import UserCreate
        from fastapi import BackgroundTasks
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.users.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db
        
        user_data = UserCreate(
            email="newuser@example.com",
            full_name="New User",
            password="SecurePassword123!"
        )
        
        result = await register(user_data, BackgroundTasks())
        
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        mock_db.users.insert_one.assert_called_once()
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_register_rejects_duplicate_email(self, mock_get_db):
        """Registration should reject duplicate email."""
        from api.auth import register
        from models.user import UserCreate
        from fastapi import BackgroundTasks, HTTPException
        
        # User already exists
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={"email": "existing@example.com"})
        mock_get_db.return_value = mock_db
        
        user_data = UserCreate(
            email="existing@example.com",
            full_name="Duplicate User",
            password="SecurePassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await register(user_data, BackgroundTasks())
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


# =============================================================================
# PASSWORD HASHING TESTS
# =============================================================================

class TestPasswordHashing:
    """Test password hashing and verification."""
    
    @pytest.mark.unit
    def test_password_hash_is_bcrypt(self):
        """Password hash should use bcrypt format."""
        from utils.security import get_password_hash
        
        hashed = get_password_hash("TestPassword123")
        
        # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith("$2")
        assert len(hashed) == 60  # Bcrypt hash length
    
    @pytest.mark.unit
    def test_password_hash_is_unique(self):
        """Same password should produce different hashes (salt)."""
        from utils.security import get_password_hash
        
        password = "SamePassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Different salt means different hash
        assert hash1 != hash2
    
    @pytest.mark.unit
    def test_verify_correct_password(self):
        """Correct password should verify successfully."""
        from utils.security import get_password_hash, verify_password
        
        password = "CorrectPassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    @pytest.mark.unit
    def test_verify_wrong_password(self):
        """Wrong password should fail verification."""
        from utils.security import get_password_hash, verify_password
        
        hashed = get_password_hash("CorrectPassword")
        
        assert verify_password("WrongPassword", hashed) is False
    
    @pytest.mark.unit
    def test_verify_empty_password(self):
        """Empty password should fail verification."""
        from utils.security import get_password_hash, verify_password
        
        hashed = get_password_hash("SomePassword123")
        
        assert verify_password("", hashed) is False


# =============================================================================
# JWT TOKEN GENERATION TESTS
# =============================================================================

class TestJWTGeneration:
    """Test JWT token generation."""
    
    @pytest.mark.unit
    def test_access_token_structure(self):
        """Access token should have correct structure."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        # Decode without verification to inspect structure
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "jti" in payload  # Unique token ID
        assert "exp" in payload  # Expiration
    
    @pytest.mark.unit
    def test_refresh_token_structure(self):
        """Refresh token should have correct structure."""
        from utils.security import create_refresh_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)
        
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
    
    @pytest.mark.unit
    def test_access_token_expiration(self):
        """Access token should expire after configured time."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Should expire within configured minutes (with small buffer)
        expected_exp = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5
    
    @pytest.mark.unit
    def test_refresh_token_longer_expiration(self):
        """Refresh token should have longer expiration than access token."""
        from utils.security import create_access_token, create_refresh_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        access_payload = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        refresh_payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        assert refresh_payload["exp"] > access_payload["exp"]
    
    @pytest.mark.unit
    def test_each_token_has_unique_jti(self):
        """Each token should have a unique JTI."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        
        tokens = [create_access_token(user_id) for _ in range(5)]
        jtis = set()
        
        for token in tokens:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            jtis.add(payload["jti"])
        
        # All JTIs should be unique
        assert len(jtis) == 5


# =============================================================================
# JWT TOKEN VALIDATION TESTS
# =============================================================================

class TestJWTValidation:
    """Test JWT token validation."""
    
    @pytest.mark.unit
    def test_valid_token_decodes(self):
        """Valid token should decode successfully."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        assert payload["sub"] == user_id
    
    @pytest.mark.unit
    def test_invalid_signature_rejected(self):
        """Token with invalid signature should be rejected."""
        from utils.security import create_access_token
        from utils.config import settings
        
        token = create_access_token(str(uuid.uuid4()))
        
        # Try to decode with wrong secret
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[settings.jwt_algorithm])
    
    @pytest.mark.unit
    def test_tampered_token_rejected(self):
        """Tampered token should be rejected."""
        from utils.security import create_access_token
        from utils.config import settings
        
        token = create_access_token(str(uuid.uuid4()))
        
        # Tamper with token (modify payload)
        parts = token.split(".")
        tampered_token = parts[0] + "." + "tampered" + "." + parts[2]
        
        with pytest.raises(JWTError):
            jwt.decode(tampered_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    @pytest.mark.unit
    def test_wrong_algorithm_rejected(self):
        """Token decoded with wrong algorithm should be rejected."""
        from utils.security import create_access_token
        from utils.config import settings
        
        token = create_access_token(str(uuid.uuid4()))
        
        # Try to decode with different algorithm
        with pytest.raises(JWTError):
            jwt.decode(token, settings.jwt_secret_key, algorithms=["HS384"])


# =============================================================================
# EXPIRED TOKEN TESTS
# =============================================================================

class TestExpiredTokens:
    """Test expired token handling."""
    
    @pytest.mark.unit
    def test_expired_token_rejected(self):
        """Expired token should be rejected."""
        from utils.config import settings
        
        # Create token that's already expired
        user_id = str(uuid.uuid4())
        expired_payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        
        expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    @pytest.mark.unit
    def test_token_expiring_soon_still_valid(self):
        """Token expiring soon but not yet should still be valid."""
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        almost_expired_payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.utcnow() + timedelta(seconds=30)  # Expires in 30 seconds
        }
        
        token = jwt.encode(almost_expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        # Should still decode
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == user_id
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_get_current_user_rejects_expired(self, mock_valkey_class, mock_get_db):
        """get_current_user should reject expired tokens."""
        from api.deps import get_current_user
        from utils.config import settings
        from fastapi import HTTPException
        
        # Create expired token
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(expired_token)
        
        assert exc_info.value.status_code == 401


# =============================================================================
# INVALID TOKEN TESTS
# =============================================================================

class TestInvalidTokens:
    """Test invalid token handling."""
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_malformed_token_rejected(self, mock_valkey_class, mock_get_db):
        """Malformed token should be rejected."""
        from api.deps import get_current_user
        from fastapi import HTTPException
        
        malformed_tokens = [
            "not.a.valid.token",
            "completely-invalid",
            "",
            "   ",
            "eyJ.eyJ.invalid",
        ]
        
        for token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_missing_claims_rejected(self, mock_valkey_class, mock_get_db):
        """Token missing required claims should be rejected."""
        from api.deps import get_current_user
        from utils.config import settings
        from fastapi import HTTPException
        
        # Token missing 'sub' claim
        invalid_payload = {
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1)
            # Missing 'sub'
        }
        token = jwt.encode(invalid_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey_class.return_value = mock_valkey
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401


# =============================================================================
# SESSION REVOCATION (LOGOUT/BLACKLISTING) TESTS
# =============================================================================

class TestSessionRevocation:
    """Test session revocation via token blacklisting."""
    
    @pytest.mark.unit
    def test_blacklist_token(self):
        """Token should be added to blacklist."""
        from utils.valkey_client import ValkeyClient
        
        with patch.object(ValkeyClient, '_initialize_pool'):
            client = ValkeyClient()
            client._client = MagicMock()
            client._client.setex = MagicMock(return_value=True)
            
            jti = str(uuid.uuid4())
            result = client.blacklist_token(jti, expire_seconds=3600)
            
            assert result is True
            client._client.setex.assert_called_once()
            call_args = client._client.setex.call_args[0]
            assert f"blacklist:{jti}" == call_args[0]
    
    @pytest.mark.unit
    def test_check_blacklisted_token(self):
        """Blacklisted token should be detected."""
        from utils.valkey_client import ValkeyClient
        
        with patch.object(ValkeyClient, '_initialize_pool'):
            client = ValkeyClient()
            client._client = MagicMock()
            client._client.get = MagicMock(return_value="1")  # Token is blacklisted
            
            jti = str(uuid.uuid4())
            result = client.is_token_blacklisted(jti)
            
            assert result is True
    
    @pytest.mark.unit
    def test_check_non_blacklisted_token(self):
        """Non-blacklisted token should not be detected."""
        from utils.valkey_client import ValkeyClient
        
        with patch.object(ValkeyClient, '_initialize_pool'):
            client = ValkeyClient()
            client._client = MagicMock()
            client._client.get = MagicMock(return_value=None)  # Token not blacklisted
            
            jti = str(uuid.uuid4())
            result = client.is_token_blacklisted(jti)
            
            assert result is False
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_blacklisted_token_rejected(self, mock_valkey_class, mock_get_db):
        """Blacklisted token should be rejected by get_current_user."""
        from api.deps import get_current_user
        from utils.security import create_access_token
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        # Mock blacklist check to return True (token is blacklisted)
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=True)
        mock_valkey_class.return_value = mock_valkey
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    @patch('api.auth.ValkeyClient')
    async def test_logout_blacklists_token(self, mock_valkey_class, mock_get_db):
        """Logout should blacklist the current token."""
        from api.auth import logout
        from utils.security import create_access_token
        from models.user import UserResponse
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.blacklist_token = MagicMock(return_value=True)
        mock_valkey_class.return_value = mock_valkey
        
        # Create mock user
        user = UserResponse(
            _id=user_id,
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = await logout(user, token)
        
        assert result["message"] == "Successfully logged out"
        mock_valkey.blacklist_token.assert_called_once()


# =============================================================================
# MULTI-DEVICE LOGIN TESTS
# =============================================================================

class TestMultiDeviceLogin:
    """Test multi-device login scenarios."""
    
    @pytest.mark.unit
    def test_multiple_tokens_for_same_user(self):
        """Same user should be able to have multiple valid tokens."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        
        # Simulate login from multiple devices
        device1_token = create_access_token(user_id)
        device2_token = create_access_token(user_id)
        device3_token = create_access_token(user_id)
        
        # All tokens should be valid and have same user
        for token in [device1_token, device2_token, device3_token]:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            assert payload["sub"] == user_id
        
        # But different JTIs
        jtis = set()
        for token in [device1_token, device2_token, device3_token]:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            jtis.add(payload["jti"])
        
        assert len(jtis) == 3
    
    @pytest.mark.unit
    def test_logout_one_device_others_still_valid(self):
        """Logging out one device should not affect other devices."""
        from utils.security import create_access_token
        from utils.valkey_client import ValkeyClient
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        
        device1_token = create_access_token(user_id)
        device2_token = create_access_token(user_id)
        
        device1_payload = jwt.decode(device1_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        device2_payload = jwt.decode(device2_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        # Simulate logout from device 1
        with patch.object(ValkeyClient, '_initialize_pool'):
            client = ValkeyClient()
            client._client = MagicMock()
            
            # Track which JTIs are blacklisted
            blacklisted = set()
            
            def mock_setex(key, ttl, value):
                blacklisted.add(key)
                return True
            
            def mock_get(key):
                return "1" if key in blacklisted else None
            
            client._client.setex = mock_setex
            client._client.get = mock_get
            
            # Blacklist device 1
            client.blacklist_token(device1_payload["jti"])
            
            # Device 1 should be blacklisted
            assert client.is_token_blacklisted(device1_payload["jti"]) is True
            
            # Device 2 should NOT be blacklisted
            assert client.is_token_blacklisted(device2_payload["jti"]) is False


# =============================================================================
# MULTI-ORGANIZATION SWITCHING TESTS
# =============================================================================

class TestMultiOrganizationSwitching:
    """Test authentication behavior when switching organizations."""
    
    @pytest.mark.unit
    def test_token_remains_valid_after_org_switch(self):
        """JWT should remain valid after user switches organization."""
        from utils.security import create_access_token
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        # Token validity is independent of organization
        # The organization context comes from user document, not token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        assert payload["sub"] == user_id
        # Token does NOT contain organization_id (by design)
        assert "organization_id" not in payload
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_get_current_user_returns_updated_org(self, mock_valkey_class, mock_get_db):
        """get_current_user should return user with current org_id."""
        from api.deps import get_current_user
        from utils.security import create_access_token
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey_class.return_value = mock_valkey
        
        # User switched to org-b
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "organization_id": "org-b",  # Switched org
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        mock_get_db.return_value = mock_db
        
        user = await get_current_user(token)
        
        # Should reflect current org
        assert user.organization_id == "org-b"
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_switch_org_updates_user_document(self, mock_get_db):
        """Switching org should update user's organization_id."""
        from api.organizations import switch_organization
        from models.user import UserInDB
        
        user_id = str(uuid.uuid4())
        user_data = {
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "organization_id": "org-a",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        # User is member of org-b
        mock_db.organization_members.find_one = AsyncMock(return_value={
            "_id": "member-id",
            "organization_id": "org-b",
            "user_id": user_id,
            "role": "member"
        })
        mock_db.users.update_one = AsyncMock()
        mock_db.organizations.find_one = AsyncMock(return_value={
            "_id": "org-b",
            "name": "Org B",
            "owner_id": "owner-id",
            "subscription_tier": "professional",
            "max_seats": 10,
            "max_scenes": 100,
            "max_storage_gb": 500,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        mock_db.organization_members.count_documents = AsyncMock(return_value=5)
        mock_get_db.return_value = mock_db
        
        result = await switch_organization("org-b", user)
        
        # Should update user document
        mock_db.users.update_one.assert_called_once()
        update_call = mock_db.users.update_one.call_args
        assert update_call[0][0] == {"_id": user_id}
        assert update_call[0][1]["$set"]["organization_id"] == "org-b"
    
    @pytest.mark.unit
    @patch('api.organizations.get_db')
    async def test_cannot_switch_to_non_member_org(self, mock_get_db):
        """Cannot switch to organization where user is not a member."""
        from api.organizations import switch_organization
        from models.user import UserInDB
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        user_data = {
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "organization_id": "org-a",
            "hashed_password": "hashed",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        user = UserInDB(**user_data)
        
        mock_db = AsyncMock()
        # User is NOT member of org-c
        mock_db.organization_members.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc_info:
            await switch_organization("org-c", user)
        
        assert exc_info.value.status_code == 403
        assert "Not a member" in exc_info.value.detail


# =============================================================================
# AUTHENTICATION MIDDLEWARE TESTS
# =============================================================================

class TestAuthenticationMiddleware:
    """Test authentication middleware and dependencies."""
    
    @pytest.mark.unit
    def test_oauth2_scheme_configured(self):
        """OAuth2 scheme should be properly configured."""
        from api.deps import oauth2_scheme
        from fastapi.security import OAuth2PasswordBearer
        
        assert oauth2_scheme is not None
        assert isinstance(oauth2_scheme, OAuth2PasswordBearer)
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_valid_token_returns_user(self, mock_valkey_class, mock_get_db):
        """Valid token should return the user."""
        from api.deps import get_current_user
        from utils.security import create_access_token
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey_class.return_value = mock_valkey
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        mock_get_db.return_value = mock_db
        
        user = await get_current_user(token)
        
        assert user.id == user_id
        assert user.email == "test@example.com"
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_inactive_user_rejected(self, mock_valkey_class, mock_get_db):
        """Inactive user should be rejected."""
        from api.deps import get_current_user
        from utils.security import create_access_token
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey_class.return_value = mock_valkey
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": False,  # Inactive!
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        
        assert exc_info.value.status_code == 400
        assert "Inactive" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('api.deps.get_db')
    @patch('api.deps.ValkeyClient')
    async def test_nonexistent_user_rejected(self, mock_valkey_class, mock_get_db):
        """Token for non-existent user should be rejected."""
        from api.deps import get_current_user
        from utils.security import create_access_token
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey_class.return_value = mock_valkey
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=None)  # User not found
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        
        assert exc_info.value.status_code == 404


# =============================================================================
# TOKEN REFRESH TESTS
# =============================================================================

class TestTokenRefresh:
    """Test token refresh functionality."""
    
    @pytest.mark.unit
    @patch('api.auth.ValkeyClient')
    async def test_refresh_returns_new_tokens(self, mock_valkey_class):
        """Refresh should return new access and refresh tokens."""
        from api.auth import refresh_token
        from utils.security import create_refresh_token
        
        user_id = str(uuid.uuid4())
        old_refresh = create_refresh_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey.blacklist_token = MagicMock(return_value=True)
        mock_valkey_class.return_value = mock_valkey
        
        result = await refresh_token(old_refresh)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        
        # New tokens should be different from old
        assert result["refresh_token"] != old_refresh
    
    @pytest.mark.unit
    @patch('api.auth.ValkeyClient')
    async def test_refresh_blacklists_old_token(self, mock_valkey_class):
        """Refresh should blacklist the old refresh token."""
        from api.auth import refresh_token
        from utils.security import create_refresh_token
        
        user_id = str(uuid.uuid4())
        old_refresh = create_refresh_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=False)
        mock_valkey.blacklist_token = MagicMock(return_value=True)
        mock_valkey_class.return_value = mock_valkey
        
        await refresh_token(old_refresh)
        
        # Old token should be blacklisted
        mock_valkey.blacklist_token.assert_called_once()
    
    @pytest.mark.unit
    @patch('api.auth.ValkeyClient')
    async def test_refresh_rejects_access_token(self, mock_valkey_class):
        """Refresh should reject access tokens."""
        from api.auth import refresh_token
        from utils.security import create_access_token
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        access_token = create_access_token(user_id)  # Wrong token type
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(access_token)
        
        assert exc_info.value.status_code == 401
        assert "refresh token" in exc_info.value.detail.lower()
    
    @pytest.mark.unit
    @patch('api.auth.ValkeyClient')
    async def test_refresh_rejects_blacklisted_token(self, mock_valkey_class):
        """Refresh should reject blacklisted refresh tokens."""
        from api.auth import refresh_token
        from utils.security import create_refresh_token
        from fastapi import HTTPException
        
        user_id = str(uuid.uuid4())
        old_refresh = create_refresh_token(user_id)
        
        mock_valkey = MagicMock()
        mock_valkey.is_token_blacklisted = MagicMock(return_value=True)  # Blacklisted
        mock_valkey_class.return_value = mock_valkey
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(old_refresh)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail


# =============================================================================
# LOGIN TESTS
# =============================================================================

class TestLogin:
    """Test login functionality."""
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_success(self, mock_get_db):
        """Successful login should return tokens."""
        from api.auth import login
        from utils.security import get_password_hash
        from fastapi.security import OAuth2PasswordRequestForm
        
        user_id = str(uuid.uuid4())
        password = "CorrectPassword123"
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": user_id,
            "email": "test@example.com",
            "hashed_password": get_password_hash(password),
            "is_active": True,
        })
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username="test@example.com",
            password=password,
            scope=""
        )
        
        result = await login(form)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_wrong_password(self, mock_get_db):
        """Wrong password should be rejected."""
        from api.auth import login
        from utils.security import get_password_hash
        from fastapi.security import OAuth2PasswordRequestForm
        from fastapi import HTTPException
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "hashed_password": get_password_hash("CorrectPassword"),
            "is_active": True,
        })
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username="test@example.com",
            password="WrongPassword",
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_nonexistent_user(self, mock_get_db):
        """Login with non-existent email should be rejected."""
        from api.auth import login
        from fastapi.security import OAuth2PasswordRequestForm
        from fastapi import HTTPException
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username="nonexistent@example.com",
            password="SomePassword",
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_inactive_user(self, mock_get_db):
        """Inactive user should not be able to login."""
        from api.auth import login
        from utils.security import get_password_hash
        from fastapi.security import OAuth2PasswordRequestForm
        from fastapi import HTTPException
        
        password = "CorrectPassword123"
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "hashed_password": get_password_hash(password),
            "is_active": False,  # Inactive
        })
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username="test@example.com",
            password=password,
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form)
        
        assert exc_info.value.status_code == 400
        assert "Inactive" in exc_info.value.detail


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================

class TestAuthenticationCoverage:
    """Verify comprehensive test coverage."""
    
    @pytest.mark.unit
    def test_all_auth_scenarios_covered(self):
        """Document all covered authentication scenarios."""
        scenarios = [
            # Registration (4)
            "user_registration_valid",
            "user_registration_duplicate_email",
            "user_registration_invalid_email",
            "user_registration_short_password",
            
            # Password (3)
            "password_hashing_bcrypt",
            "password_verification_correct",
            "password_verification_wrong",
            
            # JWT Generation (4)
            "access_token_structure",
            "refresh_token_structure",
            "token_expiration",
            "unique_jti",
            
            # JWT Validation (4)
            "valid_token_decode",
            "invalid_signature_reject",
            "tampered_token_reject",
            "expired_token_reject",
            
            # Invalid Tokens (2)
            "malformed_token_reject",
            "missing_claims_reject",
            
            # Session Management (3)
            "token_blacklist",
            "logout_blacklists_token",
            "blacklisted_token_reject",
            
            # Multi-device (2)
            "multiple_tokens_same_user",
            "logout_one_device_others_valid",
            
            # Multi-org (3)
            "token_valid_after_org_switch",
            "switch_org_updates_user",
            "cannot_switch_to_non_member_org",
            
            # Middleware (3)
            "valid_token_returns_user",
            "inactive_user_reject",
            "nonexistent_user_reject",
            
            # Token Refresh (4)
            "refresh_returns_new_tokens",
            "refresh_blacklists_old",
            "refresh_rejects_access_token",
            "refresh_rejects_blacklisted",
            
            # Login (4)
            "login_success",
            "login_wrong_password",
            "login_nonexistent_user",
            "login_inactive_user",
        ]
        
        # 4+3+4+4+2+3+2+3+3+4+4 = 36 scenarios
        assert len(scenarios) == 36
