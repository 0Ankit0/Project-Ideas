# Data Flow Diagrams — Manufacturing Execution System

## Overview

This document presents the data flow diagrams (DFDs) for the Manufacturing Execution System (MES) supporting discrete manufacturing operations. DFDs model how data moves between external entities, processes, and data stores at progressively increasing levels of detail.

The MES orchestrates production orders, work center scheduling, quality management, material tracking, OEE calculation, and integration with upstream ERP (SAP) and downstream IoT/SCADA systems. These diagrams serve as the authoritative reference for understanding data lineage, transformation points, and integration boundaries across the full production lifecycle.

**Diagram Conventions**

| Symbol | Represents |
|--------|-----------|
| Rounded rectangle | External entity (source or sink) |
| Rectangle | Process (transforms data) |
| Cylinder / open rectangle | Data store (persistent) |
| Labeled arrow | Named data flow |

All flows are named to reflect the semantic content of the data, not the transport mechanism. Bidirectional arrows indicate request/response pairs where both directions carry distinct payloads.

---

## Level 0 Data Flow Diagram (context)

The context diagram presents the entire MES as a single process interacting with all external entities. It establishes the system boundary and identifies every actor that either provides data to or consumes data from the MES.

**External Entities**

| Entity | Role |
|--------|------|
| SAP ERP | Master data, production orders, material requirements planning |
| SCADA / DCS | Real-time machine states, alarms, process parameters |
| IoT Sensor Network | Raw sensor telemetry (temperature, pressure, torque, vibration) |
| Production Operator | Work order execution inputs, component scans, manual measurements |
| Quality Inspector | Inspection results, non-conformance reports, lot dispositions |
| Plant Manager | Schedule adjustments, KPI consumption, capacity constraints |
| Maintenance Engineer | Equipment downtime events, corrective action data |
| Warehouse Management System | Inventory levels, goods receipt confirmations, material staging |

```mermaid
flowchart LR
    ERP["SAP ERP\n(External Entity)"]
    SCADA["SCADA / DCS\n(External Entity)"]
    IoT["IoT Sensor Network\n(External Entity)"]
    OP["Production Operator\n(External Entity)"]
    QI["Quality Inspector\n(External Entity)"]
    PM["Plant Manager\n(External Entity)"]
    ME["Maintenance Engineer\n(External Entity)"]
    WMS["Warehouse Management System\n(External Entity)"]

    MES(["MES\nManufacturing Execution System"])

    ERP -->|"Production orders, BOMs, routings,\nmaster data, material masters"| MES
    MES -->|"Goods movement confirmations,\nproduction confirmations, QM notifications"| ERP

    SCADA -->|"Machine states, alarms,\nprocess parameters"| MES
    MES -->|"Setpoint commands,\nrecipe downloads"| SCADA

    IoT -->|"Sensor telemetry streams\n(OPC-UA / MQTT)"| MES

    OP -->|"Work order starts/stops,\ncomponent scans, quantity reports"| MES
    MES -->|"Work instructions, job queue,\nstatus feedback"| OP

    QI -->|"Inspection measurements,\nNCR decisions"| MES
    MES -->|"Inspection plans, SPC alerts,\nquality dashboards"| QI

    PM -->|"Schedule adjustments,\ncapacity constraints"| MES
    MES -->|"OEE reports, production KPIs,\nshift summaries"| PM

    ME -->|"Downtime reason codes,\nmaintenance work orders"| MES
    MES -->|"Equipment health alerts,\nMTTF/MTTR metrics"| ME

    WMS -->|"Inventory availability,\ngoods receipt confirmations"| MES
    MES -->|"Material withdrawal requests,\ncomponent consumption"| WMS
```

---

## Level 1 Data Flow Diagram (MES subsystems)

The Level 1 diagram decomposes the MES into its primary functional subsystems and shows how data flows among them and with external entities.

**MES Subsystems**

| Subsystem | Responsibility |
|-----------|---------------|
| Production Planning & Scheduling | Transforms ERP orders into dispatched work orders with time-phased schedules |
| Production Execution | Tracks work order progress, operator interactions, and cycle times |
| Quality Management | Manages inspection plans, SPC charting, and non-conformance lifecycle |
| Material Tracking | Maintains real-time WIP inventory, lot/serial genealogy, and component traceability |
| IoT Data Pipeline | Ingests, filters, contextualizes, and routes machine telemetry |
| OEE Analytics | Calculates Availability, Performance, and Quality metrics per work center |
| ERP Integration | Bidirectional synchronization with SAP PP, QM, MM, and PM modules |
| Traceability Engine | Builds and queries full production genealogy records |

