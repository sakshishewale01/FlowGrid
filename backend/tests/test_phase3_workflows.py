"""Focused tests for Phase 3 maintenance, recommendation, forecast, and reports."""

import csv
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app


engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_headers(client: TestClient, role: str = "MANAGER") -> dict:
    email = f"phase3-{role.lower()}@flowgrid.io"
    password = "SecurePassword2026!"
    client.post("/api/v1/auth/register", json={"name": role, "email": email, "password": password, "role": role})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_maintenance_schedule_and_history_are_role_protected(client):
    headers = auth_headers(client)
    vehicle = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"registration_number": "P3-001", "vehicle_type": "Van", "capacity": 1000},
    ).json()
    created = client.post(
        f"/api/v1/vehicles/{vehicle['id']}/maintenance",
        headers=headers,
        json={"service_type": "Brake inspection", "scheduled_date": "2026-12-01"},
    )
    assert created.status_code == 201
    assert client.get(f"/api/v1/vehicles/{vehicle['id']}/maintenance", headers=headers).json()[0]["status"] == "SCHEDULED"

    viewer_headers = auth_headers(client, "VIEWER")
    forbidden = client.post(
        f"/api/v1/vehicles/{vehicle['id']}/maintenance",
        headers=viewer_headers,
        json={"service_type": "Oil change", "scheduled_date": "2026-12-02"},
    )
    assert forbidden.status_code == 403


def test_route_recommendation_is_explainable_and_estimated(client):
    headers = auth_headers(client)
    client.post(
        "/api/v1/routes",
        headers=headers,
        json={"name": "P3 Corridor", "origin": "Chicago", "destination": "Detroit", "estimated_distance": 280, "estimated_duration": 5},
    )
    response = client.post(
        "/api/v1/routes/recommendations",
        headers=headers,
        json={"origin": "Chicago", "destination": "Detroit"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["estimated_only"] is True
    assert body["recommendations"][0]["explanation"]
    assert "traffic" in " ".join(body["limitations"]).lower()


def test_inventory_forecast_discloses_insufficient_history_and_report_is_csv(client):
    headers = auth_headers(client)
    warehouse = client.post(
        "/api/v1/warehouses",
        headers=headers,
        json={"name": "P3 Hub", "location": "Chicago", "address": "1 Main", "capacity": 1000},
    ).json()
    product = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "P3 Product", "sku": "P3-SKU", "unit_price": 1},
    ).json()
    inventory = client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"warehouse_id": warehouse["id"], "product_id": product["id"], "quantity": 4, "reorder_level": 10},
    ).json()
    forecast = client.get(f"/api/v1/inventory/{inventory['id']}/forecast", headers=headers)
    assert forecast.status_code == 200
    assert forecast.json()["data_sufficiency"] == "insufficient"
    assert forecast.json()["reorder_recommended"] is True

    report = client.get("/api/v1/analytics/reports.csv?report_type=inventory", headers=headers)
    assert report.status_code == 200
    rows = list(csv.reader(io.StringIO(report.text)))
    assert rows[0][0] == "inventory_id"
    assert report.headers["content-type"].startswith("text/csv")
