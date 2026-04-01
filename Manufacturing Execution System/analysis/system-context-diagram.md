# System Context Diagram

## Overview

This document presents the C4 Model Level-1 (Context) view of the **Manufacturing Execution System (MES)**. The context diagram establishes the system boundary and illustrates every significant human and system interaction. It is the highest-level architectural view, deliberately abstract — focusing on *who* uses the MES and *which external systems* it communicates with, without exposing internal components.

The MES is the central digital nervous system of the production plant, bridging the enterprise layer (ERP) with the shop-floor control layer (SCADA/PLC) and providing a single source of truth for all manufacturing execution activities — production order management, work order execution, quality management, downtime tracking, and genealogy/traceability.

---

## C4 Context Diagram

```mermaid
C4Context
    title System Context: Manufacturing Execution System (MES)

    %% ── People ──────────────────────────────────────────────────────────
    Person(PS, "Production Supervisor", "Plans production schedules, releases orders, monitors KPIs, performs shift handover, resolves exceptions.")
    Person(MO, "Machine Operator", "Executes work orders at HMI, records material consumption, reports downtime, acknowledges work instructions.")
    Person(QI, "Quality Inspector", "Records inspection results, manages SPC, initiates quality holds, approves lot disposition.")
    Person(MT, "Maintenance Technician", "Logs downtime root causes, creates and executes maintenance work orders, verifies equipment restart.")
    Person(PM, "Plant Manager", "Views real-time OEE and production KPIs, reviews shift reports, approves major deviations.")

    %% ── Central System ───────────────────────────────────────────────────
    System(MES, "Manufacturing Execution System", "Orchestrates shop-floor execution: production order management, work order dispatch, quality management, downtime tracking, material genealogy, and integration with enterprise and control systems.")

    %% ── External Systems ────────────────────────────────────────────────
    System_Ext(SAP, "SAP ERP", "Enterprise planning system: pushes production orders, BOMs, and routings; receives production confirmations, goods receipts, and goods issues.")
    System_Ext(SCADA, "SCADA / PLC System", "Plant-floor control layer: streams real-time machine telemetry (speed, temperature, faults); receives production parameters and recipe setpoints from MES.")
    System_Ext(LIMS, "Quality Lab System (LIMS)", "Laboratory Information Management System: shares inspection results and COA data with MES; receives inspection requests for lab-based tests.")
    System_Ext(WMS, "Warehouse Management System", "Manages physical stock movements: receives material staging requests from MES; confirms goods availability and putaway completion.")
    System_Ext(HRS, "HR / Labor System", "Maintains employee master data, shift schedules, and skills certifications; MES queries for operator qualification validation.")
    System_Ext(PI, "OSIsoft PI Historian", "Time-series process data archive: MES forwards machine telemetry for long-term storage; MES queries historian for SPC trending and process analytics.")
    System_Ext(BI, "Business Intelligence Platform", "Reporting and analytics layer (e.g., Power BI / Tableau): queries MES data via reporting API for OEE dashboards, quality scorecards, and capacity analyses.")

    %% ── Relationships: People → MES ─────────────────────────────────────
    Rel(PS, MES, "Manages production orders, schedules, shift handover, exception handling", "HTTPS / Browser + Mobile")
    Rel(MO, MES, "Starts/completes work orders, records consumption and downtime, views work instructions", "HTTPS / HMI Touch Terminal")
    Rel(QI, MES, "Records inspection results, manages inspection plans, initiates holds, views SPC", "HTTPS / Tablet / Desktop")
    Rel(MT, MES, "Creates maintenance work orders, logs downtime codes, updates equipment status", "HTTPS / Mobile App")
    Rel(PM, MES, "Views OEE dashboards, production KPIs, shift summaries (read-only analytical access)", "HTTPS / Browser")

    %% ── Relationships: MES ↔ External Systems ────────────────────────────
    BiRel(MES, SAP, "Receives: production orders, BOMs, routings, material masters. Sends: production confirmations, goods receipts, goods issues, activity times", "RFC/BAPI + REST (every 5 min / event-driven)")
    BiRel(MES, SCADA, "Receives: machine telemetry, fault codes, cycle counts. Sends: recipe parameters, setpoints, production schedules to PLC", "OPC-UA (1 Hz – 100 Hz)")
    BiRel(MES, LIMS, "Sends: inspection requests for lab analysis. Receives: lab results and certificates of analysis", "REST API (event-driven)")
    BiRel(MES, WMS, "Sends: material staging requests, backflush confirmations. Receives: stock availability confirmations, transfer order completions", "REST API (event-driven)")
    Rel(MES, HRS, "Queries employee data, shift schedules, operator skill certifications for qualification checks", "REST API (on-demand)")
    Rel(MES, PI, "Forwards machine telemetry for long-term archival; queries historical process data for SPC analysis", "PI Web API / AF SDK (continuous + on-demand)")
    Rel(BI, MES, "Queries production, quality, and downtime data for reporting and dashboards", "REST Reporting API / OData (scheduled + on-demand)")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## System Boundary Definition

### In Scope (MES Responsibilities)

| Capability | Description |
|---|---|
| Production Order Management | Receive, validate, schedule, and track production orders from creation through technical completion |
| Work Order Dispatch | Generate and assign operation-level work orders to work centers and operators |
| Shop Floor Execution | Support operator start/complete transactions, material scanning, work instruction display |
| Quality Management | Inspection plan management, in-process and final inspection recording, SPC charting, lot disposition |
| Downtime Management | Downtime event recording, classification, OEE calculation, maintenance work order generation |
| Material Genealogy & Traceability | Lot and serial number tracking through every operation; full forward and backward traceability |
| Shift Management | Shift scheduling, shift handover workflows, per-shift KPI reporting |
| ERP Integration | Bidirectional data exchange with SAP for orders, confirmations, and material movements |
| SCADA Integration | OPC-UA data collection from PLCs; recipe/setpoint delivery to machine controllers |
| Reporting & Analytics API | Expose aggregated production, quality, and OEE data to BI platforms |

### Out of Scope (Handled by Adjacent Systems)

| Capability | Handled By |
|---|---|
| Demand planning and production scheduling beyond 1-week horizon | SAP PP (Production Planning) |
| Physical lab analysis and certificate of analysis generation | LIMS |
| Warehouse slotting, pick-path optimization, forklift management | WMS |
| Preventive maintenance scheduling and asset management | CMMS (SAP PM) |
| Payroll and workforce scheduling | HR System |
| Long-term process data archival (> 3 months) | OSIsoft PI Historian |
| Financial accounting and cost center management | SAP FI/CO |
| Quality management system (CAPA, audit management, document control) | eQMS |

---

## Integration Points Detail

| System | Protocol | Direction | Data Exchanged | Frequency | Authentication |
|---|---|---|---|---|---|
| SAP ERP | RFC/BAPI + REST | Bidirectional | **In:** Production orders, BOMs, routings, material masters, customer orders. **Out:** Production confirmations, goods receipts, goods issues, activity confirmations | Every 5 min (batch) + event-driven on completion | OAuth 2.0 (client credentials) + TLS 1.3 |
| SCADA/PLC | OPC-UA | Bidirectional | **In:** Machine telemetry (speed RPM, temperature °C, pressure bar, cycle count, fault codes). **Out:** Recipe parameters, target setpoints, production parameters, material IDs | 1 Hz (telemetry) up to 100 Hz (high-speed signals) | OPC-UA security policy: Sign & Encrypt, X.509 certificates |
| LIMS | REST API (JSON) | Bidirectional | **In:** Lab test results (CoA), analytical measurement data. **Out:** Inspection requests, sample metadata, test specifications | Event-driven (on inspection trigger) | API key + TLS 1.3 |
| WMS | REST API (JSON) | Bidirectional | **In:** Stock availability confirmation, transfer order status. **Out:** Material staging requests, backflush goods-issue confirmations | Event-driven | OAuth 2.0 + TLS 1.3 |
| HR / Labor System | REST API (JSON) | Read-only (MES reads) | Employee IDs, roles, shift assignments, skill/qualification records, certifications | On-demand (at login, operator assignment) | Service account + TLS 1.3 |
| OSIsoft PI Historian | PI Web API / AF SDK | Bidirectional | **To PI:** Machine telemetry forwarding, process parameter values. **From PI:** Historical data queries for SPC trend analysis | Continuous write; on-demand read | Kerberos / integrated Windows authentication |
| BI Platform | OData / REST Read-only API | Read-only (BI reads MES) | Production KPIs, OEE metrics, downtime events, quality summaries, order status | Scheduled (hourly) + on-demand | OAuth 2.0 bearer token |

---

## Data Flow Descriptions

### SAP ERP ↔ MES

```mermaid
flowchart LR
    SAP["🖥️ SAP ERP"]
    MES["🏭 MES"]

    SAP -- "1. Production Order + BOM + Routing\n[REST POST /api/v1/production-orders]\nEvery 5 min polling or on PP confirmation" --> MES
    SAP -- "2. Material Master updates\n[REST PATCH /api/v1/materials]\nOn-demand delta sync" --> MES
    MES -- "3. Production Confirmation\n[BAPI CO_SE_BACKFLUSH_GOODSMOV]\nOn order technical completion" --> SAP
    MES -- "4. Goods Issue (Component Consumption)\n[BAPI MB_CREATE_GOODS_MOVEMENT]\nPer operation backflush" --> SAP
    MES -- "5. Goods Receipt (Finished Product)\n[BAPI MIGO_GR]\nOn order completion" --> SAP
    MES -- "6. Activity Confirmation (Labor + Machine time)\n[BAPI CO_SE_COMPLETION_CONFIRM]\nOn order completion" --> SAP
