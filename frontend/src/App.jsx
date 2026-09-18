import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import MetricCard from './components/MetricCard';
import PipelineStepper from './components/PipelineStepper';
import WarehouseCards from './components/WarehouseCards';
import RecentShipmentsTable from './components/RecentShipmentsTable';
import RouteMapPanel from './components/RouteMapPanel';
import QuickActions from './components/QuickActions';
import AiInsightPanel from './components/AiInsightPanel';

import {
  summaryMetrics,
  pipelineStages,
  warehouses,
  recentShipments,
  activeCorridors,
  aiOptimizationInsights
} from './data/mockLogisticsData';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  // Ping backend FastAPI /health endpoint
  const checkBackendHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      if (response.ok) {
        const data = await response.json();
        setBackendHealth({ ok: true, data });
        showNotification(`✓ FastAPI Backend Online: ${JSON.stringify(data)}`);
      } else {
        setBackendHealth({ ok: false, error: `HTTP ${response.status}` });
        showNotification(`✕ Backend returned status ${response.status}`);
      }
    } catch (err) {
      setBackendHealth({
        ok: false,
        error: 'Offline'
      });
      showNotification('FastAPI Backend is not reachable at http://127.0.0.1:8000. Start with: uvicorn app.main:app --reload in backend/');
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const showNotification = (msg) => {
    setActionNotice(msg);
    setTimeout(() => {
      setActionNotice((current) => (current === msg ? null : current));
    }, 4500);
  };

  const handleQuickAction = (actionName) => {
    showNotification(`Operational Action Triggered: "${actionName}"`);
  };

  const handleRunAiForecast = () => {
    showNotification('AI Route Optimization Algorithm triggered: Analyzing 42 active freight legs with scikit-learn pipeline...');
  };

  return (
    <div className="app-layout" id="flowgrid-ops-center">
      {/* Dark Navy Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
      />

      {/* Main Workspace */}
      <div className="main-viewport">
        {/* Top Navigation Bar with Title, Notifications, and Profile */}
        <TopNavbar
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          backendHealth={backendHealth}
          isCheckingHealth={isCheckingHealth}
          onCheckHealth={checkBackendHealth}
          pageTitle="Logistics Overview"
        />

        {/* Global Toast Notification */}
        {actionNotice && (
          <div className="ops-toast-banner" role="alert">
            <span className="toast-icon">⚡</span>
            <span className="toast-text">{actionNotice}</span>
            <button className="toast-close" onClick={() => setActionNotice(null)}>×</button>
          </div>
        )}

        {/* Primary Dashboard Content */}
        <main className="dashboard-content" id="main-dashboard-view">
          {/* Header Row: "Logistics Overview" Heading */}
          <div className="dashboard-header-bar">
            <div className="header-titles">
              <div className="breadcrumbs">OPERATIONS CONTROL / {activeTab.toUpperCase()}</div>
              <h1 className="dashboard-title">Logistics Overview</h1>
              <p className="dashboard-caption">
                Unified freight coordination, multi-hub inventory, and predictive transit telemetry.
              </p>
            </div>

            <div className="header-meta-group">
              <div className="facility-status-pill">
                <span className="indicator-dot online" />
                <span>3 Warehouses Optimal</span>
              </div>
              <div className="facility-status-pill">
                <span className="indicator-dot in-transit" />
                <span>28 Active Drivers</span>
              </div>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <QuickActions onAction={handleQuickAction} />

          {/* Summary KPI Cards (Total Shipments, In Transit, Delivered, Delayed) */}
          <section className="metrics-grid" aria-label="Summary KPI Metrics">
            {summaryMetrics.map((metric) => (
              <MetricCard key={metric.id} metric={metric} />
            ))}
          </section>

          {/* Shipment Lifecycle Visualization (Created → Confirmed → Assigned → In Transit → Delivered) */}
          <section className="dashboard-section" aria-label="Shipment Lifecycle Pipeline">
            <PipelineStepper stages={pipelineStages} />
          </section>

          {/* AI / Optimization Insight Panel Placeholder (Uses Cyan #22D3EE) */}
          <section className="dashboard-section" aria-label="AI Optimization Insights">
            <AiInsightPanel 
              insights={aiOptimizationInsights} 
              onRunForecast={handleRunAiForecast}
            />
          </section>

          {/* Two-Column Middle Grid: Route Map & Warehouse Performance */}
          <div className="dashboard-split-grid">
            <section className="split-col-map" aria-label="Freight Corridor Map">
              <RouteMapPanel corridors={activeCorridors} />
            </section>
            <section className="split-col-wh" aria-label="Warehouse Facilities">
              <WarehouseCards warehouses={warehouses} />
            </section>
          </div>

          {/* Recent Shipments Table */}
          <section className="dashboard-section" aria-label="Recent Shipments">
            <RecentShipmentsTable shipments={recentShipments} />
          </section>
        </main>

        {/* Operational Footer */}
        <footer className="ops-footer">
          <div className="footer-left">
            <span><strong>FlowGrid</strong> • Deep Tech Blue Logistics Control Center</span>
            <span className="footer-separator">|</span>
            <span>Target Cloud: AWS (ECS + RDS + S3)</span>
          </div>
          <div className="footer-right">
            <span>FastAPI Backend: <code>http://127.0.0.1:8000</code></span>
            <span className="footer-separator">•</span>
            <span>Phase 1 Architecture Active</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
