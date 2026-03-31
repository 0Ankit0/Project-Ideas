# Implementation Guidelines

Sprint-ready implementation guidance for the **Resource Lifecycle Management Platform** engineering teams.

---

## Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Runtime | Node.js (TypeScript) or Go | Node 20 LTS / Go 1.22 | Go preferred for allocation/state-machine hot path |
| Framework | Express (Node) / Chi (Go) | Latest stable | |
| ORM / SQL | Prisma (Node) / pgx (Go) | — | Raw SQL for hot paths with optimistic locking |
| Database | PostgreSQL | 15 | With `btree_gist` extension for range exclusion |
| Cache | Redis | 7 | Standalone for dev; Redis Cluster for prod |
| Event Bus | Apache Kafka | 3.7 | Topics: 12 partitions, replication factor 3 |
| Policy Engine | Open Policy Agent (OPA) | 0.65 | Sidecar deployment |
| Search | Elasticsearch | 8 | Single cluster, 3 nodes minimum |
| Container runtime | Docker + Kubernetes | K8s 1.29 | |
| IaC | Terraform + Helm | Terraform 1.8, Helm 3 | |
| CI/CD | GitHub Actions / GitLab CI | — | |
| Observability | OpenTelemetry → Datadog / Grafana | — | |
| Secret management | HashiCorp Vault / AWS Secrets Manager | — | |

---

## Project Structure

```
rlmp/
├── cmd/                          # Entry points (API server, worker, cron jobs)
│   ├── api/main.go
│   ├── worker/main.go
│   └── cron/main.go
├── internal/
│   ├── domain/                   # Pure domain logic (no external deps)
│   │   ├── resource/
│   │   │   ├── resource.go       # Aggregate
│   │   │   ├── state_machine.go  # Transition guards
│   │   │   └── events.go         # Domain events
│   │   ├── reservation/
│   │   ├── allocation/
│   │   ├── incident/
│   │   └── settlement/
│   ├── application/              # Use cases / command handlers
│   │   ├── provisioning/
│   │   ├── allocation/
│   │   ├── custody/
│   │   ├── incident/
│   │   └── settlement/
│   ├── infrastructure/           # Adapters (DB, cache, events, ext APIs)
│   │   ├── postgres/             # Repository implementations
│   │   ├── redis/                # Cache + idempotency
│   │   ├── kafka/                # Producer + consumer
│   │   ├── opa/                  # Policy engine client
│   │   └── elasticsearch/        # Search client
│   └── api/                      # HTTP handlers + DTOs
│       ├── handlers/
│       ├── middleware/
│       └── dto/
├── migrations/                   # SQL migration files (numbered)
├── policies/                     # OPA .rego policy files
├── helm/                         # Kubernetes Helm charts
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Coding Standards

### State Machine
- All state transitions MUST go through `StateMachineEngine.transition(entity, command)`.
- **Never** update entity `state` directly in application code.
- Guards must be pure functions (no I/O) to ensure testability.
- Every guard failure must return a typed `TransitionError` with `error_code` and `current_state`.

### Idempotency
- All command handlers MUST check the `Idempotency-Key` header before executing.
- Keys are stored in Redis with 24-hour TTL.
- Duplicate commands return the cached response without side effects.

### Transactional Outbox
- Outbox writes and entity state mutations MUST occur in the same database transaction.
- Never publish to Kafka directly from a command handler.
- The Outbox Relay Job runs every 1 second; it is the only path from state mutation to event bus.

### Optimistic Locking
```sql
-- Always include version in UPDATE WHERE clause
UPDATE resources 
SET state = $1, version = version + 1, updated_at = NOW()
WHERE resource_id = $2 AND version = $3;
-- If rowsAffected = 0: retry up to 3 times, then return 409 CONCURRENCY_CONFLICT
```

### Error Handling
```typescript
// All errors must be typed with error_code
throw new PlatformError({
  error_code: 'WINDOW_CONFLICT',
  http_status: 409,
  message: 'Reservation window conflicts with existing reservation',
  details: { conflicting_reservation_id: '...', alternatives: [] },
  correlation_id: ctx.correlationId
});
```

### Audit Trail
- `AuditWriter.write()` is called by the StateMachineEngine, not by application code.
- Never bypass audit writing.
- The `hash` field must be computed as `SHA-256(previous_hash + JSON.stringify(audit_record))`.

---

## Testing Strategy

| Test Type | Coverage Target | Tools | What to Test |
|---|---|---|---|
| Unit tests | ≥ 90% domain layer | Jest / Go test | State machine guards, domain aggregate methods, policy evaluation logic |
| Integration tests | All command handlers | Jest / Testcontainers | DB transactions, outbox writes, idempotency, concurrency (optimistic lock conflicts) |
| Contract tests | All external integrations | Pact | IAM token validation, Financial Ledger event schema, Notification Service API |
| E2E tests | Critical user journeys | Playwright / k6 | Provision → Reserve → Checkout → Checkin → Decommission full flow |
| Load tests | NFR targets | k6 | P95 < 500 ms command latency; 100,000 concurrent allocations |
| Chaos tests | Resilience | Chaos Monkey / Toxiproxy | DB unavailable, Kafka down, OPA sidecar restart |

### Key Test Scenarios

```
Scenario: Concurrent reservation conflict
  Given resource R is available
  When 50 concurrent clients POST /reservations for overlapping windows
  Then exactly 1 reservation is CONFIRMED
  And remaining 49 receive 409 with alternatives

