from pydantic import BaseModel


class Token(BaseModel):
    """Schema for returning issued JWTs to the client."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Internal schema for token payload validation."""
    sub: str
    jti: str
