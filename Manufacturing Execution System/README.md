# Manufacturing Execution System

> Enterprise-grade MES for discrete and process manufacturing — production orders, work centers, OEE analytics, quality management, material tracking, and shop floor execution.

---

## Table of Contents

1. [Documentation Structure](#documentation-structure)
2. [Key Features](#key-features)
3. [Getting Started](#getting-started)
4. [Architecture Overview](#architecture-overview)
5. [Technology Stack](#technology-stack)
6. [Prerequisites](#prerequisites)
7. [Documentation Status](#documentation-status)

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


| File | Path | Description |
|------|------|-------------|
| README | `README.md` | Project overview, architecture summary, and navigation guide |
| Requirements | `requirements/requirements.md` | Functional (FR-001–FR-045) and non-functional (NFR-001–NFR-022) requirements |
| User Stories | `requirements/user-stories.md` | 30+ user stories across six shop floor personas |
| System Context | `analysis/system-context.md` | C4 system context, external actors, integration boundaries |
| Domain Model | `analysis/domain-model.md` | Core MES entities, aggregates, bounded contexts, ubiquitous language |
| Process Flows | `analysis/process-flows.md` | End-to-end production order lifecycle, quality hold workflows |
| Data Flows | `analysis/data-flows.md` | IoT ingestion pipeline, ERP sync, historian write paths |
| High-Level Architecture | `high-level-design/architecture.md` | Microservice decomposition, deployment topology, ADRs |
| API Design | `high-level-design/api-design.md` | REST + gRPC contract overview, versioning strategy, OpenAPI anchors |
| Event Catalog | `high-level-design/event-catalog.md` | Kafka topic taxonomy, event schema registry, consumer groups |
| Integration Design | `high-level-design/integration-design.md` | SAP IDoc/RFC, OPC-UA, MQTT broker topology, Greengrass edge runtime |
| Production Order Service | `detailed-design/production-order-service.md` | Order lifecycle state machine, scheduling algorithm, BOM explosion |
| Work Center Service | `detailed-design/work-center-service.md` | Capacity model, shift calendars, queue management, bottleneck detection |
| OEE Service | `detailed-design/oee-service.md` | Availability/Performance/Quality computation, downtime classification, ISO 22400 |
| Quality Service | `detailed-design/quality-service.md` | SPC engine, inspection plan execution, CAPA workflow, 21 CFR Part 11 |
| Material Service | `detailed-design/material-service.md` | Lot management, BOM consumption, back-flushing, yield variance |
| Traceability Service | `detailed-design/traceability-service.md` | Forward/backward genealogy graph, serialization, recall simulation |
| IoT Gateway | `detailed-design/iot-gateway.md` | Edge runtime, PLC adapters, protocol normalization, buffering strategy |
| Labor Service | `detailed-design/labor-service.md` | Operator assignments, time tracking, skills matrix, electronic signatures |
| Notification Service | `detailed-design/notification-service.md` | Escalation rules, shift handover reports, alert routing |
| Database Schema | `detailed-design/database-schema.md` | PostgreSQL schemas, TimescaleDB hypertables, partitioning strategy |
| Infrastructure | `infrastructure/infrastructure.md` | Kubernetes manifests, Helm charts, AWS topology, network segmentation |
| Observability | `infrastructure/observability.md` | OpenTelemetry, Prometheus, Grafana dashboards, alert runbooks |
| Security | `infrastructure/security.md` | ISA/IEC 62443 zones, mTLS, RBAC, OT/IT DMZ, secret management |
| Disaster Recovery | `infrastructure/disaster-recovery.md` | RTO/RPO targets, backup strategy, failover runbooks |
| Implementation Guide | `implementation/implementation-guide.md` | Sprint plan, onboarding checklist, local dev setup |
| Coding Standards | `implementation/coding-standards.md` | Java/Spring Boot conventions, test pyramid, PR checklist |
| Deployment Runbook | `implementation/deployment-runbook.md` | Blue-green deployment, Helm upgrade procedure, rollback steps |
| Edge Cases | `edge-cases/edge-cases.md` | 40+ production edge cases: split orders, partial scrap, network partition, PLC brownout |

---

## Key Features

### 1. Production Order Management
Full lifecycle management for discrete and process manufacturing orders — create, plan, release, start, suspend, complete, and cancel. Supports split orders, rework orders, and phantom assemblies. BOM explosion with alternate BOMs, engineering change control, and revision management.

### 2. Work Center Scheduling & Capacity Planning
Forward/backward finite-capacity scheduling with configurable shift calendars, crew sizes, and setup/teardown matrices. Bottleneck detection via Theory of Constraints drum-buffer-rope logic. Gantt visualization with drag-and-drop rescheduling and what-if scenario comparison.

### 3. OEE Tracking (Availability × Performance × Quality)
Real-time ISO 22400-compliant OEE calculation per work center, production line, and plant. Downtime events auto-classified against a configurable reason code tree. Six-big-loss waterfall charts updated at 1-minute resolution using TimescaleDB continuous aggregates.

### 4. Statistical Process Control (SPC) / Quality Management
Xbar-R, Xbar-S, p, np, c, u control charts with configurable Western Electric and Nelson rules. Inline inspection plan execution with AQL sampling logic. Lot disposition workflow (pass, reject, conditional release, hold). Full CAPA lifecycle with 8D template, effectiveness verification, and recurrence tracking.

### 5. Material Consumption & Traceability
BOM-driven automatic and manual material consumption with lot/serial-number granularity. FIFO/FEFO lot allocation engine. Back-flushing at operation completion. Yield tracking with theoretical vs. actual variance calculation and automatic deviation triggers.

### 6. Forward & Backward Genealogy
Graph-based traceability store (Neo4j-backed) enabling full forward trace (from raw material to finished goods) and backward trace (from finished goods to source lots/suppliers). Recall simulation with impact analysis executed in < 10 seconds for 1 million+ component nodes.

### 7. IoT / SCADA Integration
AWS IoT Greengrass v2 edge runtime with plug-in adapters for OPC-UA, Modbus TCP, MQTT, and PROFINET. PLC machine state collection at 100 ms polling intervals. Automatic signal normalization, unit-of-measure conversion, and dead-band filtering before cloud ingest.

### 8. ERP Integration (SAP S/4HANA)
Bidirectional sync with SAP via IDoc (LOIPRO01, LOIROU01, MBLIM, MBGMCR) and RFC calls. Production order confirmation (CO11N equivalent), goods issue/receipt posting, and quality notification creation. Delta-sync with exponential retry, poison-message quarantine, and idempotency keys.

### 9. Labor Management & Electronic Signatures
Operator login via badge scan or PIN. Time-and-attendance integration with granular task-level labor tracking. Skills matrix enforcement — operators can only start operations matching their certified skill/level. 21 CFR Part 11-compliant electronic signatures with meaning capture and audit trail.

### 10. Real-Time Shop Floor Visibility
WebSocket-based live dashboards showing production order status, work-in-process (WIP) counts, machine states (running, idle, fault, changeover), and queue depths. Andon-board integration over MQTT for physical signal stack alerting.

### 11. Electronic Batch Records (EBR)
Auto-generated batch records capturing all process parameters, material consumptions, quality results, operator actions, and deviations for each production lot. Tamper-evident PDF/A archival with SHA-256 hash verification for GMP compliance.

### 12. Deviation & Non-Conformance Management
Automated deviation detection from set-point out-of-tolerance thresholds, SPC rule violations, and missing inspection results. Deviation record creation with severity classification, immediate containment actions, root cause analysis, and linkage to CAPA.

### 13. Shift Handover Management
Structured shift handover report generated from live WIP snapshot, open deviations, machine downtime events, and pending quality holds. Supervisor acknowledgement workflow with digital signature. Handover data retained and queryable for trend analysis.

### 14. Barcode & RFID Scanning
Native support for GS1-128, GS1 DataMatrix, QR Code, and EPC RFID (UHF 900 MHz). Scan-to-confirm operations, material picks, container moves, and serialized unit tracking. Offline scan buffering on shop floor terminals for DMZ network resilience.

### 15. Predictive Maintenance Hooks
Machine health index calculated from vibration, temperature, and cycle-count signals via streaming ML inference (AWS SageMaker endpoint). Maintenance work order pre-generation at configurable risk thresholds with integration to CMMS (IBM Maximo / SAP PM).

### 16. Reporting & KPI Analytics
Pre-built BIRT/Jasper report templates for production performance, OEE trending, quality yield, scrap/rework costs, and labor efficiency. Ad-hoc query builder using Apache Superset over read-replica PostgreSQL. Scheduled report distribution via email and S3.

### 17. Multi-Plant & Multi-Tenant Architecture
Tenant-isolated deployments with plant-level data partitioning. Cross-plant production order transfer with material and quality record migration. Centralized plant KPI comparison dashboards for corporate operations teams.

---

## Getting Started

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        CORPORATE / CLOUD LAYER                            │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────────┐ │
│  │  SAP S/4HANA  │  │  CMMS (Maximo)│  │  Corporate BI / Data Lake     │ │
│  └──────┬────────┘  └──────┬────────┘  └──────────────┬────────────────┘ │
│         │ IDoc/RFC          │ REST                      │ S3/Redshift      │
└─────────┼───────────────────┼───────────────────────────┼──────────────────┘
          │                   │                           │
┌─────────▼───────────────────▼───────────────────────────▼──────────────────┐
│                        MES APPLICATION LAYER (Kubernetes)                   │
│                                                                              │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐  │
│  │ Production   │ │ Work Center │ │ OEE Service  │ │ Quality Service   │  │
│  │ Order Svc    │ │ Service     │ │              │ │ (SPC + CAPA)      │  │
│  └──────┬───────┘ └──────┬──────┘ └──────┬───────┘ └─────────┬─────────┘  │
│         │                │               │                    │             │
│  ┌──────▼───────┐ ┌──────▼──────┐ ┌──────▼───────┐ ┌─────────▼─────────┐  │
│  │ Material Svc │ │ Labor Svc   │ │ Traceability │ │ Notification Svc  │  │
│  └──────┬───────┘ └─────────────┘ │ Service      │ └───────────────────┘  │
│         │                         └──────────────┘                         │
│  ┌──────▼─────────────────────────────────────────────────────────────┐    │
│  │               Kafka Event Bus (MSK)                                │    │
│  └──────┬──────────────────────────────────────────────────────────┬──┘    │
│         │                                                          │        │
│  ┌──────▼──────┐                                         ┌─────────▼──────┐ │
│  │ PostgreSQL  │                                         │ TimescaleDB    │ │
│  │ (Transact.) │                                         │ (Time-series)  │ │
│  └─────────────┘                                         └────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
          │ MQTT/TLS
┌─────────▼──────────────────────────────────────────────────────────────────┐
│                     OT/IT DMZ — IoT Edge Layer                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  AWS IoT Greengrass v2 (per plant)                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │  │
│  │  │ OPC-UA Adapt.│  │ Modbus Adapt.│  │ MQTT Local Broker        │    │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘    │  │
│  └─────────┼─────────────────┼───────────────────────────────────────────┘  │
│            │ OPC-UA           │ Modbus TCP                                   │
│  ┌─────────▼─────────────────▼──────────────────────────────────────────┐   │
│  │  Shop Floor: PLCs, CNCs, Robots, Sensors, SCADA                       │   │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Services** | Java 21 / Spring Boot 3.x | Microservice runtime |
| **API Gateway** | Spring Cloud Gateway | Routing, auth, rate limiting |
| **Service Mesh** | Istio | mTLS, traffic management, observability |
| **Event Bus** | Apache Kafka (AWS MSK) | Async messaging, event sourcing |
| **Transactional DB** | PostgreSQL 16 | Orders, quality, labor records |
| **Time-Series DB** | TimescaleDB 2.x | OEE metrics, IoT telemetry |
| **Graph DB** | Neo4j Enterprise | Genealogy / traceability graph |
| **Cache** | Redis Cluster | Session, real-time dashboard state |
| **Object Storage** | AWS S3 | EBR PDFs, report archives |
| **Edge Runtime** | AWS IoT Greengrass v2 | PLC data collection, local compute |
| **Protocol Adapters** | Eclipse Milo (OPC-UA), j2mod (Modbus) | PLC connectivity |
| **Frontend** | React 18 + TypeScript + TanStack Query | Shop floor UI |
| **Mobile / Handheld** | React Native | Barcode scanning, mobile WI |
| **Container Platform** | Kubernetes 1.29 (EKS) | Service orchestration |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps delivery pipeline |
| **Observability** | OpenTelemetry + Prometheus + Grafana | Metrics, traces, logs |
| **Secret Management** | AWS Secrets Manager + External Secrets | Credential lifecycle |
| **Schema Registry** | Confluent Schema Registry (Avro) | Event schema governance |
| **ML Inference** | AWS SageMaker endpoints | Predictive maintenance |

### Prerequisites

**Development Environment:**
- JDK 21 (Temurin distribution recommended)
- Docker Desktop 4.x with Kubernetes enabled
- Node.js 20 LTS + pnpm 9
- Helm 3.14+
- kubectl 1.29+
- AWS CLI v2 configured with appropriate IAM role
- `make` (GNU Make 4+)

**Infrastructure Access:**
- AWS account with EKS, MSK, RDS, IoT Core, SageMaker permissions
- VPN access to plant floor network (OT DMZ segment)
- SAP RFC user with appropriate authorization objects (C_AFKO_AWK, M_MSEG_BWA)

**Clone and Bootstrap:**
```bash
git clone https://github.com/your-org/manufacturing-execution-system.git
cd manufacturing-execution-system
make bootstrap          # installs tool dependencies
make dev-up             # starts all services via docker-compose
make seed               # loads reference data (work centers, reason codes, BOMs)
open http://localhost:3000   # shop floor UI
```

---

## Documentation Status

| Document | Path | Status | Last Updated |
|----------|------|--------|--------------|
| README | `README.md` | ✅ Complete | 2025-01-01 |
| Requirements | `requirements/requirements.md` | ✅ Complete | 2025-01-01 |
| User Stories | `requirements/user-stories.md` | ✅ Complete | 2025-01-01 |
| System Context | `analysis/system-context.md` | ✅ Complete | 2025-01-01 |
| Domain Model | `analysis/domain-model.md` | ✅ Complete | 2025-01-01 |
| Process Flows | `analysis/process-flows.md` | ✅ Complete | 2025-01-01 |
| Data Flows | `analysis/data-flows.md` | ✅ Complete | 2025-01-01 |
| High-Level Architecture | `high-level-design/architecture.md` | ✅ Complete | 2025-01-01 |
| API Design | `high-level-design/api-design.md` | ✅ Complete | 2025-01-01 |
| Event Catalog | `high-level-design/event-catalog.md` | ✅ Complete | 2025-01-01 |
| Integration Design | `high-level-design/integration-design.md` | ✅ Complete | 2025-01-01 |
| Production Order Service | `detailed-design/production-order-service.md` | ✅ Complete | 2025-01-01 |
| Work Center Service | `detailed-design/work-center-service.md` | ✅ Complete | 2025-01-01 |
| OEE Service | `detailed-design/oee-service.md` | ✅ Complete | 2025-01-01 |
| Quality Service | `detailed-design/quality-service.md` | ✅ Complete | 2025-01-01 |
| Material Service | `detailed-design/material-service.md` | ✅ Complete | 2025-01-01 |
| Traceability Service | `detailed-design/traceability-service.md` | ✅ Complete | 2025-01-01 |
| IoT Gateway | `detailed-design/iot-gateway.md` | ✅ Complete | 2025-01-01 |
| Labor Service | `detailed-design/labor-service.md` | ✅ Complete | 2025-01-01 |
| Notification Service | `detailed-design/notification-service.md` | ✅ Complete | 2025-01-01 |
| Database Schema | `detailed-design/database-schema.md` | ✅ Complete | 2025-01-01 |
| Infrastructure | `infrastructure/infrastructure.md` | ✅ Complete | 2025-01-01 |
| Observability | `infrastructure/observability.md` | ✅ Complete | 2025-01-01 |
| Security | `infrastructure/security.md` | ✅ Complete | 2025-01-01 |
| Disaster Recovery | `infrastructure/disaster-recovery.md` | ✅ Complete | 2025-01-01 |
| Implementation Guide | `implementation/implementation-guide.md` | ✅ Complete | 2025-01-01 |
| Coding Standards | `implementation/coding-standards.md` | ✅ Complete | 2025-01-01 |
| Deployment Runbook | `implementation/deployment-runbook.md` | ✅ Complete | 2025-01-01 |
| Edge Cases | `edge-cases/edge-cases.md` | ✅ Complete | 2025-01-01 |

---

## Contributing

Shop floor software demands zero-defect engineering practices. All changes must pass the full test pyramid (unit → integration → E2E) before merging. Pull requests touching OEE calculation logic, lot disposition, or electronic signature workflows require a second review from a domain expert. See `implementation/coding-standards.md` for the full PR checklist.

## License

Proprietary — All rights reserved. See `LICENSE` for terms.
