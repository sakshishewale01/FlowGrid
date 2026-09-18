"""
Driver Model
============
Represents field logistics drivers linked to user accounts for authentication and mobile dispatch.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Driver(Base):
    """
    SQLAlchemy ORM model for the `drivers` table.
    Extends a User account (with role DRIVER) with operational logistics credentials.
    """
    __tablename__ = "drivers"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # One-to-one link to Users table
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Driver credentials and status
    license_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(25), nullable=False)
    availability_status: Mapped[str] = mapped_column(
        String(20),
        default="AVAILABLE",
        nullable=False,
    )  # e.g., AVAILABLE, ON_DUTY, IN_TRANSIT, OFF_DUTY

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
    user: Mapped["User"] = relationship("User", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver id={self.id} license='{self.license_number}' status='{self.availability_status}'>"
