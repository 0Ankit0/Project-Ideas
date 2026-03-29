# Swimlane Diagrams

## Outpatient Visit Swimlane
```mermaid
flowchart LR
    subgraph FrontDesk[Front Desk]
      A[Register/check-in patient]
      B[Collect consent & insurance]
    end

    subgraph Nursing[Nursing]
      C[Triage and vitals]
    end

    subgraph Physician[Physician]
      D[Assess patient]
      E[Create diagnosis/orders]
    end

    subgraph HIS[HIS]
      F[Persist encounter]
      G[Send orders to lab/radiology]
    end

    A --> B --> C --> D --> E --> F --> G
```

## Billing Swimlane
```mermaid
flowchart LR
    subgraph Clinical[Clinical Team]
      A[Finalize encounter]
    end

    subgraph Coding[Coding Team]
      B[Assign ICD/CPT]
      C[Resolve coding edits]
    end

    subgraph Billing[Billing Team]
      D[Create & submit claim]
      E[Process remittance/denial]
    end

    subgraph Payer[Payer]
      F[Adjudicate claim]
    end

    A --> B --> C --> D --> F --> E
```

---


## Implementation-Ready Swimlane Notes
### Responsibility Matrix
- Front desk owns identity verification and consent intake.
- Nursing owns triage completeness and medication safety checks.
- Physician owns diagnostic decision, order signature, and discharge intent.
- HIS platform owns state transitions, audit evidence, and integration dispatch.

### Escalation Swimlane (Abnormal Result)
```mermaid
flowchart LR
    subgraph Lab[Lab System]
      L1[Publish critical result]
    end
    subgraph HIS[HIS Rules Engine]
      H1[Evaluate critical threshold]
      H2[Create escalation task]
    end
    subgraph Care[Nurse + Physician]
      C1[Acknowledge alert]
      C2[Document intervention]
    end
    L1 --> H1 --> H2 --> C1 --> C2
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **role accountability across front desk, nursing, physician, and platform teams**. The boundaries below are specific to `analysis/swimlane-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Intake & Identity Analysis | Entry validation checkpoints and mismatch heuristics | UI widget design details | Data-quality metrics and EMPI false-positive rate |
| Clinical Flow Analysis | Encounter/order sequence timing and critical path dependencies | Persistence implementation details | Throughput, wait-time, and bottleneck reporting |
| Governance Analysis | Rule conformance and audit evidence completeness | Runtime policy engine internals | Compliance scorecards and control effectiveness trends |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `swimlane-diagrams` workflows must be validated before state mutation. | `GET /v1/analytics/operational-checkpoints` with explicit error taxonomy and correlation IDs. | `workflow_checkpoints, rule_decisions, observability_snapshots` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `swimlane-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[analysis:swimlane-diagrams] --> B[API: GET /v1/analytics/operational-checkpoints]
    B --> C[Data: workflow_checkpoints, rule_decisions, observability_snapshots]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `swimlane-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
