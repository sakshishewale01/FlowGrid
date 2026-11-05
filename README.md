# FlowGrid

## Intelligent Logistics and Supply Chain Management Platform

FlowGrid is a full-stack logistics control tower for managing warehouses, products,
inventory, drivers, vehicles, shipments, routes, tracking, analytics, and
decision-support workflows.

This README is the current project status and repository guide. It describes the
implementation currently present in the repository, not only the original plan.



## Current implementation status

### Completed and integrated

- **Authentication and authorization**
  - User registration and login
  - JWT access tokens
  - Argon2 password hashing
  - Role-based access control for `ADMIN`, `MANAGER`, `DRIVER`, and `VIEWER`
  - Protected HTTP and WebSocket resources
- **Warehouse management**
  - Warehouse CRUD operations
  - Capacity and active-status tracking
  - Warehouse utilization analytics
- **Product and inventory management**
  - Product catalog and SKU management
  - Warehouse-level inventory records
  - Stock adjustments, reorder levels, and low-stock detection
- **Fleet management**
  - Driver records, license data, phone data, and availability
  - Vehicle records, types, capacity, and operational status
  - Driver and vehicle assignment workflows
- **Shipment operations**
  - Shipment creation, listing, detail, update, and assignment
  - Lifecycle state-machine validation
  - Capacity checks before dispatch
  - Estimated delivery timestamps
  - Terminal-state safeguards
- **Tracking and routes**
  - Route and freight-corridor management
  - Shipment-to-route allocation
  - Tracking events and immutable status history
  - Authenticated real-time shipment tracking over WebSocket
- **Analytics**
  - Overview KPIs
  - Shipment, warehouse, inventory, route, driver, and vehicle analytics
  - Operational risk and low-stock indicators
- **AI-ready data pipeline**
  - Dataset generation from operational records
  - Feature extraction and engineering
  - Data-quality checks and pipeline schemas
  - Dataset export scripts and generated ML datasets
- **Delay-risk machine learning prototype**
  - Scikit-learn Random Forest pipeline
  - India logistics benchmark dataset
  - Model artifact loading and cached inference
  - Delay probability and `LOW`/`MEDIUM`/`HIGH` risk bands
  - API integration at `POST /api/v1/ml/predict-delay`
- **Grounded logistics assistant**
  - Authenticated assistant API
  - Operational responses based on application data
  - Frontend assistant modal and insight panels
- **Frontend control tower**
  - React and Vite single-page application
  - Login, registration, protected routes, role gates, and settings
  - Dashboard KPI cards and live shipment flow map
  - Warehouses, inventory, drivers, vehicles, shipments, routes, and analytics pages
  - Rescue Center and disruption simulator workflows
  - Notifications, toasts, loading states, empty states, error boundary, and modals
  - Leaflet-based route and shipment maps
  - Shipment CSV export with sensitive-field sanitization
  - Dark/light operational UI styling
- **Operational hardening**
  - CORS configuration
  - Security response headers
  - Request timing headers and structured logging
  - Sanitized database and unexpected-error responses
  - WebSocket authentication, RBAC, and connection limits
- **Database and migrations**
  - SQLAlchemy 2.x models and repositories
  - PostgreSQL configuration through `DATABASE_URL`
  - SQLite-compatible local/test operation
  - Alembic migration history for core logistics, shipments, tracking, routes,
    and estimated delivery timestamps
  - Development seed data and demo accounts

### Prototype and operational limitations

- The delay model is a **prototype decision-support model**, not a production
  carrier-performance predictor. Its labels come from a synthetic benchmark
  dataset and must not be interpreted as real-world Indian freight history.
- The frontend integration tests that call `http://127.0.0.1:8000` are skipped
  when the backend server is not running.
- Production deployment, observability, and cloud infrastructure are not
  included as a completed deployment target in this repository.

---

## Architecture

```text
React + Vite control tower
        │
        ├── REST/JSON ────────┐
        └── WebSocket tracking│
                              ▼
                       FastAPI application
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
        API routers       Services         ML/pipeline
             │                │                │
             └──────────► Repositories ◄───────┘
                              │
                       SQLAlchemy ORM
                              │
                   PostgreSQL or SQLite
```

The backend follows a layered design:

1. **Endpoints** define HTTP/WebSocket contracts and authorization dependencies.
2. **Schemas** validate request and response data with Pydantic.
3. **Services** implement business rules and workflow invariants.
4. **Repositories** encapsulate database queries.
5. **Models** map domain entities to database tables.

The shipment lifecycle is governed by explicit transition rules. Status changes
must go through the shipment service so that history, assignment, capacity, and
terminal-state rules remain consistent.

---

## API surface

The API is versioned under `/api/v1`:

