/**
 * FlowGrid Geographic & Coordinate Resolution Utilities
 * =====================================================
 * Provides parsing, validation, and spatial resolution of logistics hubs,
 * warehouse corridors, destination cities, and tracking waypoint checkpoints.
 */

// Well-known coordinates for standard logistics hubs and cities
export const KNOWN_LOGISTICS_COORDINATES = {
  // Hubs / Warehouses
  'chicago': { lat: 41.8781, lng: -87.6298, label: 'Chicago, IL (Midwest Hub ORD-01)' },
  'ord-01': { lat: 41.8781, lng: -87.6298, label: 'Midwest Regional Hub (ORD-01)' },
  'newark': { lat: 40.7357, lng: -74.1724, label: 'Newark, NJ (East Coast Gateway EWR-02)' },
  'ewr-02': { lat: 40.7357, lng: -74.1724, label: 'East Coast Gateway (EWR-02)' },
  'dallas': { lat: 32.7767, lng: -96.7970, label: 'Dallas, TX (Southwest Center DFW-04)' },
  'dfw-04': { lat: 32.7767, lng: -96.7970, label: 'Southwest Logistics Center (DFW-04)' },

  // Destination Cities & Corridors
  'detroit': { lat: 42.3314, lng: -83.0458, label: 'Detroit, MI' },
  'boston': { lat: 42.3601, lng: -71.0589, label: 'Boston, MA' },
  'austin': { lat: 30.2672, lng: -97.7431, label: 'Austin, TX' },
  'minneapolis': { lat: 44.9778, lng: -93.2650, label: 'Minneapolis, MN' },
  'philadelphia': { lat: 39.9526, lng: -75.1652, label: 'Philadelphia, PA' },
  'cleveland': { lat: 41.4993, lng: -81.6944, label: 'Cleveland, OH' },
  'atlanta': { lat: 33.7490, lng: -84.3880, label: 'Atlanta, GA' },
  'denver': { lat: 39.7392, lng: -104.9903, label: 'Denver, CO' },
  'los angeles': { lat: 34.0522, lng: -118.2437, label: 'Los Angeles, CA' },
  'seattle': { lat: 47.6062, lng: -122.3321, label: 'Seattle, WA' },
  'miami': { lat: 25.7617, lng: -80.1918, label: 'Miami, FL' },
  'new york': { lat: 40.7128, lng: -74.0060, label: 'New York, NY' },
  'toledo': { lat: 41.6528, lng: -83.5379, label: 'Toledo Transit Point, OH' },
  'hartford': { lat: 41.7658, lng: -72.6734, label: 'Hartford, CT' },
  'waco': { lat: 31.5493, lng: -97.1467, label: 'Waco Waypoint, TX' },
  'indianapolis': { lat: 39.7684, lng: -86.1581, label: 'Indianapolis, IN' },
  'columbus': { lat: 39.9612, lng: -82.9988, label: 'Columbus, OH' },
  'pittsburgh': { lat: 40.4406, lng: -79.9959, label: 'Pittsburgh, PA' },
  'houston': { lat: 29.7604, lng: -95.3698, label: 'Houston, TX' },
};

/**
 * Validates whether numeric latitude and longitude fall within legal WGS84 ranges.
 */
export function isValidCoordinate(lat, lng) {
  if (typeof lat !== 'number' || typeof lng !== 'number') return false;
  if (Number.isNaN(lat) || Number.isNaN(lng)) return false;
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
}

/**
 * Parses coordinates directly embedded in text, supporting:
 * - "41.8781, -87.6298"
 * - "[41.8781, -87.6298]"
 * - "(41.8781, -87.6298)"
 * - "lat: 41.8781, lng: -87.6298"
 * - "Hub Location [41.8781, -87.6298]"
 */
export function parseCoordinates(inputStr) {
  if (!inputStr || typeof inputStr !== 'string') return null;

  // Pattern 1: [lat, lng] or (lat, lng) or just lat, lng
  const coordRegex = /[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)/;
  const match = inputStr.match(coordRegex);

  if (match) {
    const parts = match[0].split(',').map((p) => parseFloat(p.trim()));
    if (parts.length === 2 && isValidCoordinate(parts[0], parts[1])) {
      return { lat: parts[0], lng: parts[1] };
    }
  }

  // Pattern 2: lat: X, lon/lng: Y
  const labeledRegex = /lat(?:itude)?[:=\s]+([-+]?\d+(\.\d+)?)[,\s]+l(?:ng|on|ongitude)?[:=\s]+([-+]?\d+(\.\d+)?)/i;
  const labeledMatch = inputStr.match(labeledRegex);
  if (labeledMatch) {
    const lat = parseFloat(labeledMatch[1]);
    const lng = parseFloat(labeledMatch[3]);
    if (isValidCoordinate(lat, lng)) {
      return { lat, lng };
    }
  }

  return null;
}

