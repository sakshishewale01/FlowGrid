# FlowGrid — Project Technical Memory & Developer Context
**Durable Engineering Knowledge Base for Human Developers & AI Coding Agents**

*Document Version:* 1.0.0  
*Status:* Authoritative Technical Memory  
*Last Updated:* October 2026  
*Location:* `docs/MEMORY.md`

---

## 1. Project Identity & Objective

**FlowGrid** is a full-stack, enterprise-grade **Intelligent Logistics & Transportation Management Platform** operating as an **Operational Logistics Control Tower**.

Its primary operational objectives are:
- Centralize multi-facility warehouse storage and inventory tracking.
- Enforce a strict finite state machine across the commercial shipment lifecycle (`CREATED` $\to$ `DELIVERED`).
- Guarantee equipment payload safety by enforcing vehicle carrying capacity limits.
- Deliver real-time milestone telemetry via WebSockets to connected operations dashboards.
- Provide deterministic, explainable operational delay-risk intelligence (0–100 index).
- Lay an anti-leakage data foundation for future statistical machine learning.

---

## 2. Repository & Directory Structure

```text
FlowGrid/
├── backend/
│   ├── alembic/              # Database migration environment
│   │   └── versions/         # 4 version-controlled migration scripts
│   ├── app/
│   │   ├── api/              # FastAPI router controllers and request dependencies
│   │   │   ├── deps.py       # Reusable dependencies (get_db, require_roles, get_current_user)
│   │   │   └── v1/           # API v1 endpoints (auth, shipments, analytics, etc.)
│   │   ├── core/             # Configuration (pydantic-settings), logging, and security (Argon2/JWT)
│   │   ├── db/               # SQLAlchemy engine, DeclarativeBase, SessionLocal
│   │   ├── models/           # 10 pure SQLAlchemy 2.0 ORM models
│   │   ├── pipeline/         # AI data pipeline (FeatureExtractor, QualityChecker, Exporter)
│   │   ├── repositories/     # Data access layer (CRUD queries, filters, joins)
│   │   ├── schemas/          # Pydantic v2 validation and serialization schemas
│   │   ├── services/         # Domain business logic (ShipmentService, DelayRiskService, etc.)
│   │   └── main.py           # FastAPI application entrypoint and middleware
│   ├── ml_exports/           # Exported ML datasets and data_quality_report.json
│   ├── scripts/              # Seed fixtures (seed_demo_data.py) and export CLI (export_ml_dataset.py)
│   ├── tests/                # 18 pytest automated test modules (278 passing tests)
│   ├── Dockerfile            # Multi-stage production container specification
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── api/              # Domain API clients (shipments.js, client.js, analytics.js, etc.)
│   │   ├── components/       # 30 modular React components (ShipmentDetailDrawer, DataTable, etc.)
│   │   ├── context/          # React Contexts (AuthContext, ToastContext, NotificationContext)
│   │   ├── hooks/            # Custom hooks (useDashboardData, useTrackingWebSocket)
│   │   ├── pages/            # 6 management views (ShipmentsPage, WarehousesPage, etc.)
│   │   ├── utils/            # Geographic coordinates and CSV formatting utilities
│   │   ├── App.jsx           # Root layout and client-side router
│   │   ├── main.jsx          # React DOM mount entrypoint
│   │   └── index.css         # Custom Deep Tech Blue design tokens and styling (Vanilla CSS)
│   ├── tests/                # 7 Node.js test runner modules (43 automated tests)
│   ├── package.json          # Node dependencies (React 19, Leaflet, Vite, Oxlint)
│   └── vite.config.js        # Vite configuration
│
├── docs/                     # Authoritative Project Documentation Suite
│   ├── PRD.md                # Product Requirements Document
│   ├── ARCHITECTURE.md       # System Architecture & Technical Specifications
│   ├── RULES.md              # Enforced Business Rules, Invariants & AI Agent Directives
│   ├── DESIGN.md             # Design System Tokens, UI Layouts & UX Principles
│   ├── TASKS.md              # Phased Implementation Roadmap & Progress Tracker
│   └── MEMORY.md             # (This file) Compact Technical Knowledge Base
│
├── README.md                 # Root project overview and local quickstart
└── .gitignore                # Source control ignore rules
```

---

## 3. Verified Technology Stack

