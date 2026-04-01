# C4 Architecture Diagrams — Manufacturing Execution System

## Overview

This document presents the C4 model views of the Manufacturing Execution System (MES). The C4 model provides a hierarchical set of diagrams that zoom into the system at increasing levels of detail, enabling different stakeholder groups to understand the architecture at the right level of abstraction without being overwhelmed by irrelevant detail.

**Diagram Levels**

| Level | Audience | Describes |
|-------|---------|-----------|
| Level 1 — System Context | All stakeholders | The MES and its relationships with users and external systems |
| Level 2 — Container | Architects, tech leads | The deployable units (services, databases, frontends) inside the MES boundary |
| Level 3 — Component | Service developers | The major components inside each MES Core service |

**People**

| Person | Role in Manufacturing Operations |
|--------|----------------------------------|
| Production Operator | Executes work orders on the plant floor; scans components via barcode or RFID; reports finished quantities and scrap |
| Quality Inspector | Performs scheduled and triggered inspections; records measurements; manages non-conformance reports and lot dispositions |
| Plant Manager | Monitors production KPIs, OEE trends, and schedule adherence; reviews quality summaries; adjusts capacity constraints |
| ERP Administrator | Configures and monitors the SAP integration; manages master data synchronization schedules; resolves integration errors |
| Maintenance Engineer | Responds to equipment downtime alerts; records maintenance activities and root causes; reviews MTTR and MTTF metrics |

**Notation**

All diagrams use Mermaid flowchart notation styled to approximate C4 semantics. Boxes with blue fill represent internal system containers or components. Grey fill indicates external systems. Person shapes represent human actors.

---

## Level 1: System Context Diagram

The System Context diagram places the MES inside its broader ecosystem. It shows the MES as a black box and identifies every person and external system that interacts with it, along with the nature of those interactions.

```mermaid
flowchart TB
    classDef person fill:#08427b,color:#fff,stroke:#052e56,rx:50
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884
    classDef external fill:#6b6b6b,color:#fff,stroke:#444

    PO["👷 Production Operator\n─────────────────\nExecutes work orders;\nscans components;\nreports output quantities\nand scrap"]:::person

    QI["🔍 Quality Inspector\n─────────────────\nRecords inspection results;\ndispositions lots;\nmanages NCRs and CAPAs"]:::person

    PM["📊 Plant Manager\n─────────────────\nMonitors OEE and KPIs;\nreviews shift summaries;\nadjusts capacity constraints"]:::person

    EA["🛠 ERP Administrator\n─────────────────\nConfigures SAP integration;\nmanages master data sync;\nresolves interface errors"]:::person

    ME["🔧 Maintenance Engineer\n─────────────────\nReceives downtime alerts;\nrecords maintenance work;\nreviews MTTR metrics"]:::person

    MES["Manufacturing Execution System\n══════════════════════════════\nOrchestrates production order\nexecution, quality management,\nmaterial tracking, OEE analytics,\nand plant-floor integration for\ndiscrete manufacturing operations"]:::system

    SAP["SAP ERP\n─────────────────\nProduction orders, BOMs,\nroutings, material masters,\nQM notifications"]:::external

    SCADA["SCADA / DCS\n─────────────────\nMachine states, alarms,\nprocess parameters,\nsetpoint feedback"]:::external

    IOT["IoT Sensor Network\n─────────────────\nTemperature, pressure,\ntorque, vibration sensors\npublishing MQTT telemetry"]:::external

    WHS["Warehouse Management System\n─────────────────\nInventory levels, goods\nreceipts, material staging,\npicking confirmations"]:::external

    QMS_EXT["External QMS\n─────────────────\nDocument control, audit\nmanagement, external\nquality certifications"]:::external

    PO -->|"Work order execution events,\ncomponent scans, output quantities"| MES
    MES -->|"Work instructions, job queue,\nstatus feedback, alerts"| PO

    QI -->|"Inspection measurements,\nNCR decisions, lot dispositions"| MES
    MES -->|"Inspection plans, SPC alerts,\nquality dashboards"| QI

    PM -->|"Schedule adjustments,\ncapacity constraints"| MES
    MES -->|"OEE reports, production KPIs,\nshift summaries, anomaly alerts"| PM

    EA -->|"Integration configuration,\nmaster data sync triggers"| MES
    MES -->|"Integration health status,\nerror reports, sync logs"| EA

    ME -->|"Downtime reason codes,\nmaintenance records"| MES
    MES -->|"Equipment health alerts,\nMTTF/MTTR metrics"| ME

    MES <-->|"Production orders, BOMs, routings;\ngoods movement and production confirmations"| SAP

    MES <-->|"Machine state events, alarms;\nsetpoint commands, recipe downloads"| SCADA

    IOT -->|"Raw sensor telemetry\n(OPC-UA / MQTT over TLS)"| MES

    MES <-->|"Material withdrawal requests,\ncomponent consumption;\ninventory levels, GR confirmations"| WHS

    MES <-->|"Quality notifications,\nNCR export, certificate data"| QMS_EXT
```

