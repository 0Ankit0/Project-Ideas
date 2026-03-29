# State Machine Diagrams

## Appointment Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Requested
    Requested --> Confirmed
    Confirmed --> CheckedIn
    CheckedIn --> InProgress
    InProgress --> Completed
    Requested --> Cancelled
    Confirmed --> Cancelled
    Confirmed --> NoShow
    Completed --> [*]
    Cancelled --> [*]
    NoShow --> [*]
```

## Admission Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Admitted
    Admitted --> Transferred
    Transferred --> Admitted
    Admitted --> Discharged
    Admitted --> Expired
    Discharged --> [*]
    Expired --> [*]
```

## Claim Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Submitted
    Submitted --> Accepted
    Submitted --> Rejected
    Accepted --> Paid
    Accepted --> PartiallyPaid
    Accepted --> Denied
    Rejected --> Draft
    Paid --> [*]
    Denied --> [*]
```

---


## State Machine Enforcement Notes
### Guard Conditions
- `Confirmed -> CheckedIn` requires identity+consent verified within configurable recency window.
- `InProgress -> Completed` requires signed clinician note and closure of open high-priority tasks.
- `Admitted -> Discharged` requires discharge summary draft at minimum, with post-discharge task plan.

### Override and Exception State
```mermaid
stateDiagram-v2
    [*] --> Active
    Active --> OverridePending: policy exception requested
    OverridePending --> Active: denied
    OverridePending --> OverrideGranted: approved + reason
    OverrideGranted --> Active: expiry reached
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **legal state transitions, guard conditions, and override pathways**. The boundaries below are specific to `detailed-design/state-machine-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Application Service Layer | Command validation, transaction demarcation, event emission | Direct infrastructure adapter logic | Deterministic command behavior and retry safety |
| Domain Model Layer | Aggregate invariants, lifecycle transitions, and business calculations | API transport concerns | Strong consistency inside aggregate boundaries |
| Integration Adapter Layer | HL7/FHIR/payer translation and delivery receipts | Domain state mutation logic | Isolation from external protocol drift |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `state-machine-diagrams` workflows must be validated before state mutation. | `PATCH /v1/{resource}/{id}/state` with explicit error taxonomy and correlation IDs. | `aggregate_versions, outbox_messages, integration_receipts` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `state-machine-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[detailed-design:state-machine-diagrams] --> B[API: PATCH /v1/{resource}/{id}/state]
    B --> C[Data: aggregate_versions, outbox_messages, integration_receipts]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `state-machine-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