- **Backend Runtime**: Python 3.11+ / 3.14 (FastAPI `>=0.110.0`, Uvicorn `>=0.28.0`).
- **Database Layer**: PostgreSQL 15+ (Production) / In-Memory SQLite (Automated Tests).
- **ORM & Migrations**: SQLAlchemy `>=2.0.0` (Declarative mapping), psycopg 3 (`psycopg[binary] >=3.1.18`), Alembic `>=1.13.0`.
- **Security & Tokens**: `pwdlib[argon2] >=0.2.0` (Argon2id password hashing), `pyjwt >=2.8.0` (HMAC-SHA256 JWT tokens).
- **Validation**: Pydantic `>=2.6.0`, `pydantic-settings >=2.2.0`, `email-validator >=2.0.0`.
- **Frontend Stack**: React `^19.2.8`, Vite `^8.3.0`, Leaflet `^1.9.4`, Vanilla CSS custom design system, Oxlint `^1.81.0`.

---

## 4. Key Implementation Conventions

1. **Layered Monolith Pattern**:
   `HTTP Request -> Middleware -> Router -> Dependencies (RBAC/Auth) -> Service -> Repository -> Model -> Database`.
   *Never issue raw database queries from route handlers.*
2. **State Machine Exclusivity**:
   All status updates must execute via `ShipmentService.update_shipment_status()`, which enforces `ALLOWED_TRANSITIONS` and writes an atomic audit record in `ShipmentStatusHistory`.
3. **Payload Capacity Safety**:
   `ShipmentService` automatically verifies `shipment.total_weight_kg <= vehicle.capacity` on create and update.
4. **WebSocket Concurrency Defense**:
   `ConnectionManager` enforces a hard limit of 50 concurrent sockets per shipment and 1,000 globally to prevent Denial of Service.
5. **No External CSS Frameworks**:
   Frontend styles exclusively utilize CSS Custom Properties defined in `frontend/src/index.css` (e.g. `var(--bg-main)`, `var(--primary-blue)`, `var(--ai-cyan)`).

---

## 5. Subsystem Directory Quick-Reference

| Domain Subsystem | Database Model | Pydantic Schema | Repository | Service | API Router |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `models/user.py` | `schemas/auth.py`, `schemas/user.py` | *(In deps/service)* | `core/security.py` | `endpoints/auth.py` |
| **Warehouses** | `models/warehouse.py`| `schemas/warehouse.py` | `warehouse_repository.py` | `warehouse_service.py` | `endpoints/warehouses.py` |
| **Products** | `models/product.py` | `schemas/product.py` | `product_repository.py` | `product_service.py` | `endpoints/products.py` |
| **Inventory** | `models/inventory.py`| `schemas/inventory.py` | `inventory_repository.py` | `inventory_service.py` | `endpoints/inventory.py` |
| **Drivers** | `models/driver.py` | `schemas/driver.py` | `driver_repository.py` | `driver_service.py` | `endpoints/drivers.py` |
| **Vehicles** | `models/vehicle.py` | `schemas/vehicle.py` | `vehicle_repository.py` | `vehicle_service.py` | `endpoints/vehicles.py` |
| **Shipments** | `models/shipment.py`| `schemas/shipment.py` | `shipment_repository.py` | `shipment_service.py` | `endpoints/shipments.py` |
| **Tracking/Events**| `models/tracking.py`| `schemas/tracking.py` | `tracking_repository.py` | `tracking_service.py` | `endpoints/shipments.py` |
| **Routes** | `models/route.py` | `schemas/route.py` | `route_repository.py` | `route_service.py` | `endpoints/routes.py` |
| **Analytics/Risk** | *(Multi-entity)* | `schemas/analytics.py` | `analytics_repository.py` | `analytics_service.py`, `delay_risk_service.py` | `endpoints/analytics.py` |
| **AI Pipeline** | *(Multi-entity)* | `pipeline/schema.py` | *(Queries via pipeline)*| `dataset_generator.py`, `feature_engineer.py` | `endpoints/pipeline.py` |
| **WebSockets** | *(In-memory)* | *(JSON events)* | N/A | `connection_manager.py`| `endpoints/ws_tracking.py` |

---

## 6. Database & Persistence Overview

- **Database Name**: `flowgrid_db` (PostgreSQL default port `5432`).
- **Migration Strategy**: Version-controlled through Alembic:
  - `alembic upgrade head` applies all pending migrations.
  - `alembic revision --autogenerate -m "description"` generates migrations from model alterations.