| Prefix | Responsibility |
|---|---|
| `/auth` | Registration, login, current-user access, authentication |
| `/warehouses` | Warehouse CRUD and capacity information |
| `/products` | Product catalog |
| `/inventory` | Stock listing, adjustment, and reorder information |
| `/drivers` | Driver records and availability |
| `/vehicles` | Fleet records and vehicle status |
| `/shipments` | Shipment lifecycle, assignments, and manifests |
| `/routes` | Corridors, routes, and shipment allocations |
| `/analytics` | Operational KPIs and domain analytics |
| `/pipeline` | AI-ready dataset and pipeline operations |
| `/ml` | Delay-risk prediction |
| `/assistant` | Grounded logistics assistant |

Additional application endpoints:

- `GET /` — service information
- `GET /health` — application health
- `GET /health/db` — database connectivity health
- `WS /ws/tracking/{shipment_id}` — authenticated live shipment tracking
- `/docs` — Swagger UI
- `/redoc` — ReDoc

---

## Technology stack

### Backend

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic v2 and pydantic-settings
- SQLAlchemy 2.x
- PostgreSQL with psycopg 3
- Alembic
- PyJWT and Argon2 via pwdlib
- pytest and HTTPX
- scikit-learn and joblib

### Frontend

- React `^19.2.8`
- React DOM `^19.2.8`
- Vite `^8.3.0`
- Leaflet `^1.9.4`
- Native Node test runner
- Oxlint

---

## Local setup

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- Git
- PostgreSQL is optional for local development; configure it when required

### Backend on Windows PowerShell

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

The frontend uses `http://127.0.0.1:8000` by default. To override it, create
`frontend/.env` from `frontend/.env.example` and set the documented API URL
variable.

### Database and seed data

Copy `backend/.env.example` to `backend/.env` and set a secure `SECRET_KEY`.
Configure `DATABASE_URL` for PostgreSQL when available. The application startup
initializes the local development schema and verifies development seed data.
Production uses the versioned Alembic migration workflow and does not seed demo
records automatically. Migrations can be managed explicitly with:

```powershell
cd backend
alembic upgrade head
python scripts\seed_demo_data.py
```

The production Docker image runs `alembic upgrade head` before starting
Uvicorn. It includes the application, migrations, seed script, and ML inference
artifact required by the backend. Production requires `APP_ENV=production`,
`DEBUG=False`, a strong explicitly configured `SECRET_KEY`, and PostgreSQL.

### Development demo accounts

These accounts are for local development only:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@flowgrid.io` | `AdminPass123!` |
| Manager | `manager@flowgrid.io` | `ManagerPass123!` |
| Driver | `driver@flowgrid.io` | `DriverPass123!` |
| Viewer | `viewer@flowgrid.io` | `ViewerPass123!` |

Do not use these credentials in a shared or production environment.

---

## Testing and verification

### Backend

```powershell
cd backend
pytest -v
```

The current suite contains **306 collected tests** covering authentication,
RBAC, validation, models, CRUD workflows, analytics, shipment transitions,
tracking, WebSockets, pipeline behavior, and ML inference.

### Frontend

```powershell
cd frontend
npm test
npm run build
npm run lint
```

Latest repository verification:

- Backend: **306 tests**, all passing
- Frontend: **49 tests**; the latest run had **45 passed**, **3 failed**, and
  **1 skipped** because an already-running backend contained stale local demo
  state during live integration checks
- Frontend production build: **successful**
- Build output includes a non-blocking bundle-size warning for the main chunk

---

## Complete repository structure

Generated environments and caches such as `backend/venv/`, `backend/.venv/`,
`.venv/`, `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, and
`.pytest_cache/` are intentionally omitted from the source tree below.