```mermaid
flowchart TB
    ERP["SAP ERP"]
    SCADA["SCADA / DCS"]
    IoT["IoT Sensors"]
    OP["Production Operator"]
    QI["Quality Inspector"]
    PM["Plant Manager"]
    WMS["WMS"]

    subgraph MES ["MES Subsystems"]
        PPS["Production Planning\n& Scheduling"]
        PE["Production Execution"]
        QM["Quality Management"]
        MT["Material Tracking"]
        IDP["IoT Data Pipeline"]
        OEE["OEE Analytics"]
        EI["ERP Integration"]
        TE["Traceability Engine"]

        DS_WO[("Work Order Store")]
        DS_RT[("Real-Time Event Log")]
        DS_QD[("Quality Data Store")]
        DS_MAT[("Material Ledger")]
        DS_TS[("Time-Series DB")]
        DS_OEE[("OEE Metrics Store")]
        DS_TRACE[("Traceability Store")]
    end

    ERP <-->|"Orders / Confirmations"| EI
    EI -->|"Planned orders"| PPS
    PE -->|"Confirmations, scrap, yield"| EI

    PPS -->|"Dispatched work orders"| DS_WO
    DS_WO -->|"Active work orders"| PE

    SCADA -->|"Machine events"| IDP
    IoT -->|"Raw telemetry"| IDP
    IDP -->|"Contextualized events"| DS_RT
    DS_RT -->|"Machine states"| PE
    DS_RT -->|"Process parameters"| QM
    DS_RT -->|"Sensor streams"| DS_TS
    DS_TS -->|"Aggregated metrics"| OEE

    OP -->|"Execution events"| PE
    PE -->|"Production records"| DS_RT
    PE -->|"Component consumption"| MT
    PE -->|"Serial/lot assignments"| TE

    QI -->|"Inspection results"| QM
    QM -->|"SPC data, NCRs"| DS_QD
    DS_QD -->|"Quality disposition"| PE
    DS_QD -->|"Quality records"| TE

    MT -->|"Material movements"| DS_MAT
    WMS <-->|"Inventory sync"| MT
    DS_MAT -->|"Material genealogy"| TE

    TE -->|"Genealogy records"| DS_TRACE
    DS_TRACE -->|"Traceability queries"| PM

    OEE -->|"KPI dashboards"| PM
    DS_OEE -->|"Shift reports"| PM
```

---

## Level 2 Data Flow Diagrams (one each for: Production Execution, Quality Management, Material Tracking, IoT Data Pipeline)

### Production Execution

The Production Execution subsystem manages the lifecycle of a work order from release through completion. It coordinates operator interactions, machine state changes, and component consumption to generate a complete production record.

```mermaid
flowchart TB
    OP["Production Operator"]
    SCADA_PE["SCADA / DCS"]

    DS_WO[("Work Order Store")]
    DS_RT[("Real-Time Event Log")]
    DS_MAT[("Material Ledger")]
    DS_TRACE[("Traceability Store")]

    subgraph PE ["Production Execution Processes"]
        P1["Receive & Validate\nWork Order"]
        P2["Dispatch to\nWork Center"]
        P3["Record Operation\nStart / Stop"]
        P4["Capture Component\nConsumption"]
        P5["Record Output\nQuantity & Scrap"]
        P6["Calculate Cycle\nTime & Efficiency"]
        P7["Generate Production\nConfirmation"]
    end

    DS_WO -->|"Released work order"| P1
    P1 -->|"Validated work order"| P2
    P2 -->|"Dispatched order + instructions"| OP
    OP -->|"Start signal + operator ID"| P3
    SCADA_PE -->|"Machine run / idle state"| P3
    P3 -->|"Operation timestamp events"| DS_RT
    OP -->|"Component barcode / RFID scans"| P4
    P4 -->|"Lot / serial consumption"| DS_MAT
    P4 -->|"BOM traceability link"| DS_TRACE
    OP -->|"Finished quantity + scrap reason"| P5
    P5 -->|"Output record"| DS_RT
    P5 -->|"Yield data"| P6
    DS_RT -->|"Operation durations"| P6
    P6 -->|"Cycle time record"| DS_RT
    P6 -->|"OEE Performance input"| DS_RT
    P6 -->|"Completion trigger"| P7
    P7 -->|"Production confirmation"| DS_WO
    P7 -->|"SAP-bound confirmation"| DS_RT
```

