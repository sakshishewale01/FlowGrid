# FlowGrid — Project Technical Memory & Developer Context

> **Durable Technical Knowledge Base for Developers & AI Coding Agents**  
> *Status:* Production Baseline • *Updated:* October 2026 • *Location:* `docs/MEMORY.md`

---

## 1. Project Overview & Identity

**FlowGrid** is a full-stack, enterprise-grade **Smart Logistics Control Tower & Transportation Management System (TMS)**.

### Core Objectives
- Unify multi-facility warehouse storage and inventory tracking.
- Enforce an immutable 5-stage shipment lifecycle state machine (`PENDING` $\to$ `DELIVERED`).
- Validate payload weight capacity against assigned vehicle limits prior to dispatch.
- Broadcast real-time milestone telemetry via WebSockets to connected operator cockpits.
- Provide explainable rule-based exception triage (Shipment Rescue Center) and sandbox What-If simulations.
- Serve a grounded natural language assistant backed strictly by real API data.
- Run an authenticated ML delay prediction pipeline (`POST /api/v1/ml/predict-delay`) with transparent synthetic baselines.

---

## 2. Verified Technology Stack

| Layer | Technologies & Libraries | Key Packages / Specs |
| :--- | :--- | :--- |
| **Backend Runtime** | Python 3.11+ / 3.14 | FastAPI (`>=0.110.0`), Uvicorn (`>=0.28.0`) |
| **Database & ORM** | PostgreSQL 15+ / SQLite (Tests) | SQLAlchemy (`>=2.0.0`), psycopg3 (`psycopg[binary]`), Alembic (`>=1.13.0`) |
| **Security & Auth** | Argon2id & JWT | `pwdlib[argon2]`, `PyJWT` (HMAC-SHA256, 15m–24h expiry) |
| **Data Validation** | Pydantic v2 | `pydantic (>=2.6.0)`, `pydantic-settings` |
| **Machine Learning**| Scikit-Learn | `scikit-learn (>=1.4.0)`, `joblib`, Random Forest Pipeline |
| **Frontend Stack** | React 18/19 SPA + Vite | React (`^19.2.8`), Vite (`^8.3.0`), Leaflet (`^1.9.4`), Vanilla CSS |
| **Test Suites** | Node.js Test Runner & Pytest | `node --test` (46 frontend tests), `pytest` (backend test suite) |

---

## 3. Directory Layout & Architecture Map

```text
FlowGrid/
├── backend/
│   ├── alembic/              # Database migration version scripts
│   ├── app/
│   │   ├── api/v1/           # Modular FastAPI routers (auth, shipments, warehouses, ml, etc.)
│   │   ├── core/             # App settings, security, and logging config
│   │   ├── db/               # SQLAlchemy engine, session maker, base model
│   │   ├── models/           # SQLAlchemy 2.0 ORM models (User, Shipment, Warehouse, etc.)
│   │   ├── pipeline/         # ML feature extractor & data quality reporting
│   │   ├── repositories/     # Data query layer with soft-deletes and filters
│   │   ├── schemas/          # Pydantic v2 request/response schemas
│   │   ├── services/         # Business logic (ShipmentService, DelayRiskService, etc.)
│   │   └── main.py           # FastAPI entrypoint, CORS, and WebSocket manager
│   ├── ml_exports/           # Trained pipeline artifacts (rf_pipeline.joblib)
│   ├── tests/                # Pytest automated test suite
│   └── requirements.txt      # Locked Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api/              # Domain API clients (shipments, warehouses, ml, etc.)
│   │   ├── components/       # TopNavbar, Sidebar, Modals, QuickActions, DataTables
│   │   ├── context/          # AuthContext, NotificationContext, ToastContext
│   │   ├── pages/            # Feature views (RescueCenter, Simulator, Analytics, etc.)
│   │   ├── utils/            # Geo-coordinate parsing & CSV export sanitizers
│   │   ├── App.jsx           # App shell, client router & Control Tower dashboard
│   │   ├── index.css         # Design tokens, Dark (#0B1220) & Light (#F1F5F9) themes
│   │   └── main.jsx          # React DOM entrypoint
│   ├── tests/                # 46 automated frontend unit & integration tests
│   └── package.json          # Node scripts and dependencies
│
└── docs/                     # Authoritative documentation (PRD, ARCHITECTURE, DESIGN, RULES)
```

