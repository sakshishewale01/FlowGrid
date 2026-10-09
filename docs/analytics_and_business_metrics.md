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
| `GET` | `/api/v1/analytics/delay-risk` | `shipment_id`, `status`, `risk_category`, `skip`, `limit` | `DelayRiskAnalyticsResponse` | Fleetwide explainable delay risk evaluations and fleet risk summary. |
| `GET` | `/api/v1/analytics/delay-risk/{shipment_id}` | Path: `shipment_id` | `ShipmentDelayRiskResponse` | Single shipment explainable delay risk score, category, and factor breakdown. |

---

## 5. Explainable Delay Risk Scoring (Phase 24.2)

FlowGrid Phase 24.2 introduces a deterministic, explainable operational risk engine that scores shipment delay risk on a scale of **0–100**.

### 5.1 Scoring Rubric & Weights

Points accumulate additively based on real-time operational bottlenecks, clamped to $[0, 100]$:

| Operational Dimension | Factor Code | Condition | Points | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Driver Assignment** | `UNASSIGNED_DRIVER` | `assigned_driver_id` is null | +20 | HIGH |
| **Vehicle Assignment** | `UNASSIGNED_VEHICLE` | `assigned_vehicle_id` is null | +15 | MEDIUM |
| **Route Assignment** | `UNASSIGNED_ROUTE` | `route_id` is null | +10 | MEDIUM |
| **Capacity Strain** | `CRITICAL_CAPACITY_STRAIN` | Cargo weight / Vehicle capacity > 90% | +20 | HIGH |
| **Capacity Strain** | `HIGH_CAPACITY_UTILIZATION` | Cargo weight / Vehicle capacity 80%–90% | +10 | MEDIUM |
| **Transit Corridor** | `INTERSTATE_TRANSIT` | Origin State $\neq$ Destination State | +15 | MEDIUM |
| **Origin Congestion** | `CRITICAL_WAREHOUSE_CONGESTION` | Warehouse inventory / capacity > 85% | +20 | HIGH |
| **Origin Congestion** | `MODERATE_WAREHOUSE_CONGESTION` | Warehouse inventory / capacity 75%–85% | +10 | MEDIUM |
| **Delivery Exception** | `PRIOR_DELIVERY_FAILURE` | Shipment status is `FAILED` | +15 | HIGH |

- **Terminal States**: Delivered shipments receive score `0` (`COMPLETED`), cancelled shipments receive score `0` (`CANCELLED`), and returned shipments receive score `0` (`RETURNED`).
- **Risk Tiers**:
  - `0 – 29`: `LOW`
  - `30 – 59`: `MEDIUM`
  - `60 – 79`: `HIGH`
  - `80 – 100`: `CRITICAL`
- **Missing Data Safety**: If weight, capacity, or warehouse metrics are missing/null, calculations fail safely to 0 points without division-by-zero or hallucinated figures.
- **Explainability**: Every response returns `contributing_factors` (with code, severity, impact points, and human-readable context) and a synthesis `explanation`. Explicitly flags `is_calibrated_probability = False`.

---

## 6. Frontend Dashboard & Drawer Integration

1. **API Client (`frontend/src/api/analytics.js`)**:
   - Added `getDelayRisk(params)` and `getShipmentDelayRisk(shipmentId)`.
2. **Waybill Drawer (`frontend/src/components/ShipmentDetailDrawer.jsx`)**:
   - **Overview Tab (TAB 1)**: Embedded Delay Risk Snapshot Card showing score circle, category badge, explanation, and deep link button.
   - **Dedicated Delay Risk Tab (TAB 4)**: Full explainable breakdown with score gauge, calibration warning, contributing factor cards (+pts), and diagnostic checklist of operational parameters.
   - **Real-Time Reactivity**: Automatically refreshes risk evaluation upon driver/vehicle assignment, status advancement, WebSocket events, and manual telemetry refresh.

