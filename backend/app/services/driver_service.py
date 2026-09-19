"""
Driver Service
==============
Business logic layer managing driver profiles, user associations,
license uniqueness validation, and repository calls.
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.user import User
from app.repositories.driver_repository import driver_repository
from app.schemas.driver import DriverCreate, DriverUpdate


class DriverService:
    """
    Business service for driver operations.
    """

    def __init__(self, repository=driver_repository):
        self.repository = repository

    def create_driver(self, db: Session, payload: DriverCreate) -> Driver:
        """
        Validates user account eligibility and license uniqueness before creating
        a new driver profile.
        """
        # 1. Verify User exists and is active
        user = db.get(User, payload.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {payload.user_id} does not exist",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User account '{user.email}' (ID {payload.user_id}) is deactivated",
            )

        # 2. Check if user already has an assigned driver profile
        existing_profile = self.repository.get_by_user_id(db, payload.user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {payload.user_id} is already linked to an existing driver profile",
            )

        # 3. Check for duplicate license number
        normalized_license = payload.license_number.strip().upper()
        conflict_license = self.repository.get_by_license_number(db, normalized_license)
        if conflict_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A driver with license number '{normalized_license}' already exists",
            )

        # 4. Create and persist Driver
        driver = Driver(
            user_id=payload.user_id,
            license_number=normalized_license,
            phone_number=payload.phone_number.strip(),
            availability_status=payload.availability_status.strip().upper(),
        )
        return self.repository.create(db, driver)

    def get_driver(self, db: Session, driver_id: int) -> Driver:
        """
        Retrieves a driver by ID or raises HTTP 404 if not found.
        """
        driver = self.repository.get_by_id(db, driver_id)
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver with ID {driver_id} was not found",
            )
        return driver

    def list_drivers(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        availability_status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Driver]:
        """
        Retrieves a paginated list of drivers with optional availability and active filters.
        """
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            availability_status=availability_status,
            is_active=is_active,
        )

    def update_driver(
        self,
        db: Session,
        driver_id: int,
        payload: DriverUpdate,
    ) -> Driver:
        """
        Updates an existing driver profile, validating license uniqueness if modified.
        Raises HTTP 404 if not found.
        """
        driver = self.get_driver(db, driver_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Validate license uniqueness if changed
        if "license_number" in update_data and update_data["license_number"] is not None:
            new_license = update_data["license_number"].strip().upper()
            if new_license != driver.license_number.strip().upper():
                conflict = self.repository.get_by_license_number(db, new_license)
                if conflict and conflict.id != driver_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A driver with license number '{new_license}' already exists",
                    )
            update_data["license_number"] = new_license

        if "phone_number" in update_data and update_data["phone_number"] is not None:
            update_data["phone_number"] = update_data["phone_number"].strip()

        if "availability_status" in update_data and update_data["availability_status"] is not None:
            update_data["availability_status"] = update_data["availability_status"].strip().upper()

        if update_data:
            return self.repository.update(db, driver, update_data)
        return driver

    def delete_driver(self, db: Session, driver_id: int) -> Dict[str, Any]:
        """
        Permanently deletes a driver profile from the database.
        Raises HTTP 404 if not found.
        """
        driver = self.get_driver(db, driver_id)
        self.repository.delete(db, driver)
        return {
            "message": f"Driver profile with ID {driver_id} was deleted successfully",
            "id": driver_id,
        }


driver_service = DriverService()
