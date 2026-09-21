/**
 * FlowGrid Data Export & Reporting Service
 * ========================================
 * Generates sanitized, RFC 4180 compliant CSV exports for shipments,
 * inventory stock, and analytics snapshots.
 *
 * Security & Integrity:
 * - Omits internal database IDs, hashes, and sensitive authentication fields.
 * - Operates strictly on client-accessible data governed by backend JWT RBAC.
 * - Prepends UTF-8 Byte Order Mark (BOM) for seamless Microsoft Excel compatibility.
 */

/**
 * Escapes and encapsulates a single cell value for RFC 4180 compliance.
 */
export function formatCSVField(val) {
  if (val === null || val === undefined) {
    return '""';
  }
  const str = String(val);
  // If string contains quotes, commas, or newlines, wrap in quotes and escape internal quotes
  if (str.includes('"') || str.includes(',') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return `"${str}"`;
}

/**
 * Triggers native browser download of a CSV file.
 */
export function downloadCSV(filename, csvRows) {
  const csvContent = csvRows.join('\r\n');
  // UTF-8 Byte Order Mark (\uFEFF) for Excel unicode compatibility
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exports a collection of shipments to a sanitized CSV spreadsheet.
 */
export function exportShipmentsToCSV(shipments, filenamePrefix = 'flowgrid_shipments') {
  if (!Array.isArray(shipments) || shipments.length === 0) {
    throw new Error('No shipment records available to export.');
  }

  const headers = [
    'Tracking Number',
    'Status',
    'Origin Facility',
    'Destination Address',
    'City',
    'State',
    'Postal Code',
    'Assigned Driver',
    'Assigned Vehicle',
    'Weight (kg)',
    'Volume (cbm)',
    'Created At',
    'Delivered At',
  ];

  const rows = [headers.map(formatCSVField).join(',')];

  shipments.forEach((s) => {
    const originName = s.origin_warehouse
      ? `${s.origin_warehouse.name} (${s.origin_warehouse.location})`
      : 'Unassigned Origin';

    const driverName = s.assigned_driver
      ? s.assigned_driver.name || `Driver #${s.assigned_driver_id}`
      : 'Unassigned';

    const vehicleReg = s.assigned_vehicle
      ? s.assigned_vehicle.registration_number || `Unit #${s.assigned_vehicle_id}`
      : 'Unassigned';

    const row = [
      s.tracking_number || '',
      s.status || '',
      originName,
      s.destination_address || '',
      s.destination_city || '',
      s.destination_state || '',
      s.destination_postal_code || '',
      driverName,
      vehicleReg,
      s.total_weight_kg ?? '',
      s.total_volume_cbm ?? '',
      s.created_at ? new Date(s.created_at).toISOString() : '',
      s.delivered_at ? new Date(s.delivered_at).toISOString() : '',
    ];

    rows.push(row.map(formatCSVField).join(','));
  });

  const timestamp = new Date().toISOString().split('T')[0];
  downloadCSV(`${filenamePrefix}_${timestamp}.csv`, rows);
  return shipments.length;
}

/**
 * Exports inventory records to a sanitized CSV spreadsheet.
 */
export function exportInventoryToCSV(inventoryItems, filenamePrefix = 'flowgrid_inventory') {
  if (!Array.isArray(inventoryItems) || inventoryItems.length === 0) {
    throw new Error('No inventory records available to export.');
  }

  const headers = [
    'Warehouse Facility',
    'Facility Location',
    'Product SKU',
    'Product Name',
    'Unit Price ($)',
    'Available Quantity',
    'Reorder Threshold',
    'Stock Status',
    'Last Updated',
  ];

  const rows = [headers.map(formatCSVField).join(',')];

  inventoryItems.forEach((item) => {
    const isLowStock = item.quantity <= item.reorder_level;
    const stockStatus = isLowStock ? 'CRITICAL LOW STOCK' : 'ADEQUATE';

    const row = [
      item.warehouse?.name || `Warehouse #${item.warehouse_id}`,
      item.warehouse?.location || 'N/A',
      item.product?.sku || 'N/A',
      item.product?.name || 'N/A',
      item.product?.unit_price ?? '',
      item.quantity ?? 0,
      item.reorder_level ?? 0,
      stockStatus,
      item.updated_at ? new Date(item.updated_at).toISOString() : '',
    ];

    rows.push(row.map(formatCSVField).join(','));
  });

  const timestamp = new Date().toISOString().split('T')[0];
  downloadCSV(`${filenamePrefix}_${timestamp}.csv`, rows);
  return inventoryItems.length;
}

/**
 * Exports executive overview analytics snapshot to CSV.
 */
export function exportAnalyticsToCSV(overview, filenamePrefix = 'flowgrid_analytics_overview') {
  if (!overview) {
    throw new Error('No analytics data available to export.');
  }

  const headers = ['Metric Description', 'Value'];
  const rows = [headers.map(formatCSVField).join(',')];

  const metrics = [
    ['Total Shipments Recorded', overview.total_shipments ?? 0],
    ['Active Shipments In Transit', overview.active_shipments ?? 0],
    ['Delivered Shipments', overview.delivered_shipments ?? 0],
    ['Exceptions / Failed Shipments', overview.delayed_or_failed_shipments ?? 0],
    ['Operational Warehouses', overview.total_warehouses ?? 0],
    ['Commercial SKUs / Products', overview.total_products ?? 0],
    ['Fleet Drivers', overview.total_drivers ?? 0],
    ['Active Transit Corridors', overview.active_routes ?? 0],
    ['Report Generated Timestamp', new Date().toISOString()],
  ];

  metrics.forEach(([desc, val]) => {
    rows.push([formatCSVField(desc), formatCSVField(val)].join(','));
  });

  const timestamp = new Date().toISOString().split('T')[0];
  downloadCSV(`${filenamePrefix}_${timestamp}.csv`, rows);
  return metrics.length;
}
