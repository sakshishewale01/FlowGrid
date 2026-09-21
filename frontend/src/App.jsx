import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
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
import NewShipmentModal from './components/NewShipmentModal';
import { useDashboardData } from './hooks/useDashboardData';
import authApi from './api/auth';

import WarehousesPage from './pages/WarehousesPage';
import InventoryPage from './pages/InventoryPage';
import DriversPage from './pages/DriversPage';
import VehiclesPage from './pages/VehiclesPage';
import ShipmentsPage from './pages/ShipmentsPage';
import RoutesPage from './pages/RoutesPage';

import { aiOptimizationInsights } from './data/mockLogisticsData';

/**
 * Determine initial route based on URL path.
 */
function getInitialRoute() {
  if (typeof window === 'undefined') return 'dashboard';
  const path = window.location.pathname.toLowerCase();
  if (path.includes('login')) return 'login';
  if (path.includes('register')) return 'register';
  if (path.includes('warehouses')) return 'warehouses';
  if (path.includes('inventory')) return 'inventory';
  if (path.includes('drivers')) return 'drivers';
  if (path.includes('vehicles')) return 'vehicles';
  if (path.includes('shipments')) return 'shipments';
  if (path.includes('routes')) return 'routes';
  return 'dashboard';
}

function getPageTitle(currentRoute) {
  switch (currentRoute) {
    case 'warehouses': return 'Warehouse Facilities';
    case 'inventory': return 'Inventory Management';
    case 'drivers': return 'Fleet Drivers';
    case 'vehicles': return 'Fleet Vehicles';
    case 'shipments': return 'Shipment Operations';
    case 'routes': return 'Transit Corridors';
    case 'dashboard':
    default:
      return 'Logistics Overview';
  }
}

