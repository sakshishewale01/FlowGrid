# FlowGrid AI-Ready Data Pipeline (Phase 21)

## 1. Overview & Purpose

FlowGrid Phase 21 establishes a production-grade, reproducible data pipeline that extracts and transforms operational shipment, fleet, facility, and routing data into an ML-ready dataset.

The pipeline is explicitly designed to support two primary downstream predictive modeling use-cases in future phases without implementing ML prediction models or adding heavyweight ML dependencies yet:

1. **Estimated Time of Arrival (ETA) / Delivery Duration Prediction**: Continuous regression predicting the elapsed transit time (`actual_duration_hours`).
2. **Shipment Delay Classification**: Binary and continuous prediction identifying whether a dispatch will exceed its planned corridor duration (`is_delayed`, `delay_hours`).

---

## 2. Pipeline Architecture

```
+-------------------------------------------------------------------------+
|                       OPERATIONAL DATA SOURCES                          |
|  [Shipments]    [Warehouses]    [Drivers]    [Vehicles]    [Routes]     |
|                       [ShipmentStatusHistory]                           |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  1. FEATURE EXTRACTOR (Safe Reading)                   |
|  - Eager joined loads of relational entities                            |
|  - Timestamp milestone parsing (PICKED_UP, IN_TRANSIT, DELIVERED)        |
|  - Audit history scan for delay remarks/events                          |
|  - Complete PII Redaction (strips emails, phone numbers, passwords)     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                 2. FEATURE ENGINEER (Leakage Prevention)                |
|  - Pre-dispatch operational features (Weight, Volume, Destinations)     |
|  - Derived temporal features (Hour, Day of Week, Month, Weekend)       |
|  - Fleet capacity utilization (Weight / Vehicle Capacity)               |
|  - Post-dispatch targets strictly isolated to completed deliveries      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                   3. QUALITY CHECKER & AUDIT SUITE                      |
|  - Missing values distribution tracking                                 |
|  - Non-negative bounds (Weight, Volume, Capacity > 0)                   |
|  - Timestamp ordering (Pickup <= Delivery)                              |
|  - Duration plausibility (0 < Hours <= 720)                             |
|  - Anti-leakage guard: Undelivered shipments must have None for targets |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                 4. CHRONOLOGICAL PARTITION & EXPORT                     |
|  - Strictly temporal train/test split (Prevents temporal lookahead)     |
|  - Deterministic export to RFC 4180 CSV and structured JSON             |
|  - Exposed via REST API (/api/v1/pipeline) & CLI utility               |
+-------------------------------------------------------------------------+
```

---

## 3. Feature Dictionary

The pipeline categorizes all fields into four explicit categories:

### A. Raw Operational Features (Known at Dispatch)
Extracted directly from operational relational tables:

| Column Name | Type | Description | Supports Missing |
| :--- | :--- | :--- | :--- |
| `shipment_id` | `int` | Unique database primary key | No |
| `tracking_number` | `str` | Public tracking identifier | No |
| `origin_warehouse_id` | `int` | Primary key of origin facility | Yes |
| `destination_city` | `str` | Municipality of destination | No |
| `destination_state` | `str` | State / province of destination | No |
| `destination_postal_code` | `str` | ZIP / postal code | No |
| `cargo_weight_kg` | `float` | Weight of shipment in kilograms | Yes |
| `cargo_volume_cbm` | `float` | Volume in cubic meters | Yes |
| `shipment_status` | `str` | Lifecycle state (`CREATED`, `IN_TRANSIT`, etc.) | No |
| `assigned_driver_id` | `int` | Driver ID (anonymized, no PII) | Yes |
| `driver_is_active` | `bool` | Driver user account status | Yes |
| `driver_availability_status` | `str` | Driver availability status at assignment | Yes |
| `assigned_vehicle_id` | `int` | Vehicle ID | Yes |
| `vehicle_type` | `str` | Vehicle classification (`Box Truck`, etc.) | Yes |
| `vehicle_capacity_kg` | `float` | Carrying limit in kilograms | Yes |
| `vehicle_status` | `str` | Vehicle fleet status | Yes |
| `warehouse_name` | `str` | Origin facility identifier | Yes |
| `warehouse_location` | `str` | Geographic region of origin facility | Yes |
| `warehouse_capacity` | `int` | Storage capacity of facility | Yes |
| `route_id` | `int` | Assigned transit corridor | Yes |
| `route_name` | `str` | Human-readable route name | Yes |
| `planned_distance_km` | `float` | Route estimated distance | Yes |
| `planned_duration_hours` | `float` | Route estimated duration | Yes |

### B. Derived Features (Engineered at Dispatch)
Synthesized mathematically from raw operational fields:

