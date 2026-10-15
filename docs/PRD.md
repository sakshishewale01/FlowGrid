# FlowGrid — Product Requirements Document (PRD)

> **Intelligent Logistics & Transportation Control Tower**  
> *Status:* Production Baseline • *Updated:* October 2026 • *Location:* `docs/PRD.md`

---

## 1. Executive Summary

**FlowGrid** is a full-stack, enterprise-grade **Logistics Operations Control Tower** and Transportation Management System (TMS). It bridges fragmented supply chain silos by pairing core execution capabilities (warehousing, inventory tracking, fleet dispatch, and immutable state transitions) with predictive intelligence:
- **Predict**: Quantify transit bottlenecks using ML pipelines and heuristic delay risk scoring.
- **Decide**: Triage operational strain via transparent rule engines and non-destructive "What-If" scenario simulations.
- **Recover**: Execute verified mitigation protocols (driver reallocation, line-haul corridor rerouting, equipment swaps) with immediate state machine validation.

---

## 2. Problem Statement & Real-World Challenges

1. **Fragmented Operational Visibility**:
   Dispatchers lose sight of freight once it leaves fulfillment centers, relying on disjointed phone calls and delayed spreadsheets.
2. **State Transition Anarchy**:
   Conventional logistics systems allow arbitrary status overrides (e.g., jumping from `CREATED` directly to `DELIVERED`), corrupting auditability and operational integrity.
3. **Capacity & Driver Mismatches**:
   Freight is frequently dispatched to inactive drivers or vehicles without checking payload weight ratings against capacity limits.
4. **Reactive Rather Than Proactive Triage**:
   Delays are identified only after delivery windows expire, making early intervention impossible without deterministic risk indicators.
5. **Superficial "AI Hype"**:
   Industry platforms market "black box" AI without transparent explanations or data validation.

---

## 3. User Roles & RBAC Matrix

FlowGrid enforces strict privilege separation both in the FastAPI service layer and on the React client:

| Privilege / Action | Admin | Manager | Driver | Viewer |
| :--- | :---: | :---: | :---: | :---: |
| **System Settings & Health Probes** | ✅ | ✅ | ❌ | ❌ |
| **Create / Deactivate Warehouses** | ✅ | ❌ | ❌ | ❌ |
| **Adjust Stock & Inventory Records** | ✅ | ✅ | ❌ | ❌ |
| **Dispatch / Reschedule Shipments** | ✅ | ✅ | ❌ | ❌ |
| **Execute Rescue Center Interventions**| ✅ | ✅ | ❌ | ❌ |
| **Update Own Driver Duty Status** | ✅ | ✅ | ✅ | ❌ |
| **Run What-If Disruption Simulations** | ✅ | ✅ | ❌ | 👁️ Read-Only |
| **Query Logistics Assistant** | ✅ | ✅ | ✅ | ✅ |
| **Export RFC 4180 CSV Manifests** | ✅ | ✅ | ✅ | ✅ |
| **Read-Only Telematics & Analytics** | ✅ | ✅ | ✅ | ✅ |

---

## 4. Key Functional Capabilities

### 4.1 Executive Control Tower Dashboard
- **Live Corridor Telematics**: Interactive SVG & Leaflet-powered flow map visualizing transit nodes, moving freight corridors, and pulsing status halos (`pulse-halo`).
- **Real-Time KPIs**: Metric cards tracking Total Active Shipments, On-Time Dispatch Rate (94.2%), Critical Risk Freight Count, and Active Fleet Hubs with 7-day sparkline trend indicators.
- **Quick Dispatch Bar**: Action shortcuts with role-aware lock icons protecting sensitive dispatch mutations from unauthorized operator roles.
- **Top Navigation Bar**: Live backend connection health probe (`/health`), global search across multiple entities, unread notification panel with real-time badges, and operator session profile dropdown.

### 4.2 Shipment Rescue Center
- **Explainable Rule-Based Triage**: Evaluates live shipment records against deterministic operational rules:
  - `RULE-EX01`: Dispatch/Transit Exception (Failed deliveries or abort events).
  - `RULE-R01`: Unassigned Fleet Driver (Missing driver profile blocking dispatch).
  - `RULE-R02`: Unassigned Transport Equipment (No vehicle/trailer asset allocated).
  - `RULE-R03`: Unassigned Transit Corridor (Missing line-haul corridor causing ETA variance).
  - `RULE-R04`: Capacity Strain (Cargo weight exceeding 85% vehicle capacity rating).
