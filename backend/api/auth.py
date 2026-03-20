import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import structlog

from utils.database import get_db
from models.user import UserCreate, UserInDB, UserResponse
from models.token import Token, TokenPayload
from utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from services.email import EmailService
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from api.deps import get_current_user, oauth2_scheme
from utils.valkey_client import ValkeyClient
from jose import jwt, JWTError
from pydantic import ValidationError
from utils.config import settings
from typing import Any

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    """
    Register a new user in the platform.
    Hashes their password and confirms uniqueness of the email.
    """
    db = await get_db()
    users_collection = db.users
    
    # 1. Check if user email already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        logger.warning("registration_failed_duplicate", email=user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
    
    # 2. Map payload to internal representation
    now = datetime.utcnow()
    # Pydantic EmailStr stores internally as string, but ensuring it's str for mongodb
    new_user_db = UserInDB(
        _id=str(uuid.uuid4()),
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        created_at=now,
        updated_at=now
    )
    
    # Dump for mongodb ensuring datetime is handled if needed
    user_dict = new_user_db.dict(by_alias=True)
    
    # 3. Create the user
    try:
        await users_collection.insert_one(user_dict)
        logger.info("user_registered", user_id=new_user_db.id, email=new_user_db.email)
    except Exception as e:
        logger.error("registration_db_insert_failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to database error."
        )
    
    # 4. Enqueue Welcome Email asynchronously
    background_tasks.add_task(
        EmailService.send_welcome_email, email=new_user_db.email, name=new_user_db.full_name
    )
    
    # 5. Return safe response projection
    return UserResponse(**user_dict)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    db = await get_db()
    user_doc = await db.users.find_one({"email": form_data.username})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
        
    hashed_password = user_doc.get("hashed_password")
    if not verify_password(form_data.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
        
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    user_id = str(user_doc["_id"])
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get the current authenticated user's information.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: UserResponse = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Logout the user by adding the current JWT Access Token to a blacklist,
    instantly terminating access until a new login or refresh occurs.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
        
        # Determine remaining lifespan of token to store in Valkey cheaply
        exp = payload.get("exp", 0)
        now = int(datetime.utcnow().timestamp())
        expire_seconds = max(0, exp - now)
        
        if expire_seconds > 0:
            valkey = ValkeyClient()
            success = valkey.blacklist_token(token_data.jti, expire_seconds)
            if not success:
               logger.warning("token_blacklist_failed", jti=token_data.jti) 
               
    except Exception as e:
        logger.error("logout_error_parsing", exc_info=e)
        
    return {"message": "Successfully logged out"}


from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(request: RefreshTokenRequest):
    """Grants a new access token and refresh token when given a valid refresh token."""
    try:
        payload = jwt.decode(
            request.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_data = TokenPayload(**payload)
        
        # Must be a refresh token explicitly
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type, must provide refresh token",
            )
            
        # Ensure refresh token isn't blacklisted (e.g if it was revoked)
        valkey = ValkeyClient()
        if valkey.is_token_blacklisted(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
            
        # Invalidate the old refresh token so it can only be used once (Rotation)
        exp = payload.get("exp", 0)
        now = int(datetime.utcnow().timestamp())
        if exp - now > 0:
            valkey.blacklist_token(token_data.jti, exp - now)
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = token_data.sub
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }
