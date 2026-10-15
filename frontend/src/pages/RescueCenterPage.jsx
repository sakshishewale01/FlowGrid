import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { shipmentsApi } from '../api/shipments.js';
import { analyticsApi } from '../api/analytics.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import EmptyState from '../components/EmptyState';
import StatusBadge from '../components/StatusBadge';
import ShipmentDetailDrawer from '../components/ShipmentDetailDrawer';
import DelayPredictionModal from '../components/DelayPredictionModal';
import { useToast } from '../context/ToastContext';

/**
 * Operational Rules applied to live shipment records.
 * Explicitly transparent and deterministic; grounded strictly in real database fields.
 */
function evaluateAttentionRules(shipment, riskData) {
  const flags = [];

  // Check shipment status exceptions
  if (shipment.status === 'FAILED') {
    flags.push({
      code: 'RULE-EX01',
      title: 'Dispatch / Transit Exception',
      category: 'EXCEPTION',
      severity: 'CRITICAL',
      ruleDescription: 'Shipment recorded a delivery failure or abort event.',
      recommendedAction: 'Review transit event history and re-dispatch or assign return protocol.',
      actionType: 'RESOLVE_EXCEPTION',
    });
  }

  // Check driver allocation
  if (!shipment.assigned_driver_id && !shipment.assigned_driver) {
    flags.push({
      code: 'RULE-R01',
      title: 'Unassigned Fleet Driver',
      category: 'MISSING_RESOURCE',
      severity: 'HIGH',
      ruleDescription: 'Shipment lacks an assigned driver profile, blocking scheduled dispatch.',
      recommendedAction: 'Allocate an available on-duty driver from fleet management.',
      actionType: 'ASSIGN_DRIVER',
    });
  }

  // Check vehicle allocation
  if (!shipment.assigned_vehicle_id && !shipment.assigned_vehicle) {
    flags.push({
      code: 'RULE-R02',
      title: 'Unassigned Transport Equipment',
      category: 'MISSING_RESOURCE',
      severity: 'MEDIUM',
      ruleDescription: 'No vehicle or trailer asset is allocated to this manifest.',
      recommendedAction: 'Allocate available transport unit matching cargo weight capacity.',
      actionType: 'ASSIGN_VEHICLE',
    });
  }

  // Check route corridor allocation
  if (riskData?.has_route_assigned === false) {
    flags.push({
      code: 'RULE-R03',
      title: 'Unassigned Transit Corridor',
      category: 'ROUTING',
      severity: 'MEDIUM',
      ruleDescription: 'No pre-planned freight corridor is linked, increasing transit variance.',
      recommendedAction: 'Assign an active line-haul corridor to stabilize transit ETA.',
      actionType: 'ASSIGN_ROUTE',
    });
  }

  // Check capacity strain
  if (riskData?.weight_capacity_utilization && riskData.weight_capacity_utilization > 0.85) {
    flags.push({
      code: 'RULE-R04',
      title: 'Vehicle Capacity Strain (>85%)',
      category: 'OVERLOAD',
      severity: riskData.weight_capacity_utilization > 0.90 ? 'CRITICAL' : 'HIGH',
      ruleDescription: `Cargo payload utilizes ${(riskData.weight_capacity_utilization * 100).toFixed(1)}% of vehicle limit.`,
      recommendedAction: 'Inspect vehicle axle balance or split cargo across multiple consignments.',
      actionType: 'INSPECT_CAPACITY',
    });
  }

  // Check interstate corridor
  if (riskData?.is_interstate) {
    flags.push({
      code: 'RULE-R05',
      title: 'Interstate Corridors Toll & Checkpoint Notice',
      category: 'CORRIDOR',
      severity: 'LOW',
      ruleDescription: `Cross-border leg from ${riskData.origin_warehouse_name || 'origin'} to ${riskData.destination_state}.`,
      recommendedAction: 'Monitor tollway checkpoints and interstate documentation compliance.',
      actionType: 'INSPECT_CORRIDOR',
    });
  }

  return flags;
}

