# User Stories

## Scope
Prioritized, testable user stories with acceptance criteria and architecture links.

## Story Backlog (Implementation Ready)
### Story US-101 Draft Creation and Autosave
**As an** Author, **I want** automatic draft persistence, **so that** edits are never lost.
**Acceptance Criteria**
- Autosave interval configurable per tenant (default 20s).
- Every autosave creates immutable revision entry with editor client version.
- Concurrency conflict returns structured `409` with merge metadata.

### Story US-204 Editorial Approval Workflow
**As an** Editor, **I want** routed review tasks with SLA timers, **so that** publication deadlines are met.
**Acceptance Criteria**
- Reviewer assignment policy supports round-robin and skill-based routing.
- Escalation event emitted at 80% of SLA budget consumed.
- Decision action logs rationale and policy snapshot hash.

### Story US-307 Safe Rollback
**As an** Operations engineer, **I want** one-click rollback with validation gates, **so that** bad publishes are reversed safely.
**Acceptance Criteria**
- Rollback preview shows impacted routes, feeds, and cache keys.
- Rollback is blocked when target revision assets are unavailable.
- Completion event includes incident correlation id.

## Story Mapping to Delivery Artifacts
| Story | APIs | Data Model | Sequence | Test Focus |
|---|---|---|---|---|
| US-101 | `POST/PATCH /v1/content` | `content_item`, `content_revision` | Create Draft | concurrency + autosave idempotency |
| US-204 | `POST /v1/workflow/tasks/{id}/decision` | `workflow_task`, `review_comment` | Review Path | SLA timers + escalation |
| US-307 | `POST /v1/publications/{id}/rollback` | `publish_job`, `rollback_job` | Rollback Path | compensating actions |


## Detailed Flow
1. Validate request context, tenant scope, and feature toggles.
2. Execute business and policy checks before mutating state.
3. Persist transactional state and emit outbox/integration events.
4. Update projections, caches, and search indexes asynchronously.
5. Record audit evidence and SLO telemetry for operational governance.

## Component Responsibilities
| Component | Responsibilities | Key Decisions |
|---|---|---|
| API Gateway | Authentication, authorization, throttling, request validation | Enforce idempotency and version headers |
| Content Service | Aggregate commands, revision management, lifecycle transitions | Maintain invariant-safe transitions |
| Workflow Service | Task routing, SLA timers, escalation | Deterministic assignment and timeout behavior |
| Publishing Service | Render, publish, cache invalidation, rollback | Idempotent publish and compensating actions |
| Data Platform | Event projections, analytics, audit archive | Exactly-once processing and retention compliance |

## Schema-Level Examples
```sql
CREATE TABLE content_item (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  slug VARCHAR(180) NOT NULL,
  locale VARCHAR(10) NOT NULL DEFAULT 'en-US',
  status VARCHAR(40) NOT NULL,
  current_revision_id UUID NOT NULL,
  published_at TIMESTAMPTZ,
  created_by UUID NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE (tenant_id, locale, slug)
);

CREATE TABLE content_revision (
  id UUID PRIMARY KEY,
  content_id UUID NOT NULL REFERENCES content_item(id),
  version INT NOT NULL,
  body_json JSONB NOT NULL,
  checksum CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE (content_id, version)
);
```

```json
{
  "eventType": "content.status.changed",
  "eventVersion": 1,
  "tenantId": "0e0d08f3-2a5d-4d85-8f1d-5fce2abf913e",
  "contentId": "3c917a78-0cbf-4f07-97d7-8f94a4f2df80",
  "fromStatus": "PENDING_REVIEW",
  "toStatus": "PUBLISHED",
  "actorId": "dfe334d4-8a7d-4d52-b3ad-a1fb36aa0508",
  "occurredAt": "2026-03-28T09:15:00Z",
  "traceId": "7f1aa03bc7d7440a"
}
```

## Non-Functional Requirements
- **Availability:** Authoring plane 99.95% monthly; publishing pipeline 99.99%.
- **Performance:** p95 command latency < 350 ms; p95 read latency < 180 ms.
- **Scalability:** Handle 8x baseline publish spikes and 20x comment spikes.
- **Security:** OIDC + MFA for privileged users; signed asset URLs; immutable audit logs.
- **Reliability:** Outbox/inbox deduplication with idempotency keys for external side effects.
- **Operability:** SLO alerts for queue lag, task SLA breaches, cache invalidation failures.

## Cross-Document Traceability
- [Requirements](../requirements/requirements.md)
- [User Stories](../requirements/user-stories.md)
- [Use Case Descriptions](../analysis/use-case-descriptions.md)
- [API Design](../detailed-design/api-design.md)
- [ERD and Database Schema](../detailed-design/erd-database-schema.md)
- [Sequence Diagrams](../detailed-design/sequence-diagrams.md)
- [Deployment Diagram](../infrastructure/deployment-diagram.md)
- [Backend Status Matrix](../implementation/backend-status-matrix.md)
- [Edge Cases Index](../edge-cases/README.md)