---

## Level 2: Container Diagram

The Container diagram opens the MES boundary to reveal the deployable units: microservices, databases, the event bus, and the user interface. Each container is independently deployable and runs in its own process.

```mermaid
flowchart TB
    classDef person fill:#08427b,color:#fff,stroke:#052e56
    classDef container fill:#1168bd,color:#fff,stroke:#0b4884
    classDef database fill:#2d6a4f,color:#fff,stroke:#1b4332
    classDef messaging fill:#774936,color:#fff,stroke:#4a2c2a
    classDef infra fill:#444,color:#fff,stroke:#222
    classDef external fill:#6b6b6b,color:#fff,stroke:#444

    PO_C2["👷 Production Operator\n+ Quality Inspector\n+ Plant Manager"]:::person
    EA_C2["🛠 ERP Administrator\n+ Maintenance Engineer"]:::person

    subgraph MES_BOUNDARY["Manufacturing Execution System  (On-Premises Kubernetes Cluster)"]

        REACT["React Frontend\n──────────────────\nTypeScript / React 18 / Vite\n\nSingle-page application:\noperator work order UI,\nproduction dashboards,\nSPC charts, OEE gauges,\nmaterial genealogy queries"]:::container

        APIGW["API Gateway\n──────────────────\nKong Gateway 3.x\n\nJWT authentication,\nTLS termination,\nrate limiting, request\nrouting to services"]:::container

        PRODSVC["Production Service\n──────────────────\nGo 1.22\n\nWork order lifecycle,\noperation start/stop,\ncycle time, output,\nproduction confirmations"]:::container

        QUALSVC["Quality Service\n──────────────────\nGo 1.22\n\nInspection plans,\nmeasurement capture,\nSPC computation,\nNCR and CAPA lifecycle"]:::container

        MATSVC["Material Service\n──────────────────\nGo 1.22\n\nLot/serial registry,\ncomponent staging,\nconsumption recording,\nWIP balance ledger"]:::container

        IOTSVC["IoT Ingest Service\n──────────────────\nGo 1.22\n\nMQTT consumption\nfrom edge gateways,\ntelemetry normalization\nand Kafka publication"]:::container

        INTGSVC["Integration Service\n──────────────────\nGo 1.22\n\nBidirectional SAP\nRFC/BAPI and WMS\nREST integration with\nretry and dead-letter"]:::container

        ANALYTICSVC["Analytics Service\n──────────────────\nPython 3.12\n\nOEE computation engine,\nML anomaly detection,\ncontinuous aggregate\nquery materialization"]:::container

        KAFKA["Event Bus\n──────────────────\nApache Kafka 3.7 (KRaft)\n\nDurable append-only log;\nasynchronous cross-service\ncommunication backbone;\npartitioned by work center"]:::messaging

        SCHEMA["Schema Registry\n──────────────────\nConfluent Schema Registry\n\nAvro schema governance\nfor all Kafka topics;\nbackward-compatibility\nenforcement"]:::messaging

        PG["PostgreSQL 16\n──────────────────\nOperational relational store:\nwork orders, quality records,\nmaterial ledger, NCR/CAPA,\ntraceability genealogy"]:::database

        TSDB["TimescaleDB 2.x\n──────────────────\nTime-series store:\nsensor telemetry,\nOEE metrics,\ncontinuous aggregates"]:::database

        REDIS["Redis 7 (Cluster)\n──────────────────\nApplication cache:\nwork order assignments,\nequipment reference data,\ndistributed locks, sessions"]:::database

        VAULT["HashiCorp Vault\n──────────────────\nSecrets management:\ndatabase credentials,\nSAP RFC keys,\nTLS certificates"]:::infra

    end

    SAP_C2["SAP ERP"]:::external
    SCADA_C2["SCADA / DCS\n+ Edge Gateways"]:::external
    WMS_C2["Warehouse\nManagement System"]:::external

    PO_C2 -->|"HTTPS"| REACT
    EA_C2 -->|"HTTPS"| REACT
    REACT -->|"HTTPS REST / WebSocket"| APIGW
    APIGW -->|"gRPC"| PRODSVC
    APIGW -->|"gRPC"| QUALSVC
    APIGW -->|"gRPC"| MATSVC
    APIGW -->|"REST"| ANALYTICSVC

    SCADA_C2 -->|"MQTT over mTLS"| IOTSVC

    PRODSVC -->|"Publish events"| KAFKA
    QUALSVC -->|"Publish events"| KAFKA
    MATSVC -->|"Publish events"| KAFKA
    IOTSVC -->|"Publish telemetry"| KAFKA
    KAFKA -->|"Consume events"| INTGSVC
    KAFKA -->|"Consume events"| ANALYTICSVC
    KAFKA -->|"Machine state events"| PRODSVC
    KAFKA --- SCHEMA

    PRODSVC <-->|"SQL"| PG
    QUALSVC <-->|"SQL"| PG
    MATSVC <-->|"SQL"| PG
    INTGSVC <-->|"SQL (outbox)"| PG
    IOTSVC -->|"Write telemetry"| TSDB
    ANALYTICSVC <-->|"Read/Write"| TSDB
    PRODSVC <-->|"Cache"| REDIS
    QUALSVC <-->|"Cache"| REDIS

    PRODSVC -->|"Secret fetch"| VAULT
    QUALSVC -->|"Secret fetch"| VAULT
    MATSVC -->|"Secret fetch"| VAULT
    INTGSVC -->|"Secret fetch"| VAULT

    INTGSVC <-->|"RFC/BAPI via JCo"| SAP_C2
    INTGSVC <-->|"REST over HTTPS"| WMS_C2
```