```

### SCADA/PLC ↔ MES

```mermaid
flowchart LR
    PLC["⚙️ SCADA / PLC"]
    MES["🏭 MES"]

    PLC -- "1. Machine Telemetry Stream\nOPC-UA NodeID subscriptions\nSpeed, Temp, Pressure, Cycle Count\n1 Hz continuous" --> MES
    PLC -- "2. Fault / Alarm Events\nOPC-UA events on state change\nFault code + description" --> MES
    MES -- "3. Recipe Parameters\nOPC-UA write on work order start\nTarget speed, temperature setpoints" --> PLC
    MES -- "4. Production Schedule Signal\nMaterial ID, target quantity, lot number\nOPC-UA write" --> PLC
    MES -- "5. Quality Hold Signal\nHalt production flag\nOPC-UA write on quality hold trigger" --> PLC
```

### MES → OSIsoft PI Historian

```mermaid
flowchart LR
    MES["🏭 MES"]
    PI["📈 PI Historian"]
    BI["📊 BI Platform"]

    MES -- "Forward machine telemetry\nPI buffered write\nAuto-tagging by work center + material" --> PI
    MES -- "Forward quality measurement values\nPer inspection characteristic\nLinked to lot and order" --> PI
    PI -- "Historical process data query\nPI Web API\nFor SPC trend analysis in MES" --> MES
    PI -- "Long-term archived data\nPI AF structured data\nFor advanced analytics" --> BI
