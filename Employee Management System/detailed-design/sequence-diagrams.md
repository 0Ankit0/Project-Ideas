# Sequence Diagrams

## Overview
Internal sequence diagrams showing object-level interactions within the Employee Management System.

---

## 1. Leave Application - Internal Flow

```mermaid
sequenceDiagram
    participant Router as LeaveRouter
    participant Service as LeaveService
    participant PolicyValidator as LeavePolicyValidator
    participant BalanceRepo as LeaveBalanceRepository
    participant RequestRepo as LeaveRequestRepository
    participant HolidayRepo as HolidayRepository
    participant NotifService as NotificationService

    Router->>Service: applyLeave(employeeId, request)
    Service->>PolicyValidator: validate(employeeId, request)
    PolicyValidator->>BalanceRepo: getBalance(employeeId, leaveTypeId)
    BalanceRepo-->>PolicyValidator: LeaveBalance
    PolicyValidator->>HolidayRepo: getHolidays(locationCode, period)
    HolidayRepo-->>PolicyValidator: List~Holiday~
    PolicyValidator-->>Service: ValidationResult

    alt Validation Fails
        Service-->>Router: 422 ValidationError
    else Validation Passes
        Service->>RequestRepo: create(leaveRequest)
        RequestRepo-->>Service: LeaveRequest
        Service->>BalanceRepo: reservePending(employeeId, leaveTypeId, days)
        Service->>NotifService: notifyManager(request)
        NotifService-->>Service: OK
        Service-->>Router: 201 Created
    end
```

---

## 2. Payroll Run - Internal Flow

```mermaid
sequenceDiagram
    participant Router as PayrollRouter
    participant RunService as PayrollRunService
    participant EmployeeRepo as EmployeeRepository
    participant SalaryRepo as SalaryStructureRepository
    participant AttendanceRepo as AttendanceRepository
    participant TaxEngine as TaxCalculationEngine
    participant PayslipService as PayslipService
    participant NotifService as NotificationService
    participant BankAdapter as BankTransferAdapter

    Router->>RunService: initiate(period, initiatedBy)
    RunService->>RunService: lockPeriodData(period)
    RunService->>EmployeeRepo: getActiveEmployees()
    EmployeeRepo-->>RunService: List~Employee~

    loop For each Employee
        RunService->>SalaryRepo: getStructure(employeeId, period)
        SalaryRepo-->>RunService: SalaryStructure
        RunService->>AttendanceRepo: getLOPDays(employeeId, period)
        AttendanceRepo-->>RunService: lopDays
        RunService->>TaxEngine: computeDeductions(salary, declarations)
        TaxEngine-->>RunService: DeductionBreakdown
        RunService->>RunService: computeNetPay(gross, deductions)
    end

    RunService-->>Router: PayrollRunSummary + Exceptions

    Router->>RunService: approve(runId, approverId)
    RunService->>PayslipService: generateAll(runId)
    PayslipService->>NotifService: deliverPayslips(employeeList)
    RunService->>BankAdapter: submitTransferFile(runId)
    BankAdapter-->>RunService: Acknowledgement
    RunService-->>Router: 200 Finalized
```

---

## 3. Appraisal Review - Internal Flow

```mermaid
sequenceDiagram
    participant Router as AppraisalRouter
    participant ReviewService as ReviewService
    participant GoalRepo as GoalRepository
    participant KRARepo as KRARepository
    participant ReviewRepo as ReviewRepository
    participant RatingEngine as RatingCalculationEngine
    participant NotifService as NotificationService

    Router->>ReviewService: submitSelfAssessment(reviewId, ratings)
    ReviewService->>ReviewRepo: get(reviewId)
    ReviewRepo-->>ReviewService: PerformanceReview
    ReviewService->>KRARepo: getForCycle(cycleId)
    KRARepo-->>ReviewService: List~KRA~
    ReviewService->>ReviewRepo: saveKRARatings(reviewId, ratings)
    ReviewService->>ReviewRepo: updateStatus(reviewId, SELF_SUBMITTED)
    ReviewService->>NotifService: notifyManager(reviewId)
    ReviewService-->>Router: 200 OK

    Router->>ReviewService: submitManagerReview(reviewId, ratings, recommendation)
    ReviewService->>ReviewRepo: saveManagerRatings(reviewId, ratings)
    ReviewService->>RatingEngine: computeWeightedScore(kraRatings, weights)
    RatingEngine-->>ReviewService: overallScore
    ReviewService->>ReviewRepo: updateStatus(reviewId, MANAGER_SUBMITTED)
    ReviewService->>NotifService: notifyHR(reviewId)
    ReviewService-->>Router: 200 OK

    Router->>ReviewService: finalize(reviewId, hrUserId)
    ReviewService->>ReviewRepo: lockRatings(reviewId)
    ReviewService->>ReviewRepo: updateStatus(reviewId, FINALIZED)
    ReviewService->>NotifService: notifyEmployee(reviewId)
    ReviewService-->>Router: 200 OK
```