---

## Level 3: Component Diagram (MES Core)

The Component diagrams zoom into each of the four primary MES Core services, exposing their internal component structure, responsibilities, and the relationships between those components.

### Production Service Components

```mermaid
flowchart TB
    classDef component fill:#1168bd,color:#fff,stroke:#0b4884
    classDef store fill:#2d6a4f,color:#fff,stroke:#1b4332

    APIGW_L3["API Gateway"]
    KAFKA_L3["Kafka Event Bus"]
    PG_L3["PostgreSQL"]
    REDIS_L3["Redis"]

    subgraph PRODSVC_L3["Production Service (Go)"]

        WO_CTRL["Work Order Controller\n──────────────────\nHTTP/gRPC handlers for\nwork order CRUD, release,\ncomplete, and cancel"]:::component

        OP_CTRL["Operation Controller\n──────────────────\nHandles operation start,\npause, resume, stop;\nvalidates work center\navailability before start"]:::component

        SCHED["Scheduling Engine\n──────────────────\nDispatches work orders\nto work centers; applies\npriority rules and\ncapacity constraints"]:::component

        STATE["Work Order State Machine\n──────────────────\nEnforces valid state\ntransitions: Created →\nReleased → In Progress\n→ Completed / Cancelled"]:::component

        CYCLE["Cycle Time Calculator\n──────────────────\nComputes actual vs.\nstandard cycle time;\ngenerates OEE Performance\nmetric inputs"]:::component

        CONFIRM["Confirmation Generator\n──────────────────\nBuilds SAP-bound CO11N\nproduction confirmations;\napplies backflush BOM\nexplosion for yield"]:::component

        OUTBOX["Outbox Publisher\n──────────────────\nReliable event publication\nusing transactional outbox\npattern; Kafka relay\nwith at-least-once delivery"]:::component

        WO_REPO["Work Order Repository\n──────────────────\nData access layer for\nwork orders, operations,\nwork center assignments,\nand state history"]:::component

    end

    APIGW_L3 -->|"gRPC"| WO_CTRL & OP_CTRL
    WO_CTRL --> STATE
    STATE --> WO_REPO
    OP_CTRL --> SCHED
    SCHED --> CYCLE
    CYCLE --> CONFIRM
    CONFIRM --> OUTBOX
    OUTBOX -->|"Publish production.events"| KAFKA_L3
    WO_REPO <-->|"SQL"| PG_L3
    SCHED <-->|"Work center cache"| REDIS_L3
    KAFKA_L3 -->|"machine.states events"| OP_CTRL
```