- **Entity Tables**:
  - `users`: Core credentials, roles (`ADMIN`, `MANAGER`, `DRIVER`, `VIEWER`), active status.
  - `warehouses`: Facility profiles, square footage capacity, locations.
  - `products`: Commercial items, unique `sku`, unit prices.
  - `inventories`: Stock balances, unique constraint `(warehouse_id, product_id)`.
  - `drivers`: Linked 1-to-1 to `users`, CDL `license_number`, availability status.
  - `vehicles`: Fleet transport units, `registration_number`, weight `capacity`, maintenance status.
  - `shipments`: Freight dispatches, `tracking_number`, gross weight/volume, status enum.
  - `shipment_status_history`: Immutable state machine audit trail with timestamps and user IDs.
  - `shipment_tracking_events`: Physical milestone checkpoints and geolocation descriptions.
  - `routes`: Transit corridors, origin, destination, estimated distance and duration.
  - `route_shipments`: Association table linking shipments to routes with uniqueness constraint.

---

## 7. Authentication & Authorization Conventions

- **Password Storage**: Argon2id via `pwdlib.PasswordHash.recommended()`. Plaintext passwords or hashes are never returned by API responses.
- **JWT Tokens**: HMAC-SHA256 Bearer tokens carrying `sub` (user ID) and `role`. Default expiration is 24 hours.
- **RBAC Enforcement**: Use `require_roles([UserRole.ADMIN, UserRole.MANAGER])` in endpoint function arguments.
- **Role Permission Summary**:
  - `ADMIN`: Full CRUD across all entities, soft-deletions, settings.
  - `MANAGER`: Operations CRUD across warehouses, inventory, drivers, vehicles, shipments, routes; no deletion rights.
  - `DRIVER`: Read-only access to dispatches, assigned shipment telemetry.
  - `VIEWER`: Read-only access across logistics records and analytics.

---

## 8. Important API Prefixes & Entry Points

- Root Base: `http://127.0.0.1:8000`
- Interactive OpenAPI Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- System Probes:
  - Liveness: `GET /health`
  - Database Probe: `GET /health/db`
  - API Greeting: `GET /`
- Version 1 API Prefix: `/api/v1`
  - `/api/v1/auth`: Authentication and profiles
  - `/api/v1/shipments`: Dispatches, state machine, history, and checkpoints
  - `/api/v1/analytics`: 9 KPI and explainable delay-risk endpoints
  - `/api/v1/pipeline`: ML feature registry, quality reports, dataset generation
- WebSocket Telemetry: `ws://127.0.0.1:8000/ws/tracking/{shipment_id}`

---

## 9. Current Verified Feature Status