---

## 4. Attendance Punch - Internal Flow

```mermaid
sequenceDiagram
    participant BiometricAPI as BiometricEndpoint
    participant AttendanceService as AttendanceService
    participant ShiftService as ShiftService
    participant AttendanceRepo as AttendanceRepository
    participant NotifService as NotificationService

    BiometricAPI->>AttendanceService: recordPunch(employeeId, timestamp, type)
    AttendanceService->>ShiftService: getActiveShift(employeeId, date)
    ShiftService-->>AttendanceService: Shift

    alt Check-In
        AttendanceService->>AttendanceRepo: createRecord(employeeId, date, checkIn)
        AttendanceRepo-->>AttendanceService: AttendanceRecord
        AttendanceService->>AttendanceService: flagIfLate(checkIn, shiftStart)
        alt Late Arrival
            AttendanceService->>NotifService: notifyManager(employeeId, lateFlag)
        end
    else Check-Out
        AttendanceService->>AttendanceRepo: updateCheckOut(recordId, checkOut)
        AttendanceService->>AttendanceService: calculateWorkedHours(checkIn, checkOut)
        AttendanceService->>AttendanceRepo: saveWorkedHours(recordId, hours)
    end

    AttendanceService-->>BiometricAPI: 201 Created
```

---

---

## Process Narrative (Interaction sequence design)
1. **Initiate**: Solution Architect captures the primary change request for **Sequence Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to interaction sequence design.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Orchestrator executes the approved path and enforces step ordering validator at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm transaction choreography.

## Role/Permission Matrix (Sequence Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View sequence diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Interaction sequence design)
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> InReview: submit
    InReview --> Approved: functional + technical checks
    InReview --> Rework: feedback
    Rework --> InReview: resubmit
    Approved --> Released: publish/deploy
    Released --> Monitored: telemetry active
    Monitored --> Stable: controls pass
    Monitored --> Incident: control failure
    Incident --> Rework: corrective action
    Stable --> [*]
```

## Integration Behavior (Sequence Diagrams)
| Integration | Trigger | Expected Behavior | Failure Handling |
|---|---|---|---|
| IAM / RBAC | Approval or assignment change | Sync permission scopes for affected actors | Retry + alert on drift |
| Workflow/Event Bus | State transition | Publish canonical event with correlation ID | Dead-letter + replay tooling |
| Payroll/Benefits (where applicable) | Compensation/lifecycle change | Apply financial side-effects only after approved state | Hold payout + reconcile |
| Notification Channels | Review decision, exception, due date | Deliver actionable notice to owners and requestors | Escalation after SLA breach |
| Audit/GRC Archive | Any controlled transition | Store immutable evidence bundle | Block progression if evidence missing |

## Onboarding/Offboarding Edge Cases (Concrete)
- **Rehire with residual access**: If a rehire request reuses a prior identity, retain historical employee ID linkage but force fresh role entitlement approval before day-1 access.
- **Early start-date acceleration**: When onboarding date is moved earlier than background-check SLA, block activation and auto-create an exception approval task.
- **Same-day termination**: For involuntary offboarding, revoke privileged access immediately while preserving records under legal hold classification.
- **Rescinded resignation after downstream sync**: If offboarding is canceled after payroll/IAM notifications, execute compensating events and log full reversal trail.

## Compliance/Audit Controls
| Control | Description | Evidence |
|---|---|---|
| Segregation of duties | Requestor and approver cannot be the same identity for controlled actions | Approval chain + user IDs |
| Transition integrity | Only allowed state transitions can be persisted | Transition log + rejection reasons |
| Timely deprovisioning | Offboarding access revocation meets SLA targets | IAM revocation timestamp report |
| Financial reconciliation | Payroll-impacting changes reconcile before close | Payroll batch diff + sign-off |
| Immutable auditability | Controlled actions are archived in WORM/append-only storage | Hash, retention tag, archive pointer |