/**
 * Resolves coordinate for any location string (checks coordinates first, then known hubs/cities).
 */
export function resolveLocationCoordinates(locationStr) {
  if (!locationStr || typeof locationStr !== 'string') return null;

  // 1. Direct coordinate format in string
  const directCoords = parseCoordinates(locationStr);
  if (directCoords) {
    return {
      lat: directCoords.lat,
      lng: directCoords.lng,
      label: locationStr.trim(),
    };
  }

  // 2. Lookup against known logistics dictionary
  const normalized = locationStr.toLowerCase();
  for (const [key, value] of Object.entries(KNOWN_LOGISTICS_COORDINATES)) {
    if (normalized.includes(key)) {
      return {
        lat: value.lat,
        lng: value.lng,
        label: value.label || locationStr,
      };
    }
  }

  return null;
}

/**
 * Builds the complete geographic route model for a shipment and its tracking events.
 * Returns origin, destination, waypoints, and ordered polyline points.
 */
export function buildShipmentRouteCoordinates(shipment, trackingEvents = []) {
  if (!shipment) {
    return {
      origin: null,
      destination: null,
      waypoints: [],
      polylinePoints: [],
      hasCoordinates: false,
    };
  }

  // 1. Resolve Origin
  let origin = null;
  const originWarehouse = shipment.origin_warehouse;
  const originSearchStr = originWarehouse
    ? `${originWarehouse.name || ''} ${originWarehouse.location || ''} ${originWarehouse.address || ''}`
    : shipment.origin_address || '';

  const resolvedOrigin = resolveLocationCoordinates(originSearchStr);
  if (resolvedOrigin) {
    origin = {
      lat: resolvedOrigin.lat,
      lng: resolvedOrigin.lng,
      label: originWarehouse ? `${originWarehouse.name} (${originWarehouse.location})` : resolvedOrigin.label,
      type: 'ORIGIN',
    };
  }

  // 2. Resolve Destination
  let destination = null;
  const destSearchStr = [
    shipment.destination_city,
    shipment.destination_state,
    shipment.destination_address,
  ].filter(Boolean).join(', ');

  const resolvedDest = resolveLocationCoordinates(destSearchStr);
  if (resolvedDest) {
    destination = {
      lat: resolvedDest.lat,
      lng: resolvedDest.lng,
      label: `${shipment.destination_city || 'Destination'}, ${shipment.destination_state || ''}`.trim(),
      address: shipment.destination_address,
      type: 'DESTINATION',
    };
  }

  // 3. Resolve Waypoints
  const waypoints = [];
  if (Array.isArray(trackingEvents)) {
    // Process chronologically (oldest to newest for path ordering)
    const sortedEvents = [...trackingEvents].sort(
      (a, b) => new Date(a.timestamp || a.created_at) - new Date(b.timestamp || b.created_at)
    );

    sortedEvents.forEach((evt, idx) => {
      const coords = resolveLocationCoordinates(evt.location);
      if (coords) {
        waypoints.push({
          lat: coords.lat,
          lng: coords.lng,
          label: evt.location,
          eventType: evt.event_type || 'CHECKPOINT',
          description: evt.description || '',
          timestamp: evt.timestamp || evt.created_at,
          index: idx + 1,
          type: 'WAYPOINT',
        });
      }
    });
  }

  // 4. Construct Polyline Points
  const polylinePoints = [];
  if (origin) {
    polylinePoints.push([origin.lat, origin.lng]);
  }
  waypoints.forEach((wp) => {
    polylinePoints.push([wp.lat, wp.lng]);
  });
  if (destination) {
    polylinePoints.push([destination.lat, destination.lng]);
  }

  const hasCoordinates = polylinePoints.length >= 2;

  return {
    origin,
    destination,
    waypoints,
    polylinePoints,
    hasCoordinates,
  };
}
