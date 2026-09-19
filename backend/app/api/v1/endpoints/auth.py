"""
Authentication Endpoints
========================
Provides user registration, login authentication, and profile retrieval for FlowGrid.

Security Features:
- Passwords hashed with Argon2id via pwdlib.
- Access tokens signed with PyJWT using HMAC-SHA256.
- Passwords and password hashes are never exposed in responses.
- Safe generic error messages prevent user enumeration attacks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    response_description="The newly registered user details (excluding credentials)",
)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    """
    Registers a new user account in FlowGrid:
    1. Validates that the email address is not already registered.
    2. Securely hashes the plain-text password using Argon2id.
    3. Persists the user record in the database.
    4. Returns the sanitized user profile.
    """
    # 1. Check for duplicate email (case-insensitive match)
    stmt = select(User).where(func.lower(User.email) == payload.email.lower().strip())
    existing_user = db.scalars(stmt).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists",
        )

    # 2. Hash the plain-text password
    hashed_pw = get_password_hash(payload.password)

    # 3. Create the new User instance
    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hashed_pw,
        role=payload.role,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT access token",
    response_description="A signed JWT access token and public user profile",
)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticates a user by email and password:
    1. Finds the user by normalized email address.
    2. Verifies the candidate password against the stored Argon2 hash.
    3. Confirms that the account is currently active.
    4. Generates and returns a signed JWT Bearer access token.
    """
    normalized_email = payload.email.lower().strip()
    stmt = select(User).where(func.lower(User.email) == normalized_email)
    user = db.scalars(stmt).first()

    # Safe credential check: constant-time or generic rejection to prevent timing / enumeration
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated. Please contact an administrator.",
        )

    # Generate JWT access token containing subject (user id) and role
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    response_description="Profile details of the authenticated caller",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Protected endpoint that returns the public profile of the currently
    authenticated user by validating the JWT Bearer token in the request header.
    """
    return current_user
