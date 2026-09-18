"""
FlowGrid - Health Check Tests
=============================
Validates that /health, /health/db, and root endpoints return expected status
codes and payload structures.
"""

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
import app.main as main_module

client = TestClient(fastapi_app)


def test_health_check_returns_200():
    """
    Ensure GET /health responds with HTTP 200 OK and
    {"status": "healthy", "application": "FlowGrid"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "application": "FlowGrid",
    }


def test_database_health_check_connected(monkeypatch):
    """
    Verify /health/db returns connected status when database test succeeds.
    """
    monkeypatch.setattr(
        main_module,
        "check_db_connection",
        lambda: (True, "Database connection successful"),
    )
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["database_connected"] is True
    assert "successful" in data["detail"]


def test_database_health_check_disconnected(monkeypatch):
    """
    Verify /health/db returns disconnected status safely without raising a 500 error
    when PostgreSQL is offline or unreachable.
    """
    monkeypatch.setattr(
        main_module,
        "check_db_connection",
        lambda: (False, "Connection refused at localhost:5432"),
    )
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disconnected"
    assert data["database_connected"] is False
    assert "refused" in data["detail"]


def test_root_endpoint_returns_200():
    """
    Ensure GET / responds with HTTP 200 OK and contains application metadata.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "FlowGrid"
    assert "version" in data
