# System Sequence Diagrams

## Purpose
Capture the highest-risk cross-service sequences in the **Hospital Information System** where latency, safety, and auditability matter most.

## Sequence 1 Admit Patient with Identity Resolution and Bed Assignment
```mermaid
sequenceDiagram
    autonumber
    actor Clerk as FrontDeskClerk
    participant UI as ADT_UI
    participant Patient as Patient_Service
    participant ADT as ADT_Service
    participant Bed as Bed_Service
    participant Audit as Audit_Service
    participant Bus as Kafka

    Clerk->>UI: start admission
    UI->>Patient: search patient
    Patient-->>UI: candidates
    UI->>Patient: confirm patient selection
    UI->>ADT: create admission request
    ADT->>Bed: evaluate bed rules
    Bed-->>ADT: compliant bed
    ADT->>Audit: append admission audit
    ADT->>Bus: publish patient admitted
    ADT-->>UI: admission confirmed
```

**Failure Expectations**
- If Patient Service returns duplicate ambiguity, UI must route to MPI review before admission can proceed.
- If no compliant bed exists, ADT creates a waitlist or override task and returns actionable status.
- Audit write failure is fail-secure for admission commit because admission is PHI-bearing state change.

## Sequence 2 Place Medication Order and Verify in Pharmacy
```mermaid
sequenceDiagram
    autonumber
    actor Physician as AttendingPhysician
    participant UI as Clinical_UI
    participant Clinical as Clinical_Service
    participant Pharmacy as Pharmacy_Service
    participant Audit as Audit_Service
    participant Bus as Kafka

    Physician->>UI: enter medication order
    UI->>Clinical: submit order draft
    Clinical->>Clinical: run cds checks
    Clinical->>Audit: append order audit
    Clinical->>Bus: publish order placed
    Bus->>Pharmacy: deliver order event
    Pharmacy->>Pharmacy: verify dispense rules
    Pharmacy-->>UI: verification status via projection
```

**Failure Expectations**
- Hard-stop CDS issues keep the order in draft or rejected state.
- Pharmacy verification may lag, but clinician-facing order state must show pending verification.
- Duplicate event delivery must not create duplicate dispense tasks.

## Sequence 3 Finalize Critical Lab Result and Escalate
```mermaid
sequenceDiagram
    autonumber
    actor Tech as LabTechnologist
    participant Lab as Lab_Service
    participant Clinical as Clinical_Service
    participant Notify as Notification_Service
    participant Audit as Audit_Service
    actor Nurse as ChargeNurse

    Tech->>Lab: finalize result
    Lab->>Lab: evaluate critical range
    Lab->>Audit: append result audit
    Lab->>Clinical: update patient chart
    Lab->>Notify: trigger critical alert
    Notify-->>Nurse: send escalation notice
    Nurse->>Clinical: acknowledge result
    Clinical->>Audit: append acknowledgement audit
```

**Failure Expectations**
- Result persistence must complete before alerting begins.
- If the ordering clinician does not acknowledge within policy SLA, Notification Service escalates to covering provider and charge nurse.
- Corrected critical results create a new notification cycle.

## Sequence 4 Complete Discharge and Trigger Claim Preparation
```mermaid
sequenceDiagram
    autonumber
    actor Physician as DischargingPhysician
    participant Clinical as Clinical_Service
    participant ADT as ADT_Service
    participant Billing as Billing_Service
    participant Insurance as Insurance_Service
    participant Audit as Audit_Service

    Physician->>Clinical: sign discharge summary
    Clinical->>Audit: append summary audit
    Clinical->>ADT: request discharge completion
    ADT->>ADT: close bed occupancy
    ADT->>Billing: publish discharge ready
    Billing->>Insurance: verify claim prerequisites
    Insurance-->>Billing: payer readiness
    Billing-->>Clinical: billing status available
```

## Sequence Control Points

| Sequence | Hard Stop | Async Step | Audit Requirement |
|---|---|---|---|
| Admit patient | duplicate unresolved or no compliant bed | notifications and external HL7 | admission creation and override evidence |
| Medication order | CDS rejection or missing signature | pharmacy verification and dispense | order signature and override evidence |
| Critical result | result not finalized | alert fan-out and escalation | result review acknowledgement |
| Discharge | summary unsigned or mandatory tasks incomplete | claim build and notifications | discharge order, summary sign-off, bed release |

## Sequence Design Rules
- Each command boundary has one owning service and one authoritative version number.
- Every cross-service sequence carries `correlation_id`, `causation_id`, actor, facility, and patient context.
- External integrations are never inside the transaction that commits clinical or ADT source-of-truth state.
- Human acknowledgements such as critical result review must be durable state transitions, not just notifications.