### Quality Service Components

```mermaid
flowchart TB
    classDef component fill:#1168bd,color:#fff,stroke:#0b4884

    APIGW_Q["API Gateway"]
    KAFKA_Q["Kafka Event Bus"]
    PG_Q["PostgreSQL"]
    TSDB_Q["TimescaleDB"]

    subgraph QUALSVC_L3["Quality Service (Go)"]

        INSP_CTRL["Inspection Controller\n──────────────────\nHTTP/gRPC handlers:\ninspection plan retrieval,\nmeasurement submission,\nand result queries"]:::component

        INSP_ENGINE["Inspection Plan Engine\n──────────────────\nApplies AQL sampling rules;\ntriggers inspection events\nfor the correct inspector\nand work center"]:::component

        MEAS["Measurement Processor\n──────────────────\nValidates values against\nspecification limits;\nrecords pass/fail results\nand attribute data"]:::component

        SPC_ENGINE["SPC Engine\n──────────────────\nMaintains Xbar-R, Xbar-S,\nand I-MR control charts;\napplies all eight Western\nElectric detection rules"]:::component

        NCR_CTRL["NCR Controller\n──────────────────\nManages NCR lifecycle:\nOpen → Under Review\n→ Dispositioned → Closed;\nnotifies stakeholders"]:::component

        CAPA_SVC["CAPA Service\n──────────────────\nLinks corrective actions\nto NCRs; tracks due dates,\nverification deadlines,\nand effectiveness reviews"]:::component

        LOT_DISP["Lot Disposition Service\n──────────────────\nRecords accept, reject,\nor rework dispositions;\npublishes lot status events\nto unblock production"]:::component

        QUAL_REPO["Quality Repository\n──────────────────\nData access for inspection\nplans, measurements, NCRs,\nSPC chart data, and\nCAPA records"]:::component

    end

    APIGW_Q -->|"gRPC"| INSP_CTRL & NCR_CTRL
    INSP_CTRL --> INSP_ENGINE
    INSP_ENGINE --> MEAS
    MEAS --> SPC_ENGINE
    SPC_ENGINE -->|"Chart time-series"| TSDB_Q
    MEAS --> LOT_DISP
    LOT_DISP -->|"Publish quality.measurements"| KAFKA_Q
    NCR_CTRL --> CAPA_SVC
    NCR_CTRL -->|"Publish quality.ncr"| KAFKA_Q
    QUAL_REPO <-->|"SQL"| PG_Q
    INSP_ENGINE --> QUAL_REPO
    MEAS --> QUAL_REPO
    NCR_CTRL --> QUAL_REPO
```

### Material Service Components

