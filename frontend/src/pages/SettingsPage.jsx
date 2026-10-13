import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import authApi from '../api/auth.js';
import PageHeader from '../components/PageHeader';
import RoleBadge from '../components/RoleBadge';

export default function SettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isPinging, setIsPinging] = useState(false);
  const [healthResult, setHealthResult] = useState(null);

  const handleTestHealth = async () => {
    setIsPinging(true);
    try {
      const data = await authApi.checkHealth();
      setHealthResult({ ok: true, data });
      toast.success('FastAPI Backend connection healthy!');
    } catch (err) {
      setHealthResult({ ok: false, error: err.message || 'Offline' });
      toast.error('Backend connection check failed');
    } finally {
      setIsPinging(false);
    }
  };

  const rolePrivileges = [
    { role: 'ADMIN', create: '✓ Full', update: '✓ Full', delete: '✓ Full', view: '✓ All', desc: 'Global system administration, facility deactivation, and pipeline management.' },
    { role: 'MANAGER', create: '✓ Operations', update: '✓ Shipments & Hubs', delete: '✗ Blocked', view: '✓ All', desc: 'Freight dispatching, stock adjustments, driver/vehicle allocations.' },
    { role: 'DRIVER', create: '✗ Blocked', update: '✓ Own Availability', delete: '✗ Blocked', view: '✓ Assigned Legs', desc: 'Field freight execution and personal duty status updates.' },
    { role: 'VIEWER', create: '✗ Blocked', update: '✗ Blocked', delete: '✗ Blocked', view: '✓ Read-Only', desc: 'Read-only visibility across dashboards, shipments, and tracking telematics.' },
  ];

  return (
    <div className="management-page" id="settings-page">
      <PageHeader
        section="SYSTEM CONFIGURATION / GOVERNANCE"
        title="Node Configuration & Access Governance"
        caption="Review authenticated credentials, role-based authorization boundaries, and live telematics connectivity."
        metaPills={[
          { label: 'Control Node', value: 'CHI-01' },
          { label: 'Current Role', value: user?.role || 'VIEWER' },
          { label: 'Session Status', value: 'Active JWT', status: 'online' },
        ]}
      />

      <div className="dashboard-split-grid" style={{ marginBottom: '24px' }}>
        {/* User Session Profile Card */}
        <div className="warehouses-panel">
          <div className="panel-title-bar">
            <div>
              <h3 className="panel-title">Active Operator Session</h3>
              <p className="panel-subtitle">Current authenticated identity and cryptographic token claims</p>
            </div>
            <RoleBadge role={user?.role} size="normal" />
          </div>

          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="dropdown-info-item">
              <span className="info-key">Full Name:</span>
              <span className="info-val">{user?.name || 'Authorized Operator'}</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">Email Address:</span>
              <span className="info-val" style={{ fontFamily: 'monospace' }}>{user?.email || 'operator@flowgrid.io'}</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">User Primary Key:</span>
              <span className="info-val">#{user?.id ?? '1'}</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">Authentication Scheme:</span>
              <span className="info-val">HMAC-SHA256 Signed Bearer JWT</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">Self-Registration Boundary:</span>
              <span className="info-val text-success">ADMIN Self-Assignment Restricted</span>
            </div>
          </div>
        </div>

        {/* Backend Node Connection Card */}
        <div className="warehouses-panel">
          <div className="panel-title-bar">
            <div>
              <h3 className="panel-title">FastAPI Telematics Server</h3>
              <p className="panel-subtitle">Central API Gateway and Database connection probe</p>
            </div>
            <button
              type="button"
              className="btn-action primary"
              onClick={handleTestHealth}
              disabled={isPinging}
            >
              {isPinging ? 'Probing...' : 'Probe /health'}
            </button>
          </div>

          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="dropdown-info-item">
              <span className="info-key">API Host:</span>
              <span className="info-val" style={{ fontFamily: 'monospace' }}>http://127.0.0.1:8000</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">Version Protocol:</span>
              <span className="info-val">v1 REST + WebSocket (RFC 6455)</span>
            </div>
            <div className="dropdown-info-item">
              <span className="info-key">Probe Status:</span>
              <span className={`info-val ${healthResult?.ok ? 'text-success' : healthResult ? 'text-danger' : ''}`}>
                {healthResult ? (healthResult.ok ? '✓ Healthy Online' : '✗ Unreachable') : 'Idle'}
              </span>
            </div>

            {healthResult?.data && (
              <pre
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '10px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  color: '#38BDF8',
                  overflowX: 'auto',
                }}
              >
                {JSON.stringify(healthResult.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>

      {/* Role-Based Access Control (RBAC) Authorization Matrix */}
      <div className="table-panel">
        <div className="panel-title-bar">
          <div>
            <h3 className="panel-title">Role-Based Access Control (RBAC) Matrix</h3>
            <p className="panel-subtitle">
              Strict permissions enforced directly in the FastAPI Python backend
            </p>
          </div>
        </div>

        <div className="table-responsive-wrapper">
          <table className="ops-table">
            <thead>
              <tr>
                <th>System Role</th>
                <th>Create Entities</th>
                <th>Update &amp; Advance</th>
                <th>Delete / Deactivate</th>
                <th>Read Telematics</th>
                <th>Operational Scope</th>
              </tr>
            </thead>
            <tbody>
              {rolePrivileges.map((p) => {
                const isCurrentRole = user?.role === p.role;
                return (
                  <tr key={p.role} style={isCurrentRole ? { background: 'rgba(59, 130, 246, 0.08)' } : undefined}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <RoleBadge role={p.role} size="small" />
                        {isCurrentRole && (
                          <span style={{ fontSize: '0.68rem', color: '#38BDF8', fontWeight: 600 }}>
                            (YOUR ROLE)
                          </span>
                        )}
                      </div>
                    </td>
                    <td>{p.create}</td>
                    <td>{p.update}</td>
                    <td>{p.delete}</td>
                    <td>{p.view}</td>
                    <td style={{ fontSize: '0.8rem', color: '#94A3B8' }}>{p.desc}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