### Quality Management

The Quality Management subsystem enforces inspection plans, evaluates measurements against specifications, manages SPC control charts, and drives the non-conformance lifecycle through disposition and corrective action.

```mermaid
flowchart TB
    QI["Quality Inspector"]
    OP_Q["Production Operator"]
    SPC_FEED["IoT / In-Process Sensors"]

    DS_QD[("Quality Data Store")]
    DS_SPC[("SPC Chart Store")]
    DS_NCR[("NCR / CAPA Store")]
    DS_WO_Q[("Work Order Store")]

    subgraph QM_PROC ["Quality Management Processes"]
        Q1["Retrieve Inspection\nPlan"]
        Q2["Trigger Inspection\nEvent"]
        Q3["Capture Measurement\nData"]
        Q4["Evaluate Against\nSpecification"]
        Q5["Update SPC\nControl Chart"]
        Q6["Detect Control\nLimit Violations"]
        Q7["Raise Non-Conformance\nReport (NCR)"]
        Q8["Disposition &\nCorrective Action"]
        Q9["Release or\nQuarantine Lot"]
    end

    DS_WO_Q -->|"Active work order"| Q1
    Q1 -->|"Inspection plan + sampling rules"| Q2
    Q2 -->|"Inspection trigger"| QI
    Q2 -->|"In-process check trigger"| OP_Q
    SPC_FEED -->|"Continuous measurements"| Q3
    QI -->|"Manual measurement values"| Q3
    OP_Q -->|"Attribute checks"| Q3
    Q3 -->|"Raw measurement record"| DS_QD
    Q3 -->|"Measurement values"| Q4
    Q4 -->|"Pass / fail result"| DS_QD
    Q4 -->|"Chart data point"| Q5
    Q5 -->|"Updated control chart"| DS_SPC
    Q5 -->|"Statistical signals"| Q6
    Q6 -->|"Control violation alert"| Q7
    Q4 -->|"Out-of-spec result"| Q7
    Q7 -->|"NCR record"| DS_NCR
    Q7 -->|"NCR notification"| QI
    QI -->|"Disposition decision"| Q8
    Q8 -->|"CAPA record"| DS_NCR
    Q8 -->|"Disposition result"| Q9
    Q9 -->|"Lot status update"| DS_QD
    Q9 -->|"Release / quarantine signal"| DS_WO_Q
```

### Material Tracking

The Material Tracking subsystem maintains real-time visibility of WIP inventory, enforces FIFO/FEFO consumption rules, records lot and serial genealogy, and synchronizes stock movements with the Warehouse Management System.

```mermaid
flowchart TB
    OP_MT["Production Operator"]
    WMS_MT["Warehouse Management System"]
    PE_MT["Production Execution"]

    DS_MAT_L[("Material Ledger")]
    DS_LOT[("Lot / Serial Registry")]
    DS_TRACE_MT[("Traceability Store")]
    DS_WO_MT[("Work Order Store")]

    subgraph MT_PROC ["Material Tracking Processes"]
        M1["Receive Material\nfrom Warehouse"]
        M2["Assign Lot / Serial\nNumbers"]
        M3["Stage Components\nto Work Center"]
        M4["Record Component\nIssue to Order"]
        M5["Track In-Process\nInventory"]
        M6["Record Output\nLot / Serial"]
        M7["Backflush or\nExplicit Consumption"]
        M8["Synchronize to\nWarehouse System"]
    end

    WMS_MT -->|"Goods receipt with lot data"| M1
    M1 -->|"Received material record"| DS_MAT_L
    M1 -->|"Lot master created"| M2
    M2 -->|"Lot / serial assignment"| DS_LOT
    DS_WO_MT -->|"Component requirements"| M3
    DS_MAT_L -->|"Available stock"| M3
    M3 -->|"Staged material list"| OP_MT
    OP_MT -->|"Scan confirmation"| M4
    PE_MT -->|"BOM pick list"| M4
    M4 -->|"Issue record"| DS_MAT_L
    M4 -->|"Genealogy link (component to order)"| DS_TRACE_MT
    DS_MAT_L -->|"WIP stock snapshot"| M5
    M5 -->|"Real-time WIP balance"| DS_MAT_L
    PE_MT -->|"Finished quantity"| M6
    M6 -->|"Output lot / serial record"| DS_LOT
    M6 -->|"Finished goods traceability"| DS_TRACE_MT
    DS_WO_MT -->|"BOM explosion"| M7
    M7 -->|"Backflush consumption"| DS_MAT_L
    M7 -->|"Consumption record"| DS_TRACE_MT
    DS_MAT_L -->|"Goods movement transactions"| M8
    M8 -->|"Inventory update"| WMS_MT
```

