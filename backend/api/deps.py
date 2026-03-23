from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional

from utils.config import settings
from utils.database import get_db
from utils.valkey_client import ValkeyClient
from models.user import UserResponse
from models.token import TokenPayload


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login"
)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """
    Decodes the JWT access token, checks it against the Valkey blacklist,
    and returns the MongoDB user. Used as a dependency to protect endpoints.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
        
        # Ensure it is not blacklisted (e.g., logged out)
        valkey = ValkeyClient()
        if valkey.is_token_blacklisted(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    db = await get_db()
    user_doc = await db.users.find_one({"_id": token_data.sub})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = UserResponse(**user_doc)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user



async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme_optional)) -> Optional[UserResponse]:
    """
    Optional authentication dependency.
    Returns user if valid token provided, None otherwise.
    Used for endpoints that work with or without authentication.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
        
        # Check blacklist
        valkey = ValkeyClient()
        if valkey.is_token_blacklisted(token_data.jti):
            return None
            
    except (JWTError, ValidationError):
        return None
        
    db = await get_db()
    user_doc = await db.users.find_one({"_id": token_data.sub})
    
    if not user_doc:
        return None
        
    user = UserResponse(**user_doc)
    if not user.is_active:
        return None
        
    return user


async def get_current_user_ws(token: Optional[str] = None) -> UserResponse:
    """
    WebSocket-compatible authentication dependency.
    Validates JWT token for WebSocket connections.
    
    Args:
        token: JWT token (passed as query parameter for WebSocket)
        
    Returns:
        UserResponse object
        
    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
        
        # Check blacklist
        valkey = ValkeyClient()
        if valkey.is_token_blacklisted(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
    db = await get_db()
    user_doc = await db.users.find_one({"_id": token_data.sub})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = UserResponse(**user_doc)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user
