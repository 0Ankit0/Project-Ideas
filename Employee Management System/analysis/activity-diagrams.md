# Activity Diagrams

## Overview
Activity diagrams illustrating the key business process flows in the Employee Management System.

---

## 1. Leave Application Process

```mermaid
flowchart TD
    Start([Employee Initiates Leave Request]) --> SelectType[Select Leave Type]
    SelectType --> EnterDates[Enter Start & End Dates]
    EnterDates --> CheckBalance{Balance\nSufficient?}
    CheckBalance -- Yes --> ValidatePolicy{Policy\nCompliant?}
    CheckBalance -- No --> ShowWarning[Show Insufficient Balance Warning]
    ShowWarning --> AllowNegative{Policy Allows\nNegative Balance?}
    AllowNegative -- No --> End1([End - Request Blocked])
    AllowNegative -- Yes --> ValidatePolicy
    ValidatePolicy -- No --> ShowError[Show Policy Violation]
    ShowError --> End2([End - Request Blocked])
    ValidatePolicy -- Yes --> SubmitRequest[Submit Request]
    SubmitRequest --> NotifyManager[Notify Manager]
    NotifyManager --> ManagerReview{Manager\nDecision}
    ManagerReview -- Approve --> UpdateBalance[Deduct Leave Balance]
    UpdateBalance --> NotifyEmployee[Notify Employee - Approved]
    ManagerReview -- Reject --> NotifyRejection[Notify Employee - Rejected]
    NotifyEmployee --> End3([End])
    NotifyRejection --> End4([End])
```

---

## 2. Monthly Payroll Processing

```mermaid
flowchart TD
    Start([Payroll Officer Initiates Run]) --> LockData[Lock Attendance & Leave Data]
    LockData --> FetchEmployees[Fetch Active Employees for Period]
    FetchEmployees --> CalculateGross[Calculate Gross Pay Per Employee]
    CalculateGross --> ApplyLOP[Apply LOP Deductions]
    ApplyLOP --> ApplyStatutory[Apply Statutory Deductions\nPF / ESI / TDS]
    ApplyStatutory --> ApplyReimbursements[Apply Approved Reimbursements]
    ApplyReimbursements --> ComputeNet[Compute Net Pay]
    ComputeNet --> ReviewExceptions{Exceptions\nExist?}
    ReviewExceptions -- Yes --> ResolveExceptions[Payroll Officer Resolves Exceptions]
    ResolveExceptions --> Recalculate[Recalculate Affected Employees]
    Recalculate --> ReviewExceptions
    ReviewExceptions -- No --> ApprovePayroll[Payroll Officer Approves Payroll]
    ApprovePayroll --> GeneratePayslips[Generate Payslips]
    GeneratePayslips --> DeliverPayslips[Deliver via Email & ESS]
    DeliverPayslips --> GenerateBankFile[Generate Bank Transfer File]
    GenerateBankFile --> GenerateComplianceReports[Generate Compliance Reports]
    GenerateComplianceReports --> End([End - Payroll Finalized])
```

---

## 3. Employee Onboarding Workflow

```mermaid
flowchart TD
    Start([Offer Letter Accepted]) --> CreateProfile[HR Creates Employee Profile]
    CreateProfile --> GenerateID[System Generates Employee ID]
    GenerateID --> AssignPolicies[Assign Payroll Group & Leave Policy]
    AssignPolicies --> CreateChecklist[Create Onboarding Checklist]
    CreateChecklist --> SendWelcomeEmail[Send Welcome Email with ESS Credentials]
    SendWelcomeEmail --> ParallelTasks{Parallel Onboarding Tasks}

    ParallelTasks --> ITTasks[IT: Provision Equipment & Access]
    ParallelTasks --> DocCollection[HR: Collect KYC Documents]
    ParallelTasks --> EmployeeTasks[Employee: Complete ESS Profile & Declarations]

    ITTasks --> ITDone{IT Tasks\nComplete?}
    DocCollection --> DocDone{Docs\nCollected?}
    EmployeeTasks --> EmpDone{Employee Tasks\nComplete?}

    ITDone -- Yes --> MergePoint[All Tasks Complete]
    DocDone -- Yes --> MergePoint
    EmpDone -- Yes --> MergePoint

    ITDone -- No --> SendReminder1[Send Reminder to IT]
    DocDone -- No --> SendReminder2[Send Reminder to HR / Employee]
    EmpDone -- No --> SendReminder3[Send Reminder to Employee]

    SendReminder1 --> ITTasks
    SendReminder2 --> DocCollection
    SendReminder3 --> EmployeeTasks

    MergePoint --> MarkOnboarded[Mark Onboarding Complete]
    MarkOnboarded --> End([End - Employee Active])
```

