import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider, useToast } from './context/ToastContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import ErrorBoundary from './components/ErrorBoundary';
import HeroBanner from './components/HeroBanner';
import ReferenceKpiCards from './components/ReferenceKpiCards';
import LiveShipmentFlowMap from './components/LiveShipmentFlowMap';
import ReferenceRecentShipments from './components/ReferenceRecentShipments';
import FeatureShortcutCards from './components/FeatureShortcutCards';
import RightOperationalPanel from './components/RightOperationalPanel';
import ModelDisclaimerBar from './components/ModelDisclaimerBar';
import DelayPredictionModal from './components/DelayPredictionModal';
import ShipmentDetailDrawer from './components/ShipmentDetailDrawer';
import OperationalRecommendationsPanel from './components/OperationalRecommendationsPanel';
import NewShipmentModal from './components/NewShipmentModal';
import LogisticsAssistantModal from './components/LogisticsAssistantModal';
import { useDashboardData } from './hooks/useDashboardData';
import authApi from './api/auth';
import { exportShipmentsToCSV } from './services/exportService';

import WarehousesPage from './pages/WarehousesPage';
import InventoryPage from './pages/InventoryPage';
import DriversPage from './pages/DriversPage';
import VehiclesPage from './pages/VehiclesPage';
import ShipmentsPage from './pages/ShipmentsPage';
import RoutesPage from './pages/RoutesPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';
import RescueCenterPage from './pages/RescueCenterPage';
import DisruptionSimulatorPage from './pages/DisruptionSimulatorPage';

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
  if (path.includes('analytics')) return 'analytics';
  if (path.includes('settings')) return 'settings';
  if (path.includes('rescue')) return 'rescue';
  if (path.includes('simulator')) return 'simulator';
  if (path.includes('recommendations')) return 'recommendations';
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
    case 'analytics': return 'Fleet Analytics & Delay Risk Control Tower';
    case 'settings': return 'Node Configuration & Access Governance';
    case 'rescue': return 'Shipment Rescue Center';
    case 'simulator': return 'What-If Disruption Simulator';
    case 'recommendations': return 'Operational Recommendations';
    case 'inventory': return 'Inventory Management';
    case 'drivers': return 'Fleet Drivers';
    case 'vehicles': return 'Fleet Vehicles';
    case 'shipments': return 'Shipment Operations';
    case 'routes': return 'Transit Corridors';
    case 'analytics': return 'Fleet Analytics & Delay Risk Control Tower';
    case 'settings': return 'Node Configuration & Access Governance';
    case 'rescue': return 'Shipment Rescue Center';
    case 'simulator': return 'What-If Disruption Simulator';
    case 'dashboard':
    default:
      return 'Logistics Overview';
  }
}

