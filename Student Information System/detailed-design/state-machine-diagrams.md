# State Machine Diagrams

## Overview
State machine diagrams showing the lifecycle and state transitions for key entities in the Student Information System.

---

## Student Status State Machine

```mermaid
stateDiagram-v2
    [*] --> APPLICANT : Admission application submitted

    APPLICANT --> ENROLLED : Admission approved and confirmation fee paid
    APPLICANT --> [*] : Application rejected

    ENROLLED --> ACTIVE : First course enrollment completed
    ENROLLED --> WITHDRAWN : Student withdraws before first enrollment

    ACTIVE --> SUSPENDED : Academic suspension or disciplinary action
    ACTIVE --> GRADUATED : Graduation requirements met and cleared
    ACTIVE --> WITHDRAWN : Student formally withdraws

    SUSPENDED --> ACTIVE : Reinstatement approved after suspension period
    SUSPENDED --> WITHDRAWN : Student withdraws while suspended
    SUSPENDED --> GRADUATED : In rare cases, petition for degree after suspension resolved

    GRADUATED --> [*] : Record archived
    WITHDRAWN --> [*] : Record archived
```

---

## Enrollment Status State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : Student submits enrollment request

    PENDING --> ENROLLED : Enrollment validated (prerequisites met, seat available, no conflict)
    PENDING --> WAITLISTED : Section is full; student joins waitlist
    PENDING --> REJECTED : Validation fails (missing prerequisite, conflict)

    WAITLISTED --> ENROLLED : Seat opens; auto-enrollment triggered
    WAITLISTED --> REMOVED : Student manually removes from waitlist

    ENROLLED --> DROPPED : Student drops course within drop deadline
    ENROLLED --> COMPLETED : Semester ends; student passes course
    ENROLLED --> FAILED : Semester ends; student fails course

    DROPPED --> [*]
    COMPLETED --> [*]
    FAILED --> [*]
    REJECTED --> [*]
    REMOVED --> [*]
```

---

## Grade Status State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Faculty starts grade entry

    DRAFT --> SUBMITTED : Faculty submits final grades to registrar
    DRAFT --> DRAFT : Faculty saves intermediate draft

    SUBMITTED --> PUBLISHED : Registrar approves and publishes grades
    SUBMITTED --> DRAFT : Registrar returns grades for correction

    PUBLISHED --> AMENDED : Grade amendment approved by registrar
    PUBLISHED --> PUBLISHED : Grade queries resolved without change

    AMENDED --> [*] : Amended grade becomes the final record
```

---

## Attendance Session State Machine

```mermaid
stateDiagram-v2
    [*] --> SCHEDULED : Session created for a class date

    SCHEDULED --> IN_PROGRESS : Class session begins; faculty opens attendance

    IN_PROGRESS --> MARKED : Faculty submits attendance for all students
    IN_PROGRESS --> CANCELLED : Session cancelled (faculty absent, holiday etc.)

    MARKED --> MARKED : Faculty updates individual attendance record (within allowed window)
    MARKED --> CLOSED : Edit window closes; attendance finalized

    CANCELLED --> [*]
    CLOSED --> [*]
```

---

## Fee Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> GENERATED : Invoice created at start of semester

    GENERATED --> PENDING : Invoice sent to student; awaiting payment
    GENERATED --> WAIVED : Invoice fully waived by admin

    PENDING --> PARTIALLY_PAID : Partial installment received
    PENDING --> PAID : Full payment received
    PENDING --> OVERDUE : Due date passes without payment

    PARTIALLY_PAID --> PAID : Remaining balance paid
    PARTIALLY_PAID --> OVERDUE : Due date passes with outstanding balance

    OVERDUE --> PAID : Late payment received
    OVERDUE --> WAIVED : Admin waives overdue dues

    PAID --> [*]
    WAIVED --> [*]
```

---

## Transcript Request State Machine

```mermaid
stateDiagram-v2
    [*] --> REQUESTED : Student submits transcript request

    REQUESTED --> ON_HOLD : Active account holds detected
    REQUESTED --> PENDING_REVIEW : No holds; sent to registrar queue

    ON_HOLD --> PENDING_REVIEW : Student resolves all holds

    PENDING_REVIEW --> GENERATING : Registrar approves request
    PENDING_REVIEW --> REJECTED : Registrar rejects request (incomplete records)

    GENERATING --> ISSUED : PDF generated, signed, and delivered

    ISSUED --> [*]
    REJECTED --> [*]
```

---

## Leave Application State Machine

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED : Student submits leave application

    SUBMITTED --> UNDER_REVIEW : Faculty or admin opens application

    UNDER_REVIEW --> APPROVED : Faculty approves leave request
    UNDER_REVIEW --> REJECTED : Faculty rejects with reason

    APPROVED --> EXCUSED : Attendance marked as excused for leave period
    REJECTED --> [*]
    EXCUSED --> [*]
```

---

## Financial Aid Application State Machine

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED : Student submits financial aid application

    SUBMITTED --> DOCUMENTS_PENDING : Admin requests additional documents
    SUBMITTED --> UNDER_REVIEW : Application complete; admin reviewing

    DOCUMENTS_PENDING --> UNDER_REVIEW : Student uploads requested documents

    UNDER_REVIEW --> APPROVED : Admin approves aid
    UNDER_REVIEW --> REJECTED : Admin rejects with reason

    APPROVED --> DISBURSED : Aid credited to student fee account

    DISBURSED --> [*]
    REJECTED --> [*]
```

## Implementation-Ready Addendum for State Machine Diagrams

### Purpose in This Artifact
Adds legal transitions and forbidden transitions with reason codes.

### Scope Focus
- Formal lifecycle state machines
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

### Supplemental Mermaid (Artifact-Specific)
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Posted
    Posted --> Amended: createNewVersion
    Amended --> Posted
    Posted --> Voided: registrarException
```

#### Implementation Rules
- Enrollment lifecycle operations must emit auditable events with correlation IDs and actor scope.
- Grade and transcript actions must preserve immutability through versioned records; no destructive updates.
- RBAC must be combined with context constraints (term, department, assigned section, advisee).
- External integrations must remain contract-first with explicit versioning and backward-compatibility strategy.

#### Acceptance Criteria
1. Business rules are testable and mapped to policy IDs in this artifact.
2. Failure paths (authorization, policy window, downstream sync) are explicitly documented.
3. Data ownership and source-of-truth boundaries are clearly identified.
4. Diagram and narrative remain consistent for the scenarios covered in this file.

