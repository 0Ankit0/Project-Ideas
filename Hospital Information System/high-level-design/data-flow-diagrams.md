# Data Flow Diagrams

## Clinical Data Flow
```mermaid
flowchart LR
    Intake[Registration/Portal] --> PatientAPI[Patient API]
    PatientAPI --> PatientStore[(Patient Master)]

    ClinicalUI[Clinician UI] --> EncounterAPI[Encounter API]
    EncounterAPI --> EncounterStore[(Encounter Records)]
    EncounterAPI --> OrdersAPI[Orders API]
    OrdersAPI --> OrderStore[(Order Tables)]
    OrdersAPI --> ExternalLab[Lab/Radiology]
    ExternalLab --> ResultsIngest[Results Ingestion]
    ResultsIngest --> EncounterStore
```

## Revenue Cycle Data Flow
```mermaid
flowchart LR
    EncounterStore[(Encounter Records)] --> ChargeEngine[Charge Generation]
    ChargeEngine --> Coding[Medical Coding]
    Coding --> Claims[Claim Builder]
    Claims --> PayerGateway[Payer Gateway]
    PayerGateway --> Remit[Remittance/Denials]
    Remit --> AR[(Accounts Receivable)]
```

---


## Data Flow Control Deep Dive
### Data Classification
- PHI and sensitive operational metadata are tagged at ingress and propagated through lineage fields.
- Export flows require purpose-of-use and retention tags at extraction time.
- Warehouse pipelines strip direct identifiers unless explicit approved use case.

### Data Lineage Flow
```mermaid
flowchart LR
    Ingress[API Ingress] --> Txn[(OLTP)]
    Txn --> Outbox[Outbox Events]
    Outbox --> Stream[Event Stream]
    Stream --> Proj[Operational Projections]
    Stream --> WH[Analytics Warehouse]
    WH --> Reports[Compliance/Operational Reports]
```

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **data lineage, PHI classification, and projection flows**. The boundaries below are specific to `high-level-design/data-flow-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Channel Boundary | UI/portal/integration ingress and trust establishment | Internal transaction details | Stable ingress contracts and auth context propagation |
| Core Domain Boundary | Patient/ADT/clinical/orders/billing service partitioning | External SLA ownership | Clear ownership and bounded failure domains |
| Platform Boundary | Eventing, observability, identity, and audit services | Domain-specific policy logic | Shared resilience and security foundations |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `data-flow-diagrams` workflows must be validated before state mutation. | `GET /v1/platform/topology/contracts` with explicit error taxonomy and correlation IDs. | `service_contracts, dependency_graph, data_lineage_edges` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `data-flow-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[high-level-design:data-flow-diagrams] --> B[API: GET /v1/platform/topology/contracts]
    B --> C[Data: service_contracts, dependency_graph, data_lineage_edges]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `data-flow-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