```text
FlowGrid/
├── README.md                         # Current project status and this guide
├── complete_guide.md                 # Team onboarding and expanded walkthrough
├── .gitignore
│
├── backend/
│   ├── Dockerfile                    # Backend container image
│   ├── alembic.ini                  # Alembic configuration
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Backend environment template
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, health, startup
│   │   ├── api/
│   │   │   ├── deps.py              # Database, current-user, and role dependencies
│   │   │   └── v1/
│   │   │       ├── api.py           # Versioned router aggregator
│   │   │       └── endpoints/
│   │   │           ├── auth.py
│   │   │           ├── warehouses.py
│   │   │           ├── products.py
│   │   │           ├── inventory.py
│   │   │           ├── drivers.py
│   │   │           ├── vehicles.py
│   │   │           ├── shipments.py
│   │   │           ├── routes.py
│   │   │           ├── analytics.py
│   │   │           ├── pipeline.py
│   │   │           ├── ml.py
│   │   │           ├── assistant.py
│   │   │           └── ws_tracking.py
│   │   ├── core/
│   │   │   ├── config.py             # Settings and environment loading
│   │   │   ├── logging.py            # Structured/sanitized logging
│   │   │   └── security.py           # Password hashing and JWT operations
│   │   ├── db/
│   │   │   ├── base.py               # SQLAlchemy declarative base
│   │   │   └── session.py            # Engine, sessions, DB checks, startup seed
│   │   ├── models/                   # SQLAlchemy domain entities
│   │   │   ├── user.py
│   │   │   ├── warehouse.py
│   │   │   ├── product.py
│   │   │   ├── inventory.py
│   │   │   ├── driver.py
│   │   │   ├── vehicle.py
│   │   │   ├── shipment.py
│   │   │   ├── tracking.py
│   │   │   └── route.py
│   │   ├── schemas/                  # Pydantic request/response contracts
│   │   ├── repositories/             # Database query and persistence layer
│   │   ├── services/                 # Business workflows and domain rules
│   │   └── pipeline/                 # AI-ready data generation and quality checks
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                 # Versioned database migrations
│   │       ├── 7b9c1a0070c1_create_core_logistics_models.py
│   │       ├── 027ff684fd07_create_shipments_table.py
│   │       ├── 63c4732baa7d_create_shipment_tracking_and_history_.py
│   │       ├── 9090bc4b1426_create_routes_and_route_shipments_tables.py
│   │       └── a1c2d3e4f5a6_add_estimated_delivery_at_to_shipments.py
│   │
│   ├── ml/
│   │   ├── train_india_delay_model.py # Train/evaluate the prototype model
│   │   └── models/
│   │       └── india_delay_pipeline.joblib
│   ├── ml_data/
│   │   └── india/                    # India benchmark source data
│   ├── ml_exports/
│   │   ├── data_quality_report.json
│   │   ├── full_dataset.csv
│   │   ├── train_dataset.csv
│   │   └── test_dataset.csv
│   ├── scripts/
│   │   ├── export_ml_dataset.py
│   │   └── seed_demo_data.py
│   └── tests/                        # Backend pytest suite
│       ├── test_auth.py
│       ├── test_health.py
│       ├── test_hardening.py
│       ├── test_models.py
│       ├── test_data_validation.py
│       ├── test_analytics.py
│       ├── test_assistant.py
│       ├── test_delay_risk.py
│       ├── test_drivers.py
│       ├── test_inventory.py
│       ├── test_ml_pipeline.py
│       ├── test_ml_prediction.py
│       ├── test_products.py
│       ├── test_routes.py
│       ├── test_shipments.py
│       ├── test_tracking.py
│       ├── test_vehicles.py
│       ├── test_warehouses.py
│       └── test_websocket_tracking.py
│
├── frontend/
│   ├── package.json                  # Scripts and JavaScript dependencies
│   ├── index.html
│   ├── vite.config.js
│   ├── .env.example
│   ├── public/
│   │   ├── favicon.svg
│   │   ├── hero_truck.jpg
│   │   └── icons.svg
│   ├── src/
│   │   ├── main.jsx                  # React entrypoint
│   │   ├── App.jsx                   # App shell and page routing
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── api/                      # REST client modules by domain
│   │   ├── assets/                   # Bundled images and template assets
│   │   ├── components/               # Reusable UI, modals, maps, panels
│   │   ├── context/                  # Auth, notifications, and toast state
│   │   ├── data/                     # Frontend data constants
│   │   ├── hooks/                    # Dashboard and WebSocket hooks
│   │   ├── pages/                    # Management and control-tower screens
│   │   ├── services/                 # Export and frontend service helpers
│   │   └── utils/                    # Geographic and shared utilities
│   ├── tests/                        # Native Node frontend tests
│   │   ├── apiServices.test.js
│   │   ├── authClient.test.js
│   │   ├── geoAndExport.test.js
│   │   ├── integration.test.js
│   │   ├── liveDelayRisk.test.js
│   │   ├── managementViews.test.js
│   │   ├── ml_api.test.js
│   │   ├── realtimeAndNotifications.test.js
│   │   └── workflowAndPolish.test.js
│   └── README.md                     # Vite template notes
│
└── docs/
    ├── ARCHITECTURE.md               # Detailed system architecture
    ├── DESIGN.md                     # Product and UI design direction
    ├── MEMORY.md                     # Project memory and decisions
    ├── PRD.md                        # Product requirements
    ├── RULES.md                      # Engineering and domain rules
    ├── TASKS.md                      # Work tracking and planned tasks
    ├── setup.md                      # Local setup instructions
    ├── database-setup.md              # Database setup notes
    ├── requirements.md               # Requirements reference
    ├── ai_ready_data_pipeline.md
    ├── ai_existing_data_and_india_dataset_audit.md
    ├── ai_readiness_and_dataset_audit.md
    ├── analytics_and_business_metrics.md
    └── ...
```

---

## Related documentation

- [Architecture specification](docs/ARCHITECTURE.md)
- [Local setup guide](docs/setup.md)
- [Database setup](docs/database-setup.md)
- [Team onboarding guide](complete_guide.md)
- [Product requirements](docs/PRD.md)

---