export default function RescueCenterPage({ onNavigate }) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Raw data from endpoints
  const [shipments, setShipments] = useState([]);
  const [delayRiskMap, setDelayRiskMap] = useState({});
  const [fleetSummary, setFleetSummary] = useState(null);

  // Filters
  const [attentionFilter, setAttentionFilter] = useState('ATTENTION_ONLY'); // 'ATTENTION_ONLY' | 'MISSING_DRIVER' | 'MISSING_VEHICLE' | 'MISSING_ROUTE' | 'CRITICAL' | 'ALL'
  const [searchQuery, setSearchQuery] = useState('');

  // Drawers & Modals
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isMlModalOpen, setIsMlModalOpen] = useState(false);

  // Fetch actual operational data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [shipmentsRes, delayRiskRes] = await Promise.all([
        shipmentsApi.listShipments({ limit: 200 }),
        analyticsApi.getDelayRisk({ limit: 200 }),
      ]);

      const rawShipments = shipmentsRes || [];
      setShipments(rawShipments);

      // Build shipment_id -> delayRisk assessment map
      const rMap = {};
      if (delayRiskRes?.shipments && Array.isArray(delayRiskRes.shipments)) {
        delayRiskRes.shipments.forEach((item) => {
          rMap[item.shipment_id] = item;
        });
        setFleetSummary(delayRiskRes.summary);
      }
      setDelayRiskMap(rMap);
    } catch (err) {
      setError(formatErrorMessage(err, 'Failed to load shipment rescue data'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Combine shipments with evaluated rules
  const enrichedShipments = useMemo(() => {
    return shipments.map((s) => {
      const riskData = delayRiskMap[s.id] || null;
      const flags = evaluateAttentionRules(s, riskData);
      return {
        ...s,
        riskData,
        attentionFlags: flags,
        needsAttention: flags.length > 0,
      };
    });
  }, [shipments, delayRiskMap]);

  // Apply filters
  const filteredShipments = useMemo(() => {
    return enrichedShipments.filter((item) => {
      // Attention filter
      if (attentionFilter === 'ATTENTION_ONLY' && !item.needsAttention) return false;
      if (attentionFilter === 'MISSING_DRIVER' && !item.attentionFlags.some((f) => f.actionType === 'ASSIGN_DRIVER')) return false;
      if (attentionFilter === 'MISSING_VEHICLE' && !item.attentionFlags.some((f) => f.actionType === 'ASSIGN_VEHICLE')) return false;
      if (attentionFilter === 'MISSING_ROUTE' && !item.attentionFlags.some((f) => f.actionType === 'ASSIGN_ROUTE')) return false;
      if (attentionFilter === 'CRITICAL' && item.riskData?.risk_category !== 'CRITICAL' && item.status !== 'FAILED') return false;

      // Search query
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const trk = item.tracking_number?.toLowerCase() || '';
      const destCity = item.destination_city?.toLowerCase() || '';
      const destState = item.destination_state?.toLowerCase() || '';
      const originName = item.origin_warehouse?.name?.toLowerCase() || '';
      return trk.includes(q) || destCity.includes(q) || destState.includes(q) || originName.includes(q);
    });
  }, [enrichedShipments, attentionFilter, searchQuery]);

  // Metrics counts
  const totalMonitored = enrichedShipments.length;
  const attentionCount = enrichedShipments.filter((s) => s.needsAttention).length;
  const missingDriversCount = enrichedShipments.filter((s) => s.attentionFlags.some((f) => f.actionType === 'ASSIGN_DRIVER')).length;
  const missingVehiclesCount = enrichedShipments.filter((s) => s.attentionFlags.some((f) => f.actionType === 'ASSIGN_VEHICLE')).length;
  const missingRoutesCount = enrichedShipments.filter((s) => s.attentionFlags.some((f) => f.actionType === 'ASSIGN_ROUTE')).length;

  const handleOpenDrawer = (shipment) => {
    setSelectedShipment(shipment);
    setIsDrawerOpen(true);
  };

  const handleShipmentUpdated = () => {
    fetchData();
  };

  const columns = useMemo(() => [
    {
      key: 'tracking_number',
      header: 'Shipment Waybill',
      sortable: true,
      render: (s) => (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38BDF8', fontSize: '0.9rem' }}>
            {s.tracking_number}
          </span>
          <span style={{ fontSize: '0.72rem', color: '#64748B' }}>
            ID #{s.id} • {s.total_weight_kg ? `${Number(s.total_weight_kg).toLocaleString()} kg` : 'Payload unstated'}
          </span>
        </div>
      ),
    },
    {
      key: 'corridor',
      header: 'Corridor & Staging',
      render: (s) => (
        <div>
          <div className="table-primary-text" style={{ fontSize: '0.82rem' }}>
            {s.origin_warehouse?.name || 'Origin Hub'} → {s.destination_city}, {s.destination_state}
          </div>
          <span className="table-secondary-text" style={{ fontSize: '0.72rem' }}>
            {s.destination_address}
          </span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Operational Status',
      render: (s) => <StatusBadge status={s.status} />,
    },
    {
      key: 'attention_rules',
      header: 'Triggered Operational Rules',
      render: (s) => {
        if (!s.attentionFlags || s.attentionFlags.length === 0) {
          return (
            <span style={{ fontSize: '0.75rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
              ✓ All allocations verified
            </span>
          );
        }
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '280px' }}>
            {s.attentionFlags.map((flag) => {
              const badgeBg =
                flag.severity === 'CRITICAL'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : flag.severity === 'HIGH'
                  ? 'rgba(245, 158, 11, 0.15)'
                  : 'rgba(56, 189, 248, 0.12)';
              const badgeColor =
                flag.severity === 'CRITICAL'
                  ? '#EF4444'
                  : flag.severity === 'HIGH'
                  ? '#F59E0B'
                  : '#38BDF8';
              return (
                <div
                  key={flag.code}
                  style={{
                    backgroundColor: badgeBg,
                    border: `1px solid ${badgeColor}40`,
                    color: badgeColor,
                    borderRadius: '4px',
                    padding: '3px 6px',
                    fontSize: '0.7rem',
                    lineHeight: '1.2',
                  }}
                  title={flag.ruleDescription}
                >
                  <strong style={{ marginRight: '4px' }}>[{flag.code}]</strong>
                  <span>{flag.title}</span>
                </div>
              );
            })}
          </div>
        );
      },
    },
    {
      key: 'delay_risk',
      header: 'Heuristic Risk Score',
      render: (s) => {
        const score = s.riskData?.risk_score ?? 0;
        const color = score >= 70 ? '#EF4444' : score >= 40 ? '#F59E0B' : '#10B981';
        return (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 700, color, fontSize: '0.92rem' }}>
                {s.riskData ? `${score}/100` : '—'}
              </span>
              {s.riskData?.risk_category && (
                <span
                  className={`status-badge badge-${s.riskData.risk_category.toLowerCase()}`}
                  style={{ fontSize: '0.65rem', padding: '1px 5px' }}
                >
                  {s.riskData.risk_category}
                </span>
              )}
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748B', display: 'block', marginTop: '2px' }}>
              Rule-based Heuristic
            </span>
          </div>
        );
      },
    },
    {
      key: 'recommended_action',
      header: 'Recommended Next Action',
      render: (s) => {
        const primaryFlag = s.attentionFlags?.[0];
        const actionLabel = primaryFlag ? primaryFlag.recommendedAction : 'Dispatch on schedule';
        return (
          <div style={{ maxWidth: '240px' }}>
            <span style={{ fontSize: '0.74rem', color: '#CBD5E1', display: 'block', lineHeight: '1.3' }}>
              {actionLabel}
            </span>
          </div>
        );
      },
    },
    {
      key: 'actions',
      header: 'Triage Actions',
      align: 'right',
      render: (s) => (
        <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="btn-action primary"
            style={{ padding: '4px 10px', fontSize: '0.72rem' }}
            onClick={(e) => {
              e.stopPropagation();
              handleOpenDrawer(s);
            }}
            title="Inspect shipment, allocate missing resources, or advance status"
          >
            Resolve / Edit →
          </button>
        </div>
      ),
    },
  ], []);

  return (
    <div className="management-page" id="shipment-rescue-center-page">
      <PageHeader
        section="OPERATIONS CONTROL / DETECT"
        title="Shipment Rescue Center"
        caption="Real-time detection of operational bottlenecks, unassigned fleet assets, and staging exceptions across active shipments."
        metaPills={[
          { label: 'Active Shipments', value: totalMonitored },
          { label: 'Needs Attention', value: attentionCount, status: attentionCount > 0 ? 'warning' : 'online' },
          { label: 'Unassigned Drivers', value: missingDriversCount, status: missingDriversCount > 0 ? 'warning' : 'online' },
          { label: 'Unassigned Vehicles', value: missingVehiclesCount, status: missingVehiclesCount > 0 ? 'warning' : 'online' },
          { label: 'Unassigned Routes', value: missingRoutesCount, status: missingRoutesCount > 0 ? 'warning' : 'online' },
        ]}
        primaryAction={{
          label: 'Run Corridor ML Predictor',
          onClick: () => setIsMlModalOpen(true),
        }}
      >
        <button
          type="button"
          className="btn-action outline"
          onClick={fetchData}
          disabled={loading}
          title="Refresh shipment and risk data"
        >
          {loading ? 'Refreshing...' : '↻ Refresh Data'}
        </button>
      </PageHeader>

      {/* Transparency & Governance Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.7) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          borderRadius: '8px',
          padding: '12px 18px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.25rem' }}>🛡️</span>
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#E2E8F0' }}>
              Dual Risk Engine: Operational Heuristics vs. ML Benchmark Model
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94A3B8' }}>
              • <strong>Operational Rules (0–100):</strong> Grounded in live PostgreSQL records (driver/vehicle/route allocation and capacity).
              <br />
              • <strong>Machine Learning (Random Forest):</strong> Evaluates freight corridor delay probability from synthetic benchmark training data.
            </div>
          </div>
        </div>
        <button
          type="button"
          className="btn-action outline"
          style={{ fontSize: '0.72rem', padding: '4px 10px', borderColor: '#38BDF8', color: '#38BDF8' }}
          onClick={() => setIsMlModalOpen(true)}
        >
          ✦ Test ML Predictor
        </button>
      </div>

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Failed to load shipments</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchData}>
            Retry
          </button>
        </div>
      )}

      {/* Filter Tabs & Search Controls */}
      <div className="filter-controls-bar" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div className="filter-tabs" style={{ flexWrap: 'wrap' }}>
          <button
            type="button"
            className={`filter-tab ${attentionFilter === 'ATTENTION_ONLY' ? 'active' : ''}`}
            onClick={() => setAttentionFilter('ATTENTION_ONLY')}
          >
            Needs Attention ({attentionCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${attentionFilter === 'MISSING_DRIVER' ? 'active' : ''}`}
            onClick={() => setAttentionFilter('MISSING_DRIVER')}
          >
            Missing Driver ({missingDriversCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${attentionFilter === 'MISSING_VEHICLE' ? 'active' : ''}`}
            onClick={() => setAttentionFilter('MISSING_VEHICLE')}
          >
            Missing Vehicle ({missingVehiclesCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${attentionFilter === 'MISSING_ROUTE' ? 'active' : ''}`}
            onClick={() => setAttentionFilter('MISSING_ROUTE')}
          >
            Missing Route ({missingRoutesCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${attentionFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setAttentionFilter('ALL')}
          >
            All Active ({totalMonitored})
          </button>
        </div>

        <div style={{ minWidth: '240px' }}>
          <input
            type="text"
            className="form-input"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            placeholder="Filter by waybill, destination, hub..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Main Attention Table */}
      <DataTable
        columns={columns}
        data={filteredShipments}
        loading={loading}
        pageSize={10}
        keyField="id"
        emptyState={
          <EmptyState
            icon="✅"
            title="No attention-flagged shipments found"
            description={
              attentionFilter === 'ATTENTION_ONLY'
                ? 'All monitored shipments currently have complete driver, vehicle, and corridor allocations.'
                : 'No shipments match the selected triage criteria.'
            }
            action={{
              label: 'View All Active Shipments',
              onClick: () => setAttentionFilter('ALL'),
            }}
          />
        }
      />

      {/* Detail Drawer for Real Allocation & Status Transitions */}
      {selectedShipment && (
        <ShipmentDetailDrawer
          isOpen={isDrawerOpen}
          onClose={() => {
            setIsDrawerOpen(false);
            setSelectedShipment(null);
          }}
          shipment={selectedShipment}
          onUpdated={handleShipmentUpdated}
        />
      )}

      {/* ML Delay Prediction Modal */}
      <DelayPredictionModal
        isOpen={isMlModalOpen}
        onClose={() => setIsMlModalOpen(false)}
      />
    </div>
  );
}
