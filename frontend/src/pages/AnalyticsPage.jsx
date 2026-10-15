import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { analyticsApi } from '../api/analytics.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import EmptyState from '../components/EmptyState';
import { exportShipmentsToCSV } from '../services/exportService.js';
import { useToast } from '../context/ToastContext';
import DelayPredictionModal from '../components/DelayPredictionModal';

export default function AnalyticsPage({ onNavigate = null }) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Analytics states
  const [overview, setOverview] = useState(null);
  const [delayRisk, setDelayRisk] = useState(null);
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [driverStats, setDriverStats] = useState(null);
  const [vehicleStats, setVehicleStats] = useState(null);
  const [isPredictorOpen, setIsPredictorOpen] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, drRes, drvRes, vehRes] = await Promise.allSettled([
        analyticsApi.getOverview(),
        analyticsApi.getDelayRisk({ limit: 100 }),
        analyticsApi.getDriverAnalytics(),
        analyticsApi.getVehicleAnalytics(),
      ]);

      if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
      if (drRes.status === 'fulfilled') setDelayRisk(drRes.value);
      if (drvRes.status === 'fulfilled') setDriverStats(drvRes.value);
      if (vehRes.status === 'fulfilled') setVehicleStats(vehRes.value);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const summary = delayRisk?.summary || null;
  const shipments = useMemo(
    () => (Array.isArray(delayRisk?.shipments) ? delayRisk.shipments : []),
    [delayRisk]
  );

  const filteredShipments = useMemo(() => {
    if (riskFilter === 'ALL') return shipments;
    return shipments.filter((s) => s.risk_category === riskFilter);
  }, [shipments, riskFilter]);

  const columns = useMemo(() => [
    {
      key: 'tracking_number',
      header: 'Tracking Number',
      sortable: true,
      render: (s) => (
        <div>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38BDF8', fontSize: '0.9rem' }}>
            {s.tracking_number}
          </span>
          <div style={{ fontSize: '0.72rem', color: '#64748B' }}>
            ID #{s.shipment_id} • {s.status}
          </div>
        </div>
      ),
    },
    {
      key: 'origin_destination',
      header: 'Freight Corridor',
      render: (s) => (
        <div>
          <div className="table-primary-text" style={{ fontSize: '0.82rem' }}>
            {s.origin_warehouse_name || 'Origin Hub'} → {s.destination_city}, {s.destination_state}
          </div>
          <span className="table-secondary-text" style={{ fontSize: '0.72rem' }}>
            {s.is_interstate ? 'Interstate Freight Leg' : 'Intrastate Metro Transit'}
          </span>
        </div>
      ),
    },
    {
      key: 'risk_score',
      header: 'Delay Risk Score',
      sortable: true,
      render: (s) => {
        const score = s.risk_score;
        const color = score >= 70 ? '#EF4444' : score >= 40 ? '#F59E0B' : '#10B981';
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, color, fontSize: '0.95rem' }}>
              {score} / 100
            </span>
            <span
              className={`status-badge badge-${s.risk_category?.toLowerCase() || 'default'}`}
              style={{ fontSize: '0.68rem', padding: '2px 6px' }}
            >
              {s.risk_category}
            </span>
          </div>
        );
      },
    },
    {
      key: 'dispatch_readiness',
      header: 'Asset Allocations (DB Grounded)',
      render: (s) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', fontSize: '0.74rem' }}>
          <span style={{ color: s.has_driver_assigned ? '#10B981' : '#F59E0B' }}>
            {s.has_driver_assigned ? '✓ Driver Allocated' : '⚠️ Missing Driver (+20 pts)'}
          </span>
          <span style={{ color: s.has_vehicle_assigned ? '#10B981' : '#F59E0B' }}>
            {s.has_vehicle_assigned ? '✓ Equipment Allocated' : '⚠️ Missing Vehicle (+15 pts)'}
          </span>
          <span style={{ color: s.has_route_assigned ? '#10B981' : '#F59E0B' }}>
            {s.has_route_assigned ? '✓ Route Assigned' : '⚠️ Missing Route (+10 pts)'}
          </span>
        </div>
      ),
    },
    {
      key: 'summary_explanation',
      header: 'Primary Operational Delay Drivers',
      render: (s) => (
        <span className="table-secondary-text" style={{ maxWidth: '280px', display: 'inline-block', fontSize: '0.74rem', lineHeight: '1.3' }}>
          {s.summary_explanation || 'All dispatch factors verified on schedule.'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (s) => (
        <button
          type="button"
          className="btn-action outline"
          style={{ padding: '3px 8px', fontSize: '0.72rem' }}
          onClick={(e) => {
            e.stopPropagation();
            if (onNavigate) onNavigate('rescue');
          }}
          title="Open shipment in Rescue Center"
        >
          Triage in Rescue →
        </button>
      ),
    },
  ], [onNavigate]);

  const handleExportRiskReport = () => {
    try {
      const targetList = filteredShipments.map((s) => ({
        id: s.shipment_id,
        tracking_number: s.tracking_number,
        status: s.status,
        origin_warehouse: { name: s.origin_warehouse_name, location: s.origin_warehouse_location },
        destination_city: s.destination_city,
        destination_state: s.destination_state,
        total_weight_kg: s.cargo_weight_kg,
        total_volume_cbm: null,
      }));
      const count = exportShipmentsToCSV(targetList);
      toast.success(`Exported ${count} delay-risk records to CSV`);
    } catch (err) {
      toast.error(err.message || 'Failed to export CSV report');
    }
  };

  return (
    <div className="management-page" id="analytics-control-tower-page">
      <PageHeader
        section="OPERATIONS CONTROL / ANALYTICS"
        title="Fleet Analytics & Delay Risk Control Tower"
        caption="Deterministic operational delay risk evaluations (0–100), staging bottleneck identification, and fleet telematics."
        metaPills={[
          { label: 'Total Shipments', value: overview?.total_shipments ?? '—' },
          { label: 'Avg Risk Score', value: summary ? `${Math.round(summary.average_risk_score)} / 100` : '—', status: summary?.average_risk_score > 40 ? 'warning' : 'online' },
          { label: 'Critical Risk', value: summary?.critical_risk_count ?? 0, status: summary?.critical_risk_count > 0 ? 'warning' : 'online' },
          { label: 'Active Drivers', value: driverStats?.active_drivers_count ?? overview?.total_drivers ?? '—' },
        ]}
        primaryAction={{
          label: 'Export Risk CSV',
          onClick: handleExportRiskReport,
        }}
      >
        <button
          type="button"
          id="btn-open-ml-delay-predictor"
          className="btn-action primary"
          onClick={() => setIsPredictorOpen(true)}
          title="Open AI/ML India Delay Risk Simulation"
          style={{
            background: 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
            borderColor: '#38BDF8',
            color: '#FFFFFF',
            fontWeight: 600,
          }}
        >
          <span style={{ marginRight: '6px' }}>✦</span>
          <span>Predict Corridor Delay (ML)</span>
        </button>
      </PageHeader>

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to synchronize analytics</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchData}>
            Retry
          </button>
        </div>
      )}

      {/* Control Tower Workflow Navigator Cards (DETECT -> RECOMMEND -> SIMULATE RECOVERY) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginBottom: '20px',
        }}
      >
        {/* Card 1: DETECT */}
        <div
          style={{
            backgroundColor: '#1E293B',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#FCD34D', letterSpacing: '0.05em' }}>
                STAGE 1 • DETECT & TRIAGE
              </span>
              <span style={{ fontSize: '1.1rem' }}>🛡️</span>
            </div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 6px 0' }}>
              Shipment Rescue Center
            </h4>
            <p style={{ fontSize: '0.74rem', color: '#94A3B8', margin: 0, lineHeight: '1.4' }}>
              Detect unassigned drivers, missing equipment, and capacity strain across live shipments.
            </p>
          </div>
          <button
            type="button"
            className="btn-action primary"
            style={{ marginTop: '12px', fontSize: '0.72rem', padding: '5px 10px' }}
            onClick={() => onNavigate && onNavigate('rescue')}
          >
            Open Rescue Center →
          </button>
        </div>

        {/* Card 2: SIMULATE RECOVERY */}
        <div
          style={{
            backgroundColor: '#1E293B',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#38BDF8', letterSpacing: '0.05em' }}>
                STAGE 2 • SIMULATE RECOVERY
              </span>
              <span style={{ fontSize: '1.1rem' }}>⚡</span>
            </div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 6px 0' }}>
              What-If Disruption Simulator
            </h4>
            <p style={{ fontSize: '0.74rem', color: '#94A3B8', margin: 0, lineHeight: '1.4' }}>
              Test facility outages, blizzard reroutes, and highway hot-swaps in a zero-mutation sandbox.
            </p>
          </div>
          <button
            type="button"
            className="btn-action outline"
            style={{ marginTop: '12px', fontSize: '0.72rem', padding: '5px 10px', borderColor: '#38BDF8', color: '#38BDF8' }}
            onClick={() => onNavigate && onNavigate('simulator')}
          >
            Launch Disruption Simulator →
          </button>
        </div>

        {/* Card 3: ML PROTOTYPE */}
        <div
          style={{
            backgroundColor: '#1E293B',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#C084FC', letterSpacing: '0.05em' }}>
                MACHINE LEARNING PROTOTYPE
              </span>
              <span style={{ fontSize: '1.1rem' }}>✦</span>
            </div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#F8FAFC', margin: '0 0 6px 0' }}>
              India Corridor Delay ML Model
            </h4>
            <p style={{ fontSize: '0.74rem', color: '#94A3B8', margin: 0, lineHeight: '1.4' }}>
              Random Forest pipeline inference trained on 1,451 benchmark corridor records (ROC-AUC: 0.5062).
            </p>
          </div>
          <button
            type="button"
            className="btn-action outline"
            style={{ marginTop: '12px', fontSize: '0.72rem', padding: '5px 10px', borderColor: '#C084FC', color: '#C084FC' }}
            onClick={() => setIsPredictorOpen(true)}
          >
            Test Corridor Model →
          </button>
        </div>
      </div>

      {/* Heuristic Methodology Transparency Banner */}
      <div className="ai-route-optimization-box" style={{ marginBottom: '20px' }}>
        <div className="ai-opt-left">
          <span className="ai-sparkle-icon">✦</span>
          <span className="ai-opt-badge">METHODOLOGY INTEGRITY</span>
          <span>
            Scoring Engine: <strong>Deterministic Operational Heuristic (0–100)</strong>. Grounded in actual database fields (missing driver +20, missing vehicle +15, missing route +10, overload +20, interstate +15).
          </span>
        </div>
        <button
          type="button"
          className="btn-action outline"
          style={{ padding: '3px 10px', fontSize: '0.72rem', borderColor: 'var(--ai-cyan)', color: 'var(--ai-cyan)' }}
          onClick={fetchData}
        >
          Refresh Telematics
        </button>
      </div>

      {/* Interactive Risk Tier Distribution Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div
          onClick={() => setRiskFilter('CRITICAL')}
          style={{
            cursor: 'pointer',
            backgroundColor: riskFilter === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : '#1E293B',
            border: `1px solid ${riskFilter === 'CRITICAL' ? '#EF4444' : '#334155'}`,
            borderRadius: '6px',
            padding: '12px',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>CRITICAL RISK (80–100)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#EF4444' }}>
            {summary?.critical_risk_count ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748B' }}>Severe bottlenecks</div>
        </div>

        <div
          onClick={() => setRiskFilter('HIGH')}
          style={{
            cursor: 'pointer',
            backgroundColor: riskFilter === 'HIGH' ? 'rgba(245, 158, 11, 0.2)' : '#1E293B',
            border: `1px solid ${riskFilter === 'HIGH' ? '#F59E0B' : '#334155'}`,
            borderRadius: '6px',
            padding: '12px',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>HIGH RISK (60–79)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#F59E0B' }}>
            {summary?.high_risk_count ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748B' }}>Resource unassigned</div>
        </div>

        <div
          onClick={() => setRiskFilter('MEDIUM')}
          style={{
            cursor: 'pointer',
            backgroundColor: riskFilter === 'MEDIUM' ? 'rgba(56, 189, 248, 0.2)' : '#1E293B',
            border: `1px solid ${riskFilter === 'MEDIUM' ? '#38BDF8' : '#334155'}`,
            borderRadius: '6px',
            padding: '12px',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>MEDIUM RISK (30–59)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#38BDF8' }}>
            {summary?.medium_risk_count ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748B' }}>Minor corridor strain</div>
        </div>

        <div
          onClick={() => setRiskFilter('LOW')}
          style={{
            cursor: 'pointer',
            backgroundColor: riskFilter === 'LOW' ? 'rgba(16, 185, 129, 0.2)' : '#1E293B',
            border: `1px solid ${riskFilter === 'LOW' ? '#10B981' : '#334155'}`,
            borderRadius: '6px',
            padding: '12px',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>LOW RISK (0–29)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10B981' }}>
            {summary?.low_risk_count ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#64748B' }}>Allocations nominal</div>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="filter-controls-bar">
        <div className="filter-tabs" style={{ flexWrap: 'wrap' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'COMPLETED'].map((tier) => (
            <button
              key={tier}
              type="button"
              className={`filter-tab ${riskFilter === tier ? 'active' : ''}`}
              onClick={() => setRiskFilter(tier)}
            >
              {tier === 'ALL' ? `All (${shipments.length})` : tier}
            </button>
          ))}
        </div>
      </div>

      {/* Delay Risk Data Table */}
      <DataTable
        columns={columns}
        data={filteredShipments}
        loading={loading}
        pageSize={10}
        keyField="shipment_id"
        emptyState={
          <EmptyState
            icon="📊"
            title="No shipments in selected risk tier"
            description="All active shipments are currently outside this risk threshold."
            action={{
              label: 'Reset Filter',
              onClick: () => setRiskFilter('ALL'),
            }}
          />
        }
      />

      <DelayPredictionModal
        isOpen={isPredictorOpen}
        onClose={() => setIsPredictorOpen(false)}
      />
    </div>
  );
}
