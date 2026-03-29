# Activity Diagrams

## Patient Registration and Appointment
```mermaid
flowchart TD
    A[Patient Arrives / Calls] --> B[Search Existing Patient]
    B --> C{Record Found?}
    C -- No --> D[Create Patient Profile]
    C -- Yes --> E[Verify Demographics/Insurance]
    D --> E
    E --> F[Check Provider Availability]
    F --> G{Slot Available?}
    G -- No --> H[Offer Alternate Date/Provider]
    G -- Yes --> I[Book Appointment]
    H --> I
    I --> J[Send Confirmation + Reminder]
```

## Encounter and Orders
```mermaid
flowchart TD
    A[Patient Checked In] --> B[Triage Vitals]
    B --> C[Doctor Encounter]
    C --> D{Labs/Imaging Needed?}
    D -- No --> E[Diagnosis + Care Plan]
    D -- Yes --> F[Create Orders]
    F --> G[Receive Results]
    G --> E
    E --> H[Prescribe Medication]
    H --> I[Complete Encounter Documentation]
```

## Claim Submission
```mermaid
flowchart TD
    A[Encounter Closed] --> B[Generate Charge Items]
    B --> C[Code Validation]
    C --> D{Coding Complete?}
    D -- No --> E[Coder Review Queue]
    E --> C
    D -- Yes --> F[Create Claim]
    F --> G[Submit to Payer]
    G --> H{Accepted?}
    H -- No --> I[Denial Work Queue]
    H -- Yes --> J[Post Acknowledgement]
```

---


## Implementation-Ready Deep Dive
### Workflow Gate Conditions
- **Registration complete** requires validated demographics, policy eligibility result, and signed consent artifact id.
- **Encounter start** requires triage completeness (`chief_complaint`, `acuity`, `vitals_timestamp`) and active care-team assignment.
- **Order release** requires signed order + CDS disposition (`pass`, `override`, `hard_stop`) and destination endpoint readiness.

### Failure and Recovery Paths
```mermaid
flowchart TD
    A[Start Encounter Workflow] --> B{EMPI Match Confidence >= 0.95?}
    B -- No --> C[Route to Identity Review Queue]
    B -- Yes --> D{Consent Valid for Purpose?}
    D -- No --> E[Collect/Revoke/Amend Consent]
    D -- Yes --> F[Proceed to Clinical Documentation]
    F --> G{Order Dispatch ACK <= 30s?}
    G -- No --> H[Persist in Retry Outbox + Notify Unit Clerk]
    G -- Yes --> I[Finalize workflow checkpoint]
```

### Operational SLO Checkpoints
- Intake-to-checkin p95 < 4 minutes for front-desk initiated encounters.
- Order signature to downstream ACK p95 < 30 seconds.
- Result ingestion to chart availability p95 < 2 minutes.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **workflow execution states for registration, encounter progression, and revenue handoff**. The boundaries below are specific to `analysis/activity-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Intake & Identity Analysis | Entry validation checkpoints and mismatch heuristics | UI widget design details | Data-quality metrics and EMPI false-positive rate |
| Clinical Flow Analysis | Encounter/order sequence timing and critical path dependencies | Persistence implementation details | Throughput, wait-time, and bottleneck reporting |
| Governance Analysis | Rule conformance and audit evidence completeness | Runtime policy engine internals | Compliance scorecards and control effectiveness trends |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `activity-diagrams` workflows must be validated before state mutation. | `GET /v1/analytics/operational-checkpoints` with explicit error taxonomy and correlation IDs. | `workflow_checkpoints, rule_decisions, observability_snapshots` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `activity-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[analysis:activity-diagrams] --> B[API: GET /v1/analytics/operational-checkpoints]
    B --> C[Data: workflow_checkpoints, rule_decisions, observability_snapshots]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `activity-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
