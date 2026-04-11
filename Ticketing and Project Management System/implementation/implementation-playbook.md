# Implementation Playbook - Ticketing and Project Management System

## 1. Delivery Goal
Build a production-ready hybrid platform that lets clients report issues with evidence while internal teams plan, execute, verify, and report delivery from the same operational system.

## 2. Recommended Delivery Workstreams
- Identity, access, and tenant scoping
- Ticket intake, attachments, comments, and timelines
- Triage, assignment, and SLA automation
- Project, milestone, task, and dependency management
- QA verification, release management, and reopen workflow
- Reporting, notifications, audit, and observability

## 3. Suggested Execution Order
1. Establish identity, organization scoping, and role templates.
2. Implement ticket creation, attachment handling, and timelines.
3. Add triage, assignment, and SLA policies.
4. Implement projects, milestones, tasks, and cross-linking to tickets.
5. Add QA verification, release grouping, and reopen logic.
6. Complete dashboards, exports, notifications, and audit tooling.

## 4. Release-Blocking Validation
- Unit coverage for workflow transitions, priority logic, and SLA timers
- Integration coverage for ticket-to-milestone and ticket-to-release traceability
- Security validation for tenant isolation and attachment access control
- Load and resilience validation for queues, uploads, search, and notifications
- Backup, restore, and audit-log retention verification

## 5. Go-Live Checklist
- [ ] Role matrix and scoped permissions validated
- [ ] High-severity ticket workflow tested end to end
- [ ] Milestone replanning and change-request flow validated
- [ ] Attachment malware scan and retention policies enabled
- [ ] Dashboards, alerts, and runbooks enabled
- [ ] Deployment rollback and recovery rehearsed

## 6. Core Runtime Design Deep-Dive

### 6.1 Workflow Engine Transition Guards

| Transition | Guard Set (all required) | Failure Code |
|---|---|---|
| `new -> triaged` | reporter org matches ticket org; mandatory classification complete; anti-automation risk check passed | `WF_TRIAGE_GUARD_FAILED` |
| `triaged -> assigned` | assignee has skill tag match; assignee active/on-call; ticket not already in conflicting assignment transaction | `WF_ASSIGN_GUARD_FAILED` |
| `assigned -> in_progress` | assignee acknowledgment present; no blocking dependency unresolved unless override reason supplied | `WF_START_GUARD_FAILED` |
| `in_progress -> ready_for_qa` | implementation checklist complete; linked subtasks closed; required evidence attachments clean-scanned | `WF_QA_READY_GUARD_FAILED` |
| `ready_for_qa -> closed` | QA pass result recorded; release marker set for releasable types; no open severity escalation child tickets | `WF_CLOSE_GUARD_FAILED` |
| `closed -> reopened` | reopen reason code required; actor authorized; reopened within policy window or manager override present | `WF_REOPEN_GUARD_FAILED` |

Guard evaluation order: **permission -> invariants -> dependency checks -> side-effect preflight**. Guard failures return deterministic error payloads and emit `TransitionRejected` audit events.

### 6.2 Permission Evaluation Path
1. API gateway authenticates principal and injects `subject`, `tenant`, `session`, `mfa_level`.
2. Policy middleware loads role bindings and dynamic attributes (team membership, project scope, emergency mode).
3. Domain permission engine evaluates:
   - **RBAC rule set** (static role capability)
   - **ABAC predicates** (tenant, ownership, data sensitivity, ticket visibility)
   - **Contextual constraints** (time window, freeze window, approval lock)
4. Field-level filters applied to response DTOs before serialization.
5. Decision is logged as `AuthorizationEvaluated` event with allow/deny reason and policy version hash.

### 6.3 SLA Timer Processing
- SLA engine persists canonical deadlines in UTC with source calendar and pause windows.
- Timer wheel worker processes deadlines from priority queue in 30-second buckets.
- On each tick:
  1. Pull due timers (`next_due_at <= now + 30s`).
  2. Recompute effective remaining time from event history (pause/resume/priority change).
  3. Emit one of: `SlaNearBreach`, `SlaBreached`, `SlaRecovered`.
  4. Schedule next checkpoint idempotently.
- Drift controls:
  - NTP-synchronized nodes; monotonic clock for elapsed calculations.
  - Max tolerated scheduling drift: 5s per 10 minutes.
  - If drift exceeds threshold, mark timer `degraded_clock` and escalate to ops.

### 6.4 Audit Event Schema (Canonical)

