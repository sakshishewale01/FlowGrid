# FlowGrid 🚚
### Intelligent Logistics and Supply Chain Management Platform

## About the Project

FlowGrid is a web-based logistics management platform that helps manage shipments, warehouses, inventory, drivers, vehicles, and routes in one place.

It uses machine learning to predict shipment delay risks and provides analytics to support better logistics decisions.

## Features

- **User Authentication:** Secure login and registration with role-based access (Admin, Manager, Driver, Viewer).
- **Dashboard:** Centralized view of logistics operations and key statistics.
- **Shipment Management:** Create, manage, assign, and track shipments.
- **Warehouse Management:** Manage warehouses and monitor capacity.
- **Inventory Management:** Track stock, low inventory, and reorder recommendations.
- **Fleet Management:** Manage drivers, vehicles, and maintenance records.
- **Route Recommendations:** Suggest suitable routes using stored route information.
- **AI Delay Prediction:** Predict shipment delay probability and risk levels using a Random Forest model.
- **Analytics & Reports:** View operational insights and export CSV reports.
- **Logistics Assistant:** Provides logistics-related insights using application data.
- **What-If Simulation:** Explore logistics disruption scenarios.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM & Migrations | SQLAlchemy, Alembic |
| Machine Learning | Scikit-learn, Random Forest |
| Authentication | JWT, Argon2 |
| Maps | Leaflet |
| Deployment | Vercel, Render, Neon |
| Version Control | Git, GitHub |

## System Architecture

```text
React + Vite Frontend
        |
        | REST API / WebSocket
        v
FastAPI Backend
        |
        |-------------------|
        v                   v
PostgreSQL Database    ML Prediction Pipeline
```

## Local Setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the application at:

http://localhost:5173

## Deployment

FlowGrid is deployed using:

- **Frontend:** Vercel
- **Backend:** Render
- **Database:** Neon PostgreSQL

## Limitations

- AI delay prediction is a prototype trained on benchmark data.
- Route recommendations use stored route estimates and do not include live traffic or GPS optimization.
- Inventory forecasting uses historical stock movements and simple demand estimates.
- The system is intended as an academic project and decision-support prototype.

## Future Scope

- GPS-based real-time shipment tracking
- Live traffic-based route optimization
- Improved machine learning models using real logistics data
- Integration with external logistics and transportation systems
- Advanced predictive analytics

## Project Status

FlowGrid is a full-stack academic major project integrating logistics management, analytics, and machine learning-based decision support.

---
