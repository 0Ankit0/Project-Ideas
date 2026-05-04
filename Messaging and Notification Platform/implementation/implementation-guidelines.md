# Implementation Guidelines

## Traceability
- Requirements baseline: [`../requirements/requirements.md`](../requirements/requirements.md)
- Architecture topology: [`../high-level-design/architecture-diagram.md`](../high-level-design/architecture-diagram.md)
- Detailed orchestration: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)
- Infrastructure realization: [`../infrastructure/cloud-architecture.md`](../infrastructure/cloud-architecture.md)

## Service Delivery Plan

| Phase | Deliverables |
|---|---|
| Phase 1 | API gateway integration, authentication, message persistence, idempotency, outbox, status API |
| Phase 2 | queue bus, dispatch workers, provider adapters for email/SMS/push, callback ingestion, retry classification |
| Phase 3 | template versioning, approval workflow, locale fallback, consent/suppression service |
| Phase 4 | provider failover, campaign scheduling, analytics pipeline, audit export, operator console |

## Module Breakdown

| Domain | Services/modules |
|---|---|
| Ingestion | notification-api, auth middleware, request validator |
| Policy | consent service, suppression evaluator, rate/quota engine |
| Content | template service, renderer, approval workflow |
| Dispatch | orchestrator, retry scheduler, dispatch workers, provider adapters |
| Operations | DLQ tools, analytics consumers, audit export, admin portal |

## Delivery Guardrails

1. Persist message metadata before publishing dispatch intent.
2. Introduce new channels behind adapter contracts and feature flags.
3. Roll out provider failover gradually with shadow scoring before automatic cutover.
4. Ship replay tooling only after audit and approval controls are in place.

## Test Strategy

- Contract tests for each provider adapter and callback parser.
- End-to-end tests for P0/P1/P2 message flows, including callback reconciliation.
- Chaos tests for provider brownouts, queue lag, and cache loss.
- Security tests for SSRF-safe webhook validation, PII redaction, and RBAC boundaries.

## Definition of Done

- Contract tests for provider adapters pass.
- Chaos test validates failover behavior under provider outage.
- Security review confirms PII redaction and RBAC boundaries.
- Runbook exists for callback delay, DLQ replay, provider circuit open, and consent drift incidents.

## Release and Migration Policy

- API changes follow backward-compatible versioning unless a new major version is published.
- Queue/event schema changes require dual-publish or consumer compatibility window.
- Database migrations follow expand-contract; destructive changes are deferred until all readers are upgraded.
- Template schema changes include validator migration and backfill plan for drafts.

## Phase Exit Criteria

| Phase | Exit criteria |
|---|---|
| Phase 1 | authenticated send API, persisted message state, idempotency replay, status query |
| Phase 2 | successful dispatch on at least two channels, callback reconciliation, retry + DLQ flow |
| Phase 3 | template approvals, consent/suppression enforcement, locale fallback, operator visibility |
| Phase 4 | automatic provider failover, analytics dashboards, audit exports, replay approvals |

## Operational acceptance criteria

- Each service has clear ownership, SLOs, dashboards, and alert routes before production readiness.
- Production promotion requires passing replay safety tests and provider failover drills.
- Implementation work is tracked against phase exit criteria rather than generic feature completion claims.
