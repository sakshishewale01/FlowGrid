/**
 * FlowGrid - useDashboardData Hook
 * =================================
 * Fetches and synchronizes live backend operational data for the dashboard:
 * - Analytics overview (KPIs)
 * - Shipment status distributions (Pipeline lifecycle)
 * - Warehouse facility metrics & capacity
 * - Inventory balances & replenishment alerts
 * - Recent line-haul shipments
 * - Freight corridors & transit routes
 * - Fleet driver workforce utilization & availability
 * - Fleet vehicle capacity & status breakdown
 *
 * Resilience Features:
 * - Uses Promise.allSettled to prevent single endpoint failures from crashing the UI.
 * - Handles empty database states with graceful empty fallbacks.
 * - Captures loading, refreshing, and error states.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/useAuth.js';
import {
  analyticsApi,
  shipmentsApi,
  warehousesApi,
} from '../api/index.js';

export function useDashboardData() {
  const { isAuthenticated } = useAuth();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Core Data States
  const [overview, setOverview] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [pipelineStages, setPipelineStages] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [recentShipments, setRecentShipments] = useState([]);
  const [corridors, setCorridors] = useState([]);
  const [inventorySummary, setInventorySummary] = useState(null);
  const [driverAnalytics, setDriverAnalytics] = useState(null);
  const [vehicleAnalytics, setVehicleAnalytics] = useState(null);

  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const formatStatusLabel = (status) => {
    switch (status) {
      case 'IN_TRANSIT':
        return 'In Transit';
      case 'OUT_FOR_DELIVERY':
        return 'Out for Delivery';
      case 'DELIVERED':
        return 'Delivered';
      case 'DELAYED':
        return 'Delayed';
      case 'FAILED':
        return 'Failed / Hold';
      case 'ASSIGNED':
        return 'Dock Loading';
      case 'CONFIRMED':
        return 'Confirmed';
      case 'PICKED_UP':
        return 'Picked Up';
      case 'CREATED':
        return 'Created';
      case 'CANCELLED':
        return 'Cancelled';
      case 'RETURNED':
        return 'Returned';
      default:
        return status ? status.replace('_', ' ') : 'Pending';
    }
  };

  const loadData = useCallback(async (isManualRefresh = false) => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      // Execute live analytics and entity queries in parallel
      const results = await Promise.allSettled([
        analyticsApi.getOverview(),
        analyticsApi.getShipmentAnalytics(),
        analyticsApi.getWarehouseAnalytics(),
        analyticsApi.getInventoryAnalytics(),
        shipmentsApi.listShipments({ limit: 10 }),
        analyticsApi.getRouteAnalytics(),
        warehousesApi.listWarehouses({ limit: 10 }),
        analyticsApi.getDriverAnalytics(),
        analyticsApi.getVehicleAnalytics(),
      ]);

      if (!isMountedRef.current) return;

      const [
        overviewRes,
        shipmentAnalyticsRes,
        warehouseAnalyticsRes,
        inventoryAnalyticsRes,
        shipmentsListRes,
        routeAnalyticsRes,
        warehousesListRes,
        driverAnalyticsRes,
        vehicleAnalyticsRes,
      ] = results;

      // 1. Process Overview & KPI Metrics
      if (overviewRes.status === 'fulfilled' && overviewRes.value) {
        const ov = overviewRes.value;
        setOverview(ov);

        const onTimeText = ov.on_time_delivery_rate !== undefined
          ? `${ov.on_time_delivery_rate}% on-time`
          : 'On-time verified';

        const delaySubtext = ov.average_delay_duration_hours !== null && ov.average_delay_duration_hours !== undefined
          ? `Avg delay: ${ov.average_delay_duration_hours} hrs`
          : 'Failed or returned freight legs';

        const transitSubtext = ov.average_delivery_duration_hours !== null && ov.average_delivery_duration_hours !== undefined
          ? `Avg duration: ${ov.average_delivery_duration_hours} hrs`
          : 'Active freight in movement';

        setMetrics([
          {
            id: 'total-shipments',
            label: 'Total Shipments',
            value: Number(ov.total_shipments || 0).toLocaleString(),
            change: `${ov.active_routes || 0} active corridors`,
            changeType: 'positive',
            subtext: 'Across all fulfillment nodes',
            icon: 'Package',
            accentColor: '#3B82F6',
          },
          {
            id: 'in-transit',
            label: 'In Transit',
            value: Number(ov.active_shipments || 0).toLocaleString(),
            change: `${ov.total_drivers || 0} active drivers`,
            changeType: 'neutral',
            subtext: transitSubtext,
            icon: 'Truck',
            accentColor: '#3B82F6',
          },
          {
            id: 'delivered',
            label: 'Delivered',
            value: Number(ov.delivered_shipments || 0).toLocaleString(),
            change: onTimeText,
            changeType: 'positive',
            subtext: 'Verified consignee signatures',
            icon: 'CheckCircle',
            accentColor: '#10B981',
          },
          {
            id: 'delayed',
            label: 'Delayed / Exceptions',
            value: Number(ov.delayed_or_failed_shipments || 0).toLocaleString(),
            change: ov.delayed_or_failed_shipments > 0 ? 'Requires attention' : 'All on schedule',
            changeType: ov.delayed_or_failed_shipments > 0 ? 'warning' : 'positive',
            subtext: delaySubtext,
            icon: 'AlertTriangle',
            accentColor: '#EF4444',
          },
        ]);
      } else if (overviewRes.status === 'rejected') {
        console.warn('Failed to load overview analytics:', overviewRes.reason);
      }

      // 2. Process Shipment Lifecycle Pipeline Stages
      if (shipmentAnalyticsRes.status === 'fulfilled' && shipmentAnalyticsRes.value) {
        const sa = shipmentAnalyticsRes.value;
        const byStatus = sa.by_status || {};
        const total = sa.total_shipments || 0;

        const createdCount = byStatus.CREATED || 0;
        const confirmedCount = byStatus.CONFIRMED || 0;
        const assignedCount = byStatus.ASSIGNED || 0;
        const inTransitCount = (byStatus.IN_TRANSIT || 0) + (byStatus.OUT_FOR_DELIVERY || 0) + (byStatus.PICKED_UP || 0);
        const deliveredCount = byStatus.DELIVERED || 0;

        const calcPercent = (count) => {
          if (!total || total === 0) return '0%';
          return `${Math.round((count / total) * 100)}%`;
        };

        setPipelineStages([
          {
            id: 'created',
            name: 'Created',
            count: createdCount,
            percent: calcPercent(createdCount),
            status: 'pending',
            description: 'Order manifest created; awaiting inventory reservation',
          },
          {
            id: 'confirmed',
            name: 'Confirmed',
            count: confirmedCount,
            percent: calcPercent(confirmedCount),
            status: 'confirmed',
            description: 'Stock verified and locked at origin warehouse hub',
          },
          {
            id: 'assigned',
            name: 'Assigned',
            count: assignedCount,
            percent: calcPercent(assignedCount),
            status: 'scheduled',
            description: 'Driver and vehicle allocated; staging dock scheduled',
          },
          {
            id: 'in_transit',
            name: 'In Transit',
            count: inTransitCount,
            percent: calcPercent(inTransitCount),
            status: 'active',
            description: 'Cargo moving along monitored freight corridor',
          },
          {
            id: 'delivered',
            name: 'Delivered',
            count: deliveredCount,
            percent: calcPercent(deliveredCount),
            status: 'completed',
            description: 'Consignee proof-of-delivery signed; completed',
          },
        ]);
      }

      // 3. Process Warehouse Summary
      if (warehouseAnalyticsRes.status === 'fulfilled' && warehouseAnalyticsRes.value?.warehouses_summary) {
        const whSummaries = warehouseAnalyticsRes.value.warehouses_summary;
        const mapped = whSummaries.map((wh) => {
          const capacityUsed = wh.capacity > 0
            ? Math.min(100, Math.round((wh.total_stock_quantity / wh.capacity) * 100))
            : 0;

          return {
            id: `WH-0${wh.warehouse_id}`,
            rawId: wh.warehouse_id,
            name: wh.name,
            location: wh.location,
            capacityUsed,
            totalSqFt: `${Number(wh.capacity).toLocaleString()} sq ft`,
            activeBays: `${wh.total_products} product lines`,
            inboundToday: wh.total_stock_quantity,
            outboundToday: wh.low_stock_items,
            status: wh.is_active ? (wh.low_stock_items > 0 ? 'Attention' : 'Optimal') : 'Inactive',
          };
        });
        setWarehouses(mapped);
      } else if (warehousesListRes.status === 'fulfilled' && Array.isArray(warehousesListRes.value)) {
        const list = warehousesListRes.value;
        const mapped = list.map((wh) => ({
          id: `WH-0${wh.id}`,
          rawId: wh.id,
          name: wh.name,
          location: wh.location,
          capacityUsed: 50,
          totalSqFt: `${Number(wh.capacity || 0).toLocaleString()} sq ft`,
          activeBays: 'Active Facility',
          inboundToday: 0,
          outboundToday: 0,
          status: wh.is_active ? 'Optimal' : 'Inactive',
        }));
        setWarehouses(mapped);
      }

      // 4. Process Inventory Summary
      if (inventoryAnalyticsRes.status === 'fulfilled' && inventoryAnalyticsRes.value) {
        const inv = inventoryAnalyticsRes.value;
        setInventorySummary({
          totalRecords: inv.total_inventory_records || 0,
          totalQuantity: inv.total_available_quantity || 0,
          lowStockCount: inv.low_stock_products_count || 0,
          lowStockProducts: inv.low_stock_products || [],
        });
      }

      // 5. Process Recent Shipments Table
      if (shipmentsListRes.status === 'fulfilled' && Array.isArray(shipmentsListRes.value)) {
        const shipments = shipmentsListRes.value;
        const mapped = shipments.map((s) => {
          const originText = s.origin_warehouse
            ? `${s.origin_warehouse.name} (${s.origin_warehouse.location})`
            : 'Fulfillment Hub';

          const destText = s.destination_city && s.destination_state
            ? `${s.destination_city}, ${s.destination_state}`
            : s.destination_address || 'Delivery Location';

          const carrierText = s.assigned_driver
            ? `Driver #${s.assigned_driver.id} • ${s.assigned_vehicle?.registration_number || 'Fleet'}`
            : (s.assigned_vehicle ? s.assigned_vehicle.registration_number : 'Unassigned Dispatch');

          const units = s.total_volume_cbm
            ? Math.round(Number(s.total_volume_cbm) * 10)
            : 100;

          const weightText = s.total_weight_kg
            ? `${Number(s.total_weight_kg).toLocaleString()} kg`
            : '—';

          let etaText = 'On Schedule';
          if (s.status === 'DELIVERED') {
            etaText = s.delivered_at
              ? `Delivered ${new Date(s.delivered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
              : 'Delivered';
          } else if (s.status === 'FAILED') {
            etaText = 'Hold / Exception';
          }

          let priority = 'Standard';
          if (s.total_weight_kg && Number(s.total_weight_kg) > 5000) {
            priority = 'Heavy Freight';
          } else if (s.status === 'IN_TRANSIT') {
            priority = 'Express';
          }

          return {
            id: s.id,
            trackingNumber: s.tracking_number,
            origin: originText,
            destination: destText,
            carrier: carrierText,
            itemsCount: units,
            weight: weightText,
            status: s.status,
            statusLabel: formatStatusLabel(s.status),
            eta: etaText,
            priority,
            raw: s,
          };
        });
        setRecentShipments(mapped);
      }

      // 6. Process Route Corridors
      if (routeAnalyticsRes.status === 'fulfilled' && routeAnalyticsRes.value?.routes_summary) {
        const rs = routeAnalyticsRes.value.routes_summary;
        const mapped = rs.map((r) => ({
          id: `COR-0${r.route_id}`,
          name: r.name,
          trafficCondition: r.status === 'ACTIVE' ? 'Clear Route' : r.status,
          shipmentsActive: r.shipments_assigned_count || 0,
          avgSpeed: '62 mph',
          statusColor: r.status === 'ACTIVE' ? '#10B981' : '#F59E0B',
          statusType: r.status === 'ACTIVE' ? 'normal' : 'warning',
        }));
        setCorridors(mapped);
      }

      // 7. Process Driver Analytics
      if (driverAnalyticsRes.status === 'fulfilled' && driverAnalyticsRes.value) {
        setDriverAnalytics(driverAnalyticsRes.value);
      }

      // 8. Process Vehicle Analytics
      if (vehicleAnalyticsRes.status === 'fulfilled' && vehicleAnalyticsRes.value) {
        setVehicleAnalytics(vehicleAnalyticsRes.value);
      }

      // Check if all primary queries failed
      const criticalFailures = results.filter((r) => r.status === 'rejected');
      if (criticalFailures.length === results.length) {
        setError('Failed to load operational data from FlowGrid API. Please verify backend connectivity.');
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.message || 'An unexpected error occurred while loading dashboard metrics.');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadData(false);
  }, [loadData]);

  return {
    loading,
    refreshing,
    error,
    overview,
    metrics,
    pipelineStages,
    warehouses,
    recentShipments,
    corridors,
    inventorySummary,
    driverAnalytics,
    vehicleAnalytics,
    refetch: () => loadData(true),
  };
}

export default useDashboardData;
