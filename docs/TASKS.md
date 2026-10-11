# FlowGrid — Implementation Roadmap & Task Progress Tracker
**Engineering Task Ledger, Implementation Baseline & Phased Milestone Tracker**

*Document Version:* 1.0.0  
*Status:* Authoritative Engineering Progress Baseline  
*Last Updated:* October 2026  
*Primary Source of Truth:* FlowGrid Source Code, Database Migrations & Automated Test Suites

---

## 🎯 Next Recommended Task

> [!IMPORTANT]
> **TOP PRIORITY NEXT TASK: `TASK-DATA-01` (Add `estimated_delivery_at` Column & Milestone Enrichment)**
>
> **Why this must come first:**  
> The comprehensive dataset and AI readiness audit (`docs/ai_readiness_and_dataset_audit.md`) established that 100% of statistical ML capabilities (continuous ETA regression and binary delay classification) are **hard-blocked** because the database currently contains **zero historical records with populated delivery durations or delay targets**. Furthermore, the `Shipment` database model lacks an `estimated_delivery_at` column, and initial demo fixtures generated zero rows in `shipment_status_history` and `route_shipments`.
>
> Adding `estimated_delivery_at` via an Alembic migration and enriching seed/operational dispatches with authentic milestone timestamps will unblock Phase C (Operational Data Reliability), enable genuine baseline analytics benchmarking, and create the prerequisite data foundation for Phase D (ETA Prediction).

---

