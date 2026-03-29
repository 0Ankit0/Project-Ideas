# Data Dictionary

This data dictionary is the canonical reference for **Healthcare Appointment System**. It defines shared terminology, entity semantics, and governance controls required to keep healthcare appointment workflows consistent across teams and services.

## Scope and Goals
- Establish a stable vocabulary for architecture, API, analytics, and operations teams.
- Define minimum required fields for core entities and expected relationship boundaries.
- Document data quality and retention controls needed for production readiness.

## Core Entities
| Entity | Description | Required Attributes |
|---|---|---|
| TenantOrOrganization | Top-level ownership boundary for data segregation | `org_id, name, status, region, created_at` |
| UserOrActor | Human/system principal that performs actions | `actor_id, org_id, role, status, last_active_at` |
| PrimaryRecord | Main lifecycle object handled by the platform | `record_id, org_id, state, owner_id, created_at, updated_at` |
| ChildTransaction | Operational transaction or sub-step linked to primary record | `txn_id, record_id, txn_type, amount_or_value, occurred_at` |
| PolicyOrRule | Versioned policy configuration that influences decisions | `policy_id, scope, version, effective_from, effective_to` |
| AuditEvent | Append-only evidence for state changes and controls | `audit_id, record_id, actor_id, action, reason_code, occurred_at` |

## Canonical Relationship Diagram
```mermaid
erDiagram
    TENANTORORGANIZATION ||--o{ USERORACTOR : owns
    TENANTORORGANIZATION ||--o{ PRIMARYRECORD : contains
    PRIMARYRECORD ||--o{ CHILDTRANSACTION : has
    POLICYORRULE ||--o{ PRIMARYRECORD : governs
    PRIMARYRECORD ||--o{ AUDITEVENT : audited_by
    USERORACTOR ||--o{ AUDITEVENT : performs
```

## Data Quality Controls
1. All write paths enforce required-field validation and referential integrity for mandatory foreign keys.
2. External imports must include provenance metadata (`source_system`, `source_ref`, `ingested_at`).
3. Status/state fields use controlled vocabularies and reject unknown values.
4. Duplicate detection runs on natural keys where business identity collisions are likely.
5. Sensitive fields carry classification tags to drive masking, encryption, and export behavior.

## Retention and Audit
- Operational records remain online for active workflow windows and support forensic queries.
- Historical records move to archive tiers by policy without breaking traceability.
- Audit events are immutable and linked through correlation ids for incident analysis.

## Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prohibited per provider, location, and time-slot; writes enforce an optimistic concurrency check on slot version plus an idempotency key.
- When two booking requests race for the same slot, the first committed request wins and all later requests receive `SLOT_ALREADY_BOOKED` with alternative slot suggestions.
- Provider calendar changes (leave, overrun, emergency block) trigger an automatic revalidation pass that marks impacted bookings as `REBOOK_REQUIRED` and starts remediation workflows.
- Escalation SLA: unresolved conflicts older than 15 minutes are routed to operations for manual intervention and patient outreach.

### Patient/Provider Workflow States
- Patient appointment lifecycle: `DRAFT -> PENDING_CONFIRMATION -> CONFIRMED -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED` with terminal branches `CANCELLED`, `NO_SHOW`, and `EXPIRED`.
- Provider schedule lifecycle: `AVAILABLE -> RESERVED -> LOCKED_FOR_VISIT -> RELEASED`; exceptional states include `BLOCKED` (planned) and `SUSPENDED` (incident/compliance).
- State transitions are event-driven and auditable; every transition records actor, timestamp, source channel, and reason code.
- Invalid transitions are rejected with deterministic error codes and do not mutate downstream billing or notification state.

### Notification Guarantees
- Notification channels include in-app, email, and SMS (when consented); delivery policy is at-least-once with idempotent message keys to prevent duplicate side effects.
- Critical events (`CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `REBOOK_REQUIRED`) are retried with exponential backoff for up to 24 hours.
- If all automated retries fail, a fallback task is created for support-assisted outreach and the record is flagged `NOTIFICATION_ATTENTION_REQUIRED`.
- Template rendering and localization are versioned so users receive content consistent with the transaction version that triggered the event.

### Privacy Requirements
- All PHI/PII is encrypted in transit (TLS 1.2+) and at rest (AES-256 or cloud-provider equivalent managed keys).
- Access control follows least privilege with RBAC/ABAC, MFA for privileged roles, and full audit logging for create/read/update/export actions on medical or billing data.
- Data minimization applies to notifications and analytics exports; only required fields are shared and retention follows policy/legal hold requirements.
- Integrations must use signed requests, scoped credentials, and periodic key rotation; sandbox/test data must be de-identified.

### Downtime Fallback Procedures
- During partial outages, the system enters degraded mode: read-only schedule views remain available while new bookings are queued for deferred processing.
- Clinics maintain a printable/offline daily roster and manual check-in sheet; staff can continue visits using downtime SOPs and reconcile once service is restored.
- Recovery requires replaying queued commands/events in order, conflict revalidation, and sending reconciliation notices for any changed appointments.
- Incident closure criteria include successful backlog drain, data consistency checks, and post-incident communication to affected patients/providers.

