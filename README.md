# FlowGrid 🚚⚡

### Smart Logistics & Transportation Control Tower

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Scikit--Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E.svg?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**FlowGrid** is a production-grade, full-stack intelligent logistics control tower and transportation management system (TMS). Engineered for high-throughput supply chain operations, FlowGrid delivers real-time shipment visibility, explainable disruption rescue workflows, sandbox what-if simulations, grounded conversational intelligence, and heuristic/ML delay risk analytics.

---

## 📑 Table of Contents

- [Vision & Value Proposition](#-vision--value-proposition)
- [Key Capabilities & Innovations](#-key-capabilities--innovations)
  - [1. Executive Control Tower Dashboard](#1-executive-control-tower-dashboard)
  - [2. Shipment Rescue Center](#2-shipment-rescue-center)
  - [3. What-If Disruption Simulator](#3-what-if-disruption-simulator)
  - [4. Operational Recommendations Engine](#4-operational-recommendations-engine)
  - [5. Grounded Logistics Assistant](#5-grounded-logistics-assistant)
  - [6. Machine Learning Delay Prediction](#6-machine-learning-delay-prediction)
  - [7. Core Logistics Modules (CRUD & Lifecycles)](#7-core-logistics-modules-crud--lifecycles)
- [Role-Based Access Control (RBAC)](#-role-based-access-control-rbac)
- [System Architecture](#-system-architecture)
- [Design System & Theme Switching](#-design-system--theme-switching)
- [Interactive Telematics Map](#-interactive-telematics-map)
- [Project Directory Structure](#-project-directory-structure)
- [Quickstart & Local Setup](#-quickstart--local-setup)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Default Demo Accounts](#default-demo-accounts)
- [Automated Testing Suite](#-automated-testing-suite)
- [API Documentation](#-api-documentation)
- [Documentation & Knowledge Base](#-documentation--knowledge-base)
- [Deployment](#-deployment)

---

## 🎯 Vision & Value Proposition

Traditional logistics management platforms are fragmented—dispatchers switch between separate software for inventory, fleet telematics, risk triage, and analytics. FlowGrid unifies these operational silos into a single high-performance cockpit:

- **Predict**: Quantify transit bottlenecks using ML pipelines and heuristic delay risk scoring before delivery failures occur.
- **Decide**: Triage operational strain via transparent rule engines and non-destructive "What-If" scenario simulations.
- **Recover**: Execute verified mitigation protocols (driver reallocation, line-haul corridor rerouting, equipment swaps) with optimistic UI updates and backend state machine compliance.

---

## ✨ Key Capabilities & Innovations

### 1. Executive Control Tower Dashboard
- **Live Corridor Telematics**: Interactive SVG & Leaflet-powered flow map visualizing transit nodes, hub coordinates, moving freight corridors, and pulsing status halos.
- **Real-Time KPIs**: Metric cards tracking Total Active Shipments, On-Time Dispatch Rate (94.2%), Critical Risk Freight Count, and Active Fleet Hubs with 7-day sparkline trend indicators.
- **Quick Dispatch Bar**: Action shortcuts with role-aware lock icons protecting sensitive dispatch mutations from unauthorized operator roles.
- **Top Navigation Bar**: Live backend connection health probe (`/health`), global search across multiple entities, unread notification panel with real-time badges, and operator session profile dropdown.

### 2. Shipment Rescue Center
- **Explainable Rule-Based Triage**: Evaluates live shipment records against deterministic operational rules:
  - `RULE-EX01`: Dispatch/Transit Exception (Failed deliveries or abort events).
  - `RULE-R01`: Unassigned Fleet Driver (Missing driver profile blocking dispatch).
  - `RULE-R02`: Unassigned Transport Equipment (No vehicle/trailer asset allocated).
  - `RULE-R03`: Unassigned Transit Corridor (Missing line-haul corridor causing ETA variance).
  - `RULE-R04`: Capacity Strain (Cargo weight exceeding 85% vehicle capacity rating).
- **Human-in-the-Loop Interventions**: Interactive modal drawers allowing operators to resolve missing resources directly from the triage queue with immediate state transition validation.

### 3. What-If Disruption Simulator
- **Non-Destructive Sandbox**: Tests operational shocks against real database records without altering production data.
- **4 Real-World Disruption Scenarios**:
  1. *Driver Unavailability / Fleet Strike*: Simulates cascading delays from operator shortages.
  2. *Route Corridor Closure / Weather Event*: Models line-haul transit corridor blocks and detour times.
  3. *Warehouse Capacity Bottleneck*: Evaluates staging buffer limits and cross-dock delays.
  4. *Fuel Surcharge & Transit Cost Spike*: Estimates financial impact and margin compression.
- **Cascade Impact Analysis**: Quantifies affected shipments, estimated delivery time variance (+hours), and projected financial loss ($) with side-by-side mitigation comparisons.

### 4. Operational Recommendations Engine
- Grounded suggestions categorized by priority (`CRITICAL`, `WARNING`, `OPTIMIZATION`).
- Generates transparent rationales detailing *why* an intervention is recommended, expected delivery improvement, and confidence rating.
- Requires operator confirmation before dispatching live database updates.

### 5. Grounded Logistics Assistant
- Natural language operator companion accessible via quick actions (`Ask Assistant`) or slide-out drawer.
- **Strictly Grounded Context**: Formulates responses directly from verified backend endpoints (`/shipments`, `/warehouses`, `/drivers`, `/vehicles`, `/analytics`) rather than ungrounded generative hallucinations.
- Supports entity lookups (`#SHP-101`), warehouse stock inquiries, driver duty status checks, and fleet utilization telemetry.

### 6. Machine Learning Delay Prediction
- **Trained Pipeline**: Scikit-Learn Random Forest Pipeline (`rf_pipeline.joblib`) with integrated numeric and categorical preprocessors.
- **API Endpoint**: Authenticated `POST /api/v1/ml/predict-delay`.
- **Feature Set**: Transit distance, cargo weight, vehicle capacity utilization, driver hours of service, weather index, and historical route congestion.
- **Transparent Governance Disclaimer**: Explicitly identifies the model as an experimental decision-support prototype (synthetic baseline ROC-AUC ~0.5062) requiring human verification.

### 7. Core Logistics Modules (CRUD & Lifecycles)
- **Warehouses**: Storage capacity management, geo-coordinates, dock availability, and inventory allocation.
- **Inventory**: Product catalog, batch tracking, stock level thresholds, and automatic low-stock alerts.
- **Fleet & Drivers**: Vehicle payload ratings, fuel types, maintenance states, driver duty logs, and licensing.
- **Shipments**: Comprehensive 5-stage lifecycle state machine (`PENDING` ➔ `DISPATCHED` ➔ `IN_TRANSIT` ➔ `OUT_FOR_DELIVERY` ➔ `DELIVERED` / `FAILED`).
- **Transit Routes**: Geographic waypoints, corridor distance, estimated duration, and linked toll schedules.

---

## 👥 Role-Based Access Control (RBAC)

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

## 🏛️ System Architecture

FlowGrid follows a decoupled, resilient architecture adhering to clean domain boundaries:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FLOWGRID CONTROL TOWER                          │
│                                                                        │
│   React 18 SPA + Vite  •  Design System Tokens  •  HTML5/CSS Glass     │
│   ├── Top Navigation (Health Monitor • Global Search • Notifications)  │
│   ├── Executive Telematics Dashboard & Interactive SVG Corridor Map    │
│   ├── Shipment Rescue Center (Deterministic Operational Rules)         │
│   ├── What-If Disruption Simulator (Client Sandbox Engine)             │
│   └── Grounded Logistics Assistant Modal & Chat Interface              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  Bearer JWT (HTTP/1.1 REST)
                                    │  RFC 6455 WebSocket Telematics
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI GATEWAY & API                          │
│                                                                        │
│   FastAPI 0.110+  •  Pydantic v2 Schemas  •  OAuth2 Password Bearer    │
│   ├── /api/v1/auth (Login, Registration, RBAC Dependencies)            │
│   ├── /api/v1/shipments (Lifecycle State Machine, Manifests)           │
│   ├── /api/v1/warehouses, /inventory, /drivers, /vehicles, /routes     │
│   ├── /api/v1/analytics (Fleet KPIs, Risk Heuristics)                  │
│   └── /api/v1/ml/predict-delay (Scikit-Learn Joblib Pipeline)          │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
       ┌─────────────────────────┐      ┌─────────────────────────┐
       │   SQLAlchemy 2.0 ORM    │      │ Scikit-Learn Pipeline   │
       │   Alembic DB Migrations │      │ Random Forest Model     │
       │   PostgreSQL 15+ Engine │      │ Feature Preprocessor    │
       └─────────────────────────┘      └─────────────────────────┘
```

---

## 🎨 Design System & Theme Switching

FlowGrid features a dual-theme architecture engineered for operations centers:

1. **Deep Tech Blue (Dark Mode - Default)**:
   - Primary Surface: `#0B1220` (Canvas) & `#111D32` (Cards/Panels).
   - Sidebar: `#0F172A` (Navy Control Hub).
   - Accents: Electric Blue `#3B82F6` and Cyan `#22D3EE`.
   - Optimized for low-light control rooms to reduce eye fatigue during continuous monitoring.
2. **Precision Operational Light Mode**:
   - Primary Surface: `#F1F5F9` (Canvas) & `#FFFFFF` (Cards/Panels).
   - Text Hierarchy: Deep Slate `#0F172A` and Muted Slate `#64748B`.
   - High-contrast table data grids and crisp status badges.
3. **Instant Persistence**:
   - Theme preference is stored in `localStorage` (`flowgrid_theme`).
   - Integrated zero-latency pre-mount initializer script prevents flash of unstyled theme on page reload.
   - Interactive `#btn-nav-theme-toggle` in the top navbar dynamically swaps Sun/Moon SVG icons.

---

## 🗺️ Interactive Telematics Map

- **SVG Vector Corridor Engine**: High-fidelity map viewport plotting key logistics nodes:
  - Seattle Hub (`SEA-01`)
  - Chicago Central Gateway (`CHI-01`)
  - Dallas Distribution Depot (`DFW-01`)
  - Atlanta Southeastern Cross-Dock (`ATL-01`)
  - New York Metro Hub (`JFK-01`)
- **Real-Time Visual Indicators**:
  - Pulsing status halos (`pulse-halo`) marking active transit points.
  - Dashed animated corridors depicting active freight corridors.
  - Interactive click-to-inspect popups providing active dispatch counts and hub capacity.
  - Floating telematics telemetry badge displaying live transit volume and speed variance.

---

## 📁 Project Directory Structure

```text
FlowGrid/
├── frontend/
│   ├── src/
│   │   ├── api/             # Domain API clients (shipments, warehouses, ml, etc.)
│   │   ├── components/      # Reusable UI widgets, TopNavbar, Sidebar, Modals
│   │   ├── context/         # AuthContext, NotificationContext, ToastContext
│   │   ├── pages/           # Feature pages (RescueCenter, Simulator, Analytics, etc.)
│   │   ├── utils/           # Geo-coordinate parsers, CSV export sanitizers
│   │   ├── App.jsx          # Route orchestration & Control Tower dashboard view
│   │   ├── index.css        # Core design tokens, dark/light theme definitions
│   │   └── main.jsx         # React application entrypoint
│   ├── tests/               # 46 automated frontend unit & integration tests
│   ├── index.html           # HTML shell with theme pre-loader & typography
│   └── package.json         # Scripts and npm dependencies
│
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Modular FastAPI routers (auth, shipments, ml, etc.)
│   │   ├── core/            # App settings, security, cryptographic utilities
│   │   ├── db/              # SQLAlchemy engine, session maker, base model
│   │   ├── models/          # SQLAlchemy ORM models (Shipment, Driver, Warehouse)
│   │   ├── schemas/         # Pydantic v2 validation models
│   │   ├── services/        # Business logic, state machines, ML inference
│   │   └── main.py          # FastAPI application entrypoint
│   ├── alembic/             # Version-controlled database migrations
│   ├── tests/               # Pytest suite covering RBAC, APIs, and state machine
│   ├── Dockerfile           # Multi-stage production container specification
│   └── requirements.txt     # Locked Python dependencies
│
├── docs/                    # Authoritative technical documentation & architecture
├── README.md                # Project documentation & operational manual
└── .gitignore               # Ignored build artifacts and environment secrets
```

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ and npm
- **PostgreSQL**: 15+ running on port `5432`

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Update DATABASE_URL with your PostgreSQL credentials:
   # postgresql+psycopg://postgres:password@localhost:5432/flowgrid_db
   ```

5. **Apply database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the FastAPI backend server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend will be live at `http://127.0.0.1:8000`.

---

### Frontend Setup

1. **In a separate terminal, navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The application dashboard will be live at `http://localhost:5173`.

---

### Default Demo Accounts

Use these pre-configured credentials to evaluate role-based behaviors:

| Role | Email Address | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@flowgrid.io` | `FlowGrid2026!` | Full administrative control & health monitoring |
| **Manager** | `manager@flowgrid.io` | `FlowGrid2026!` | Operations dispatch, rescue interventions, routing |
| **Driver** | `driver@flowgrid.io` | `FlowGrid2026!` | Assigned freight manifests & duty logs |
| **Viewer** | `viewer@flowgrid.io` | `FlowGrid2026!` | Read-only dashboards & telematics |

---

## 🧪 Automated Testing Suite

FlowGrid includes comprehensive unit and integration testing across both tiers:

### Frontend Test Suite (Node.js Native Test Runner)
```bash
cd frontend
npm test
```
- **Test Results**: **46/46 tests passing**.
- Covers API client modules, error formatting, RFC 4180 CSV export sanitization, geo-coordinate resolution, notification center deduplication, state machine validation, and live backend integration probes.

### Backend Test Suite (Pytest)
```bash
cd backend
pytest -v
```
- Covers JWT cryptographic validation, password hashing, RBAC endpoint boundaries, shipment lifecycle state transitions, vehicle capacity constraints, and ML prediction endpoints.

---

## 📖 API Documentation

Once the FastAPI server is running, explore the interactive OpenAPI specifications:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Specification**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema (JSON)**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 📚 Documentation & Knowledge Base

In-depth technical specifications are available in the [`docs/`](./docs) folder:

- [**PRD.md**](./docs/PRD.md): Product Requirements, user personas, and success metrics.
- [**ARCHITECTURE.md**](./docs/ARCHITECTURE.md): Decoupled architecture, ERD, and data flow.
- [**RULES.md**](./docs/RULES.md): Enforced state transitions and capacity invariants.
- [**DESIGN.md**](./docs/DESIGN.md): Design tokens, UI layout specifications, and component hierarchy.
- [**TASKS.md**](./docs/TASKS.md): Completed milestone logs and development tasks.
- [**MEMORY.md**](./docs/MEMORY.md): Developer quick reference and cheat sheet.

---

## 🐳 Deployment

### Production Startup (Bare Metal / VM)
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Container Deployment
```bash
# Build the production Docker image
docker build -t flowgrid-backend:latest -f backend/Dockerfile backend/

# Run the container
docker run -d \
  --name flowgrid-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg://user:password@host:5432/flowgrid_db" \
  -e SECRET_KEY="your-production-secret-key" \
  -e APP_ENV="production" \
  -e DEBUG="False" \
  flowgrid-backend:latest
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

**FlowGrid** — *Smarter Logistics. Stronger Supply Chains.*