---

## 4. Performance Appraisal Cycle

```mermaid
flowchart TD
    Start([HR Launches Review Cycle]) --> NotifyEmployees[Notify Employees to Complete Self-Assessment]
    NotifyEmployees --> SelfAssessment[Employee Completes Self-Assessment]
    SelfAssessment --> SelfSubmit{Self-Assessment\nSubmitted?}
    SelfSubmit -- No --> RemindEmployee[Send Reminder]
    RemindEmployee --> SelfAssessment
    SelfSubmit -- Yes --> NotifyManager[Notify Manager for Review]
    NotifyManager --> ManagerRating[Manager Rates KRAs & Adds Comments]
    ManagerRating --> ManagerSubmit{Manager Review\nSubmitted?}
    ManagerSubmit -- No --> RemindManager[Send Reminder to Manager]
    RemindManager --> ManagerRating
    ManagerSubmit -- Yes --> PeerFeedback{360 Feedback\nEnabled?}
    PeerFeedback -- Yes --> CollectPeerFeedback[Collect Peer Feedback]
    CollectPeerFeedback --> HRCalibration[HR Calibration Session]
    PeerFeedback -- No --> HRCalibration
    HRCalibration --> AdjustRatings{Adjustments\nNeeded?}
    AdjustRatings -- Yes --> UpdateRatings[HR Adjusts Ratings with Audit Note]
    UpdateRatings --> FinalizeRatings[Finalize and Lock Ratings]
    AdjustRatings -- No --> FinalizeRatings
    FinalizeRatings --> GenerateLetters[Generate Appraisal Letters]
    GenerateLetters --> ReleaseRatings[Release Ratings to Employees]
    ReleaseRatings --> End([End - Appraisal Cycle Closed])
```

---

## 5. Employee Offboarding Workflow

```mermaid
flowchart TD
    Start([Resignation / Termination Recorded]) --> SetLWD[Set Last Working Day]
    SetLWD --> TriggerOffboarding[Trigger Offboarding Workflow]
    TriggerOffboarding --> CreateClearanceChecklist[Create Clearance Checklist]
    CreateClearanceChecklist --> ParallelClearance{Parallel Clearance Tasks}

    ParallelClearance --> AssetReturn[Employee Returns Assets]
    ParallelClearance --> AccessRevocation[IT Revokes Access]
    ParallelClearance --> KnowledgeTransfer[Manager: Knowledge Transfer]
    ParallelClearance --> ExitInterview[HR: Conduct Exit Interview]

    AssetReturn --> AssetDone{Assets\nReturned?}
    AccessRevocation --> AccessDone{Access\nRevoked?}
    KnowledgeTransfer --> KTDone{KT\nComplete?}
    ExitInterview --> ExitDone{Exit Interview\nComplete?}

    AssetDone -- Yes --> FinalSettlement[Finance Computes Final Settlement]
    AccessDone -- Yes --> FinalSettlement
    KTDone -- Yes --> FinalSettlement
    ExitDone -- Yes --> FinalSettlement

    FinalSettlement --> HRApproveSettlement{HR Approves\nSettlement?}
    HRApproveSettlement -- No --> ReviseSettlement[Finance Revises Settlement]
    ReviseSettlement --> HRApproveSettlement
    HRApproveSettlement -- Yes --> GenerateDocuments[Generate Relieving & Experience Letter]
    GenerateDocuments --> DeactivateAccounts[Deactivate All Accounts on LWD]
    DeactivateAccounts --> ArchiveRecord[Archive Employee Record]
    ArchiveRecord --> End([End - Offboarding Complete])
```

---

---

## Process Narrative (Activity workflows)
1. **Initiate**: Business Analyst captures the primary change request for **Activity Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to activity workflows.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: ReviewBoard executes the approved path and enforces workflow engine at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm diagram publication.

## Role/Permission Matrix (Activity Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View activity diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Activity workflows)
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

## Integration Behavior (Activity Diagrams)
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

