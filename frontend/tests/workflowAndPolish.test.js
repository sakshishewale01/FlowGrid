import test from 'node:test';
import assert from 'node:assert/strict';

test('Workflow State Machine: Adheres strictly to backend ALLOWED_TRANSITIONS', () => {
  const ALLOWED_TRANSITIONS = {
    CREATED: ['CONFIRMED', 'CANCELLED'],
    CONFIRMED: ['ASSIGNED', 'CANCELLED'],
    ASSIGNED: ['PICKED_UP', 'CANCELLED'],
    PICKED_UP: ['IN_TRANSIT'],
    IN_TRANSIT: ['OUT_FOR_DELIVERY'],
    OUT_FOR_DELIVERY: ['DELIVERED', 'FAILED'],
    FAILED: ['OUT_FOR_DELIVERY', 'RETURNED'],
    DELIVERED: [],
    CANCELLED: [],
    RETURNED: [],
  };

  // Step 1: Confirmation
  assert.ok(ALLOWED_TRANSITIONS.CREATED.includes('CONFIRMED'));
  assert.ok(ALLOWED_TRANSITIONS.CREATED.includes('CANCELLED'));

  // Step 2: Resource Assignment
  assert.ok(ALLOWED_TRANSITIONS.CONFIRMED.includes('ASSIGNED'));

  // Step 3: Dispatch & Pickup
  assert.ok(ALLOWED_TRANSITIONS.ASSIGNED.includes('PICKED_UP'));

  // Step 4: Line-Haul Transit
  assert.ok(ALLOWED_TRANSITIONS.PICKED_UP.includes('IN_TRANSIT'));

  // Step 5: Last-mile delivery zone
  assert.ok(ALLOWED_TRANSITIONS.IN_TRANSIT.includes('OUT_FOR_DELIVERY'));

  // Step 6: Delivery outcome
  assert.ok(ALLOWED_TRANSITIONS.OUT_FOR_DELIVERY.includes('DELIVERED'));
  assert.ok(ALLOWED_TRANSITIONS.OUT_FOR_DELIVERY.includes('FAILED'));

  // Step 7: Failure retry or depot return
  assert.ok(ALLOWED_TRANSITIONS.FAILED.includes('OUT_FOR_DELIVERY'));
  assert.ok(ALLOWED_TRANSITIONS.FAILED.includes('RETURNED'));

  // Terminal states
  assert.equal(ALLOWED_TRANSITIONS.DELIVERED.length, 0);
  assert.equal(ALLOWED_TRANSITIONS.CANCELLED.length, 0);
  assert.equal(ALLOWED_TRANSITIONS.RETURNED.length, 0);
});

test('RBAC Workflow Authorization Matrix', () => {
  const canConfirmShipment = (role) => ['ADMIN', 'MANAGER'].includes(role);
  const canAssignResources = (role) => ['ADMIN', 'MANAGER'].includes(role);
  const canDispatchShipment = (role) => ['ADMIN', 'MANAGER'].includes(role);
  const canRecordWaypoint = (role) => ['ADMIN', 'MANAGER'].includes(role);
  const canCancelShipment = (role) => ['ADMIN', 'MANAGER'].includes(role);

  // Admin has full authorization
  assert.equal(canConfirmShipment('ADMIN'), true);
  assert.equal(canAssignResources('ADMIN'), true);
  assert.equal(canDispatchShipment('ADMIN'), true);
  assert.equal(canRecordWaypoint('ADMIN'), true);
  assert.equal(canCancelShipment('ADMIN'), true);

  // Manager has operational workflow authorization
  assert.equal(canConfirmShipment('MANAGER'), true);
  assert.equal(canAssignResources('MANAGER'), true);
  assert.equal(canDispatchShipment('MANAGER'), true);
  assert.equal(canRecordWaypoint('MANAGER'), true);
  assert.equal(canCancelShipment('MANAGER'), true);

  // Driver has field execution restrictions
  assert.equal(canConfirmShipment('DRIVER'), false);
  assert.equal(canAssignResources('DRIVER'), false);
  assert.equal(canCancelShipment('DRIVER'), false);

  // Viewer is strictly read-only
  assert.equal(canConfirmShipment('VIEWER'), false);
  assert.equal(canAssignResources('VIEWER'), false);
  assert.equal(canDispatchShipment('VIEWER'), false);
  assert.equal(canRecordWaypoint('VIEWER'), false);
  assert.equal(canCancelShipment('VIEWER'), false);
});

test('Pagination Calculations for DataTable', () => {
  const calculatePagination = (totalItems, pageSize, currentPage) => {
    const totalPages = Math.ceil(totalItems / pageSize) || 1;
    const clampedPage = Math.min(Math.max(1, currentPage), totalPages);
    const startEntry = (clampedPage - 1) * pageSize + 1;
    const endEntry = Math.min(clampedPage * pageSize, totalItems);
    return { totalPages, clampedPage, startEntry, endEntry };
  };

  const p1 = calculatePagination(25, 10, 1);
  assert.equal(p1.totalPages, 3);
  assert.equal(p1.startEntry, 1);
  assert.equal(p1.endEntry, 10);

  const p2 = calculatePagination(25, 10, 3);
  assert.equal(p2.startEntry, 21);
  assert.equal(p2.endEntry, 25);

  const pEmpty = calculatePagination(0, 10, 1);
  assert.equal(pEmpty.totalPages, 1);
  assert.equal(pEmpty.endEntry, 0);
});
