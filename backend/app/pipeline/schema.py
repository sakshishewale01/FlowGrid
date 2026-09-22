"""
FlowGrid - AI-Ready Data Pipeline Schema
========================================
Defines feature definitions, schemas, data quality issues, and Pydantic models
governing the extraction, engineering, and auditing of operational data for
future ML training.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class FeatureCategory(str, Enum):
    """
    Categorization of features in the FlowGrid AI pipeline.
    """
    RAW_FEATURE = "RAW_FEATURE"
    DERIVED_FEATURE = "DERIVED_FEATURE"
    TARGET_VARIABLE = "TARGET_VARIABLE"
    DEFERRED = "DEFERRED"


class FeatureDefinition(BaseModel):
    """
    Metadata describing an individual feature or target in the pipeline.
    """
    name: str = Field(..., description="Machine-readable column/feature name")
    category: FeatureCategory = Field(..., description="Pipeline classification")
    data_type: str = Field(..., description="Data type (float, int, str, bool, datetime)")
    description: str = Field(..., description="Detailed description of the feature")
    is_target: bool = Field(default=False, description="Whether this is a prediction label")
    supports_missing: bool = Field(default=True, description="Whether null values are permissible")
    leakage_mitigation: Optional[str] = Field(
        default=None,
        description="Explanation of how data leakage is prevented for this field",
    )


# ------------------------------------------------------------------------------
# Authoritative Pipeline Feature Dictionary
# ------------------------------------------------------------------------------
FEATURE_REGISTRY: List[FeatureDefinition] = [
    # --- RAW OPERATIONAL FEATURES ---
    FeatureDefinition(
        name="shipment_id",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Unique database primary key for the shipment",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="origin_warehouse_id",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Departure fulfillment hub identifier",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="destination_city",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Consignee delivery destination municipality",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="destination_state",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Consignee delivery destination state/province",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="destination_postal_code",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Consignee delivery postal code",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="cargo_weight_kg",
        category=FeatureCategory.RAW_FEATURE,
        data_type="float",
        description="Total cargo weight in kilograms",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="cargo_volume_cbm",
        category=FeatureCategory.RAW_FEATURE,
        data_type="float",
        description="Total cargo volume in cubic meters",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="shipment_status",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Current operational lifecycle status (e.g. CREATED, IN_TRANSIT, DELIVERED)",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="assigned_driver_id",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Anonymized ID of the allocated driver (PII redacted)",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="driver_availability_status",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Driver operational availability at allocation time",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="assigned_vehicle_id",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Allocated transport vehicle identifier",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="vehicle_type",
        category=FeatureCategory.RAW_FEATURE,
        data_type="str",
        description="Transport unit classification (e.g. Box Truck, Semi-Trailer)",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="vehicle_capacity_kg",
        category=FeatureCategory.RAW_FEATURE,
        data_type="float",
        description="Vehicle maximum carrying capacity in kilograms",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="warehouse_capacity",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Storage capacity of the origin fulfillment facility",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="route_id",
        category=FeatureCategory.RAW_FEATURE,
        data_type="int",
        description="Assigned logistics corridor identifier",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="planned_distance_km",
        category=FeatureCategory.RAW_FEATURE,
        data_type="float",
        description="Planned corridor transit distance from route table",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="planned_duration_hours",
        category=FeatureCategory.RAW_FEATURE,
        data_type="float",
        description="Planned transit duration from route table",
        supports_missing=True,
    ),

    # --- DERIVED FEATURES (ENGINEERED PRIOR TO DISPATCH) ---
    FeatureDefinition(
        name="has_driver_assigned",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Binary flag: 1 if driver allocated, 0 otherwise",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="has_vehicle_assigned",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Binary flag: 1 if vehicle allocated, 0 otherwise",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="has_route_assigned",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Binary flag: 1 if planned route allocated, 0 otherwise",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="weight_capacity_utilization",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="float",
        description="Ratio of cargo weight to vehicle carrying capacity (min(1.0, weight / capacity))",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="scheduled_pickup_hour",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Hour of day (0-23) for scheduled pickup",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="scheduled_pickup_day_of_week",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Day of week (0=Monday, 6=Sunday) for scheduled pickup",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="scheduled_pickup_month",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Calendar month (1-12) for scheduled pickup",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="is_weekend",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Binary indicator: 1 if scheduled pickup is Saturday or Sunday, 0 otherwise",
        supports_missing=True,
    ),
    FeatureDefinition(
        name="is_interstate",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Binary indicator: 1 if destination state differs from origin warehouse location",
        supports_missing=False,
    ),
    FeatureDefinition(
        name="historical_delay_signals_count",
        category=FeatureCategory.DERIVED_FEATURE,
        data_type="int",
        description="Count of historical failed status events or delay remarks recorded prior to transit",
        supports_missing=False,
    ),

    # --- TARGET VARIABLES (SUPERVISED LABELS) ---
    FeatureDefinition(
        name="actual_duration_hours",
        category=FeatureCategory.TARGET_VARIABLE,
        data_type="float",
        description="Observed delivery elapsed time: (actual_delivery - actual_pickup) in hours",
        is_target=True,
        supports_missing=True,
        leakage_mitigation="Only populated for DELIVERED shipments with valid timestamps. Excluded from input features.",
    ),
    FeatureDefinition(
        name="is_delayed",
        category=FeatureCategory.TARGET_VARIABLE,
        data_type="int",
        description="Binary label: 1 if delivery was delayed beyond planned duration or experienced failure, 0 otherwise",
        is_target=True,
        supports_missing=True,
        leakage_mitigation="Derived exclusively from completed delivery duration vs planned duration or terminal delivery state.",
    ),
    FeatureDefinition(
        name="delay_hours",
        category=FeatureCategory.TARGET_VARIABLE,
        data_type="float",
        description="Continuous delay quantity: max(0, actual_duration_hours - planned_duration_hours)",
        is_target=True,
        supports_missing=True,
        leakage_mitigation="Only calculated post-delivery; strictly isolated from model training input features.",
    ),

    # --- CURRENTLY UNAVAILABLE / DEFERRED FIELDS ---
    FeatureDefinition(
        name="realtime_gps_lat_lng",
        category=FeatureCategory.DEFERRED,
        data_type="str",
        description="Real-time continuous GPS telematics stream en route",
        supports_missing=True,
        leakage_mitigation="Deferred to Phase 22+ when active GPS IoT tracking is integrated.",
    ),
    FeatureDefinition(
        name="weather_precipitation_index",
        category=FeatureCategory.DEFERRED,
        data_type="float",
        description="Precipitation and storm severity along corridor during transit",
        supports_missing=True,
        leakage_mitigation="Deferred to future external meteorology API integration.",
    ),
    FeatureDefinition(
        name="corridor_traffic_congestion_level",
        category=FeatureCategory.DEFERRED,
        data_type="float",
        description="Live road traffic congestion index",
        supports_missing=True,
        leakage_mitigation="Deferred to future traffic telemetry integration.",
    ),
]


class DatasetRecord(BaseModel):
    """
    Flattened, type-safe ML record representing a single shipment entity.
    """
    # Identifiers & Metadata
    shipment_id: int
    tracking_number: str
    created_timestamp: str

    # Raw Operational Features
    origin_warehouse_id: Optional[int] = None
    destination_city: str
    destination_state: str
    destination_postal_code: str
    cargo_weight_kg: Optional[float] = None
    cargo_volume_cbm: Optional[float] = None
    shipment_status: str

    # Fleet & Facility Context
    assigned_driver_id: Optional[int] = None
    driver_is_active: Optional[bool] = None
    driver_availability_status: Optional[str] = None
    assigned_vehicle_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    vehicle_capacity_kg: Optional[float] = None
    vehicle_status: Optional[str] = None
    warehouse_name: Optional[str] = None
    warehouse_location: Optional[str] = None
    warehouse_capacity: Optional[int] = None

    # Corridor & Route Features
    route_id: Optional[int] = None
    route_name: Optional[str] = None
    planned_distance_km: Optional[float] = None
    planned_duration_hours: Optional[float] = None

    # Derived Features
    has_driver_assigned: int = 0
    has_vehicle_assigned: int = 0
    has_route_assigned: int = 0
    weight_capacity_utilization: Optional[float] = None
    scheduled_pickup_timestamp: Optional[str] = None
    scheduled_pickup_hour: Optional[int] = None
    scheduled_pickup_day_of_week: Optional[int] = None
    scheduled_pickup_month: Optional[int] = None
    is_weekend: Optional[int] = None
    is_interstate: int = 0
    historical_delay_signals_count: int = 0

    # Prediction Target Variables (None for undelivered shipments)
    actual_pickup_timestamp: Optional[str] = None
    actual_delivery_timestamp: Optional[str] = None
    actual_duration_hours: Optional[float] = None
    is_delayed: Optional[int] = None
    delay_hours: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DataQualityIssue(BaseModel):
    """
    Represents an anomalous, invalid, or suspicious observation in the ML pipeline.
    """
    issue_type: str = Field(..., description="Category (MISSING_VALUE, INVALID_TIMESTAMP, OUTLIER, LEAKAGE_RISK)")
    severity: str = Field(..., description="Severity level: WARNING or ERROR")
    field_name: str = Field(..., description="Column or attribute affected")
    record_id: Optional[int] = Field(None, description="Shipment ID if associated with a single record")
    details: str = Field(..., description="Explanatory diagnostics")


class DataQualityReport(BaseModel):
    """
    Comprehensive health audit summarizing dataset readiness for ML training.
    """
    total_records: int = 0
    clean_records: int = 0
    records_with_targets: int = 0
    missing_values_by_column: Dict[str, int] = Field(default_factory=dict)
    issues_count: int = 0
    issues: List[DataQualityIssue] = Field(default_factory=list)
    leakage_risk_detected: bool = False
    is_valid_for_training: bool = True
