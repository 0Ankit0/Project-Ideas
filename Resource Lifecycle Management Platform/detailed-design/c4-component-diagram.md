# C4 Component Diagram

Detailed C4 Level 3 component diagram for the **Core API** container of the Resource Lifecycle Management Platform, showing all internal components, their responsibilities, and communication interfaces.

---

## Core API Container – Internal Component View

```mermaid
flowchart TB
  subgraph Router["HTTP Router Layer"]
    HTTPRouter["HTTP Router\n(Express / Chi)\nRoute matching + middleware chain"]
    AuthMW["Auth Middleware\nJWT decode + role extraction"]
    RateLimitMW["Rate Limit Middleware\nPer-tenant / per-user counters"]
    LogMW["Logging Middleware\nStructured JSON + correlation ID injection"]
  end

  subgraph Controllers["Controller Layer (one per domain)"]
    ProvCtrl["Provisioning Controller\nPOST /resources\nPOST /resources/bulk"]
    AllocCtrl["Allocation Controller\nPOST /reservations\nDELETE /reservations/{id}"]
    CustCtrl["Custody Controller\nPOST /allocations\n/checkin /force-return /transfer /extend"]
    IncidentCtrl["Incident Controller\nGET/POST /incidents\nPATCH /incidents/{id}\nPOST /incidents/{id}/resolve"]
    SettleCtrl["Settlement Controller\n/approve /dispute /void"]
    DecomCtrl["Decommission Controller\nPOST /resources/{id}/decommission"]
    AuditCtrl["Audit Controller\nGET /audit/resources/{id}"]
    SearchCtrl["Search Controller\nGET /resources"]
  end

  subgraph AppServices["Application Services"]
    ProvSvc["ProvisioningService\n• template validation\n• bulk import\n• policy check"]
    AllocSvc["AllocationService\n• overlap check\n• priority ordering\n• SLA timer setup"]
    CustSvc["CustodyService\n• condition delta\n• incident trigger\n• overdue register"]
    InciSvc["IncidentService\n• case lifecycle\n• severity routing"]
    SetSvc["SettlementService\n• rate card calc\n• ledger outbox"]
    DecomSvc["DecommissionOrchestrator\n• precondition checks\n• approval workflow"]
    AuditSvc["AuditService\n• read audit trail\n• hash verification"]
  end

  subgraph CrossCut["Cross-Cutting Components"]
    CmdHandler["CommandHandler\n• schema validation\n• idempotency check\n• command dispatch"]
    StateMachine["StateMachineEngine\n• transition graph\n• guard evaluation\n• compensation logic"]
    PolicyAdapter["PolicyEngineAdapter\n• OPA client\n• decision cache (60s)\n• quota evaluation"]
    OutboxPub["OutboxPublisher\n• write outbox record\n• same-tx guarantee"]
    AuditWriter["AuditWriter\n• compute hash chain\n• write audit_event\n• same-tx guarantee"]
    IdempStore["IdempotencyStore\n• Redis GET/SET\n• TTL = 24h"]
  end

  subgraph Infra["Infrastructure Adapters"]
    PGRepo["PostgreSQL Repository\n• entity CRUD\n• optimistic locking\n• partition-aware queries"]
    RedisClient["Redis Client\n• policy cache\n• idempotency keys\n• session state"]
    ESClient["Elasticsearch Client\n• catalog search\n• availability queries"]
    OPAClient["OPA Client (sidecar)\nport 8181\n• policy evaluation\n• rule version lookup"]
  end

  HTTPRouter --> AuthMW --> RateLimitMW --> LogMW
  LogMW --> Controllers
  Controllers --> CmdHandler
  CmdHandler --> IdempStore
  CmdHandler --> AppServices
  AppServices --> PolicyAdapter
  AppServices --> StateMachine
  StateMachine --> PGRepo
  StateMachine --> OutboxPub
  StateMachine --> AuditWriter
  PolicyAdapter --> RedisClient
  PolicyAdapter --> OPAClient
  OutboxPub --> PGRepo
  AuditWriter --> PGRepo
  SearchCtrl --> ESClient
  AuditCtrl --> PGRepo
  IdempStore --> RedisClient
```

---

## Component Responsibilities

| Component | Responsibility | Key Dependency |
|---|---|---|
| HTTP Router | Route matching, middleware chain | Express / Chi framework |
| Auth Middleware | Extract and validate JWT claims; attach `actorContext` to request | Identity Provider (cached JWKS) |
| Rate Limit Middleware | Per-tenant and per-user counter enforcement | Redis |
| Controller | Parse HTTP request; call command handler; format HTTP response | Application Service |
| CommandHandler | Schema validation; idempotency check; select correct service | IdempotencyStore, Application Services |
| StateMachineEngine | Enforce state graph transitions; call guards; execute command; call outbox and audit publishers | PostgreSQL Repository, OutboxPublisher, AuditWriter |
| PolicyEngineAdapter | Send policy requests to OPA; cache decisions for 60 s; handle OPA unavailability | OPA Sidecar, Redis |
| OutboxPublisher | Write outbox record in same transaction as entity mutation | PostgreSQL (same connection) |
| AuditWriter | Compute SHA-256 hash chain entry; write immutable audit_event | PostgreSQL (same connection) |
| IdempotencyStore | Redis-backed idempotency key cache (24 h TTL) | Redis |
| PostgreSQL Repository | All entity persistence; optimistic locking; partition-aware | PostgreSQL 15 |

---

## Key Internal Contracts

### CommandHandler → StateMachineEngine

```
Input:  TransitionCommand { entity_id, command_name, payload, actor_context, idempotency_key }
Output: TransitionResult  { new_state, version, emitted_events[] }
Throws: TransitionError   { current_state, reason, error_code }
```

### StateMachineEngine → PolicyEngineAdapter

```
Input:  PolicyRequest { action, resource_id, requestor_id, tenant_id, window, quota_context }
Output: PolicyDecision { decision: PERMIT | DENY, matched_rule_id, reason }
```

### StateMachineEngine → OutboxPublisher + AuditWriter

Both are called within the same database transaction:
```
outboxPub.publish(event, connection)   // writes to outbox table
auditWriter.write(record, connection)  // writes to audit_events table
// transaction committed by StateMachineEngine
```

---

## Cross-References

- Container-level C4 view: [../high-level-design/c4-diagrams.md](../high-level-design/c4-diagrams.md)
- Class diagrams (method signatures): [class-diagrams.md](./class-diagrams.md)
- Lifecycle orchestration (transition logic): [lifecycle-orchestration.md](./lifecycle-orchestration.md)