Scenario: Idempotent checkout
  Given an active reservation
  When the same checkout command is submitted twice with the same idempotency_key
  Then the second request returns 201 with the original allocation_id
  And only one allocation record exists in the database

Scenario: Overdue detection accuracy
  Given 1000 active allocations, 100 of which passed due_at 6 minutes ago
  When the overdue detector runs
  Then exactly 100 allocations are marked OVERDUE
  And 100 rlmp.allocation.overdue events are published
  And no active allocation is incorrectly marked

Scenario: Decommission blocked by open settlement
  Given resource R with one PENDING settlement record
  When a decommission request is submitted
  Then the request is rejected with 409 DECOMMISSION_BLOCKED
  And settlement_id is listed in the blocking_entities response
```

---

## Quality Gates

| Gate | Criteria | Required Before |
|---|---|---|
| PR merge | All unit + integration tests pass; lint clean; no critical CodeQL alerts | Branch merge |
| Staging deploy | Load test P95 < 500 ms; security scan clean; rollback tested | Staging promotion |
| Production deploy | Runbook review; on-call handover; compliance attestation; smoke test pass | Production promotion |

---

## Security Guidelines

- Secrets in Vault / Secrets Manager only. No secrets in environment variables, config files, or logs.
- All HTTP endpoints require JWT. Audit queries additionally require `compliance` role.
- Database passwords rotated every 30 days via Vault dynamic secrets.
- TLS 1.3 minimum on all service-to-service and external communication.
- Elasticsearch access restricted to Core API and Search Indexer pods by network policy.
- Redis AUTH required; data encrypted at rest.
- OPA policy files are version-controlled and reviewed before deployment.

---

## Observability

### Metrics to Instrument
- `rlmp_command_duration_ms` (histogram) – labeled by `command_name`, `status`
- `rlmp_state_transitions_total` (counter) – labeled by `from_state`, `to_state`
- `rlmp_overdue_allocations` (gauge) – count of OVERDUE state allocations
- `rlmp_outbox_pending` (gauge) – pending outbox records
- `rlmp_policy_decision_duration_ms` (histogram) – OPA evaluation latency
- `rlmp_dlq_depth` (gauge) – DLQ message count per queue

### Alerts
| Alert | Condition | Severity | Runbook |
|---|---|---|---|
| High command latency | P95 > 1000 ms for 5 min | High | runbooks/high-latency.md |
| Outbox relay lag | Pending outbox > 100 for > 2 min | High | runbooks/outbox-lag.md |
| DLQ depth | DLQ > 10 messages | High | runbooks/dlq-replay.md |
| Overdue rate spike | Overdue count increases > 50% in 1 h | Medium | runbooks/overdue-spike.md |
| Settlement reconciliation mismatch | Daily reconciliation discrepancy > 0 | Critical | runbooks/settlement-mismatch.md |

---

## Cross-References

- Backend status matrix: [backend-status-matrix.md](./backend-status-matrix.md)
- API design: [../detailed-design/api-design.md](../detailed-design/api-design.md)
- Edge cases (build-time considerations): [../edge-cases/README.md](../edge-cases/README.md)
