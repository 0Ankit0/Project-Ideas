# Component Diagrams — Manufacturing Execution System

## Overview

This document provides a detailed structural decomposition of the Manufacturing Execution System (MES) into deployable components. Each component is described with its responsibilities, provided and required interfaces, technology stack, and deployment unit. Mermaid diagrams illustrate how components relate to one another across the core MES, edge layer, integration layer, and frontend.

The MES follows a domain-driven microservices architecture deployed on Kubernetes. Components communicate via synchronous REST/gRPC for request-response interactions and asynchronous event streaming via Apache Kafka for high-throughput telemetry, state change propagation, and inter-service decoupling.

---

## MES Core Components

Core components implement the primary manufacturing domain logic: production order management, work center scheduling, quality control, material tracking, and OEE analytics.

### Production Order Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Production Order Service                                               |
| Responsibility   | Lifecycle management of production orders (create, dispatch, complete, cancel). Tracks order status, quantity, routing, and due dates. |
| Interfaces Provided | `POST /api/v1/production-orders`, `GET /api/v1/production-orders/{id}`, `PATCH /api/v1/production-orders/{id}/status`, Kafka topic `production-order-events` |
| Interfaces Required | Work Center Service (capacity check), Material Service (availability check), ERP Integration Service (order sync) |
| Technology       | Java 21 / Spring Boot 3, PostgreSQL, Kafka                            |
| Deployment Unit  | `mes-production-order-service` (Kubernetes Deployment, 2–4 replicas)  |

### Work Center Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Work Center Service                                                    |
| Responsibility   | Models work centers (machines, cells, lines). Manages capacity, availability windows, shift calendars, and real-time machine states. |
| Interfaces Provided | `GET /api/v1/work-centers`, `GET /api/v1/work-centers/{id}/capacity`, Kafka topic `work-center-state-events` |
| Interfaces Required | IoT Telemetry Service (machine state), Scheduling Service (capacity reservation) |
| Technology       | Java 21 / Spring Boot 3, PostgreSQL, Redis (state cache)              |
| Deployment Unit  | `mes-work-center-service` (Kubernetes Deployment, 2 replicas)         |

### Scheduling Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Scheduling Service                                                     |
| Responsibility   | Finite capacity scheduling (FCS) of operations onto work centers. Supports FIFO, EDD, and priority-rule dispatching. Publishes schedule plans. |
| Interfaces Provided | `POST /api/v1/schedules/compute`, `GET /api/v1/schedules/{planId}`, Kafka topic `schedule-events` |
| Interfaces Required | Production Order Service (order details), Work Center Service (capacity), Material Service (material readiness) |
| Technology       | Python 3.12, OR-Tools (CP-SAT solver), PostgreSQL, Kafka              |
| Deployment Unit  | `mes-scheduling-service` (Kubernetes Deployment, 1–2 replicas)        |

### Quality Management Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Quality Management Service                                             |
| Responsibility   | Manages inspection plans, SPC control charts, inspection results, NCR (non-conformance reports), and disposition workflows. |
| Interfaces Provided | `POST /api/v1/inspections`, `GET /api/v1/spc/control-charts/{id}`, `POST /api/v1/ncr`, Kafka topic `quality-events` |
| Interfaces Required | Production Order Service (order context), Material Service (lot traceability), Notification Service (alerts) |
| Technology       | Java 21 / Spring Boot 3, PostgreSQL, Kafka                            |
| Deployment Unit  | `mes-quality-service` (Kubernetes Deployment, 2 replicas)             |

### Material Tracking Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Material Tracking Service                                              |
| Responsibility   | Tracks raw material lots, WIP containers, and finished goods by lot/serial. Manages GRN, consumption, and inventory movements. |
| Interfaces Provided | `POST /api/v1/materials/consume`, `GET /api/v1/materials/lots/{lotId}`, `GET /api/v1/materials/traceability/{serialNo}`, Kafka topic `material-events` |
| Interfaces Required | ERP Integration Service (stock sync), Quality Service (lot disposition), Production Order Service (BOM resolution) |
| Technology       | Java 21 / Spring Boot 3, PostgreSQL, Kafka                            |
| Deployment Unit  | `mes-material-service` (Kubernetes Deployment, 2 replicas)            |

