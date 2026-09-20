"""
Analytics and Dashboard Schemas
===============================
Pydantic schemas for high-level operational KPIs, shipment throughput,
inventory balances, warehouse capacity, and route metrics.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OverviewAnalyticsResponse(BaseModel):
    """
    Consolidated executive metrics across all FlowGrid logistics pillars.
    """
    total_shipments: int = Field(..., description="Total shipments recorded in system")
    active_shipments: int = Field(..., description="Shipments currently undergoing active transit or processing")
    delivered_shipments: int = Field(..., description="Successfully delivered shipments")
    delayed_or_failed_shipments: int = Field(..., description="Shipments in FAILED or RETURNED state")
    total_warehouses: int = Field(..., description="Total warehouse facilities registered")
    total_products: int = Field(..., description="Total commercial SKUs in catalog")
    total_drivers: int = Field(..., description="Total field drivers in fleet")
    active_routes: int = Field(..., description="Active transit corridors and routes")

    model_config = ConfigDict(from_attributes=True)


class ShipmentDateCount(BaseModel):
    """
    Daily shipment creation volume.
    """
    date: str = Field(..., description="ISO calendar date string (YYYY-MM-DD)")
    count: int = Field(..., description="Number of shipments created on this date")

    model_config = ConfigDict(from_attributes=True)


class ShipmentAnalyticsResponse(BaseModel):
    """
    Detailed shipment lifecycle, status, and throughput analytics.
    """
    total_shipments: int = Field(..., description="Total shipments within the requested window")
    by_status: Dict[str, int] = Field(..., description="Shipment distribution grouped by status")
    by_date: List[ShipmentDateCount] = Field(default_factory=list, description="Chronological shipment volume")
    delivery_completion_rate: float = Field(..., description="Percentage of shipments delivered (0.0 to 100.0)")
    cancelled_shipments: int = Field(..., description="Shipments marked as CANCELLED")
    returned_shipments: int = Field(..., description="Shipments marked as RETURNED")

    model_config = ConfigDict(from_attributes=True)


class LowStockProductSummary(BaseModel):
    """
    Itemized summary of an inventory balance below or equal to reorder threshold.
    """
    product_id: int = Field(..., description="Product primary key ID")
    product_name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Stock keeping unit identifier")
    warehouse_id: int = Field(..., description="Warehouse facility ID")
    warehouse_name: str = Field(..., description="Warehouse facility name")
    quantity: int = Field(..., description="Current available balance")
    reorder_level: int = Field(..., description="Safety stock threshold level")

    model_config = ConfigDict(from_attributes=True)


class WarehouseInventoryBreakdown(BaseModel):
    """
    Aggregated inventory metrics grouped by warehouse facility.
    """
    warehouse_id: int = Field(..., description="Warehouse primary key ID")
    warehouse_name: str = Field(..., description="Warehouse name")
    total_quantity: int = Field(..., description="Sum of physical units stored")
    unique_products_count: int = Field(..., description="Number of distinct products stocked")
    low_stock_count: int = Field(..., description="Number of inventory items at or below reorder level")

    model_config = ConfigDict(from_attributes=True)


class InventoryAnalyticsResponse(BaseModel):
    """
    Global inventory balances, safety thresholds, and warehouse allocations.
    """
    total_inventory_records: int = Field(..., description="Total warehouse-product stock pairs")
    total_available_quantity: int = Field(..., description="Gross sum of physical units on hand")
    low_stock_products_count: int = Field(..., description="Total items triggering replenishment warnings")
    low_stock_products: List[LowStockProductSummary] = Field(default_factory=list, description="Itemized low stock warnings")
    by_warehouse: List[WarehouseInventoryBreakdown] = Field(default_factory=list, description="Facility-level inventory summary")

    model_config = ConfigDict(from_attributes=True)


class WarehouseSummaryItem(BaseModel):
    """
    Warehouse operational profile including capacity and inventory footprint.
    """
    warehouse_id: int = Field(..., description="Warehouse primary key ID")
    name: str = Field(..., description="Warehouse facility name")
    location: str = Field(..., description="City or regional hub location")
    capacity: int = Field(..., description="Max capacity in square feet or units")
    is_active: bool = Field(..., description="Operational status flag")
    total_products: int = Field(..., description="Number of distinct product lines stored")
    total_stock_quantity: int = Field(..., description="Gross physical items on site")
    low_stock_items: int = Field(..., description="Count of low stock items at this facility")

    model_config = ConfigDict(from_attributes=True)


class WarehouseAnalyticsResponse(BaseModel):
    """
    Consolidated warehouse network statistics.
    """
    total_warehouses: int = Field(..., description="Total warehouses in the network")
    active_warehouses: int = Field(..., description="Number of active warehouses")
    inactive_warehouses: int = Field(..., description="Number of inactive or decommissioned warehouses")
    warehouses_summary: List[WarehouseSummaryItem] = Field(default_factory=list, description="Detailed list of all facilities")

    model_config = ConfigDict(from_attributes=True)


class RouteSummaryItem(BaseModel):
    """
    Individual route overview with assigned shipment volume.
    """
    route_id: int = Field(..., description="Route primary key ID")
    name: str = Field(..., description="Route or corridor name")
    origin: str = Field(..., description="Origin location")
    destination: str = Field(..., description="Destination location")
    status: str = Field(..., description="Operational corridor status")
    is_active: bool = Field(..., description="Active route record flag")
    shipments_assigned_count: int = Field(..., description="Number of shipments currently linked to route")

    model_config = ConfigDict(from_attributes=True)


class RouteAnalyticsResponse(BaseModel):
    """
    Transit route utilization and shipment allocation analytics.
    """
    total_routes: int = Field(..., description="Total routes defined in system")
    active_routes: int = Field(..., description="Routes with status ACTIVE and is_active True")
    completed_routes: int = Field(..., description="Routes marked as COMPLETED")
    by_status: Dict[str, int] = Field(..., description="Route distribution grouped by status")
    total_shipments_assigned: int = Field(..., description="Total shipment allocations across all routes")
    routes_summary: List[RouteSummaryItem] = Field(default_factory=list, description="Corridor summary items")

    model_config = ConfigDict(from_attributes=True)
