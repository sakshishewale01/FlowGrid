# FlowGrid Analytics & Business Metrics (Phase 22)

## 1. Overview & Purpose

FlowGrid Phase 22 establishes a production-grade analytics and operational Key Performance Indicator (KPI) engine. Built strictly upon FlowGrid's existing PostgreSQL/SQLite database models, it delivers executive-level operational intelligence across all five logistical pillars:
1. **Shipments & Order Throughput**
2. **Warehouses & Facility Storage Footprint**
3. **Inventory Balances & Stock Replenishment**
4. **Field Driver Workforce & Dispatch Allocation**
5. **Transport Fleet Vehicles & Carrying Capacity**
6. **Transit Corridors & Line-Haul Routes**

Crucially, Phase 22 defines **AI Baseline Metrics** that capture pre-AI operational performance benchmarks. In subsequent phases, predictive machine learning models (such as ETA regression and delay classification) will be evaluated directly against these historical baselines.

---

## 2. Metric Definitions & Mathematical Formulas

Every metric is derived purely from real operational tables (`shipments`, `warehouses`, `inventory`, `products`, `drivers`, `vehicles`, `routes`, `shipment_status_history`). All formulas contain explicit division-by-zero protection.

### 2.1 Shipment & Delivery Performance KPIs

| KPI Name | Formula / Derivation | Data Source | Notes |
| :--- | :--- | :--- | :--- |
| **Total Shipments** | $\sum \text{Shipment}$ (filtered by window) | `shipments.id` | Filterable by `start_date`, `end_date`. |
| **Active Shipments** | $\sum [\text{status} \in \{\text{CREATED}, \text{CONFIRMED}, \text{ASSIGNED}, \text{PICKED\_UP}, \text{IN\_TRANSIT}, \text{OUT\_FOR\_DELIVERY}\} \land \text{is\_active} = \text{True}]$ | `shipments.status` | Shipments actively moving or in dispatch. |
| **Delivered Shipments** | $\sum [\text{status} = \text{DELIVERED}]$ | `shipments.status` | Verified deliveries. |
| **Delivery Completion Rate** | $\frac{\text{Delivered Shipments}}{\text{Total Shipments}} \times 100\%$ | `shipments.status` | Evaluates throughput against backlog. |
| **On-Time Delivery Rate** | $\frac{\text{On-Time Delivered Shipments}}{\text{Total Delivered Shipments}} \times 100\%$ | Status history milestones & routes | Delivery duration $\le \text{planned duration} + 0.1\text{ hrs}$ (6-min buffer). Defaults to $0.0\%$ if no delivered shipments. |
| **Late Delivery Rate** | $\frac{\text{Late Delivered Shipments}}{\text{Total Delivered Shipments}} \times 100\%$ | Status history milestones & routes | Shipments where duration exceeds planned corridor duration or logged delay remarks. |
| **Average Delivery Duration** | $\frac{1}{N_{\text{deliv}}} \sum (t_{\text{delivered}} - t_{\text{pickup}})$ (in hours) | `shipments.delivered_at`, status milestones | Computed for delivered shipments with recorded pickup and delivery timestamps. |
| **Average Delay Duration** | $\frac{1}{N_{\text{late}}} \sum (\text{actual\_duration} - \text{planned\_duration})$ (in hours) | `shipments`, `routes.estimated_duration` | Average magnitude of transit delays among late shipments. |
| **Historical Delay Frequency** | $\frac{\sum \text{Shipments with Delay Signals}}{\text{Total Shipments}} \times 100\%$ | `shipments.status`, `shipment_status_history` | Includes `FAILED`, `RETURNED`, or status history remarks mentioning breakdown/delay/traffic. |

### 2.2 Warehouse & Facility Capacity KPIs

| KPI Name | Formula / Derivation | Data Source | Notes |
| :--- | :--- | :--- | :--- |
| **Total Warehouses** | $\sum \text{Warehouse}$ | `warehouses.id` | Global facility count. |
| **Active / Inactive Warehouses** | $\sum [\text{is\_active} = \text{True}]$ vs $\sum [\text{is\_active} = \text{False}]$ | `warehouses.is_active` | Operational readiness. |
| **Total Active Capacity** | $\sum_{\text{active}} \text{capacity}$ | `warehouses.capacity` | Gross capacity across active fulfillment centers. |
| **Total Inventory Quantity** | $\sum \text{Inventory.quantity}$ | `inventory.quantity` | Sum of physical stock units on site. |
| **Overall Capacity Utilization** | $\min\left(100.0, \frac{\text{Total Inventory Quantity}}{\text{Total Active Capacity}} \times 100\%\right)$ | `inventory`, `warehouses` | Network-wide facility volume saturation. |
| **Warehouse Capacity Utilization** | $\min\left(100.0, \frac{\sum \text{stock at facility}}{\text{capacity of facility}} \times 100\%\right)$ | `inventory`, `warehouses` | Per-facility capacity utilization rate. |
| **Low Stock Items Count** | $\sum [\text{quantity} \le \text{reorder\_level}]$ | `inventory.quantity`, `inventory.reorder_level` | Inventory lines triggering replenishment warnings. |

### 2.3 Driver Workforce KPIs

