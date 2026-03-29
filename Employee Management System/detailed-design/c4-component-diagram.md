# C4 Component Diagram

## Overview
C4 Level 3 component diagram for the Employee Management System's API Service, showing internal component structure.

---

## API Service Component Diagram

```mermaid
graph TB
    subgraph "API Service - Internal Components"
        subgraph "Entry Points"
            Router[API Router\nVersioned /api/v1 route groups]
            AuthMiddleware[Auth Middleware\nJWT validation, RBAC enforcement]
            RateLimiter[Rate Limiter\nPer-user and global rate limiting]
        end

        subgraph "IAM Component"
            IAMController[IAM Controller]
            AuthService[Auth Service\nLogin, logout, refresh, 2FA]
            SSOService[SSO Service\nSAML 2.0 / OAuth 2.0]
            SessionRepo[Session Repository]
        end

        subgraph "Employee Component"
            EmployeeController[Employee Controller]
            EmployeeService[Employee Service\nCRUD, transfer, lifecycle]
            OnboardingService[Onboarding Service\nChecklists & task management]
            DocumentService[Document Service\nUpload, download, expiry tracking]
            EmployeeRepo[Employee Repository]
        end

        subgraph "Leave Component"
            LeaveController[Leave Controller]
            LeaveApplicationService[Leave Application Service]
            LeaveApprovalService[Leave Approval Service]
            LeaveBalanceService[Leave Balance Service\nAccrual, deductions, carry-forward]
            LeavePolicyEngine[Leave Policy Engine\nRules validation]
            LeaveRepo[Leave Repository]
        end

        subgraph "Attendance Component"
            AttendanceController[Attendance Controller]
            PunchService[Punch Service\nBiometric event processing]
            ShiftService[Shift Service\nAssignment & roster]
            TimesheetService[Timesheet Service\nApproval workflow]
            AttendanceRepo[Attendance Repository]
        end

        subgraph "Payroll Component"
            PayrollController[Payroll Controller]
            PayrollRunService[Payroll Run Service\nOrchestration]
            SalaryCalculator[Salary Calculator\nGross, LOP, net pay]
            TaxEngine[Tax Calculation Engine\nTDS, PF, ESI]
            PayslipService[Payslip Service\nGenerate & deliver]
            BankTransferService[Bank Transfer Service\nFile generation]
            PayrollRepo[Payroll Repository]
        end

        subgraph "Performance Component"
            PerformanceController[Performance Controller]
            ReviewService[Review Service\nAppraisal workflow]
            GoalService[Goal Service\nSetting & progress]
            PIPService[PIP Service\nCreate, track, close]
            RatingEngine[Rating Calculation Engine\nWeighted KRA scoring]
            PerformanceRepo[Performance Repository]
        end

        subgraph "Notification Component"
            NotifController[Notification Controller]
            NotifDispatcher[Notification Dispatcher\nRoute to email/SMS/push/in-app]
            WSManager[WebSocket Manager\nReal-time push]
            NotifRepo[Notification Repository]
        end

        subgraph "Report Component"
            ReportController[Report Controller]
            ReportJobService[Report Job Service\nAsync generation]
            ReportBuilders[Report Builders\nHR, Payroll, Leave, Performance]
            ReportRepo[Report Repository]
        end
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[(Object Storage)]
        Queue[(Task Queue)]
    end

    Router --> AuthMiddleware
    AuthMiddleware --> RateLimiter
    RateLimiter --> IAMController
    RateLimiter --> EmployeeController
    RateLimiter --> LeaveController
    RateLimiter --> AttendanceController
    RateLimiter --> PayrollController
    RateLimiter --> PerformanceController
    RateLimiter --> NotifController
    RateLimiter --> ReportController

    IAMController --> AuthService
    IAMController --> SSOService
    AuthService --> SessionRepo
    SessionRepo --> Cache

    EmployeeController --> EmployeeService
    EmployeeController --> OnboardingService
    EmployeeService --> DocumentService
    EmployeeService --> EmployeeRepo
    DocumentService --> Storage
    EmployeeRepo --> DB

    LeaveController --> LeaveApplicationService
    LeaveController --> LeaveApprovalService
    LeaveController --> LeaveBalanceService
    LeaveApplicationService --> LeavePolicyEngine
    LeaveApplicationService --> LeaveRepo
    LeaveBalanceService --> Cache
    LeaveRepo --> DB

    AttendanceController --> PunchService
    AttendanceController --> ShiftService
    AttendanceController --> TimesheetService
    AttendanceRepo --> DB

    PayrollController --> PayrollRunService
    PayrollRunService --> SalaryCalculator
    SalaryCalculator --> TaxEngine
    PayrollRunService --> PayslipService
    PayslipService --> Storage
    PayrollRunService --> BankTransferService
    PayrollRepo --> DB

    PerformanceController --> ReviewService
    PerformanceController --> GoalService
    PerformanceController --> PIPService
    ReviewService --> RatingEngine
    PerformanceRepo --> DB

    NotifController --> NotifDispatcher
    NotifDispatcher --> WSManager
    NotifDispatcher --> Queue
    NotifRepo --> DB

    ReportController --> ReportJobService
    ReportJobService --> Queue
    ReportJobService --> ReportBuilders
    ReportBuilders --> DB
    ReportBuilders --> Storage
```

---

---

## Process Narrative (C4 component decomposition)
1. **Initiate**: System Designer captures the primary change request for **C4 Component Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to c4 component decomposition.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Service Mesh executes the approved path and enforces component boundary checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm component coupling.

## Role/Permission Matrix (C4 Component Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View c4 component diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (C4 component decomposition)
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

## Integration Behavior (C4 Component Diagram)
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

