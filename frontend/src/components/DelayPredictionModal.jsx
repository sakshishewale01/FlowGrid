import React, { useState, useMemo, useEffect } from 'react';
import Modal from './Modal.jsx';
import { mlApi } from '../api/index.js';
import { formatErrorMessage } from '../api/client.js';
import { useToast } from '../context/ToastContext.jsx';

/**
 * Verified Indian logistics benchmark corridors and road distances (km).
 * Sourced directly from backend/ml_data/india/flowgrid_delay_model_india.csv (1,451 rows).
 * Great-circle distance x 1.3 highway factor.
 */
const ROUTE_DISTANCES = {
  'Central Warehouse - Pune': {
    'Bengaluru Distribution Point': 955.8,
    'Bhopal Depot': 836.5,
    'Guwahati Market District': 2628.8,
    'Hyderabad Logistics Park': 657.5,
    'Indore Industrial Zone': 664.6,
    'JNPT Nhava Sheva Port Area': 138.8,
    'Jaipur Commerce Center': 1240.0,
    'Lucknow Retail Hub': 1529.7,
    'Mumbai City Center': 156.2,
    'Patna Supply Point': 1823.3,
    'Surat Trade Zone': 407.6,
    'Visakhapatnam Terminal': 1291.8,
  },
  'East Depot - Kolkata': {
    'Bengaluru Distribution Point': 2028.9,
    'Bhopal Depot': 1461.1,
    'Guwahati Market District': 681.0,
    'Hyderabad Logistics Park': 1536.4,
    'Indore Industrial Zone': 1668.1,
    'JNPT Nhava Sheva Port Area': 2147.0,
    'Jaipur Commerce Center': 1765.1,
    'Lucknow Retail Hub': 1153.1,
    'Mumbai City Center': 2151.3,
    'Patna Supply Point': 609.9,
    'Surat Trade Zone': 2092.6,
    'Visakhapatnam Terminal': 993.0,
  },
  'North Hub - Delhi NCR': {
    'Bengaluru Distribution Point': 2261.7,
    'Bhopal Depot': 774.4,
    'Guwahati Market District': 1897.3,
    'Hyderabad Logistics Park': 1632.0,
    'Indore Industrial Zone': 870.0,
    'JNPT Nhava Sheva Port Area': 1505.9,
    'Jaipur Commerce Center': 305.9,
    'Lucknow Retail Hub': 542.1,
    'Mumbai City Center': 1492.5,
    'Patna Supply Point': 1109.4,
    'Surat Trade Zone': 1219.2,
    'Visakhapatnam Terminal': 1769.1,
  },
  'South Terminal - Chennai': {
    'Bengaluru Distribution Point': 377.2,
    'Bhopal Depot': 1522.4,
    'Guwahati Market District': 2446.8,
    'Hyderabad Logistics Park': 669.8,
    'Indore Industrial Zone': 1519.2,
    'JNPT Nhava Sheva Port Area': 1323.9,
    'Jaipur Commerce Center': 2089.2,
    'Lucknow Retail Hub': 1991.7,
    'Mumbai City Center': 1343.0,
    'Patna Supply Point': 1925.9,
    'Surat Trade Zone': 1555.8,
    'Visakhapatnam Terminal': 782.1,
  },
  'West Storage - Ahmedabad': {
    'Bengaluru Distribution Point': 1608.2,
    'Bhopal Depot': 644.4,
    'Guwahati Market District': 2556.8,
    'Hyderabad Logistics Park': 1143.3,
    'Indore Industrial Zone': 439.9,
    'JNPT Nhava Sheva Port Area': 590.9,
    'Jaipur Commerce Center': 702.6,
    'Lucknow Retail Hub': 1228.6,
    'Mumbai City Center': 572.0,
    'Patna Supply Point': 1695.9,
    'Surat Trade Zone': 270.0,
    'Visakhapatnam Terminal': 1635.3,
  },
};

