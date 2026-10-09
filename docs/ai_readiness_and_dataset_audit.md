# FlowGrid — Phase 24.1: AI/ML Readiness & Dataset Audit Report

**Audit Date**: October 2026  
**Auditor**: Antigravity AI Engineering  
**Scope**: Read-only verification of Phase 21 AI data pipeline, Phase 22 analytics, database models, shipment lifecycle timestamps, dataset exports, test coverage, and readiness for planned AI capabilities (ETA Prediction, Shipment Delay Prediction, Delay Risk Score, AI Logistics Assistant).

---

## Executive Summary

A comprehensive, non-destructive audit of the FlowGrid platform was conducted to determine the operational and statistical readiness of existing data for four planned AI capabilities.

### Key Audit Findings:
1. **Infrastructure Maturity**: FlowGrid possesses an architecturally clean, robust feature extraction and engineering framework ([`FeatureExtractor`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_extractor.py), [`FeatureEngineer`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py), [`DataQualityChecker`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/quality_checker.py), and [`DatasetGenerator`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/dataset_generator.py)), backed by 258 passing automated tests (including 9 specialized pipeline tests and 18 analytics tests).
2. **Current Data Inventory**: The live PostgreSQL database and exported CSVs contain exactly **6 shipment records**, generated from seed fixtures ([`seed_demo_data.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/seed_demo_data.py)). There are **zero genuine historical operational records**.
3. **Target Variable Availability**: Across all 6 records, **0 records (0.0%) have populated target variables** (`actual_duration_hours`, `is_delayed`, `delay_hours`). The automated quality audit explicitly flags `records_with_targets = 0` and `is_valid_for_training = false`.
4. **Timestamp & Route Deficits**: Zero shipments have route assignments (`route_shipments` table has 0 rows). The `Shipment` database model lacks an `estimated_delivery_at` column. Actual pickup timestamps depend on status transition history, which has 0 rows in the seeded database.
5. **Frontend vs. Reality Gap**: The frontend UI ([`mockLogisticsData.js`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/data/mockLogisticsData.js)) displays prototype marketing text claiming a *"scikit-learn gradient boosting regression trained on 42k historical legs"* with *"96.4% precision"*. This is confirmed to be fictional UI mock copy; no trained models, weights, or 42k training records exist.
6. **Feature Feasibility Verdict**:
   - **ETA Prediction (Continuous Regression)**: **BLOCKED / NOT READY** (0 samples with duration).
   - **Delay Prediction (Binary Classification)**: **BLOCKED / NOT READY** (0 labeled instances).
   - **Delay Risk Score**: **FEASIBLE AS A RULE-BASED / DETERMINISTIC HEURISTIC INDEX**; NOT ready as a trained probability model.
   - **AI Logistics Assistant**: **HIGH READINESS**; fully feasible immediately using deterministic tool-calling/RAG over existing REST API endpoints with RBAC and PII safeguards.

---

## 1. Summary of Existing AI & Data Infrastructure

FlowGrid's Phase 21 established the foundation for ML dataset processing, while Phase 22 implemented analytics aggregation.

### 1.1 Pipeline Architecture ([`backend/app/pipeline/`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline))

| Component | File | Responsibility | Audit Status |
| :--- | :--- | :--- | :--- |
| **Schema Registry** | [`schema.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/schema.py) | Defines 24 features across `RAW_FEATURE`, `DERIVED_FEATURE`, `TARGET_VARIABLE`, and `DEFERRED`. Pydantic schema [`DatasetRecord`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/schema.py#L294-L351) has 40 fields. | Verified. Schema is well-typed and comprehensive. |
| **Feature Extractor** | [`feature_extractor.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_extractor.py) | Safely queries `Shipment` joined with `Warehouse`, `Driver`, `Vehicle`, `Route`, and `ShipmentStatusHistory`. Extracts actual pickup/delivery milestones. | Verified. Redacts PII. Identified lookahead risk in delay remark scanning. |
| **Feature Engineer** | [`feature_engineer.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py) | Calculates weight utilization, scheduled pickup hour/day/month/weekend, interstate flag, and isolates target calculation exclusively to `DELIVERED` status. | Verified. Correctly halts target generation for active shipments. Identified target-feature coupling. |
| **Quality Checker** | [`quality_checker.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/quality_checker.py) | Audits missing values, duplicates, non-negative bounds, inverted timestamps, and enforces anti-leakage quarantine rules. | Verified. Produces structured [`DataQualityReport`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/schema.py#L364-L376). Correctly flags `is_valid_for_training = False`. |
| **Dataset Generator** | [`dataset_generator.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/dataset_generator.py) | Coordinates extraction, quality checks, chronological train/test splitting, and CSV/JSON export. | Verified. Identifies sorting subtleties with string ISO timestamps. |
| **Export CLI** | [`scripts/export_ml_dataset.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/export_ml_dataset.py) | Command-line utility to generate partitioned CSVs and JSON quality audits into `ml_exports/`. | Verified. Executes cleanly and deterministically. |
| **REST APIs** | [`api/v1/endpoints/pipeline.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/pipeline.py) | Exposes `/schema`, `/quality-report`, `/dataset`, and `/export/csv` protected by RBAC (`ADMIN`, `MANAGER`). | Verified. Complete role protection in place. |

### 1.2 Analytics Infrastructure ([`backend/app/repositories/analytics_repository.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/repositories/analytics_repository.py))

Phase 22 implemented analytical calculations:
- `_calculate_delivery_performance()`: Calculates on-time rate, late rate, average duration, and average delay by checking `ShipmentStatusHistory` and comparing against route `estimated_duration`.
- Endpoints under `/api/v1/analytics/` provide dashboard KPIs for Overview, Shipments, Inventory, Warehouses, Routes, Drivers, and Vehicles.

---

## 2. Dataset Inventory and Measured Statistics

### 2.1 File Inventory

Four dataset artifacts exist on disk in [`backend/ml_exports/`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports):

| File Path | Format | File Size | Record Count | Description |
| :--- | :--- | :--- | :--- | :--- |
| [`backend/ml_exports/full_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/full_dataset.csv) | RFC 4180 CSV | 1,906 bytes | 6 records | Consolidated export of all database shipments |
| [`backend/ml_exports/train_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/train_dataset.csv) | RFC 4180 CSV | 1,468 bytes | 4 records | Chronological 80% training partition |
| [`backend/ml_exports/test_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/test_dataset.csv) | RFC 4180 CSV | 1,200 bytes | 2 records | Chronological 20% evaluation partition |
| [`backend/ml_exports/data_quality_report.json`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/data_quality_report.json) | JSON | 1,427 bytes | 1 audit | Audit report generated by [`quality_checker.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/quality_checker.py) |

### 2.2 Measured Statistics & Missingness (from [`data_quality_report.json`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/data_quality_report.json))

- **Total records**: `6`
- **Clean records**: `6` (meets basic Pydantic constraints)
- **Records with populated targets**: `0` (0.0%)
- **Valid for ML training**: `False`
- **Missing values by column**:

| Field Name | Category | Missing Count | Missing Rate | Operational Cause |
| :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | Identifier | 0 / 6 | 0.0% | Always present |
| `tracking_number` | Identifier | 0 / 6 | 0.0% | Always present |
| `created_timestamp` | Timestamp | 0 / 6 | 0.0% | Always populated by DB |
| `origin_warehouse_id` | Facility | 0 / 6 | 0.0% | Populated |
| `destination_city` | Consignee | 0 / 6 | 0.0% | Populated |
| `destination_state` | Consignee | 0 / 6 | 0.0% | Populated |
| `cargo_weight_kg` | Cargo | 0 / 6 | 0.0% | Populated |
| `cargo_volume_cbm` | Cargo | 0 / 6 | 0.0% | Populated |
| `assigned_driver_id` | Fleet | 5 / 6 | **83.3%** | Only 1 shipment assigned to driver in seed data |
| `assigned_vehicle_id` | Fleet | 5 / 6 | **83.3%** | Only 1 shipment assigned to vehicle in seed data |
| `route_id` | Route | 6 / 6 | **100.0%** | Zero shipments linked to `routes` via `route_shipments` |
| `route_name` | Route | 6 / 6 | **100.0%** | Zero shipments linked to `routes` |
| `planned_distance_km` | Route | 6 / 6 | **100.0%** | Zero shipments linked to `routes` |
| `planned_duration_hours` | Route | 6 / 6 | **100.0%** | Zero shipments linked to `routes` |
| `scheduled_pickup_timestamp` | Timestamp | 6 / 6 | **100.0%** | `scheduled_pickup_at` was `None` during seed |
| `actual_pickup_timestamp` | Timestamp | 6 / 6 | **100.0%** | No `PICKED_UP` status history events recorded |
| `actual_delivery_timestamp` | Timestamp | 5 / 6 | **83.3%** | Only shipment ID 3 is in `DELIVERED` status |
| `actual_duration_hours` | **Target** | 6 / 6 | **100.0%** | Cannot calculate without valid pickup timestamp |
| `is_delayed` | **Target** | 6 / 6 | **100.0%** | Cannot calculate without actual duration & route |
| `delay_hours` | **Target** | 6 / 6 | **100.0%** | Cannot calculate without actual duration & route |

### 2.3 Operational Database Audit (Live PostgreSQL Read-Only Query)

A read-only query of the live development PostgreSQL database (`flowgrid_db`) verified:
- `shipments` table: **6 rows** (Statuses: `IN_TRANSIT`: 2, `DELIVERED`: 1, `FAILED`: 1, `ASSIGNED`: 1, `CONFIRMED`: 1).
- `warehouses` table: **3 rows** (Chicago ORD-01, Newark EWR-02, Dallas DFW-04).
- `drivers` table: **1 row** (Alex Rivera).
- `vehicles` table: **3 rows** (Semi-Trailer, Box Truck, Flatbed).
- `routes` table: **3 rows** (I-80, I-95 North, I-35).
- `shipment_status_history` table: **0 rows** (No audit trail events were generated when seed script inserted directly).
- `shipment_tracking_events` table: **0 rows**.
- `route_shipments` table: **0 rows**.

**Conclusion on Data Authenticity**: All existing records are 100% synthetic development fixtures created by [`seed_demo_data.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/seed_demo_data.py). Zero genuine operational delivery records exist in the system.

---

## 3. Timestamp, Milestone, and Lifecycle Audit

### 3.1 Availability of Milestone Timestamps

| Operational Milestone | Model / Field | Populated in Data? | Pipeline Handling |
| :--- | :--- | :--- | :--- |
| **Creation** | [`Shipment.created_at`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py#L124) | Yes (100%) | Formatted to ISO string. |
| **Scheduled Pickup** | [`Shipment.scheduled_pickup_at`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py#L111) | No (0%) | Optional in schema; null in demo records. |
| **Actual Pickup / Dispatch** | *No direct column on `Shipment`* | No (0%) | Inferred dynamically from [`ShipmentStatusHistory`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/tracking.py#L27) (`PICKED_UP` or `IN_TRANSIT`). Falls back to `scheduled_pickup_at`. Both are null. |
| **Estimated Delivery (ETA)** | *Does NOT exist in schema* | **Unavailable** | The database model has no `estimated_delivery_at` or `promised_delivery_at`. Route table has static `estimated_duration` in hours. |
| **Actual Delivery** | [`Shipment.delivered_at`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py#L115) | Yes for 1 shipment (ID 3) | Populated when transitioning to `DELIVERED`. |

### 3.2 Historical Durations and Delay Labels

- **Historical Durations**: Non-existent. Even for delivered shipment ID 3, `actual_pickup_at` was `None` because no status history record was created at pickup. Duration cannot be calculated ($t_{\text{delivery}} - \text{None} = \text{None}$).
- **Defensible Delay Labels**: Non-existent. In [`feature_engineer.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py#L93-L104), delay requires both `actual_duration_hours` and `route.estimated_duration`. Since neither is available, zero labels exist.
- **External Telematics**:
  - Distance: Available only at route corridor level; not assigned to shipments.
  - GPS Lat/Lng: Schema lists `realtime_gps_lat_lng` under `DEFERRED`. No telemetry streams exist.
  - Weather: Schema lists `weather_precipitation_index` under `DEFERRED`. No weather data exists.
  - Traffic: Schema lists `corridor_traffic_congestion_level` under `DEFERRED`. No traffic data exists.

---

## 4. Evaluation of Proposed AI Capabilities

### 4.1 Feature 1: ETA Prediction (Continuous Delivery Duration Regression)
* **Goal**: Predict continuous elapsed transit time from pickup to delivery (`actual_duration_hours`).
* **Readiness**: 🔴 **NOT READY (Blocked)**
* **Audit Evaluation**:
  - **Target Variable**: `actual_duration_hours` is well-defined mathematically, but has **0 observed instances** in the dataset.
  - **Volume**: 0 training samples. Statistical regression (Linear, Ridge, Gradient Boosting) requires at least several hundred completed dispatches.
  - **Route Grounding**: Deliveries cannot have transit times estimated accurately without distance or origin-destination routing. Currently, routes are unlinked.
  - **Prerequisites for Implementation**: Accumulate $\ge 500$ completed dispatches with enforced pickup and delivery timestamps; assign routes or calculate haversine distance.

### 4.2 Feature 2: Shipment Delay Prediction (Binary Classification)
* **Goal**: Predict whether an in-transit dispatch will arrive later than planned (`is_delayed` $\in \{0, 1\}$).
* **Readiness**: 🔴 **NOT READY (Blocked)**
* **Audit Evaluation**:
  - **Target Definition**: The current pipeline definition (`actual_duration > planned_duration + 0.1`) is objective, but completely unpopulated (0 positive, 0 negative examples).
  - **SLA Ambiguity**: The platform tracks route duration but lacks a committed customer SLA delivery deadline (`promised_delivery_at`).
  - **Prerequisites for Implementation**: Establish SLA timestamps on shipment creation; accumulate balanced historical records ($\ge 300$ samples with $\ge 15\%$ delay rate).

### 4.3 Feature 3: Delay Risk Score (Multi-Factor Risk Assessment)
* **Goal**: Provide dispatchers with a proactive 0–100 risk score highlighting dispatches vulnerable to bottlenecks.
* **Readiness**: 🟡 **FEASIBLE AS A RULE-BASED / DETERMINISTIC HEURISTIC INDEX; NOT READY AS A STATISTICAL PROBABILITY MODEL**
* **Audit Evaluation**:
  - **Measurable Pre-Dispatch Features Available**:
    1. Unassigned resources: `has_driver_assigned == 0` (+25 pts), `has_vehicle_assigned == 0` (+25 pts), `has_route_assigned == 0` (+15 pts).
    2. Capacity strain: `weight_capacity_utilization > 0.85` (+15 pts).
    3. Geographical complexity: `is_interstate == 1` (+10 pts).
    4. Temporal schedule: `is_weekend == 1` (+10 pts), night dispatch (+5 pts).
    5. Warehouse congestion: Origin hub utilization rate from [`analytics_repository.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/repositories/analytics_repository.py#L251) ($> 85\%$ adds +10 pts).
  - **Statistical Calibration**: Calibrated probabilities ($P(\text{delay} \mid X)$) cannot be calculated without training labels.
  - **Recommendation**: Implement an **interpretable, deterministic Rule-Based Delay Risk Index (0–100)** with transparent risk factors in Phase 24.2. Upgrade to ML probability weighting once data accumulates.

### 4.4 Feature 4: AI Logistics Assistant (Natural Language Operational Intelligence)
* **Goal**: Enable dispatchers and managers to query inventory, tracking, hub capacity, and fleet availability via conversational interface.
* **Readiness**: 🟢 **HIGH READINESS (Feasible Immediately)**
* **Audit Evaluation**:
  - **Data Source Grounding**: FlowGrid already exposes well-documented, clean REST endpoints and repositories:
    - Tracking: [`/api/v1/shipments/tracking/{tracking_number}`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/shipments.py#L108) and status history.
    - Inventory: [`/api/v1/inventory/low-stock`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/inventory.py) and stock balance queries.
    - Facilities: [`/api/v1/warehouses`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/warehouses.py) capacity and locations.
    - Fleet: [`/api/v1/drivers`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/drivers.py) and [`/api/v1/vehicles`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/vehicles.py) availability.
    - Analytics: [`/api/v1/analytics/overview`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/analytics.py#L33) KPIs and throughput.
  - **Security & RBAC**: The assistant can inherit user JWT credentials via [`get_current_user`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/deps.py) to prevent unauthorized privilege escalation.
  - **Safety Boundaries**: The assistant must operate strictly in **read-only mode**, barring autonomous mutations, deletions, or status overrides.

---

## 5. Review of Phase 21 Feature Engineering & Leakage Risks

A detailed code review of [`backend/app/pipeline/`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline) revealed three critical data leakage and engineering concerns:

### 5.1 Lookahead Leakage: `historical_delay_signals_count`
- **Location**: [`feature_extractor.py:130-136`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_extractor.py#L130-L136) and [`feature_engineer.py:140`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py#L140).
- **The Issue**: `FeatureExtractor` loops over `shipment.status_history` across the shipment's entire lifecycle and counts any remark matching `"delay"`, `"late"`, `"breakdown"`, or `"traffic"`. This number is then provided as `historical_delay_signals_count` in the input feature vector.
- **Leakage Impact**: If a dispatcher logs *"Breakdown on highway"* 4 hours into transit, that remark occurred **after** dispatch. Feeding this into a pre-dispatch delay prediction model introduces severe future lookahead leakage.
- **Circular Target Identity**: In [`feature_engineer.py:102`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py#L102), if `planned_duration_hours` is missing, the code sets `is_delayed = 1 if ctx.delay_signals_count > 0 else 0`. If `delay_signals_count` is also an input feature, the model trivially predicts the target using itself.
- **Remediation**: Filter status history events by timestamp: only audit events created *before or at dispatch* ($t \le t_{\text{dispatch}}$) may be counted as pre-dispatch features.

### 5.2 Timestamp Inversion & Scheduled Pickup Conflation
- **Location**: [`feature_extractor.py:118-120`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_extractor.py#L118-L120).
- **The Issue**: If no `PICKED_UP` or `IN_TRANSIT` milestone is found, `actual_pickup_at` falls back to `scheduled_pickup_at`.
- **Impact**: Conflates planned schedule with actual departure. If a driver departs 4 hours late, `actual_duration_hours` calculated against `scheduled_pickup_at` misattributes loading dock delays to on-road transit time.

### 5.3 ISO String Sorting in Chronological Splitting
- **Location**: [`dataset_generator.py:73-76`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/dataset_generator.py#L73-L76).
- **The Issue**: `DatasetGenerator.split_chronologically()` sorts records using lexical Python string comparisons on `r.scheduled_pickup_timestamp or r.created_timestamp`.
- **Impact**: If ISO strings have varying timezone offsets (e.g. `+05:30` vs `Z`) or microsecond precisions, lexical string sorting diverges from true chronological ordering, potentially contaminating train and test splits.
- **Remediation**: Parse to `datetime` objects before sorting.

---

## 6. Recommended Baseline Approaches

Based on empirical evidence from the audit:

| AI Capability | Recommended Baseline Approach for Phase 24.2 | ML Model Justified Now? |
| :--- | :--- | :---: |
| **ETA Prediction** | **Static Route Corridor Baseline**: Use `Route.estimated_duration` plus a dynamic staging buffer (+0.5 hrs for local, +1.5 hrs for interstate). | **No** (0 training rows) |
| **Delay Prediction** | **Corridor Buffer Threshold**: Flag dispatch as at-risk if elapsed transit time exceeds planned duration by $\ge 10\%$. | **No** (0 training rows) |
| **Delay Risk Score** | **Deterministic Operational Heuristic Index (0–100)**: Transparent weighted formula evaluating driver/vehicle allocation, capacity utilization, interstate travel, and origin hub congestion. | **No** (Rule-based first) |
| **AI Logistics Assistant** | **Deterministic Tool-Calling Query Agent**: Integrate secure, authenticated service calls against existing API endpoints with RBAC enforcement and PII redaction. | **N/A** (LLM/Agent) |

---

## 7. Data Collection Strategy & Next Steps

To transition ETA and Delay Prediction from rule-based baselines to supervised machine learning models in future phases:

1. **Enforce Mandatory Lifecycle Timestamps**:
   - Record `actual_dispatched_at` on the `Shipment` record when moving to `PICKED_UP`.
   - Add optional `promised_delivery_at` (customer SLA commitment) to `Shipment` schema to create an unambiguous delay ground truth.
2. **Mandate Route Linking**:
   - Ensure the dispatch workflow connects each active shipment to a route in `route_shipments`, providing baseline planned distances and corridor durations.
3. **Data Accumulation Thresholds**:
   - **Minimum for Regression ETA Model**: 500 completed dispatches with verified pickup and delivery timestamps across active routes.
   - **Minimum for Binary Delay Classifier**: 300 completed dispatches with at least 50 delayed dispatches (balanced class representation).
4. **Fix Pipeline Anti-Leakage Filters**:
   - Update `FeatureExtractor` to restrict `delay_signals_count` strictly to pre-dispatch audit entries.
   - Update `DatasetGenerator.split_chronologically()` to parse datetime objects for temporal sorting.

---

## 8. Audit Evidence & Verification Log

### 8.1 Files Inspected
- Backend Pipeline:
  - [`backend/app/pipeline/schema.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/schema.py)
  - [`backend/app/pipeline/feature_extractor.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_extractor.py)
  - [`backend/app/pipeline/feature_engineer.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/feature_engineer.py)
  - [`backend/app/pipeline/quality_checker.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/quality_checker.py)
  - [`backend/app/pipeline/dataset_generator.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/pipeline/dataset_generator.py)
- Models & Services:
  - [`backend/app/models/shipment.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py)
  - [`backend/app/models/route.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/route.py)
  - [`backend/app/models/tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/tracking.py)
  - [`backend/app/services/shipment_service.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/shipment_service.py)
  - [`backend/app/services/analytics_service.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/analytics_service.py)
  - [`backend/app/repositories/analytics_repository.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/repositories/analytics_repository.py)
- Scripts & Seed Fixtures:
  - [`backend/scripts/export_ml_dataset.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/export_ml_dataset.py)
  - [`backend/scripts/seed_demo_data.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/seed_demo_data.py)
- Frontend:
  - [`frontend/src/components/AiInsightPanel.jsx`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/components/AiInsightPanel.jsx)
  - [`frontend/src/hooks/useDashboardData.js`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/hooks/useDashboardData.js)
  - [`frontend/src/data/mockLogisticsData.js`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/data/mockLogisticsData.js)
- Datasets Inspected:
  - [`backend/ml_exports/data_quality_report.json`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/data_quality_report.json)
  - [`backend/ml_exports/full_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/full_dataset.csv)
  - [`backend/ml_exports/train_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/train_dataset.csv)
  - [`backend/ml_exports/test_dataset.csv`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/test_dataset.csv)

### 8.2 Tests & Non-Destructive Checks Executed

1. **Test Suite Execution**:
   - `pytest backend/tests/test_ml_pipeline.py`: **9 passed** in 9.96s.
   - `pytest backend/tests/test_analytics.py`: **18 passed** in 10.84s.
   - Full test suite `pytest backend/tests`: **258 passed** in 74.15s.
2. **Database State Verification**:
   - Read-only SQLAlchemy query executed: confirmed exactly 6 shipments, 0 status history rows, 0 route shipment associations.
3. **Quality Report Verification**:
   - Confirmed `is_valid_for_training == False` and `records_with_targets == 0` in [`data_quality_report.json`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/data_quality_report.json).

---

## 9. Clear Recommendation for Next Implementation Phase (Phase 24.2)

Proceed to **Phase 24.2** with the following concrete, verified scope:

1. **Implement Feature 3: Deterministic Delay Risk Score**:
   - Build a lightweight, interpretable, non-ML service calculating a 0–100 risk score and identifying top operational risk factors (unassigned assets, high load utilization, warehouse congestion, interstate journey).
   - Expose via `GET /api/v1/analytics/delay-risk` or integrate into shipment response schema.
2. **Implement Feature 4: AI Logistics Assistant**:
   - Build an operational assistant service connecting safe, read-only FlowGrid endpoints (Tracking, Hub status, Low Stock, Driver availability, Analytics KPIs).
   - Enforce strict RBAC and PII masking.
3. **Implement Static Baseline for ETA**:
   - Surface static route estimated duration + buffer as an interim heuristic until historical operational records accumulate.
4. **Fix Pre-Dispatch Leakage in Phase 21 Pipeline**:
   - Add timestamp filtering to `FeatureExtractor` to eliminate the lookahead leakage in `historical_delay_signals_count`.
5. **Do NOT Attempt Training ML Models Yet**:
   - Defer regression and classification model training until the operational platform records at least 500 genuine delivered dispatches.
