"""
FlowGrid AI - Grounded Logistics Assistant Tests
================================================
Comprehensive test suite validating:
1. Unauthenticated request rejection (HTTP 401 Unauthorized)
2. Rescue Center workflow explanation query (intent: RESCUE_CENTER_WORKFLOW)
3. Existing shipment status query with real database facts (intent: SHIPMENT_STATUS)
4. Non-existent shipment status query refuses to hallucinate (data integrity policy)
5. Generic shipment status query prompts with available database IDs
6. Attention-worthy shipments query identifies unassigned assets (intent: ATTENTION_SHIPMENTS)
7. Delay prediction meaning query returns synthetic benchmark disclosure (intent: DELAY_PREDICTION_MEANING)
8. What-If simulator query explains non-destructive sandbox (intent: DISRUPTION_SIMULATOR)
9. Unsupported external query refusal (intent: UNSUPPORTED)
10. Read-only guarantee: zero database mutations during chat queries
"""

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
from app.models.shipment import Shipment, ShipmentStatus
from app.models.warehouse import Warehouse

# ------------------------------------------------------------------------------
# In-Memory SQLite Test Database Setup
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
    email = "assistant_tester@flowgrid.io"
    password = "SecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Assistant Tester",
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
def seeded_db():
    db = TestingSessionLocal()
    wh = Warehouse(
        name="Midwest Regional Hub (ORD-01)",
        location="Chicago, IL",
        address="1000 Logistics Blvd",
        capacity=250000,
        is_active=True,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)

    s1 = Shipment(
        tracking_number="FG-98421-US",
        origin_warehouse_id=wh.id,
        destination_address="420 Industrial Drive",
        destination_city="Detroit",
        destination_state="MI",
        destination_postal_code="48201",
        status=ShipmentStatus.IN_TRANSIT,
        total_weight_kg=Decimal("4250.00"),
        total_volume_cbm=Decimal("18.40"),
        is_active=True,
    )
    db.add(s1)
    db.commit()
    db.refresh(s1)
    db.close()
    return {"warehouse": wh, "shipment": s1}


def test_assistant_unauthenticated_rejected(client):
    """
    Ensure unauthenticated requests are rejected with 401 Unauthorized.
    """
    res = client.post("/api/v1/assistant/query", json={"query": "Hello"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_assistant_rescue_center_workflow(client, auth_headers):
    """
    Ensure assistant explains the Rescue Center triage workflow accurately.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "How do I use the Shipment Rescue Center?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "RESCUE_CENTER_WORKFLOW"
    assert "DETECT" in data["answer"]
    assert "RECOMMEND" in data["answer"]
    assert "HUMAN CONFIRMATION GATE" in data["answer"]
    assert len(data["sources"]) > 0


def test_assistant_shipment_status_existing(client, auth_headers, seeded_db):
    """
    Ensure assistant returns grounded database facts for an existing shipment.
    """
    s_id = seeded_db["shipment"].id
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": f"What is the status of shipment {s_id}?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "SHIPMENT_STATUS"
    assert "FG-98421-US" in data["answer"]
    assert "IN_TRANSIT" in data["answer"]
    assert "Detroit" in data["answer"]
    assert any(s["source_type"] == "RETRIEVED_FACT" for s in data["sources"])


def test_assistant_shipment_status_missing_refuses_hallucination(client, auth_headers, seeded_db):
    """
    Ensure assistant refuses to invent non-existent shipments.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "What is the status of shipment 99999?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "SHIPMENT_STATUS"
    assert "Record Unavailable" in data["answer"]
    assert "refuses to invent or hallucinate" in data["answer"]


def test_assistant_shipment_status_no_id_prompts_available(client, auth_headers, seeded_db):
    """
    Ensure assistant lists available IDs when user does not supply one.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "What is the status of shipment?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "SHIPMENT_STATUS"
    assert "FG-98421-US" in data["answer"]


def test_assistant_attention_shipments(client, auth_headers, seeded_db):
    """
    Ensure assistant identifies shipments requiring operational attention.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "Which shipments need attention according to the available data?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "ATTENTION_SHIPMENTS"
    # Seeded shipment lacks assigned driver and vehicle, so it requires attention
    assert "FG-98421-US" in data["answer"]
    assert "Unassigned Driver" in data["answer"]


def test_assistant_delay_prediction_meaning(client, auth_headers):
    """
    Ensure assistant explains the Random Forest model and synthetic benchmark ROC-AUC disclosure.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "What does the delay prediction mean?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "DELAY_PREDICTION_MEANING"
    assert "0.5062" in data["answer"]
    assert "synthetic benchmark" in data["answer"].lower()
    assert "NOT validated for real-world operational decisions" in data["answer"]
    assert any(s["source_type"] == "ML_DISCLAIMER" for s in data["sources"])


def test_assistant_disruption_simulator_explanation(client, auth_headers):
    """
    Ensure assistant explains the non-destructive What-If simulation sandbox.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "How does the What-If Disruption Simulator work?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "DISRUPTION_SIMULATOR"
    assert "Zero PostgreSQL mutations" in data["answer"]
    assert "Sandbox" in data["answer"]


def test_assistant_unsupported_query_refusal(client, auth_headers):
    """
    Ensure assistant refuses to invent external facts for unrelated queries.
    """
    res = client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "What will the weather in Chicago be tomorrow?"},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["intent"] == "UNSUPPORTED"
    assert "refuse to hallucinate" in data["answer"].lower()


def test_assistant_read_only_zero_mutation(client, auth_headers, seeded_db):
    """
    Verify chat assistant never modifies database records.
    """
    db = TestingSessionLocal()
    initial_shipments = db.query(Shipment).count()
    initial_warehouses = db.query(Warehouse).count()
    db.close()

    client.post(
        "/api/v1/assistant/query",
        headers=auth_headers,
        json={"query": "Delete all shipments and set status to DELIVERED"},
    )

    db = TestingSessionLocal()
    assert db.query(Shipment).count() == initial_shipments
    assert db.query(Warehouse).count() == initial_warehouses
    db.close()