```mermaid
flowchart TB
    classDef component fill:#1168bd,color:#fff,stroke:#0b4884

    APIGW_M["API Gateway"]
    KAFKA_M["Kafka Event Bus"]
    PG_M["PostgreSQL"]

    subgraph MATSVC_L3["Material Service (Go)"]

        LOT_CTRL["Lot Controller\n──────────────────\nHandles lot creation,\nstatus updates, split/merge\noperations, and lot\nmaster queries"]:::component

        SERIAL_SVC["Serial Number Service\n──────────────────\nManages serial number\nassignment, validation,\nreassignment, and full\nserial history queries"]:::component

        ISSUE_SVC["Component Issue Service\n──────────────────\nProcesses component issues\nto work orders; validates\nBOM consistency; enforces\nFIFO / FEFO rules"]:::component

        BACKFLUSH["Backflush Engine\n──────────────────\nAutomatically consumes\nBOM components on work\norder completion;\nconfigurable per routing step"]:::component

        WIP_LEDGER["WIP Ledger\n──────────────────\nDouble-entry inventory\nledger recording every\nmaterial movement with\ndebit and credit entries"]:::component

        GENEA["Genealogy Builder\n──────────────────\nConstructs parent-child\ntraceability links enabling\nfull forward and backward\ngenealogy traversal"]:::component

        MAT_REPO["Material Repository\n──────────────────\nData access for lots,\nserials, movements,\nledger entries, and\ngenealogy graph"]:::component

    end

    APIGW_M -->|"gRPC"| LOT_CTRL & SERIAL_SVC & ISSUE_SVC
    ISSUE_SVC --> WIP_LEDGER
    ISSUE_SVC --> GENEA
    LOT_CTRL --> SERIAL_SVC
    BACKFLUSH --> ISSUE_SVC
    KAFKA_M -->|"production.events (complete)"| BACKFLUSH
    WIP_LEDGER -->|"Publish material.movements"| KAFKA_M
    GENEA -->|"Publish traceability events"| KAFKA_M
    MAT_REPO <-->|"SQL"| PG_M
    WIP_LEDGER --> MAT_REPO
    GENEA --> MAT_REPO
    LOT_CTRL --> MAT_REPO
```

### Integration Service Components

```mermaid
flowchart TB
    classDef component fill:#1168bd,color:#fff,stroke:#0b4884

    KAFKA_I["Kafka Event Bus"]
    PG_I["PostgreSQL"]
    SAP_I["SAP ERP\n(RFC/BAPI)"]
    WMS_I["WMS\n(REST)"]

    subgraph INTGSVC_L3["Integration Service (Go)"]

        SAP_ADAPTER["SAP Adapter\n──────────────────\nTranslates MES domain events\nto SAP BAPI calls covering\nPP (CO11N), QM (QM02),\nMM (MIGO), PM (IW31)"]:::component

        WMS_ADAPTER["WMS Adapter\n──────────────────\nTranslates material movements\nto WMS REST API calls;\nhandles goods receipts\nand transfer orders"]:::component

        RETRY_MGR["Retry Manager\n──────────────────\nExponential backoff retry\nfor all failed external\ncalls; configurable max\nattempts per integration"]:::component

        DLQ["Dead Letter Queue Handler\n──────────────────\nProcesses permanently\nfailed messages; raises\nalerts to ERP Admin;\nlogs for manual review"]:::component

        IDEMPOTENCY["Idempotency Guard\n──────────────────\nPrevents duplicate SAP\nor WMS calls using a\nmessage hash deduplication\ntable in PostgreSQL"]:::component

        MAPPER["Domain Mapper\n──────────────────\nBidirectional field\ntransformation between\nMES domain models and\nSAP / WMS data structures"]:::component

        INBOUND["Inbound Processor\n──────────────────\nConsumes SAP-originated\nevents (order changes,\nmaterial master updates)\nand publishes to Kafka"]:::component

    end

    KAFKA_I -->|"erp.outbound events"| SAP_ADAPTER
    KAFKA_I -->|"material.movements"| WMS_ADAPTER
    SAP_ADAPTER --> MAPPER
    MAPPER --> IDEMPOTENCY
    IDEMPOTENCY --> RETRY_MGR
    RETRY_MGR <-->|"RFC/JCo calls"| SAP_I
    RETRY_MGR --> DLQ
    WMS_ADAPTER <-->|"REST"| WMS_I
    SAP_I -->|"Inbound RFC / IDoc callbacks"| INBOUND
    INBOUND -->|"Publish to erp.inbound"| KAFKA_I
    IDEMPOTENCY <-->|"Dedup hash table"| PG_I
    DLQ -->|"Dead-letter records"| PG_I
```

