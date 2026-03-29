# Data Flow Diagrams

## Overview
Data flow diagrams showing how data moves through the Employee Management System at different levels of abstraction.

---

## Level 0 - Context DFD

```mermaid
graph LR
    Employee((Employee))
    Manager((Manager))
    HR((HR Staff))
    Payroll((Payroll Officer))
    Admin((Admin))
    Biometric((Biometric Device))
    Bank((Banking System))
    ERP((ERP System))

    EMS[Employee Management System]

    Employee -->|profile updates, leave requests, timesheets, self-assessments| EMS
    Manager -->|approvals, appraisal ratings, shift rosters| EMS
    HR -->|employee data, policies, org structure| EMS
    Payroll -->|payroll instructions, tax declarations| EMS
    Admin -->|system config, roles, audit queries| EMS
    Biometric -->|attendance punch events| EMS

    EMS -->|payslips, leave status, notifications| Employee
    EMS -->|team reports, pending approvals| Manager
    EMS -->|HR reports, onboarding status| HR
    EMS -->|payroll reports, compliance filings| Payroll
    EMS -->|audit logs, dashboards| Admin
    EMS -->|bank transfer file| Bank
    EMS <-->|employee data sync, journal entries| ERP
```

---

## Level 1 - Major Process DFD

```mermaid
graph TB
    subgraph Inputs
        EmpInput[Employee Input]
        MgrInput[Manager Input]
        HRInput[HR Input]
        PayrollInput[Payroll Input]
        BiometricInput[Biometric Punch]
    end

    subgraph "EMS Processes"
        P1[1.0 Employee\nManagement]
        P2[2.0 Leave &\nAttendance]
        P3[3.0 Payroll\nProcessing]
        P4[4.0 Performance\nManagement]
        P5[5.0 Notifications\n& Reporting]
    end

    subgraph DataStores
        DS1[(Employee\nProfiles)]
        DS2[(Leave &\nAttendance)]
        DS3[(Payroll\nRecords)]
        DS4[(Performance\nData)]
        DS5[(Notifications\n& Audit Logs)]
        DS6[(Documents)]
    end

    subgraph Outputs
        PayslipOut[Payslips]
        ReportOut[Reports]
        BankFile[Bank Transfer File]
        NotifOut[Notifications]
    end

    EmpInput --> P1
    HRInput --> P1
    P1 --> DS1
    P1 --> DS6

    EmpInput --> P2
    MgrInput --> P2
    BiometricInput --> P2
    P2 --> DS2
    DS1 --> P2

    PayrollInput --> P3
    DS2 --> P3
    DS1 --> P3
    P3 --> DS3
    P3 --> PayslipOut
    P3 --> BankFile

    EmpInput --> P4
    MgrInput --> P4
    HRInput --> P4
    DS1 --> P4
    P4 --> DS4

    DS1 --> P5
    DS2 --> P5
    DS3 --> P5
    DS4 --> P5
    P5 --> DS5
    P5 --> ReportOut
    P5 --> NotifOut
```

---

## Level 2 - Payroll Process DFD

```mermaid
graph TB
    subgraph Inputs
        PayrollOfficer[Payroll Officer]
        AttendanceDS[(Attendance Data)]
        LeaveDS[(Leave Data)]
        SalaryDS[(Salary Structures)]
        TaxRuleDS[(Tax Rules)]
        ClaimsDS[(Approved Claims)]
    end

    subgraph "Payroll Processes"
        P3_1[3.1 Calculate\nGross Pay]
        P3_2[3.2 Apply LOP\n& Deductions]
        P3_3[3.3 Compute\nStatutory Deductions]
        P3_4[3.4 Apply\nReimbursements]
        P3_5[3.5 Calculate\nNet Pay]
        P3_6[3.6 Generate\nPayslips]
        P3_7[3.7 Generate\nBank Transfer File]
        P3_8[3.8 Generate\nCompliance Reports]
    end

    subgraph Outputs
        PayslipDS[(Payroll Records)]
        BankFile[Bank Transfer File]
        ComplianceReport[Compliance Report]
        Employee[Employee - Payslip]
    end

    PayrollOfficer --> P3_1
    SalaryDS --> P3_1
    P3_1 --> P3_2
    AttendanceDS --> P3_2
    LeaveDS --> P3_2
    P3_2 --> P3_3
    TaxRuleDS --> P3_3
    P3_3 --> P3_4
    ClaimsDS --> P3_4
    P3_4 --> P3_5
    P3_5 --> P3_6
    P3_6 --> PayslipDS
    P3_6 --> Employee
    PayslipDS --> P3_7
    P3_7 --> BankFile
    PayslipDS --> P3_8
    P3_8 --> ComplianceReport
```

---

## Level 2 - Leave Management DFD

```mermaid
graph TB
    subgraph Inputs
        Employee[Employee]
        Manager[Manager]
        HolidayCalendar[(Holiday Calendar)]
        BalanceDS[(Leave Balances)]
        PolicyDS[(Leave Policies)]
    end

    subgraph "Leave Processes"
        P2_1[2.1 Validate\nLeave Request]
        P2_2[2.2 Route to\nApprover]
        P2_3[2.3 Process\nApproval Decision]
        P2_4[2.4 Update\nLeave Balance]
        P2_5[2.5 Accrue\nLeave Credits]
        P2_6[2.6 Year-End\nCarry Forward]
    end

    subgraph Outputs
        RequestDS[(Leave Requests)]
        UpdatedBalance[(Updated Balances)]
        Notifications[Notifications]
    end

    Employee --> P2_1
    PolicyDS --> P2_1
    HolidayCalendar --> P2_1
    BalanceDS --> P2_1
    P2_1 --> P2_2
    P2_2 --> RequestDS
    P2_2 --> Notifications
    Manager --> P2_3
    RequestDS --> P2_3
    P2_3 --> P2_4
    P2_4 --> UpdatedBalance
    P2_4 --> Notifications
    PolicyDS --> P2_5
    P2_5 --> UpdatedBalance
    PolicyDS --> P2_6
    BalanceDS --> P2_6
    P2_6 --> UpdatedBalance
```

---

---

## Process Narrative (Data movement architecture)
1. **Initiate**: Data Architect captures the primary change request for **Data Flow Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to data movement architecture.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Data Pipeline executes the approved path and enforces flow classification checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm data movement governance.

## Role/Permission Matrix (Data Flow Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View data flow diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Data movement architecture)
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

## Integration Behavior (Data Flow Diagrams)
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

