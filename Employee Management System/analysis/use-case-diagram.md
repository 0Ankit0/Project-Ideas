# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the Employee Management System.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Employee((Employee))
        Manager((Manager))
        HR((HR Staff))
        Payroll((Payroll Officer))
        Admin((Admin))
        BiometricDevice((Biometric Device))
        EmailProvider((Email Provider))
        PaymentGateway((Payment / Bank System))
    end

    subgraph "Employee Management System"
        UC1[Manage Profile]
        UC2[Apply for Leave]
        UC3[View Payslips]
        UC4[Submit Timesheet]
        UC5[View Performance]
        UC6[Submit Self-Assessment]

        UC10[Approve Leave]
        UC11[Conduct Appraisal]
        UC12[Manage Team Attendance]
        UC13[Create Shift Roster]

        UC20[Manage Employee Lifecycle]
        UC21[Configure Leave Policies]
        UC22[Run Onboarding Workflow]
        UC23[Generate HR Reports]

        UC30[Process Payroll]
        UC31[Generate Payslips]
        UC32[Manage Tax Compliance]

        UC40[Manage Roles & Permissions]
        UC41[View Audit Logs]
        UC42[Configure System]
        UC43[View Executive Dashboard]
    end

    Employee --> UC1
    Employee --> UC2
    Employee --> UC3
    Employee --> UC4
    Employee --> UC5
    Employee --> UC6

    Manager --> UC10
    Manager --> UC11
    Manager --> UC12
    Manager --> UC13

    HR --> UC20
    HR --> UC21
    HR --> UC22
    HR --> UC23

    Payroll --> UC30
    Payroll --> UC31
    Payroll --> UC32

    Admin --> UC40
    Admin --> UC41
    Admin --> UC42
    Admin --> UC43

    BiometricDevice --> UC12
    UC31 --> EmailProvider
    UC30 --> PaymentGateway
```

---

## Employee Use Cases

```mermaid
graph LR
    Employee((Employee))

    subgraph "Profile & Documents"
        UC1[Login / Logout]
        UC2[Update Personal Info]
        UC3[Upload Documents]
        UC4[View Employment Details]
        UC5[View Org Chart]
    end

    subgraph "Leave Management"
        UC6[View Leave Balance]
        UC7[Apply for Leave]
        UC8[Cancel Leave Request]
        UC9[View Leave History]
    end

    subgraph "Attendance & Timesheet"
        UC10[View Attendance]
        UC11[Submit Timesheet]
        UC12[Regularize Attendance]
        UC13[Apply for Comp-Off]
    end

    subgraph "Payroll"
        UC14[View Payslips]
        UC15[Download Payslip PDF]
        UC16[Submit Expense Claim]
        UC17[View Tax Certificate]
        UC18[Submit Tax Declaration]
    end

    subgraph "Performance"
        UC19[Set Goals]
        UC20[Update Goal Progress]
        UC21[Submit Self-Assessment]
        UC22[View Appraisal Rating]
        UC23[View Feedback]
    end

    Employee --> UC1
    Employee --> UC2
    Employee --> UC3
    Employee --> UC4
    Employee --> UC5
    Employee --> UC6
    Employee --> UC7
    Employee --> UC8
    Employee --> UC9
    Employee --> UC10
    Employee --> UC11
    Employee --> UC12
    Employee --> UC13
    Employee --> UC14
    Employee --> UC15
    Employee --> UC16
    Employee --> UC17
    Employee --> UC18
    Employee --> UC19
    Employee --> UC20
    Employee --> UC21
    Employee --> UC22
    Employee --> UC23
```

---

## Manager Use Cases

```mermaid
graph LR
    Manager((Manager))

    subgraph "Team Oversight"
        UC1[View Team Dashboard]
        UC2[View Team Attendance]
        UC3[View Team Leave Calendar]
        UC4[View Org Chart]
    end

    subgraph "Approvals"
        UC5[Approve / Reject Leave]
        UC6[Approve / Reject Timesheet]
        UC7[Approve Regularization]
        UC8[Approve Comp-Off]
        UC9[Approve Expense Claims]
    end

    subgraph "Shift Management"
        UC10[Create Shift Roster]
        UC11[Assign Shifts]
        UC12[Approve Shift Swap]
    end

    subgraph "Performance Management"
        UC13[Set Team Goals]
        UC14[Track Goal Progress]
        UC15[Conduct Performance Review]
        UC16[Rate Employee KRAs]
        UC17[Initiate PIP]
        UC18[Provide 360 Feedback]
    end

    Manager --> UC1
    Manager --> UC2
    Manager --> UC3
    Manager --> UC4
    Manager --> UC5
    Manager --> UC6
    Manager --> UC7
    Manager --> UC8
    Manager --> UC9
    Manager --> UC10
    Manager --> UC11
    Manager --> UC12
    Manager --> UC13
    Manager --> UC14
    Manager --> UC15
    Manager --> UC16
    Manager --> UC17
    Manager --> UC18
