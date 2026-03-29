# C4 Code Diagram

## Overview
C4 Level 4 code-level diagrams for key domain modules in the Student Information System, showing class-level interactions within specific components.

---

## Enrollment Service Code Diagram

```mermaid
graph TB
    subgraph "Enrollment Module"
        subgraph "Routers"
            EnrollRouter[EnrollmentRouter<br>POST /enrollments<br>DELETE /enrollments/{id}<br>POST /waitlists]
        end

        subgraph "Services"
            EnrollService[EnrollmentService<br>+enrollStudent()<br>+dropCourse()<br>+joinWaitlist()]
            WaitlistService[WaitlistService<br>+addToWaitlist()<br>+promoteFromWaitlist()<br>+getPosition()]
        end

        subgraph "Validators"
            PrereqValidator[PrerequisiteValidator<br>+validate(studentId, courseId)<br>+getCompletedCourses()]
            ConflictChecker[ConflictChecker<br>+detect(studentId, sectionId)<br>+getStudentSchedule()]
        end

        subgraph "Repositories"
            EnrollRepo[EnrollmentRepository<br>+create()<br>+findByStudent()<br>+updateStatus()]
            SectionRepo[CourseSectionRepository<br>+findById()<br>+decrementSeats()<br>+getAvailableSeats()]
            WaitlistRepo[WaitlistRepository<br>+create()<br>+findBySection()<br>+reorderPositions()]
        end

        subgraph "Events"
            EnrollEvent[EnrollmentEventPublisher<br>+publishEnrolled()<br>+publishDropped()<br>+publishWaitlisted()]
        end
    end

    EnrollRouter --> EnrollService
    EnrollService --> PrereqValidator
    EnrollService --> ConflictChecker
    EnrollService --> WaitlistService
    EnrollService --> EnrollRepo
    EnrollService --> SectionRepo
    WaitlistService --> WaitlistRepo
    EnrollService --> EnrollEvent
    WaitlistService --> EnrollEvent
```

---

## Grade Service Code Diagram

```mermaid
graph TB
    subgraph "Academics Module"
        subgraph "Routers"
            GradeRouter[GradeRouter<br>POST /faculty/courses/{id}/grades<br>POST /registrar/grades/{id}/publish<br>POST /grades/{id}/amend]
        end

        subgraph "Services"
            GradeService[GradeService<br>+submitGrades()<br>+publishGrades()<br>+requestAmendment()]
            GPAService[GPAService<br>+calculateSGPA()<br>+calculateCGPA()<br>+updateStanding()]
            AmendmentService[GradeAmendmentService<br>+createRequest()<br>+approve()<br>+reject()]
        end

        subgraph "Calculators"
            GPACalc[GPACalculator<br>+computeGradePoints(grade)<br>+sumWeightedPoints()<br>+divideByCredits()]
            StandingCalc[AcademicStandingCalculator<br>+classify(cgpa)<br>+checkProbation()<br>+checkDismissal()]
        end

        subgraph "Repositories"
            GradeRepo[GradeRepository<br>+bulkCreate()<br>+findBySection()<br>+updateStatus()]
            GPARepo[StudentGPARepository<br>+upsert()<br>+findByStudent()<br>+getHistory()]
            AmendRepo[GradeAmendmentRepository<br>+create()<br>+findPending()<br>+resolve()]
        end

        subgraph "Events"
            GradeEvent[GradeEventPublisher<br>+publishGradesPublished()<br>+publishAmendmentRequest()]
        end
    end

    GradeRouter --> GradeService
    GradeService --> AmendmentService
    GradeService --> GPAService
    GPAService --> GPACalc
    GPAService --> StandingCalc
    GradeService --> GradeRepo
    GPAService --> GPARepo
    AmendmentService --> AmendRepo
    GradeService --> GradeEvent
```

---

## Attendance Service Code Diagram

