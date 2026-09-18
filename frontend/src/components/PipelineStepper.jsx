import React, { useState } from 'react';

export default function PipelineStepper({ stages }) {
  const [selectedStage, setSelectedStage] = useState(stages[3] || stages[0]); // Default to In Transit

  return (
    <div className="pipeline-container" id="shipment-pipeline-panel">
      <div className="panel-title-bar">
        <div>
          <h3 className="panel-title">Shipment Lifecycle Pipeline</h3>
          <p className="panel-subtitle">Real-time status progression from order intake to recipient delivery</p>
        </div>
        <div className="pipeline-total-badge">
          Total Tracked: <strong>1,428 Shipments</strong>
        </div>
      </div>

      {/* 5-Stage Lifecycle Stepper: Created → Confirmed → Assigned → In Transit → Delivered */}
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
                <span className="step-count">{stage.count}</span>
              </div>
              <div className="step-label">{stage.name}</div>
              <div className="step-progress-bar">
                <div 
                  className={`step-progress-fill ${stage.id}`} 
                  style={{ width: stage.percent }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Stage Inspector Detail */}
      {selectedStage && (
        <div className="pipeline-inspector">
          <div className="inspector-left">
            <span className="inspector-tag">STAGE INSPECTION</span>
            <span className="inspector-title">{selectedStage.name} ({selectedStage.count} shipments)</span>
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
