# FlowGrid — Audit: Existing Operational Data & India ML Dataset

**Date**: October 2026  
**Auditor**: Antigravity AI Engineering  
**Scope**: Read-only verification of existing FlowGrid data sources, database tables, label trustworthiness, and inspection of the India-focused shipment dataset.  
**Strict Mandate Followed**: Read-only audit. No code modified, no database records touched, no packages installed, no models trained.

---

## Executive Summary

This audit evaluates the feasibility of introducing an **India-focused shipment delay prediction ML feature** into FlowGrid without disrupting or replacing existing operational data.

### Key Conclusions:
1. **Access Confirmation**: The India-focused dataset was **successfully located and accessed** at `C:\Users\saksh\Downloads\FlowGrid_India_Dataset.zip` containing `flowgrid_delay_model_india.csv` (1,451 rows) and its companion `README_FLOWGRID_AI_DATASET_INDIA.txt`. Tabular contents also match the 124-page `flowgrid_delay_model_india.pdf` document.
2. **Existing FlowGrid Data**: Comes from seed fixtures ([`seed_demo_data.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/seed_demo_data.py)) stored in the live PostgreSQL database (`flowgrid_db`), representing a 6-shipment US-based logistics demo.
3. **Existing Historical Labels**: **Unusable for ML training** (0 out of 6 shipments have valid delay labels; target completion is 0.0%).
4. **India Dataset Quality**: Mechanically clean (1,451 rows, 0 nulls, 11 columns, realistic Indian hub-to-hub road distances), but its **delay labels are synthetic carryovers** from an earlier dataset rather than real-world Indian operational performance.
5. **Safe Integration Strategy**: We can train the delay prediction model **completely offline** as an independent module. The existing PostgreSQL database, frontend views, and backend seed fixtures will remain 100% untouched.

---

## 1. Where FlowGrid Data Currently Comes From

The data currently visible in the FlowGrid user interface originates from two distinct layers:

### 1.1 Live PostgreSQL Database (`flowgrid_db`)
The operational backbone is a PostgreSQL database. When the backend service runs, it queries real database tables populated by [`backend/scripts/seed_demo_data.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/scripts/seed_demo_data.py):
- **Warehouses (3 rows)**: Midwest Regional Hub (`ORD-01`, Chicago, IL), East Coast Gateway (`EWR-02`, Newark, NJ), Southwest Logistics Center (`DFW-04`, Dallas, TX).
- **Shipments (6 rows)**: Commercial freight records (`FG-98421-US` through `FG-98426-US`) connecting US destinations (Detroit, Boston, Austin, Minneapolis, Philadelphia, Cleveland).
- **Drivers & Vehicles (1 driver, 3 vehicles)**: Alex Rivera; Mercedes Sprinter, Ford Transit 350, Freightliner Cascadia.
- **Routes (3 corridors)**: `CHI-DET-01`, `EWR-BOS-01`, `DFW-AUS-01`.

### 1.2 Frontend REST API Integration
The frontend application ([`frontend/src/pages/ShipmentsPage.jsx`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/pages/ShipmentsPage.jsx)) calls backend REST endpoints (`GET /api/v1/shipments`, `/api/v1/warehouses`, etc.) via [`frontend/src/api/client.js`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/api/client.js).

### 1.3 Prototype Mock Copy
An earlier design file, [`frontend/src/data/mockLogisticsData.js`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/data/mockLogisticsData.js), contains static prototype UI copy and marketing placeholders (such as claiming a *"scikit-learn gradient boosting regression trained on 42k historical legs"* with *"96.4% precision"*). These were created as design-time placeholders; no 42k dataset or trained weights exist in the codebase.

---

## 2. Database Tables and Fields for Shipments, Statuses, and Delays

FlowGrid organizes shipment lifecycles across four interconnected SQLAlchemy ORM models:

| Table Name | Model File | Key Fields | Purpose & Delay Information |
| :--- | :--- | :--- | :--- |
| **`shipments`** | [`shipment.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/shipment.py) | `id`, `tracking_number`, `status`, `origin_warehouse_id`, `destination_city`, `destination_state`, `total_weight_kg`, `total_volume_cbm`, `assigned_driver_id`, `assigned_vehicle_id`, `scheduled_pickup_at`, `delivered_at`, `created_at`, `updated_at`, `is_active` | Core shipment record and current lifecycle status. **Notice**: The table does *not* contain an `estimated_delivery_at`, `actual_pickup_at`, or `is_delayed` column. |
| **`shipment_status_history`** | [`tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/tracking.py) | `id`, `shipment_id`, `previous_status`, `new_status`, `changed_by_user_id`, `remarks`, `created_at` | Audit trail of all state changes. In FlowGrid's architecture, the timestamp when `new_status = 'PICKED_UP'` serves as the operational pickup time. |
| **`shipment_tracking_events`** | [`tracking.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/tracking.py) | `id`, `shipment_id`, `event_type`, `location`, `description`, `timestamp`, `created_by_user_id` | Granular operational events (checkpoints, sorting hub scans, out-for-delivery milestones). |
| **`routes` & `route_shipments`** | [`route.py`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/app/models/route.py) | `routes`: `id`, `name`, `origin`, `destination`, `estimated_distance`, `estimated_duration`, `status`<br>`route_shipments`: `route_id`, `shipment_id`, `sequence_order`, `assigned_at` | Corridor specifications. `estimated_duration` represents the planned transit hours against which delay thresholds are measured. |

---

## 3. Trustworthiness of Existing Shipment Records for ML

### Verdict: **NOT Trustworthy and NOT Suitable for ML Training**

Our audit confirms that existing database records cannot train a machine learning model:

1. **Near-Zero Sample Volume**: The database contains only **6 shipment records**. Machine learning models require hundreds to thousands of records to identify reliable statistical relationships.
2. **Zero Historical Labels (0.0% Target Rate)**:
   - According to the automated quality audit ([`backend/ml_exports/data_quality_report.json`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/backend/ml_exports/data_quality_report.json)), exactly `records_with_targets = 0` (0.0%).
   - All target fields (`actual_duration_hours`, `is_delayed`, `delay_hours`) are `NULL`.
3. **Missing Lifecycle Milestones**:
   - None of the 6 seeded shipments have entries in `shipment_status_history`. Therefore, there is no recorded `actual_pickup_timestamp`.
   - Without an actual pickup time and delivered time, duration cannot be calculated.
4. **No Route Linkages**:
   - The junction table `route_shipments` has 0 rows. No shipments are tied to planned routes, meaning `planned_duration_hours` is 100% missing.
5. **Synthetic Purpose**: The 6 records were hand-crafted purely to test navigation and UI components, not derived from real delivery vehicles.

---

## 4. Inspection of the India-Focused Dataset

### 4.1 File Location & Access Confirmation
The India dataset was successfully located and read directly from:
- **Primary Archive**: `C:\Users\saksh\Downloads\FlowGrid_India_Dataset.zip` (25,584 bytes compressed)
- **Reference Document**: `flowgrid_delay_model_india.pdf` (124 pages) in `C:\Users\saksh\Downloads\`
- **Status**: **Successfully accessed and parsed in-memory without altering any files.**

### 4.2 Dataset Inventory & Structure
The archive contains two files:
1. `README_FLOWGRID_AI_DATASET_INDIA.txt` (1,205 bytes)
2. `flowgrid_delay_model_india.csv` (279,910 bytes)

### 4.3 Schema and Column Breakdown (1,451 Rows, 11 Columns)

| Column Name | Data Type | Nulls | Unique | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | String | 0 (0%) | 1,451 | `SHP-001169` | Unique identifier per consignment |
| `date` | Date (YYYY-MM-DD) | 0 (0%) | 373 | `2024-08-06` | Dispatch date (Span: 2024-08-06 to 2026-08-05) |
| `supplier` | String | 0 (0%) | 8 | `Orion Freight Co.` | Logistics 3PL / carrier partner |
| `warehouse` | String | 0 (0%) | 5 | `East Depot - Kolkata` | Dispatch origin hub (5 major Indian metro hubs) |
| `destination` | String | 0 (0%) | 12 | `Jaipur Commerce Center` | Destination commercial/depot terminal |
| `route` | String | 0 (0%) | 60 | `Kolkata → Jaipur Commerce Center` | Corridor pair with unicode arrow (`→`) |
| `transport_mode` | String | 0 (0%) | 5 | `Mini Truck (Tata Ace class)` | Vehicle class category |
| `distance_km` | Float | 0 (0%) | 60 | `1765.1` | Corridor road distance in kilometers |
| `driver` | String | 0 (0%) | 15 | `A. Kumar` | Assigned driver alias |
| `vehicle` | String | 0 (0%) | 75 | `Mini Truck - A.Kumar` | Composite fleet tag (`<Mode> - <Driver>`) |
| `is_delayed` | Boolean (`True`/`False`) | 0 (0%) | 2 | `False` | **Target label**: Delay indicator |

### 4.4 Target Variable Distribution
- **Total Records**: 1,451
- **Not Delayed (`False`)**: 1,152 records (**79.39%**)
- **Delayed (`True`)**: 299 records (**20.61%**)
- **Class Balance**: Natural, healthy logistics imbalance (~4:1 on-time to delayed ratio).

### 4.5 Data Quality Assessment
- **Completeness**: 100% complete across all 11 columns (zero missing values).
- **Physical Plausibility**: Distances are realistic Indian highway distances (e.g., Pune to Mumbai is 156.2 km; Kolkata to Guwahati is 681 km; Chennai to Guwahati is 2,446.8 km).
- **Format Integrity**: Clean CSV format; standard UTF-8 encoding.

### 4.6 Provenance (Origin of Data)
According to the dataset's README:
- The dataset was created by adapting and localizing an earlier synthetic supply chain benchmark (originally configured for Bangladesh).
- The creator replaced geographic entities with Indian hubs (Pune, Kolkata, Ahmedabad, Delhi NCR, Chennai) and 12 destination cities.
- The `distance_km` values were calculated mathematically using great-circle coordinates multiplied by a standard 1.3 highway circuity factor.
- Fictional Indian driver names (e.g., R. Yadav, S. Kulkarni, A. Kumar) and carrier names were introduced.

---

## 5. Do the Delay Labels Genuinely Correspond to Indian Records?

### Verdict: **NO. The delay labels do NOT reflect genuine Indian shipping operations.**

We established this fact based on two independent pieces of evidence:

### 5.1 Direct README Disclosure
The dataset author explicitly disclosed:
> *"What was NOT changed:*  
> *- shipment_id, date, and the is_delayed label are carried over from the original file.*  
> *Important:*  
> *- This is still NOT real Indian shipment history. Delay labels come from the original synthetic data, so they do not reflect real Indian carrier performance, and they were not generated from distance/route/mode.*  
> *- Do not use the model for real decisions. For real delay data, use sources like NHAI/FASTag toll data, Indian Railways freight data, or company logs."*

### 5.2 Statistical Correlation Analysis
In authentic logistics data, long distances (e.g., a 2,600 km cross-country run) experience significantly higher delay rates than short feeder trips (e.g., 270 km). Furthermore, specialized vehicles (such as temperature-controlled reefer trucks or heavy multi-axle trailers) exhibit distinct failure profiles compared to small intra-city mini trucks.

Our statistical audit of `flowgrid_delay_model_india.csv` reveals that the delay rate remains artificially flat across all segments:

**Delay Rate by Distance Bucket:**
- `0 – 500 km`: 29 / 158 (**18.4%**)
- `500 – 1,000 km`: 81 / 382 (**21.2%**)
- `1,000 – 1,500 km`: 54 / 272 (**19.9%**)
- `1,500 – 2,000 km`: 88 / 427 (**20.6%**)
- `2,000 – 2,500 km`: 36 / 160 (**22.5%**)
- `2,500 – 3,000 km`: 11 / 52 (**21.2%**)

**Delay Rate by Vehicle Type:**
- `Mini Truck (Tata Ace class)`: 56 / 291 (**19.2%**)
- `Reefer Truck`: 56 / 285 (**19.6%**)
- `Medium Truck (Eicher 14ft class)`: 56 / 281 (**19.9%**)
- `Multi-Axle Trailer`: 60 / 276 (**21.7%**)
- `Heavy Truck (10-wheeler)`: 71 / 318 (**22.3%**)

Every distance bucket and vehicle type hovers within 1.5% to 2% of the overall dataset average (~20.6%). This confirms that the labels were not generated by Indian route conditions or vehicle physics, but were carried over from the legacy synthetic file.

---

## 6. Recommended Architecture: How to Use the India Dataset Safely

To build an India-focused delay prediction feature while protecting existing FlowGrid data, we recommend a **Decoupled Offline Training & Inference Architecture**:

```
+-------------------------------------------------------------------------+
|                  Existing FlowGrid System (UNTOUCHED)                   |
|                                                                         |
|  PostgreSQL Database (flowgrid_db)    <--->    Backend API (FastAPI)    |
|  - 6 Seed Shipments (US Demo)                  - CRUD Endpoints         |
|  - 3 Warehouses, 1 Driver, 3 Vehicles          - Auth & RBAC            |
|  - Operational Tables Unaltered                - Frontend (React)       |
+-------------------------------------------------------------------------+
                                    |
                                    | (Read-Only Feature Queries)
                                    v
+-------------------------------------------------------------------------+
|                New Isolated India ML Module (DECOUPLED)                 |
|                                                                         |
|  1. Offline Dataset Staging:                                            |
|     data/india_ml/flowgrid_delay_model_india.csv (isolated from DB)     |
|                                                                         |
|  2. Trained Model Artifacts:                                            |
|     backend/app/ml/models/india_delay_classifier.joblib                 |
|                                                                         |
|  3. Standalone Inference Service:                                       |
|     POST /api/v1/ml/predict-delay                                       |
|     - Takes: origin, destination, vehicle_mode, distance_km             |
|     - Returns: delay_risk_probability, predicted_label, risk_level      |
|     - Writes: ZERO rows to operational tables                           |
+-------------------------------------------------------------------------+
```

### Key Principles of the Strategy:
1. **Zero Database Mutations**: The 1,451 records from the CSV should **never** be inserted into the operational `shipments` table. The existing database stays clean and operational.
2. **Offline Artifact Directory**: The CSV is placed in a dedicated dataset folder (e.g., `data/india_ml/` or `backend/ml_data/india/`), kept completely separate from PostgreSQL migrations.
3. **Dedicated Inference Endpoint**: When a user selects or simulates an Indian route in the UI, or requests a delay risk assessment, the frontend or backend passes the parameters to a dedicated prediction endpoint (`/api/v1/ml/predict-delay`), returning real-time risk scores without altering any database records.
4. **Honest System Transparency**: In the application UI, display an informative note (e.g., *"Benchmark Model: Trained on 1,451 synthetic Indian corridor records"*), maintaining total technical integrity.

---

## 7. Recommended Next Single Step

**Next Step**: Copy `FlowGrid_India_Dataset.zip` (and extract its CSV and README) into a newly created, non-invasive workspace directory:  
`backend/ml_data/india/`

This prepares the data for offline preprocessing and baseline model exploration without altering any code, database tables, or application behavior.

*Awaiting your approval before proceeding.*
