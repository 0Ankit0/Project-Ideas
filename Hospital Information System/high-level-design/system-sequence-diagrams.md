# System Sequence Diagrams

## Admit Patient
```mermaid
sequenceDiagram
    autonumber
    actor Clerk as Front Desk
    participant UI as ADT UI
    participant API as Admission API
    participant Bed as Bed Service
    participant DB as DB

    Clerk->>UI: Start admission
    UI->>API: POST /v1/admissions
    API->>Bed: allocate bed
    Bed-->>API: bed assigned
    API->>DB: persist admission
    API-->>UI: admission confirmed
```

## Submit Insurance Claim
```mermaid
sequenceDiagram
    autonumber
    actor Bill as Billing Staff
    participant UI as Billing UI
    participant API as Claims API
    participant CLM as Claims Service
    participant Payer as Payer Gateway

    Bill->>UI: submit claim
    UI->>API: POST /v1/claims/{id}/submit
    API->>CLM: validate and package claim
    CLM->>Payer: transmit claim
    Payer-->>CLM: ack
    CLM-->>API: status submitted
    API-->>UI: 200 submitted
```

---


## End-to-End Sequence Constraints
### Admission Critical Path Controls
- Bed assignment must complete under 10 seconds p95 with fallback to manual assignment queue.
- All state transitions include audit append and event publish transactionally.
- Downstream notifications are asynchronous and non-blocking to admission commit.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **cross-service orchestration checkpoints and latency budgets**. The boundaries below are specific to `high-level-design/system-sequence-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Channel Boundary | UI/portal/integration ingress and trust establishment | Internal transaction details | Stable ingress contracts and auth context propagation |
| Core Domain Boundary | Patient/ADT/clinical/orders/billing service partitioning | External SLA ownership | Clear ownership and bounded failure domains |
| Platform Boundary | Eventing, observability, identity, and audit services | Domain-specific policy logic | Shared resilience and security foundations |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `system-sequence-diagrams` workflows must be validated before state mutation. | `GET /v1/platform/topology/contracts` with explicit error taxonomy and correlation IDs. | `service_contracts, dependency_graph, data_lineage_edges` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `system-sequence-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[high-level-design:system-sequence-diagrams] --> B[API: GET /v1/platform/topology/contracts]
    B --> C[Data: service_contracts, dependency_graph, data_lineage_edges]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `system-sequence-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
