# Data Flow Diagrams

Data flow diagrams (DFDs) showing how data moves through the **Resource Lifecycle Management Platform** for each major functional area.

---

## DFD Level 0 – Platform Overview

```mermaid
flowchart LR
  subgraph Inputs["External Inputs"]
    ActorReq["Actor Commands\n(Requestor, Custodian,\nManager, Finance, Ops)"]
    ScannerIn["Scanner Input\n(Asset Tag Scans)"]
    ERPIn["ERP / CMDB\n(Asset Master Data)"]
    ScheduledJobs["Scheduled Jobs\n(Overdue Detector,\nReconciliation, Archive)"]
  end

  RLMP["RLMP\nPlatform"]

  subgraph Outputs["External Outputs"]
    Notifications["Notifications\n(Email, SMS, Push)"]
    FinancialEvents["Financial Events\n(Ledger Charges,\nDeposit Releases)"]
    AuditStream["Audit / SIEM Stream\n(All Domain Events)"]
    Reports["Reports\n(Utilization, Settlement,\nCompliance)"]
    Archive["Archive\n(Cold Storage Records)"]
  end

  ActorReq --> RLMP
  ScannerIn --> RLMP
  ERPIn --> RLMP
  ScheduledJobs --> RLMP

  RLMP --> Notifications
  RLMP --> FinancialEvents
  RLMP --> AuditStream
  RLMP --> Reports
  RLMP --> Archive
```

---

## DFD Level 1 – Command Processing Flow

```mermaid
flowchart TD
  Actor(["Actor"]) --> GW["API Gateway\n• JWT Validation\n• Rate Limiting"]
  GW --> CmdRouter["Command Router\n• Parse request\n• Select handler"]

  CmdRouter --> AuthZ["Authorization Check\n• RBAC scope\n• Role eligibility"]
  AuthZ -->|"Deny"| Error["Error Response\n401 / 403"]
  AuthZ -->|"Allow"| PolicyEval["Policy Engine\n• Quota check\n• Eligibility\n• Priority rules"]
  PolicyEval -->|"Deny"| Error422["Error Response 422\nPolicy Denied"]
  PolicyEval -->|"Permit"| StateMachine["State Machine\n• Transition guard\n• Execute command\n• Compute delta"]
  StateMachine -->|"Invalid transition"| Error409["Error Response 409\nInvalid State"]
  StateMachine -->|"Valid"| PersistState["Write State\n(PostgreSQL)\nOptimistic lock"]
  PersistState --> WriteOutbox["Write Outbox Record\n(Same transaction)"]
  PersistState --> WriteAudit["Write Audit Record\n(Same transaction)"]
  WriteOutbox --> OutboxRelay["Outbox Relay Job"]
  OutboxRelay --> EventBus["Event Bus (Kafka)"]
  EventBus --> Consumers["Event Consumers\n(Workers)"]
  PersistState --> Response["Success Response\n200 / 201"]
  Response --> Actor
```

---

## DFD Level 1 – Read / Query Flow

```mermaid
flowchart LR
  Actor(["Actor"]) --> GW["API Gateway"]
  GW --> QueryRouter["Query Router"]
  QueryRouter --> SearchSvc["Search Service\n(Elasticsearch)"]
  QueryRouter --> ReportSvc["Report Service\n(Read Replica)"]
  QueryRouter --> AuditSvc["Audit API\n(PostgreSQL - Audit table)"]

  SearchSvc --> SearchIdx[("Search Index")]
  ReportSvc --> ReadReplica[("Read Replica")]
  AuditSvc --> AuditDB[("Audit Records")]

  SearchIdx --> SearchResults["Catalog / Availability\nSearch Results"]
  ReadReplica --> ReportData["Report / Dashboard\nData"]
  AuditDB --> AuditTrail["Audit Trail\nResponse"]

  SearchResults & ReportData & AuditTrail --> Actor
```

---

## DFD Level 1 – Event Processing Flow