### IoT Data Pipeline

The IoT Data Pipeline ingests raw sensor telemetry from the plant floor, applies edge filtering and contextualization, detects machine state transitions, and routes enriched events to the appropriate MES subsystems.

```mermaid
flowchart TB
    SENSORS["IoT Sensors\n(OPC-UA / MQTT)"]
    SCADA_IDP["SCADA / DCS\n(OPC-UA DA/HDA)"]
    EDGE["Edge Gateway\n(Industrial PC)"]

    DS_TS_IDP[("Time-Series DB\n(TimescaleDB)")]
    DS_RT_IDP[("Real-Time Event Log")]
    DS_REF[("Equipment\nReference Data")]

    subgraph IDP_PROC ["IoT Data Pipeline Processes"]
        I1["Receive Raw\nTelemetry"]
        I2["Schema Validate\n& Normalize"]
        I3["Apply Edge\nFilter / Deadband"]
        I4["Enrich with\nEquipment Context"]
        I5["Detect Machine\nState Changes"]
        I6["Calculate Derived\nMetrics"]
        I7["Persist Time-Series\nData"]
        I8["Publish Contextualized\nEvents"]
    end

    SENSORS -->|"Raw MQTT payloads"| EDGE
    SCADA_IDP -->|"OPC-UA data items"| EDGE
    EDGE -->|"Filtered telemetry"| I1
    I1 -->|"Raw message"| I2
    I2 -->|"Normalized record"| I3
    I3 -->|"Significant change event"| I4
    DS_REF -->|"Equipment master + tag mapping"| I4
    I4 -->|"Enriched telemetry event"| I5
    I5 -->|"State transition event\n(Running / Idle / Fault)"| DS_RT_IDP
    I5 -->|"State change"| I6
    I4 -->|"Time-stamped values"| I7
    I7 -->|"Persisted telemetry"| DS_TS_IDP
    I6 -->|"Availability/Performance inputs"| DS_TS_IDP
    I4 -->|"Enriched event"| I8
    I8 -->|"Contextualized machine events"| DS_RT_IDP
```

---

## Data Store Descriptions

| Data Store | Technology | Contents | Retention | Access Pattern |
|------------|-----------|----------|-----------|---------------|
| Work Order Store | PostgreSQL | Production orders, operations, work center assignments, status transitions | 7 years (regulatory) | OLTP read/write; indexed on work center, order status, date range |
| Real-Time Event Log | Apache Kafka + PostgreSQL | Machine state transitions, operator events, production records | 90 days hot; archive to S3 cold | High-throughput append; consumer-group replay; partition by work center |
| Quality Data Store | PostgreSQL | Inspection plans, measurement results, SPC data points, NCR records | 10 years (ISO/TS 16949) | Read-heavy for SPC trending; write at inspection completion |
| SPC Chart Store | TimescaleDB | Control chart time-series, Western Electric rule evaluations | 5 years | Time-range queries; hypertable partitioned by characteristic and work center |
| NCR / CAPA Store | PostgreSQL | Non-conformance reports, dispositions, corrective actions, effectiveness reviews | 10 years | Document-style CRUD; full-text search on description and root cause fields |
| Material Ledger | PostgreSQL | Stock movements, WIP balances, consumption records, goods movements | 7 years | Double-entry ledger; balance queries by storage location and lot |
| Lot / Serial Registry | PostgreSQL | Lot masters, serial number assignments, status, expiry dates, supplier info | 10 years | Lookup by lot or serial number; parent-child hierarchy traversal |
| Traceability Store | PostgreSQL (with graph extension) | Production genealogy, component-to-finished-goods links, process parameter snapshots | 10 years | Graph traversal for forward and backward traceability queries |
| Time-Series DB | TimescaleDB | Sensor telemetry, OPC-UA tag values, derived process metrics | 1 year hot; S3 cold | Continuous aggregates; time-bucket queries; hypertable compression at 7 days |
| OEE Metrics Store | TimescaleDB | Availability, Performance, Quality, and OEE per shift and work center | 3 years | Dashboard queries; shift-level and daily aggregates; rolling 12-month trend |
| Equipment Reference Data | PostgreSQL | Work center masters, tag-to-equipment mappings, alarm thresholds | Perpetual (master data) | Low-frequency read; entire reference set cached in Redis at startup |

