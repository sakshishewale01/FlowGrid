import React from 'react';

export default function AiInsightPanel({
  delayRiskSummary = null,
  delayRiskShipments = [],
  onRunAudit = null,
  onNavigate = null,
  loading = false,
}) {
  const avgScore = delayRiskSummary
    ? Math.round(delayRiskSummary.average_risk_score)
    : 0;

  const criticalAndHigh = delayRiskSummary
    ? (delayRiskSummary.critical_risk_count || 0) + (delayRiskSummary.high_risk_count || 0)
    : 0;

  const totalEvaluated = delayRiskSummary?.total_evaluated || 0;

  // Derive unassigned counts across evaluated shipments
  const unassignedDrivers = delayRiskShipments.filter((s) => !s.has_driver_assigned).length;
  const unassignedVehicles = delayRiskShipments.filter((s) => !s.has_vehicle_assigned).length;
  const unassignedRoutes = delayRiskShipments.filter((s) => !s.has_route_assigned).length;
  const totalStagingGaps = unassignedDrivers + unassignedVehicles + unassignedRoutes;

  const handleCardClick = (target) => {
    if (!onNavigate) return;
    if (target === 'shipments-critical') {
      onNavigate('shipments');
    } else if (target === 'drivers') {
      onNavigate('drivers');
    } else if (target === 'routes') {
      onNavigate('routes');
    } else {
      onNavigate('shipments');
    }
  };

  return (
    <div className="ai-insight-panel" id="ai-insight-panel">
      <div className="panel-title-bar">
        <div className="ai-title-wrapper">
          <div className="ai-icon-pulse">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#22D3EE"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </div>
          <div>
            <div className="ai-badge-row">
              <span className="ai-category-badge">INTELLIGENT CONTROL TOWER</span>
              <span className="ai-status-pill">Deterministic Heuristic (0–100)</span>
            </div>
            <h3 className="panel-title">Operational Delay Risk &amp; Dispatch Readiness</h3>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className="btn-ai-action"
            id="btn-trigger-ai-forecast"
            onClick={onRunAudit}
            title="Recalculate deterministic risk scoring across active freight manifests"
          >
            <span className="ai-sparkle">✦</span>
            <span>Audit Fleet Risk Telematics</span>
          </button>
        </div>
      </div>

      <div style={{ padding: '0 16px 8px', fontSize: '0.78rem', color: '#94A3B8' }}>
        Rule-based, explainable risk calculations based on asset allocation, vehicle payload strain, and corridor geometry. Explicitly distinct from calibrated ML probability distributions.
      </div>

      <div className="ai-cards-grid">
        {/* Card 1: Fleet Delay Risk Index */}
        <div
          className="ai-card"
          id="ai-card-risk-index"
          onClick={() => handleCardClick('shipments')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('shipments')}
          style={{ cursor: 'pointer' }}
          title="Click to view all active shipment manifests"
        >
          <div className="ai-card-header">
            <span className="ai-card-category">FLEET RISK INDEX</span>
            <span className="ai-card-metric" style={{ color: avgScore > 50 ? '#EF4444' : avgScore > 25 ? '#F59E0B' : '#10B981' }}>
              {loading ? '...' : `${avgScore} / 100`}
            </span>
          </div>
          <h4 className="ai-card-title">Average Operational Delay Risk</h4>
          <p className="ai-card-desc">
            {totalEvaluated > 0
              ? `Calculated across ${totalEvaluated} registered shipments using origin congestion, payload ratio, and transit status.`
              : 'Zero active shipments currently at delay risk.'}
          </p>
          <div className="ai-card-footer">
            <span
              className="ai-footer-dot"
              style={{ backgroundColor: avgScore > 50 ? '#EF4444' : avgScore > 25 ? '#F59E0B' : '#10B981' }}
            />
            <span className="ai-footer-status">
              {totalEvaluated > 0 ? `${totalEvaluated} Shipments Evaluated` : 'No shipments registered'}
            </span>
          </div>
        </div>

        {/* Card 2: High / Critical Delay Exceptions */}
        <div
          className="ai-card"
          id="ai-card-exceptions"
          onClick={() => handleCardClick('shipments-critical')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('shipments-critical')}
          style={{ cursor: 'pointer' }}
          title="Click to filter shipments needing dispatch attention"
        >
          <div className="ai-card-header">
            <span className="ai-card-category">HIGH-RISK FREIGHT</span>
            <span className="ai-card-metric" style={{ color: criticalAndHigh > 0 ? '#F87171' : '#38BDF8' }}>
              {loading ? '...' : `${criticalAndHigh} Flagged`}
            </span>
          </div>
          <h4 className="ai-card-title">Staging &amp; Exception Hotspots</h4>
          <p className="ai-card-desc">
            {criticalAndHigh > 0
              ? `${criticalAndHigh} line-haul leg(s) require intervention before departure to avoid SLA transit breaches.`
              : 'All active line-haul shipments are operating within target scheduling thresholds.'}
          </p>
          <div className="ai-card-footer">
            <span
              className="ai-footer-dot"
              style={{ backgroundColor: criticalAndHigh > 0 ? '#EF4444' : '#10B981' }}
            />
            <span className="ai-footer-status">
              {criticalAndHigh > 0 ? 'Requires Dispatch Action' : 'Schedule On Target'}
            </span>
          </div>
        </div>

        {/* Card 3: Dispatch Readiness Bottlenecks */}
        <div
          className="ai-card"
          id="ai-card-dispatch-readiness"
          onClick={() => handleCardClick('drivers')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('drivers')}
          style={{ cursor: 'pointer' }}
          title="Click to manage fleet drivers and allocations"
        >
          <div className="ai-card-header">
            <span className="ai-card-category">DISPATCH READINESS</span>
            <span className="ai-card-metric" style={{ color: totalStagingGaps > 0 ? '#FBBF24' : '#34D399' }}>
              {loading ? '...' : `${totalStagingGaps} Gaps`}
            </span>
          </div>
          <h4 className="ai-card-title">Unassigned Resource Coverage</h4>
          <p className="ai-card-desc">
            Missing: {unassignedDrivers} driver(s) (+20 pts), {unassignedVehicles} vehicle(s) (+15 pts), and {unassignedRoutes} corridor(s) (+10 pts).
          </p>
          <div className="ai-card-footer">
            <span
              className="ai-footer-dot"
              style={{ backgroundColor: totalStagingGaps > 0 ? '#F59E0B' : '#10B981' }}
            />
            <span className="ai-footer-status">
              {totalStagingGaps > 0 ? 'Pre-Dispatch Allocation Required' : 'All Resources Allocated'}
            </span>
          </div>
        </div>

        {/* Card 4: Heuristic Factor Transparency */}
        <div
          className="ai-card"
          id="ai-card-transparency"
          onClick={() => handleCardClick('routes')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCardClick('routes')}
          style={{ cursor: 'pointer' }}
          title="Click to inspect transit corridor routes"
        >
          <div className="ai-card-header">
            <span className="ai-card-category">EXPLAINABLE CRITERIA</span>
            <span className="ai-card-metric" style={{ color: '#22D3EE' }}>
              Deterministic
            </span>
          </div>
          <h4 className="ai-card-title">Transparent Heuristic Penalty Model</h4>
          <p className="ai-card-desc">
            Evaluates unassigned drivers (+20), unassigned vehicles (+15), corridor absence (+10), payload strain &gt;90% (+20), and terminal status.
          </p>
          <div className="ai-card-footer">
            <span className="ai-footer-dot" style={{ backgroundColor: '#22D3EE' }} />
            <span className="ai-footer-status">Audit-Compliant • Zero Hallucination</span>
          </div>
        </div>
      </div>
    </div>
  );
}
