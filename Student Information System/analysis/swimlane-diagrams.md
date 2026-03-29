# Swimlane Diagrams

## Overview
Swimlane (BPMN-style) diagrams showing cross-department workflows in the Student Information System.

---

## Course Enrollment Process

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant ADV as Academic Advisor
    participant REG as Registrar

    STU->>SIS: Browse course catalog
    SIS-->>STU: Display available courses

    STU->>SIS: Select course and request enrollment
    SIS->>SIS: Validate prerequisites
    SIS->>SIS: Check seat availability

    alt Prerequisites Not Met
        SIS-->>STU: Show missing prerequisites
    else Seats Full
        SIS-->>STU: Offer waitlist
        STU->>SIS: Join waitlist
        SIS-->>STU: Confirm waitlist position
    else Normal Enrollment
        SIS->>SIS: Create enrollment record
        SIS-->>STU: Send enrollment confirmation
        SIS-->>ADV: Notify advisor of enrollment update
    end

    Note over REG: Registrar monitors enrollment stats during window
    REG->>SIS: Review enrollment summary
    SIS-->>REG: Display enrollment statistics
```

---

## Grade Submission and Publication Workflow

```mermaid
sequenceDiagram
    participant FAC as Faculty
    participant SIS as SIS Platform
    participant REG as Registrar
    participant STU as Student
    participant PAR as Parent

    FAC->>SIS: Open grade entry for course
    SIS-->>FAC: Display student roster

    FAC->>SIS: Enter/upload grades
    SIS->>SIS: Validate grade format
    FAC->>SIS: Submit final grades

    SIS-->>REG: Notify grades submitted for review
    REG->>SIS: Review grade sheet

    alt Grades Rejected
        REG->>SIS: Return grades with comments
        SIS-->>FAC: Notify faculty of rejection
        FAC->>SIS: Revise and resubmit grades
    else Grades Approved
        REG->>SIS: Approve grade publication
        SIS->>SIS: Calculate GPA and CGPA
        SIS->>SIS: Update academic standing
        SIS-->>STU: Notify grade publication
        SIS-->>PAR: Notify parent/guardian
    end
```

---

## Attendance Alert and Intervention Workflow

```mermaid
sequenceDiagram
    participant FAC as Faculty
    participant SIS as SIS Platform
    participant STU as Student
    participant PAR as Parent
    participant ADV as Academic Advisor

    FAC->>SIS: Mark class attendance
    SIS->>SIS: Calculate attendance percentage

    alt Below Warning Threshold (below 80%)
        SIS-->>STU: Send attendance warning notification
        SIS-->>PAR: Send alert to parent/guardian
    end

    alt Below Critical Threshold (below 75%)
        SIS-->>STU: Send critical attendance warning
        SIS-->>ADV: Alert academic advisor
        SIS-->>PAR: Alert parent/guardian
        ADV->>SIS: Schedule intervention meeting with student
        ADV->>SIS: Log intervention notes
    end

    alt Exam Block Threshold (below 65%)
        SIS->>SIS: Flag student for exam block
        SIS-->>STU: Notify exam debarment warning
        STU->>SIS: Submit attendance condonation request
        ADV->>SIS: Review and approve/reject condonation
    end
```

---

## Financial Aid Application Workflow

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant ADM as Admin Staff
    participant FIN as Finance Office

    STU->>SIS: Open financial aid application
    SIS-->>STU: Display aid programs and criteria

    STU->>SIS: Fill application form and upload documents
    STU->>SIS: Submit application

    SIS-->>ADM: Notify new aid application
    ADM->>SIS: Review application and documents

    alt Documents Incomplete
        ADM->>SIS: Request additional documents
        SIS-->>STU: Notify document request
        STU->>SIS: Upload requested documents
        ADM->>SIS: Re-review application
    end

    ADM->>SIS: Approve or reject application
    SIS-->>STU: Notify aid decision

    alt Aid Approved
        SIS-->>FIN: Notify finance office of aid approval
        FIN->>SIS: Process aid disbursement
        SIS->>SIS: Apply aid credit to student fee account
        SIS-->>STU: Notify aid applied to account
    end
```

---

## Student Admission and Onboarding Workflow

```mermaid
sequenceDiagram
    participant STU as Applicant/Student
    participant SIS as SIS Platform
    participant ADM as Admin Staff
    participant REG as Registrar
    participant ADV as Academic Advisor

    STU->>SIS: Submit admission application
    SIS-->>ADM: Notify new application

    ADM->>SIS: Review application and documents
    ADM->>SIS: Make admission decision

    alt Rejected
        SIS-->>STU: Send rejection notification
    else Accepted
        SIS-->>STU: Send admission offer
        STU->>SIS: Accept offer and pay confirmation fee

        SIS->>SIS: Create student account and assign ID
        SIS-->>REG: Notify new student registration
        REG->>SIS: Assign degree program and semester

        SIS->>SIS: Assign academic advisor
        SIS-->>ADV: Notify new student assignment
        SIS-->>STU: Send login credentials and orientation details

        ADV->>SIS: Schedule initial advising session
        SIS-->>STU: Notify enrollment window opening
    end
```

---

## Transcript Request and Issuance Workflow

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant REG as Registrar

    STU->>SIS: Submit transcript request
    SIS->>SIS: Check for account holds

    alt Active Holds
        SIS-->>STU: Notify of holds blocking request
    else No Holds
        SIS-->>REG: Place transcript request in queue
        REG->>SIS: Review student academic record

        alt Records Incomplete
            REG->>SIS: Flag issue
            SIS-->>STU: Notify of record issue
        else Records Complete
            REG->>SIS: Approve transcript generation
            SIS->>SIS: Generate official transcript PDF
            SIS->>SIS: Apply digital signature

            alt Download
                SIS-->>STU: Notify transcript ready for download
            else Email Delivery
                SIS-->>STU: Send transcript via secure email
            end
        end
    end
```

---

## Exam Scheduling and Hall Allocation Workflow

```mermaid
sequenceDiagram
    participant ADM as Admin Staff
    participant SIS as SIS Platform
    participant FAC as Faculty
    participant STU as Student
    participant REG as Registrar

    ADM->>SIS: Create exam schedule for semester
    SIS->>SIS: Check for student exam conflicts
    SIS->>SIS: Allocate exam halls and seating

    alt Conflicts Found
        SIS-->>ADM: Show conflict report
        ADM->>SIS: Resolve conflicts and reschedule
    else No Conflicts
        ADM->>SIS: Publish exam schedule
        SIS-->>STU: Send exam schedule notification
        SIS-->>FAC: Notify faculty of invigilation duties
    end

    Note over STU: Student downloads hall ticket
    STU->>SIS: Request hall ticket
    SIS->>SIS: Check attendance eligibility
    alt Attendance Below Threshold
        SIS-->>STU: Block hall ticket; notify of debarment
    else Eligible
        SIS-->>STU: Generate and deliver hall ticket
    end

    REG->>SIS: Finalize exam register
    SIS-->>REG: Confirm all hall tickets issued
```

## Implementation-Ready Addendum for Swimlane Diagrams

### Purpose in This Artifact
Clarifies ownership handoffs between student, faculty, advisor, registrar, finance, and LMS.

### Scope Focus
- Cross-team swimlane constraints
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

