# Data Flow Diagrams

## Overview
Data flow diagrams showing how data moves through the Student Information System.

---

## Level 0: Context DFD (System Overview)

```mermaid
graph LR
    Student((Student))
    Faculty((Faculty))
    Admin((Admin))
    Registrar((Registrar))
    Parent((Parent))
    PayGW((Payment<br>Gateway))
    LDAP((LDAP / SSO))

    subgraph SIS ["Student Information System"]
        Process[SIS Processing]
    end

    Student -->|Registration, enrollment requests, fee payments| Process
    Process -->|Confirmation, grades, transcripts, receipts| Student

    Faculty -->|Grade entries, attendance data, announcements| Process
    Process -->|Course rosters, reports, approvals| Faculty

    Admin -->|User management, course config, fee structures| Process
    Process -->|Reports, dashboards, system status| Admin

    Registrar -->|Grade approvals, transcript issuance| Process
    Process -->|Student records, audit reports| Registrar

    Parent -->|View requests| Process
    Process -->|Grade/attendance/fee summaries| Parent

    Process -->|Payment initiation| PayGW
    PayGW -->|Payment confirmation/failure| Process

    Process -->|Authentication requests| LDAP
    LDAP -->|Auth tokens, user attributes| Process
```

---

## Level 1: DFD - Student Academic Workflow

```mermaid
graph LR
    Student((Student))

    subgraph "SIS Processes"
        P1[1.0 Enrollment Process]
        P2[2.0 Grade Management]
        P3[3.0 Attendance Tracking]
        P4[4.0 Fee Processing]
        P5[5.0 Transcript Generation]
    end

    subgraph "Data Stores"
        DS1[(Enrollment Records)]
        DS2[(Academic Records)]
        DS3[(Attendance Records)]
        DS4[(Fee Records)]
        DS5[(Document Store)]
    end

    Student -->|Enrollment request| P1
    P1 -->|Enrollment confirmation| Student
    P1 -->|Enrollment data| DS1
    DS1 -->|Student roster| P2

    P2 -->|Grade notification| Student
    P2 -->|Grade data| DS2
    DS2 -->|Grade history| P5

    P3 -->|Attendance alert| Student
    P3 -->|Attendance data| DS3

    Student -->|Fee payment| P4
    P4 -->|Receipt| Student
    P4 -->|Payment records| DS4

    Student -->|Transcript request| P5
    P5 -->|Official transcript| Student
    P5 -->|Transcript document| DS5
```

---

## Level 1: DFD - Faculty and Academic Operations

```mermaid
graph LR
    Faculty((Faculty))
    Registrar((Registrar))

    subgraph "Processes"
        P1[1.0 Course Management]
        P2[2.0 Grade Entry]
        P3[3.0 Attendance Marking]
        P4[4.0 Grade Review & Publication]
    end

    subgraph "Data Stores"
        DS1[(Course Catalog)]
        DS2[(Student Roster)]
        DS3[(Grade Records)]
        DS4[(Attendance Records)]
    end

    Faculty -->|Course material upload| P1
    P1 -->|Course details| Faculty
    P1 <-->|Course data| DS1
    DS1 -->|Enrolled students| DS2

    DS2 -->|Student list| P2
    Faculty -->|Grade submission| P2
    P2 -->|Draft/final grades| DS3
    DS3 -->|Grades for review| P4

    Faculty -->|Attendance marks| P3
    P3 -->|Attendance records| DS4
    DS4 -->|Attendance summary| Faculty

    Registrar -->|Approval action| P4
    P4 -->|Published grades| DS3
    P4 -->|Grade notification| Faculty
```

---

## Level 1: DFD - Fee and Financial Operations

```mermaid
graph LR
    Student((Student))
    Admin((Admin))
    Finance((Finance Office))
    PayGW((Payment Gateway))

    subgraph "Processes"
        P1[1.0 Fee Structure Management]
        P2[2.0 Invoice Generation]
        P3[3.0 Payment Processing]
        P4[4.0 Financial Aid Management]
    end

    subgraph "Data Stores"
        DS1[(Fee Structures)]
        DS2[(Invoices)]
        DS3[(Payment Records)]
        DS4[(Aid Applications)]
    end

    Admin -->|Fee configuration| P1
    P1 -->|Fee structure data| DS1

    DS1 -->|Fee rules| P2
    Student -->|Trigger invoice| P2
    P2 -->|Invoice details| Student
    P2 -->|Invoice records| DS2

    Student -->|Payment initiation| P3
    P3 -->|Payment request| PayGW
    PayGW -->|Payment confirmation| P3
    P3 -->|Receipt| Student
    P3 -->|Payment data| DS3

    Student -->|Aid application| P4
    Finance -->|Aid approval| P4
    P4 -->|Aid credit| DS2
    P4 -->|Aid decision| Student
    P4 -->|Aid data| DS4
```

---

## Level 2: DFD - Enrollment Validation Sub-Process

```mermaid
graph LR
    Student((Student))

    subgraph "Enrollment Validation"
        P1[1.1 Check Enrollment Window]
        P2[1.2 Validate Prerequisites]
        P3[1.3 Check Seat Availability]
        P4[1.4 Detect Schedule Conflicts]
        P5[1.5 Create Enrollment Record]
    end

    DS1[(Enrollment Windows)]
    DS2[(Prerequisite Rules)]
    DS3[(Course Sections)]
    DS4[(Student Timetable)]
    DS5[(Enrollment Records)]

    Student -->|Enrollment request| P1
    DS1 -->|Window dates| P1
    P1 -->|Window valid| P2

    DS2 -->|Prerequisite rules| P2
    P2 -->|Prerequisites met| P3

    DS3 -->|Seat data| P3
    P3 -->|Seat available| P4

    DS4 -->|Existing schedule| P4
    P4 -->|No conflict| P5

    P5 -->|Enrollment confirmation| Student
    P5 -->|Enrollment record| DS5
```

## Implementation-Ready Addendum for Data Flow Diagrams

### Purpose in This Artifact
Documents authoritative source of truth and anti-corruption boundaries.

### Scope Focus
- Data lineage controls
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

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

