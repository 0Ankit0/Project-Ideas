# Class Diagrams

```mermaid
classDiagram
    class Patient {
      +UUID id
      +String mrn
      +String fullName
      +Date dob
      +String gender
      +updateDemographics()
    }

    class Appointment {
      +UUID id
      +UUID patientId
      +UUID providerId
      +DateTime startsAt
      +AppointmentStatus status
      +confirm()
      +cancel(reason)
      +checkIn()
    }

    class Encounter {
      +UUID id
      +UUID patientId
      +UUID appointmentId
      +DateTime startedAt
      +DateTime endedAt
      +close()
    }

    class Admission {
      +UUID id
      +UUID patientId
      +UUID bedId
      +AdmissionStatus status
      +admit()
      +transfer(newBedId)
      +discharge()
    }

    class LabOrder {
      +UUID id
      +UUID encounterId
      +String testCode
      +OrderStatus status
      +place()
      +result()
    }

    class Claim {
      +UUID id
      +UUID encounterId
      +Money amount
      +ClaimStatus status
      +submit()
      +postRemittance()
    }

    class MedicationOrder {
      +UUID id
      +UUID encounterId
      +String drugCode
      +String dose
      +sign()
      +discontinue()
    }

    Patient "1" --> "many" Appointment
    Patient "1" --> "many" Encounter
    Patient "1" --> "many" Admission
    Appointment "0..1" --> "1" Encounter
    Encounter "1" --> "many" LabOrder
    Encounter "1" --> "many" MedicationOrder
    Encounter "1" --> "many" Claim
```

---


## Class-Level Implementation Notes
### Aggregate Boundaries
- `Patient` aggregate owns identity and consent references only; clinical records are separate aggregates.
- `Encounter` aggregate owns encounter status transitions and care-team assignments.
- `Order` aggregate owns order lifecycle and result linkage state.

### Invariant Checklist
- Aggregate methods must enforce transition guards and emit domain events atomically with state mutation.
- Entity constructors require coded-value validation through terminology adapters.
- Value objects are immutable and serialization-safe for event payloads.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **aggregate invariants, object lifecycle rules, and domain consistency checks**. The boundaries below are specific to `detailed-design/class-diagrams.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Application Service Layer | Command validation, transaction demarcation, event emission | Direct infrastructure adapter logic | Deterministic command behavior and retry safety |
| Domain Model Layer | Aggregate invariants, lifecycle transitions, and business calculations | API transport concerns | Strong consistency inside aggregate boundaries |
| Integration Adapter Layer | HL7/FHIR/payer translation and delivery receipts | Domain state mutation logic | Isolation from external protocol drift |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `class-diagrams` workflows must be validated before state mutation. | `PATCH /v1/{resource}/{id}/state` with explicit error taxonomy and correlation IDs. | `aggregate_versions, outbox_messages, integration_receipts` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `class-diagrams.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

### Interoperability and Control Flow
```mermaid
flowchart LR
    A[detailed-design:class-diagrams] --> B[API: PATCH /v1/{resource}/{id}/state]
    B --> C[Data: aggregate_versions, outbox_messages, integration_receipts]
    C --> D[Control: Monitoring + Audit + Runbook]
    D --> E[Recovery/Verification Loop]
```

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `class-diagrams.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