## Table of Contents
1. [Project Status Summary](#1-project-status-summary)
2. [Current Implementation Baseline](#2-current-implementation-baseline)
3. [Completed & Verified Tasks](#3-completed--verified-tasks)
4. [Implemented but Incompletely Verified Tasks](#4-implemented-but-incompletely-verified-tasks)
5. [In-Progress Tasks](#5-in-progress-tasks)
6. [Blocked Work & Critical Dependencies](#6-blocked-work--critical-dependencies)
7. [Known Technical Debt, Bugs & Risks](#7-known-technical-debt-bugs--risks)
8. [Prioritized Implementation Roadmap (Phases A–F)](#8-prioritized-implementation-roadmap-phases-a-f)
9. [Definition of Done (DoD)](#9-definition-of-done-dod)
10. [Testing & Validation Checklist](#10-testing--validation-checklist)
11. [Suggested Immediate Next Steps](#11-suggested-immediate-next-steps)

---

## 1. Project Status Summary

FlowGrid has reached a robust, production-grade **Operational Baseline**. The decoupled monolith architecture features an enterprise-grade backend with 278 automated pytest tests and an interactive React 19 frontend with 43 automated tests.

### Status Indicators Legend:
- `[x]` **Completed & Verified**: Fully implemented in code, passing automated tests, operational in UI.
- `[-]` **Partially Implemented / Incomplete Verification**: Implemented in code or UI mock, but requires integration verification or operational testing.
- `[!]` **Blocked / Needs Investigation**: Cannot progress due to missing database schema columns, absent data dependencies, or upstream blockers.
- `[ ]` **Not Started / Planned**: Scheduled for upcoming development phases.

---

## 2. Current Implementation Baseline

| Subsystem | Implemented Components | Verified Automated Test Coverage | Status |
| :--- | :--- | :--- | :---: |
| **Authentication & RBAC** | Argon2id hashing, PyJWT tokens, `require_roles` dependency factory | 18 tests in `test_auth.py` | `[x]` |
| **Warehouses Module** | Facility CRUD, capacity, soft-deletions, active filtering | 19 tests in `test_warehouses.py` | `[x]` |
| **Products Catalog** | Catalog CRUD, SKU uniqueness, soft-deletions, pricing | 19 tests in `test_products.py` | `[x]` |
| **Inventory Module** | Stock levels, `uq_warehouse_product` constraint, reorder levels | 19 tests in `test_inventory.py` | `[x]` |
| **Drivers & Vehicles** | CDL credentials, license uniqueness, vehicle payload limits | 40 tests (`test_drivers.py` & `test_vehicles.py`) | `[x]` |
| **Shipment State Machine** | Strict `ALLOWED_TRANSITIONS`, tracking generator, weight guards | 22 tests in `test_shipments.py` | `[x]` |
| **Tracking & Audit Trail**| Atomic status history logging, physical checkpoint events | 14 tests in `test_tracking.py` | `[x]` |
| **Transit Corridors / Routes**| Route corridors, `route_shipments` association, waypoints | 20 tests in `test_routes.py` | `[x]` |
| **Executive Analytics** | 9 KPI endpoints across all pillars, date filtering, division-by-zero guards | 18 tests in `test_analytics.py` | `[x]` |
| **Real-time Telemetry** | WebSocket `/ws/tracking/{id}`, JWT query auth, connection limits | 14 tests in `test_websocket_tracking.py` | `[x]` |
| **Delay Risk Engine** | Deterministic 0–100 heuristic scoring, factor breakdown, UI integration | 20 tests in `test_delay_risk.py` | `[x]` |
| **AI Data Pipeline** | PII redaction, feature engineering, chronological train/test split | 9 tests in `test_ml_pipeline.py` | `[x]` |
| **Security & Hardening** | Security headers, request timing, sanitized exception handlers | 8 tests in `test_hardening.py` | `[x]` |
| **Frontend Operations UI**| React 19, custom routing, Leaflet mapping, high-density drawer | 43 tests in `frontend/tests/*.test.js` | `[x]` |

---

## 3. Completed & Verified Tasks

### 3.1 Authentication & Security
- [x] **`TASK-AUTH-01`**: Implement Argon2id password hashing using `pwdlib` (`app/core/security.py`).
- [x] **`TASK-AUTH-02`**: Implement JWT token issuance and decoding using PyJWT (`app/core/security.py`).
- [x] **`TASK-AUTH-03`**: Build `require_roles` FastAPI dependency factory enforcing RBAC (`app/api/deps.py`).
- [x] **`TASK-AUTH-04`**: Block deactivated user accounts from authentication and token validation.
- [x] **`TASK-AUTH-05`**: Implement HTTP security headers (`nosniff`, `DENY`, `XSS`, latency timing).

### 3.2 Core Logistics Registries
- [x] **`TASK-CORE-01`**: Create `Warehouse` model, migration, service, repository, and CRUD endpoints.
- [x] **`TASK-CORE-02`**: Create `Product` model, SKU uniqueness constraint, and soft-delete endpoints.
- [x] **`TASK-CORE-03`**: Create `Inventory` model with `uq_warehouse_product` constraint and reorder levels.
- [x] **`TASK-CORE-04`**: Create `Driver` model linked 1-to-1 to `User` with CDL license uniqueness.
- [x] **`TASK-CORE-05`**: Create `Vehicle` model with licensed carrying capacity and maintenance status.
- [x] **`TASK-CORE-06`**: Create `Route` model and `route_shipments` association table with uniqueness.

### 3.3 Shipment Governance & Telemetry
- [x] **`TASK-SHP-01`**: Implement `Shipment` entity with auto-generated collision-free tracking numbers (`FG-YYYYMMDD-XXXXXXXX`).
- [x] **`TASK-SHP-02`**: Enforce `ALLOWED_TRANSITIONS` state machine governing all 10 lifecycle states.
- [x] **`TASK-SHP-03`**: Prevent updating shipments in terminal states (`DELIVERED`, `CANCELLED`, `RETURNED`).
- [x] **`TASK-SHP-04`**: Enforce vehicle weight capacity guard (`shipment.total_weight_kg <= vehicle.capacity`).
- [x] **`TASK-SHP-05`**: Create `ShipmentStatusHistory` atomic audit trail logging all state changes.
- [x] **`TASK-SHP-06`**: Create `ShipmentTrackingEvent` logging physical milestones with timestamps.
- [x] **`TASK-SHP-07`**: Implement real-time WebSocket hub `/ws/tracking/{shipment_id}` with per-shipment (50) and global (1,000) caps.

### 3.4 Analytics & Explainable Risk Intelligence
- [x] **`TASK-ANL-01`**: Implement 7 standard KPI endpoints (Overview, Shipments, Inventory, Warehouses, Routes, Drivers, Vehicles).
- [x] **`TASK-ANL-02`**: Protect all analytical formulas with explicit division-by-zero guards.
- [x] **`TASK-RSK-01`**: Implement `DelayRiskService` computing deterministic 0–100 risk score and factor explanations.
- [x] **`TASK-RSK-02`**: Expose `/api/v1/analytics/delay-risk` and `/api/v1/analytics/delay-risk/{shipment_id}` endpoints.
- [x] **`TASK-RSK-03`**: Enforce explicit transparency flag (`is_calibrated_probability = False`).

### 3.5 AI Data Pipeline
- [x] **`TASK-PIP-01`**: Build `FeatureExtractor` with eager queries and complete PII redaction.
- [x] **`TASK-PIP-02`**: Build `FeatureEngineer` with anti-leakage target quarantine for undelivered loads.
- [x] **`TASK-PIP-03`**: Build `DataQualityChecker` auditing missing values, bounds, and timestamp sequences.
- [x] **`TASK-PIP-04`**: Build `DatasetGenerator` and CLI script generating chronological RFC 4180 CSV exports.

### 3.6 Frontend Experience
- [x] **`TASK-UI-01`**: Implement "Deep Tech Blue" design system with CSS custom properties in `index.css`.
- [x] **`TASK-UI-02`**: Build lightweight browser history routing in `App.jsx`.
- [x] **`TASK-UI-03`**: Build `ShipmentDetailDrawer` with Overview, Live Tracking, History, and Delay Risk tabs.
- [x] **`TASK-UI-04`**: Integrate Leaflet map route rendering with OpenStreetMap tiles in `ShipmentRouteMap.jsx`.
- [x] **`TASK-UI-05`**: Implement `useTrackingWebSocket` hook handling auto-reconnect and real-time updates.

---

## 4. Implemented but Incompletely Verified Tasks

- [-] **`TASK-VER-01`**: Live multi-client WebSocket concurrency test under load (verified unit/mock tests, needs multi-browser concurrency validation).
- [-] **`TASK-VER-02`**: Verification of delay risk UI updates during real-time status transitions.
- [-] **`TASK-VER-03`**: Frontend integration test suite execution against live running backend on port 8000 (currently 7 integration tests skip when backend is not actively running during `npm test`).

---

## 5. In-Progress Tasks

- [-] **`TASK-DOC-01`**: Complete comprehensive, authoritative documentation suite (`PRD.md`, `ARCHITECTURE.md`, `RULES.md`, `DESIGN.md`, `TASKS.md`, `MEMORY.md`).

---

## 6. Blocked Work & Critical Dependencies

| Task ID | Description | Blocking Dependency | Resolution Strategy |
| :--- | :--- | :--- | :--- |
| **`TASK-ML-01`** | Train Scikit-Learn Continuous ETA Regression Model | **BLOCKED**: 0 historical shipments with recorded pickup-to-delivery durations. | Add `estimated_delivery_at`, record authentic dispatches, run `DataQualityChecker` until `is_valid_for_training = True`. |
| **`TASK-ML-02`** | Train Binary Delay Classification Model | **BLOCKED**: 0 labeled delay instances in database. | Accumulate genuine operational dispatches exceeding route corridor durations. |
| **`TASK-ITEM-01`** | Automatic Inventory Deduction on Shipment Dispatch | **BLOCKED**: Database schema tracks gross cargo weight directly; lacks `shipment_items` join table. | Design and migrate `shipment_items` schema linking products and quantities to shipments. |

---

## 7. Known Technical Debt, Bugs & Risks

1. **Missing `estimated_delivery_at` Column on `Shipment`**:
   - *Debt*: Current schema lacks an explicit ETA timestamp column on `Shipment`, forcing reliance on static route durations.
   - *Risk*: High; prevents comparing promised vs. actual arrival times on individual shipments.
2. **Empty History Audit Trail in Initial Demo Seed**:
   - *Debt*: `seed_demo_data.py` created 6 shipments directly via SQL insert without creating corresponding rows in `shipment_status_history` or `route_shipments`.
   - *Risk*: Causes delay risk scoring and ML feature extraction to report 100% missing milestone timestamps.
3. **Fictional UI Copy in `mockLogisticsData.js`**:
   - *Debt*: Displays text claiming *"scikit-learn gradient boosting trained on 42k historical legs with 96.4% precision"*.
   - *Risk*: Misleads users regarding data readiness.
4. **Starlette Deprecation Warnings in Pytest**:
   - *Debt*: `fastapi.testclient` issues deprecation warnings regarding `httpx` imports in starlette.
   - *Risk*: Low; cosmetic test output noise.

---

## 8. Prioritized Implementation Roadmap (Phases A–F)

### Phase A: Product & Workflow Audit (Verified Baseline)
- [x] **`A.1`**: Audit shipment state machine and verify `ALLOWED_TRANSITIONS`.
- [x] **`A.2`**: Verify driver and vehicle allocation capacity guards.
- [x] **`A.3`**: Audit role permissions across all 10 API router modules.

### Phase B: Explainable Delay-Risk Intelligence (Completed & Verified)
- [x] **`B.1`**: Implement `DelayRiskService` factor-by-factor scoring algorithm.
- [x] **`B.2`**: Expose `/api/v1/analytics/delay-risk` REST endpoints.
- [x] **`B.3`**: Add 20 unit/integration tests in `tests/test_delay_risk.py`.
- [x] **`B.4`**: Integrate Delay Risk tab into `ShipmentDetailDrawer.jsx`.
- [x] **`B.5`**: Ensure transparent non-probability labeling (`is_calibrated_probability = False`).

### Phase C: Reliable Operational Data & Milestone Enrichment (Immediate Next Phase)
- [ ] **`TASK-DATA-01`**: Create Alembic migration adding `estimated_delivery_at: Optional[datetime]` to `shipments` table.
- [ ] **`TASK-DATA-02`**: Update `seed_demo_data.py` to populate realistic `ShipmentStatusHistory` transitions (`PICKED_UP`, `IN_TRANSIT`, `DELIVERED`) and link shipments to routes via `route_shipments`.
- [ ] **`TASK-DATA-03`**: Clean up prototype marketing copy in `mockLogisticsData.js`, replacing it with live `/api/v1/analytics/delay-risk` summaries.
- [ ] **`TASK-DATA-04`**: Verify dataset export via CLI (`scripts/export_ml_dataset.py`) yields non-zero target variables for delivered loads.

### Phase D: Baseline Benchmarking & ETA Estimation
- [ ] **`TASK-ETA-01`**: Implement naive heuristic baseline: Historical Corridor Mean Duration.
- [ ] **`TASK-ETA-02`**: Evaluate dataset quality using `DataQualityChecker`; require minimum 200 clean completed dispatches.
- [ ] **`TASK-ETA-03`**: Train Scikit-Learn baseline regression model evaluating MAE and RMSE against the historical mean baseline.
- [ ] **`TASK-ETA-04`**: Document regression limitations and fallback behavior for unmapped routes.

### Phase E: Grounded AI Logistics Assistant
- [ ] **`TASK-AI-01`**: Design read-only Assistant Service with deterministic tool-calling over existing FlowGrid endpoints (`/shipments/{id}`, `/analytics/overview`, `/analytics/delay-risk/{id}`).
- [ ] **`TASK-AI-02`**: Enforce caller RBAC: The assistant must strictly respect the authenticated user's permissions.
- [ ] **`TASK-AI-03`**: Add negative tests verifying the assistant explains missing milestones rather than speculating.
- [ ] **`TASK-AI-04`**: Add frontend slide-out chat drawer in `TopNavbar.jsx`.

### Phase F: Product Quality & Release Readiness
- [ ] **`TASK-REL-01`**: Implement `shipment_items` table linking products and quantities to shipments.
- [ ] **`TASK-REL-02`**: Dedicated mobile-optimized driver portal view for field status reporting.
- [ ] **`TASK-REL-03`**: Add Redis Pub/Sub backend to `ConnectionManager` for horizontal multi-instance scaling.
- [ ] **`TASK-REL-04`**: AWS ECS / Fargate deployment verification and infrastructure configuration scripts.

---

## 9. Definition of Done (DoD)

A task or feature in FlowGrid is considered **Done** only when:
1. **Code Complete**: Fully implemented adhering to layered architecture (`Routers -> Services -> Repositories -> Models`).
2. **Type Safe**: 100% Python type hints and Pydantic validation schemas.
3. **Database Governed**: Any schema alteration includes an explicit, tested Alembic migration script.
4. **Tested**: Automated tests added/updated; all 278 backend tests and 43 frontend tests pass with zero regressions.
5. **Role Protected**: Enforces RBAC permissions via `require_roles()`.
6. **Documented**: Updated in `TASKS.md`, `ARCHITECTURE.md`, `RULES.md`, and `MEMORY.md`.
7. **No Hardcoded Secrets**: Credentials loaded strictly via environment variables.

---

## 10. Testing & Validation Checklist

Before submitting code changes:
- [ ] Backend test execution: `pytest -v` passes with 0 failures.
- [ ] Frontend test execution: `npm test` passes with 0 failures.
- [ ] Frontend linter: `npm run lint` (`oxlint`) reports zero errors.
- [ ] Database migrations: `alembic check` reports zero unapplied schema changes.
- [ ] WebSocket verification: Connected clients receive live broadcast upon status change.
- [ ] PII audit: Exported ML datasets contain zero emails, phone numbers, or CDL numbers.

---

## 11. Suggested Immediate Next Steps

1. **Step 1**: Execute **`TASK-DATA-01`**: Generate Alembic migration to add `estimated_delivery_at` column to `shipments`.
2. **Step 2**: Execute **`TASK-DATA-02`**: Update `seed_demo_data.py` to create audit trails and route allocations.
3. **Step 3**: Re-run `scripts/export_ml_dataset.py` and verify `data_quality_report.json` reflects populated milestone targets.
4. **Step 4**: Replace fictional mock UI copy in `mockLogisticsData.js` with live delay-risk API data.
