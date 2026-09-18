"""
User Model
==========
Represents authenticated users in the FlowGrid platform.

User Roles:
-----------
- ADMIN: Global administrative management.
- MANAGER: Warehouse operations and shipment dispatch.
- DRIVER: Field driver linked to shipments.
- VIEWER: Read-only access for stakeholders and tracking.
"""

from datetime import datetime
import enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver


class UserRole(str, enum.Enum):
    """
    Allowed user roles for FlowGrid Role-Based Access Control (RBAC).
    Inherits from `str` so values serialize cleanly as strings.
    """
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DRIVER = "DRIVER"
    VIEWER = "VIEWER"


class User(Base):
    """
    SQLAlchemy ORM model for the `users` table.
    """
    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core user attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=True),
        default=UserRole.VIEWER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Audit Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    # One-to-one relationship with Driver profile (if user has role DRIVER)
    driver: Mapped[Optional["Driver"]] = relationship(
        "Driver",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role.value}'>"