function AppContent() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const { toast } = useToast();
  const [route, setRoute] = useState(getInitialRoute);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);
  const [isShipmentModalOpen, setIsShipmentModalOpen] = useState(false);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [isPredictorModalOpen, setIsPredictorModalOpen] = useState(false);
  const [selectedShipment, setSelectedShipment] = useState(null);

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
    delayRiskSummary,
    delayRiskShipments,
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
    if (actionName === 'Open Rescue Center') {
      navigate('rescue');
      return;
    }
    if (actionName === 'Open Assistant') {
      setIsAssistantOpen(true);
      return;
    }
    if (actionName === 'Dispatch Route') {
      navigate('routes');
      return;
    }
    if (actionName === 'Audit Fleet Delay Risk') {
      refetchDashboardData();
      toast.info('Recalculating deterministic delay risk across active shipments...');
      return;
    }
    if (actionName === 'Export Manifest (CSV)') {
      try {
        const rawList = recentShipments.map((s) => s.raw).filter(Boolean);
        if (rawList.length > 0) {
          const count = exportShipmentsToCSV(rawList);
          toast.success(`Exported ${count} active line-haul shipments to CSV`);
        } else {
          toast.info('No active shipments recorded to export.');
        }
      } catch (err) {
        toast.error(err.message || 'Failed to export manifest');
      }
      return;
    }
    showNotification(`Operational Action: "${actionName}"`);
  };

  const handleRunAiAudit = () => {
    refetchDashboardData();
    toast.info('Auditing fleet-wide delay risk scores and staging bottlenecks...');
  };

  const handleShipmentCreated = (newShipment) => {
    showNotification(`✓ Shipment ${newShipment.tracking_number} created and dispatched successfully!`);
    refetchDashboardData();
  };

  const handleGlobalSearch = (query) => {
    navigate('shipments');
    showNotification(`Filtering manifests for query: "${query}"`);
  };

  const handleMetricCardClick = (metricId) => {
    switch (metricId) {
      case 'total-shipments':
      case 'in-transit':
      case 'delivered':
      case 'delayed':
        navigate('shipments');
        break;
      default:
        navigate('shipments');
    }
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
          onOpenAssistant={() => setIsAssistantOpen(true)}
          backendHealth={backendHealth}
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
            onSearch={handleGlobalSearch}
            onOpenAssistant={() => setIsAssistantOpen(true)}
          />

          {/* Global Toast Notification */}
          {actionNotice && (
            <div className="ops-toast-banner" role="alert">
              <span className="toast-icon">⚡</span>
              <span className="toast-text">{actionNotice}</span>
              <button className="toast-close" onClick={() => setActionNotice(null)}>×</button>
            </div>
          )}

          {/* Role Status Notice for VIEWER */}
          {user?.role === 'VIEWER' && (
            <div
              style={{
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderBottom: '1px solid rgba(59, 130, 246, 0.25)',
                padding: '6px 24px',
                fontSize: '0.78rem',
                color: '#93C5FD',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>ℹ️</span>
              <span>
                <strong>Viewer Session (Read-Only)</strong>: Live operational telemetry and tracking data are visible. Creation, status transitions, and resource allocation require MANAGER or ADMIN privileges.
              </span>
            </div>
          )}

          {/* Primary View Content protected by ErrorBoundary */}
          <ErrorBoundary onReset={refetchDashboardData}>
            <main className="dashboard-content" id="main-dashboard-view">
            {route === 'warehouses' && <WarehousesPage />}
            {route === 'inventory' && <InventoryPage />}
            {route === 'drivers' && <DriversPage />}
            {route === 'vehicles' && <VehiclesPage />}
            {route === 'shipments' && <ShipmentsPage />}
            {route === 'routes' && <RoutesPage />}
            {route === 'analytics' && <AnalyticsPage onNavigate={navigate} />}
            {route === 'settings' && <SettingsPage />}
            {route === 'rescue' && <RescueCenterPage onNavigate={navigate} />}
            {route === 'recommendations' && (
              <div className="recommendations-page-view" style={{ padding: '20px 24px' }}>
                <OperationalRecommendationsPanel
                  shipments={recentShipments.map((s) => s.raw || s)}
                  warehouses={warehouses}
                  drivers={overview?.drivers || []}
                  vehicles={overview?.vehicles || []}
                  onApplied={refetchDashboardData}
                />
              </div>
            )}

            {/* Default Reference Summary Dashboard Route */}
            {(route === 'dashboard' || !['warehouses', 'inventory', 'drivers', 'vehicles', 'shipments', 'routes', 'analytics', 'settings', 'rescue', 'simulator', 'recommendations'].includes(route)) && (
              <div className="ref-dashboard-container" id="ref-dashboard-container">
                {/* Hero Banner matching Reference */}
                <HeroBanner />

                {/* 4 Consistent KPI Cards Directly Beneath Hero */}
                <ReferenceKpiCards
                  overview={overview}
                  delayRiskSummary={delayRiskSummary}
                  onNavigate={navigate}
                />

                {/* Main Workspace Split Grid */}
                <div className="ref-dashboard-split-grid">
                  <div className="ref-workspace-left">
                    {/* Upper Row: Live Shipment Flow Map & Recent Shipments Table */}
                    <div className="ref-middle-split">
                      <LiveShipmentFlowMap onNavigate={navigate} />
                      <ReferenceRecentShipments
                        shipments={recentShipments}
                        onNavigate={navigate}
                        onSelectShipment={(s) => setSelectedShipment(s)}
                      />
                    </div>

                    {/* Lower Row: 4 Feature Shortcut Cards */}
                    <FeatureShortcutCards onNavigate={navigate} />
                  </div>

                  {/* Right-Side Operational Column */}
                  <RightOperationalPanel
                    onNavigate={navigate}
                    onOpenPredictor={() => setIsPredictorModalOpen(true)}
                  />
                </div>

                {/* Bottom Transparent ML Model Disclaimer Bar */}
                <ModelDisclaimerBar />
              </div>
            )}
          </main>
          </ErrorBoundary>

          {/* Operational Footer */}
          <footer className="ops-footer">
            <div className="footer-left">
              <span><strong>FlowGrid</strong> • Logistics Control Center</span>
              <span className="footer-separator">|</span>
              <span>Authenticated Role: <strong>{user?.role || 'ANONYMOUS'}</strong></span>
            </div>
            <div className="footer-right">
              <span>FastAPI Backend: <code>http://127.0.0.1:8000</code></span>
              <span className="footer-separator">•</span>
              <span>Operational Control Tower</span>
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

      {/* Grounded Logistics Assistant Modal */}
      <LogisticsAssistantModal
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        onNavigate={navigate}
      />

      {/* ML Corridor Delay Predictor Modal */}
      <DelayPredictionModal
        isOpen={isPredictorModalOpen}
        onClose={() => setIsPredictorModalOpen(false)}
      />

      {/* Shipment Detail Drawer */}
      <ShipmentDetailDrawer
        shipment={selectedShipment}
        isOpen={Boolean(selectedShipment)}
        onClose={() => setSelectedShipment(null)}
      />
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </ToastProvider>
    </AuthProvider>
  );
}