| Capability | Status | Reference |
| :--- | :--- | :--- |
| **Authentication & RBAC** | Verified & Enforced | [`test_auth.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_auth.py) |
| **Core Logistics CRUD** | Verified & Enforced | `test_warehouses.py`, `test_products.py`, etc. |
| **Shipment State Machine** | Verified & Enforced | [`test_shipments.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_shipments.py) |
| **Audit Status History Trail** | Verified & Enforced | [`test_tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_tracking.py) |
| **WebSocket Real-Time Hub** | Verified & Enforced | [`test_websocket_tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_websocket_tracking.py) |
| **Analytics KPI Engine** | Verified & Enforced | [`test_analytics.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_analytics.py) |
| **Explainable Delay Risk Scoring**| Verified & Enforced | [`test_delay_risk.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_delay_risk.py) |
| **AI Data Pipeline & Export** | Verified & Enforced | [`test_ml_pipeline.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_ml_pipeline.py) |
| **Statistical ETA Regression ML**| **BLOCKED (0 Targets)** | See [`docs/TASKS.md`](./TASKS.md#6-blocked-work--critical-dependencies) |
| **Binary Delay Classification ML**| **BLOCKED (0 Targets)** | See [`docs/TASKS.md`](./TASKS.md#6-blocked-work--critical-dependencies) |

---

## 10. Known Limitations & Technical Debt

1. **Missing `estimated_delivery_at`**: `Shipment` database model lacks a dedicated estimated arrival timestamp column.
2. **Initial Seed Fixture Sparse Data**: `seed_demo_data.py` created 6 shipments without corresponding `shipment_status_history` transitions or `route_shipments` links.
3. **No Direct Line-Item Join Table**: `Shipment` tracks gross weight and volume directly rather than joining to a `shipment_items` table.
4. **Mock Copy in UI**: `mockLogisticsData.js` contains fictional text claiming trained scikit-learn models exist.

---

## 11. Important Architectural Decisions & Rationale

- **Decoupled Monolith**: Chosen over microservices to avoid distributed transaction failures, network latency, and complex deployment orchestration for a student/mid-market project.
- **Argon2id over Bcrypt**: Selected because Argon2id is the winner of the Password Hashing Competition (PHC) and offers state-of-the-art resistance to GPU cracking attacks.
- **Vanilla CSS Tokens over Tailwind**: Selected to provide maximum custom styling control for an authentic "Deep Tech Blue" operations console without bundler plugin overhead or version drift.
- **Deterministic Heuristic Risk Index over Naive ML**: Implemented in Phase 24.2 because the current database lacks authentic historical duration targets; heuristic scoring provides 100% transparent, explainable operational value immediately without hallucinating ML predictions.

---

## 12. Local Setup Prerequisites & Verified Commands

### Prerequisites
- Python 3.11+ (Python 3.12 or 3.14 verified)
- Node.js 18+ (Node 20+ recommended)
- PostgreSQL 15+ running on port `5432` with database `flowgrid_db`

### Backend Setup & Test Commands
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Seed development fixtures
python scripts/seed_demo_data.py

# Run complete backend automated test suite (278 tests)
pytest

# Run tests with verbose output
pytest -v

# Start development API server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup & Test Commands
```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install packages
npm install

# Run automated tests (43 tests)
npm test

# Run code linter
npm run lint

# Start Vite development server
npm run dev
```

---

## 13. Critical Files to Inspect Before Modifying Subsystems

- **Authentication / Permissions**: [`backend/app/api/deps.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/deps.py), [`backend/app/core/security.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/core/security.py).
- **Shipments / State Machine**: [`backend/app/services/shipment_service.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/shipment_service.py), [`backend/app/models/shipment.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py).
- **WebSockets / Live Telemetry**: [`backend/app/services/connection_manager.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/connection_manager.py), [`backend/app/api/v1/endpoints/ws_tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/api/v1/endpoints/ws_tracking.py).
- **Delay Risk Engine**: [`backend/app/services/delay_risk_service.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/services/delay_risk_service.py), [`backend/tests/test_delay_risk.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/tests/test_delay_risk.py).
- **Frontend Operational Drawer**: [`frontend/src/components/ShipmentDetailDrawer.jsx`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/components/ShipmentDetailDrawer.jsx).
- **Design Tokens & Theme**: [`frontend/src/index.css`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/index.css).

---

## 14. Current Next Task & Dependencies

- **Immediate Task**: `TASK-DATA-01` (Add `estimated_delivery_at` column to `Shipment` model and generate Alembic migration).
- **Next Follow-up**: `TASK-DATA-02` (Update `seed_demo_data.py` to create realistic status history milestones and route allocations).
- **Target Outcome**: Unblock Phase C operational data quality checks so `DataQualityChecker` marks the dataset valid for training.

---

## 15. Links to the Other Documentation Files

- [Product Requirements Document (PRD)](./PRD.md): Product vision, stakeholder personas, functional requirements, and success metrics.
- [System Architecture (ARCHITECTURE.md)](./ARCHITECTURE.md): Technology stack, Mermaid component diagrams, request lifecycles, and database schemas.
- [System Rules & Invariants (RULES.md)](./RULES.md): Business invariants, state transitions, capacity constraints, and AI coding agent rules.
- [UI/UX Design System (DESIGN.md)](./DESIGN.md): Design tokens, Deep Tech Blue styling, component catalog, and responsive layouts.
- [Implementation Tasks (TASKS.md)](./TASKS.md): Current implementation baseline, roadmap phases A–F, and Definition of Done.

---

## 16. How to Resume Work (For a New Developer or AI Agent)

When starting a new work session on FlowGrid:
1. **Read `docs/MEMORY.md`** (this document) to understand the project architecture and technology stack.
2. **Check `docs/TASKS.md`** to identify the current top priority task (`TASK-DATA-01`).
3. **Review `docs/RULES.md`** to ensure you do not violate any state machine invariants, RBAC boundaries, or coding conventions.
4. **Run `pytest tests/test_health.py`** to confirm your local backend Python environment is operational.
5. **Run `npm test`** in `frontend/` to confirm the frontend test runner is clean.
6. **Focus exclusively on the requested task**, adding corresponding tests and updating `TASKS.md` upon completion.
