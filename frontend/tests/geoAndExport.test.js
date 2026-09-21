/**
 * Automated Tests for Phase 18:
 * - Geographic Coordinate Parsing & Logistics Corridor Resolution (geoUtils.js)
 * - CSV Generation, Escaping, and Data Sanitization (exportService.js)
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

import {
  isValidCoordinate,
  parseCoordinates,
  resolveLocationCoordinates,
  buildShipmentRouteCoordinates,
  KNOWN_LOGISTICS_COORDINATES,
} from '../src/utils/geoUtils.js';

import {
  formatCSVField,
} from '../src/services/exportService.js';

describe('Geographic Coordinate Utilities (geoUtils.js)', () => {
  test('isValidCoordinate validates latitude and longitude ranges correctly', () => {
    assert.equal(isValidCoordinate(41.8781, -87.6298), true);
    assert.equal(isValidCoordinate(0, 0), true);
    assert.equal(isValidCoordinate(90, 180), true);
    assert.equal(isValidCoordinate(-90, -180), true);

    // Invalid ranges
    assert.equal(isValidCoordinate(91, 0), false);
    assert.equal(isValidCoordinate(-91, 0), false);
    assert.equal(isValidCoordinate(0, 181), false);
    assert.equal(isValidCoordinate(0, -181), false);

    // Invalid types / NaNs
    assert.equal(isValidCoordinate(NaN, -87.62), false);
    assert.equal(isValidCoordinate(41.87, NaN), false);
    assert.equal(isValidCoordinate('41.87', '-87.62'), false);
    assert.equal(isValidCoordinate(null, null), false);
  });

  test('parseCoordinates extracts lat and lng from various string patterns', () => {
    // Pattern 1: standard comma separated
    const res1 = parseCoordinates('41.8781, -87.6298');
    assert.ok(res1);
    assert.equal(res1.lat, 41.8781);
    assert.equal(res1.lng, -87.6298);

    // Pattern 2: bracketed [lat, lng]
    const res2 = parseCoordinates('Chicago Depot [41.8781, -87.6298]');
    assert.ok(res2);
    assert.equal(res2.lat, 41.8781);
    assert.equal(res2.lng, -87.6298);

    // Pattern 3: labeled latitude / longitude
    const res3 = parseCoordinates('lat: 32.7767, lng: -96.7970');
    assert.ok(res3);
    assert.equal(res3.lat, 32.7767);
    assert.equal(res3.lng, -96.7970);

    // Invalid or unparseable inputs return null safely
    assert.equal(parseCoordinates('Unspecified warehouse location'), null);
    assert.equal(parseCoordinates(''), null);
    assert.equal(parseCoordinates(null), null);
    assert.equal(parseCoordinates(undefined), null);
  });

  test('resolveLocationCoordinates resolves known logistics hubs and cities', () => {
    // Known hubs
    const chicago = resolveLocationCoordinates('Midwest Regional Hub (ORD-01)');
    assert.ok(chicago);
    assert.equal(chicago.lat, 41.8781);
    assert.equal(chicago.lng, -87.6298);

    const newark = resolveLocationCoordinates('East Coast Gateway (EWR-02)');
    assert.ok(newark);
    assert.equal(newark.lat, 40.7357);

    const dallas = resolveLocationCoordinates('Southwest Logistics Center (DFW-04)');
    assert.ok(dallas);
    assert.equal(dallas.lat, 32.7767);

    // Known destination cities
    const detroit = resolveLocationCoordinates('420 Industrial Drive, Detroit, MI');
    assert.ok(detroit);
    assert.equal(detroit.lat, 42.3314);

    const boston = resolveLocationCoordinates('Boston, MA 02108');
    assert.ok(boston);
    assert.equal(boston.lat, 42.3601);

    // Unknown location
    const unknown = resolveLocationCoordinates('Unknown Location Island X');
    assert.equal(unknown, null);
  });

  test('buildShipmentRouteCoordinates constructs comprehensive corridor and waypoints', () => {
    const mockShipment = {
      tracking_number: 'FG-98421-US',
      status: 'IN_TRANSIT',
      origin_warehouse: {
        name: 'Midwest Regional Hub (ORD-01)',
        location: 'Chicago, IL',
      },
      destination_city: 'Detroit',
      destination_state: 'MI',
      destination_address: '420 Industrial Drive',
    };

    const mockEvents = [
      {
        location: 'Toledo Transit Point, OH',
        event_type: 'CHECKPOINT',
        description: 'Passed inspection dock',
        timestamp: '2026-09-21T10:00:00Z',
      },
    ];

    const route = buildShipmentRouteCoordinates(mockShipment, mockEvents);

    assert.equal(route.hasCoordinates, true);
    assert.ok(route.origin);
    assert.equal(route.origin.lat, 41.8781); // Chicago

    assert.ok(route.destination);
    assert.equal(route.destination.lat, 42.3314); // Detroit

    assert.equal(route.waypoints.length, 1);
    assert.equal(route.waypoints[0].lat, 41.6528); // Toledo

    // Polyline includes Origin -> Waypoint -> Destination
    assert.equal(route.polylinePoints.length, 3);
    assert.deepEqual(route.polylinePoints[0], [41.8781, -87.6298]);
    assert.deepEqual(route.polylinePoints[1], [41.6528, -83.5379]);
    assert.deepEqual(route.polylinePoints[2], [42.3314, -83.0458]);
  });

  test('buildShipmentRouteCoordinates handles missing/invalid coordinates gracefully without crashing', () => {
    const emptyRoute = buildShipmentRouteCoordinates(null);
    assert.equal(emptyRoute.hasCoordinates, false);
    assert.equal(emptyRoute.polylinePoints.length, 0);

    const unmappedShipment = {
      tracking_number: 'FG-00000',
      origin_warehouse: null,
      destination_city: 'Uncharted Station Nowhere',
    };
    const route = buildShipmentRouteCoordinates(unmappedShipment, []);
    assert.equal(route.hasCoordinates, false);
    assert.equal(route.origin, null);
    assert.equal(route.destination, null);
  });
});

describe('CSV Data Export & Sanitization (exportService.js)', () => {
  test('formatCSVField properly wraps and escapes values per RFC 4180', () => {
    // Normal string
    assert.equal(formatCSVField('Standard Delivery'), '"Standard Delivery"');

    // Number & Boolean
    assert.equal(formatCSVField(4250.5), '"4250.5"');
    assert.equal(formatCSVField(true), '"true"');

    // Null and Undefined
    assert.equal(formatCSVField(null), '""');
    assert.equal(formatCSVField(undefined), '""');

    // Escaping double quotes inside text
    assert.equal(formatCSVField('Fragile "Handle with care" Box'), '"Fragile ""Handle with care"" Box"');

    // Text with commas
    assert.equal(formatCSVField('Chicago, IL 60666'), '"Chicago, IL 60666"');

    // Text with newlines
    assert.equal(formatCSVField('Line 1\nLine 2'), '"Line 1\nLine 2"');
  });

  test('Sanitization rules prevent sensitive database attributes from leaking', () => {
    const mockShipment = {
      id: 101, // internal PK
      tracking_number: 'FG-98421-US',
      status: 'IN_TRANSIT',
      user_password_hash: '$2b$12$secretHash', // simulated internal leak
      origin_warehouse: { name: 'ORD Hub', location: 'Chicago' },
      destination_address: '420 Industrial Dr',
      destination_city: 'Detroit',
      destination_state: 'MI',
      destination_postal_code: '48201',
      total_weight_kg: 1500,
    };

    // Verify formatCSVField on tracking number vs hash
    const formattedTracking = formatCSVField(mockShipment.tracking_number);
    assert.equal(formattedTracking, '"FG-98421-US"');
  });
});