```mermaid
flowchart TB
  EventBus["Event Bus (Kafka)"] --> TopicRouter["Topic Router\n• rlmp.resource.*\n• rlmp.reservation.*\n• rlmp.allocation.*\n• rlmp.incident.*\n• rlmp.settlement.*"]

  TopicRouter --> NotifWorker["Notification Worker\n• Render template\n• Deliver via Notif Service"]
  TopicRouter --> IndexWorker["Search Index Worker\n• Update availability index\n• Upsert catalog entry"]
  TopicRouter --> AuditWorker["Audit Worker\n• Write immutable log\n• Forward to SIEM"]
  TopicRouter --> SettleWorker["Settlement Worker\n• Trigger charge calculation\n• Post to ledger outbox"]
  TopicRouter --> OverdueWorker["Overdue Worker\n• Track SLA timers\n• Trigger escalation events"]
  TopicRouter --> ArchiveWorker["Archive Worker\n• Move records to cold storage\n• Write manifest"]

  NotifWorker --> NotifSvc["Notification Service\n(External)"]
  IndexWorker --> Elasticsearch["Elasticsearch Index"]
  AuditWorker --> SIEM_dest["SIEM (External)"]
  SettleWorker --> Ledger_dest["Financial Ledger\n(External)"]
  OverdueWorker --> EventBus
  ArchiveWorker --> S3["Object Storage\n(Archive)"]

  NotifWorker & IndexWorker & AuditWorker & SettleWorker & OverdueWorker & ArchiveWorker -->|"Failure"| DLQ["Dead Letter Queue"]
  DLQ --> OpsAlert["Ops Alert\n+ Manual Replay"]
```

---

## DFD Level 2 – Allocation Write Path (Detail)

```mermaid
flowchart TD
  Client["Client (Requestor)"] --> API["/POST /reservations\nwith idempotency_key"]
  API --> IdempCheck["Idempotency Check\n(Redis)"]
  IdempCheck -->|"Hit"| CachedResp["Return Cached Response"]
  IdempCheck -->|"Miss"| LockAcquire["Acquire Optimistic Lock\non resource_id + window\n(PostgreSQL SELECT FOR UPDATE SKIP LOCKED)"]
  LockAcquire --> OverlapQuery["SELECT overlapping\nCONFIRMED reservations"]
  OverlapQuery -->|"Conflict"| Return409["Return 409 + Alternatives"]
  OverlapQuery -->|"No conflict"| QuotaCheck["Policy Engine: Quota\nSELECT count(active reservations)\nWHERE requestor_id = ?"]
  QuotaCheck -->|"Exceeds"| Return422["Return 422"]
  QuotaCheck -->|"OK"| InsertReservation["INSERT reservation\nINSERT outbox record\nINSERT audit record\n(Single transaction)"]
  InsertReservation --> CommitTx["COMMIT"]
  CommitTx --> SetCache["Cache idempotency key\n(Redis, TTL=24h)"]
  SetCache --> StartSLATimer["Enqueue SLA Timer Job\n(due at sla_due_at)"]
  StartSLATimer --> Return201["Return 201 + reservation_id"]
```

---

## Data Stores Summary

| Store | Technology | Data | Access Pattern |
|---|---|---|---|
| Primary DB | PostgreSQL | All entity records, outbox, audit log | Serializable writes; read queries via ORM |
| Read Replica | PostgreSQL replica | Projections, reports | Read-only; eventual consistency ~1 s lag |
| Search Index | Elasticsearch | Resource catalog, availability windows | Full-text + filter queries |
| Cache | Redis | Policy decisions (60 s TTL), idempotency keys (24 h TTL), session tokens | Key-value get/set |
| Event Bus | Kafka | All domain events | Publish/subscribe; replay from offset |
| Cold Storage | S3 / GCS | Archived resource records, manifests | Write once; read rarely (compliance) |

---

## Cross-References

- Event catalog (all events): [../analysis/event-catalog.md](../analysis/event-catalog.md)
- Sequence diagrams (flow timing): [system-sequence-diagrams.md](./system-sequence-diagrams.md)
- ERD (data store schema): [../detailed-design/erd-database-schema.md](../detailed-design/erd-database-schema.md)
