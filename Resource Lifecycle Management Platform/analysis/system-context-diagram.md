# System Context Diagram

High-level view of the **Resource Lifecycle Management Platform** and all external systems, users, and integrations it interacts with.

## Context Description

The RLMP is the central system of record for asset lifecycle management. It sits between human actors (requestors, managers, custodians, compliance, finance, operations) and a set of external technical systems (identity provider, financial ledger, SIEM, notification delivery, and integrating enterprise systems).

---

## System Context Diagram (C4 Level 1)

```mermaid
flowchart TB
  %% People
  Requestor(["👤 Requestor\nEmployee who reserves\nand uses resources"])
  Custodian(["👤 Custodian\nHolds physical/logical\ncustody of assets"])
  Manager(["👤 Resource Manager\nManages catalog,\npolicies, approvals"])
  Compliance(["👤 Compliance Officer\nAudit trails, retention\npolicy management"])
  Finance(["👤 Finance\nSettlement review\nand charge posting"])
  Ops(["👤 Operations / SRE\nPlatform monitoring,\nforced returns, DLQ"])

  %% Central System
  RLMP["🖥️ Resource Lifecycle\nManagement Platform\n\nProvisioning · Reservation\nAllocation · Custody\nOverdue Detection\nSettlement · Decommissioning"]

  %% External Systems
  IAM["🔐 Identity Provider\n(OAuth 2.0 / OIDC)\nAuthentication &\nRole Management"]
  Ledger["💰 Financial Ledger\nReceives deposit holds,\ncharges, and refunds\nas domain events"]
  SIEM["🔍 SIEM / Audit Store\nReceives all domain\nevents for compliance\nand security monitoring"]
  Notif["📬 Notification Service\nEmail · SMS · Push\nDelivery for reminders,\nalerts, and escalations"]
  ERP["🏢 ERP / CMDB\nSource of asset data,\ncost centres, and\npurchase orders"]
  Barcode["📷 Barcode / RFID Scanner\nHardware used by\ncustodians for checkout\nand check-in scans"]

  %% Actor → RLMP
  Requestor -->|"Search catalog,\ncreate/cancel reservations,\ndispute charges"| RLMP
  Custodian -->|"Checkout, check-in,\ntransfer custody,\nreport loss"| RLMP
  Manager -->|"Provision resources,\nset policies,\ndecommission approval"| RLMP
  Compliance -->|"Pull audit trails,\nmanage retention rules"| RLMP
  Finance -->|"Review settlements,\napprove/dispute charges"| RLMP
  Ops -->|"Monitor events,\nforced return,\nDLQ replay"| RLMP

  %% RLMP → External Systems
  RLMP -->|"Validate JWT,\nlookup user roles"| IAM
  RLMP -->|"Publish financial events\nvia outbox (exactly-once)"| Ledger
  RLMP -->|"Stream all domain events\nfor compliance & SIEM"| SIEM
  RLMP -->|"Send reminders,\nalerts, escalations"| Notif
  RLMP -->|"Import asset data,\ncost centre sync"| ERP
  Barcode -->|"Asset tag scan\ntriggers checkout/checkin\ncommand"| RLMP
```

---

## External System Descriptions

| External System | Protocol / Integration | Data Exchanged | Criticality |
|---|---|---|---|
| **Identity Provider** | OAuth 2.0 / OIDC (JWT) | User identity, role claims, group memberships | Critical – all API calls require valid JWT |
| **Financial Ledger** | Async event (outbox → event bus) | Deposit holds, damage charges, refunds, reconciliation confirmations | High – financial integrity depends on this |
| **SIEM / Audit Store** | Event stream (Kafka / Kinesis) | All domain events with actor, correlation ID, timestamps | High – compliance and forensic audit |
| **Notification Service** | HTTP API / message queue | Reminder emails, SMS, push; escalation notifications | Medium – degraded-mode OK with retry |
| **ERP / CMDB** | REST API (inbound sync) | Asset master data, purchase orders, cost centres | Medium – sync at provisioning time |
| **Barcode / RFID Scanner** | Local HTTP or mobile app | Asset tag value triggering checkout/checkin commands | High – primary field interaction method |

---

## Trust Boundaries

```mermaid
flowchart LR
  subgraph Internet["Public Internet"]
    Browser["Web Browser\n/ Mobile App"]
    Scanner["Scanner App"]
  end
  subgraph DMZ["DMZ / API Gateway"]
    GW["API Gateway\nTLS Termination\nJWT Validation\nRate Limiting"]
  end
  subgraph Private["Private Application Network"]
    RLMP_Core["RLMP Core Services\n(Provisioning, Allocation,\nCustody, Incident,\nSettlement, Decommission)"]
    PolicySvc["Policy Engine"]
    EventBus["Event Bus (Kafka)"]
  end
  subgraph DataZone["Data Zone (Encrypted)"]
    Postgres["PostgreSQL\n(Primary Datastore)"]
    ColdStorage["Cold Storage\n(Archive)"]
  end
  subgraph ExtZone["External Integrations"]
    IAM_Ext["Identity Provider"]
    Ledger_Ext["Financial Ledger"]
    SIEM_Ext["SIEM"]
    Notif_Ext["Notification Service"]
  end

  Browser --> GW
  Scanner --> GW
  GW --> RLMP_Core
  RLMP_Core --> PolicySvc
  RLMP_Core --> Postgres
  RLMP_Core --> EventBus
  RLMP_Core --> ColdStorage
  GW --> IAM_Ext
  EventBus --> Ledger_Ext
  EventBus --> SIEM_Ext
  RLMP_Core --> Notif_Ext
```

---

## Integration Contract Summary

| Integration | Direction | Consistency Model | Failure Mode |
|---|---|---|---|
| Identity Provider | Inbound (token validation) | Synchronous, cached 60 s | Deny request if IAM unreachable; alert ops |
| Financial Ledger | Outbound (event) | Async, exactly-once via outbox | Queue events; retry with exponential backoff |
| SIEM | Outbound (event stream) | Async, at-least-once | Events queued; loss acceptable only if SIEM fully down |
| Notification Service | Outbound (event consumer) | Async, at-least-once | Retry with backoff; missed notification non-blocking |
| ERP / CMDB | Bidirectional (sync job) | Eventual, daily batch | Alert on sync failure; manual reconciliation available |
| Scanner | Inbound (command) | Synchronous | Retry via mobile app; offline mode stores scan locally |

---

## Cross-References

- Detailed service topology: [../high-level-design/architecture-diagram.md](../high-level-design/architecture-diagram.md)
- C4 Container and Component views: [../high-level-design/c4-diagrams.md](../high-level-design/c4-diagrams.md)
- Infrastructure topology: [../infrastructure/deployment-diagram.md](../infrastructure/deployment-diagram.md)
