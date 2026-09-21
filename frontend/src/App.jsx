import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import MetricCard from './components/MetricCard';
import PipelineStepper from './components/PipelineStepper';
import WarehouseCards from './components/WarehouseCards';
import RecentShipmentsTable from './components/RecentShipmentsTable';
import RouteMapPanel from './components/RouteMapPanel';
import QuickActions from './components/QuickActions';
import AiInsightPanel from './components/AiInsightPanel';
import authApi from './api/auth';

import {
  summaryMetrics,
  pipelineStages,
  warehouses,
  recentShipments,
  activeCorridors,
  aiOptimizationInsights
} from './data/mockLogisticsData';

/**
 * Determine initial route based on URL path.
 */
function getInitialRoute() {
  if (typeof window === 'undefined') return 'dashboard';
  const path = window.location.pathname.toLowerCase();
  if (path.includes('login')) return 'login';
  if (path.includes('register')) return 'register';
  return 'dashboard';
}

function AppContent() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [route, setRoute] = useState(getInitialRoute);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  // Sync route changes with browser address bar
  const navigate = useCallback((targetRoute) => {
    setRoute(targetRoute);
    if (typeof window !== 'undefined') {
      const targetPath = targetRoute === 'dashboard' ? '/' : `/${targetRoute}`;
      if (window.location.pathname !== targetPath) {
        window.history.pushState({}, '', targetPath);
      }
    }
  }, []);

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      setRoute(getInitialRoute());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Automatic routing based on authentication state
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated && (route !== 'login' && route !== 'register')) {
        navigate('login');
      } else if (isAuthenticated && (route === 'login' || route === 'register')) {
        navigate('dashboard');
      }
    }
  }, [isAuthenticated, isLoading, route, navigate]);

  const showNotification = useCallback((msg) => {
    setActionNotice(msg);
    setTimeout(() => {
      setActionNotice((current) => (current === msg ? null : current));
    }, 4500);
  }, []);

  // Ping backend FastAPI /health endpoint
  const checkBackendHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const data = await authApi.checkHealth();
      setBackendHealth({ ok: true, data });
      showNotification(`✓ FastAPI Backend Online (${data.application})`);
    } catch (err) {
      setBackendHealth({
        ok: false,
        error: err.message || 'Offline'
      });

      showNotification('FastAPI Backend is not reachable. Start with: uvicorn app.main:app --reload in backend/');
    } finally {
      setIsCheckingHealth(false);
    }
  }, [showNotification]);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);


  const handleQuickAction = (actionName) => {
    showNotification(`Operational Action Triggered: "${actionName}"`);
  };

  const handleRunAiForecast = () => {
    if (user?.role === 'VIEWER' || user?.role === 'DRIVER') {
      showNotification(`Access Restricted: Dynamic AI forecasting requires MANAGER or ADMIN role. (Current: ${user?.role})`);
      return;
    }
    showNotification('AI Route Optimization Algorithm triggered: Analyzing 42 active freight legs with scikit-learn pipeline...');
  };

  // 1. Unauthenticated Login Route
  if (route === 'login' && !isAuthenticated) {
    return <LoginPage onNavigate={navigate} />;
  }

  // 2. Unauthenticated Register Route
  if (route === 'register' && !isAuthenticated) {
    return <RegisterPage onNavigate={navigate} />;
  }

  // 3. Authenticated Dashboard Route (Protected)
  return (
    <ProtectedRoute onNavigate={navigate}>
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

            {/* Quick Action Buttons with Role Gating */}
            <QuickActions onAction={handleQuickAction} />

            {/* Summary KPI Cards (Total Shipments, In Transit, Delivered, Delayed) */}
            <section className="metrics-grid" aria-label="Summary KPI Metrics">
              {summaryMetrics.map((metric) => (
                <MetricCard key={metric.id} metric={metric} />
              ))}
            </section>

            {/* Shipment Lifecycle Visualization */}
            <section className="dashboard-section" aria-label="Shipment Lifecycle Pipeline">
              <PipelineStepper stages={pipelineStages} />
            </section>

            {/* AI / Optimization Insight Panel */}
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
              <span>Authenticated Role: <strong>{user?.role || 'ANONYMOUS'}</strong></span>
            </div>
            <div className="footer-right">
              <span>FastAPI Backend: <code>http://127.0.0.1:8000</code></span>
              <span className="footer-separator">•</span>
              <span>Phase 14 Active</span>
            </div>
          </footer>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