### OEE Analytics Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | OEE Analytics Service                                                  |
| Responsibility   | Computes Availability, Performance, and Quality metrics per work center and shift. Aggregates micro-stoppages and generates OEE trend reports. |
| Interfaces Provided | `GET /api/v1/oee/{workCenterId}`, `GET /api/v1/oee/trends`, Kafka topic `oee-calculated-events` |
| Interfaces Required | IoT Telemetry Service (machine runtime data), Production Order Service (planned vs actual), Quality Service (defect counts) |
| Technology       | Python 3.12 / FastAPI, TimescaleDB, Kafka, Redis                      |
| Deployment Unit  | `mes-oee-service` (Kubernetes Deployment, 2 replicas)                 |

```mermaid
graph TD
    subgraph "MES Core Services"
        PO[Production Order Service]
        WC[Work Center Service]
        SCH[Scheduling Service]
        QM[Quality Management Service]
        MT[Material Tracking Service]
        OEE[OEE Analytics Service]
    end

    PO -->|capacity check| WC
    PO -->|material availability| MT
    SCH -->|order details| PO
    SCH -->|capacity slots| WC
    SCH -->|material readiness| MT
    QM -->|order context| PO
    QM -->|lot traceability| MT
    OEE -->|planned qty / actuals| PO
    OEE -->|defect counts| QM
```

---

## Edge Components

Edge components run on-premises at the factory floor, close to machines and PLCs, handling real-time data acquisition, protocol translation, and local buffering.

### IoT Gateway

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | IoT Gateway                                                            |
| Responsibility   | Collects machine signals from PLCs and sensors via OPC-UA, Modbus TCP, and MQTT. Normalizes payloads and forwards to the cloud broker. |
| Interfaces Provided | MQTT broker endpoint (local), OPC-UA server (read), REST `/health` |
| Interfaces Required | Cloud Kafka broker (TLS), PLC/sensor endpoints (OPC-UA / Modbus)    |
| Technology       | Node.js 20, node-opcua, MQTT.js, Docker on industrial PC             |
| Deployment Unit  | `iot-gateway` (Docker Compose on edge node, HA pair)                  |

### SCADA Adapter

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | SCADA Adapter                                                          |
| Responsibility   | Bridges the plant SCADA system (Ignition / WinCC) with the MES event bus. Translates SCADA tag changes into structured MES events. |
| Interfaces Provided | REST `POST /scada/events` (inbound from SCADA), Kafka topic `scada-raw-events` |
| Interfaces Required | SCADA historian API, Cloud Kafka broker                              |
| Technology       | Python 3.12, pyignition / pywincc SDK, Docker                        |
| Deployment Unit  | `scada-adapter` (Docker on edge DMZ server)                           |

### Edge Data Buffer

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Edge Data Buffer                                                       |
| Responsibility   | Local time-series store for telemetry during network outages. Replays buffered data to the cloud once connectivity is restored. |
| Interfaces Provided | InfluxDB line protocol (write/read), `/buffer/status` REST endpoint |
| Interfaces Required | IoT Gateway (write), Cloud Kafka (replay upload)                    |
| Technology       | InfluxDB OSS 2.x, Docker                                              |
| Deployment Unit  | `edge-buffer` (Docker on edge node, persistent volume)                |

```mermaid
graph LR
    subgraph "Factory Floor"
        PLC[PLC / Sensors]
        SCADA_SYS[SCADA System]
    end
    subgraph "Edge Layer"
        GW[IoT Gateway]
        SA[SCADA Adapter]
        BUF[Edge Data Buffer]
    end
    subgraph "Cloud / On-Prem Data Centre"
        KAFKA[Apache Kafka]
        IOT_SVC[IoT Telemetry Service]
    end

    PLC -- "OPC-UA / Modbus" --> GW
    SCADA_SYS -- "Tag historian API" --> SA
    GW --> BUF
    GW -- "MQTT/TLS" --> KAFKA
    BUF -- "replay on reconnect" --> KAFKA
    SA --> KAFKA
    KAFKA --> IOT_SVC
```

---

## Integration Components

Integration components manage data exchange with external enterprise systems (SAP ERP) and expose MES data to downstream consumers.

