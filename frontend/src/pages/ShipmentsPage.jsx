import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { shipmentsApi } from '../api/shipments.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import ShipmentDetailDrawer from '../components/ShipmentDetailDrawer';
import NewShipmentModal from '../components/NewShipmentModal';

export default function ShipmentsPage() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Drawers / Modals
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchShipments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await shipmentsApi.listShipments({ limit: 200 });
      setShipments(data || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchShipments();
  }, [fetchShipments]);

  const filteredShipments = useMemo(() => {
    return shipments.filter((s) => {
      if (statusFilter !== 'ALL' && s.status !== statusFilter) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const trk = s.tracking_number?.toLowerCase() || '';
      const city = s.destination_city?.toLowerCase() || '';
      const addr = s.destination_address?.toLowerCase() || '';
      const state = s.destination_state?.toLowerCase() || '';
      return trk.includes(q) || city.includes(q) || addr.includes(q) || state.includes(q);
    });
  }, [shipments, statusFilter, searchQuery]);

  const inTransitCount = shipments.filter((s) => s.status === 'IN_TRANSIT' || s.status === 'PICKED_UP').length;
  const deliveredCount = shipments.filter((s) => s.status === 'DELIVERED').length;
  const assignedCount = shipments.filter((s) => s.status === 'ASSIGNED').length;

  const handleOpenDetail = (shipment) => {
    setSelectedShipment(shipment);
    setIsDrawerOpen(true);
  };

  const handleShipmentUpdated = (updated) => {
    setSelectedShipment(updated);
    fetchShipments();
  };

  const handleCreated = () => {
    fetchShipments();
  };

  const columns = useMemo(() => [
    {
      key: 'tracking_number',
      header: 'Tracking Waybill',
      sortable: true,
      render: (s) => (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38BDF8' }}>
            {s.tracking_number}
          </span>
          <span style={{ fontSize: '0.72rem', color: '#64748B' }}>
            ID #{s.id} • {s.created_at ? new Date(s.created_at).toLocaleDateString() : 'Active'}
          </span>
        </div>
      ),
    },
    {
      key: 'origin',
      header: 'Origin Facility',
      render: (s) => (
        <div>
          <div className="table-primary-text">
            {s.origin_warehouse?.name || `Warehouse #${s.origin_warehouse_id || 'N/A'}`}
          </div>
          <span className="table-secondary-text">{s.origin_warehouse?.location || 'Origin Hub'}</span>
        </div>
      ),
    },
    {
      key: 'destination_city',
      header: 'Consignee Destination',
      sortable: true,
      render: (s) => (
        <div>
          <div className="table-primary-text">{s.destination_city}, {s.destination_state}</div>
          <span className="table-secondary-text" style={{ maxWidth: '200px', display: 'inline-block' }}>
            {s.destination_address}
          </span>
        </div>
      ),
    },
    {
      key: 'assigned',
      header: 'Driver & Vehicle',
      render: (s) => (
        <div>
          <div style={{ fontSize: '0.8rem', color: '#CBD5E1' }}>
            {s.assigned_driver ? `Driver #${s.assigned_driver.id}` : 'No driver'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748B' }}>
            {s.assigned_vehicle ? s.assigned_vehicle.registration_number : 'No vehicle'}
          </div>
        </div>
      ),
    },
    {
      key: 'total_weight_kg',
      header: 'Payload',
      sortable: true,
      render: (s) => (
        <div>
          <div style={{ fontSize: '0.8rem', color: '#F1F5F9', fontWeight: 600 }}>
            {s.total_weight_kg ? `${s.total_weight_kg} kg` : '0 kg'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748B' }}>
            {s.total_volume_cbm ? `${s.total_volume_cbm} m³` : 'Standard'}
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Lifecycle State',
      sortable: true,
      render: (s) => <StatusBadge status={s.status} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (s) => (
        <button
          type="button"
          className="btn-action outline"
          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
          onClick={(e) => {
            e.stopPropagation();
            handleOpenDetail(s);
          }}
        >
          Waybill & Status
        </button>
      ),
    },
  ], []);

  return (
    <div className="management-page" id="shipments-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / LOGISTICS"
        title="Shipment Operations"
        caption="End-to-end freight manifests, lifecycle stage transitions, waybills, and GPS waypoint breadcrumbs."
        metaPills={[
          { label: 'Total Shipments', value: shipments.length },
          { label: 'In Transit', value: inTransitCount, status: 'in-transit' },
          { label: 'Assigned', value: assignedCount, status: 'warning' },
          { label: 'Delivered', value: deliveredCount, status: 'online' },
        ]}
        primaryAction={{
          label: 'New Shipment',
          onClick: () => setIsCreateModalOpen(true),
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load shipments manifest</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchShipments}>
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
            placeholder="Search by tracking number, city, or destination street..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-tabs" style={{ flexWrap: 'wrap' }}>
          {['ALL', 'CREATED', 'CONFIRMED', 'ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'CANCELLED'].map((st) => (
            <button
              key={st}
              type="button"
              className={`filter-tab ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
            >
              {st === 'ALL' ? `All (${shipments.length})` : st.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Reusable Data Table */}
      <DataTable
        columns={columns}
        data={filteredShipments}
        loading={loading}
        pageSize={10}
        keyField="id"
        onRowClick={handleOpenDetail}
        emptyState={
          <EmptyState
            icon="📦"
            title="No shipment records found"
            description={
              searchQuery
                ? `No shipments matched search query "${searchQuery}".`
                : 'No shipments recorded in the selected status filter.'
            }
            action={{
              label: 'Dispatch New Shipment',
              onClick: () => setIsCreateModalOpen(true),
              requiredRoles: ['ADMIN', 'MANAGER'],
            }}
          />
        }
      />

      {/* Shipment Detail & Tracking Events Drawer */}
      <ShipmentDetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        shipment={selectedShipment}
        onUpdated={handleShipmentUpdated}
      />

      {/* New Shipment Dispatch Modal */}
      <NewShipmentModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  );
}
