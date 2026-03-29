# System Context Diagram

This diagram shows the Hospital Information System (HIS) boundary and external actors/systems.

```mermaid
flowchart LR
    subgraph ClinicalActors[Clinical Actors]
      Doc[Doctor]
      Nurse[Nurse]
      Clerk[Front Desk Clerk]
      Billing[Billing Staff]
      Admin[Hospital Admin]
    end

    HIS[Hospital Information System]

    subgraph ExternalSystems[External Systems]
      LIS[Lab Information System]
      PACS[Radiology/PACS]
      Payer[Insurance/Payer Gateway]
      Pharm[Pharmacy System]
      HIE[Health Information Exchange]
      IdP[Enterprise IdP/SSO]
    end

    Doc --> HIS
    Nurse --> HIS
    Clerk --> HIS
    Billing --> HIS
    Admin --> HIS

    HIS --> LIS
    LIS --> HIS
    HIS --> PACS
    PACS --> HIS
    HIS --> Payer
    HIS --> Pharm
    HIS --> HIE
    IdP --> HIS
```

---


## Implementation-Ready Context Assumptions
### Trust and Responsibility Boundaries
- HIS is system-of-record for encounters, orders, and admission states.
- IdP is source-of-truth for principal authentication; HIS remains source-of-truth for authorization context.
- Payer, LIS, and PACS are external systems of participation with explicit retry contracts and SLA tracking.

### Context Failure Boundary Diagram
```mermaid
flowchart TB
    User[Clinical User] --> HIS[HIS]
    HIS --> LIS[External LIS]
    HIS --> PACS[External PACS]
    HIS --> Payer[Payer Gateway]
    LIS -.timeout/retry.-> HIS
    PACS -.schema drift alert.-> HIS
    Payer -.adjudication delay.-> HIS
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **external system boundaries, trust zones, and integration SLAs**. The boundaries below are specific to `analysis/system-context-diagram.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Intake & Identity Analysis | Entry validation checkpoints and mismatch heuristics | UI widget design details | Data-quality metrics and EMPI false-positive rate |
| Clinical Flow Analysis | Encounter/order sequence timing and critical path dependencies | Persistence implementation details | Throughput, wait-time, and bottleneck reporting |
| Governance Analysis | Rule conformance and audit evidence completeness | Runtime policy engine internals | Compliance scorecards and control effectiveness trends |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `system-context-diagram` workflows must be validated before state mutation. | `GET /v1/analytics/operational-checkpoints` with explicit error taxonomy and correlation IDs. | `workflow_checkpoints, rule_decisions, observability_snapshots` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `system-context-diagram.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[analysis:system-context-diagram] --> B[API: GET /v1/analytics/operational-checkpoints]
    B --> C[Data: workflow_checkpoints, rule_decisions, observability_snapshots]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `system-context-diagram.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
