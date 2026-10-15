import React from 'react';

/**
 * ModelDisclaimerBar
 * Slim information bar at the base of the dashboard matching the reference image.
 * Explicitly transparent regarding the synthetic ML model benchmark status.
 */
export default function ModelDisclaimerBar() {
  return (
    <aside className="ref-model-disclaimer-bar" aria-label="Machine Learning Model Operational Disclaimer">
      <div className="disclaimer-left">
        <div className="disclaimer-icon-circle">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" strokeWidth="2.2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        </div>
        <div className="disclaimer-text-group">
          <span className="disclaimer-badge-title">Model Disclaimer</span>
          <p className="disclaimer-paragraph">
            Experimental ML model trained on synthetic shipment data. Predictions are not validated for real-world shipment-delay decisions. Risk levels are application-defined categories, not calibrated operational risk ratings.
          </p>
        </div>
      </div>

      <div className="disclaimer-right">
        <span className="disclaimer-model-tag" title="RandomForestClassifier pipeline benchmark">
          india_delay_rf_v1 ⓘ
        </span>
      </div>
    </aside>
  );
}
