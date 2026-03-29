# C4 Code Diagram

## Overview
C4 Level 4 code-level diagrams for key classes within the Employee Management System's most critical modules.

---

## Payroll Calculation Engine - Code Diagram

```mermaid
classDiagram
    class PayrollRunService {
        -EmployeeRepository employeeRepo
        -SalaryStructureRepository salaryRepo
        -AttendanceRepository attendanceRepo
        -TaxEngine taxEngine
        -PayrollRepository payrollRepo
        -PayslipService payslipService
        -NotificationDispatcher notifDispatcher
        +initiate(period, initiatedBy) PayrollRun
        +getExceptions(runId) List~PayrollException~
        +override(runId, employeeId, overrides) void
        +approve(runId, approverId) void
        -processEmployee(run, employee) PayrollRecord
        -lockPeriodData(period) void
    }

    class SalaryCalculator {
        -TaxEngine taxEngine
        +computeGross(structure) float
        +computeLOP(lopDays, workingDays, gross) float
        +computeNetPay(gross, deductions) float
        +buildRecord(employee, structure, attendance) PayrollRecord
    }

    class TaxEngine {
        -TaxSlabRepository taxSlabRepo
        +computeTDS(annualIncome, declarations) float
        +computePFEmployee(basic) float
        +computePFEmployer(basic) float
        +computeESIEmployee(gross) float
        +computeESIEmployer(gross) float
        +computeGratuityAccrual(basic, yearsOfService) float
    }

    class PayslipService {
        -StorageService storageService
        -EmailService emailService
        -PayslipRepository payslipRepo
        +generate(record) Payslip
        +generateAll(runId) List~Payslip~
        +deliver(payslip, email) void
        +deliverAll(runId) void
        -renderPDF(record) bytes
    }

    PayrollRunService --> SalaryCalculator : uses
    PayrollRunService --> PayslipService : triggers
    SalaryCalculator --> TaxEngine : delegates tax computation
```

---

## Leave Application Service - Code Diagram

```mermaid
classDiagram
    class LeaveApplicationService {
        -LeavePolicyEngine policyEngine
        -LeaveBalanceRepository balanceRepo
        -LeaveRequestRepository requestRepo
        -HolidayRepository holidayRepo
        -NotificationDispatcher notifDispatcher
        +apply(employeeId, request) LeaveRequest
        +cancel(requestId, employeeId) void
        -calculateDays(start, end, holidays) float
    }

    class LeavePolicyEngine {
        -LeavePolicyRepository policyRepo
        +validate(employeeId, request, balance) ValidationResult
        -checkMinNoticePeriod(request, policy) bool
        -checkMaxConsecutiveDays(request, policy) bool
        -checkNoOverlap(employeeId, request) bool
        -checkBalance(balance, requestedDays, policy) bool
    }

    class LeaveApprovalService {
        -LeaveRequestRepository requestRepo
        -LeaveBalanceRepository balanceRepo
        -NotificationDispatcher notifDispatcher
        +approve(requestId, approverId, comment) void
        +reject(requestId, approverId, comment) void
        +delegate(requestId, fromApproverId, toApproverId) void
    }

    class LeaveBalanceService {
        -LeaveBalanceRepository balanceRepo
        -LeavePolicyRepository policyRepo
        +getBalance(employeeId, leaveTypeId) LeaveBalance
        +accrueMonthly(employeeId) void
        +processYearEnd(year) void
        +deduct(employeeId, leaveTypeId, days) void
        +restorePending(employeeId, leaveTypeId, days) void
    }

    LeaveApplicationService --> LeavePolicyEngine : validates
    LeaveApplicationService --> LeaveBalanceService : checks balance
    LeaveApprovalService --> LeaveBalanceService : deducts on approval
```

---

## Performance Review Service - Code Diagram

```mermaid
classDiagram
    class ReviewService {
        -ReviewRepository reviewRepo
        -KRARepository kraRepo
        -RatingEngine ratingEngine
        -NotificationDispatcher notifDispatcher
        +submitSelfAssessment(reviewId, employeeId, ratings) void
        +submitManagerReview(reviewId, managerId, ratings, recommendation) void
        +finalize(reviewId, hrUserId) void
        -validateReviewOwnership(reviewId, employeeId) void
        -validateReviewWindow(cycleId, phase) void
    }

    class RatingEngine {
        +computeWeightedScore(kraRatings, kras) float
        +applyDistributionCurve(teamReviews, curve) List~AdjustedReview~
    }

    class GoalService {
        -GoalRepository goalRepo
        -NotificationDispatcher notifDispatcher
        +create(employeeId, cycleId, goalData) Goal
        +updateProgress(goalId, employeeId, percent, notes) void
        +getTeamGoals(managerId, cycleId) List~Goal~
        -checkOwnership(goalId, employeeId) void
    }

    class PIPService {
        -PIPRepository pipRepo
        -NotificationDispatcher notifDispatcher
        +initiate(employeeId, managerId, pipData) PIP
        +recordCheckIn(pipId, managerId, notes) PIPCheckIn
        +close(pipId, managerId, outcome) void
        -notifyHR(pip) void
    }

    ReviewService --> RatingEngine : computes score
    ReviewService --> GoalService : reads goal progress
```

---

---

## Process Narrative (Code-to-component realization)
1. **Initiate**: Tech Lead captures the primary change request for **C4 Code Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to code-to-component realization.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Code Indexer executes the approved path and enforces dependency conformance checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm design/code parity.

## Role/Permission Matrix (C4 Code Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View c4 code diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Code-to-component realization)
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

## Integration Behavior (C4 Code Diagram)
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