```mermaid
graph TB
    subgraph "Attendance Module"
        subgraph "Routers"
            AttRouter[AttendanceRouter<br>POST /faculty/sessions/{id}/attendance<br>GET /students/me/attendance<br>POST /students/me/leaves]
        end

        subgraph "Services"
            SessionService[SessionService<br>+createSession()<br>+getSessionsForSection()]
            AttService[AttendanceService<br>+markAttendance()<br>+calculatePercentage()<br>+checkThresholds()]
            LeaveService[LeaveService<br>+submitLeave()<br>+approveLeave()<br>+rejectLeave()]
        end

        subgraph "Processors"
            ThresholdProc[ThresholdAlertProcessor<br>+processWarning()<br>+processCritical()<br>+blockExam()]
            QRProcessor[QRCodeProcessor<br>+generate(sessionId)<br>+validate(token, sessionId)]
            EligibilityChecker[ExamEligibilityChecker<br>+isEligible(studentId, sectionId)<br>+getDebarmentReason()]
        end

        subgraph "Repositories"
            SessionRepo[SessionRepository<br>+create()<br>+findBySection()]
            AttRepo[AttendanceRecordRepository<br>+bulkUpsert()<br>+getSummary()<br>+getPercentage()]
            LeaveRepo[LeaveRepository<br>+create()<br>+findPending()<br>+updateStatus()]
        end

        subgraph "Events"
            AttEvent[AttendanceEventPublisher<br>+publishAlert()<br>+publishLeaveStatus()]
        end
    end

    AttRouter --> SessionService
    AttRouter --> AttService
    AttRouter --> LeaveService
    AttService --> ThresholdProc
    AttService --> QRProcessor
    AttService --> EligibilityChecker
    AttService --> SessionRepo
    AttService --> AttRepo
    LeaveService --> LeaveRepo
    ThresholdProc --> AttEvent
    LeaveService --> AttEvent
```

---

## Fee Payment Code Diagram

```mermaid
graph TB
    subgraph "Fee Module"
        subgraph "Routers"
            FeeRouter[FeeRouter<br>POST /fees/payments/initiate<br>POST /fees/payments/verify<br>POST /fees/payments/webhooks/{gw}]
        end

        subgraph "Services"
            PaymentService[PaymentService<br>+initiate()<br>+verify()<br>+processWebhook()]
            InvoiceService[InvoiceService<br>+generate()<br>+updateStatus()<br>+applyAid()]
            ReceiptService[ReceiptService<br>+generate(paymentId)<br>+upload()<br>+getUrl()]
        end

        subgraph "Gateway Adapters"
            GatewayFactory[PaymentGatewayFactory<br>+getAdapter(gateway)]
            BankAdapter[BankTransferAdapter<br>+createSession()<br>+verify()]
            CardAdapter[CardGatewayAdapter<br>+createSession()<br>+verify()]
            UPIAdapter[UPIGatewayAdapter<br>+createSession()<br>+verify()]
        end

        subgraph "Repositories"
            InvoiceRepo[InvoiceRepository<br>+findByStudent()<br>+updateStatus()]
            PaymentRepo[PaymentRepository<br>+create()<br>+updateStatus()<br>+findByGatewayRef()]
        end

        subgraph "Events"
            FeeEvent[FeeEventPublisher<br>+publishPaymentSuccess()<br>+publishPaymentFailed()]
        end
    end

    FeeRouter --> PaymentService
    FeeRouter --> InvoiceService
    PaymentService --> GatewayFactory
    GatewayFactory --> BankAdapter
    GatewayFactory --> CardAdapter
    GatewayFactory --> UPIAdapter
    PaymentService --> ReceiptService
    PaymentService --> InvoiceService
    PaymentService --> PaymentRepo
    InvoiceService --> InvoiceRepo
    PaymentService --> FeeEvent
```

## Implementation-Ready Addendum for C4 Code Diagram

### Purpose in This Artifact
Defines modules and anti-corruption layer boundaries for integrations.

### Scope Focus
- Code-level package boundaries
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

