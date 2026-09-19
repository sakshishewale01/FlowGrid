"""
FlowGrid - Authentication & Role-Based Access Control Tests
============================================================
Comprehensive test suite validating:
- Password hashing & verification with pwdlib Argon2id
- JWT access token generation and decoding
- User registration (success, duplicate email, password security)
- User login (success, invalid password, unknown email)
- Protected /api/v1/auth/me endpoint (missing token, valid token)
- Role-Based Access Control (require_roles dependency)
"""

import pytest
from fastapi import APIRouter, Depends, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db, require_roles
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.base import Base
from app.main import app
from app.models.user import User, UserRole

# ------------------------------------------------------------------------------
# Test Database Setup (In-Memory SQLite with StaticPool for fast isolated tests)
# ------------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Add a test-only route to explicitly verify require_roles dependency
rbac_test_router = APIRouter(prefix="/test-rbac")


@rbac_test_router.get("/admin-only")
def admin_only_endpoint(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    return {"message": f"Welcome Admin {current_user.name}"}


@rbac_test_router.get("/manager-or-admin")
def manager_or_admin_endpoint(
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
):
    return {"message": f"Welcome {current_user.role.value} {current_user.name}"}


app.include_router(rbac_test_router)


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Creates fresh database schema before each test and cleanly drops afterwards.
    """
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Security Utilities Tests
# ------------------------------------------------------------------------------
def test_password_hashing_and_verification():
    raw_password = "FlowGridSecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    token = create_access_token(subject=42, role=UserRole.MANAGER.value)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "MANAGER"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_jwt_token():
    invalid_token = "invalid.token.structure"
    payload = decode_access_token(invalid_token)
    assert payload is None


# ------------------------------------------------------------------------------
# 2. User Registration Tests
# ------------------------------------------------------------------------------
def test_successful_registration(client):
    payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@flowgrid.io",
        "password": "SecurePassword123!",
        "role": "MANAGER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["name"] == "Sarah Connor"
    assert data["email"] == "sarah.connor@flowgrid.io"
    assert data["role"] == "MANAGER"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    # Security requirement: hashed_password MUST NEVER be present in responses
    assert "hashed_password" not in data
    assert "password" not in data


def test_duplicate_email_registration_fails(client):
    payload = {
        "name": "Marcus Wright",
        "email": "marcus@flowgrid.io",
        "password": "Password123!",
        "role": "DRIVER",
    }
    first_response = client.post("/api/v1/auth/register", json=payload)
    assert first_response.status_code == status.HTTP_201_CREATED

    # Attempt registration again with duplicate email (different casing)
    duplicate_payload = {
        "name": "Marcus Duplicate",
        "email": "MARCUS@flowgrid.io",
        "password": "OtherPassword456!",
        "role": "DRIVER",
    }
    second_response = client.post("/api/v1/auth/register", json=duplicate_payload)
    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in second_response.json()["detail"]


def test_registration_validation_error(client):
    # Invalid email format and too-short password
    payload = {
        "name": "X",
        "email": "not-an-email",
        "password": "123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 3. User Login Tests
# ------------------------------------------------------------------------------
def test_successful_login(client):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Elena Rostova",
            "email": "elena@flowgrid.io",
            "password": "LoginSecret2026!",
            "role": "ADMIN",
        },
    )

    # Login
    login_payload = {
        "email": "elena@flowgrid.io",
        "password": "LoginSecret2026!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "elena@flowgrid.io"
    assert data["user"]["role"] == "ADMIN"
    assert "hashed_password" not in data["user"]


def test_login_invalid_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "John Doe",
            "email": "john@flowgrid.io",
            "password": "CorrectPassword123!",
            "role": "VIEWER",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "john@flowgrid.io",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ghost@flowgrid.io",
            "password": "AnyPassword123!",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in response.json()["detail"]


# ------------------------------------------------------------------------------
# 4. Protected /api/v1/auth/me Endpoint Tests
# ------------------------------------------------------------------------------
def test_protected_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "credentials were not provided" in response.json()["detail"]


def test_protected_me_with_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid or expired" in response.json()["detail"]


def test_protected_me_with_valid_token(client):
    # 1. Register user
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Kyle Reese",
            "email": "kyle@flowgrid.io",
            "password": "Password789!",
            "role": "DRIVER",
        },
    )
    user_id = reg_response.json()["id"]

    # 2. Login to obtain access token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "kyle@flowgrid.io",
            "password": "Password789!",
        },
    )
    token = login_response.json()["access_token"]

    # 3. Request /api/v1/auth/me using Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK

    me_data = me_response.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "kyle@flowgrid.io"
    assert me_data["name"] == "Kyle Reese"
    assert me_data["role"] == "DRIVER"
    assert "hashed_password" not in me_data


# ------------------------------------------------------------------------------
# 5. Role-Based Access Control (require_roles) Tests
# ------------------------------------------------------------------------------
def test_rbac_admin_access_allowed(client):
    # Register ADMIN
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Super Admin",
            "email": "admin@flowgrid.io",
            "password": "AdminPassword123!",
            "role": "ADMIN",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@flowgrid.io", "password": "AdminPassword123!"},
    )
    admin_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin accessing admin-only route
    response = client.get("/test-rbac/admin-only", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "Welcome Admin" in response.json()["message"]


def test_rbac_viewer_access_denied_to_admin_route(client):
    # Register VIEWER
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Guest Viewer",
            "email": "viewer@flowgrid.io",
            "password": "ViewerPassword123!",
            "role": "VIEWER",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@flowgrid.io", "password": "ViewerPassword123!"},
    )
    viewer_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer attempting to access admin-only route -> 403 Forbidden
    response = client.get("/test-rbac/admin-only", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_rbac_manager_access_to_manager_or_admin_route(client):
    # Register MANAGER
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Warehouse Manager",
            "email": "manager@flowgrid.io",
            "password": "ManagerPassword123!",
            "role": "MANAGER",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@flowgrid.io", "password": "ManagerPassword123!"},
    )
    mgr_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {mgr_token}"}

    # Manager accessing manager-or-admin route -> 200 OK
    response = client.get("/test-rbac/manager-or-admin", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "Welcome MANAGER" in response.json()["message"]
