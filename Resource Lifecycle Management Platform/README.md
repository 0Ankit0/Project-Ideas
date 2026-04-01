# Resource Lifecycle Management Platform

> A production-grade, event-driven platform for managing the complete lifecycle of physical and
> logical resources — equipment, rooms, vehicles, tools, hardware, and venues — from catalog
> provisioning through active use, maintenance, and decommissioning.

---

## Overview

The Resource Lifecycle Management Platform (RLMP) provides a unified control plane for every
stage of a resource's operational life. Operators catalog assets, customers reserve and check
out resources, field custodians capture condition evidence at each handoff, and the finance team
settles deposits and damage charges — all coordinated through a single event-driven system with
strong consistency guarantees, SLA enforcement, and full audit trails.

### Core Lifecycle Flow

```
Catalog → Reserve → Allocate → Checkout → Active Use → Check-In → Condition Assessment
        → Maintenance → Return to Availability → Decommission
```

```mermaid
flowchart LR
    A([ResourceCataloged]) --> B([DRAFT])
    B -->|activate| C([ACTIVE])
    C -->|reserve| D([RESERVED])
    D -->|allocate| E([ALLOCATED])
    E -->|checkout| F([CHECKED_OUT])
    F -->|check-in| G([RETURNING])
    G -->|condition ok| C
    G -->|damage| H([INCIDENT])
    H -->|resolved| C
    C -->|maintenance| I([MAINTENANCE])
    I -->|completed| C
    C -->|retire| J([RETIRED])
```

---

## Documentation Structure

| Directory | Contents |
|-----------|----------|
| `requirements/` | Functional and non-functional requirements, user stories |
| `analysis/` | Use-case diagrams, system context, business rules, event catalog, data dictionary |
| `high-level-design/` | Architecture overview, domain model, C4 diagrams (L1/L2), data-flow diagrams |
| `detailed-design/` | Class diagrams, sequence diagrams, state machines, ERD/schema, API design |
| `implementation/` | Coding guidelines, backend status matrix, C4 code diagram |
| `infrastructure/` | Deployment topology, network design, cloud architecture (AWS) |
| `edge-cases/` | Domain-specific edge-case analyses across 7 concern areas |

---

## Key Features

### Resource Catalog and Availability
- Hierarchical resource types with configurable attribute schemas
- Real-time availability calendar with multi-location support
- Barcode/QR-code integration for physical asset identification
- SLA-based availability guarantees per resource class

### Reservation and Allocation
- Conflict detection via optimistic locking on `Resource.availability` (BR-01)
- Lead-time enforcement: 30 min standard, 24 h premium resources (BR-02)
- Quota management per customer and resource pool
- Priority queue for premium SLA customers

### Checkout and Check-In Workflows
- Mandatory deposit hold before checkout (BR-03)
- Photo evidence capture and damage-note entry at check-in
- Mandatory condition report within 2 h of check-in (BR-04)
- Barcode scanner integration with offline fallback

### Maintenance and Scheduling
- Scheduled and on-demand maintenance jobs
- Active maintenance blocks all reservations (BR-05)
- Auto-cancellation of conflicting reservations with customer notification
- Maintenance history and cost tracking

### Incident and Settlement Management
- Automatic deposit hold on damage incident creation (BR-06)
- Settlement calculation: refund = deposit − (damage charges + late fees) (BR-07)
- Overdue escalation: 1 h → reminder, 4 h → manager, 24 h → legal hold (BR-08)
- SLA breach detection and automatic credit (BR-09)

### Finance and Compliance
- Full audit trail for every state transition
- Configurable policies per resource type
- Role-based access: Requestor, Custodian, Resource Manager, Finance, Compliance

---

## Getting Started

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Node.js / TypeScript | ≥ 20 LTS | Core API services |
| PostgreSQL | ≥ 15 | Transactional data store |
| Redis | ≥ 7 | Distributed cache and idempotency store |
| Apache Kafka | ≥ 3.6 | Event streaming backbone |
| Elasticsearch / OpenSearch | ≥ 8 | Full-text search and analytics |
| OPA (Open Policy Agent) | ≥ 0.60 | Policy engine |
| Docker / Kubernetes | latest | Container orchestration |

### Local Development

