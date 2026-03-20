"""
Tests for Tasks 2.1 and 2.2: User registration and JWT authentication.

Task 2.1: User registration system
Task 2.2: JWT authentication

Requirements: 18.4, 18.5
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid


class TestUserModels:
    """Test user model definitions."""
    
    @pytest.mark.unit
    def test_user_base_importable(self):
        """UserBase model should be importable."""
        from models.user import UserBase
        assert UserBase is not None
    
    @pytest.mark.unit
    def test_user_create_importable(self):
        """UserCreate model should be importable."""
        from models.user import UserCreate
        assert UserCreate is not None
    
    @pytest.mark.unit
    def test_user_in_db_importable(self):
        """UserInDB model should be importable."""
        from models.user import UserInDB
        assert UserInDB is not None
    
    @pytest.mark.unit
    def test_user_response_importable(self):
        """UserResponse model should be importable."""
        from models.user import UserResponse
        assert UserResponse is not None
    
    @pytest.mark.unit
    def test_user_create_requires_password(self):
        """UserCreate should require password with min length."""
        from models.user import UserCreate
        from pydantic import ValidationError
        
        # Valid user
        user = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="ValidPassword123"
        )
        assert user.password == "ValidPassword123"
        
        # Invalid - password too short
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                full_name="Test User",
                password="short"
            )
    
    @pytest.mark.unit
    def test_user_create_validates_email(self):
        """UserCreate should validate email format."""
        from models.user import UserCreate
        from pydantic import ValidationError
        
        # Valid email
        user = UserCreate(
            email="valid@example.com",
            full_name="Test User",
            password="ValidPassword123"
        )
        assert user.email == "valid@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                full_name="Test User",
                password="ValidPassword123"
            )


class TestTokenModels:
    """Test token model definitions."""
    
    @pytest.mark.unit
    def test_token_model_importable(self):
        """Token model should be importable."""
        from models.token import Token
        assert Token is not None
    
    @pytest.mark.unit
    def test_token_payload_importable(self):
        """TokenPayload model should be importable."""
        from models.token import TokenPayload
        assert TokenPayload is not None


class TestSecurityModule:
    """Test security utility functions."""
    
    @pytest.mark.unit
    def test_get_password_hash_importable(self):
        """get_password_hash should be importable."""
        from utils.security import get_password_hash
        assert callable(get_password_hash)
    
    @pytest.mark.unit
    def test_verify_password_importable(self):
        """verify_password should be importable."""
        from utils.security import verify_password
        assert callable(verify_password)
    
    @pytest.mark.unit
    def test_create_access_token_importable(self):
        """create_access_token should be importable."""
        from utils.security import create_access_token
        assert callable(create_access_token)
    
    @pytest.mark.unit
    def test_create_refresh_token_importable(self):
        """create_refresh_token should be importable."""
        from utils.security import create_refresh_token
        assert callable(create_refresh_token)
    
    @pytest.mark.unit
    def test_password_hashing(self):
        """Password should be hashed correctly with bcrypt."""
        from utils.security import get_password_hash, verify_password
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Hash should be different from original
        assert hashed != password
        # Hash should start with bcrypt identifier
        assert hashed.startswith("$2b$")
        # Verification should work
        assert verify_password(password, hashed) is True
        # Wrong password should fail
        assert verify_password("WrongPassword", hashed) is False
    
    @pytest.mark.unit
    def test_access_token_creation(self):
        """Access token should be created correctly."""
        from utils.security import create_access_token
        from jose import jwt
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        
        # Token should be a string
        assert isinstance(token, str)
        
        # Token should be decodable
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
    
    @pytest.mark.unit
    def test_refresh_token_creation(self):
        """Refresh token should be created correctly."""
        from utils.security import create_refresh_token
        from jose import jwt
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)
        
        # Token should be a string
        assert isinstance(token, str)
        
        # Token should be decodable
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
    
    @pytest.mark.unit
    def test_access_token_expiration(self):
        """Access token should have correct expiration."""
        from utils.security import create_access_token
        from jose import jwt
        from utils.config import settings
        
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        # Check expiration is in the future
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now
        
        # Should expire within configured minutes
        max_exp = now + timedelta(minutes=settings.jwt_access_token_expire_minutes + 1)
        assert exp_time < max_exp


class TestAuthRouter:
    """Test authentication API router."""
    
    @pytest.mark.unit
    def test_auth_router_importable(self):
        """Auth router should be importable."""
        from api.auth import router
        assert router is not None
    
    @pytest.mark.unit
    def test_register_endpoint_exists(self):
        """Register endpoint should exist in router."""
        from api.auth import router
        routes = [r.path for r in router.routes]
        assert "/register" in routes
    
    @pytest.mark.unit
    def test_login_endpoint_exists(self):
        """Login endpoint should exist in router."""
        from api.auth import router
        routes = [r.path for r in router.routes]
        assert "/login" in routes
    
    @pytest.mark.unit
    def test_logout_endpoint_exists(self):
        """Logout endpoint should exist in router."""
        from api.auth import router
        routes = [r.path for r in router.routes]
        assert "/logout" in routes
    
    @pytest.mark.unit
    def test_refresh_endpoint_exists(self):
        """Refresh endpoint should exist in router."""
        from api.auth import router
        routes = [r.path for r in router.routes]
        assert "/refresh" in routes


class TestAuthDependencies:
    """Test authentication dependencies."""
    
    @pytest.mark.unit
    def test_oauth2_scheme_importable(self):
        """OAuth2 scheme should be importable."""
        from api.deps import oauth2_scheme
        assert oauth2_scheme is not None
    
    @pytest.mark.unit
    def test_get_current_user_importable(self):
        """get_current_user dependency should be importable."""
        from api.deps import get_current_user
        assert callable(get_current_user)


class TestRegistrationAPI:
    """Test user registration API endpoint."""
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    @patch('services.email.EmailService.send_welcome_email')
    async def test_register_new_user(self, mock_email, mock_get_db, sample_user_data):
        """Should register a new user successfully."""
        from api.auth import register
        from fastapi import BackgroundTasks
        from models.user import UserCreate
        
        # Setup mocks
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.users.insert_one = AsyncMock()
        mock_get_db.return_value = mock_db
        
        user = UserCreate(**sample_user_data)
        bg_tasks = BackgroundTasks()
        
        result = await register(user, bg_tasks)
        
        assert result.email == sample_user_data["email"]
        assert result.full_name == sample_user_data["full_name"]
        mock_db.users.insert_one.assert_called_once()
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_register_duplicate_email(self, mock_get_db, sample_user_data, sample_user_in_db):
        """Should reject registration with existing email."""
        from api.auth import register
        from fastapi import BackgroundTasks, HTTPException
        from models.user import UserCreate
        
        # Setup mock to return existing user
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=sample_user_in_db)
        mock_get_db.return_value = mock_db
        
        user = UserCreate(**sample_user_data)
        bg_tasks = BackgroundTasks()
        
        with pytest.raises(HTTPException) as exc_info:
            await register(user, bg_tasks)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


class TestLoginAPI:
    """Test login API endpoint."""
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_success(self, mock_get_db, sample_user_in_db):
        """Should login successfully with valid credentials."""
        from api.auth import login
        from fastapi.security import OAuth2PasswordRequestForm
        from utils.security import get_password_hash
        
        # Update the mock user with a real hashed password
        password = "TestPassword123!"
        sample_user_in_db["hashed_password"] = get_password_hash(password)
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=sample_user_in_db)
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username=sample_user_in_db["email"],
            password=password,
            scope=""
        )
        
        result = await login(form)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_invalid_email(self, mock_get_db):
        """Should reject login with non-existent email."""
        from api.auth import login
        from fastapi.security import OAuth2PasswordRequestForm
        from fastapi import HTTPException
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username="nonexistent@example.com",
            password="SomePassword123",
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form)
        
        assert exc_info.value.status_code == 400
        assert "Incorrect email or password" in exc_info.value.detail
    
    @pytest.mark.unit
    @patch('api.auth.get_db')
    async def test_login_wrong_password(self, mock_get_db, sample_user_in_db):
        """Should reject login with wrong password."""
        from api.auth import login
        from fastapi.security import OAuth2PasswordRequestForm
        from fastapi import HTTPException
        from utils.security import get_password_hash
        
        sample_user_in_db["hashed_password"] = get_password_hash("CorrectPassword")
        
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value=sample_user_in_db)
        mock_get_db.return_value = mock_db
        
        form = OAuth2PasswordRequestForm(
            username=sample_user_in_db["email"],
            password="WrongPassword",
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login(form)
        
        assert exc_info.value.status_code == 400


class TestEmailService:
    """Test email service."""
    
    @pytest.mark.unit
    def test_email_service_importable(self):
        """EmailService should be importable."""
        from services.email import EmailService
        assert EmailService is not None
    
    @pytest.mark.unit
    def test_send_welcome_email_method_exists(self):
        """send_welcome_email method should exist."""
        from services.email import EmailService
        assert hasattr(EmailService, 'send_welcome_email')
