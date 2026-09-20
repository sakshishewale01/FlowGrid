"""
FlowGrid - Security Hardening & Documentation Tests (Phase 13)
============================================================
Comprehensive test suite validating:
- Security hardening:
  * Rejection of invalid, tampered, or malformed JWT tokens (HTTP 401).
  * Rejection of expired JWT tokens (HTTP 401).
  * Enforcement of WWW-Authenticate headers on 401 Unauthorized responses.
  * Injection of HTTP security headers (X-Content-Type-Options, X-Frame-Options).
  * CORS origin handling for authorized clients.
- Error handling & exception masking:
  * Global exception handling masking internal database errors (HTTP 500) without trace leakage.
  * Generic runtime error masking (HTTP 500) without trace leakage.
- OpenAPI & Interactive Documentation:
  * Swagger UI (/docs) returns HTTP 200 and HTML.
  * ReDoc (/redoc) returns HTTP 200 and HTML.
  * OpenAPI schema (/openapi.json) returns HTTP 200 with complete module tags.
- Logging and Health Probes:
  * /health and /health/db probe functionality.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. JWT Security & Expiration Tests
# ==============================================================================

def test_jwt_invalid_token_rejected():
    """Tampered or garbage JWT tokens are rejected with 401."""
    res = client.get(
        "/api/v1/warehouses",
        headers={"Authorization": "Bearer invalid_garbage_token.1234.5678"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid or expired" in res.json()["detail"].lower()
    assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_jwt_tampered_signature_rejected():
    """A token signed with an invalid secret is rejected."""
    tampered_token = jwt.encode(
        {"sub": "1", "role": "ADMIN", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "iat": datetime.now(timezone.utc)},
        "wrong_fake_secret_key_1234567890!",
        algorithm="HS256",
    )
    res = client.get(
        "/api/v1/warehouses",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid or expired" in res.json()["detail"].lower()


def test_jwt_expired_token_rejected():
    """Expired JWT token is strictly rejected with 401."""
    expired_token = create_access_token(
        subject=1,
        role="ADMIN",
        expires_delta=timedelta(seconds=-3600),  # expired 1 hour ago
    )
    res = client.get(
        "/api/v1/warehouses",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid or expired" in res.json()["detail"].lower()


def test_missing_auth_header_rejected():
    """Requests without Authorization header are rejected with 401."""
    res = client.get("/api/v1/warehouses")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "credentials were not provided" in res.json()["detail"].lower()


# ==============================================================================
# 2. HTTP Security Headers & CORS Tests
# ==============================================================================

def test_security_headers_present():
    """Verifies that security hardening headers are injected into HTTP responses."""
    res = client.get("/health")
    assert res.status_code == status.HTTP_200_OK
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Process-Time-Ms" in res.headers


def test_cors_allowed_origin():
    """Verifies CORS headers for allowed origins."""
    origin = "http://localhost:5173"
    res = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.headers.get("access-control-allow-origin") == origin
    assert res.headers.get("access-control-allow-credentials") == "true"


# ==============================================================================
# 3. OpenAPI Documentation Tests
# ==============================================================================

def test_swagger_ui_available():
    """Verifies that Swagger UI endpoint /docs returns 200 and HTML content."""
    res = client.get("/docs")
    assert res.status_code == status.HTTP_200_OK
    assert "text/html" in res.headers["content-type"]
    assert "Swagger UI" in res.text or "swagger" in res.text.lower()


def test_redoc_available():
    """Verifies that ReDoc endpoint /redoc returns 200 and HTML content."""
    res = client.get("/redoc")
    assert res.status_code == status.HTTP_200_OK
    assert "text/html" in res.headers["content-type"]
    assert "ReDoc" in res.text or "redoc" in res.text.lower()


def test_openapi_json_schema_valid():
    """Verifies that /openapi.json contains comprehensive metadata and tags."""
    res = client.get("/openapi.json")
    assert res.status_code == status.HTTP_200_OK
    schema = res.json()
    assert schema["info"]["title"] == "FlowGrid API"
    assert "paths" in schema
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/warehouses" in schema["paths"]
    assert "/api/v1/shipments" in schema["paths"]
    assert "/api/v1/routes" in schema["paths"]
    assert "/api/v1/analytics/overview" in schema["paths"]
    assert "/health" in schema["paths"]

    # Verify tags exist
    tag_names = [t["name"] for t in schema.get("tags", [])]
    assert "Authentication" in tag_names
    assert "Warehouses" in tag_names
    assert "Shipments" in tag_names
    assert "Routes" in tag_names
    assert "Analytics" in tag_names


# ==============================================================================
# 4. Error Handling & Data Leakage Prevention Tests
# ==============================================================================

def test_global_database_error_handler_masks_internals():
    """Unhandled database exceptions return a sanitized 500 without stack trace leakage."""
    with patch(
        "app.api.v1.endpoints.auth.select",
        side_effect=OperationalError(
            "connection string with postgres://secret_user:secret_pw@host:5432",
            params=None,
            orig=Exception("Raw DB Error"),
        ),
    ):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "test@flowgrid.io", "password": "Password123!"},
        )
        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = res.json()
        assert "database error occurred" in data["detail"].lower()
        # Ensure password or connection string is not leaked in response
        assert "secret_pw" not in res.text
        assert "secret_user" not in res.text
        assert "Traceback" not in res.text


def test_generic_exception_handler_masks_internals():
    """Unhandled runtime exceptions return a sanitized 500 without stack trace leakage."""
    with patch(
        "app.api.v1.endpoints.auth.select",
        side_effect=RuntimeError("Critical unexpected bug in /var/log/secret_file.py"),
    ):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "test@flowgrid.io", "password": "Password123!"},
        )
        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = res.json()
        assert "unexpected internal server error" in data["detail"].lower()
        assert "secret_file" not in res.text
        assert "Traceback" not in res.text
