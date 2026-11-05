"""
Proof of Delivery API tests.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from .test_shipments import SAMPLE_SHIPMENT
from .test_shipments import TestingSessionLocal, test_engine


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


def _get_auth_headers(client, email, role):
    password = "SecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": f"{role.capitalize()} User",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return _get_auth_headers(client, "admin_pod@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return _get_auth_headers(client, "manager_pod@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return _get_auth_headers(client, "driver_pod@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return _get_auth_headers(client, "viewer_pod@flowgrid.io", "VIEWER")


def _create_driver_profile(client, admin_headers, driver_headers):
    user = client.get("/api/v1/auth/me", headers=driver_headers).json()
    response = client.post(
        "/api/v1/drivers",
        headers=admin_headers,
        json={
            "user_id": user["id"],
            "license_number": "DL-POD-2026",
            "phone_number": "+1-555-0101",
            "availability_status": "ON_DUTY",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _create_out_for_delivery_shipment(client, admin_headers, driver_id=None):
    payload = dict(SAMPLE_SHIPMENT)
    if driver_id:
        payload["assigned_driver_id"] = driver_id
    shipment = client.post(
        "/api/v1/shipments",
        json=payload,
        headers=admin_headers,
    ).json()
    for next_status in ("CONFIRMED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"):
        response = client.patch(
            f"/api/v1/shipments/{shipment['id']}/status",
            json={"status": next_status},
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK
    return shipment


def test_assigned_driver_can_confirm_delivery_and_manager_can_review(
    client,
    admin_headers,
    manager_headers,
    driver_headers,
):
    driver = _create_driver_profile(client, admin_headers, driver_headers)
    shipment = _create_out_for_delivery_shipment(
        client,
        admin_headers,
        driver_id=driver["id"],
    )
    delivered_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    response = client.post(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=driver_headers,
        json={
            "recipient_name": "  Alex Recipient  ",
            "delivered_at": delivered_at.isoformat(),
            "delivery_notes": "Left with receiving desk",
            "evidence_metadata": {"reference": "POD-2026-001"},
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    confirmation = response.json()
    assert confirmation["recipient_name"] == "Alex Recipient"
    assert confirmation["evidence_metadata"] == {"reference": "POD-2026-001"}

    shipment_response = client.get(
        f"/api/v1/shipments/{shipment['id']}",
        headers=manager_headers,
    )
    assert shipment_response.status_code == status.HTTP_200_OK
    assert shipment_response.json()["status"] == "DELIVERED"
    assert shipment_response.json()["delivered_at"].startswith(
        delivered_at.replace(tzinfo=None).isoformat()
    )

    review = client.get(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=manager_headers,
    )
    assert review.status_code == status.HTTP_200_OK
    assert review.json()["submitted_by_user_id"] == driver["user_id"]

    history = client.get(
        "/api/v1/shipments/delivery-confirmations/history",
        headers=manager_headers,
    )
    assert history.status_code == status.HTTP_200_OK
    assert any(item["shipment_id"] == shipment["id"] for item in history.json())


def test_delivery_confirmation_rejects_unauthorized_driver_and_invalid_input(
    client,
    admin_headers,
    driver_headers,
    viewer_headers,
):
    driver = _create_driver_profile(client, admin_headers, driver_headers)
    shipment = _create_out_for_delivery_shipment(
        client,
        admin_headers,
        driver_id=driver["id"],
    )
    payload = {
        "recipient_name": "Recipient",
        "delivered_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    }

    viewer_response = client.post(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=viewer_headers,
        json=payload,
    )
    assert viewer_response.status_code == status.HTTP_403_FORBIDDEN

    invalid_response = client.post(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=driver_headers,
        json={
            **payload,
            "delivered_at": "2026-11-05T15:00:00",
        },
    )
    assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delivery_confirmation_prevents_duplicates_and_invalid_lifecycle(
    client,
    admin_headers,
    manager_headers,
    driver_headers,
):
    driver = _create_driver_profile(client, admin_headers, driver_headers)
    shipment = _create_out_for_delivery_shipment(
        client,
        admin_headers,
        driver_id=driver["id"],
    )
    payload = {
        "recipient_name": "Recipient",
        "delivered_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    }

    first = client.post(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=manager_headers,
        json=payload,
    )
    assert first.status_code == status.HTTP_201_CREATED

    duplicate = client.post(
        f"/api/v1/shipments/{shipment['id']}/delivery-confirmation",
        headers=driver_headers,
        json=payload,
    )
    assert duplicate.status_code == status.HTTP_409_CONFLICT

    not_ready_shipment = client.post(
        "/api/v1/shipments",
        json=SAMPLE_SHIPMENT,
        headers=admin_headers,
    ).json()
    not_ready = client.post(
        f"/api/v1/shipments/{not_ready_shipment['id']}/delivery-confirmation",
        headers=manager_headers,
        json=payload,
    )
    assert not_ready.status_code == status.HTTP_400_BAD_REQUEST


def test_managers_can_find_delivered_shipments_without_confirmation(
    client,
    admin_headers,
    manager_headers,
):
    shipment = client.post(
        "/api/v1/shipments",
        json=SAMPLE_SHIPMENT,
        headers=admin_headers,
    ).json()
    for next_status in ("CONFIRMED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"):
        response = client.patch(
            f"/api/v1/shipments/{shipment['id']}/status",
            json={"status": next_status},
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    missing = client.get(
        "/api/v1/shipments/delivery-confirmations/missing",
        headers=manager_headers,
    )
    assert missing.status_code == status.HTTP_200_OK
    assert any(item["id"] == shipment["id"] for item in missing.json())
