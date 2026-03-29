# Component Diagrams

```mermaid
flowchart LR
    subgraph API[API Layer]
      Gateway[Gateway/BFF]
    end

    subgraph Clinical[Clinical Components]
      Reg[Registration]
      Sched[Scheduling]
      EHR[Encounter/Clinical Notes]
      Orders[Orders]
      Meds[Medication Administration]
      Admit[Admission/Bed Mgmt]
    end

    subgraph Revenue[Revenue Cycle Components]
      Charge[Charge Capture]
      Coding[Coding]
      Claims[Claims]
      Payments[Payments/Denials]
    end

    subgraph Platform[Platform Components]
      Auth[AuthZ]
      Audit[Audit]
      Notify[Notifications]
      Int[Integration Adapter]
    end

    subgraph Data[Data]
      DB[(PostgreSQL)]
      Bus[(Event Bus)]
      Cache[(Redis)]
    end

    Gateway --> Reg --> DB
    Gateway --> Sched --> DB
    Gateway --> EHR --> DB
    Gateway --> Orders --> DB
    Gateway --> Meds --> DB
    Gateway --> Admit --> DB

    EHR --> Charge --> Coding --> Claims --> Payments
    Claims --> Int

    Reg --> Bus
    Sched --> Bus
    EHR --> Bus
    Claims --> Bus

    Gateway --> Auth
    EHR --> Audit
    Claims --> Audit
    Bus --> Notify
    Auth --> Cache
```

---


## Component Deployment and Scaling Notes
### Scaling Profiles
- Registration and scheduling services scale on request concurrency.
- Results ingestion and billing projectors scale on queue lag + batch latency.
- Audit pipeline is append-only and horizontally partitioned by tenant and month.

### Fault Isolation
- Circuit breakers isolate LIS/PACS outages from core charting path.
- Queue backpressure policies prevent order dispatch saturation.
- Dead-letter queues include replay metadata and ownership routing.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **module interaction topology and operational failure isolation boundaries**. The boundaries below are specific to `detailed-design/component-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Application Service Layer | Command validation, transaction demarcation, event emission | Direct infrastructure adapter logic | Deterministic command behavior and retry safety |
| Domain Model Layer | Aggregate invariants, lifecycle transitions, and business calculations | API transport concerns | Strong consistency inside aggregate boundaries |
| Integration Adapter Layer | HL7/FHIR/payer translation and delivery receipts | Domain state mutation logic | Isolation from external protocol drift |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `component-diagrams` workflows must be validated before state mutation. | `PATCH /v1/{resource}/{id}/state` with explicit error taxonomy and correlation IDs. | `aggregate_versions, outbox_messages, integration_receipts` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `component-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[detailed-design:component-diagrams] --> B[API: PATCH /v1/{resource}/{id}/state]
    B --> C[Data: aggregate_versions, outbox_messages, integration_receipts]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `component-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
