"""Focused tests for Phase 3 maintenance, recommendation, forecast, and reports."""

import csv
import io
from datetime import date, timedelta

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


def test_maintenance_tracks_service_dates_updates_and_due_alerts(client):
    headers = auth_headers(client)
    vehicle = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"registration_number": "P3-002", "vehicle_type": "Van", "capacity": 1000},
    ).json()
    created = client.post(
        f"/api/v1/vehicles/{vehicle['id']}/maintenance",
        headers=headers,
        json={
            "service_type": "Oil change",
            "service_date": "2026-10-01",
            "scheduled_date": "2026-10-15",
            "next_service_due_date": "2026-11-15",
        },
    )
    assert created.status_code == 201
    record_id = created.json()["id"]
    assert created.json()["next_service_due_date"] == "2026-11-15"

    updated = client.patch(
        f"/api/v1/vehicles/maintenance/{record_id}",
        headers=headers,
        json={"status": "COMPLETED", "completed_at": "2026-10-15T12:00:00Z"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "COMPLETED"

    due_date = date.today() + timedelta(days=5)
    pending = client.post(
        f"/api/v1/vehicles/{vehicle['id']}/maintenance",
        headers=headers,
        json={
            "service_type": "Tire rotation",
            "scheduled_date": str(date.today()),
            "next_service_due_date": str(due_date),
        },
    )
    assert pending.status_code == 201
    upcoming = client.get("/api/v1/vehicles/maintenance/due?days=365", headers=headers)
    assert upcoming.status_code == 200
    assert all(item["status"] not in {"COMPLETED", "CANCELLED"} for item in upcoming.json())
    assert upcoming.json()[0]["due_date"] == str(due_date)


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


def test_route_recommendation_capacity_and_approval_are_authorized(client):
    headers = auth_headers(client)
    vehicle = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"registration_number": "P3-ROUTE-VEH", "vehicle_type": "Van", "capacity": 1000},
    ).json()
    route = client.post(
        "/api/v1/routes",
        headers=headers,
        json={"name": "P3 Approved Corridor", "origin": "Chicago", "destination": "Detroit", "estimated_distance": 280, "estimated_duration": 5},
    ).json()
    shipment = client.post(
        "/api/v1/shipments",
        headers=headers,
        json={
            "tracking_number": "FG-P3-ROUTE-001",
            "destination_address": "1 Detroit Ave",
            "destination_city": "Detroit",
            "destination_state": "MI",
            "destination_postal_code": "48201",
            "total_weight_kg": 500,
        },
    ).json()
    recommendation = client.post(
        "/api/v1/routes/recommendations",
        headers=headers,
        json={"origin": "Chicago", "destination": "Detroit", "shipment_id": shipment["id"]},
    )
    assert recommendation.status_code == 200
    assert recommendation.json()["recommendations"][0]["capacity_feasible"] is True
    assert recommendation.json()["recommendations"][0]["shipment_id"] == shipment["id"]

    viewer_headers = auth_headers(client, "VIEWER")
    forbidden = client.post(
        f"/api/v1/routes/recommendations/{route['id']}/approve",
        headers=viewer_headers,
        json={"shipment_id": shipment["id"], "vehicle_id": vehicle["id"]},
    )
    assert forbidden.status_code == 403

    approved = client.post(
        f"/api/v1/routes/recommendations/{route['id']}/approve",
        headers=headers,
        json={"shipment_id": shipment["id"], "vehicle_id": vehicle["id"]},
    )
    assert approved.status_code == 200
    assert approved.json()["vehicle_id"] == vehicle["id"]
    assigned = client.get(f"/api/v1/routes/{route['id']}/shipments", headers=headers)
    assert assigned.status_code == 200
    assert assigned.json()[0]["id"] == shipment["id"]


def test_route_recommendation_rejects_insufficient_vehicle_capacity(client):
    headers = auth_headers(client)
    client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"registration_number": "P3-ROUTE-SMALL", "vehicle_type": "Van", "capacity": 100},
    )
    client.post(
        "/api/v1/routes",
        headers=headers,
        json={"name": "P3 Capacity Corridor", "origin": "Chicago", "destination": "Detroit"},
    )
    response = client.post(
        "/api/v1/routes/recommendations",
        headers=headers,
        json={"origin": "Chicago", "destination": "Detroit", "shipment_weight_kg": 500},
    )
    assert response.status_code == 200
    assert response.json()["recommendations"][0]["capacity_feasible"] is False
    assert "capacity" in " ".join(response.json()["recommendations"][0]["constraints"]).lower()


def test_route_recommendation_rejects_missing_corridor_input(client):
    headers = auth_headers(client)
    response = client.post("/api/v1/routes/recommendations", headers=headers, json={})
    assert response.status_code == 422


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


def test_inventory_forecast_uses_recorded_movements_and_recommendations_are_protected(client):
    headers = auth_headers(client)
    warehouse = client.post(
        "/api/v1/warehouses",
        headers=headers,
        json={"name": "P3 Forecast Hub", "location": "Chicago", "address": "2 Main", "capacity": 1000},
    ).json()
    product = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "P3 Forecast Product", "sku": "P3-FORECAST", "unit_price": 1},
    ).json()
    inventory = client.post(
        "/api/v1/inventory",
        headers=headers,
        json={"warehouse_id": warehouse["id"], "product_id": product["id"], "quantity": 100, "reorder_level": 20},
    ).json()
    for quantity in (90, 80, 70):
        response = client.patch(
            f"/api/v1/inventory/{inventory['id']}",
            headers=headers,
            json={"quantity": quantity},
        )
        assert response.status_code == 200

    forecast = client.get(f"/api/v1/inventory/{inventory['id']}/forecast?horizon_days=30", headers=headers)
    assert forecast.status_code == 200
    assert forecast.json()["data_sufficiency"] == "sufficient"
    assert forecast.json()["average_daily_demand"] > 0
    assert forecast.json()["movement_count"] >= 4
    movements = client.get(f"/api/v1/inventory/{inventory['id']}/movements", headers=headers)
    assert movements.status_code == 200
    assert len(movements.json()) >= 4

    recommendations = client.get("/api/v1/inventory/recommendations?horizon_days=220", headers=headers)
    assert recommendations.status_code == 200
    recommendation = next(item for item in recommendations.json() if item["inventory_id"] == inventory["id"])
    assert recommendation["recommendation_status"] == "REORDER"

    viewer_headers = auth_headers(client, "VIEWER")
    forbidden = client.get("/api/v1/inventory/recommendations", headers=viewer_headers)
    assert forbidden.status_code == 403
