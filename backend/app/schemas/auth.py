"""
Authentication Schemas
======================
Pydantic schemas for registration requests, login payloads, and JWT token responses.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
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
        min_length=8,
        max_length=100,
        description="Strong password (will be hashed with Argon2id)",
        examples=["SecurePass2026!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if (
            not any(char.islower() for char in value)
            or not any(char.isupper() for char in value)
            or not any(char.isdigit() for char in value)
            or not any(not char.isalnum() for char in value)
        ):
            raise ValueError(
                "Password must include uppercase, lowercase, number, and special character"
            )
        return value


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
