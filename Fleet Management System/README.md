# Fleet Management System

A production-grade, multi-tenant SaaS Fleet Management System designed for logistics companies, freight carriers, municipal fleets, and enterprise vehicle fleets. The platform scales from 1,000 to 100,000+ vehicles, providing real-time GPS tracking, driver lifecycle management, regulatory compliance, predictive maintenance, and executive-level analytics — all from a single unified platform.

---

## Table of Contents

- [System Overview](#system-overview)
- [Tech Stack](#tech-stack)
- [Documentation Structure](#documentation-structure)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Documentation Status](#documentation-status)

---

## System Overview

Fleet operators face mounting pressure from rising fuel costs, tightening DOT/FMCSA regulations, driver shortages, and customer demands for real-time shipment visibility. Legacy fleet management tools are siloed, expensive to integrate, and fail at scale.

This system solves those challenges with a cloud-native, event-driven architecture that ingests high-frequency GPS telemetry, enforces compliance rules in real time, predicts vehicle failures before they cause downtime, and gives every stakeholder — from drivers in the cab to executives in the boardroom — the data they need.

**Target customers:**
| Segment | Fleet Size | Primary Pain Points |
|---|---|---|
| Regional freight carriers | 50–500 trucks | HOS/IFTA compliance, driver retention |
| National logistics providers | 500–10,000 vehicles | Real-time visibility, cost control |
| Municipal fleets | 100–5,000 mixed vehicles | Utilization, maintenance budgets |
| Enterprise fleets (retail/utilities) | 200–50,000+ vehicles | Multi-site coordination, driver safety |

**Core value proposition:**
- Reduce fuel costs by 12–18% through route optimization and idle-time alerts
- Cut unplanned maintenance downtime by 35% with predictive maintenance
- Achieve 100% FMCSA ELD compliance with automated HOS enforcement
- Recover stolen vehicles 4× faster with 15-second GPS polling in high-alert zones

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| API Services | Node.js 20 + TypeScript | Rich ecosystem, strong typing, async I/O for REST/WebSocket APIs |
| GPS Ingestion Service | Go 1.22 | High-throughput, low-latency binary protocol parsing; handles 50,000 GPS pings/second |
| Web Dashboard | React 18 + TypeScript + Vite | Component reuse, strong typing, fast HMR for developer productivity |
| Driver Mobile App | React Native 0.74 | Single codebase for iOS + Android; offline-first with background location |
| Primary Database | PostgreSQL 16 | ACID compliance, JSONB for flexible telemetry metadata, mature ecosystem |
| Time-Series Database | TimescaleDB (PostgreSQL extension) | Continuous aggregates and hypertables for GPS history at petabyte scale |
| Caching & Sessions | Redis 7 (Cluster) | Sub-millisecond lookups for live vehicle positions, session tokens, rate limiting |
| Event Streaming | Apache Kafka 3.7 | Durable, ordered event log for GPS events, alerts, and audit trails |
| Search | Elasticsearch 8 | Full-text search across driver records, maintenance notes, incidents |
| Object Storage | AWS S3 | DVIR photos, insurance documents, dashcam footage |
| Container Orchestration | Kubernetes (EKS) | Auto-scaling GPS ingestion pods, blue/green deployments |
| Cloud Provider | AWS | EKS, RDS Aurora, ElastiCache, MSK (Kafka), CloudFront, Route 53 |
| CI/CD | GitHub Actions + ArgoCD | GitOps-based deployments; canary releases for GPS service |
| Monitoring | Prometheus + Grafana + PagerDuty | Real-time SLO tracking, on-call alerting |
| Infrastructure as Code | Terraform + Helm | Reproducible multi-region infrastructure |

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Fleet Management System/
├── README.md                                  ← This file — project overview and navigation
│
├── traceability-matrix.md
├── requirements/
│   ├── requirements-document.md              ← Functional (FR-01–FR-55) and non-functional requirements (NFR-01–NFR-22)
│   └── user-stories.md                       ← 40+ user stories with Given/When/Then acceptance criteria
│
├── design/
│   ├── system-design.md                      ← Architecture overview, component diagram, data flow
│   ├── database-design.md                    ← ERD, table schemas, indexing strategy, partitioning
│   └── api-design.md                         ← REST API contracts, WebSocket events, authentication
│
├── implementation/
│   ├── backend-implementation.md             ← Service structure, domain logic, GPS ingestion pipeline
│   ├── frontend-implementation.md            ← Dashboard architecture, live map, component library
│   └── mobile-implementation.md             ← React Native app, offline sync, ELD integration
│
├── security/
│   └── security-compliance.md               ← Multi-tenant isolation, encryption, SOC 2, FMCSA ELD
│
└── testing/
    └── testing-strategy.md                  ← Unit, integration, load testing; GPS replay harness
```

---

## Key Features

### 🛰️ Real-Time GPS Tracking
Vehicles report position every 15 seconds (configurable down to 5 seconds in high-alert mode). Live positions are pushed to the web dashboard and dispatcher apps via WebSocket with sub-200ms end-to-end latency. Historical breadcrumb trails are stored in TimescaleDB with automatic retention policies (90 days full resolution, 2 years hourly aggregates).

### 📍 Geofencing
Fleet managers define unlimited geofences per tenant — polygon, circle, or corridor shapes — on an interactive map. Entry/exit events trigger configurable actions: push notifications to drivers, SMS alerts to dispatchers, automatic time-stamping for customer proof-of-delivery, or webhook callbacks to customer TMS systems.

### 👤 Driver Scoring & Coaching
Each driving event (harsh braking, rapid acceleration, sharp cornering, speeding, phone usage via OBD integration) is scored in real time using a weighted algorithm. Drivers receive in-app coaching cards after each trip. Managers see weekly trend reports and can set score thresholds that trigger mandatory coaching sessions.

### 🔧 Predictive Maintenance
Integrates with OBD-II/J1939 telematics to collect engine fault codes, oil life, brake pad wear indicators, and tire pressure. A rule-based engine (configurable per vehicle make/model) raises maintenance tickets before failures occur. Tracks service history, parts inventory, and warranty status per vehicle.

### 📋 DVIR (Driver Vehicle Inspection Reports)
Drivers complete pre-trip and post-trip inspections on the mobile app in under 2 minutes. Defects are categorized as minor or major (out-of-service). Major defects lock vehicle dispatch until a mechanic certifies the repair. Full FMCSA Part 396 compliance with digital signature capture and 90-day record retention.

### ⛽ Fuel Management
Records fuel transactions via manual entry, RFID card integrations (WEX, Comdata, Fleetcor), or pump telemetry. Detects fuel theft by comparing tank sensor fill events against card transactions. Generates IFTA fuel tax reports automatically by jurisdiction based on GPS-tracked mileage.

### 🕐 HOS Compliance (ELD)
FMCSA-certified Electronic Logging Device integration tracks driving, on-duty, off-duty, and sleeper berth time automatically from the mobile app. Drivers receive warnings at 30, 15, and 5 minutes before HOS violations. The system flags violations, supports exemptions (short-haul, adverse conditions), and generates DOT-ready log exports.

### 📊 IFTA Reporting
Automatically calculates miles driven per jurisdiction by cross-referencing GPS trip data with state/province boundary maps (updated quarterly). Generates quarterly IFTA tax returns pre-filled with jurisdiction miles and fuel gallons, ready for submission or export to accounting systems.

### 🚨 Incident Management
Drivers report incidents (collisions, theft, cargo damage, near-misses) from the mobile app with photo/video attachment. Incident records are linked to the vehicle, driver, location, and active trip. Built-in workflows route incidents to the fleet manager, insurance team, or safety officer with SLA tracking.

### 🗺️ Route Optimization
Dispatchers plan multi-stop routes with time windows, vehicle capacity constraints, and driver HOS availability. The routing engine (powered by OSRM + custom traffic model) minimizes total distance and fuel cost. Routes are pushed to driver navigation in the mobile app.

### 🏢 Multi-Tenant Architecture
Complete data isolation between tenants via row-level security in PostgreSQL. Each tenant gets configurable role permissions, custom alert rules, branded driver app themes, and separate API keys. Tenant administrators manage their own users without platform-level access.

### 📈 Analytics & Reporting
Executive dashboards show fleet utilization rate, cost-per-mile, on-time delivery rate, and safety score trends. Standard reports include: vehicle utilization, driver performance, fuel efficiency, maintenance cost, geofence compliance, and idle time. Custom report builder supports drag-and-drop metric selection with CSV/PDF/XLSX export.

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

- Node.js 20+ and pnpm 9+
- Go 1.22+
- Docker Desktop 4.x and Docker Compose v2
- AWS CLI v2 configured with appropriate credentials
- kubectl and Helm 3+
- PostgreSQL client (psql)

### Local Development Setup

1. **Clone the repository and install dependencies:**
   ```bash
   git clone https://github.com/your-org/fleet-management-system.git
   cd fleet-management-system
   pnpm install
   ```

2. **Start infrastructure services with Docker Compose:**
   ```bash
   docker compose -f infra/docker-compose.local.yml up -d
   # Starts PostgreSQL + TimescaleDB, Redis, Kafka, Zookeeper, Elasticsearch
   ```

3. **Run database migrations:**
   ```bash
   pnpm --filter @fleet/api run db:migrate
   # Applies all Flyway migrations in services/api/src/db/migrations/
   ```

4. **Seed development data:**
   ```bash
   pnpm --filter @fleet/api run db:seed
   # Creates 3 demo tenants, 50 vehicles, 30 drivers with historical GPS data
   ```

5. **Start all services in development mode:**
   ```bash
   pnpm run dev
   # Starts API (port 4000), GPS ingestion (port 5000), web dashboard (port 3000)
   ```

6. **Access the dashboard:**
   Open `http://localhost:3000` and log in with:
   - Fleet Manager: `manager@demo-fleet.com` / `Demo1234!`
   - Driver: `driver@demo-fleet.com` / `Demo1234!`
   - Admin: `admin@demo-fleet.com` / `Demo1234!`

### Running Tests

```bash
# Unit and integration tests (all services)
pnpm run test

# Load test — GPS ingestion service (requires running infra)
cd services/gps-ingestion
go test -run TestLoad -count=1 -timeout=120s

# End-to-end tests (requires full local stack)
pnpm --filter @fleet/e2e run test
```

### Environment Configuration

Copy the example environment files and update values:
```bash
cp services/api/.env.example services/api/.env
cp services/gps-ingestion/.env.example services/gps-ingestion/.env
cp apps/dashboard/.env.example apps/dashboard/.env.local
```

Key environment variables:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://fleet:pass@localhost:5432/fleetdb` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `KAFKA_BROKERS` | Kafka broker list | `localhost:9092` |
| `JWT_SECRET` | JWT signing secret (min 64 chars) | (generate with `openssl rand -hex 32`) |
| `AWS_S3_BUCKET` | S3 bucket for document storage | `fleet-docs-dev` |
| `MAPBOX_TOKEN` | Mapbox API token for map tiles | `pk.eyJ1...` |
| `ELD_PROVIDER_KEY` | ELD telematics provider API key | (obtain from provider portal) |

### Kubernetes Deployment (Staging/Production)

```bash
# Deploy to staging
helmfile -e staging apply

# Deploy GPS ingestion service only (canary)
helm upgrade gps-ingestion ./charts/gps-ingestion \
  --set image.tag=v2.3.1 \
  --set canary.enabled=true \
  --set canary.weight=10 \
  -n fleet-staging

# Run smoke tests against staging
pnpm --filter @fleet/e2e run test:staging
```

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Section | Document | Status | Last Updated |
|---|---|---|---|
| Requirements | [requirements-document.md](./requirements/requirements-document.md) | ✅ Complete | 2025-01 |
| Requirements | [user-stories.md](./requirements/user-stories.md) | ✅ Complete | 2025-01 |
| Design | [system-design.md](./design/system-design.md) | ✅ Complete | 2025-01 |
| Design | [database-design.md](./design/database-design.md) | ✅ Complete | 2025-01 |
| Design | [api-design.md](./design/api-design.md) | ✅ Complete | 2025-01 |
| Implementation | [backend-implementation.md](./implementation/backend-implementation.md) | ✅ Complete | 2025-01 |
| Implementation | [frontend-implementation.md](./implementation/frontend-implementation.md) | ✅ Complete | 2025-01 |
| Implementation | [mobile-implementation.md](./implementation/mobile-implementation.md) | ✅ Complete | 2025-01 |
| Security | [security-compliance.md](./security/security-compliance.md) | ✅ Complete | 2025-01 |
| Testing | [testing-strategy.md](./testing/testing-strategy.md) | ✅ Complete | 2025-01 |
