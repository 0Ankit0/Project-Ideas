# C4 Component Diagram

## HIS Application Container - Components
```mermaid
flowchart TB
    subgraph Users[Users]
      Doctor
      Nurse
      Clerk
      Biller
    end

    subgraph HIS[HIS App Container]
      UIBFF[Web UI + BFF]
      PatientCmp[Patient Registry]
      ScheduleCmp[Scheduling]
      EncounterCmp[Encounter Management]
      OrdersCmp[Lab/Radiology Orders]
      AdmissionCmp[Admission/Bed Management]
      BillingCmp[Revenue Cycle]
      PolicyCmp[Clinical Policy + Auth]
      AuditCmp[Audit Component]
      IntegrCmp[Integration Orchestrator]
    end

    subgraph Infra[Infra Containers]
      OLTP[(HIS OLTP DB)]
      Bus[(Event Bus)]
      Cache[(Redis)]
      DWH[(Analytics Warehouse)]
    end

    Doctor --> UIBFF
    Nurse --> UIBFF
    Clerk --> UIBFF
    Biller --> UIBFF

    UIBFF --> PatientCmp
    UIBFF --> ScheduleCmp
    UIBFF --> EncounterCmp
    UIBFF --> OrdersCmp
    UIBFF --> AdmissionCmp
    UIBFF --> BillingCmp
    UIBFF --> PolicyCmp

    PatientCmp --> OLTP
    ScheduleCmp --> OLTP
    EncounterCmp --> OLTP
    OrdersCmp --> OLTP
    AdmissionCmp --> OLTP
    BillingCmp --> OLTP

    EncounterCmp --> Bus
    OrdersCmp --> Bus
    BillingCmp --> Bus

    IntegrCmp --> Bus
    IntegrCmp --> DWH
    PolicyCmp --> Cache
    AuditCmp --> OLTP
```

---


## Component Interaction Contracts
### Dependency Rules
- Controllers call application services only; no direct repository access.
- Domain services are side-effect free and deterministic for replayability.
- Integration adapters are anti-corruption layers for HL7/FHIR and payer protocols.

### Runtime Collaboration (Order Submission)
```mermaid
flowchart LR
    Ctrl[OrdersController] --> App[OrderApplicationService]
    App --> Policy[CDS/Policy Engine]
    App --> Repo[OrderRepository]
    App --> Outbox[OutboxPublisher]
    Outbox --> Adapter[Lab/PACS Adapter]
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **component responsibilities and dependency restrictions inside HIS container**. The boundaries below are specific to `detailed-design/c4-component-diagram.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Application Service Layer | Command validation, transaction demarcation, event emission | Direct infrastructure adapter logic | Deterministic command behavior and retry safety |
| Domain Model Layer | Aggregate invariants, lifecycle transitions, and business calculations | API transport concerns | Strong consistency inside aggregate boundaries |
| Integration Adapter Layer | HL7/FHIR/payer translation and delivery receipts | Domain state mutation logic | Isolation from external protocol drift |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `c4-component-diagram` workflows must be validated before state mutation. | `PATCH /v1/{resource}/{id}/state` with explicit error taxonomy and correlation IDs. | `aggregate_versions, outbox_messages, integration_receipts` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `c4-component-diagram.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[detailed-design:c4-component-diagram] --> B[API: PATCH /v1/{resource}/{id}/state]
    B --> C[Data: aggregate_versions, outbox_messages, integration_receipts]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `c4-component-diagram.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
