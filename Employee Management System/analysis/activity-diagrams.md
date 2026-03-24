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
