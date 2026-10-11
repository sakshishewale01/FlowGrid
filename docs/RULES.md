# FlowGrid — System Rules, Invariants & Engineering Standards
**The Authoritative Specification of Enforced Business Logic, Security Boundaries & Development Conventions**

*Document Version:* 1.0.0  
*Status:* Authoritative & Enforced Baseline  
*Last Updated:* October 2026  
*Primary Source of Truth:* FlowGrid Backend Services, ORM Models, Schemas & Automated Tests

---

## Table of Contents
1. [Core Principles](#1-core-principles)
2. [Business Rules Classification (Enforced vs. Proposed)](#2-business-rules-classification-enforced-vs-proposed)
3. [Shipment Lifecycle & Valid State Transitions](#3-shipment-lifecycle--valid-state-transitions)
4. [Inventory Consistency & Stock-Management Rules](#4-inventory-consistency--stock-management-rules)
5. [Facility, Driver, Vehicle & Route Allocation Rules](#5-facility-driver-vehicle--route-allocation-rules)
6. [Vehicle Capacity & Weight Invariants](#6-vehicle-capacity--weight-invariants)
7. [Tracking & Timestamp Semantics](#7-tracking--timestamp-semantics)
8. [Authentication, Password Security & Token Invariants](#8-authentication-password-security--token-invariants)
9. [Role-Based Access Control (RBAC) Invariants](#9-role-based-access-control-rbac-invariants)
10. [Database Integrity & Constraint Invariants](#10-database-integrity--constraint-invariants)
11. [API Validation & Error-Handling Conventions](#11-api-validation--error-handling-conventions)
12. [Coding Conventions (Backend & Frontend)](#12-coding-conventions-backend--frontend)
13. [Testing & Quality Verification Requirements](#13-testing--quality-verification-requirements)
14. [Data Privacy & Sensitive-Information Handling](#14-data-privacy--sensitive-information-handling)
15. [AI/ML Data-Quality & Model-Safety Rules](#15-aiml-data-quality--model-safety-rules)
16. [Prohibited Shortcuts & Anti-Patterns](#16-prohibited-shortcuts--anti-patterns)
17. [Mandatory Rules for AI Coding Agents](#17-mandatory-rules-for-ai-coding-agents)

---

## 1. Core Principles

1. **Truth Over Assumption**:
   Never assume a capability exists because it was described in a vision document, an old phase report, or an initial requirement draft. Verify against actual executable Python/JavaScript code and database models.
2. **Deterministic Lifecycle Governance**:
   Logistics status transitions must adhere to an immutable state machine. No operational entity may bypass valid intermediary stages.
3. **Auditability by Default**:
   Every state modification, status advance, and physical checkpoint must produce an immutable audit record linking the timestamp, previous state, new state, and authenticated user identity.
4. **Zero Data Fabrication**:
   Operational analytics and future ML pipelines must strictly reflect real persisted transactions. Fabricating synthetic completion data to artificially inflate metrics is strictly forbidden.
5. **Fail Closed on Security**:
   Endpoints must reject unauthenticated callers (`HTTP 401`) and unauthorized roles (`HTTP 403`). Never bypass RBAC checks or loosen security dependencies to make tests or client components pass.

---

## 2. Business Rules Classification (Enforced vs. Proposed)

To prevent ambiguity, rules in this document are strictly classified as:
- **[ENFORCED]**: Actively implemented in code, checked by FastAPI dependencies, validated by Pydantic schemas, or enforced by PostgreSQL database constraints.
- **[PROPOSED / ROADMAP]**: Planned for future development phases, not yet implemented in backend application logic or database schemas.

---

## 3. Shipment Lifecycle & Valid State Transitions

### 3.1 The Enforced State Machine (`ALLOWED_TRANSITIONS`)
The shipment lifecycle is governed by the state machine defined in [`backend/app/services/shipment_service.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/shipment_service.py#L28-L39):

```text
CREATED  ───────────► CONFIRMED ───────────► ASSIGNED ───────────► PICKED_UP ───────────► IN_TRANSIT ───────────► OUT_FOR_DELIVERY ───────────► DELIVERED (Terminal)
   │                      │                      │                                                                                  │
   ▼                      ▼                      ▼                                                                                  ▼
CANCELLED (Terminal)   CANCELLED (Terminal)   CANCELLED (Terminal)                                                                FAILED
                                                                                                                                    │
                                                                                                  OUT_FOR_DELIVERY ◄────────────────┘
                                                                                                         │
                                                                                                         ▼
                                                                                                 RETURNED (Terminal)
```

### 3.2 Exact Transition Rules Matrix [ENFORCED]

| From State | Allowed Target States | Permitted Roles | Required Conditions & System Actions |
| :--- | :--- | :--- | :--- |
| **`CREATED`** | `CONFIRMED`, `CANCELLED` | `ADMIN`, `MANAGER` | `CONFIRMED`: Shipment details verified.<br>`CANCELLED`: Draft abandoned prior to assignment. |
| **`CONFIRMED`** | `ASSIGNED`, `CANCELLED` | `ADMIN`, `MANAGER` | `ASSIGNED`: Valid available driver and vehicle allocated.<br>`CANCELLED`: Dispatch cancelled. |
| **`ASSIGNED`** | `PICKED_UP`, `CANCELLED` | `ADMIN`, `MANAGER` | `PICKED_UP`: Goods custody accepted at origin facility.<br>`CANCELLED`: Driver/vehicle released. |
| **`PICKED_UP`** | `IN_TRANSIT` | `ADMIN`, `MANAGER` | `IN_TRANSIT`: Freight departs origin facility along transit corridor. |
| **`IN_TRANSIT`** | `OUT_FOR_DELIVERY` | `ADMIN`, `MANAGER` | `OUT_FOR_DELIVERY`: Freight arrives at final local delivery hub/zone. |
| **`OUT_FOR_DELIVERY`** | `DELIVERED`, `FAILED` | `ADMIN`, `MANAGER` | `DELIVERED`: Handover completed. Sets `delivered_at = NOW()`.<br>`FAILED`: Recipient absent or delivery exception encountered. |
| **`FAILED`** | `OUT_FOR_DELIVERY`, `RETURNED` | `ADMIN`, `MANAGER` | `OUT_FOR_DELIVERY`: Re-attempt delivery.<br>`RETURNED`: Goods transported back to facility (Terminal). |
| **`DELIVERED`** | *None* | *None* | **Terminal State**: Cannot transition to any other state. |
| **`CANCELLED`** | *None* | *None* | **Terminal State**: Cannot transition to any other state. |
| **`RETURNED`** | *None* | *None* | **Terminal State**: Cannot transition to any other state. |

### 3.3 Lifecycle Technical Invariants [ENFORCED]
- **Duplicate Status Calls**: If a status update requests the status the shipment is *already in*, the service returns the existing record without raising an error or appending duplicate history.
- **Illegal Status Calls**: Any transition not in `ALLOWED_TRANSITIONS` raises `HTTP 400 Bad Request` with an explicit message listing permitted outbound states.
- **Terminal Immutability**: Shipments in `DELIVERED`, `CANCELLED`, or `RETURNED` cannot have their destination, total weight, total volume, or asset assignments updated via `PUT` or `PATCH`. Requests are rejected with `HTTP 400 Bad Request`.
- **Atomic Audit Trail**: Every status transition MUST write a record to `shipment_status_history` in the same database transaction (`db.commit()`). If history insertion fails, the status change is rolled back.

---

## 4. Inventory Consistency & Stock-Management Rules

1. **[ENFORCED] Warehouse-Product Uniqueness**:
   A database table constraint `uq_warehouse_product` enforces that a warehouse can have at most one inventory record per product ID. Duplicate creation attempts fail with an integrity error.
2. **[ENFORCED] Non-Negative Balances**:
   Inventory quantities on hand cannot be adjusted to negative values. Pydantic validation rejects negative stock counts (`ge=0`).
3. **[ENFORCED] Safety Reorder Threshold**:
   Every inventory line item maintains a `reorder_level` (default 10). When `quantity <= reorder_level`, analytics services flag the line as a low-stock alert.
4. **[PROPOSED] Inventory Reservation & Locking**:
   *Status: Not yet implemented in database models.* In the initial SRS draft, reserving stock on `CONFIRMED` and deducting on `PICKED_UP` was discussed. Currently, `Inventory` has only `quantity` and `reorder_level` without a `quantity_reserved` column. Do not assume automatic inventory deduction occurs on shipment dispatch until an inventory transaction module is formally added.

---

## 5. Facility, Driver, Vehicle & Route Allocation Rules

### 5.1 Warehouse Allocation Rules [ENFORCED]
- Shipments can only be originated from active warehouses (`warehouse.is_active == True`). Specifying an inactive warehouse ID raises `HTTP 400 Bad Request`.

### 5.2 Driver Allocation Rules [ENFORCED]
- Driver must exist in the `drivers` table.
- Driver user account must be active (`driver.user.is_active == True`).
- Driver operational status cannot be `OFF_DUTY` or `SUSPENDED`. Attempting to assign an off-duty or suspended driver raises `HTTP 400 Bad Request`.

### 5.3 Vehicle Allocation Rules [ENFORCED]
- Vehicle must exist in the `vehicles` table.
- Vehicle status cannot be `MAINTENANCE` or `DECOMMISSIONED`. Attempting assignment raises `HTTP 400 Bad Request`.

### 5.4 Route Corridor Allocation Rules [ENFORCED]
- A shipment can be linked to a route via `POST /api/v1/routes/{id}/shipments`.
- The association table enforces `uq_route_shipment`: the same shipment cannot be linked to the same route multiple times.
- Both the route and shipment must exist; missing either raises `HTTP 404 Not Found`.

---

## 6. Vehicle Capacity & Weight Invariants

### 6.1 Carrying Capacity Invariant [ENFORCED]
Under no operational circumstances may freight weight exceed the assigned vehicle's licensed maximum weight capacity.
- **Rule**: If `shipment.total_weight_kg > vehicle.capacity`, assignment is rejected with:
  `HTTP 400 Bad Request: "Shipment weight (X kg) exceeds vehicle carrying capacity (Y kg)"`.
- **Enforcement Points**: Checked at shipment creation (`POST /shipments`) and during shipment modification (`PUT/PATCH /shipments/{id}`).

---

## 7. Tracking & Timestamp Semantics

1. **[ENFORCED] Authentic System Timestamps**:
   - `created_at`: Persisted by database default (`func.now()`).
   - `delivered_at`: Set automatically to `datetime.now(timezone.utc)` upon transitioning to `DELIVERED`. Never set manually by callers.
2. **[ENFORCED] Checkpoint Timestamps**:
   Every record in `shipment_tracking_events` records an explicit ISO timestamp and records the creating user's ID.
3. **[CRITICAL INVARIANT] Never Substitute Timestamps**:
   Never substitute scheduled timestamps (`scheduled_pickup_at`) for actual event timestamps (`actual_pickup_timestamp`). If an actual milestone has not occurred, the field must remain `None` / `null`. Substituting scheduled dates corrupts duration metrics and introduces catastrophic data leakage.

---

## 8. Authentication, Password Security & Token Invariants

1. **[ENFORCED] Argon2id Hashing**:
   All user passwords must be hashed using `pwdlib` with Argon2id recommended parameters. The plain-text password must never be stored, logged, or returned in any API response schema.
2. **[ENFORCED] Stateless JWT Tokens**:
   Access tokens are signed using HMAC-SHA256 with the application `SECRET_KEY`. Tokens carry `sub` (user ID) and `role` claims with a defined expiration (24 hours).
3. **[ENFORCED] Deactivated Account Block**:
   If a user has `is_active = False`, all authenticated requests must immediately fail with `HTTP 400 Bad Request` ("User account is deactivated").
4. **[ENFORCED] No Hardcoded Secrets**:
   Production `SECRET_KEY` and `DATABASE_URL` must be loaded exclusively through `.env` via `pydantic-settings`. Default fallback secrets are permitted only in local development/test environments.

---

## 9. Role-Based Access Control (RBAC) Invariants

Role permissions are strictly verified through `require_roles()` in `backend/app/api/deps.py`:

```python
# Allowed User Roles
UserRole.ADMIN    # Global platform administrator
UserRole.MANAGER  # Logistics operations and dispatch coordinator
UserRole.DRIVER   # Field transport personnel
UserRole.VIEWER   # Read-only stakeholder and auditor
```

### 9.1 RBAC Invariant Matrix [ENFORCED]
- **Administrative Deletions**: Deletion endpoints (`DELETE /warehouses/{id}`, `/products/{id}`, `/inventory/{id}`, `/drivers/{id}`, `/vehicles/{id}`, `/shipments/{id}`, `/routes/{id}`) require `require_roles([UserRole.ADMIN])`. Managers, Drivers, and Viewers receive `HTTP 403 Forbidden`.
- **Dispatch Operations**: Creating and modifying shipments, routes, facilities, and inventory requires `require_roles([UserRole.ADMIN, UserRole.MANAGER])`.
- **Auditing & Tracking**: Read endpoints (`GET`) are open to all authenticated users (`ADMIN`, `MANAGER`, `DRIVER`, `VIEWER`).
- **AI Data Pipeline**: Access to `/api/v1/pipeline/*` is restricted to `ADMIN` and `MANAGER`.

---

## 10. Database Integrity & Constraint Invariants

1. **[ENFORCED] Referential Integrity**:
   All foreign keys must declare explicit `ondelete` strategies. Nullable relationships (like `assigned_driver_id`) use `SET NULL` so deleting a user does not destroy historical shipments. Strong relationships (like `inventories`) use `CASCADE`.
2. **[ENFORCED] Soft Deletions**:
   Entities representing historical logistics assets (`Shipment`, `Route`, `Warehouse`, `Product`) must utilize soft deletion (`is_active = False`) to prevent breaking historical tracking records and analytics aggregations.
3. **[ENFORCED] Relational Model Declarations**:
   All models must inherit from `app.db.base.Base` (SQLAlchemy 2.0 `DeclarativeBase`) and use `Mapped[...]` and `mapped_column(...)` typing annotations.

---

## 11. API Validation & Error-Handling Conventions

1. **[ENFORCED] Schema Validation**:
   All request payloads must be defined as Pydantic models. String fields must have leading and trailing whitespace stripped (`strip()`).
2. **[ENFORCED] Clean HTTP Status Codes**:
   - `200 OK`: Successful retrieval or update.
   - `201 CREATED`: Resource successfully created.
   - `400 BAD REQUEST`: Business validation failed (e.g. invalid status transition, weight capacity exceeded).
   - `401 UNAUTHORIZED`: Authentication credentials missing, invalid, or expired.
   - `403 FORBIDDEN`: Valid credentials supplied, but user role lacks authorization.
   - `404 NOT FOUND`: Target entity does not exist.
   - `422 UNPROCESSABLE ENTITY`: Inbound payload failed Pydantic schema validation.
   - `500 INTERNAL SERVER ERROR`: Unhandled database or system exception (sanitized response).
3. **[ENFORCED] Sanitized Internal Exceptions**:
   Never allow raw SQLAlchemy traces, table structures, or Python stack frames to be returned to HTTP clients.

---

## 12. Coding Conventions (Backend & Frontend)

### 12.1 Backend Conventions
- **Explicit Type Hints**: All Python function signatures must declare argument and return types (e.g., `def get_shipment(db: Session, shipment_id: int) -> Shipment:`).
- **Comprehensive Docstrings**: Every module, class, and service function must include a clear docstring explaining purpose, parameters, and exceptions.
- **Repository-Service Separation**:
  - Repositories (`app/repositories/`) execute database queries and return models.
  - Services (`app/services/`) execute business logic, validations, and state machine transitions.
  - Routers (`app/api/`) handle HTTP request deserialization, authorization dependencies, and response formatting.

### 12.2 Frontend Conventions
- **Vanilla CSS Design System**: Style all components using existing CSS variables in `frontend/src/index.css` (e.g., `var(--bg-main)`, `var(--primary-blue)`, `var(--ai-cyan)`). Do not install Tailwind or ad-hoc utility classes.
- **Error Formatting**: Always route API errors through `formatErrorMessage()` in `src/api/client.js` to parse FastAPI Pydantic 422 error arrays cleanly.
- **Role Gating in UI**: Wrap privileged actions in `<RoleGate allowed={['ADMIN', 'MANAGER']}>` or disable buttons with descriptive tooltips.

---

## 13. Testing & Quality Verification Requirements

1. **[ENFORCED] Zero-Broken Tests Policy**:
   No code may be committed that breaks any of the **278 backend tests** (`pytest`) or **43 frontend tests** (`npm test`).
2. **[ENFORCED] Isolated SQLite Test Execution**:
   Backend tests must execute using the in-memory SQLite fixture (`sqlite:///:memory:`) and `override_get_db`. Tests must never depend on a persistent external database or mutate development seed data.
3. **[ENFORCED] Honest Test Reporting**:
   Never claim tests passed without executing them. Always record actual command output and execution time.

---

## 14. Data Privacy & Sensitive-Information Handling

1. **[ENFORCED] ML Dataset PII Redaction**:
   The AI data pipeline (`app/pipeline/feature_extractor.py`) MUST strip:
   - User emails, phone numbers, and full names.
   - Driver license numbers (`license_number`).
   - Street addresses (retaining only destination city, state, postal code).
   - Password hashes.
2. **[ENFORCED] Safe Logging**:
   Loggers must never print plain-text passwords, JWT tokens, or database credentials.

---

## 15. AI/ML Data-Quality & Model-Safety Rules

1. **[CRITICAL] Deterministic Heuristics vs. Statistical ML**:
   The delay-risk score (0–100) produced by `DelayRiskService` is a **deterministic heuristic index**, NOT a calibrated statistical probability. Never market or label this score as an empirical probability. Responses must include `is_calibrated_probability = False`.
2. **[CRITICAL] Anti-Leakage Quarantine**:
   When extracting features for machine learning:
   - Undelivered shipments MUST have `None` for target variables (`actual_duration_hours`, `is_delayed`, `delay_hours`).
   - Target variables must NEVER be computed from data or status remarks logged after dispatch.
3. **[CRITICAL] No Fictional Model Claims**:
   Never display fictional marketing claims (such as *"gradient boosting regression trained on 42k legs with 96.4% precision"*) in production UI. Acknowledge real operational data readiness honestly.
4. **[CRITICAL] Chronological Partitioning**:
   Train/test splits must be partitioned chronologically by creation timestamp, never randomly shuffled, to prevent temporal lookahead leakage.

---

## 16. Prohibited Shortcuts & Anti-Patterns

- **PROHIBITED**: Bypassing the state machine by directly updating `Shipment.status` without calling `ShipmentService.update_shipment_status()`.
- **PROHIBITED**: Modifying database records directly in route handlers instead of going through the Service and Repository layers.
- **PROHIBITED**: Fabricating seed records with bogus delivery durations to trick the ML quality checker.
- **PROHIBITED**: Disabling CORS or JWT checks to quickly resolve frontend communication errors.
- **PROHIBITED**: Storing plain-text API secrets or database credentials in source control.
- **PROHIBITED**: Performing destructive schema migrations (`alembic downgrade`) in development without preserving schema history.

---

## 17. Mandatory Rules for AI Coding Agents

Future AI coding agents modifying FlowGrid MUST adhere to the following ten directives:

1. **Inspect Relevant Code First**:
   Read and verify existing models, schemas, services, and tests before writing or editing any code.
2. **Follow Layered Architecture**:
   Maintain the established `Routers -> Services -> Repositories -> Models` pattern. Place business rules in Services, not Routers.
3. **Reuse Existing Entities & Schemas**:
   Check `app/schemas/` and `app/repositories/` before creating duplicate schemas, repositories, or utility functions.
4. **Focus Exclusively on Requested Work**:
   Do not introduce sweeping unrelated refactors, rename functioning database columns, or reformat untouched files.
5. **Preserve State Machine & RBAC Invariants**:
   Never relax or remove `require_roles` or `ALLOWED_TRANSITIONS` checks to make a feature work.
6. **Add or Update Tests for Meaningful Changes**:
   Every new endpoint, schema modification, or service method must include corresponding pytest or Node.js tests.
7. **Execute Relevant Test Suites**:
   Run `pytest` and `npm test` after making changes to verify zero regressions.
8. **Report Actual Results Honestly**:
   State real command output, pass counts, warnings, and failures. Never report hypothetical or unverified success.
9. **Synchronize Documentation**:
   Update `PRD.md`, `ARCHITECTURE.md`, `RULES.md`, `DESIGN.md`, `TASKS.md`, and `MEMORY.md` whenever APIs, schemas, or implementation states change.
10. **Ask for Clarification When Uncertain**:
    If an essential business decision or requirement cannot be established from the repository, ask the user before guessing.
