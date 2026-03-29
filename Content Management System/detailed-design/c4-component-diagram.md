# C4 Component Diagram

## Scope
Component decomposition for authoring and publishing containers.

## Mermaid Diagram
```mermaid
flowchart LR
    subgraph AuthoringContainer
      API[REST Controller]
      APP[Application Service]
      DOM[Domain Model]
      REPO[Repository]
    end
    subgraph PublishingContainer
      ORCH[Publish Orchestrator]
      REND[Renderer]
      INV[Invalidation Worker]
    end
    API-->APP-->DOM-->REPO
    APP-->ORCH
    ORCH-->REND-->INV
```

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