---

## 4. Key Architectural Conventions

1. **Layered Monolith Pattern**:
   `Request -> Router -> Dependencies (Auth/RBAC) -> Service -> Repository -> Model -> PostgreSQL`.  
   *Never invoke raw SQL or database queries directly inside route handlers.*
2. **Lifecycle State Machine Governance**:
   Shipment status transitions must route through `ShipmentService.update_shipment_status()`, which enforces `ALLOWED_TRANSITIONS` and logs an immutable audit trail in `ShipmentStatusHistory`.
   - Allowed lifecycle: `PENDING` $\to$ `DISPATCHED` $\to$ `IN_TRANSIT` $\to$ `OUT_FOR_DELIVERY` $\to$ `DELIVERED` (or `FAILED`).
3. **Payload Capacity Safety**:
   `ShipmentService` automatically validates that `shipment.total_weight_kg <= vehicle.capacity` on shipment creation and driver/vehicle assignment.
4. **Deterministic Rule Engine (Shipment Rescue Center)**:
   Exceptions are flagged using deterministic logic grounded strictly in database fields (`RULE-EX01`, `RULE-R01` to `RULE-R04`) rather than opaque black-box AI.
5. **Non-Destructive Simulation (What-If Simulator)**:
   The disruption simulator runs client-side in an isolated memory sandbox against live database records without mutating production data.
6. **Grounded Logistics Assistant**:
   The conversational companion fetches verified records from authenticated backend endpoints (`/shipments`, `/warehouses`, `/drivers`, `/vehicles`, `/analytics`) before generating responses.
7. **Dual-Theme Design System**:
   Theme state persists in `localStorage` (`flowgrid_theme`) and applies via `document.documentElement.setAttribute('data-theme', theme)`. An inline script in `index.html` prevents theme flashing on load.

---

## 5. Role-Based Access Control (RBAC) Matrix

| Action | Admin | Manager | Driver | Viewer |
| :--- | :---: | :---: | :---: | :---: |
| **System Settings & Health Probes** | ✅ | ✅ | ❌ | ❌ |
| **Create / Deactivate Warehouses** | ✅ | ❌ | ❌ | ❌ |
| **Stock Adjustments & Inventory CRUD** | ✅ | ✅ | ❌ | ❌ |
| **Shipment Creation & Status Updates** | ✅ | ✅ | ❌ | ❌ |
| **Execute Rescue Center Interventions**| ✅ | ✅ | ❌ | ❌ |
| **Update Own Driver Duty Status** | ✅ | ✅ | ✅ | ❌ |
| **Run Disruption Simulations** | ✅ | ✅ | ❌ | 👁️ Read-Only |
| **Query Logistics Assistant** | ✅ | ✅ | ✅ | ✅ |
| **Export RFC 4180 CSV Manifests** | ✅ | ✅ | ✅ | ✅ |

---

## 6. Verified Developer Commands

### Backend Commands
```bash
# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1  # Windows PowerShell
source backend/venv/bin/activate     # Linux / macOS

# Run FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Apply database migrations
alembic upgrade head

# Run backend test suite
pytest -v
```

### Frontend Commands
```bash
cd frontend

# Install dependencies
npm install

# Run Vite development server
npm run dev

# Run automated frontend test suite (46 tests)
npm test

# Production bundle build
npm run build
```

### Pre-Configured Demo Accounts
- **Admin**: `admin@flowgrid.io` / `FlowGrid2026!`
- **Manager**: `manager@flowgrid.io` / `FlowGrid2026!`
- **Driver**: `driver@flowgrid.io` / `FlowGrid2026!`
- **Viewer**: `viewer@flowgrid.io` / `FlowGrid2026!`