const WAREHOUSES = Object.keys(ROUTE_DISTANCES);

const DESTINATIONS = [
  'Bengaluru Distribution Point',
  'Bhopal Depot',
  'Guwahati Market District',
  'Hyderabad Logistics Park',
  'Indore Industrial Zone',
  'JNPT Nhava Sheva Port Area',
  'Jaipur Commerce Center',
  'Lucknow Retail Hub',
  'Mumbai City Center',
  'Patna Supply Point',
  'Surat Trade Zone',
  'Visakhapatnam Terminal',
];

const TRANSPORT_MODES = [
  'Heavy Truck (10-wheeler)',
  'Medium Truck (Eicher 14ft class)',
  'Mini Truck (Tata Ace class)',
  'Multi-Axle Trailer',
  'Reefer Truck',
];

const SUPPLIERS = [
  'Atlas Haulage Pvt. Ltd.',
  'BlueWave Logistics India',
  'Cobalt Route Systems',
  'Falcon Transit Group',
  'Meridian Freight Pvt. Ltd.',
  'NorthStar Carriers',
  'Orion Freight Co.',
  'Summit Cargo Partners',
];

const DRIVERS = [
  'A. Kumar',
  'B. Chatterjee',
  'D. Gupta',
  'F. Khan',
  'H. Shaikh',
  'J. Sharma',
  'K. Singh',
  'L. Nair',
  'M. Patil',
  'N. Iyer',
  'P. Das',
  'R. Yadav',
  'S. Kulkarni',
  'T. Reddy',
  'Y. Jadhav',
];

