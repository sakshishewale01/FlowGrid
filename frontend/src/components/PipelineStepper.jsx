import React, { useState, useEffect } from 'react';

export default function PipelineStepper({ stages = [], loading = false }) {
  const [selectedStage, setSelectedStage] = useState(null);

  useEffect(() => {
    if (stages.length > 0) {
      // Prioritize In Transit stage or stage with highest count, otherwise default to first
      const defaultStage = stages.find((s) => s.id === 'in_transit') || stages[0];
      setSelectedStage(defaultStage);
    } else {
      setSelectedStage(null);
    }
  }, [stages]);

  const totalTracked = stages.reduce((acc, s) => acc + (Number(s.count) || 0), 0);

  return (
    <div className="pipeline-container" id="shipment-pipeline-panel">
      <div className="panel-title-bar">
        <div>
          <h3 className="panel-title">Shipment Lifecycle Pipeline</h3>
          <p className="panel-subtitle">Real-time status progression from order intake to recipient delivery</p>
        </div>
        <div className="pipeline-total-badge">
          Total Tracked: <strong>{Number(totalTracked).toLocaleString()} Shipments</strong>
        </div>
      </div>

      {loading ? (
        <div className="pipeline-track five-stages">
          {[1, 2, 3, 4, 5].map((idx) => (
            <div key={idx} className="pipeline-step skeleton-step">
              <div className="skeleton-line step-header" />
              <div className="skeleton-line step-name" />
              <div className="skeleton-bar" />
            </div>
          ))}
        </div>
      ) : stages.length === 0 ? (
        <div className="pipeline-empty-state">
          <span>No lifecycle shipment telemetry recorded.</span>
        </div>
      ) : (
        /* 5-Stage Lifecycle Stepper: Created → Confirmed → Assigned → In Transit → Delivered */
        <div className="pipeline-track five-stages">
          {stages.map((stage, idx) => {
            const isSelected = selectedStage?.id === stage.id;
            return (
              <div
                key={stage.id}
                className={`pipeline-step ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedStage(stage)}
                id={`pipeline-step-${stage.id}`}
              >
                <div className="step-top-line">
                  <span className="step-index">0{idx + 1}</span>
                  <span className="step-count">{Number(stage.count || 0).toLocaleString()}</span>
                </div>
                <div className="step-label">{stage.name}</div>
                <div className="step-progress-bar">
                  <div 
                    className={`step-progress-fill ${stage.id}`} 
                    style={{ width: stage.percent || '0%' }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Active Stage Inspector Detail */}
      {selectedStage && (
        <div className="pipeline-inspector">
          <div className="inspector-left">
            <span className="inspector-tag">STAGE INSPECTION</span>
            <span className="inspector-title">
              {selectedStage.name} ({Number(selectedStage.count || 0).toLocaleString()} shipments)
            </span>
            <span className="inspector-desc">{selectedStage.description}</span>
          </div>
          <div className="inspector-right">
            <span className="pipeline-percent-badge">{selectedStage.percent} of active volume</span>
          </div>
        </div>
      )}
    </div>
  );
}