| KPI Name | Formula / Derivation | Data Source | Notes |
| :--- | :--- | :--- | :--- |
| **Total Drivers** | $\sum \text{Driver}$ | `drivers.id` | Registered field drivers. |
| **Active Drivers** | $\sum [\text{User.is\_active} = \text{True}]$ | `drivers.user_id` $\to$ `users.is_active` | Drivers with active login accounts. |
| **Status Distribution** | Group-by `availability_status` (`AVAILABLE`, `ON_DUTY`, `IN_TRANSIT`, `OFF_DUTY`, `SUSPENDED`) | `drivers.availability_status` | Workforce allocation breakdown. |
| **Driver Utilization Rate** | $\frac{\text{Count}(\text{ON\_DUTY} + \text{IN\_TRANSIT})}{\text{Active Drivers}} \times 100\%$ | `drivers.availability_status` | Percentage of active workforce actively assigned to dispatch or line-haul movement. |
| **Active Shipments Per Driver** | $\sum [\text{assigned\_driver\_id} = \text{driver.id} \land \text{is\_active} = \text{True} \land \text{status is active}]$ | `shipments.assigned_driver_id` | Individual driver workload. |

### 2.4 Vehicle Fleet KPIs

| KPI Name | Formula / Derivation | Data Source | Notes |
| :--- | :--- | :--- | :--- |
| **Total Vehicles** | $\sum \text{Vehicle}$ | `vehicles.id` | Total fleet transport units. |
| **Status Distribution** | Group-by `status` (`AVAILABLE`, `IN_USE`, `MAINTENANCE`, `DECOMMISSIONED`) | `vehicles.status` | Fleet operational readiness. |
| **Vehicle Type Distribution** | Group-by `vehicle_type` (`Van`, `Box Truck`, `Semi-Trailer`, etc.) | `vehicles.vehicle_type` | Fleet asset composition. |
| **Total Fleet Capacity (kg)** | $\sum \text{Vehicle.capacity}$ | `vehicles.capacity` | Combined weight carrying capability. |
| **Vehicle Utilization Rate** | $\frac{\text{Count}(\text{IN\_USE})}{\text{Total Vehicles}} \times 100\%$ | `vehicles.status` | Fleet deployment efficiency. |
| **Active Shipments Per Vehicle** | $\sum [\text{assigned\_vehicle\_id} = \text{vehicle.id} \land \text{is\_active} = \text{True} \land \text{status is active}]$ | `shipments.assigned_vehicle_id` | Individual transport unit cargo allocations. |

---

## 3. AI Baseline Metrics

Before training machine learning models, baseline heuristics represent the standard against which predictive models must demonstrate quantifiable improvement:

1. **Duration Baseline (Simple Historical Mean)**:
   - Metric: Historical `average_delivery_duration_hours`.
   - Use-case: An ETA regression model (XGBoost / LightGBM) must achieve a lower Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) than simply predicting the historical average transit duration.
2. **Delay Frequency Baseline (Majority Class Classifier)**:
   - Metric: Historical `on_time_delivery_rate` vs `late_delivery_rate`.
   - Use-case: A binary delay classification model must outperform the naive majority-class baseline (e.g. predicting "On Time" for 100% of shipments).
3. **Delay Magnitude Baseline**:
   - Metric: Historical `average_delay_duration_hours`.
   - Use-case: When a delay is predicted, regression on delay magnitude must outperform the static average delay duration.

---

## 4. API Endpoints Reference

All analytics endpoints reside under `/api/v1/analytics` and are accessible to all authenticated roles (`ADMIN`, `MANAGER`, `DRIVER`, `VIEWER`). Unauthenticated requests are rejected with `HTTP 401 Unauthorized`.

| Method | Path | Parameters | Response Model | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/analytics/overview` | `start_date`, `end_date` | `OverviewAnalyticsResponse` | Executive summary metrics across all pillars. |
| `GET` | `/api/v1/analytics/shipments` | `start_date`, `end_date` | `ShipmentAnalyticsResponse` | Throughput, status counts, on-time rates, and delays. |
| `GET` | `/api/v1/analytics/inventory` | None | `InventoryAnalyticsResponse` | Global stock, safety thresholds, and warehouse breakdowns. |
| `GET` | `/api/v1/analytics/warehouses` | None | `WarehouseAnalyticsResponse` | Facility profiles and capacity utilization rates. |
| `GET` | `/api/v1/analytics/routes` | `start_date`, `end_date` | `RouteAnalyticsResponse` | Corridors, completion status, and shipment density. |
| `GET` | `/api/v1/analytics/drivers` | None | `DriverAnalyticsResponse` | Driver workforce status distribution and utilization rate. |
| `GET` | `/api/v1/analytics/vehicles` | None | `VehicleAnalyticsResponse` | Vehicle status distribution, carrying capacity, and utilization. |

---

## 5. Frontend Dashboard Integration

1. **API Client (`frontend/src/api/analytics.js`)**:
   - Added `getDriverAnalytics()` and `getVehicleAnalytics()`.
2. **Data Hook (`frontend/src/hooks/useDashboardData.js`)**:
   - Executes parallel, resilient queries via `Promise.allSettled`.
   - Exposes `driverAnalytics`, `vehicleAnalytics`, and computed delivery performance indicators.
   - Updates executive KPI cards with on-time delivery rates, average transit duration, and delay duration indicators.
3. **Theme & Design Consistency**:
   - Preserves Deep Tech Blue aesthetic and responsive CSS grid (`.metrics-grid`).
   - Skeletons displayed during telemetry synchronization.