| Column Name | Type | Formula / Logic |
| :--- | :--- | :--- |
| `has_driver_assigned` | `int` (0/1) | `1 if driver_id else 0` |
| `has_vehicle_assigned` | `int` (0/1) | `1 if vehicle_id else 0` |
| `has_route_assigned` | `int` (0/1) | `1 if route_id else 0` |
| `weight_capacity_utilization` | `float` | $\min(1.0, \text{weight} / \text{capacity})$ |
| `scheduled_pickup_hour` | `int` (0-23) | Extracted hour of pickup |
| `scheduled_pickup_day_of_week` | `int` (0-6) | 0 = Monday, ..., 6 = Sunday |
| `scheduled_pickup_month` | `int` (1-12) | Calendar month |
| `is_weekend` | `int` (0/1) | `1 if day_of_week in (5, 6) else 0` |
| `is_interstate` | `int` (0/1) | `1 if destination_state not in warehouse_location else 0` |
| `historical_delay_signals_count` | `int` | Count of prior `FAILED` statuses or delay notes |

### C. Supervised Target Variables (Labels for ML Training)
**STRICTLY ISOLATED TO COMPLETED/DELIVERED SHIPMENTS**:

| Column Name | Type | Mathematical Definition | Leakage Mitigation |
| :--- | :--- | :--- | :--- |
| `actual_duration_hours` | `float` | $(t_{\text{delivered}} - t_{\text{actual\_pickup}}) / 3600$ | `None` for undelivered shipments. |
| `is_delayed` | `int` (0/1) | `1 if actual_duration > planned_duration + 0.1 else 0` | Excluded from input features; verified by quality audit. |
| `delay_hours` | `float` | $\max(0.0, \text{actual\_duration} - \text{planned\_duration})$ | Derived exclusively post-delivery. |

### D. Deferred Telematics & Environmental Fields
Fields documented for future IoT / external service integration:

- `realtime_gps_lat_lng`: Continuous live vehicle telematics.
- `weather_precipitation_index`: Route weather impact metrics.
- `corridor_traffic_congestion_level`: Live third-party road congestion telemetry.

---

## 4. Data Leakage & Temporal Integrity Rules

1. **Target Variable Quarantine**:
   - `actual_duration_hours`, `is_delayed`, and `delay_hours` are **never** populated for shipments with status other than `DELIVERED`.
   - The data quality checker automatically halts and marks datasets as `is_valid_for_training = False` if an undelivered shipment contains populated target labels.

2. **Temporal (Chronological) Splitting**:
   - Standard random train/test splitting (e.g., $K$-fold cross-validation or random $80/20$ splits) produces severe temporal lookahead bias in time-series and dispatch data.
   - FlowGrid enforces deterministic chronological ordering:
     $$\text{Train Set} = \{r \mid t_r \le t_{\text{cutoff}}\}, \quad \text{Test Set} = \{r \mid t_r > t_{\text{cutoff}}\}$$
   - This ensures models are evaluated strictly on their ability to forecast future dispatches using only historical patterns.

---

## 5. Usage & Integration

### CLI Tool Usage

Generate, audit, split, and export datasets from the terminal:

```bash
# Export delivered and active dispatches to CSVs and quality report
python scripts/export_ml_dataset.py --output-dir ./ml_exports --train-ratio 0.8 --include-undelivered
```

Output files produced:
- `ml_exports/train_dataset.csv`: Historical training partition.
- `ml_exports/test_dataset.csv`: Future evaluation partition.
- `ml_exports/full_dataset.csv`: Consolidated dataset.
- `ml_exports/data_quality_report.json`: Quality report with missing value rates, clean record counts, and leakage validation.

### REST API Integration

Authorized `ADMIN` and `MANAGER` roles can interact with the pipeline via HTTP:

- `GET /api/v1/pipeline/schema`: Retrieves the full feature dictionary.
- `GET /api/v1/pipeline/quality-report`: Audits live operational database records.
- `GET /api/v1/pipeline/dataset?split=true&train_ratio=0.8`: Returns chronologically partitioned JSON records.
- `GET /api/v1/pipeline/export/csv`: Streams or downloads the RFC 4180 CSV export.

---

## 6. Blueprint for Phase 22 (Future Model Training)

When Phase 22 begins model training:
1. Ingest `train_dataset.csv` and `test_dataset.csv` generated by this pipeline.
2. Select target: `actual_duration_hours` (for regression ETA) or `is_delayed` (for classification).
3. Use only `RAW_FEATURE` and `DERIVED_FEATURE` columns as model inputs ($X$).
4. Evaluate model performance against the strictly chronological `test_dataset.csv` ($y_{\text{test}}$).
