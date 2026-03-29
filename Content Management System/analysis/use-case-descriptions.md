# Use Case Descriptions

## Scope
Implementation-ready actor workflows including alternative and failure paths.

## Primary Use Cases
### UC-01 Create and Save Draft
**Actors:** Author, Editor delegate.  
**Preconditions:** Role contains `content:create`; feature `richEditor` enabled.
**Main Success Path:**
1. Author opens editor and creates draft.
2. Autosave persists revision every 20 seconds with optimistic concurrency token.
3. Validation service flags missing fields inline.
4. Draft preview renders against active theme container.

**Alternate Paths:**
- A1: Concurrency conflict -> client receives `409 VERSION_CONFLICT` and prompts merge.
- A2: Media upload virus flag -> attachment quarantined and draft marked `BLOCKED`.

### UC-04 Review, Approve, or Request Changes
**Actors:** Editor, Compliance Reviewer.
**Business Rules:** Two-person approval required for regulated categories.
**Postconditions:** Workflow task closed, status changed, audit snapshot written.

### UC-06 Schedule, Publish, and Rollback
**Actors:** Editor/Admin, Publishing Worker, SRE On-call.
**SLA:** 99% of scheduled publish jobs executed within ±30 seconds.
**Failure Handling:** If CDN invalidation fails twice, publish enters `PARTIAL_PUBLISH` and auto-rollback policy evaluates blast radius.


## Detailed Flow
1. Actor enters through UI/API with signed session and tenant context.
2. Application service orchestrates policy checks and aggregate commands.
3. Asynchronous orchestration schedules long-running processing.
4. Completion events update read models and user-facing status.
5. Operational alerts fire on SLA breach paths.

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
