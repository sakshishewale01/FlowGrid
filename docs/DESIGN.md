# FlowGrid — UI/UX Design System Specification

> **Intelligent Logistics Control Tower: Dual-Theme Operational Design System**  
> *Status:* Production Baseline • *Updated:* October 2026 • *Location:* `docs/DESIGN.md`

---

## 1. Visual Identity & Design Principles

FlowGrid is designed as a mission-critical **Logistics Operations Control Tower**. The interface prioritizes high information density, cognitive clarity, and immediate exception salience without visual clutter.

### Core Principles
- **Clarity Over Clutter**: Compact spacing, scannable data hierarchies, and high contrast for rapid decision-making.
- **Immediate Exception Salience**: Normal operations remain calm and cohesive; anomalies, capacity bottlenecks, and high delay risks immediately stand out using saturated alerts (crimson `#EF4444`, amber `#F59E0B`, cyan `#22D3EE`).
- **Data Honesty**: Explicitly displays telematics connection states, rule rationales, and ML confidence levels without fabricating placeholder metrics.
- **Seamless Dual-Theme Support**: Instant toggle between low-fatigue dark mode and high-contrast daylight mode with zero-latency persistence.

---

## 2. Color Palette & Design Tokens

Design tokens are declared as CSS Custom Properties in [`frontend/src/index.css`](file:///c:/Users/saksh/OneDrive/Pictures/Documents/FlowGrid/frontend/src/index.css):

| Token Category | Token Variable | Dark Mode (Default) | Light Mode (`[data-theme="light"]`) | Semantic Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Canvas** | `--bg-main` | `#0B1220` (Midnight Navy) | `#F1F5F9` (Slate Canvas) | Application root viewport |
| **Surfaces** | `--bg-card` / `--bg-panel` | `#111D32` (Deep Tech Blue) | `#FFFFFF` (Pure White) | KPI cards, data tables, modal dialogs |
| **Elevated** | `--bg-elevated` | `#1E293B` (Elevated Slate) | `#F8FAFC` (Light Elevated) | Hover rows, popups, inner wrappers |
| **Primary Accent** | `--primary-blue` | `#3B82F6` (Electric Blue) | `#2563EB` (Royal Blue) | Primary dispatch actions, active tabs |
| **AI & Telematics**| `--ai-cyan` | `#22D3EE` (Luminescent Cyan) | `#0284C7` (Cyan Accent) | Transit corridors, assistant launcher |
| **Primary Text** | `--text-main` | `#F8FAFC` (High-Contrast White)| `#0F172A` (Deep Slate) | Headings, key values, active data |
| **Secondary Text**| `--text-muted` | `#94A3B8` (Slate Grey) | `#64748B` (Muted Slate) | Field labels, captions, metadata |
| **Success** | `--success` | `#10B981` (Emerald Green) | `#059669` (Dark Emerald) | Delivered status, online telemetry |
| **Warning / Risk**| `--warning` | `#F59E0B` (Amber) | `#D97706` (Deep Amber) | In-transit status, moderate delay risk |
| **Exception** | `--critical` / `--error` | `#F43F5E` (Rose Crimson) | `#DC2626` (Bright Red) | Delivery failures, severe bottlenecks |
| **Hairline Borders**| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | `rgba(0, 0, 0, 0.09)` | Card separators, table cell borders |

---

## 3. Layout Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│ TOP NAVBAR (Height: 60px, Sticky)                                      │
│ [☰] FlowGrid / Overview   [🔍 Global Search...]   [● API] [🤖] [🔔] [☀️/🌙] [User] │
├──────────────┬─────────────────────────────────────────────────────────┤
│ SIDEBAR      │ MAIN WORKSPACE VIEWPORT                                 │
│ (250px)      │                                                         │
│ • Dashboard  │  [HERO BANNER: Fleet Telematics & Live Operating Corridor]│
│ • Shipments  │  ┌──────────┬──────────┬──────────┬──────────┐           │
│ • Rescue Ctr │  │ KPI 1    │ KPI 2    │ KPI 3    │ KPI 4    │           │
│ • Simulator  │  └──────────┴──────────┴──────────┴──────────┘           │
│ • Recommend. │  ┌──────────────────────────────┬─────────────────────┐  │
│ • Analytics  │  │ Live Flow Telematics Map     │ Attention Needed    │  │
│ • Warehouses │  │ (Interactive SVG & Leaflet)  │ (Triage Queue)      │  │
│ • Drivers    │  ├──────────────────────────────┼─────────────────────┤  │
│ • Assistant  │  │ Recent Shipments Table       │ Assistant Companion │  │
│ [Truck Card] │  │ (Lifecycle Actions & Drawer) │ (Contextual Chat)   │  │
│ [Status: OK] │  └──────────────────────────────┴─────────────────────┘  │
└──────────────┴─────────────────────────────────────────────────────────┘
```

### 3.1 Top Navigation Bar (`TopNavbar.jsx`)
- **Telemetry Monitor**: Live ping test (`/health`) displaying API connectivity and real-time response indicator.
- **Multi-Entity Search**: Immediate filter across shipments, drivers, and warehouse facilities.
- **Notification Panel**: Slide-down alert drawer displaying unread alerts and deduplicated warnings.
- **Interactive Theme Switcher (`#btn-nav-theme-toggle`)**: Dynamically toggles dark/light theme, flips Sun/Moon SVG icons, and saves preference to `localStorage`.
- **Profile Dropdown**: Displays authenticated operator name, role claim badge, and session logout.

### 3.2 Sidebar Navigation (`Sidebar.jsx`)
- Deep navy background (`#0F172A`) across both dark and light modes for maximum brand cohesion.
- Brand logo with cyan glow accent and active tab indicators.
- Dynamic truck illustration card with velocity speedlines and slogan: *"Keeping your supply chain moving"*.
- System online heartbeat led indicator.

---

## 4. Component Design Patterns

### 4.1 KPI Telemetry Cards (`.ref-kpi-card`)
- Four primary metrics placed directly below the hero banner: Active Shipments, On-Time Dispatch Rate (94.2%), Critical Risk Freight, and Operating Hubs.
- Includes 7-day sparkline vector curves and color-coded delta pills (+4.2%, -1.1%).

### 4.2 Interactive Live Flow Map (`.live-flow-card`)
- High-fidelity SVG vector map displaying key national transport corridors (Seattle, Chicago, Dallas, Atlanta, New York).
- Animated dashed freight corridors and pulsing status halo nodes (`.pulse-halo`).
- Click-to-inspect city popups displaying active load counts, hub capacity, and weather conditions.
- Floating telematics telemetry badge displaying transit volume and speed variance.

### 4.3 Shipment Rescue Center (`RescueCenterPage.jsx`)
- Transparent exception triage table displaying evaluated deterministic operational rules:
  - `[RULE-EX01]`: Transit Exception (red badge).
  - `[RULE-R01]`: Missing Driver Allocation (amber badge).
  - `[RULE-R02]`: Missing Transport Vehicle (amber badge).
  - `[RULE-R03]`: Missing Transit Corridor (cyan badge).
  - `[RULE-R04]`: Capacity Overload >85% (amber badge).
- One-click intervention drawers to reassign drivers, vehicles, or line-haul corridors.

### 4.4 What-If Disruption Simulator (`DisruptionSimulatorPage.jsx`)
- Non-destructive client-side simulation cockpit.
- 4 scenario triggers: Driver Unavailability, Corridor Closure, Warehouse Bottleneck, and Fuel Surcharge Spikes.
- Side-by-side impact cards: Estimated Delivery Variance (+Hours) and Financial Strain ($).
- Single-click mitigation preview with side-by-side sandbox diff comparison.

### 4.5 Grounded Assistant UI (`LogisticsAssistantModal.jsx`)
- Slide-out drawer & dialog with quick prompt chips (*"Show unassigned shipments"*, *"Check warehouse capacity"*, *"Driver duty status"*).
- Responses styled with distinct Bot/User message bubbles, monospace entity tags (`#SHP-101`), and real API query execution indicators.

---

## 5. Responsive Breakpoints

| Breakpoint | Target Screen | Layout Adaptations |
| :--- | :--- | :--- |
| **Desktop Wide** (`>1200px`) | Control Tower Monitors | Full 2-column split grid, persistent sidebar, expanded tables. |
| **Desktop / Laptop** (`1024px–1200px`) | Standard Laptops | 2-column grid adapts with stacked KPI blocks and scrollable tables. |
| **Tablet** (`768px–1024px`) | Tablet Dispatchers | Collapsible sidebar overlay via hamburger toggle, stacked panels. |
| **Mobile** (`<768px`) | Field Personnel | Single-column view, horizontal scroll on data tables, compact headers. |

---

## 6. Accessibility & Operational UX
- **WCAG AA Compliance**: High contrast ratios on all text elements across both dark and light modes.
- **Monospace Formatting**: All tracking numbers, ISO timestamps, geographic coordinates, and SKUs use `var(--font-mono)` for scannability.
- **Keyboard Navigation**: Interactive modals and drawers support Escape-to-close, Tab traps, and Enter-to-search.
