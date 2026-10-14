"""
FlowGrid AI - Machine Learning Prediction Tests
===============================================
Comprehensive test suite validating:
1. Valid prediction requests with full date parsing
2. Valid prediction requests with explicit (month, day_of_week)
3. Unauthenticated request rejection (HTTP 401 Unauthorized)
4. Input validation errors (negative distance, missing fields) (HTTP 422)
5. Missing temporal features rejection without silent defaults (HTTP 422)
6. Missing model artifact safe failure (HTTP 503 Service Unavailable)
7. Response format verification (probability, risk band, explanation)
8. Zero database mutation verification (no rows added to PostgreSQL/SQLite)
"""

from pathlib import Path
from decimal import Decimal
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.shipment import Shipment
from app.services.ml_service import ml_delay_service

# ------------------------------------------------------------------------------
# Test Database Setup
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


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    email = "ml_test_user@flowgrid.io"
    password = "SecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "ML Tester",
            "email": email,
            "password": password,
            "role": "MANAGER",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_payload():
    return {
        "warehouse": "East Depot - Kolkata",
        "destination": "Jaipur Commerce Center",
        "transport_mode": "Mini Truck (Tata Ace class)",
        "distance_km": 1765.1,
        "supplier": "Orion Freight Co.",
        "driver": "A. Kumar",
        "dispatch_date": "2026-10-15",
    }


def test_predict_delay_valid_input_authenticated(client, auth_headers, sample_payload):
    """
    Ensure POST /api/v1/ml/predict-delay returns 200 with complete structured fields.
    """
    response = client.post(
        "/api/v1/ml/predict-delay",
        headers=auth_headers,
        json=sample_payload,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "is_delayed" in data
    assert isinstance(data["is_delayed"], bool)

    assert "delay_probability" in data
    assert 0.0 <= data["delay_probability"] <= 1.0

    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "model_version" in data
    assert "explanation" in data
    assert "Prototype notice" in data["explanation"]

    assert "features_used" in data
    assert data["features_used"]["warehouse"] == "East Depot - Kolkata"
    assert data["features_used"]["month"] == 10.0
    assert data["features_used"]["day_of_week"] == 3.0
    assert data["features_used"]["is_weekend"] == 0.0


def test_predict_delay_with_explicit_month_and_day(client, auth_headers):
    """
    Ensure request works when explicit month and day_of_week are supplied without dispatch_date.
    """
    payload = {
        "warehouse": "Central Warehouse - Pune",
        "destination": "Indore Industrial Zone",
        "transport_mode": "Reefer Truck",
        "distance_km": 664.6,
        "supplier": "Meridian Freight Pvt. Ltd.",
        "driver": "R. Yadav",
        "month": 11,
        "day_of_week": 6,  # Sunday -> is_weekend = 1.0
    }
    response = client.post(
        "/api/v1/ml/predict-delay",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["features_used"]["is_weekend"] == 1.0
    assert data["features_used"]["month"] == 11.0


def test_predict_delay_unauthenticated_rejected(client, sample_payload):
    """
    Ensure unauthenticated requests are rejected with HTTP 401 Unauthorized.
    """
    response = client.post(
        "/api/v1/ml/predict-delay",
        json=sample_payload,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_predict_delay_invalid_input_negative_distance(client, auth_headers, sample_payload):
    """
    Ensure distance <= 0 is rejected with HTTP 422 Unprocessable Entity.
    """
    sample_payload["distance_km"] = -50.0
    response = client.post(
        "/api/v1/ml/predict-delay",
        headers=auth_headers,
        json=sample_payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_predict_delay_missing_temporal_features_rejected(client, auth_headers, sample_payload):
    """
    Ensure missing both dispatch_date and month/day_of_week raises 422 rather than inventing values.
    """
    del sample_payload["dispatch_date"]
    response = client.post(
        "/api/v1/ml/predict-delay",
        headers=auth_headers,
        json=sample_payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_predict_delay_missing_model_artifact_returns_503(client, auth_headers, sample_payload, monkeypatch):
    """
    Ensure missing model artifact fails gracefully with HTTP 503 Service Unavailable.
    """
    original_path = ml_delay_service.model_path
    original_cached = ml_delay_service._cached_pipeline

    try:
        # Force cache invalidation and point to nonexistent file
        ml_delay_service._cached_pipeline = None
        ml_delay_service.model_path = Path("/nonexistent/path/to/missing_model.joblib")

        response = client.post(
            "/api/v1/ml/predict-delay",
            headers=auth_headers,
            json=sample_payload,
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "not available" in data["detail"]
    finally:
        ml_delay_service.model_path = original_path
        ml_delay_service._cached_pipeline = original_cached


def test_predict_delay_zero_database_mutations(client, auth_headers, sample_payload):
    """
    Ensure the ML inference endpoint has zero database side-effects (does not add rows to shipments table).
    """
    db = TestingSessionLocal()
    initial_shipment_count = db.query(Shipment).count()
    db.close()

    # Call predict endpoint 3 times
    for _ in range(3):
        res = client.post(
            "/api/v1/ml/predict-delay",
            headers=auth_headers,
            json=sample_payload,
        )
        assert res.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    final_shipment_count = db.query(Shipment).count()
    db.close()

    assert final_shipment_count == initial_shipment_count
