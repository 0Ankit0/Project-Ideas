# Domain Model

## Overview
The domain model captures the key entities, their attributes, and relationships within the Employee Management System.

---

## Core Domain Model

```mermaid
classDiagram
    class Employee {
        +String employeeId
        +String firstName
        +String lastName
        +String email
        +String phone
        +Date dateOfBirth
        +Date dateOfJoining
        +EmploymentStatus status
        +Grade grade
        +Department department
        +Designation designation
        +Employee reportingManager
    }

    class Department {
        +int id
        +String name
        +String code
        +CostCenter costCenter
        +Department parent
    }

    class Designation {
        +int id
        +String title
        +Grade grade
    }

    class LeaveBalance {
        +Employee employee
        +LeaveType type
        +float entitled
        +float used
        +float pending
        +float available
    }

    class LeaveRequest {
        +int id
        +Employee employee
        +LeaveType type
        +Date startDate
        +Date endDate
        +float days
        +String reason
        +LeaveStatus status
        +Employee approver
    }

    class AttendanceRecord {
        +int id
        +Employee employee
        +Date date
        +DateTime checkIn
        +DateTime checkOut
        +float workedHours
        +AttendanceStatus status
    }

    class PayrollRun {
        +int id
        +String period
        +PayrollRunStatus status
        +Date processedAt
        +Date finalizedAt
    }

    class PayrollRecord {
        +int id
        +PayrollRun run
        +Employee employee
        +float basicPay
        +float grossPay
        +float totalDeductions
        +float netPay
    }

    class Payslip {
        +int id
        +PayrollRecord record
        +String pdfUrl
        +Date generatedAt
    }

    class AppraisalCycle {
        +int id
        +String name
        +CycleType type
        +Date startDate
        +Date endDate
        +CycleStatus status
    }

    class PerformanceReview {
        +int id
        +AppraisalCycle cycle
        +Employee employee
        +Employee reviewer
        +float overallScore
        +ReviewStatus status
    }

    class Goal {
        +int id
        +Employee employee
        +AppraisalCycle cycle
        +String title
        +float weightage
        +float progressPercent
        +GoalStatus status
    }

    Employee "1" --> "1" Department
    Employee "1" --> "1" Designation
    Employee "many" --> "1" Employee : reports to
    Employee "1" --> "many" LeaveBalance
    Employee "1" --> "many" LeaveRequest
    Employee "1" --> "many" AttendanceRecord
    Employee "1" --> "many" PayrollRecord
    Employee "1" --> "many" PerformanceReview
    Employee "1" --> "many" Goal
    PayrollRun "1" --> "many" PayrollRecord
    PayrollRecord "1" --> "1" Payslip
    AppraisalCycle "1" --> "many" PerformanceReview
    AppraisalCycle "1" --> "many" Goal
```

---

## Payroll Domain Model

```mermaid
classDiagram
    class SalaryStructure {
        +int id
        +Employee employee
        +float basicPay
        +float hra
        +float transportAllowance
        +float medicalAllowance
        +float specialAllowance
        +Date effectiveFrom
    }

    class PayrollRecord {
        +int id
        +PayrollRun run
        +Employee employee
        +SalaryStructure salaryStructure
        +float grossPay
        +float lopDeduction
        +float pfEmployee
        +float pfEmployer
        +float esiEmployee
        +float esiEmployer
        +float tds
        +float totalDeductions
        +float netPay
    }

    class ExpenseClaim {
        +int id
        +Employee employee
        +String category
        +float amount
        +String receiptUrl
        +ClaimStatus status
        +Date submittedAt
    }

    class Bonus {
        +int id
        +Employee employee
        +BonusType type
        +float amount
        +String remarks
        +PayrollRun payrollRun
    }

    PayrollRecord "1" --> "1" SalaryStructure
    PayrollRecord "many" --> "1" PayrollRun
    PayrollRecord "many" --> "many" ExpenseClaim : includes
    PayrollRecord "many" --> "many" Bonus : includes
```

---

## Leave & Attendance Domain Model

```mermaid
classDiagram
    class LeavePolicy {
        +int id
        +String name
        +String applicableTo
    }

    class LeaveType {
        +int id
        +LeavePolicy policy
        +String name
        +float annualEntitlement
        +bool carryForwardAllowed
        +float maxCarryForward
        +bool encashmentAllowed
    }

    class LeaveAccrual {
        +int id
        +Employee employee
        +LeaveType type
        +float accruedDays
        +Date accrualDate
    }

    class Shift {
        +int id
        +String name
        +Time startTime
        +Time endTime
        +ShiftType type
    }

    class ShiftAssignment {
        +int id
        +Employee employee
        +Shift shift
        +Date effectiveFrom
        +Date effectiveTo
    }

    class Timesheet {
        +int id
        +Employee employee
        +Date weekStart
        +TimesheetStatus status
        +float totalHours
    }

    class TimesheetEntry {
        +int id
        +Timesheet timesheet
        +Date date
        +String projectCode
        +float hours
        +String notes
    }

    LeavePolicy "1" --> "many" LeaveType
    LeaveType "1" --> "many" LeaveAccrual
    Shift "1" --> "many" ShiftAssignment
    Timesheet "1" --> "many" TimesheetEntry
```

---

---

## Process Narrative (Business domain boundaries)
1. **Initiate**: Domain Lead captures the primary change request for **Domain Model** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to business domain boundaries.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Domain Registry executes the approved path and enforces ubiquitous language checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm domain cohesion.

## Role/Permission Matrix (Domain Model)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View domain model artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Business domain boundaries)
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

## Integration Behavior (Domain Model)
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

