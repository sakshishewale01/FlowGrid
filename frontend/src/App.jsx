import { useState } from 'react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(false);
  const [selectedLifecycleIndex, setSelectedLifecycleIndex] = useState(0);

  // Core modules defined in docs/requirements.md
  const coreModules = [
    {
      id: 'auth-rbac',
      title: 'Authentication & RBAC',
      desc: 'Role-based access control (Admin, Manager, Driver, Viewer) with secure JWT tokens.',
      icon: '🔐',
      accent: 'rgba(99, 102, 241, 0.15)',
    },
    {
      id: 'warehouse-mgmt',
      title: 'Warehouse Management',
      desc: 'Multi-facility tracking, zone configurations, geo-coordinates, and intake capacity.',
      icon: '🏢',
      accent: 'rgba(6, 182, 212, 0.15)',
    },
    {
      id: 'product-inventory',
      title: 'Product & Inventory',
      desc: 'SKU cataloging, on-hand vs. reserved stock locking, and automated transaction logs.',
      icon: '📦',
      accent: 'rgba(16, 185, 129, 0.15)',
    },
    {
      id: 'driver-vehicle',
      title: 'Driver & Vehicle Registry',
      desc: 'Driver profiles, licensing checks, vehicle status tracking, and weight/volume constraints.',
      icon: '🚚',
      accent: 'rgba(245, 158, 11, 0.15)',
    },
    {
      id: 'shipment-mgmt',
      title: 'Shipment Management',
      desc: 'Manifest compilation, multi-item line reservations, and origin-to-destination booking.',
      icon: '📑',
      accent: 'rgba(244, 63, 94, 0.15)',
    },
    {
      id: 'shipment-tracking',
      title: 'Shipment Tracking',
      desc: 'Immutable checkpoint logs, time-series events, and customer tracking queries.',
      icon: '📍',
      accent: 'rgba(168, 85, 247, 0.15)',
    },
    {
      id: 'route-mgmt',
      title: 'Route Management',
      desc: 'Multi-stop delivery corridors, intermediate waypoints, and distance calculations.',
      icon: '🗺️',
      accent: 'rgba(59, 130, 246, 0.15)',
    },
    {
      id: 'analytics',
      title: 'Analytics & KPIs',
      desc: 'On-time delivery rates, fleet utilization, facility throughput, and status distribution.',
      icon: '📊',
      accent: 'rgba(20, 184, 166, 0.15)',
    },
  ];

  // Shipment lifecycle states defined in docs/requirements.md
  const lifecycleStates = [
    {
      name: 'CREATED',
      actor: 'Admin / Manager',
      desc: 'Shipment draft initialized with destination and cargo line items.',
      effect: 'No inventory reserved yet; editable draft.',
    },
    {
      name: 'CONFIRMED',
      actor: 'Admin / Manager',
      desc: 'Shipment verified against stock availability.',
      effect: 'Inventory balances moved from Available to Reserved.',
    },
    {
      name: 'ASSIGNED',
      actor: 'Admin / Manager',
      desc: 'Available driver and vehicle allocated to the manifest.',
      effect: 'Driver notified; equipment locked from concurrent assignments.',
    },
    {
      name: 'PICKED_UP',
      actor: 'Driver / Admin',
      desc: 'Driver accepts physical custody and scans freight at origin.',
      effect: 'Stock deducted from warehouse on-hand; vehicle set to IN_USE.',
    },
    {
      name: 'IN_TRANSIT',
      actor: 'Driver',
      desc: 'Consignment moving along planned route corridors.',
      effect: 'Periodic GPS checkpoints recorded in audit log.',
    },
    {
      name: 'OUT_FOR_DELIVERY',
      actor: 'Driver',
      desc: 'Arrived in destination zone; on final-mile delivery run.',
      effect: 'Consignee ETA notification triggered.',
    },
    {
      name: 'DELIVERED',
      actor: 'Driver / Admin',
      desc: 'Handover complete with recipient confirmation.',
      effect: 'Terminal success state; billing & completion metrics logged.',
    },
  ];

  // User Roles defined in requirements.md
  const userRoles = [
    {
      role: 'Admin',
      badgeClass: 'admin',
      scope: 'Global System Authority',
      desc: 'Full administrative control, user provisioning, system parameters, and cross-module CRUD.',
    },
    {
      role: 'Manager',
      badgeClass: 'manager',
      scope: 'Logistics Operations',
      desc: 'Dispatches shipments, manages inventory, oversees warehouses, and monitors operational KPIs.',
    },
    {
      role: 'Driver',
      badgeClass: 'driver',
      scope: 'Field Execution',
      desc: 'Inspects assigned deliveries, advances checkpoint milestones, and reports delivery exceptions.',
    },
    {
      role: 'Viewer',
      badgeClass: 'viewer',
      scope: 'Read-Only Auditing',
      desc: 'Monitors shipment milestones, queries tracking numbers, and views operational dashboards.',
    },
  ];

  // Live test for backend health check
  const checkBackendHealth = async () => {
    setIsLoadingHealth(true);
    setHealthStatus(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/health');
      if (res.ok) {
        const data = await res.json();
        setHealthStatus({ ok: true, data });
      } else {
        setHealthStatus({ ok: false, message: `HTTP error ${res.status}` });
      }
    } catch (err) {
      setHealthStatus({
        ok: false,
        message: 'Backend server not responding at http://127.0.0.1:8000. Run "uvicorn app.main:app --reload" in backend/.',
      });
    } finally {
      setIsLoadingHealth(false);
    }
  };

  const currentState = lifecycleStates[selectedLifecycleIndex];

  return (
    <div id="flowgrid-app">
      {/* Navigation */}
      <header className="navbar">
        <div className="container nav-content">
          <a href="#" className="brand-wrapper" id="brand-logo-link">
            <div className="brand-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z" />
              </svg>
            </div>
            <div>
              <span className="brand-title">FlowGrid</span>
              <span className="brand-version" style={{ marginLeft: '8px' }}>v0.1.0 (Phase 1)</span>
            </div>
          </a>

          <div className="nav-links">
            <span className="status-pill" id="system-status-indicator">
              <span className="status-dot"></span>
              Foundation Ready
            </span>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="nav-link-btn"
              id="swagger-link"
            >
              API Docs ↗
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero container">
        <div className="hero-badge">
          <span>⚡</span> Phase 1: Clean Foundation &amp; Architecture
        </div>
        <h1 className="hero-title">
          Intelligent Logistics &amp; <br />
          <span className="hero-title-highlight">Supply Chain Coordination</span>
        </h1>
        <p className="hero-subtitle">
          Engineered with Python FastAPI, PostgreSQL, SQLAlchemy, and React.
          Built for scalable multi-warehouse dispatch, driver tracking, and end-to-end custody control.
        </p>

        {/* Live Backend Connection Tester */}
        <div className="glass-panel health-box" id="backend-health-card">
          <div className="health-box-inner">
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#fff' }}>
                Backend Connectivity
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Target: <code>http://127.0.0.1:8000/health</code>
              </div>
            </div>
            <button
              id="btn-test-health"
              className="btn-primary"
              onClick={checkBackendHealth}
              disabled={isLoadingHealth}
            >
              {isLoadingHealth ? 'Checking...' : 'Ping /health'}
            </button>
          </div>

          {healthStatus && (
            <div style={{ marginTop: '16px', textAlign: 'left' }}>
              {healthStatus.ok ? (
                <div className="health-result" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399' }}>
                  ✓ Connected: {JSON.stringify(healthStatus.data)}
                </div>
              ) : (
                <div className="health-result" style={{ borderColor: 'rgba(244, 63, 94, 0.4)', color: '#fb7185' }}>
                  ✕ {healthStatus.message}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Core Modules Grid */}
      <section className="section container" id="modules-section">
        <div className="section-header">
          <h2 className="section-title">Platform Architecture Modules</h2>
          <p className="section-subtitle">
            8 core functional domains documented in <code>docs/requirements.md</code>
          </p>
        </div>

        <div className="modules-grid">
          {coreModules.map((module) => (
            <div key={module.id} className="glass-panel module-card" id={`card-${module.id}`}>
              <div className="module-icon-wrap" style={{ background: module.accent }}>
                {module.icon}
              </div>
              <h3>{module.title}</h3>
              <p>{module.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Shipment Lifecycle Pipeline */}
      <section className="section container" id="lifecycle-section">
        <div className="section-header">
          <h2 className="section-title">Shipment Lifecycle State Machine</h2>
          <p className="section-subtitle">
            Interactive state progression with enforced state transition rules. Click any stage to inspect.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div className="lifecycle-stepper" id="lifecycle-stepper">
            {lifecycleStates.map((state, index) => {
              const isActive = index === selectedLifecycleIndex;
              return (
                <div key={state.name} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <div
                    className={`step-node ${isActive ? 'active' : ''}`}
                    onClick={() => setSelectedLifecycleIndex(index)}
                    id={`step-${state.name.toLowerCase()}`}
                  >
                    <div className="step-number">Stage 0{index + 1}</div>
                    <div className="step-name">{state.name}</div>
                  </div>
                  {index < lifecycleStates.length - 1 && <span className="step-arrow">→</span>}
                </div>
              );
            })}
          </div>

          <div className="step-details-box glass-panel" id="lifecycle-details-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#fff' }}>
                Stage {selectedLifecycleIndex + 1}: {currentState.name}
              </span>
              <span className="role-badge manager" style={{ fontSize: '0.75rem' }}>
                Actor: {currentState.actor}
              </span>
            </div>
            <p style={{ color: 'var(--text-main)', marginBottom: '8px' }}>{currentState.desc}</p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <strong>Business Rules &amp; Effects:</strong> {currentState.effect}
            </p>
          </div>

          {/* Exception States */}
          <div style={{ marginTop: '20px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-dim)' }}>
              Exception States:
            </span>
            <span className="role-badge admin">CANCELLED (Pre-transit abort)</span>
            <span className="role-badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
              FAILED (Delivery exception)
            </span>
            <span className="role-badge viewer">RETURNED (Restocked to origin)</span>
          </div>
        </div>
      </section>

      {/* User Roles & Permissions */}
      <section className="section container" id="roles-section">
        <div className="section-header">
          <h2 className="section-title">Role-Based Access Control (RBAC)</h2>
          <p className="section-subtitle">
            Defined access boundaries across system actors
          </p>
        </div>

        <div className="roles-grid">
          {userRoles.map((role) => (
            <div key={role.role} className="glass-panel role-card" id={`role-card-${role.role.toLowerCase()}`}>
              <div className="role-header">
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#fff' }}>{role.role}</span>
                <span className={`role-badge ${role.badgeClass}`}>{role.scope}</span>
              </div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{role.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="footer container">
        <div>
          FlowGrid Platform &copy; 2026. Phase 1 Foundation established. Refer to <code>docs/setup.md</code> and <code>docs/requirements.md</code>.
        </div>
      </footer>
    </div>
  );
}