| Field | Type | Notes |
|---|---|---|
| `event_id` | UUID | globally unique |
| `event_type` | string | e.g., `TicketAssigned`, `TransitionRejected` |
| `occurred_at` | timestamp(UTC) | producer time |
| `ingested_at` | timestamp(UTC) | audit pipeline time |
| `tenant_id` | UUID | multitenancy boundary |
| `actor` | object | `{type,id,role,ip,user_agent}` |
| `entity` | object | `{type,id,version}` |
| `correlation_id` | UUID/string | request tracing |
| `idempotency_key` | string | replay-safe writes |
| `before` | JSONB | redacted prior state snapshot |
| `after` | JSONB | redacted resulting state snapshot |
| `reason_code` | string/null | required for privileged/reopen/override actions |
| `policy_version` | string | auth/workflow policy hash |
| `signature` | string | optional tamper-evidence signature |

## 7. Implementation Milestones with Definition of Done (DoD)

| Milestone | Modules | Definition of Done |
|---|---|---|
| M1: Identity & Access Foundation | auth service, role templates, tenant scoping, audit writer | SSO + MFA enforced; RBAC/ABAC policy tests passing; deny-path events visible in audit stream |
| M2: Ticket Intake & Attachments | ticket service, comment service, attachment service, malware scanner | Create/update/comment flows live; attachment states enforced (`pending/clean/quarantined`); signed URL policy validated |
| M3: Workflow & Assignment Engine | workflow engine, assignment policy, notification orchestrator | Guard matrix fully implemented; stale assignment detector enabled; reassignment audit trail immutable |
| M4: SLA & Escalations | SLA engine, timer worker, escalation notifier | deterministic timer recompute; breach/near-breach events emitted; escalation ACK flow tested |
| M5: Project Planning Integration | project/milestone modules, dependency resolver, cross-link service | ticket↔task↔milestone traceability complete; blocker propagation and replanning workflows operational |
| M6: Search, Reporting, and Ops Hardening | projection workers, OpenSearch, dashboards, runbooks | projection lag SLO met; KPI definitions codified; backup/restore + incident game day completed |

## 8. Test Strategy Coverage Map

| Module | Unit | Integration | Contract | E2E | Non-Functional |
|---|---|---|---|---|---|
| Workflow engine | transition guards, conflict detection | state persistence + outbox | transition API errors | triage→close lifecycle | chaos retries, concurrency races |
| Permission engine | RBAC/ABAC predicates | identity provider + org graph | response redaction contract | user role journey tests | penetration tests, authZ latency |
| SLA processing | deadline math, pause/resume | queue/timer worker with DB | SLA event payload schema | breach/escalation scenario | clock drift soak, load burst |
| Attachment pipeline | metadata validation | upload→scan→download | signed URL and scan webhook | client upload + internal download | malware simulation, large file tests |
| Search/indexing | mapper/projection logic | outbox→OpenSearch pipeline | query/filter API contracts | keyword search from ticket UI | reindex timing + relevance checks |
| Notifications | routing policy | provider adapters + callbacks | delivery status contracts | user receives escalation paths | provider throttle and failover tests |

## 9. Migration and Backfill Plan (Historical Tickets & Comments)
1. **Inventory & profiling**: classify legacy sources, record schema variants, identify corrupt/partial records.
2. **Canonical mapping spec**: map old statuses/priorities/users to new enums and IDs; define irreversible transforms.
3. **Dry-run extraction**: export to staging, compute row counts and hash totals per entity type.
4. **Backfill pipeline**:
   - load organizations/users/projects first,
   - load tickets with created/updated timestamps preserved,
   - load comments chronologically with author mapping,
   - attach legacy files with `legacy_unscanned` state until scan completion.
5. **Dual-write/dual-read window** (optional by cutover strategy): compare critical queries across old/new systems.
6. **Validation gates**:
   - count parity by tenant and month,
   - sampled timeline parity (ticket + comment ordering),
   - SLA recomputation parity on historical high-severity tickets.
7. **Cutover**: freeze legacy writes, perform delta load, run smoke tests, switch routing.
8. **Post-cutover monitoring**: 7-day hypercare dashboard for migration anomalies and attachment scan lag.

**Rollback posture**
- Keep legacy system read-only for at least one release cycle.
- Maintain reversible ID crosswalk tables.
- Snapshot new system before cutover delta load for rapid restore if parity thresholds fail.

## Cross-Cutting Workflow and Operational Governance

### Implementation Playbook: Document-Specific Scope
- Primary focus for this artifact: **delivery phases, rollout gates, and operational readiness checks**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
- For this document, workflow guidance must **enforce state semantics in code paths, tests, and release gates**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
- For this document, SLA guidance must **implement recomputable SLA engine behavior and regression coverage**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
- For this document, permission guidance must **verify API/UI authorization parity using contract tests**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
- For this document, reporting guidance must **ship dashboards-as-code and data quality tests in CI**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
- For this document, operational guidance must **wire executable runbooks to deployment and incident response gates**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (IMPLEMENTATION_IMPLEMENTATION_PLAYBOOK)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `implementation/implementation-playbook.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |
