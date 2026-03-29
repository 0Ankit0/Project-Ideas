# Component Diagrams

## Overview
Component diagrams showing the software module structure of the Employee Management System.

---

## Backend Component Diagram

```mermaid
graph TB
    subgraph "API Gateway Layer"
        Router[API Router\n/api/v1]
        Auth[Auth Middleware\nJWT Validation + RBAC]
        RateLimit[Rate Limiter]
    end

    subgraph "Domain Modules"
        IAMModule[IAM Module\nAuth, Sessions, 2FA, SSO]
        EmployeeModule[Employee Module\nProfiles, Org, Documents, Onboarding, Offboarding]
        LeaveModule[Leave Module\nRequests, Approvals, Balances, Holidays]
        AttendanceModule[Attendance Module\nPunches, Shifts, Timesheets, Comp-Off]
        PayrollModule[Payroll Module\nRuns, Computation, Payslips, Tax, Compliance]
        PerformanceModule[Performance Module\nCycles, Goals, KRAs, Reviews, PIP]
        BenefitsModule[Benefits Module\nPlans, Enrolments, Compensation]
        NotifModule[Notification Module\nIn-App, Email, SMS, Push, WebSocket]
        ReportModule[Report Module\nHR, Payroll, Leave, Performance Reports]
        AdminModule[Admin Module\nRoles, Config, Audit Logs, Integrations]
    end

    subgraph "Shared Services"
        PolicyEngine[Policy Engine\nLeave & Payroll Rules]
        TaxEngine[Tax Calculation Engine\nTDS, PF, ESI]
        DocumentService[Document Service\nUpload, Download, Expiry Tracking]
        WorkflowEngine[Workflow Engine\nApproval Chains & Escalations]
        EventBus[Domain Event Bus\nAsync Event Dispatch]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[(Object Storage)]
        Queue[(Task Queue)]
    end

    Router --> Auth
    Auth --> RateLimit
    RateLimit --> IAMModule
    RateLimit --> EmployeeModule
    RateLimit --> LeaveModule
    RateLimit --> AttendanceModule
    RateLimit --> PayrollModule
    RateLimit --> PerformanceModule
    RateLimit --> BenefitsModule
    RateLimit --> ReportModule
    RateLimit --> AdminModule

    LeaveModule --> PolicyEngine
    PayrollModule --> TaxEngine
    EmployeeModule --> DocumentService
    LeaveModule --> WorkflowEngine
    PayrollModule --> WorkflowEngine

    IAMModule --> DB
    EmployeeModule --> DB
    LeaveModule --> DB
    AttendanceModule --> DB
    PayrollModule --> DB
    PerformanceModule --> DB
    BenefitsModule --> DB
    NotifModule --> DB
    ReportModule --> DB
    AdminModule --> DB

    IAMModule --> Cache
    LeaveModule --> Cache
    PayrollModule --> Cache

    DocumentService --> Storage
    PayrollModule --> Storage
    ReportModule --> Storage

    LeaveModule --> EventBus
    PayrollModule --> EventBus
    PerformanceModule --> EventBus
    EventBus --> Queue
    Queue --> NotifModule
```

---

## Frontend Component Diagram

```mermaid
graph TB
    subgraph "Employee Self-Service (ESS)"
        ESSDashboard[Dashboard]
        ESSLeave[Leave Management\nApply, History, Balance]
        ESSAttendance[Attendance\nView, Regularize, Timesheet]
        ESSPayslip[Payslips\nView, Download]
        ESSPerformance[Performance\nGoals, Self-Assessment, Rating]
        ESSProfile[My Profile\nPersonal Info, Documents]
    end

    subgraph "Manager Self-Service (MSS)"
        MSSDashboard[Team Dashboard]
        MSSApprovals[Approvals\nLeave, Timesheet, Comp-Off]
        MSSPerformance[Performance\nAppraisals, PIP]
        MSSSchedule[Shift Roster]
        MSSReports[Team Reports]
    end

    subgraph "HR Portal"
        HREmployees[Employee Management\nCreate, Edit, Transfer, Offboard]
        HROnboarding[Onboarding\nChecklists & Tasks]
        HRPolicies[Policies\nLeave, Appraisal Config]
        HROrgChart[Org Chart]
        HRReports[HR Reports\nHeadcount, Attrition]
    end

    subgraph "Payroll Dashboard"
        PayrollRuns[Payroll Runs]
        PayrollReview[Review & Approve]
        PayrollCompliance[Compliance Reports\nForm 16, PF, ESI]
        PayrollReports[Payroll Analytics]
    end

    subgraph "Admin Console"
        AdminRoles[Roles & Permissions]
        AdminConfig[System Config]
        AdminAudit[Audit Logs]
        AdminIntegrations[Integrations]
    end

    subgraph "Shared Components"
        APIClient[API Client\nREST + Auth Interceptor]
        Notifications[Notification Bell\nIn-App Notifications]
        AuthProvider[Auth Context\nJWT Management]
    end

    ESSDashboard --> APIClient
    MSSDashboard --> APIClient
    HREmployees --> APIClient
    PayrollRuns --> APIClient
    AdminRoles --> APIClient
    APIClient --> AuthProvider
```

---

---

## Process Narrative (Runtime component interactions)
1. **Initiate**: Platform Architect captures the primary change request for **Component Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to runtime component interactions.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Service Registry executes the approved path and enforces dependency policy checker at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm runtime composition.

## Role/Permission Matrix (Component Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View component diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Runtime component interactions)
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

## Integration Behavior (Component Diagrams)
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