function AppContent() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [route, setRoute] = useState(getInitialRoute);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);
  const [isShipmentModalOpen, setIsShipmentModalOpen] = useState(false);

  // Live Dashboard Data Hook
  const {
    loading: isDataLoading,
    refreshing: isDataRefreshing,
    error: dashboardError,
    overview,
    metrics,
    pipelineStages,
    warehouses,
    recentShipments,
    corridors,
    inventorySummary,
    refetch: refetchDashboardData,
  } = useDashboardData();

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
    if (actionName === 'Create New Shipment') {
      setIsShipmentModalOpen(true);
      return;
    }
    showNotification(`Operational Action Triggered: "${actionName}"`);
  };

  const handleRunAiForecast = () => {
    if (user?.role === 'VIEWER' || user?.role === 'DRIVER') {
      showNotification(`Access Restricted: Dynamic AI forecasting requires MANAGER or ADMIN role. (Current: ${user?.role})`);
      return;
    }
    showNotification('AI Route Optimization Algorithm triggered: Analyzing active freight corridors...');
  };

  const handleShipmentCreated = (newShipment) => {
    showNotification(`✓ Shipment ${newShipment.tracking_number} created and dispatched successfully!`);
    refetchDashboardData();
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
          activeTab={route}
          setActiveTab={(tab) => navigate(tab)}
          isOpen={isSidebarOpen}
          setIsOpen={setIsSidebarOpen}
          onNavigate={navigate}
        />

        {/* Main Workspace */}
        <div className="main-viewport">
          {/* Top Navigation Bar with Title, Notifications, and Profile */}
          <TopNavbar
            onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            backendHealth={backendHealth}
            isCheckingHealth={isCheckingHealth}
            onCheckHealth={checkBackendHealth}
            pageTitle={getPageTitle(route)}
          />

          {/* Global Toast Notification */}
          {actionNotice && (
            <div className="ops-toast-banner" role="alert">
              <span className="toast-icon">⚡</span>
              <span className="toast-text">{actionNotice}</span>
              <button className="toast-close" onClick={() => setActionNotice(null)}>×</button>
            </div>
          )}

          {/* Primary View Content */}
          <main className="dashboard-content" id="main-dashboard-view">
            {route === 'warehouses' && <WarehousesPage />}
            {route === 'inventory' && <InventoryPage />}
            {route === 'drivers' && <DriversPage />}
            {route === 'vehicles' && <VehiclesPage />}
            {route === 'shipments' && <ShipmentsPage />}
            {route === 'routes' && <RoutesPage />}

            {/* Default Summary Dashboard Route */}
            {(route === 'dashboard' || !['warehouses', 'inventory', 'drivers', 'vehicles', 'shipments', 'routes'].includes(route)) && (
              <>
                {/* Header Row: "Logistics Overview" Heading with Live Telematics Status */}
                <div className="dashboard-header-bar">
                  <div className="header-titles">
                    <div className="breadcrumbs">OPERATIONS CONTROL / OVERVIEW</div>
                    <h1 className="dashboard-title">Logistics Overview</h1>
                    <p className="dashboard-caption">
                      Unified freight coordination, multi-hub inventory, and live API telemetry.
                    </p>
                  </div>

                  <div className="header-meta-group">
                    <div className="facility-status-pill">
                      <span className="indicator-dot online" />
                      <span>{overview ? `${overview.total_warehouses} Warehouses Registered` : '3 Warehouses Optimal'}</span>
                    </div>
                    <div className="facility-status-pill">
                      <span className="indicator-dot in-transit" />
                      <span>{overview ? `${overview.total_drivers} Fleet Drivers` : 'Active Drivers'}</span>
                    </div>
                    <button
                      className="btn-refresh-telematics"
                      onClick={refetchDashboardData}
                      disabled={isDataRefreshing || isDataLoading}
                      title="Synchronize real-time operational data from backend"
                    >
                      <svg
                        className={isDataRefreshing ? 'spin-anim' : ''}
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <polyline points="23 4 23 10 17 10" />
                        <polyline points="1 20 1 14 7 14" />
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                      </svg>
                      <span>{isDataRefreshing ? 'Syncing...' : 'Sync Telematics'}</span>
                    </button>
                  </div>
                </div>

                {/* Dashboard Error Notice (If API Fails) */}
                {dashboardError && (
                  <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
                    <div className="auth-alert-content">
                      <span className="auth-alert-title">API Synchronization Notice</span>
                      <span className="auth-alert-text">{dashboardError}</span>
                    </div>
                    <button
                      type="button"
                      className="btn-action outline"
                      style={{ padding: '4px 12px', fontSize: '0.78rem' }}
                      onClick={refetchDashboardData}
                    >
                      Retry Connection
                    </button>
                  </div>
                )}

                {/* Quick Action Buttons with Role Gating */}
                <QuickActions onAction={handleQuickAction} />

                {/* Summary KPI Cards (Connected to live backend overview) */}
                <section className="metrics-grid" aria-label="Summary KPI Metrics">
                  {metrics.length > 0 ? (
                    metrics.map((metric) => (
                      <MetricCard key={metric.id} metric={metric} loading={isDataLoading} />
                    ))
                  ) : (
                    [1, 2, 3, 4].map((id) => (
                      <MetricCard key={id} metric={null} loading={true} />
                    ))
                  )}
                </section>

                {/* Shipment Lifecycle Visualization (Connected to live shipment state counts) */}
                <section className="dashboard-section" aria-label="Shipment Lifecycle Pipeline">
                  <PipelineStepper stages={pipelineStages} loading={isDataLoading} />
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
                    <RouteMapPanel corridors={corridors} loading={isDataLoading} />
                  </section>
                  <section className="split-col-wh" aria-label="Warehouse Facilities">
                    <WarehouseCards 
                      warehouses={warehouses} 
                      loading={isDataLoading} 
                      inventorySummary={inventorySummary}
                    />
                  </section>
                </div>

                {/* Recent Shipments Table (Connected to live shipments API) */}
                <section className="dashboard-section" aria-label="Recent Shipments">
                  <RecentShipmentsTable 
                    shipments={recentShipments} 
                    loading={isDataLoading} 
                  />
                </section>
              </>
            )}
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
              <span>Phase 17 End-to-End Workflow & UX Polish</span>
            </div>
          </footer>
        </div>
      </div>

      {/* New Shipment Dispatch Modal */}
      <NewShipmentModal
        isOpen={isShipmentModalOpen}
        onClose={() => setIsShipmentModalOpen(false)}
        onCreated={handleShipmentCreated}
      />
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </AuthProvider>
  );
}
