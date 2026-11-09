# 🚚 FlowGrid

Welcome to **FlowGrid**!

---

## 📌 1. What is FlowGrid?

**FlowGrid** is an intelligent logistics and supply chain management platform. It gives logistics companies a centralized "Control Center" to:
- Monitor **Warehouses** and storage capacity.
- Track **Inventory** levels and get low-stock replenishment alerts.
- Manage **Drivers & Fleet Vehicles**.
- Dispatch and track **Shipments** in real time across transit corridors.
- Plan **Freight Routes** with automated distance and timing estimates.
- View **Operational Analytics & KPIs** on executive dashboards.
- Provide secure **Role-Based Access Control (RBAC)** for Admins, Managers, Drivers, and Viewers.

---

## 💻 2. Tech Stack

- **Backend**:
  - Python 3.11+ / 3.12 / 3.14
  - **FastAPI**: High-performance RESTful API framework
  - **SQLAlchemy 2.0**: Modern Object-Relational Mapping (ORM)
  - **Pydantic v2**: Strict data validation and schema serialization
  - **PostgreSQL** (Production / Local default) + **Automatic SQLite Fallback** for zero-setup local dev
  - **Passlib & Argon2**: Secure cryptographic password hashing
  - **PyJWT**: Secure JSON Web Tokens (JWT) for authentication
- **Frontend**:
  - **React 18** (Modern functional components & hooks)
  - **Vite**: Ultra-fast frontend development server
  - **Vanilla CSS**: Custom "Deep Tech Blue" design system with responsive layouts
- **Automated Testing**:
  - **Pytest**: Over 295 automated unit and integration tests

---

## 🧩 3. What Has Been Built Up to Now

All core modules are fully built, tested, and integrated:

1. **Authentication & Security (`/api/v1/auth`)**:
   - Secure login, user registration, JWT token generation, and password hashing with Argon2.
   - Role-Based Access Control (`ADMIN`, `MANAGER`, `DRIVER`, `VIEWER`).
2. **Warehouses (`/api/v1/warehouses`)**:
   - Create, list, search, update, and manage regional logistics hubs (e.g. Chicago ORD-01, Newark EWR-02, Dallas DFW-04).
3. **Products & Inventory (`/api/v1/products`, `/api/v1/inventory`)**:
   - Product catalog with SKUs and unit pricing.
   - Real-time warehouse-level stock counts, safety thresholds, and low-stock reorder warnings.
4. **Drivers & Vehicles (`/api/v1/drivers`, `/api/v1/vehicles`)**:
   - Driver commercial licensing, telephone records, and status (`AVAILABLE`, `IN_TRANSIT`, `OFF_DUTY`).
   - Vehicle fleet types (Semi-Trailer, Box Truck, Flatbed) with weight capacities and assignments.
5. **Shipments & Tracking (`/api/v1/shipments`, `/api/v1/tracking`)**:
   - Full shipment dispatch lifecycle: `CONFIRMED` ➔ `ASSIGNED` ➔ `PICKED_UP` ➔ `IN_TRANSIT` ➔ `OUT_FOR_DELIVERY` ➔ `DELIVERED` (or `FAILED` / `CANCELLED`).
   - Audit trail of tracking events and waypoint history.
6. **Corridors & Routes (`/api/v1/routes`)**:
   - Freight corridor route management (origin, destination, distance, estimated travel time).
7. **Analytics (`/api/v1/analytics/overview`)**:
   - Central control KPIs: total shipments, active deliveries, warehouse utilization percentage, driver availability, and inventory health.
8. **Interactive UI (`frontend`)**:
   - Dark-mode Logistics Control Center with quick demo login chips, telemetry cards, and multi-tab management.

---

## ⚡ 4. Step-by-Step Setup: Run on Your Laptop

Follow these steps to run FlowGrid on any Windows, macOS, or Linux laptop.

### Prerequisites:
- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.11, 3.12, or 3.14) - [Download here](https://python.org/)
- **Git**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/sakshishewale01/FlowGrid.git
cd FlowGrid
```

---

### Step 2: Set Up and Start the Backend

1. **Open a terminal** and navigate to `backend`:
   ```bash
   cd backend
   ```

2. **Create and activate a Python virtual environment**:
   - **On Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
     *(If PowerShell blocks scripts, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then retry activation)*
   - **On macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the `.env` configuration file**:
   - **Windows**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **macOS / Linux**:
     ```bash
     cp .env.example .env
     ```
   *(Note: The default `.env` is already pre-configured to work out of the box!)*

5. **Start the FastAPI backend server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   You should see:
   ```text
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   ```

---

### Step 3: Set Up and Start the Frontend

1. **Open a second terminal** and navigate to `frontend`:
   ```bash
   cd frontend
   ```

2. **Install Node packages**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to: **[http://localhost:5173](http://localhost:5173)**

---

## 🛡️ 5. Zero-Configuration Database Resilience

You **do not need** to spend hours configuring PostgreSQL or troubleshooting database errors:
- **If PostgreSQL is installed and running** on port `5432` with password `postgres`, FlowGrid connects to it automatically.
- **If PostgreSQL is NOT installed or NOT running**, FlowGrid's intelligent engine automatically detects this and **falls back to a local SQLite database (`flowgrid_dev.db`)**.
- **Automatic Auto-Seeding**: On backend startup, FlowGrid automatically verifies the database schema and seeds all demo accounts, warehouses, products, and shipments. No manual migration or manual seeding is required!

---

## 🔑 6. Demo Login Credentials

On the login screen (`http://localhost:5173`), you can click any of the **Quick Demo Chips** or enter these credentials manually:

| Role | Email | Password | What You Can Access |
| :--- | :--- | :--- | :--- |
| **Manager** | `manager@flowgrid.io` | `ManagerPass123!` | Warehouses, shipments, inventory, route planning, dispatch |
| **Driver** | `driver@flowgrid.io` | `DriverPass123!` | Assigned deliveries, route tracking, shipment status updates |
| **Admin** | `admin@flowgrid.io` | `AdminPass123!` | Complete administrative control across all resources and users |
| **Viewer** | `viewer@flowgrid.io` | `ViewerPass123!` | Read-only analytics, telemetry dashboard, and shipment visibility |

---

## 🧪 7. Running Automated Tests

To run the complete test suite (295 tests):

```bash
cd backend
# Make sure your virtual environment is active (venv)
pytest -v
```

All 295 tests run using an in-memory SQLite database, verifying API responses, RBAC security rules, state machines, and data validation.

---

## 📖 8. Interactive API Documentation

While the backend is running, you can explore and test every API endpoint directly in your browser:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Database Health Check**: [http://127.0.0.1:8000/health/db](http://127.0.0.1:8000/health/db)

---

## ❓ 9. Troubleshooting & FAQ

#### 1. "Port 8000 or Port 5173 is already in use"
- Another instance of uvicorn or vite may be running. Stop it in the terminal with `Ctrl + C`, or close the previous terminal window.

#### 2. "Scripts are disabled on this system" (Windows PowerShell)
- If `.\venv\Scripts\Activate.ps1` gives an execution policy error, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
  Then run `.\venv\Scripts\Activate.ps1` again.

#### 3. "Authentication Failed: A database error occurred..."
- This has been permanently resolved with our auto-fallback feature. If you ever see this, simply restart the backend server (`uvicorn app.main:app --reload`), and it will auto-verify the database and seed the accounts immediately.
