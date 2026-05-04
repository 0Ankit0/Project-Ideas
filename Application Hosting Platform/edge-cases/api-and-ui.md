# Edge Cases: API and UI

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- API contracts: [`../detailed-design/api-design.md`](../detailed-design/api-design.md)
- Delivery workflow: [`../implementation/implementation-guidelines.md`](../implementation/implementation-guidelines.md)

## Scenario Set A: Concurrent Deployment Trigger from UI and CLI

### Trigger
A developer clicks **Deploy latest commit** in the web UI while an automation job triggers `ahp deploy` for the same application and environment within the same minute.

```mermaid
sequenceDiagram
  participant UI as Dashboard User
  participant CLI as CI/CLI
  participant API as Public API
  participant DEP as Deploy Service
  participant DB as Metadata DB

  UI->>API: POST /applications/{id}/deployments
  CLI->>API: POST /applications/{id}/deployments
  API->>DEP: Create deployment request A
  API->>DEP: Create deployment request B
  DEP->>DB: Check active rollout lock
  DB-->>DEP: Lock held by request A
  DEP-->>API: Reject request B with conflict metadata
  API-->>CLI: 409 deployment_in_progress + active deployment_id
  DEP->>DB: Continue request A
  DEP-->>API: Accepted
  API-->>UI: 202 Accepted
```

### Invariants
- Only one mutable rollout may target the same application and environment at a time.
- Rejected duplicate requests return the active `deployment_id` so clients can resume tracking instead of retrying blindly.

### Operational acceptance criteria
- Conflict response must be deterministic across web UI, CLI, and API clients.
- Audit log must show which actor acquired the rollout lock and which actor was rejected.

## Scenario Set B: Stale Dashboard State During Progressive Rollout

### Trigger
The dashboard polls deployment state from a lagging read replica while rollout decisions are written to the primary metadata store.

```mermaid
flowchart LR
  User[Operator opens deployment page] --> UI[Dashboard]
  UI --> ReadReplica[(Read Replica)]
  UI --> Events[SSE Status Stream]
  Control[Deploy Controller] --> Primary[(Primary DB)]
  Primary --> ReadReplica
  Control --> Events
  ReadReplica -->|lagging status| UI
  Events -->|authoritative status| UI
  UI --> Decision{Conflict between poll and stream?}
  Decision -->|Yes| Banner[Show stale-data banner + disable destructive actions]
  Decision -->|No| Normal[Render current status]
```

### Invariants
- Streaming rollout state is authoritative over eventually consistent list/poll endpoints.
- UI must suppress destructive actions such as rollback or cancel when state sources disagree.

### Operational acceptance criteria
- Replica lag greater than 5 seconds surfaces an explicit UI warning.
- Operators can still access raw deployment events and request IDs for support escalation.

## Scenario Set C: Deployment Log Stream Disconnect

### Trigger
Browser or CLI log stream disconnects during a build because of proxy timeout, browser tab suspension, or network blip.

```mermaid
sequenceDiagram
  participant Client as Browser/CLI
  participant GW as API Gateway
  participant Log as Log Stream Service
  participant Store as Log Buffer

  Client->>GW: GET /deployments/{id}/logs?follow=true&cursor=123
  GW->>Log: Open stream
  Log->>Store: Read buffered events > cursor
  Log-->>Client: Event stream
  Note over Client,GW: Network disconnect
  Client->>GW: Reconnect with last_seen_event_id
  GW->>Log: Resume from cursor
  Log->>Store: Replay missed events
  Log-->>Client: Backfilled stream + live tail
```

### Invariants
- Log events have monotonically increasing sequence IDs per deployment.
- Reconnect flow must be loss-aware; clients are never told “up to date” without replaying missed buffered events first.

### Operational acceptance criteria
- Buffered replay covers at least the last 15 minutes of deployment events.
- CLI and dashboard both expose reconnection status and whether any events were dropped.

## Scenario Set D: API Rate Limit Misclassification for Shared NAT or CI Runners

### Trigger
Multiple legitimate developers or CI jobs share a source IP and hit per-IP rate limits despite separate identities and applications.

```mermaid
flowchart TB
  Request[Authenticated request] --> Identity[Resolve actor, team, app, IP]
  Identity --> Policy[Rate-limit evaluator]
  Policy --> Decision{Identity quota or IP shield?}
  Decision -->|Actor/App budget OK| Allow[Allow request]
  Decision -->|Actor exceeds budget| Throttle[429 with reset metadata]
  Decision -->|IP abuse pattern only| Shield[Temporary IP shield + challenge]
  Shield --> Review[Security review queue]
```

### Invariants
- Primary rate-limit key is actor/team/app, not IP alone.
- Abuse protections may consider IP reputation, but must not collapse tenant isolation or cause cross-tenant throttling.

### Operational acceptance criteria
- Every 429 response includes `retry_after`, policy ID, and support correlation ID.
- Security analytics can distinguish abusive bot traffic from bursty but valid CI activity.

## Scenario Set E: Webhook Delivery Duplicate or Out-of-Order

### Trigger
Git provider retries a webhook after a transient timeout, resulting in duplicated or out-of-order delivery for push and pull-request events.

```mermaid
sequenceDiagram
  participant Git as Git Provider
  participant WH as Webhook Ingress
  participant Queue as Event Queue
  participant Proc as Event Processor
  participant DEP as Deploy Service

  Git->>WH: webhook event #42
  WH->>Queue: Enqueue with delivery_id
  Git->>WH: Retry event #42
  WH->>Queue: Deduplicate by delivery_id
  Git->>WH: Older event #41 arrives late
  WH->>Queue: Mark stale candidate
  Proc->>DEP: Compare repo SHA/order against current desired state
  DEP-->>Proc: Ignore stale event, keep newest desired revision
```

### Invariants
- Webhook processing is idempotent on provider delivery ID and repository revision.
- Late events cannot roll desired state backward once a newer revision is accepted.

### Operational acceptance criteria
- Duplicate suppression metrics are exposed per integration provider.
- Support tooling can reconstruct why a webhook was processed, ignored, or classified as stale.

---

**Status**: Complete  
**Document Version**: 2.0