### ERP Integration Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | ERP Integration Service                                                |
| Responsibility   | Bi-directional sync with SAP S/4HANA: inbound production orders and BOMs; outbound goods movements, confirmations, and quality notifications. |
| Interfaces Provided | `POST /erp/inbound/production-orders`, `POST /erp/outbound/confirmations`, Kafka topics `erp-inbound-events`, `erp-outbound-events` |
| Interfaces Required | SAP RFC / OData APIs, Production Order Service, Material Service     |
| Technology       | Java 21 / Spring Integration, SAP JCo connector, Kafka               |
| Deployment Unit  | `mes-erp-integration` (Kubernetes Deployment, 2 replicas)             |

### IoT Telemetry Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | IoT Telemetry Service                                                  |
| Responsibility   | Ingests raw telemetry from Kafka, validates, enriches with asset metadata, and persists to TimescaleDB. Streams processed events to downstream services. |
| Interfaces Provided | `GET /api/v1/telemetry/{assetId}`, Kafka topic `telemetry-processed`, WebSocket `wss://…/live/{assetId}` |
| Interfaces Required | Kafka (raw topics from edge), TimescaleDB, Asset Registry            |
| Technology       | Python 3.12 / FastAPI, TimescaleDB, Kafka, WebSocket                 |
| Deployment Unit  | `mes-iot-telemetry` (Kubernetes Deployment, 3–6 replicas, HPA)        |

### Notification Service

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Notification Service                                                   |
| Responsibility   | Routes OEE threshold alerts, quality alarms, and order status changes to operators via email, SMS, or push notification. |
| Interfaces Provided | `POST /api/v1/notifications`, Kafka consumer `notification-requests` |
| Interfaces Required | SMTP relay, SMS gateway (Twilio), FCM push                          |
| Technology       | Node.js 20, Kafka consumer, Nodemailer, Twilio SDK                   |
| Deployment Unit  | `mes-notification-service` (Kubernetes Deployment, 2 replicas)        |

```mermaid
graph TD
    subgraph "Core Services"
        PO2[Production Order Service]
        MT2[Material Service]
        OEE2[OEE Service]
        QM2[Quality Service]
    end
    subgraph "Integration Layer"
        ERP[ERP Integration Service]
        IOT[IoT Telemetry Service]
        NOTIF[Notification Service]
    end
    subgraph "External Systems"
        SAP[SAP S/4HANA]
        EMAIL[Email / SMS]
        EDGE2[Edge Layer]
    end

    SAP <-->|RFC / OData| ERP
    ERP -->|inbound orders| PO2
    ERP -->|stock sync| MT2
    PO2 -->|confirmations| ERP
    EDGE2 -->|telemetry| IOT
    IOT -->|processed events| OEE2
    OEE2 -->|alert requests| NOTIF
    QM2 -->|alarm requests| NOTIF
    NOTIF --> EMAIL
```

---

## Frontend Components

Frontend components deliver operator, quality, and management interfaces via a single-page web application and operator station displays.

### MES Web Shell

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | MES Web Shell                                                          |
| Responsibility   | Micro-frontend host: lazy-loads domain modules (production, quality, OEE) and provides shared navigation, auth context, and theme. |
| Interfaces Provided | Browser SPA, module federation entry points                        |
| Interfaces Required | Auth Service (OIDC/PKCE), all MES REST APIs                        |
| Technology       | React 18, Vite, Module Federation, TypeScript                        |
| Deployment Unit  | `mes-web-shell` (Nginx container, CDN-backed)                         |

### Production Floor Display

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Production Floor Display (Andon Board)                                 |
| Responsibility   | Real-time kiosk display showing current order status, target vs. actual quantities, machine state, and OEE for each work center. |
| Interfaces Provided | Full-screen browser display (TV/kiosk)                              |
| Interfaces Required | IoT Telemetry WebSocket, OEE API, Work Center API                  |
| Technology       | React 18, WebSocket client, Recharts                                  |
| Deployment Unit  | `mes-andon-display` (Nginx container, served to floor kiosks)         |

### Quality Inspection Module

| Attribute        | Detail                                                                 |
|------------------|------------------------------------------------------------------------|
| Name             | Quality Inspection Module                                              |
| Responsibility   | Touch-friendly interface for quality inspectors to record measurement results, trigger SPC calculations, and raise NCRs. |
| Interfaces Provided | Module federation remote `quality@/remoteEntry.js`                 |
| Interfaces Required | Quality Management API, Material Tracking API                      |
| Technology       | React 18, React Hook Form, Recharts (SPC charts), TypeScript         |
| Deployment Unit  | Loaded dynamically by MES Web Shell                                   |