// Helper to get local date string YYYY-MM-DD
function getLocalDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function DelayPredictionModal({ isOpen, onClose }) {
  const { toast } = useToast();

  // Form input state
  const [warehouse, setWarehouse] = useState(WAREHOUSES[0]);
  const [destination, setDestination] = useState(DESTINATIONS[0]);
  const [transportMode, setTransportMode] = useState(TRANSPORT_MODES[0]);
  const [supplier, setSupplier] = useState(SUPPLIERS[0]);
  const [driver, setDriver] = useState(DRIVERS[0]);
  const [dispatchDate, setDispatchDate] = useState(getLocalDateString);

  // Dynamic verified distance lookup
  const distanceKm = useMemo(() => {
    return ROUTE_DISTANCES[warehouse]?.[destination] ?? null;
  }, [warehouse, destination]);

  // Request & Response state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [predictionResult, setPredictionResult] = useState(null);

  const handleInputChange = (setter) => (e) => {
    setter(e.target.value);
    if (predictionResult) setPredictionResult(null);
    if (errorMessage) setErrorMessage('');
  };

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!distanceKm || distanceKm <= 0) {
      setErrorMessage('Selected corridor has no verified road distance.');
      return;
    }

    if (!dispatchDate) {
      setErrorMessage('Please specify a dispatch date.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    setPredictionResult(null);

    const payload = {
      warehouse: warehouse.trim(),
      destination: destination.trim(),
      transport_mode: transportMode.trim(),
      distance_km: distanceKm,
      supplier: supplier.trim(),
      driver: driver.trim(),
      dispatch_date: dispatchDate,
    };

    try {
      const response = await mlApi.predictDelay(payload);
      setPredictionResult(response);
      toast.success('Corridor delay risk evaluated successfully');
    } catch (err) {
      const formatted = formatErrorMessage(err, 'Failed to evaluate delay prediction');
      setErrorMessage(formatted);
      toast.error(formatted);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetForm = () => {
    setWarehouse(WAREHOUSES[0]);
    setDestination(DESTINATIONS[0]);
    setTransportMode(TRANSPORT_MODES[0]);
    setSupplier(SUPPLIERS[0]);
    setDriver(DRIVERS[0]);
    setDispatchDate(getLocalDateString());
    setPredictionResult(null);
    setErrorMessage('');
  };

  const riskBadgeColor = predictionResult?.risk_level === 'HIGH'
    ? '#EF4444'
    : predictionResult?.risk_level === 'MEDIUM'
    ? '#F59E0B'
    : '#10B981';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="India Freight Delay Risk Predictor (ML Prototype)"
      subtitle="Evaluates transit delay likelihood using the trained Random Forest India benchmark pipeline"
      size="large"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* Mandatory Governance Disclaimer */}
        <div
          style={{
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            borderRadius: '8px',
            padding: '12px 16px',
            fontSize: '0.82rem',
            lineHeight: '1.45',
            color: '#FCD34D',
          }}
          role="note"
          aria-label="Model Governance Disclaimer"
        >
          <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <span>⚠️</span>
            <span>MODEL GOVERNANCE &amp; BENCHMARK NOTICE</span>
          </div>
          <p style={{ margin: 0 }}>
            Experimental ML benchmark trained on synthetic shipment data. Predictions are not validated for real-world shipment-delay decisions. Risk levels are application-defined categories, not calibrated operational risk ratings.
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="auth-alert error" role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Inference Error</span>
              <span className="auth-alert-text">{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Corridor Input Form */}
        <form onSubmit={handleSubmit} id="delay-prediction-form">
          <div className="auth-grid-2col" style={{ marginBottom: '14px' }}>
            {/* Origin Warehouse */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-select-warehouse">
                Origin Warehouse Hub
              </label>
              <select
                id="ml-select-warehouse"
                className="auth-select"
                value={warehouse}
                onChange={handleInputChange(setWarehouse)}
                disabled={isSubmitting}
                required
              >
                {WAREHOUSES.map((w) => (
                  <option key={w} value={w}>{w}</option>
                ))}
              </select>
            </div>

            {/* Destination Hub */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-select-destination">
                Destination Commercial Hub
              </label>
              <select
                id="ml-select-destination"
                className="auth-select"
                value={destination}
                onChange={handleInputChange(setDestination)}
                disabled={isSubmitting}
                required
              >
                {DESTINATIONS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="auth-grid-2col" style={{ marginBottom: '14px' }}>
            {/* Verified Corridor Highway Distance */}
            <div className="auth-field">
              <label className="auth-label">
                Verified Corridor Distance (km)
              </label>
              <div
                style={{
                  height: '42px',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 14px',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  borderRadius: '6px',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: '#38BDF8',
                }}
              >
                {distanceKm !== null ? `${distanceKm.toLocaleString()} km (Highway Great-Circle x 1.3)` : 'Select origin & destination'}
              </div>
            </div>

            {/* Transport Mode */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-select-mode">
                Transport Mode / Vehicle Class
              </label>
              <select
                id="ml-select-mode"
                className="auth-select"
                value={transportMode}
                onChange={handleInputChange(setTransportMode)}
                disabled={isSubmitting}
                required
              >
                {TRANSPORT_MODES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="auth-grid-2col" style={{ marginBottom: '14px' }}>
            {/* Carrier / Supplier */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-select-supplier">
                Carrier Partner / Supplier
              </label>
              <select
                id="ml-select-supplier"
                className="auth-select"
                value={supplier}
                onChange={handleInputChange(setSupplier)}
                disabled={isSubmitting}
                required
              >
                {SUPPLIERS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Driver */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-select-driver">
                Designated Fleet Driver
              </label>
              <select
                id="ml-select-driver"
                className="auth-select"
                value={driver}
                onChange={handleInputChange(setDriver)}
                disabled={isSubmitting}
                required
              >
                {DRIVERS.map((dr) => (
                  <option key={dr} value={dr}>{dr}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="auth-grid-2col" style={{ marginBottom: '20px' }}>
            {/* Planned Dispatch Date */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="ml-input-dispatch-date">
                Planned Dispatch Date (YYYY-MM-DD)
              </label>
              <input
                id="ml-input-dispatch-date"
                type="date"
                className="auth-input"
                style={{ paddingLeft: '12px' }}
                value={dispatchDate}
                onChange={handleInputChange(setDispatchDate)}
                disabled={isSubmitting}
                required
              />
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px' }}>
              <button
                type="submit"
                id="btn-submit-delay-prediction"
                className="btn-action primary"
                disabled={isSubmitting || !distanceKm}
                style={{ flex: 1, height: '42px', justifyContent: 'center' }}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner" style={{ width: '16px', height: '16px' }} />
                    <span>Evaluating Inference...</span>
                  </>
                ) : (
                  <>
                    <span>✦</span>
                    <span>Predict Delay Risk</span>
                  </>
                )}
              </button>
              <button
                type="button"
                className="btn-action outline"
                onClick={handleResetForm}
                disabled={isSubmitting}
                style={{ height: '42px' }}
                title="Reset form to defaults"
              >
                Reset
              </button>
            </div>
          </div>
        </form>

        {/* Prediction Results Panel */}
        {predictionResult && (
          <div
            id="ml-prediction-results-card"
            style={{
              marginTop: '4px',
              padding: '18px 20px',
              backgroundColor: 'rgba(15, 23, 42, 0.75)',
              border: `1px solid ${riskBadgeColor}55`,
              borderRadius: '8px',
              boxShadow: `0 0 20px ${riskBadgeColor}15`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    borderRadius: '4px',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    backgroundColor: predictionResult.is_delayed ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)',
                    color: predictionResult.is_delayed ? '#F87171' : '#34D399',
                    border: `1px solid ${predictionResult.is_delayed ? '#EF4444' : '#10B981'}`,
                  }}
                >
                  {predictionResult.is_delayed ? 'DELAY PREDICTED' : 'ON-TIME PREDICTED'}
                </span>
                <span
                  style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    backgroundColor: `${riskBadgeColor}22`,
                    color: riskBadgeColor,
                    border: `1px solid ${riskBadgeColor}`,
                  }}
                >
                  {predictionResult.risk_level} RISK TIER
                </span>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                Model: <code>{predictionResult.model_version}</code>
              </div>
            </div>

            {/* Score Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '12px',
                marginBottom: '14px',
              }}
            >
              <div
                style={{
                  backgroundColor: 'rgba(30, 41, 59, 0.5)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                }}
              >
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Delay Probability Score
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: riskBadgeColor, marginTop: '2px' }}>
                  {(predictionResult.delay_probability * 100).toFixed(2)}%
                </div>
                <div style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '2px' }}>
                  Raw output: {predictionResult.delay_probability.toFixed(4)}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(30, 41, 59, 0.5)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                }}
              >
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Corridor Evaluated
                </div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#F1F5F9', marginTop: '4px', lineHeight: '1.3' }}>
                  {warehouse.replace(' - ', ' → ')}
                </div>
                <div style={{ fontSize: '0.74rem', color: '#38BDF8', marginTop: '2px' }}>
                  ➔ {destination} ({distanceKm} km)
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(30, 41, 59, 0.5)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                }}
              >
                <div style={{ fontSize: '0.72rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Carrier &amp; Equipment
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#F1F5F9', marginTop: '4px' }}>
                  {transportMode}
                </div>
                <div style={{ fontSize: '0.74rem', color: '#94A3B8', marginTop: '2px' }}>
                  {supplier} • {driver}
                </div>
              </div>
            </div>

            {/* Explanation & Technical Context */}
            <div style={{ fontSize: '0.78rem', color: '#94A3B8', lineHeight: '1.45', borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '10px' }}>
              <div style={{ fontWeight: 600, color: '#CBD5E1', marginBottom: '2px' }}>Pipeline Explanation:</div>
              <div>{predictionResult.explanation}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: '6px' }}>
                Benchmark Details: Random Forest (depth=8, balanced) on synthetic benchmark dataset (1,451 records, base delay rate 20.61%, test ROC-AUC 0.5062).
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