---

## Key Relationships

The table below summarises the critical relationships between containers, the communication protocol, direction, and the primary data exchanged in each relationship.

| From | To | Protocol | Direction | Key Data Exchanged |
|------|----|----------|-----------|-------------------|
| React Frontend | API Gateway | HTTPS REST + WebSocket | Bidirectional | Work orders, quality records, OEE metrics, real-time production events |
| API Gateway | Production Service | gRPC | Bidirectional | Work order commands and state queries |
| API Gateway | Quality Service | gRPC | Bidirectional | Inspection submissions, measurement queries, NCR management |
| API Gateway | Material Service | gRPC | Bidirectional | Lot queries, component issue requests, genealogy traversal |
| Production Service | Kafka | Kafka Producer | Outbound | `production.events`: order state changes, operation completions, confirmations |
| Quality Service | Kafka | Kafka Producer | Outbound | `quality.measurements`, `quality.ncr`: measurement results, NCR lifecycle events |
| Material Service | Kafka | Kafka Producer | Outbound | `material.movements`: lot issuance, consumption, goods movements |
| IoT Ingest Service | Kafka | Kafka Producer | Outbound | `machine.states`, `sensor.telemetry`: enriched machine events and telemetry |
| Integration Service | Kafka | Kafka Consumer + Producer | Bidirectional | Consumes all outbound topics; produces `erp.inbound` with SAP-originated changes |
| Analytics Service | Kafka | Kafka Consumer | Inbound | `machine.states`, `production.events` for real-time OEE computation |
| Production Service | PostgreSQL | SQL (pgx) | Bidirectional | Work orders, operations, work center assignments, state history |
| Quality Service | PostgreSQL | SQL (pgx) | Bidirectional | Inspection plans, measurements, NCRs, CAPA records |
| Material Service | PostgreSQL | SQL (pgx) | Bidirectional | Lots, serials, movements, WIP ledger, genealogy graph |
| IoT Ingest Service | TimescaleDB | SQL (pgx) | Write-only | Sensor telemetry hypertable: tag value, timestamp, unit, work center |
| Analytics Service | TimescaleDB | SQL (pgx) | Bidirectional | OEE metric writes; continuous aggregate and trend reads |
| Integration Service | SAP ERP | SAP JCo (RFC/BAPI) | Bidirectional | CO11N confirmations, QM02 notifications, MIGO goods movements, IW31 orders |
| Integration Service | WMS | REST / HTTPS | Bidirectional | Goods movement notifications, inventory level queries, staging requests |
| Edge Gateways | IoT Ingest Service | MQTT 5.0 over mTLS | Inbound | Sensor payloads: device ID, tag name, value, engineering unit, UTC timestamp |

### Architectural Invariants

The following rules are enforced by design and must not be violated by any future architectural change:

- The **Production Service**, **Quality Service**, and **Material Service** never call each other directly over synchronous interfaces. All cross-domain coordination flows exclusively through Kafka events, preserving bounded context isolation and preventing cascading failures.
- **TimescaleDB** is written to only by the IoT Ingest Service and the Analytics Service. Operational services (Production, Quality, Material) have no write access to TimescaleDB, preserving a clean separation between transactional and analytical workloads.
- The **Integration Service** is the sole component authorized to initiate calls to SAP ERP and the WMS. No other service may reach external enterprise systems directly, ensuring all integration logic is centralized, auditable, and replaceable.
- All services retrieve secrets exclusively from **HashiCorp Vault** at startup and on lease expiry. Secrets must never appear in environment variables passed through Kubernetes manifests, ConfigMaps, container images, or source code repositories.
- The **API Gateway** is the only authorized ingress point for external HTTP and WebSocket traffic. Direct pod-to-pod requests from outside the cluster are blocked by Kubernetes NetworkPolicy and Istio AuthorizationPolicy rules, preventing bypass of authentication and authorization controls.
- Events published to Kafka topics that carry production or quality data are considered **immutable records**. Consumers must never request deletion or modification of Kafka messages as a workaround for application errors; instead, compensating events must be published referencing the original event identifier.
