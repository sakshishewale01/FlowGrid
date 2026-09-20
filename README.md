# FlowGrid 🚚

### Intelligent Logistics & Supply Chain Management Platform

FlowGrid is a full-stack logistics and supply chain management platform designed to improve operational efficiency, shipment visibility, warehouse management, inventory tracking, and delivery coordination.

The platform provides a centralized system for managing warehouses, products, inventory, drivers, vehicles, shipments, routes, and logistics analytics.

---

## 🎯 Project Vision

FlowGrid aims to provide a scalable, secure, and intelligent logistics platform that helps businesses manage supply chain operations through:

- Centralized logistics data
- Role-based access control
- Shipment lifecycle tracking
- Warehouse and inventory management
- Route and delivery coordination
- Operational analytics
- Future AI-powered decision support

---

## ✨ Key Features

- Authentication and role-based access control
- Warehouse management
- Product and inventory management
- Driver and vehicle management
- Shipment management
- Shipment lifecycle tracking
- Route management
- Delivery coordination
- Logistics analytics
- Modular backend architecture
- Future AI/ML-powered insights

---

## 👥 User Roles

FlowGrid supports multiple user roles with different levels of access:

| Role | Description |
|---|---|
| **Admin** | Manages users, system settings, and all logistics operations |
| **Manager** | Oversees warehouses, shipments, inventory, routes, and analytics |
| **Driver** | Views assigned deliveries, routes, and shipment information |
| **Viewer** | Has read-only access to permitted logistics data |

---

## 🧩 Core Modules

### Authentication and Authorization

- User authentication
- Role-based access control
- Protected API endpoints
- Permission-based resource access

### Warehouse Management

- Warehouse registration and management
- Warehouse capacity tracking
- Product storage organization
- Warehouse-level inventory visibility

### Product and Inventory Management

- Product catalog management
- Stock-level monitoring
- Inventory movement tracking
- Low-stock visibility
- Warehouse-specific inventory records

### Driver and Vehicle Management

- Driver records
- Vehicle registration
- Driver-to-vehicle assignments
- Availability and operational status tracking

### Shipment Management

- Shipment creation and management
- Sender and receiver information
- Shipment status tracking
- Shipment assignment to drivers and vehicles
- Delivery progress visibility

### Route Management

- Route planning
- Driver route assignments
- Delivery sequence management
- Route status tracking

### Logistics Analytics

- Shipment performance insights
- Inventory analytics
- Warehouse activity metrics
- Delivery and route performance tracking

### Future AI/ML Features

Planned intelligent capabilities include:

- Delivery time prediction
- Route optimization
- Demand forecasting
- Inventory replenishment recommendations
- Logistics performance insights

---

## 🛠️ Technology Stack

### Frontend

- React.js
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

### Database and Migrations

- PostgreSQL
- Alembic

### Future AI/ML

- Python
- Scikit-learn

### Future Deployment

- AWS Cloud Services

---

## 🏗️ Architecture

FlowGrid is being developed using a modular and scalable architecture with clear separation of responsibilities.

The backend is organized around:

- API routes
- Service layer
- Repository layer
- Database models
- Validation schemas
- Authentication and authorization
- Configuration management

The frontend is designed around reusable React components and modular feature-based views.

### High-Level Request Flow

```text
Frontend
   │
   ▼
FastAPI API Routes
   │
   ▼
Service Layer
   │
   ▼
Repository Layer
   │
   ▼
SQLAlchemy ORM
   │
   ▼
PostgreSQL Database
```

---

## 📁 Planned Project Structure

```text
FlowGrid/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   └── App.jsx
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/          # Modular API routers and dependencies
│   │   ├── core/         # Config, security, and logging
│   │   ├── db/           # Session management and engine
│   │   ├── models/       # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic layer
│   │   ├── repositories/ # Database query operations
│   │   └── main.py       # FastAPI application entrypoint
│   ├── alembic/          # Database migrations
│   ├── tests/            # Automated pytest suite
│   ├── Dockerfile        # Production container specification
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variables template
│
├── README.md
└── .gitignore
```

---

## 🚀 Quickstart & Local Development

### 1. Prerequisites
- **Python**: 3.11+ (recommended 3.12 or 3.14)
- **Node.js**: 18+ and npm
- **PostgreSQL**: 15+ running on port `5432`

### 2. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup
```bash
# In a separate terminal, navigate to the frontend directory
cd frontend

# Install packages
npm install

# Start the Vite development server
npm run dev
```

---

## 📖 Interactive API Documentation

Once the backend service is running, access the interactive OpenAPI documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🧪 Running Automated Tests

FlowGrid comes with an automated test suite covering all modules, RBAC enforcement, state machine transitions, validations, and analytics:

```bash
cd backend

# Run the complete test suite
pytest

# Run tests with verbose output
pytest -v

# Run specific test modules
pytest tests/test_auth.py
pytest tests/test_shipments.py
pytest tests/test_routes.py
pytest tests/test_analytics.py
```

---

## 🐳 Production Deployment

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
  -e SECRET_KEY="your-cryptographically-secure-production-secret" \
  -e APP_ENV="production" \
  -e DEBUG="False" \
  flowgrid-backend:latest
```

