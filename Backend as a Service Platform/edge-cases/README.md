# Edge Cases – Backend as a Service Platform

This folder documents cross-cutting scenarios that can break abstraction stability, tenant isolation, provider portability, migration safety, security, or platform operations if not handled deliberately.

## Contents

| File | Domain | Scenario Count |
|------|--------|---------------|
| [provider-selection-and-provisioning.md](./provider-selection-and-provisioning.md) | Provider binding, compatibility, readiness | 8 |
| [auth-and-tenancy.md](./auth-and-tenancy.md) | Identity, session, tenant isolation | 9 |
| [data-api-and-schema.md](./data-api-and-schema.md) | Schema migration, RLS, query facade | 8 |
| [storage-and-file-providers.md](./storage-and-file-providers.md) | File uploads, consistency, access control | 7 |
| [functions-and-jobs.md](./functions-and-jobs.md) | Cold starts, timeouts, deployment failures | 8 |
| [realtime-and-messaging.md](./realtime-and-messaging.md) | At-least-once delivery, fan-out, WebSocket | 7 |
| [api-and-sdk.md](./api-and-sdk.md) | Versioning, idempotency, rate limiting | 8 |
| [security-and-compliance.md](./security-and-compliance.md) | Secrets, audit, privilege escalation | 8 |
| [operations.md](./operations.md) | PostgreSQL failover, queue backlog, incident | 8 |

## Severity Legend

| Level | Meaning |
|-------|---------|
| **Critical** | Data loss, cross-tenant leak, or complete capability unavailability |
| **High** | Degraded user experience or partial data inconsistency |
| **Medium** | Delayed processing or temporary user-facing errors |
| **Low** | Minor UX degradation with transparent self-recovery |

## Cross-Cutting Guardrails (Apply to All Domains)

1. **Tenant isolation first**: every operation must carry and validate `tenantId` + `projectId` + `envId` before touching any data store.
2. **Idempotency for mutations**: all state-changing operations accept an idempotency key; duplicate requests return the original response.
3. **Structured error envelopes**: every error surfaces as a machine-readable code with `retryable` flag and `correlationId`.
4. **Audit on every state change**: all side-effectful operations append an immutable audit log entry before returning.
5. **Circuit breaker on adapters**: all provider adapter calls go through a circuit breaker; open circuit surfaces as `DEP_PROVIDER_UNAVAILABLE` rather than timeout.
