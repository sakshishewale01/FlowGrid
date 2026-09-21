/**
 * FlowGrid Shipment Route Map Component
 * =====================================
 * Interactive Leaflet-powered route visualizer styled for Deep Tech Blue.
 * Visualizes:
 * - Origin logistics hub / warehouse (Emerald glow)
 * - Destination consignee location (Sky Blue glow)
 * - Sequential tracking waypoints (Amber/cyan pings)
 * - Transit corridor polyline
 * - Graceful fallback empty state if coordinates cannot be resolved.
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { buildShipmentRouteCoordinates } from '../utils/geoUtils.js';
import EmptyState from './EmptyState.jsx';

// Custom Marker HTML Generators
const createOriginIcon = (label) =>
  L.divIcon({
    className: 'custom-map-marker-wrapper',
    html: `
      <div class="map-marker map-marker-origin" title="${label || 'Origin Warehouse'}">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });

const createDestinationIcon = (label) =>
  L.divIcon({
    className: 'custom-map-marker-wrapper',
    html: `
      <div class="map-marker map-marker-dest" title="${label || 'Destination'}">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
          <circle cx="12" cy="10" r="3"></circle>
        </svg>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });

const createWaypointIcon = (index, label) =>
  L.divIcon({
    className: 'custom-map-marker-wrapper',
    html: `
      <div class="map-marker map-marker-waypoint" title="${label || `Waypoint ${index}`}">
        <span>${index}</span>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });

export default function ShipmentRouteMap({
  shipment,
  trackingEvents = [],
  height = '340px',
  className = '',
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapError, setMapError] = useState(null);

  const routeData = buildShipmentRouteCoordinates(shipment, trackingEvents);
  const { origin, destination, waypoints, polylinePoints, hasCoordinates } = routeData;

  useEffect(() => {
    if (!mapContainerRef.current || !hasCoordinates) {
      return;
    }

    try {
      // Cleanup previous map instance if it exists
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      // Initialize Leaflet map with CartoDB Dark Matter tiles
      const initialCenter = origin
        ? [origin.lat, origin.lng]
        : polylinePoints[0] || [39.8283, -98.5795]; // Center of USA default

      const map = L.map(mapContainerRef.current, {
        center: initialCenter,
        zoom: 5,
        zoomControl: true,
        attributionControl: true,
      });

      mapInstanceRef.current = map;

      // Dark theme CartoDB basemap
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

      // Add Origin Marker
      if (origin) {
        const originMarker = L.marker([origin.lat, origin.lng], {
          icon: createOriginIcon(origin.label),
        }).addTo(map);

        originMarker.bindPopup(`
          <div class="map-popup">
            <div class="map-popup-badge origin">ORIGIN DISPATCH</div>
            <div class="map-popup-title">${origin.label}</div>
            <div class="map-popup-meta">Coords: [${origin.lat.toFixed(4)}, ${origin.lng.toFixed(4)}]</div>
          </div>
        `);
      }

      // Add Waypoint Markers
      waypoints.forEach((wp) => {
        const wpMarker = L.marker([wp.lat, wp.lng], {
          icon: createWaypointIcon(wp.index, wp.label),
        }).addTo(map);

        wpMarker.bindPopup(`
          <div class="map-popup">
            <div class="map-popup-badge waypoint">WAYPOINT #${wp.index}</div>
            <div class="map-popup-title">${wp.label}</div>
            ${wp.eventType ? `<div class="map-popup-sub">${wp.eventType}</div>` : ''}
            ${wp.description ? `<p class="map-popup-desc">${wp.description}</p>` : ''}
            <div class="map-popup-meta">${wp.timestamp ? new Date(wp.timestamp).toLocaleString() : ''}</div>
          </div>
        `);
      });

      // Add Destination Marker
      if (destination) {
        const destMarker = L.marker([destination.lat, destination.lng], {
          icon: createDestinationIcon(destination.label),
        }).addTo(map);

        destMarker.bindPopup(`
          <div class="map-popup">
            <div class="map-popup-badge destination">DESTINATION CONSIGNEE</div>
            <div class="map-popup-title">${destination.label}</div>
            ${destination.address ? `<div class="map-popup-sub">${destination.address}</div>` : ''}
            <div class="map-popup-meta">Coords: [${destination.lat.toFixed(4)}, ${destination.lng.toFixed(4)}]</div>
          </div>
        `);
      }

      // Add Glowing Polyline
      if (polylinePoints.length >= 2) {
        // Outer glow
        L.polyline(polylinePoints, {
          color: '#0284c7',
          weight: 7,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        // Core line
        L.polyline(polylinePoints, {
          color: '#38bdf8',
          weight: 3.5,
          opacity: 0.9,
          dashArray: shipment?.status === 'DELIVERED' ? null : '6, 6',
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        // Fit map bounds to show all markers with comfortable margin
        map.fitBounds(polylinePoints, {
          padding: [45, 45],
          maxZoom: 12,
        });
      }

      // Trigger map resize invalidate after render to ensure proper tile sizing
      setTimeout(() => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.invalidateSize();
        }
      }, 250);
    } catch (err) {
      console.error('Failed to initialize Leaflet route map:', err);
      setMapError('Unable to render map view.');
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [hasCoordinates, shipment, trackingEvents, origin, destination, waypoints, polylinePoints]);

  if (!hasCoordinates || mapError) {
    return (
      <div
        className={`route-map-fallback ${className}`}
        style={{ minHeight: height }}
      >
        <EmptyState
          icon="map-pin"
          title="Geographic Corridor Unavailable"
          description={
            shipment
              ? `Could not resolve geographic coordinates for "${shipment.destination_city || 'destination'}" or origin facility.`
              : 'Select a shipment with valid facility and destination details to view the route.'
          }
        />
      </div>
    );
  }

  return (
    <div className={`route-map-wrapper ${className}`}>
      <div className="route-map-header">
        <div className="route-map-legend">
          <span className="legend-item origin">
            <span className="legend-dot"></span> Origin Hub
          </span>
          {waypoints.length > 0 && (
            <span className="legend-item waypoint">
              <span className="legend-dot"></span> {waypoints.length} Checkpoint{waypoints.length > 1 ? 's' : ''}
            </span>
          )}
          <span className="legend-item destination">
            <span className="legend-dot"></span> Destination
          </span>
        </div>
        <div className="route-map-tag">
          {shipment?.tracking_number || 'Transit Corridor'}
        </div>
      </div>

      <div
        ref={mapContainerRef}
        className="leaflet-map-container"
        style={{ height, width: '100%' }}
      />
    </div>
  );
}