---

## Data Flow Security Controls

### Transport Security

All data flows crossing network boundaries use TLS 1.3 as the minimum transport security. MQTT broker connections require mutual TLS (mTLS) with client certificates issued by the plant PKI. OPC-UA sessions use X.509 certificate authentication with message signing and encryption configured to **Basic256Sha256** security policy or higher.

Internal service-to-service communication within the Kubernetes cluster is secured by Istio service mesh mTLS, enforced by PeerAuthentication policies requiring mutual authentication for all pod-to-pod traffic.

### Authentication and Authorization

| Flow | Authentication Method | Authorization |
|------|-----------------------|---------------|
| Operator → MES UI | OIDC / OAuth 2.0 via Azure AD SSO | Role-based: Operator, Quality Inspector, Supervisor, Plant Manager, Admin |
| MES → SAP ERP | RFC / SOAP with service account + mTLS | SAP authorization objects scoped per RFC function group |
| IoT Sensors → Edge Gateway | X.509 device certificates | Device registry allowlist; per-topic ACL enforced on MQTT broker |
| Edge Gateway → MES Core | mTLS + signed JWT (short-lived, 15 min) | API Gateway validates JWT claims; scope-based route authorization |
| MES → WMS | REST API + OAuth 2.0 client credentials | Scoped to inventory read and goods-movement write only |
| Internal Services | Istio mTLS + SPIFFE SVID | Service account authorization via Kubernetes RBAC and Istio AuthorizationPolicy |

### Data Integrity Controls

- **Event immutability**: All events written to the Real-Time Event Log (Kafka) are append-only. Log compaction is disabled for audit-critical topics; retention is time-based, not size-based.
- **Cryptographic audit trail**: Production confirmations and NCR closure records carry a SHA-256 hash of the record payload, stored alongside the record in the database to detect unauthorized modification.
- **Input validation**: All API endpoints validate incoming payloads against registered OpenAPI schemas. Numeric measurements are range-checked against specification limits before persistence.
- **Duplicate detection**: The IoT Data Pipeline uses idempotency keys (device ID + timestamp + sequence number) to detect and discard duplicate sensor events at the ingestion stage, preventing double-counting in OEE calculations.
- **Outbox pattern**: Cross-domain state changes (e.g., production completion triggering material backflush) use the transactional outbox pattern to guarantee exactly-once event publication relative to the database write.

### Data Classification

| Classification | Examples | Controls |
|---------------|---------|----------|
| Restricted | ERP service credentials, PKI private keys, Vault root token | HSM or Vault storage; never in application config files or container images |
| Confidential | Production recipes, quality specifications, customer traceability data | Encrypted at rest (AES-256); access audit log; role-restricted API endpoints |
| Internal | Work orders, OEE metrics, material movements | Role-based access control; encrypted in transit; standard audit logging |
| Operational | Machine telemetry, event timestamps, state changes | Encrypted in transit; integrity-checked via message signing at edge |

### Regulatory and Compliance Flows

For regulated industries (automotive IATF 16949, aerospace AS9100), the following additional controls apply to specific data flows:

- **Electronic signatures**: Critical quality decisions — lot disposition, NCR closure, recipe parameter changes — require a second authenticator (password re-entry or hardware token) captured as part of the audit record, satisfying 21 CFR Part 11 equivalent requirements.
- **Data lineage**: The Traceability Engine maintains an immutable link from every finished serial number back through all contributing component lots, process parameters, operator IDs, and quality measurements, satisfying full forward and backward traceability obligations.
- **Change control**: Modifications to inspection plans, SPC specifications, or recipe parameters are versioned. The prior version, change author, timestamp, and change justification are retained permanently in the Quality Data Store. Active recipes cannot be modified; a new version must be created and explicitly activated.
- **Data residency**: All raw production data, quality records, and traceability information remain on-premises within the plant network boundary. Only aggregated and anonymized OEE trend data is replicated to cloud analytics infrastructure.
