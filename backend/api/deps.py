from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from utils.config import settings
from utils.database import get_db
from utils.valkey_client import ValkeyClient
from models.user import UserResponse
from models.token import TokenPayload


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login"
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
