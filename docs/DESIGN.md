# FlowGrid — UI/UX Design System & Frontend Specifications
**Deep Tech Blue: Intelligent Logistics Control Center**

*Document Version:* 1.0.0  
*Status:* Verified Implementation Baseline  
*Last Updated:* October 2026  
*Primary Technical Reference:* `frontend/src/index.css`, `frontend/src/App.jsx`, Reusable Components & Pages

---

## Table of Contents
1. [Product UI/UX Philosophy](#1-product-uiux-philosophy)
2. [Visual Identity & Design Direction](#2-visual-identity--design-direction)
3. [Verified Design Tokens & Styling System](#3-verified-design-tokens--styling-system)
4. [Application Layout & Navigation Structure](#4-application-layout--navigation-structure)
5. [Dashboard Architecture & Information Hierarchy](#5-dashboard-architecture--information-hierarchy)
6. [Page Inventory & Route Map](#6-page-inventory--route-map)
7. [Reusable Component Catalog](#7-reusable-component-catalog)
8. [Form, Table, Filter & Modal Patterns](#8-form-table-filter--modal-patterns)
9. [Feedback States (Loading, Error, Empty & Success)](#9-feedback-states-loading-error-empty--success)
10. [Responsive Behavior & Breakpoints](#10-responsive-behavior--breakpoints)
11. [Accessibility & Keyboard Navigation](#11-accessibility--keyboard-navigation)
12. [Geographic Data Visualization & Route Mapping](#12-geographic-data-visualization--route-mapping)
13. [Role-Specific Experiences (RBAC in UI)](#13-role-specific-experiences-rbac-in-ui)
14. [Shipment Risk & Exception-Management UX](#14-shipment-risk--exception-management-ux)
15. [AI Logistics Assistant UI Principles (Planned)](#15-ai-logistics-assistant-ui-principles-planned)
16. [Frontend Developer Quality Checklist](#16-frontend-developer-quality-checklist)

---

## 1. Product UI/UX Philosophy

FlowGrid is designed as a **mission-critical Logistics Control Center**—not a generic consumer web application or a rudimentary database CRUD admin tool.

### Core Philosophy Tenets:
1. **High Information Density with Cognitive Clarity**:
   Logistics operators process large volumes of shipments, inventory lines, and vehicle manifests. The UI prioritizes compact spacing, scannable typography, and high contrast over oversized empty margins.
2. **Immediate Exception Salience**:
   Normal operations should feel calm and cohesive (deep slate and navy), while anomalies, low-stock warnings, delivery failures, and high delay risks immediately demand visual attention using saturated alerts (amber, crimson, cyan).
3. **Action-Oriented Context**:
   Every visual card, table row, or map waypoint provides instant drill-down into operational details (such as the `ShipmentDetailDrawer`), allowing dispatchers to advance shipment states or review telemetry with minimal navigation friction.
4. **Data Honesty & Freshness Visibility**:
   The UI clearly communicates live backend connectivity, distinguishes verified heuristic scores from statistical predictions, and never masks missing data behind fabricated placeholder metrics.

---

## 2. Visual Identity & Design Direction

The FlowGrid visual identity is rooted in the **"Deep Tech Blue"** operational theme:
- **Base Environment**: Deep midnight slate (`#0F172A`) providing maximum visual comfort for dispatchers working extended shifts.
- **Card & Panel Layer**: Elevated dark slate panels (`#1E293B`) framed with subtle light borders (`rgba(255, 255, 255, 0.08)`).
- **Primary Operational Accent**: Electric blue (`#3B82F6`) for interactive controls, primary buttons, and navigational active states.
- **Intelligence & Optimization Accent**: Luminescent cyan (`#22D3EE`) reserved specifically for AI data pipeline indicators, route corridors, telemetry pings, and optimization insights.
- **Status Signal Lights**: Strict semantics for success (emerald green), warning/transit (amber), and exception/failure (crimson).

---

## 3. Verified Design Tokens & Styling System

All design tokens are defined as CSS Custom Properties in [`frontend/src/index.css`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/index.css#L6-L53):

### 3.1 Color Palette Tokens
| Token | Hex / Value | Semantic Role |
| :--- | :--- | :--- |
| `--bg-main` | `#0F172A` | Global background canvas (Dark Navy Slate) |
| `--bg-panel` | `#1E293B` | Content cards, data table wrappers, modal backgrounds |
| `--bg-panel-hover` | `#273549` | Interactive table row and card hover state |
| `--bg-panel-subtle`| `rgba(15, 23, 42, 0.6)` | Translucent input backgrounds and inner containers |
| `--primary-blue` | `#3B82F6` | Primary action buttons, active navigation links, progress nodes |
| `--primary-blue-hover` | `#2563EB` | Active button hover state |
| `--primary-blue-glow` | `rgba(59, 130, 246, 0.25)` | Focus ring glow, active tab highlights |
| `--ai-cyan` | `#22D3EE` | Telemetry indicators, route corridors, AI pipeline signals |
| `--ai-cyan-glow` | `rgba(34, 211, 238, 0.2)` | Glow effect around AI insight panels and route markers |
| `--text-main` | `#E2E8F0` | High-contrast body text, headings, primary table data |
| `--text-muted` | `#94A3B8` | Field labels, secondary descriptions, metadata dates |
| `--text-dim` | `#64748B` | Subtle captions, deactivated hints, table footer counters |
| `--success` | `#10B981` | Delivered status, positive throughput, healthy backend pill |
| `--warning` | `#F59E0B` | In-transit status, low-stock threshold warning, medium risk |
| `--error` | `#EF4444` | Delivery failed status, critical delay risk, validation error |
| `--border-subtle`| `rgba(255, 255, 255, 0.08)` | Standard hairline borders between panels and rows |
| `--border-medium`| `#334155` | Input borders, elevated divider lines, modal separators |

### 3.2 Layout & Sizing Tokens
- `--sidebar-width`: `240px` (Sticky left navigation)
- `--topbar-height`: `56px` (Sticky top bar)
- Border Radii:
  - Small elements (badges, buttons, inputs): `4px` to `6px`
  - Cards and panels: `8px` to `12px`
  - Modal dialogues: `12px`
- Elevation Shadows:
  - `--shadow-panel`: `0 4px 6px -1px rgba(0, 0, 0, 0.25), 0 2px 4px -2px rgba(0, 0, 0, 0.25)`
  - `--shadow-glow`: `0 0 15px rgba(59, 130, 246, 0.2)`

### 3.3 Typography
- **Primary Font**: `'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Monospace Font**: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` (Used for tracking numbers, coordinates, SKUs, and ISO timestamps)
- Font Scale:
  - Headings (Page Title): `1.5rem` (`24px`), font-weight 700
  - Subheadings (Card Headers): `1.125rem` (`18px`), font-weight 600
  - Section Headers: `0.875rem` (`14px`), font-weight 600, uppercase letter-spacing
  - Body Text: `0.875rem` (`14px`), font-weight 400
  - Captions & Badges: `0.75rem` (`12px`), font-weight 500

---

## 4. Application Layout & Navigation Structure

```text
+-----------------------------------------------------------------------------------------+
| [FG] FlowGrid    | Search Shipments...    | Live Health: [● Healthy] | User: Admin (▼)  |
+------------------+----------------------------------------------------------------------+
| 🚚 Dashboard     |                                                                      |
| 🏢 Warehouses    | PAGE CONTENT VIEWPORT                                                |
| 📦 Inventory     |                                                                      |
| 👤 Drivers       | (Responsive Grid / Flex Container)                                   |
| 🚛 Vehicles      |                                                                      |
| 📋 Shipments     |                                                                      |
| 🛣️ Routes        |                                                                      |
|                  |                                                                      |
| ⚙️ Logout        |                                                                      |
+------------------+----------------------------------------------------------------------+
```

1. **Sticky Left Sidebar (`Sidebar.jsx`)**:
   - Persists along the left margin (`width: 240px`).
   - Displays FlowGrid brand badge, active route navigation links with icons, user role indicator, and sign-out action.
   - Collapses into an off-canvas drawer on mobile screens (`max-width: 768px`).
2. **Top Navigation Bar (`TopNavbar.jsx`)**:
   - Fixed header (`height: 56px`).
   - Displays active page title, real-time backend health probe indicator (`healthy` / `disconnected`), notification center bell with unread badge count, and user profile pill with role badge.
3. **Main Viewport**:
   - Scrollable canvas (`background-color: var(--bg-main)`), structured with standardized page headers and grid panels.

---

## 5. Dashboard Architecture & Information Hierarchy

The primary dashboard route (`/` or `/dashboard`) is organized into an operational hierarchy:

1. **Top Metric Cards Row (`MetricCard.jsx`)**:
   Four key performance indicators offering instant network awareness:
   - *Total Active Shipments* (with active dispatch badge)
   - *Delivery Completion Rate* (% on-time delivery indicator)
   - *Network Fleet Utilization* (% vehicles currently `IN_USE`)
   - *Warehouse Capacity Saturation* (Facility storage footprint %)
2. **Interactive Pipeline Stepper (`PipelineStepper.jsx`)**:
   Horizontal lifecycle progression bar illustrating active shipments across the seven standard stages:
   `CREATED` $\to$ `CONFIRMED` $\to$ `ASSIGNED` $\to$ `PICKED_UP` $\to$ `IN_TRANSIT` $\to$ `OUT_FOR_DELIVERY` $\to$ `DELIVERED`. Clicking any stage filters the shipment table immediately.
3. **Primary Operations Grid**:
   - Left Column (60% width): `RecentShipmentsTable.jsx` showing latest dispatches, tracking numbers, destinations, weights, status badges, and action triggers.
   - Right Column (40% width):
     - `RouteMapPanel.jsx`: Interactive Leaflet map displaying active transit corridors.
     - `WarehouseCards.jsx`: Facility capacity meters and storage utilization bars.
     - `QuickActions.jsx`: Shortcuts for New Shipment, Stock Adjustment, and Route Creation.
     - `AiInsightPanel.jsx`: Heuristic delay-risk and dispatch optimization summaries.

---

## 6. Page Inventory & Route Map

| Client Route | Page Component | Primary Functional Responsibilities |
| :--- | :--- | :--- |
| `dashboard` | `AppContent` in `App.jsx` | Consolidated executive overview, metrics, stepper, recent dispatches, map. |
| `warehouses` | `WarehousesPage.jsx` | Facility grid/table, square footage meters, address details, New Facility modal. |
| `inventory` | `InventoryPage.jsx` | Stock balances across facilities, safety reorder thresholds, Stock Adjustment modal. |
| `drivers` | `DriversPage.jsx` | Driver roster, CDL licenses, availability status pills (`AVAILABLE`, `IN_TRANSIT`, etc.). |
| `vehicles` | `VehiclesPage.jsx` | Fleet registry, vehicle classifications, payload weight capacities, maintenance tags. |
| `shipments` | `ShipmentsPage.jsx` | Comprehensive dispatch list, status/tracking filters, pagination, New Shipment modal. |
| `routes` | `RoutesPage.jsx` | Transit corridors, origin-destination waypoints, assigned shipment manifests. |
| `login` | `LoginPage.jsx` | User authentication form, error banners, demo credentials reference. |
| `register` | `RegisterPage.jsx` | New user onboarding form, role selection, validation feedback. |

---

## 7. Reusable Component Catalog

- **`ShipmentDetailDrawer.jsx`**: The central operational workspace for any selected shipment. Contains 4 tabs:
  - *Overview*: Consignee address, driver/vehicle allocations, quick transition action buttons.
  - *Tracking*: Live WebSocket connectivity status, real-time checkpoint event stream, new checkpoint form.
  - *Audit History*: Chronological table of state machine transitions with user IDs and remarks.
  - *Delay Risk*: Explainable risk score (0–100), risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and itemized contributing factor pills.
- **`DataTable.jsx`**: Standardized table with sorting, search filtering, empty states, and pagination controls (`Previous`, page count, `Next`).
- **`StatusBadge.jsx`**: Color-coded pill reflecting shipment lifecycle status:
  - `CREATED`, `CONFIRMED`: Blue / Slate
  - `ASSIGNED`, `PICKED_UP`: Cyan / Blue
  - `IN_TRANSIT`, `OUT_FOR_DELIVERY`: Amber (warning glow)
  - `DELIVERED`: Emerald Green (success)
  - `FAILED`, `CANCELLED`, `RETURNED`: Crimson (error)
- **`RoleGate.jsx`**: Structural authorization component that renders children only if the logged-in user possesses an approved role (`allowed={['ADMIN', 'MANAGER']}`).
- **`RoleBadge.jsx`**: Visual indicator in user pills displaying `ADMIN` (purple/red), `MANAGER` (blue), `DRIVER` (cyan), or `VIEWER` (slate).
- **`ConfirmDialog.jsx`**: Modal dialogue requesting explicit confirmation before soft-deleting an asset or cancelling an active shipment.
- **`EmptyState.jsx`**: Clean placeholder graphic and prompt displayed when a search query or filter yields zero results.
- **`LoadingState.jsx`**: Pulsing skeleton loaders matching table/card dimensions to prevent layout shifts during API fetches.

---

## 8. Form, Table, Filter & Modal Patterns

### 8.1 Modal Dialogues
- Centered over an opaque backdrop (`rgba(0, 0, 0, 0.7)` with `backdrop-filter: blur(4px)`).
- Trapped focus with escape key (`Esc`) listener.
- Explicit `Save / Submit` and `Cancel` actions.
- Form inputs feature clear labels, placeholder hints, and inline Pydantic validation error parsing via `formatErrorMessage()`.

### 8.2 Data Tables
- Sticky table header (`position: sticky; top: 0`).
- Subtle alternating row backgrounds with hover highlighting (`--bg-panel-hover`).
- Right-aligned numeric columns (weights, quantities, prices).
- Left-aligned text columns (tracking numbers, destinations, names).

---

## 9. Feedback States (Loading, Error, Empty & Success)

1. **Loading State**:
   - Initial page loads render `<LoadingState message="Loading logistics data..." />`.
   - Action buttons display a spinning indicator and are disabled (`isSubmitting = true`) during network requests.
2. **Error State**:
   - Network or server exceptions trigger a persistent banner with a retry button or display an auto-dismissing toast (`error`).
   - Pydantic 422 validation arrays are formatted into human-readable bullet points.
3. **Empty State**:
   - Zero-data results render `<EmptyState title="No Shipments Found" description="..." />` with an action button to clear active filters.
4. **Success State**:
   - Write actions trigger positive green toasts (`"Shipment FG-98421 transitioned to IN_TRANSIT"`).

---

## 10. Responsive Behavior & Breakpoints

FlowGrid uses CSS media queries to ensure operational responsiveness across desktop and tablet displays:

| Breakpoint | Target Devices | Layout Adaptations |
| :--- | :--- | :--- |
| `> 1200px` | Large Desktop / Wall Displays | Full 2-column operations grid, expanded Leaflet map, all table columns visible. |
| `768px – 1199px` | Laptops & Tablets | 1-column stacked grid; secondary table columns (created date, volume) hidden. |
| `< 768px` | Mobile & Compact Tablets | Sidebar collapses to off-canvas drawer triggered by hamburger toggle; drawer spans 100% screen width. |

---

## 11. Accessibility & Keyboard Navigation

1. **Color Contrast**: All text tokens meet WCAG 2.1 AA standards (minimum 4.5:1 contrast against `--bg-panel` and `--bg-main`).
2. **Focus Visibility**: All interactive buttons, links, and inputs display an explicit focus outline (`2px solid var(--primary-blue)` with `--primary-blue-glow`).
3. **Keyboard Escaper**: Modals and the `ShipmentDetailDrawer` close immediately upon pressing the `Escape` key.
4. **Descriptive ARIA Labels**: Action icons (close buttons, view drawer triggers, refresh actions) carry explicit `aria-label` attributes.

---

## 12. Geographic Data Visualization & Route Mapping

Implemented in `ShipmentRouteMap.jsx` and `RouteMapPanel.jsx`:
- Built on **Leaflet 1.9.4** using OpenStreetMap tiles.
- Origin fulfillment centers are marked with custom high-contrast blue facility icons.
- Destination drop-off locations are marked with destination pins.
- Active transit corridors are drawn using SVG polylines in luminescent cyan (`#22D3EE`).
- Clicking any waypoint pin displays a Leaflet popup detailing the facility name, address, and current cargo weight.
- Fault tolerance: If coordinates are missing or invalid, the component renders a safe fallback without crashing.

---

## 13. Role-Specific Experiences (RBAC in UI)

The user interface adapts dynamically based on `user.role` from `AuthContext`:

| UI Area | Admin & Manager | Driver | Viewer |
| :--- | :--- | :--- | :--- |
| **New Shipment / Asset Buttons** | Visible & Active | Hidden / Disabled | Hidden / Disabled |
| **Status Advance Controls** | Enabled in Drawer | Disabled (View only) | Disabled (View only) |
| **Delete / Archive Actions** | Admin only | Hidden | Hidden |
| **Stock Adjustment Modal** | Accessible | Denied | Denied |
| **Analytics Dashboards** | Full Access | Accessible | Accessible |
| **Delay Risk Details** | Full Access | Accessible | Accessible |

---

## 14. Shipment Risk & Exception-Management UX

Located in the **Delay Risk Tab** of `ShipmentDetailDrawer`:
- **Risk Score Gauge**: Large, prominent numeric score (0–100) color-coded by severity:
  - `0–29`: Emerald Green (`LOW`)
  - `30–59`: Amber (`MEDIUM`)
  - `60–79`: Deep Orange (`HIGH`)
  - `80–100`: Bright Crimson (`CRITICAL`)
- **Assessment Transparency Badge**: Explicitly labeled *"Deterministic Heuristic Index — Not a Calibrated Probability"*.
- **Itemized Contributing Factors**: Scannable breakdown cards listing exactly what drove the score up:
  - ⚠️ *Unassigned Field Driver* (+25 pts)
  - ⚠️ *Unassigned Fleet Vehicle* (+20 pts)
  - ⚠️ *Vehicle Payload Near Limit (92%)* (+15 pts)
  - ⚠️ *Interstate Long-Haul Transit* (+10 pts)
  - ⚠️ *Origin Facility Congestion (95% Saturation)* (+10 pts)
- **Direct Mitigation Actions**: Dispatcher can click directly on the factor card to open the driver/vehicle assignment panel.

---

## 15. AI Logistics Assistant UI Principles (Planned)

For future conversational assistant features (Phase E):
1. **Docked Slide-Out Assistant**: An unobtrusive side drawer accessible from the top navbar.
2. **Strict Grounding & Citation**: Every assertion made by the assistant must link directly to an existing FlowGrid entity (e.g. `[Shipment #FG-98421]`).
3. **Zero Speculation Notice**: If milestone data or delivery dates are unrecorded, the assistant must state *"No actual pickup timestamp recorded in database"* rather than guessing.
4. **Read-Only Safety**: The assistant answers inquiries and generates draft summaries; it cannot unilaterally trigger database modifications without user confirmation.

---

## 16. Frontend Developer Quality Checklist

Before marking any UI feature or page complete, verify:
- [ ] Uses existing CSS variables in `index.css` (no ad-hoc hardcoded colors or arbitrary margins).
- [ ] All interactive buttons and inputs have visible focus states.
- [ ] Network errors are routed through `formatErrorMessage()`.
- [ ] Table views handle empty search results using `<EmptyState />`.
- [ ] Privileged action buttons are wrapped in `<RoleGate>` or appropriately disabled.
- [ ] The component does not crash when coordinates, weights, or timestamps are `null`.
- [ ] Form submission buttons disable during network requests to prevent duplicate submissions.
- [ ] All text conforms to WCAG AA contrast against the dark background.
- [ ] Responsive layout verified at desktop (1400px), tablet (900px), and mobile (600px).
- [ ] `npm test` executes cleanly with zero failing tests.
