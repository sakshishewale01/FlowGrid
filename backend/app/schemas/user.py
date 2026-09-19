"""
User Schemas
============
Pydantic models for user representations and responses.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.user import UserRole


class UserBase(BaseModel):
    """
    Shared attributes for user schemas.
    """
    name: str
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserResponse(BaseModel):
    """
    Public response schema for user data.
    Security Notice: `hashed_password` is intentionally excluded so credentials
    are never leaked in API payloads.
    """
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