```

---

## Key Architectural Constraints

| Constraint | Description | Impact |
|---|---|---|
| **Real-time OEE** | OEE must be updated within 30 seconds of any machine state change (SCADA event). | MES must maintain a persistent OPC-UA subscription and process events asynchronously without blocking the main transaction pipeline. |
| **ERP as System of Record** | SAP ERP remains the system of record for production orders, material masters, and BOMs. MES holds a synchronized replica. | MES must handle ERP data conflicts gracefully; order of precedence is always ERP > MES for master data. |
| **Offline capability** | HMI terminals at work centers must continue to accept start/complete transactions for up to 30 minutes during network outage. | MES HMI layer requires a local transaction buffer with sync-on-reconnect capability. |
| **Data retention** | Production records must be retained in MES for a minimum of 5 years online (queryable) and 10 years archived. | Database partitioning strategy required; archival tier must support query-by-lot-number and query-by-date. |
| **Security zones** | SCADA/PLC network and enterprise network are in separate security zones (ISA/IEC 62443 compliant). MES acts as a DMZ system with controlled communication paths. | Network segmentation required; all SCADA communication via a dedicated OPC-UA server in the MES DMZ. |
| **Multi-plant capability** | MES must support multiple production plants under a single instance (multi-tenant data model). | All data entities are plant-scoped; users are assigned to one or more plants; reporting can aggregate cross-plant. |

---

## Deployment Context

```mermaid
flowchart TD
    subgraph Enterprise["🏢 Enterprise Network (Zone 4)"]
        SAP["SAP ERP"]
        HRS["HR System"]
        BI["BI Platform"]
        LIMS["LIMS"]
    end

    subgraph DMZ["🔒 MES DMZ (Zone 3)"]
        MESAPP["MES Application Server\n(Active/Passive HA)"]
        MESDB["MES Database Cluster\n(PostgreSQL HA)"]
        OPCPROXY["OPC-UA Proxy Server"]
        APIGTW["API Gateway\n(OAuth 2.0)"]
    end

    subgraph ShopFloor["🏭 Shop Floor Network (Zone 2)"]
        HMI1["HMI Terminal — WC-01"]
        HMI2["HMI Terminal — WC-02"]
        HMIN["HMI Terminal — WC-N"]
        SCADA["SCADA Server"]
        PLC1["PLC — Line 1"]
        PLC2["PLC — Line 2"]
    end

    subgraph Field["⚙️ Field Level (Zone 1)"]
        MACHINE1["Machine — Line 1"]
        MACHINE2["Machine — Line 2"]
    end

    SAP <-->|"RFC/REST\nTLS 1.3"| APIGTW
    HRS -->|"REST\nTLS 1.3"| APIGTW
    BI -->|"OData\nTLS 1.3"| APIGTW
    LIMS <-->|"REST\nTLS 1.3"| APIGTW
    APIGTW <--> MESAPP
    MESAPP <--> MESDB
    MESAPP <-->|"PI Web API"| PI["OSIsoft PI"]
    MESAPP <-->|"OPC-UA\nEncrypted"| OPCPROXY
    OPCPROXY <-->|"OPC-UA"| SCADA
    SCADA <--> PLC1
    SCADA <--> PLC2
    PLC1 <--> MACHINE1
    PLC2 <--> MACHINE2
    HMI1 <-->|"HTTPS"| MESAPP
    HMI2 <-->|"HTTPS"| MESAPP
    HMIN <-->|"HTTPS"| MESAPP
