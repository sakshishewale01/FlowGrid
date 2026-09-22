"""
FlowGrid - AI-Ready Data Pipeline Tests (Phase 21)
=================================================
Comprehensive test suite validating:
1. Feature Extraction & Engineering from operational database records
2. Temporal Feature Extraction (hour, day of week, month, weekend)
3. Delivery Duration and Delay Target Calculations
4. Data Leakage Prevention and Detection
5. Chronological Train/Test Splitting (Preventing temporal lookahead)
6. Data Quality Checks (Timestamps, Bounds, Duplicates, Outliers)
7. CSV and JSON Dataset Exports
8. RBAC and Endpoint Security for Pipeline APIs
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import io
import csv
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
from app.models.tracking import ShipmentStatusHistory
from app.pipeline.schema import (
    FEATURE_REGISTRY,
    FeatureCategory,
    DatasetRecord,
    DataQualityReport,
)
from app.pipeline.feature_extractor import feature_extractor
from app.pipeline.feature_engineer import feature_engineer
from app.pipeline.quality_checker import quality_checker
from app.pipeline.dataset_generator import dataset_generator

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


def get_auth_headers_for_role(client: TestClient, email: str, role: str) -> dict:
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
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    return get_auth_headers_for_role(client, "admin_pipe@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_pipe@flowgrid.io", "MANAGER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_pipe@flowgrid.io", "VIEWER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_pipe@flowgrid.io", "DRIVER")


@pytest.fixture
def operational_setup(client, admin_headers):
    # Warehouse
    wh_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Chicago Logistics Terminal",
            "location": "Chicago, IL",
            "address": "400 Terminal Way, Chicago, IL 60601",
            "capacity": 10000,
            "is_active": True,
        },
        headers=admin_headers,
    )
    wh = wh_res.json()

    # Driver User
    u_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Frank Driver",
            "email": "frank_drv@flowgrid.io",
            "password": "SecurePassword2026!",
            "role": "DRIVER",
        },
    )
    u_id = u_res.json()["id"]

    # Driver Profile
    drv_res = client.post(
        "/api/v1/drivers",
        json={
            "user_id": u_id,
            "license_number": "CDL-PIPE-001",
            "phone_number": "+1-555-444-3333",
            "availability_status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    drv = drv_res.json()

    # Vehicle
    veh_res = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "TRK-PIPE-99",
            "vehicle_type": "Semi-Trailer",
            "capacity": 20000.00,
            "status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    veh = veh_res.json()

    # Route
    route_res = client.post(
        "/api/v1/routes",
        json={
            "name": "Chicago to Indianapolis Express",
            "origin": "Chicago, IL",
            "destination": "Indianapolis, IN",
            "estimated_distance": 295.50,
            "estimated_duration": 4.50,
            "status": "ACTIVE",
        },
        headers=admin_headers,
    )
    rte = route_res.json()

    return {"warehouse": wh, "driver": drv, "vehicle": veh, "route": rte}


# ==============================================================================
# 1. Feature Registry & Metadata Tests
# ==============================================================================

def test_feature_registry_definitions():
    assert len(FEATURE_REGISTRY) > 20

    raw_features = [f for f in FEATURE_REGISTRY if f.category == FeatureCategory.RAW_FEATURE]
    derived_features = [f for f in FEATURE_REGISTRY if f.category == FeatureCategory.DERIVED_FEATURE]
    target_variables = [f for f in FEATURE_REGISTRY if f.category == FeatureCategory.TARGET_VARIABLE]
    deferred_features = [f for f in FEATURE_REGISTRY if f.category == FeatureCategory.DEFERRED]

    assert len(raw_features) >= 12
    assert len(derived_features) >= 7
    assert len(target_variables) >= 3
    assert len(deferred_features) >= 3

    # Ensure all target variables specify leakage mitigation notes
    for target in target_variables:
        assert target.is_target is True
        assert target.leakage_mitigation is not None
        assert len(target.leakage_mitigation) > 10


# ==============================================================================
# 2. Feature Extraction and Engineering Tests
# ==============================================================================

def test_delivered_shipment_feature_extraction_and_engineering(
    client, admin_headers, operational_setup
):
    wh = operational_setup["warehouse"]
    drv = operational_setup["driver"]
    veh = operational_setup["vehicle"]
    rte = operational_setup["route"]

    # 1. Create shipment
    create_res = client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": wh["id"],
            "destination_address": "500 Monument Circle",
            "destination_city": "Indianapolis",
            "destination_state": "IN",
            "destination_postal_code": "46204",
            "assigned_driver_id": drv["id"],
            "assigned_vehicle_id": veh["id"],
            "total_weight_kg": 8000.00,
            "total_volume_cbm": 35.00,
            "scheduled_pickup_at": "2026-10-15T08:30:00Z",
        },
        headers=admin_headers,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    shipment_id = create_res.json()["id"]

    # Assign route
    client.post(
        f"/api/v1/routes/{rte['id']}/shipments",
        json={"shipment_id": shipment_id},
        headers=admin_headers,
    )

    # Transition through lifecycle to DELIVERED
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "CONFIRMED"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "ASSIGNED"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "PICKED_UP"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "IN_TRANSIT"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "OUT_FOR_DELIVERY"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{shipment_id}/status", json={"status": "DELIVERED"}, headers=admin_headers)

    # Extract single context
    db = TestingSessionLocal()
    try:
        ctx = feature_extractor.extract_single_shipment(db, shipment_id)
        assert ctx is not None
        assert ctx.shipment.id == shipment_id
        assert ctx.warehouse.id == wh["id"]
        assert ctx.driver.id == drv["id"]
        assert ctx.vehicle.id == veh["id"]
        assert ctx.route.id == rte["id"]

        # Engineer features
        rec = feature_engineer.transform(ctx)
        assert isinstance(rec, DatasetRecord)
        assert rec.shipment_id == shipment_id
        assert rec.cargo_weight_kg == 8000.00
        assert rec.cargo_volume_cbm == 35.00
        assert rec.has_driver_assigned == 1
        assert rec.has_vehicle_assigned == 1
        assert rec.has_route_assigned == 1
        assert rec.weight_capacity_utilization == 0.4  # 8000 / 20000
        assert rec.is_interstate == 1  # IL to IN
        assert rec.scheduled_pickup_hour == 8
        assert rec.scheduled_pickup_month == 10
        assert rec.shipment_status == "DELIVERED"
        assert rec.actual_pickup_timestamp is not None
        assert rec.actual_delivery_timestamp is not None
        assert rec.actual_duration_hours is not None
        assert rec.is_delayed in (0, 1)
    finally:
        db.close()


# ==============================================================================
# 3. Data Leakage Prevention Tests
# ==============================================================================

def test_undelivered_shipment_target_isolation(client, admin_headers, operational_setup):
    wh = operational_setup["warehouse"]

    # Create active shipment in CREATED status
    create_res = client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": wh["id"],
            "destination_address": "100 South St",
            "destination_city": "Chicago",
            "destination_state": "IL",
            "destination_postal_code": "60601",
            "total_weight_kg": 1500.00,
        },
        headers=admin_headers,
    )
    shipment_id = create_res.json()["id"]

    db = TestingSessionLocal()
    try:
        ctx = feature_extractor.extract_single_shipment(db, shipment_id)
        assert ctx is not None
        rec = feature_engineer.transform(ctx)

        # TARGETS MUST BE NONE FOR UNDELIVERED SHIPMENTS (Prevent data leakage)
        assert rec.shipment_status == "CREATED"
        assert rec.actual_duration_hours is None
        assert rec.is_delayed is None
        assert rec.delay_hours is None

        # Quality audit must confirm zero leakage
        report = quality_checker.audit([rec])
        assert report.leakage_risk_detected is False
    finally:
        db.close()


def test_leakage_risk_detection():
    # Artificially populate target variables on an in-transit shipment
    leaky_record = DatasetRecord(
        shipment_id=999,
        tracking_number="FG-LEAK-01",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="Peoria",
        destination_state="IL",
        destination_postal_code="61602",
        shipment_status="IN_TRANSIT",  # UNDELIVERED!
        actual_duration_hours=5.2,     # LEAKED TARGET!
        is_delayed=1,                  # LEAKED TARGET!
    )

    report = quality_checker.audit([leaky_record])
    assert report.leakage_risk_detected is True
    assert report.is_valid_for_training is False
    assert any(i.issue_type == "LEAKAGE_RISK" for i in report.issues)


# ==============================================================================
# 4. Chronological Splitting Tests
# ==============================================================================

def test_chronological_splitting_preserves_temporal_order():
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    records = []

    for i in range(10):
        t = (base_time + timedelta(days=i)).isoformat()
        records.append(
            DatasetRecord(
                shipment_id=i + 1,
                tracking_number=f"FG-SPLIT-{i}",
                created_timestamp=t,
                scheduled_pickup_timestamp=t,
                destination_city="City",
                destination_state="State",
                destination_postal_code="12345",
                shipment_status="DELIVERED",
                actual_duration_hours=4.0,
                is_delayed=0,
            )
        )

    # Split 80 / 20
    train_set, test_set = dataset_generator.split_chronologically(records, train_ratio=0.8)
    assert len(train_set) == 8
    assert len(test_set) == 2

    # Check that train set records strictly precede test set records
    max_train_time = max(r.scheduled_pickup_timestamp for r in train_set)
    min_test_time = min(r.scheduled_pickup_timestamp for r in test_set)
    assert max_train_time <= min_test_time

    # Invalid train ratio raises ValueError
    with pytest.raises(ValueError):
        dataset_generator.split_chronologically(records, train_ratio=1.5)


# ==============================================================================
# 5. Data Quality Auditing Tests
# ==============================================================================

def test_data_quality_anomalies_detection():
    # 1. Invalid negative weight
    r_bad_weight = DatasetRecord(
        shipment_id=1,
        tracking_number="FG-BAD-01",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="City",
        destination_state="State",
        destination_postal_code="12345",
        cargo_weight_kg=-50.0,
        shipment_status="CREATED",
    )

    # 2. Inverted timestamps (delivery before pickup)
    r_inverted = DatasetRecord(
        shipment_id=2,
        tracking_number="FG-BAD-02",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="City",
        destination_state="State",
        destination_postal_code="12345",
        shipment_status="DELIVERED",
        actual_pickup_timestamp="2026-09-02T15:00:00Z",
        actual_delivery_timestamp="2026-09-02T10:00:00Z",  # Earlier than pickup!
    )

    # 3. Duplicate shipment IDs
    r_dup1 = DatasetRecord(
        shipment_id=3,
        tracking_number="FG-DUP-01",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="City",
        destination_state="State",
        destination_postal_code="12345",
        shipment_status="CREATED",
    )
    r_dup2 = DatasetRecord(
        shipment_id=3,
        tracking_number="FG-DUP-01",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="City",
        destination_state="State",
        destination_postal_code="12345",
        shipment_status="CREATED",
    )

    report = quality_checker.audit([r_bad_weight, r_inverted, r_dup1, r_dup2])
    assert report.total_records == 4
    assert report.clean_records == 0
    assert report.is_valid_for_training is False
    issue_types = {i.issue_type for i in report.issues}
    assert "INVALID_NUMERICAL_VALUE" in issue_types
    assert "INVALID_TIMESTAMP" in issue_types
    assert "DUPLICATE_RECORD" in issue_types


# ==============================================================================
# 6. Serialization & Export Tests
# ==============================================================================

def test_csv_and_json_export_operations():
    rec = DatasetRecord(
        shipment_id=101,
        tracking_number="FG-EXP-01",
        created_timestamp="2026-09-01T10:00:00Z",
        destination_city="Dallas",
        destination_state="TX",
        destination_postal_code="75001",
        cargo_weight_kg=2500.0,
        cargo_volume_cbm=12.0,
        shipment_status="DELIVERED",
        actual_duration_hours=6.5,
        is_delayed=0,
    )

    # CSV export
    csv_str = dataset_generator.export_to_csv([rec])
    assert "shipment_id" in csv_str
    assert "FG-EXP-01" in csv_str
    assert "Dallas" in csv_str

    # JSON export
    json_str = dataset_generator.export_to_json([rec])
    assert "FG-EXP-01" in json_str

    # Empty export
    empty_csv = dataset_generator.export_to_csv([])
    assert "shipment_id" in empty_csv


# ==============================================================================
# 7. Pipeline API Endpoint & RBAC Tests
# ==============================================================================

def test_pipeline_schema_endpoint(client, admin_headers, viewer_headers):
    # Admin access allowed
    res_admin = client.get("/api/v1/pipeline/schema", headers=admin_headers)
    assert res_admin.status_code == status.HTTP_200_OK
    assert len(res_admin.json()) >= 20

    # Viewer access rejected with 403
    res_viewer = client.get("/api/v1/pipeline/schema", headers=viewer_headers)
    assert res_viewer.status_code == status.HTTP_403_FORBIDDEN

    # Unauthenticated rejected with 401
    res_unauth = client.get("/api/v1/pipeline/schema")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED


def test_pipeline_dataset_and_quality_report_endpoints(
    client, admin_headers, operational_setup
):
    wh = operational_setup["warehouse"]

    # Create a test shipment
    client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": wh["id"],
            "destination_address": "800 Elm St",
            "destination_city": "Dallas",
            "destination_state": "TX",
            "destination_postal_code": "75001",
            "total_weight_kg": 1200.00,
        },
        headers=admin_headers,
    )

    # Quality Report endpoint
    res_qual = client.get("/api/v1/pipeline/quality-report", headers=admin_headers)
    assert res_qual.status_code == status.HTTP_200_OK
    data_qual = res_qual.json()
    assert data_qual["total_records"] >= 1

    # Dataset endpoint
    res_data = client.get("/api/v1/pipeline/dataset", headers=admin_headers)
    assert res_data.status_code == status.HTTP_200_OK
    data = res_data.json()
    assert data["total_records"] >= 1
    assert "records" in data

    # Dataset split endpoint
    res_split = client.get("/api/v1/pipeline/dataset?split=true&train_ratio=0.8", headers=admin_headers)
    assert res_split.status_code == status.HTTP_200_OK
    split_data = res_split.json()
    assert "train" in split_data
    assert "test" in split_data

    # CSV export endpoint
    res_csv = client.get("/api/v1/pipeline/export/csv", headers=admin_headers)
    assert res_csv.status_code == status.HTTP_200_OK
    assert "text/csv" in res_csv.headers["content-type"]
    assert "shipment_id" in res_csv.text