```bash
# Clone and install
git clone https://github.com/your-org/resource-lifecycle-platform
cd resource-lifecycle-platform
npm install

# Start infrastructure dependencies
docker compose up -d postgres redis kafka elasticsearch

# Run database migrations
npm run db:migrate

# Seed catalog data
npm run db:seed

# Start the API server
npm run dev
```

### Environment Variables

```bash
DATABASE_URL=postgresql://rlmp:secret@localhost:5432/rlmp_dev
REDIS_URL=redis://localhost:6379
KAFKA_BROKERS=localhost:9092
ELASTICSEARCH_URL=http://localhost:9200
PAYMENT_GATEWAY_URL=https://pay.example.com
JWT_SECRET=<your-secret>
OPA_URL=http://localhost:8181
```

### API Quick Reference

```
POST /resource-types          # Define a new resource type
POST /resources               # Catalog a new resource unit
POST /reservations            # Create a reservation
POST /allocations             # Confirm allocation
POST /checkouts               # Begin checkout (triggers deposit hold)
POST /check-ins               # Return resource (triggers condition flow)
POST /condition-reports       # File condition report
POST /maintenance             # Schedule maintenance job
POST /incidents               # Report damage or loss
POST /settlements             # Initiate settlement calculation
```

Base URL: `https://api.rlmp.example.com/v1`  
Auth: `Authorization: Bearer <JWT>`

---

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Requirements | ✅ Complete | 2024-Q4 |
| User Stories | ✅ Complete | 2024-Q4 |
| Use-Case Diagram | ✅ Complete | 2024-Q4 |
| Use-Case Descriptions | ✅ Complete | 2024-Q4 |
| System Context Diagram | ✅ Complete | 2024-Q4 |
| Activity Diagrams | ✅ Complete | 2024-Q4 |
| Swimlane Diagrams | ✅ Complete | 2024-Q4 |
| Business Rules | ✅ Complete | 2024-Q4 |
| Event Catalog | ✅ Complete | 2024-Q4 |
| Data Dictionary | ✅ Complete | 2024-Q4 |
| Architecture Diagram | ✅ Complete | 2024-Q4 |
| Domain Model | ✅ Complete | 2024-Q4 |
| C4 Diagrams (L1/L2/L3) | ✅ Complete | 2024-Q4 |
| Data-Flow Diagrams | ✅ Complete | 2024-Q4 |
| System Sequence Diagrams | ✅ Complete | 2024-Q4 |
| Class Diagrams | ✅ Complete | 2024-Q4 |
| Sequence Diagrams | ✅ Complete | 2024-Q4 |
| State-Machine Diagrams | ✅ Complete | 2024-Q4 |
| ERD / Database Schema | ✅ Complete | 2024-Q4 |
| Component Diagrams | ✅ Complete | 2024-Q4 |
| API Design | ✅ Complete | 2024-Q4 |
| C4 Component Diagram | ✅ Complete | 2024-Q4 |
| Lifecycle Orchestration | ✅ Complete | 2024-Q4 |
| Implementation Guidelines | ✅ Complete | 2024-Q4 |
| C4 Code Diagram | ✅ Complete | 2024-Q4 |
| Backend Status Matrix | ✅ Complete | 2024-Q4 |
| Deployment Diagram | ✅ Complete | 2024-Q4 |
| Network Infrastructure | ✅ Complete | 2024-Q4 |
| Cloud Architecture | ✅ Complete | 2024-Q4 |
| Edge Cases — Reservation | ✅ Complete | 2024-Q4 |
| Edge Cases — Checkout | ✅ Complete | 2024-Q4 |
| Edge Cases — Lifecycle | ✅ Complete | 2024-Q4 |
| Edge Cases — Settlement | ✅ Complete | 2024-Q4 |
| Edge Cases — API/UI | ✅ Complete | 2024-Q4 |
| Edge Cases — Security | ✅ Complete | 2024-Q4 |
| Edge Cases — Operations | ✅ Complete | 2024-Q4 |

---

## Related Projects

- **Payment Orchestration Platform** — handles deposit holds and settlement disbursements
- **Identity and Access Management Platform** — JWT issuance and role enforcement
- **Notification Service** — SMS/email delivery for reservation confirmations, overdue alerts
- **ERP Integration (SAP)** — asset register synchronization and cost posting