```

---

## HR Staff Use Cases

```mermaid
graph LR
    HR((HR Staff))

    subgraph "Employee Lifecycle"
        UC1[Create Employee Profile]
        UC2[Manage Onboarding Tasks]
        UC3[Process Employee Transfer]
        UC4[Initiate Offboarding]
        UC5[Generate Employment Letters]
    end

    subgraph "Configuration"
        UC6[Configure Leave Policies]
        UC7[Manage Holiday Calendar]
        UC8[Configure Appraisal Cycles]
        UC9[Manage Org Structure]
        UC10[Manage Departments & Designations]
    end

    subgraph "Benefits"
        UC11[Configure Benefit Plans]
        UC12[Manage Enrolment Windows]
        UC13[Process Benefit Changes]
    end

    subgraph "Reports & Compliance"
        UC14[Generate Headcount Reports]
        UC15[View Attrition Reports]
        UC16[Track Document Expiry]
        UC17[Generate Diversity Reports]
        UC18[Export Compliance Data]
    end

    HR --> UC1
    HR --> UC2
    HR --> UC3
    HR --> UC4
    HR --> UC5
    HR --> UC6
    HR --> UC7
    HR --> UC8
    HR --> UC9
    HR --> UC10
    HR --> UC11
    HR --> UC12
    HR --> UC13
    HR --> UC14
    HR --> UC15
    HR --> UC16
    HR --> UC17
    HR --> UC18
```

---

## Payroll Officer Use Cases

```mermaid
graph LR
    Payroll((Payroll Officer))

    subgraph "Payroll Processing"
        UC1[Initiate Payroll Run]
        UC2[Review Payroll Exceptions]
        UC3[Override Payroll Values]
        UC4[Finalize and Approve Payroll]
        UC5[Process Off-Cycle Payments]
        UC6[Process Bonuses]
    end

    subgraph "Payslip Management"
        UC7[Generate Payslips]
        UC8[Deliver Payslips via Email]
        UC9[View Payslip History]
    end

    subgraph "Tax & Compliance"
        UC10[Process Tax Declarations]
        UC11[Calculate TDS]
        UC12[Generate Form 16]
        UC13[Generate PF Report]
        UC14[Generate ESI Report]
        UC15[Track Statutory Deadlines]
    end

    subgraph "Reports"
        UC16[View Payroll Summary]
        UC17[Cost Center Reports]
        UC18[Month-over-Month Variance]
        UC19[Export Bank Transfer File]
    end

    Payroll --> UC1
    Payroll --> UC2
    Payroll --> UC3
    Payroll --> UC4
    Payroll --> UC5
    Payroll --> UC6
    Payroll --> UC7
    Payroll --> UC8
    Payroll --> UC9
    Payroll --> UC10
    Payroll --> UC11
    Payroll --> UC12
    Payroll --> UC13
    Payroll --> UC14
    Payroll --> UC15
    Payroll --> UC16
    Payroll --> UC17
    Payroll --> UC18
    Payroll --> UC19
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        ApplyLeave[Apply for Leave] -->|includes| CheckBalance[Check Leave Balance]
        ApplyLeave -->|includes| ValidateDates[Validate Dates Against Policy]
        ApplyLeave -->|includes| NotifyManager[Notify Manager]

        ProcessPayroll[Process Payroll] -->|includes| CalculateGross[Calculate Gross Pay]
        ProcessPayroll -->|includes| ApplyDeductions[Apply Deductions & Tax]
        ProcessPayroll -->|includes| GeneratePayslip[Generate Payslip]

        ConductAppraisal[Conduct Appraisal] -->|includes| CollectSelfAssessment[Collect Self-Assessment]
        ConductAppraisal -->|includes| ManagerRating[Manager Rating]
        ConductAppraisal -->|includes| HRFinalization[HR Finalization]
    end

    subgraph "Extend Relationships"
        SubmitTimesheet[Submit Timesheet] -.->|extends| AddOvertimeHours[Add Overtime Hours]
        SubmitTimesheet -.->|extends| LinkToProject[Link to Project Code]

        PayrollRun[Run Payroll] -.->|extends| ProcessBonuses[Process Bonuses]
        PayrollRun -.->|extends| ProcessReimbursements[Process Reimbursements]

        AppraisalReview[Appraisal Review] -.->|extends| InitiatePIP[Initiate PIP]
        AppraisalReview -.->|extends| RecommendPromotion[Recommend Promotion]
    end
```

---

---

## Process Narrative (Use-case relationship model)
1. **Initiate**: Solution Analyst captures the primary change request for **Use Case Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to use-case relationship model.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Model Repository executes the approved path and enforces relationship consistency checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm actor/use-case alignment.

## Role/Permission Matrix (Use Case Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View use case diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Use-case relationship model)
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

## Integration Behavior (Use Case Diagram)
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