- **Human-in-the-Loop Interventions**: Interactive modal drawers allowing operators to resolve missing resources directly from the triage queue with immediate state transition validation.

### 4.3 What-If Disruption Simulator
- **Non-Destructive Sandbox**: Tests operational shocks against real database records without altering production data.
- **4 Real-World Disruption Scenarios**:
  1. *Driver Unavailability / Fleet Strike*: Simulates cascading delays from operator shortages.
  2. *Route Corridor Closure / Weather Event*: Models line-haul transit corridor blocks and detour times.
  3. *Warehouse Capacity Bottleneck*: Evaluates staging buffer limits and cross-dock delays.
  4. *Fuel Surcharge & Transit Cost Spike*: Estimates financial impact and margin compression.
- **Cascade Impact Analysis**: Quantifies affected shipments, estimated delivery time variance (+hours), and projected financial loss ($) with side-by-side mitigation comparisons.

### 4.4 Operational Recommendations Engine
- Grounded suggestions categorized by priority (`CRITICAL`, `WARNING`, `OPTIMIZATION`).
- Generates transparent rationales detailing *why* an intervention is recommended, expected delivery improvement, and confidence rating.
- Requires operator confirmation before dispatching live database updates.

### 4.5 Grounded Logistics Assistant
- Natural language operator companion accessible via quick actions (`Ask Assistant`) or slide-out drawer.
- **Strictly Grounded Context**: Formulates responses directly from verified backend endpoints (`/shipments`, `/warehouses`, `/drivers`, `/vehicles`, `/analytics`) rather than ungrounded generative hallucinations.
- Supports entity lookups (`#SHP-101`), warehouse stock inquiries, driver duty status checks, and fleet utilization telemetry.

### 4.6 Machine Learning Delay Prediction
- **Trained Pipeline**: Scikit-Learn Random Forest Pipeline (`rf_pipeline.joblib`) with integrated numeric and categorical preprocessors.
- **API Endpoint**: Authenticated `POST /api/v1/ml/predict-delay`.
- **Feature Set**: Transit distance, cargo weight, vehicle capacity utilization, driver hours of service, weather index, and historical route congestion.
- **Transparent Governance Disclaimer**: Explicitly identifies the model as an experimental decision-support prototype (synthetic baseline ROC-AUC ~0.5062) requiring human verification.

### 4.7 Core Logistics Modules (CRUD & Lifecycles)
- **Warehouses**: Storage capacity management, geo-coordinates, dock availability, and inventory allocation.
- **Inventory**: Product catalog, batch tracking, stock level thresholds, and automatic low-stock alerts.
- **Fleet & Drivers**: Vehicle payload ratings, fuel types, maintenance states, driver duty logs, and licensing.
- **Shipments**: Comprehensive 5-stage lifecycle state machine (`PENDING` ➔ `DISPATCHED` ➔ `IN_TRANSIT` ➔ `OUT_FOR_DELIVERY` ➔ `DELIVERED` / `FAILED`).
- **Transit Routes**: Geographic waypoints, corridor distance, estimated duration, and linked toll schedules.

---

## 5. Non-Functional Requirements & Security

- **Performance**: API p95 response time $<120\text{ms}$ for standard CRUD operations; initial SPA load $<1.2\text{s}$.
- **Security & Cryptography**: Argon2id password hashing, HMAC-SHA256 Bearer JWTs, strict CORS whitelist, and Pydantic v2 input sanitization.
- **Dual-Theme Support**: Dark Mode (Deep Tech Blue `#0B1220`) as reference baseline; Light Mode (Precision Operational `#F1F5F9`) with instant `localStorage` persistence and zero-flash initialization.
- **Data Integrity**: Enforced foreign key constraints, atomic database transactions, payload weight validation, and soft-delete protection on active records.

---

## 6. Success Metrics & Scope Boundaries

### Target Metrics
- **Exception Resolution Time**: $\ge 40\%$ reduction in dispatcher triage time via the Shipment Rescue Center.
- **Audit Compliance**: $100\%$ adherence to the 5-stage shipment state machine with zero orphaned transitions.
- **Equipment Safety**: $0$ dispatches exceeding rated vehicle payload capacities.

### Explicit Non-Goals
- Autonomous self-driving vehicle hardware telemetry.
- Direct credit card payment gateway integration (B2B corporate invoicing assumed).
- Unvalidated "black box" automated decision making without operator sign-off.
