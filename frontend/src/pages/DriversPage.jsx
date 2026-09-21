import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { driversApi } from '../api/drivers.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import DriverModal from '../components/DriverModal';

export default function DriversPage() {
  const { user } = useAuth();
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';
  const canUpdateStatus = isManagerOrAdmin || user?.role === 'DRIVER';

  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'AVAILABLE' | 'ON_DUTY' | 'IN_TRANSIT' | 'OFF_DUTY'

  // Modal control
  const [modalState, setModalState] = useState({
    isOpen: false,
    driver: null,
    isStatusOnly: false,
  });

  const fetchDrivers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await driversApi.listDrivers({ limit: 150 });
      setDrivers(data || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDrivers();
  }, [fetchDrivers]);

  const filteredDrivers = useMemo(() => {
    return drivers.filter((driver) => {
      if (statusFilter !== 'ALL' && driver.availability_status !== statusFilter) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const lic = driver.license_number?.toLowerCase() || '';
      const phone = driver.phone_number?.toLowerCase() || '';
      const uId = String(driver.user_id);
      return lic.includes(q) || phone.includes(q) || uId.includes(q);
    });
  }, [drivers, statusFilter, searchQuery]);

  const availableCount = drivers.filter((d) => d.availability_status === 'AVAILABLE').length;
  const inTransitCount = drivers.filter((d) => d.availability_status === 'IN_TRANSIT').length;

  const handleOpenRegister = () => {
    setModalState({ isOpen: true, driver: null, isStatusOnly: false });
  };

  const handleOpenEdit = (driver) => {
    setModalState({ isOpen: true, driver, isStatusOnly: false });
  };

  const handleOpenStatus = (driver) => {
    setModalState({ isOpen: true, driver, isStatusOnly: true });
  };

  return (
    <div className="management-page" id="drivers-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / FLEET"
        title="Fleet Drivers"
        caption="Manage logistics personnel, commercial licenses, contact channels, and live dispatch availability."
        metaPills={[
          { label: 'Total Drivers', value: drivers.length },
          { label: 'Available', value: availableCount, status: 'online' },
          { label: 'In Transit', value: inTransitCount, status: 'in-transit' },
        ]}
        primaryAction={{
          label: 'Register Driver',
          onClick: handleOpenRegister,
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load drivers</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchDrivers}>
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
            placeholder="Search drivers by license, phone, or User ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-tabs">
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ALL')}
          >
            All ({drivers.length})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'AVAILABLE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('AVAILABLE')}
          >
            Available ({availableCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ON_DUTY' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ON_DUTY')}
          >
            On Duty ({drivers.filter((d) => d.availability_status === 'ON_DUTY').length})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'IN_TRANSIT' ? 'active' : ''}`}
            onClick={() => setStatusFilter('IN_TRANSIT')}
          >
            In Transit ({inTransitCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'OFF_DUTY' ? 'active' : ''}`}
            onClick={() => setStatusFilter('OFF_DUTY')}
          >
            Off Duty ({drivers.filter((d) => d.availability_status === 'OFF_DUTY').length})
          </button>
        </div>
      </div>

      {/* Drivers Table */}
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Driver ID</th>
              <th>License Number</th>
              <th>Contact Phone</th>
              <th>Linked Account</th>
              <th>Availability Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4].map((n) => (
                <tr key={n} className="skeleton-row">
                  <td colSpan="6">
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filteredDrivers.length === 0 ? (
              <tr>
                <td colSpan="6" className="table-empty-cell">
                  <div className="empty-state-wrap">
                    <span className="empty-icon">👤</span>
                    <p className="empty-title">No drivers found</p>
                    <p className="empty-desc">
                      {searchQuery
                        ? `No driver profiles matched query "${searchQuery}".`
                        : 'No drivers found matching selected availability status.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredDrivers.map((driver) => (
                <tr key={driver.id}>
                  <td>
                    <span className="id-tag">DRV-{driver.id}</span>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#F1F5F9' }}>
                      {driver.license_number}
                    </span>
                  </td>
                  <td>
                    <span className="table-secondary-text">{driver.phone_number}</span>
                  </td>
                  <td>
                    <span className="table-secondary-text">User #{driver.user_id}</span>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${
                        driver.availability_status === 'AVAILABLE'
                          ? 'delivered'
                          : driver.availability_status === 'IN_TRANSIT' || driver.availability_status === 'ON_DUTY'
                          ? 'in-transit'
                          : 'cancelled'
                      }`}
                    >
                      {driver.availability_status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
                      {canUpdateStatus && (
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenStatus(driver)}
                        >
                          Status
                        </button>
                      )}
                      {isManagerOrAdmin && (
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenEdit(driver)}
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Driver Modal */}
      <DriverModal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ isOpen: false, driver: null, isStatusOnly: false })}
        driver={modalState.driver}
        isStatusOnly={modalState.isStatusOnly}
        onSaved={fetchDrivers}
      />
    </div>
  );
}
