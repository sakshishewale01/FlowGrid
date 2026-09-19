"""
Authentication Schemas
======================
Pydantic schemas for registration requests, login payloads, and JWT token responses.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole
from app.schemas.user import UserResponse


class UserRegisterRequest(BaseModel):
    """
    Payload for user registration endpoint (POST /api/v1/auth/register).
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user",
        examples=["Sarah Jenkins"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid and unique corporate or personal email address",
        examples=["sarah.jenkins@flowgrid.io"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Plain-text password (will be hashed with Argon2id)",
        examples=["SecurePass2026!"],
    )
    role: UserRole = Field(
        default=UserRole.VIEWER,
        description="Assigned role: ADMIN, MANAGER, DRIVER, or VIEWER",
        examples=[UserRole.MANAGER],
    )


class UserLoginRequest(BaseModel):
    """
    Payload for user login endpoint (POST /api/v1/auth/login).
    """
    email: EmailStr = Field(
        ...,
        description="Registered user email",
        examples=["sarah.jenkins@flowgrid.io"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User account password",
        examples=["SecurePass2026!"],
    )


class TokenResponse(BaseModel):
    """
    Authentication response returned after successful registration or login.
    """
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token scheme (bearer)")
    user: Optional[UserResponse] = Field(
        default=None,
        description="Public user details associated with the issued token",
    )
