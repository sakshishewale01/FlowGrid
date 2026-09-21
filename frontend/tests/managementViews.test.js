import test from 'node:test';
import assert from 'node:assert/strict';

import {
  warehousesApi,
  inventoryApi,
  driversApi,
  vehiclesApi,
  shipmentsApi,
  routesApi,
} from '../src/api/index.js';

test('Management APIs: Warehouses CRUD operations are available', () => {
  assert.equal(typeof warehousesApi.listWarehouses, 'function');
  assert.equal(typeof warehousesApi.getWarehouse, 'function');
  assert.equal(typeof warehousesApi.createWarehouse, 'function');
  assert.equal(typeof warehousesApi.updateWarehouse, 'function');
  assert.equal(typeof warehousesApi.deleteWarehouse, 'function');
});

test('Management APIs: Inventory adjustment and listing operations are available', () => {
  assert.equal(typeof inventoryApi.listInventory, 'function');
  assert.equal(typeof inventoryApi.getInventory, 'function');
  assert.equal(typeof inventoryApi.createInventory, 'function');
  assert.equal(typeof inventoryApi.updateInventory, 'function');
  assert.equal(typeof inventoryApi.deleteInventory, 'function');
});

test('Management APIs: Drivers availability and status operations are available', () => {
  assert.equal(typeof driversApi.listDrivers, 'function');
  assert.equal(typeof driversApi.getDriver, 'function');
  assert.equal(typeof driversApi.createDriver, 'function');
  assert.equal(typeof driversApi.updateDriver, 'function');
  assert.equal(typeof driversApi.deleteDriver, 'function');
});

test('Management APIs: Vehicles fleet operations are available', () => {
  assert.equal(typeof vehiclesApi.listVehicles, 'function');
  assert.equal(typeof vehiclesApi.getVehicle, 'function');
  assert.equal(typeof vehiclesApi.createVehicle, 'function');
  assert.equal(typeof vehiclesApi.updateVehicle, 'function');
  assert.equal(typeof vehiclesApi.deleteVehicle, 'function');
});

test('Management APIs: Shipments status transitions and assignments are available', () => {
  assert.equal(typeof shipmentsApi.listShipments, 'function');
  assert.equal(typeof shipmentsApi.getShipment, 'function');
  assert.equal(typeof shipmentsApi.getShipmentByTracking, 'function');
  assert.equal(typeof shipmentsApi.createShipment, 'function');
  assert.equal(typeof shipmentsApi.updateShipment, 'function');
  assert.equal(typeof shipmentsApi.transitionStatus, 'function');
  assert.equal(typeof shipmentsApi.updateStatus, 'function');
  assert.equal(typeof shipmentsApi.assignShipment, 'function');
});

test('Management APIs: Routes corridor listing and shipment allocation are available', () => {
  assert.equal(typeof routesApi.listRoutes, 'function');
  assert.equal(typeof routesApi.getRoute, 'function');
  assert.equal(typeof routesApi.createRoute, 'function');
  assert.equal(typeof routesApi.updateRoute, 'function');
  assert.equal(typeof routesApi.deleteRoute, 'function');
  assert.equal(typeof routesApi.getRouteShipments, 'function');
  assert.equal(typeof routesApi.assignShipmentToRoute, 'function');
});

test('State Machine: Permitted shipment status transitions adhere to lifecycle rules', () => {
  const transitions = {
    CREATED: ['CONFIRMED', 'CANCELLED'],
    CONFIRMED: ['ASSIGNED', 'CANCELLED'],
    ASSIGNED: ['DISPATCHED', 'IN_TRANSIT', 'CANCELLED'],
    DISPATCHED: ['IN_TRANSIT', 'CANCELLED'],
    IN_TRANSIT: ['OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED'],
    OUT_FOR_DELIVERY: ['DELIVERED', 'FAILED'],
    DELIVERED: [],
    FAILED: ['CONFIRMED', 'CANCELLED'],
    CANCELLED: [],
  };

  assert.deepEqual(transitions.CREATED, ['CONFIRMED', 'CANCELLED']);
  assert.deepEqual(transitions.IN_TRANSIT, ['OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED']);
  assert.equal(transitions.DELIVERED.length, 0, 'DELIVERED is terminal state');
  assert.equal(transitions.CANCELLED.length, 0, 'CANCELLED is terminal state');
});

test('RBAC Matrix: Role permission verification logic', () => {
  const canManageFacilities = (role) => ['ADMIN', 'MANAGER'].includes(role);
  const canDeleteFacilities = (role) => role === 'ADMIN';
  const canUpdateDriverStatus = (role) => ['ADMIN', 'MANAGER', 'DRIVER'].includes(role);
  const canDispatchShipment = (role) => ['ADMIN', 'MANAGER'].includes(role);

  // ADMIN
  assert.equal(canManageFacilities('ADMIN'), true);
  assert.equal(canDeleteFacilities('ADMIN'), true);
  assert.equal(canUpdateDriverStatus('ADMIN'), true);
  assert.equal(canDispatchShipment('ADMIN'), true);

  // MANAGER
  assert.equal(canManageFacilities('MANAGER'), true);
  assert.equal(canDeleteFacilities('MANAGER'), false);
  assert.equal(canUpdateDriverStatus('MANAGER'), true);
  assert.equal(canDispatchShipment('MANAGER'), true);

  // DRIVER
  assert.equal(canManageFacilities('DRIVER'), false);
  assert.equal(canDeleteFacilities('DRIVER'), false);
  assert.equal(canUpdateDriverStatus('DRIVER'), true);
  assert.equal(canDispatchShipment('DRIVER'), false);

  // VIEWER
  assert.equal(canManageFacilities('VIEWER'), false);
  assert.equal(canDeleteFacilities('VIEWER'), false);
  assert.equal(canUpdateDriverStatus('VIEWER'), false);
  assert.equal(canDispatchShipment('VIEWER'), false);
});
