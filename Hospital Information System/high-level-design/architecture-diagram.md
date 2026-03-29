# Architecture Diagram

```mermaid
flowchart TB
    Channels[Clinician UI, Patient Portal, Integrations] --> Edge[API Gateway]

    subgraph Services[Core HIS Services]
      Patient[Patient Registry]
      Scheduling[Scheduling]
      Clinical[Clinical Documentation]
      Orders[Orders & Results]
      Admission[ADT/Bed Management]
      Billing[Revenue Cycle]
    end

    Edge --> Patient
    Edge --> Scheduling
    Edge --> Clinical
    Edge --> Orders
    Edge --> Admission
    Edge --> Billing

    subgraph Shared[Shared Platform]
      Auth[Identity/AuthZ]
      Audit[Audit Logging]
      Jobs[Workflow/Async Jobs]
      Notify[Notifications]
    end

    Edge --> Auth
    Clinical --> Audit
    Billing --> Audit

    subgraph Storage[Storage & Messaging]
      DB[(OLTP Database)]
      MQ[(Event Bus)]
      Search[(Search)]
      WH[(Warehouse)]
    end

    Services --> DB
    Clinical --> MQ
    Orders --> MQ
    Billing --> MQ
    MQ --> Jobs
    MQ --> Search
    MQ --> WH
    Jobs --> Notify
```

---


## Architecture Decision Records (ADR) Summary
- ADR-001: Domain-oriented service partitioning by patient, encounter, orders, ADT, billing.
- ADR-002: Event-driven integration with transactional outbox for reliability.
- ADR-003: Zero-trust service-to-service communication with mTLS and short-lived identities.

## High-Level Failure Domains
```mermaid
flowchart TB
    UI[UI/BFF] --> Core[Core Services]
    Core --> Data[(OLTP)]
    Core --> Bus[(Event Bus)]
    Bus --> Proj[Read Projections]
    Core -.external SLA.-> Ext[External Systems]
    Ext -.degraded mode.-> Core
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **service partitioning and high-level fault domain boundaries**. The boundaries below are specific to `high-level-design/architecture-diagram.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Channel Boundary | UI/portal/integration ingress and trust establishment | Internal transaction details | Stable ingress contracts and auth context propagation |
| Core Domain Boundary | Patient/ADT/clinical/orders/billing service partitioning | External SLA ownership | Clear ownership and bounded failure domains |
| Platform Boundary | Eventing, observability, identity, and audit services | Domain-specific policy logic | Shared resilience and security foundations |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `architecture-diagram` workflows must be validated before state mutation. | `GET /v1/platform/topology/contracts` with explicit error taxonomy and correlation IDs. | `service_contracts, dependency_graph, data_lineage_edges` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `architecture-diagram.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[high-level-design:architecture-diagram] --> B[API: GET /v1/platform/topology/contracts]
    B --> C[Data: service_contracts, dependency_graph, data_lineage_edges]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `architecture-diagram.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
