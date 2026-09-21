import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { routesApi } from '../api/routes.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import RouteModal from '../components/RouteModal';

export default function RoutesPage() {
  const { user } = useAuth();
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'ACTIVE' | 'PLANNED' | 'COMPLETED' | 'INACTIVE'

  // Modal control
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchRoutes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await routesApi.listRoutes({ limit: 100 });
      setRoutes(data || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoutes();
  }, [fetchRoutes]);

  const filteredRoutes = useMemo(() => {
    return routes.filter((r) => {
      if (statusFilter !== 'ALL' && r.status !== statusFilter) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const name = r.name?.toLowerCase() || '';
      const orig = r.origin?.toLowerCase() || '';
      const dest = r.destination?.toLowerCase() || '';
      return name.includes(q) || orig.includes(q) || dest.includes(q);
    });
  }, [routes, statusFilter, searchQuery]);

  const activeCount = routes.filter((r) => r.status === 'ACTIVE').length;
  const totalDistance = routes.reduce((acc, r) => acc + (Number(r.estimated_distance) || 0), 0);

  const handleOpenCreate = () => {
    setSelectedRoute(null);
    setIsModalOpen(true);
  };

  const handleOpenDetail = (route) => {
    setSelectedRoute(route);
    setIsModalOpen(true);
  };

  return (
    <div className="management-page" id="routes-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / LOGISTICS"
        title="Transit Routes & Corridors"
        caption="Interstate freight corridors, estimated transit durations, route legs, and shipment corridor assignments."
        metaPills={[
          { label: 'Total Corridors', value: routes.length },
          { label: 'Active', value: activeCount, status: 'online' },
          { label: 'Tracked Distance', value: `${totalDistance.toLocaleString()} km` },
        ]}
        primaryAction={{
          label: 'Create Corridor',
          onClick: handleOpenCreate,
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load transit corridors</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchRoutes}>
            Retry
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="filter-controls-bar">
        <div className="search-input-wrapper">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="search"
            className="table-search-input"
            placeholder="Search routes by corridor name, origin hub, or destination..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-tabs">
          {['ALL', 'ACTIVE', 'PLANNED', 'COMPLETED', 'INACTIVE'].map((st) => (
            <button
              key={st}
              type="button"
              className={`filter-tab ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
            >
              {st === 'ALL' ? `All (${routes.length})` : st}
            </button>
          ))}
        </div>
      </div>

      {/* Routes Table */}
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Corridor ID</th>
              <th>Route Name</th>
              <th>Origin Terminal</th>
              <th>Destination Terminal</th>
              <th>Est. Distance</th>
              <th>Est. Duration</th>
              <th>Corridor Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4].map((n) => (
                <tr key={n} className="skeleton-row">
                  <td colSpan="8">
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filteredRoutes.length === 0 ? (
              <tr>
                <td colSpan="8" className="table-empty-cell">
                  <div className="empty-state-wrap">
                    <span className="empty-icon">🛣️</span>
                    <p className="empty-title">No transit routes found</p>
                    <p className="empty-desc">
                      {searchQuery
                        ? `No corridors matched query "${searchQuery}".`
                        : 'No routes found in the selected status filter.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredRoutes.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span className="id-tag">RT-{r.id}</span>
                  </td>
                  <td>
                    <div className="table-primary-text">{r.name}</div>
                  </td>
                  <td>
                    <span className="table-secondary-text">{r.origin}</span>
                  </td>
                  <td>
                    <span className="table-secondary-text">{r.destination}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
                        {r.estimated_distance ? Number(r.estimated_distance).toLocaleString() : '—'}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748B' }}>km</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
                        {r.estimated_duration ? `${r.estimated_duration}h` : '—'}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748B' }}>transit</span>
                    </div>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${
                        r.status === 'ACTIVE'
                          ? 'delivered'
                          : r.status === 'PLANNED'
                          ? 'in-transit'
                          : 'cancelled'
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
                      <button
                        type="button"
                        className="btn-action outline"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        onClick={() => handleOpenDetail(r)}
                      >
                        {isManagerOrAdmin ? 'Edit / Shipments' : 'View'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Route Modal */}
      <RouteModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        route={selectedRoute}
        onSaved={fetchRoutes}
      />
    </div>
  );
}