```

---

## Assumptions and Dependencies

| ID | Assumption / Dependency | Risk if Not Met |
|---|---|---|
| DEP-01 | SAP ERP production planning runs at least once per day to push new production orders. | MES will have stale or missing order data; production supervisor must create orders manually. |
| DEP-02 | All production machines have PLC controllers with OPC-UA server capability (or classic OPC bridged via gateway). | Without SCADA integration, OEE machine availability data must be entered manually — significant data quality risk. |
| DEP-03 | LIMS is capable of receiving inspection requests via REST API and returning structured result payloads. | Lab results must be manually transcribed into MES — slower cycle time and transcription error risk. |
| DEP-04 | WMS maintains real-time stock availability and can respond to staging requests within 5 minutes. | Material shortages will not be detected until the operator attempts to scan materials at the work center. |
| DEP-05 | HR system provides a REST API for employee and skills data queries. | MES cannot validate operator qualifications; work center assignment becomes a purely manual process. |
| DEP-06 | Network connectivity between MES DMZ and shop floor network is high-reliability (dual links, <10 ms latency). | HMI responsiveness degrades; offline buffer scenarios become more frequent. |

---

## Security Architecture

The MES spans multiple ISA/IEC 62443 security zones and must enforce strict access controls both internally and at integration boundaries.

### Security Zone Model

```mermaid
flowchart TD
    subgraph Z4 ["Zone 4 — Enterprise (IT)"]
        SAP_S["SAP ERP"]
        LIMS_S["LIMS"]
        BI_S["BI Platform"]
        HRS_S["HR System"]
    end

    subgraph Z3 ["Zone 3 — Site Operations (OT-IT DMZ)"]
        APIGW_S["API Gateway\nOAuth 2.0 / TLS 1.3\nRate limiting / WAF"]
        MESAPP_S["MES Application\nServers (HA Pair)"]
        MESDB_S["MES Database\nCluster (Encrypted)"]
        OPCPRX_S["OPC-UA Proxy\nCertificate-based auth"]
        PI_S["Historian Connector"]
    end

    subgraph Z2 ["Zone 2 — Control (OT)"]
        HMI_S["HMI Terminals\nHTTPS — cert-pinned"]
        SCADA_S["SCADA Server\nOPC-UA server"]
    end

    subgraph Z1 ["Zone 1 — Field (OT)"]
        PLC_S["PLCs\nOPC-UA embedded server"]
        MACHINE_S["Production Machines"]
    end

    Z4 <-->|"Firewall FW-1\nWhitelist RFC/REST only"| Z3
    Z3 <-->|"Firewall FW-2\nOPC-UA + HTTPS only"| Z2
    Z2 <-->|"Firewall FW-3\nPLC protocol only"| Z1
    SAP_S --> APIGW_S
    APIGW_S --> MESAPP_S
    MESAPP_S --> MESDB_S
    MESAPP_S --> OPCPRX_S
    OPCPRX_S --> SCADA_S
    SCADA_S --> PLC_S
    PLC_S --> MACHINE_S
    HMI_S --> APIGW_S
