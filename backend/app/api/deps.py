"""
FastAPI Request Dependencies
===========================
Reusable dependency functions for database sessions, JWT authentication,
and Role-Based Access Control (RBAC).
"""

from typing import Optional, Sequence, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# Re-export get_db so api handlers can import all common dependencies from app.api.deps
__all__ = ["get_db", "get_current_user", "require_roles", "security_scheme"]

# HTTP Bearer security scheme for OpenAPI documentation and header extraction.
# auto_error=False allows us to return custom 401 UNAUTHORIZED responses with
# standard WWW-Authenticate headers rather than generic errors.
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and validates the JWT Bearer token from the Authorization header,
    retrieves the active user from the database, and returns the User model instance.

    Raises:
        HTTPException (401 UNAUTHORIZED): If the token is missing, invalid, expired,
            or the user does not exist.
        HTTPException (400 BAD REQUEST): If the user exists but is deactivated.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_raw: Optional[str] = payload.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identification encoded in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token was not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated",
        )

    return user


def require_roles(allowed_roles: Union[Sequence[UserRole], UserRole]):
    """
    Role-Based Access Control (RBAC) dependency factory.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
        def admin_endpoint(): ...

        or to access the user:
        @router.get("/manager-panel")
        def manager_endpoint(current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))): ...

    Raises:
        HTTPException (403 FORBIDDEN): If the authenticated user's role is not in allowed_roles.
    """
    if isinstance(allowed_roles, UserRole):
        permitted_roles = [allowed_roles]
    else:
        permitted_roles = list(allowed_roles)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in permitted_roles:
            role_names = [r.value if isinstance(r, UserRole) else str(r) for r in permitted_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: action requires one of the following roles: {', '.join(role_names)}",
            )
        return current_user

    return role_checker
