import test from 'node:test';
import assert from 'node:assert/strict';

import {
  warehousesApi,
  productsApi,
  inventoryApi,
  driversApi,
  vehiclesApi,
  shipmentsApi,
  trackingApi,
  routesApi,
  analyticsApi,
} from '../src/api/index.js';

test('API Services: All domain service modules are properly exported', () => {
  assert.ok(warehousesApi, 'warehousesApi should exist');
  assert.ok(productsApi, 'productsApi should exist');
  assert.ok(inventoryApi, 'inventoryApi should exist');
  assert.ok(driversApi, 'driversApi should exist');
  assert.ok(vehiclesApi, 'vehiclesApi should exist');
  assert.ok(shipmentsApi, 'shipmentsApi should exist');
  assert.ok(trackingApi, 'trackingApi should exist');
  assert.ok(routesApi, 'routesApi should exist');
  assert.ok(analyticsApi, 'analyticsApi should exist');
});

test('API Services: warehousesApi has all expected methods', () => {
  assert.equal(typeof warehousesApi.listWarehouses, 'function');
  assert.equal(typeof warehousesApi.getWarehouse, 'function');
  assert.equal(typeof warehousesApi.createWarehouse, 'function');
  assert.equal(typeof warehousesApi.updateWarehouse, 'function');
  assert.equal(typeof warehousesApi.deleteWarehouse, 'function');
});

test('API Services: shipmentsApi has all expected methods', () => {
  assert.equal(typeof shipmentsApi.listShipments, 'function');
  assert.equal(typeof shipmentsApi.getShipment, 'function');
  assert.equal(typeof shipmentsApi.getShipmentByTracking, 'function');
  assert.equal(typeof shipmentsApi.createShipment, 'function');
  assert.equal(typeof shipmentsApi.updateShipment, 'function');
  assert.equal(typeof shipmentsApi.transitionStatus, 'function');
  assert.equal(typeof shipmentsApi.assignShipment, 'function');
});

test('API Services: trackingApi has all expected methods', () => {
  assert.equal(typeof trackingApi.getStatusHistory, 'function');
  assert.equal(typeof trackingApi.addTrackingEvent, 'function');
  assert.equal(typeof trackingApi.getTrackingEvents, 'function');
  assert.equal(typeof trackingApi.getLatestTrackingInfo, 'function');
  assert.equal(typeof trackingApi.lookupByTrackingNumber, 'function');
});

test('API Services: analyticsApi has all expected methods', () => {
  assert.equal(typeof analyticsApi.getOverview, 'function');
  assert.equal(typeof analyticsApi.getShipmentAnalytics, 'function');
  assert.equal(typeof analyticsApi.getInventoryAnalytics, 'function');
  assert.equal(typeof analyticsApi.getWarehouseAnalytics, 'function');
  assert.equal(typeof analyticsApi.getRouteAnalytics, 'function');
});
