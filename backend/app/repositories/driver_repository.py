"""
Driver Repository
=================
Encapsulates all database queries and persistence operations for the Driver model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.driver import Driver
from app.models.user import User


class DriverRepository:
    """
    Data access layer for Driver profiles.
    """

    @staticmethod
    def get_by_id(db: Session, driver_id: int) -> Optional[Driver]:
        """
        Retrieves a driver by primary key ID, eagerly loading the associated user.
        """
        stmt = (
            select(Driver)
            .options(joinedload(Driver.user))
            .where(Driver.id == driver_id)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[Driver]:
        """
        Retrieves a driver profile linked to a specific user ID.
        """
        stmt = select(Driver).where(Driver.user_id == user_id)
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_license_number(db: Session, license_number: str) -> Optional[Driver]:
        """
        Retrieves a driver by license number with case-insensitive match.
        """
        normalized = license_number.strip().upper()
        stmt = select(Driver).where(
            func.upper(func.trim(Driver.license_number)) == normalized
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        availability_status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Driver]:
        """
        Retrieves a paginated list of driver profiles with optional availability status
        and user active-status filtering.
        """
        stmt = select(Driver).options(joinedload(Driver.user))

        if availability_status:
            stmt = stmt.where(
                func.upper(Driver.availability_status) == availability_status.strip().upper()
            )

        if is_active is not None:
            stmt = stmt.join(Driver.user).where(User.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit).order_by(Driver.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, driver: Driver) -> Driver:
        """
        Persists a new driver profile record.
        """
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver

    @staticmethod
    def update(
        db: Session,
        driver: Driver,
        update_data: Dict[str, Any],
    ) -> Driver:
        """
        Updates fields on an existing driver profile.
        """
        for field, value in update_data.items():
            setattr(driver, field, value)
        db.commit()
        db.refresh(driver)
        return driver

    @staticmethod
    def delete(db: Session, driver: Driver) -> None:
        """
        Deletes a driver profile from the database.
        """
        db.delete(driver)
        db.commit()


driver_repository = DriverRepository()