```mermaid
graph TD
    SHELL[MES Web Shell]
    PROD_MOD[Production Module]
    QUAL_MOD[Quality Inspection Module]
    OEE_MOD[OEE Dashboard Module]
    ANDON[Andon Board Display]

    SHELL -->|lazy load| PROD_MOD
    SHELL -->|lazy load| QUAL_MOD
    SHELL -->|lazy load| OEE_MOD

    PROD_MOD -->|REST| PO_API[Production Order API]
    PROD_MOD -->|REST| WC_API[Work Center API]
    QUAL_MOD -->|REST| QM_API[Quality API]
    OEE_MOD -->|REST + WebSocket| OEE_API[OEE API]
    ANDON -->|WebSocket| TELEM_WS[Telemetry WebSocket]
    ANDON -->|REST| OEE_API
```

---

## Component Dependency Graph

The following graph provides a holistic view of all component dependencies across all layers of the system.

```mermaid
graph TD
    subgraph "Frontend Layer"
        SHELL2[Web Shell]
        ANDON2[Andon Board]
    end
    subgraph "API Gateway"
        GW2[Kong API Gateway]
    end
    subgraph "Core Services"
        PO3[Production Order Svc]
        WC3[Work Center Svc]
        SCH3[Scheduling Svc]
        QM3[Quality Svc]
        MT3[Material Svc]
        OEE3[OEE Analytics Svc]
    end
    subgraph "Integration & Infra"
        ERP3[ERP Integration Svc]
        IOT3[IoT Telemetry Svc]
        NOTIF3[Notification Svc]
        AUTH3[Auth Service - Keycloak]
        KAFKA3[Apache Kafka]
    end
    subgraph "Edge Layer"
        EDGE3[IoT Gateway + SCADA Adapter]
    end
    subgraph "Data Stores"
        PG[PostgreSQL cluster]
        TS[TimescaleDB]
        RD[Redis cluster]
    end

    SHELL2 --> GW2
    ANDON2 --> GW2
    GW2 --> AUTH3
    GW2 --> PO3
    GW2 --> WC3
    GW2 --> QM3
    GW2 --> MT3
    GW2 --> OEE3
    GW2 --> IOT3

    PO3 --> PG
    WC3 --> PG
    WC3 --> RD
    SCH3 --> PG
    QM3 --> PG
    MT3 --> PG
    OEE3 --> TS
    OEE3 --> RD
    IOT3 --> TS

    PO3 --> KAFKA3
    WC3 --> KAFKA3
    QM3 --> KAFKA3
    MT3 --> KAFKA3
    OEE3 --> KAFKA3
    ERP3 --> KAFKA3
    IOT3 --> KAFKA3

    EDGE3 --> KAFKA3
    ERP3 <-->|RFC/OData| SAP2[SAP S/4HANA]
    QM3 --> NOTIF3
    OEE3 --> NOTIF3

    SCH3 --> PO3
    SCH3 --> WC3
    SCH3 --> MT3
    QM3 --> PO3
    QM3 --> MT3
    OEE3 --> PO3
    OEE3 --> QM3
```

### Dependency Summary Table

| Consumer                  | Depends On                                    | Interface Type        |
|---------------------------|-----------------------------------------------|-----------------------|
| Scheduling Service        | Production Order Svc, Work Center Svc, Material Svc | REST (sync)      |
| Quality Service           | Production Order Svc, Material Svc            | REST (sync)           |
| OEE Analytics Service     | Production Order Svc, Quality Svc, IoT Telemetry | Kafka (async)      |
| ERP Integration Service   | Production Order Svc, Material Svc            | Kafka (async) + REST  |
| IoT Telemetry Service     | Edge Gateway (via Kafka)                      | Kafka (async)         |
| Notification Service      | Quality Svc, OEE Svc (via Kafka)              | Kafka (async)         |
| MES Web Shell             | All core services                             | REST / WebSocket      |
| Andon Board               | IoT Telemetry Svc, OEE Svc                    | REST + WebSocket      |