```

### Authentication and Authorization Matrix

| Actor / System | Authentication Method | Session Management | Authorization Model |
|---|---|---|---|
| Production Supervisor | SSO (SAML 2.0) + MFA | 8-hour session, idle lock at 15 min | RBAC — `PROD_SUPERVISOR` role |
| Machine Operator | Badge scan (RFID) + PIN | 4-hour session, idle lock at 5 min | RBAC — `OPERATOR` role, work-center scoped |
| Quality Inspector | SSO (SAML 2.0) + MFA | 8-hour session | RBAC — `QA_INSPECTOR` role |
| Maintenance Technician | Mobile app + SSO | 4-hour session, idle lock at 10 min | RBAC — `MAINTENANCE_TECH` role |
| Plant Manager | SSO (SAML 2.0) + MFA | 8-hour session | RBAC — `PLANT_MANAGER` read-only role |
| SAP ERP | OAuth 2.0 client credentials | Token refresh every 3,600 s | Service account — `ERP_INTEGRATION` scope |
| SCADA/PLC | OPC-UA X.509 certificate | Certificate validity 1 year | OPC-UA security policy: Sign & Encrypt |
| LIMS | API key in header | Stateless | IP whitelist + API key |
| BI Platform | OAuth 2.0 bearer token | Token TTL 3,600 s | Read-only `REPORTING_API` scope |

---

## Scalability and High-Availability Design

```mermaid
flowchart TD
    LB["Load Balancer\nActive–Active\nHealth-check interval: 10 s"] --> MES_A["MES App Server A\nPrimary"]
    LB --> MES_B["MES App Server B\nSecondary"]
    MES_A --> DB_P["PostgreSQL Primary\nSync replication"]
    MES_B --> DB_P
    DB_P -->|"Streaming replication\nRPO < 1 s"| DB_S["PostgreSQL Standby\nAuto-failover via Patroni"]
    MES_A --> CACHE["Redis Cluster\nSession store\nWork queue cache"]
    MES_B --> CACHE
    MES_A --> MQ["Message Queue\nRabbitMQ / Kafka\nERP + SCADA integration events"]
    MES_B --> MQ
    MQ --> INT_WORKER["Integration Workers\nERP posting\nSCADA data ingestion\nHistorian forwarding"]
```

| HA Requirement | Target | Mechanism |
|---|---|---|
| Application uptime | 99.9% (scheduled hours) | Active–Active app servers behind load balancer |
| Database RPO | < 1 second | PostgreSQL synchronous streaming replication |
| Database RTO | < 2 minutes | Patroni auto-failover |
| HMI offline resilience | 30 minutes local buffering | IndexedDB local transaction buffer in HMI browser app |
| ERP integration retry | Up to 3 retries at 5-minute intervals | Dead letter queue for failed ERP postings |
| OPC-UA subscription recovery | Automatic reconnect within 30 seconds | OPC-UA client session watchdog |

---

## Regulatory and Compliance Context

The MES must satisfy the following regulatory frameworks depending on the industry vertical:

| Framework | Applicability | MES-Specific Requirements |
|---|---|---|
| **ISO 9001:2015** | All manufacturing industries | Quality management records, inspection traceability, CAPA linkage |
| **FDA 21 CFR Part 11** | Pharmaceutical / medical device manufacturing | Electronic records, audit trail, electronic signatures for quality disposition |
| **EU GMP Annex 11** | Pharmaceutical EU operations | Computer system validation, backup/recovery, audit trail completeness |
| **ISA/IEC 62443** | All OT/IT environments | Security zone segregation, access control, patch management |
| **ISO 22400** | KPI standardization | OEE calculation methodology, KPI definitions aligned with standard |
| **IATF 16949** | Automotive manufacturing | PPAP integration, SPC requirements, process traceability |

### Audit Trail Requirements

```mermaid
flowchart LR
    ACT["User/System Action"] --> AUD["Audit Log Entry"]
    AUD --> FIELDS["Fields recorded:\n• Timestamp UTC\n• Actor ID + Role\n• Action type\n• Entity type + ID\n• Before value\n• After value\n• IP address / terminal ID\n• Session ID"]
    FIELDS --> STORE["Immutable audit store\nAppend-only table\nNo update/delete permitted"]
    STORE --> RET["Retention:\n5 years online\n10 years archive"]
    STORE --> EXPORT["Export API:\nAudit report generation\nFor regulatory inspection"]
```

