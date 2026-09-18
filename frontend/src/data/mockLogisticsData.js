// Realistic logistics mock data for FlowGrid "Deep Tech Blue" Control Center

export const summaryMetrics = [
  {
    id: 'total-shipments',
    label: 'Total Shipments',
    value: '1,428',
    change: '+12.4%',
    changeType: 'positive',
    subtext: 'vs. previous 7 days',
    icon: 'Package',
    accentColor: '#3B82F6', // Primary Blue
  },
  {
    id: 'in-transit',
    label: 'In Transit',
    value: '384',
    change: '28 active routes',
    changeType: 'neutral',
    subtext: '94.2% on schedule',
    icon: 'Truck',
    accentColor: '#3B82F6', // Primary Blue
  },
  {
    id: 'delivered',
    label: 'Delivered (Today)',
    value: '892',
    change: '+8.1%',
    changeType: 'positive',
    subtext: 'Avg transit: 18.4 hrs',
    icon: 'CheckCircle',
    accentColor: '#10B981', // Success Green
  },
  {
    id: 'delayed',
    label: 'Delayed / Exceptions',
    value: '14',
    change: '3 weather alerts',
    changeType: 'warning',
    subtext: 'Requires dispatcher review',
    icon: 'AlertTriangle',
    accentColor: '#EF4444', // Error/Delay Red
  },
];

// Shipment lifecycle: Created → Confirmed → Assigned → In Transit → Delivered
export const pipelineStages = [
  {
    id: 'created',
    name: 'Created',
    count: 142,
    percent: '10%',
    status: 'pending',
    description: 'Order manifest created; awaiting inventory reservation',
  },
  {
    id: 'confirmed',
    name: 'Confirmed',
    count: 186,
    percent: '13%',
    status: 'confirmed',
    description: 'Stock verified and locked at origin warehouse hub',
  },
  {
    id: 'assigned',
    name: 'Assigned',
    count: 218,
    percent: '15%',
    status: 'scheduled',
    description: 'Driver and vehicle allocated; staging dock scheduled',
  },
  {
    id: 'in_transit',
    name: 'In Transit',
    count: 384,
    percent: '27%',
    status: 'active',
    description: 'Cargo moving along monitored freight corridor',
  },
  {
    id: 'delivered',
    name: 'Delivered',
    count: 684,
    percent: '48%',
    status: 'completed',
    description: 'Consignee proof-of-delivery signed; completed',
  },
];

export const warehouses = [
  {
    id: 'WH-CHI-01',
    name: 'Midwest Regional Hub (ORD-01)',
    location: 'Chicago, IL',
    capacityUsed: 84,
    totalSqFt: '250,000 sq ft',
    activeBays: '18 / 20 In Use',
    inboundToday: 42,
    outboundToday: 58,
    status: 'Optimal',
  },
  {
    id: 'WH-NJ-02',
    name: 'East Coast Gateway (EWR-02)',
    location: 'Newark, NJ',
    capacityUsed: 92,
    totalSqFt: '310,000 sq ft',
    activeBays: '24 / 24 In Use',
    inboundToday: 65,
    outboundToday: 71,
    status: 'High Load',
  },
  {
    id: 'WH-TX-04',
    name: 'Southwest Logistics Center (DFW-04)',
    location: 'Dallas, TX',
    capacityUsed: 68,
    totalSqFt: '180,000 sq ft',
    activeBays: '12 / 16 In Use',
    inboundToday: 29,
    outboundToday: 34,
    status: 'Optimal',
  },
];

export const recentShipments = [
  {
    trackingNumber: 'FG-98421-US',
    origin: 'WH-CHI-01 (Chicago)',
    destination: 'DC-04 (Detroit, MI)',
    carrier: 'Marcus Vance (Unit #402)',
    itemsCount: 120,
    weight: '4,250 kg',
    status: 'IN_TRANSIT',
    statusLabel: 'In Transit',
    eta: 'Today, 16:45 EST',
    priority: 'Standard',
  },
  {
    trackingNumber: 'FG-98422-US',
    origin: 'WH-NJ-02 (Newark)',
    destination: 'Boston Metro (MA)',
    carrier: 'Elena Rostova (Unit #118)',
    itemsCount: 48,
    weight: '1,120 kg',
    status: 'IN_TRANSIT',
    statusLabel: 'In Transit',
    eta: 'Today, 14:15 EST',
    priority: 'Express',
  },
  {
    trackingNumber: 'FG-98423-US',
    origin: 'WH-TX-04 (Dallas)',
    destination: 'Austin Retail Hub (TX)',
    carrier: 'Jerome Washington (Unit #305)',
    itemsCount: 310,
    weight: '7,800 kg',
    status: 'DELIVERED',
    statusLabel: 'Delivered',
    eta: 'Delivered at 11:20 CST',
    priority: 'Standard',
  },
  {
    trackingNumber: 'FG-98424-US',
    origin: 'WH-CHI-01 (Chicago)',
    destination: 'Minneapolis Depot (MN)',
    carrier: 'Dmitri Cruz (Unit #214)',
    itemsCount: 85,
    weight: '3,400 kg',
    status: 'DELAYED',
    statusLabel: 'Weather Hold',
    eta: 'Delayed (+2.5 hrs)',
    priority: 'Critical',
  },
  {
    trackingNumber: 'FG-98425-US',
    origin: 'WH-NJ-02 (Newark)',
    destination: 'Philadelphia Crossdock (PA)',
    carrier: 'Sarah Lin (Unit #109)',
    itemsCount: 64,
    weight: '1,850 kg',
    status: 'ASSIGNED',
    statusLabel: 'Dock Loading',
    eta: 'Departure 15:00 EST',
    priority: 'Standard',
  },
];

export const activeCorridors = [
  {
    id: 'COR-01',
    name: 'I-80 Corridor: Chicago → Cleveland → Newark',
    trafficCondition: 'Clear',
    shipmentsActive: 18,
    avgSpeed: '62 mph',
    statusColor: '#10B981', // Green
    statusType: 'normal',
  },
  {
    id: 'COR-02',
    name: 'I-95 North: Newark → Hartford → Boston',
    trafficCondition: 'Weather Congestion',
    shipmentsActive: 14,
    avgSpeed: '48 mph',
    statusColor: '#F59E0B', // Amber warning
    statusType: 'congested',
  },
  {
    id: 'COR-03',
    name: 'I-35 Corridor: Dallas → Waco → Austin',
    trafficCondition: 'Clear',
    shipmentsActive: 9,
    avgSpeed: '65 mph',
    statusColor: '#10B981', // Green
    statusType: 'normal',
  },
];

export const aiOptimizationInsights = [
  {
    id: 'ai-1',
    category: 'PREDICTIVE ETA',
    metric: '96.4%',
    title: 'Model Arrival Precision',
    description: 'scikit-learn gradient boosting regression trained on 42k historical legs.',
    status: 'Active Pipeline',
  },
  {
    id: 'ai-2',
    category: 'ROUTE EFFICIENCY',
    metric: '+18.2%',
    title: 'Dynamic Mileage Optimization',
    description: 'Algorithmic waypoint sequencing avoiding metro I-95 congestion nodes.',
    status: 'Simulated Gain',
  },
  {
    id: 'ai-3',
    category: 'ANOMALY DETECTION',
    metric: '2 Detected',
    title: 'Pre-emptive Delay Forecasts',
    description: 'Winter weather pattern along northeast corridor may impact BOS-bound freight.',
    status: 'High Confidence',
  },
];
