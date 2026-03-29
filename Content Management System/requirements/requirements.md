# Requirements

## Scope
Baseline functional and non-functional requirements with direct traceability to design artifacts.

## Functional Requirements
### Content Lifecycle
- **FR-CNT-001** Draft authoring with autosave, version history, and conflict detection.
- **FR-CNT-002** Editorial review queue with delegation, comments, and SLA timers.
- **FR-CNT-003** Multi-channel publishing (`web`, `rss`, `amp`) with publish preview.
- **FR-CNT-004** Controlled rollback to prior revision with cache/feed repair.

### Platform and Operations
- **FR-OPS-001** Multi-tenant isolation for data, cache keys, and search indexes.
- **FR-OPS-002** Zero-downtime migrations for schema and API version rollouts.
- **FR-OPS-003** Auditability for privileged actions and compliance evidence export.

## Non-Functional Requirements (Target Levels)
| Area | Requirement |
|---|---|
| Availability | CMS authoring APIs 99.95%; publishing worker 99.99% |
| Performance | p95 command latency < 350 ms; p99 read latency < 500 ms |
| Scalability | Sustain 10k publish actions/hour with no manual intervention |
| Security | OIDC + MFA for staff roles; field-level encryption for sensitive attributes |
| Resilience | RPO 5 min; RTO 30 min for authoring plane |

## Requirement-to-Implementation Traceability
| Requirement | Use Case | API | Diagram | Edge Case |
|---|---|---|---|---|
| FR-CNT-001 | [UC-01](../analysis/use-case-descriptions.md#uc-01-create-and-save-draft) | [POST /v1/content](../detailed-design/api-design.md#content-api) | [Create Draft Sequence](../detailed-design/sequence-diagrams.md#create-draft-sequence) | [Ingestion/Versioning](../edge-cases/content-ingestion-and-versioning.md) |
| FR-CNT-002 | [UC-04](../analysis/use-case-descriptions.md#uc-04-review-approve-or-request-changes) | [POST /v1/workflow/tasks/{id}/decision](../detailed-design/api-design.md#workflow-api) | [Review System Sequence](../high-level-design/system-sequence-diagrams.md#review-and-publish-system-sequence) | [Workflow/Approvals](../edge-cases/workflow-and-approvals.md) |
| FR-CNT-004 | [UC-06](../analysis/use-case-descriptions.md#uc-06-schedule-publish-and-rollback) | [POST /v1/publications/{id}/rollback](../detailed-design/api-design.md#publishing-api) | [Rollback Sequence](../detailed-design/sequence-diagrams.md#rollback-sequence) | [Publishing/Rollbacks](../edge-cases/publishing-and-rollbacks.md) |


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
