# State Machine Diagrams

## Overview
State machine diagrams showing state transitions for key entities in the Employee Management System.

---

## 1. Leave Request States

```mermaid
stateDiagram-v2
    [*] --> Draft : Employee starts request
    Draft --> Pending : Employee submits
    Pending --> Approved : Manager approves
    Pending --> Rejected : Manager rejects
    Pending --> Cancelled : Employee cancels
    Approved --> Cancelled : Employee cancels (if future dated)
    Approved --> Active : Leave period starts
    Active --> Completed : Leave period ends
    Rejected --> [*]
    Cancelled --> [*]
    Completed --> [*]
```

---

## 2. Payroll Run States

```mermaid
stateDiagram-v2
    [*] --> Initiated : Payroll Officer initiates
    Initiated --> Processing : System starts computation
    Processing --> PendingReview : Computation complete
    PendingReview --> Processing : Officer corrects exceptions
    PendingReview --> Approved : Officer approves payroll
    Approved --> PayslipGeneration : Trigger payslip creation
    PayslipGeneration --> BankTransfer : Payslips delivered
    BankTransfer --> Finalized : Bank acknowledgement received
    Finalized --> [*]

    Processing --> Failed : Critical error
    Failed --> [*]
```

---

## 3. Employee Employment Status States

```mermaid
stateDiagram-v2
    [*] --> Offered : Offer letter issued
    Offered --> Onboarding : Employee joins
    Onboarding --> Probation : Profile setup complete
    Probation --> Active : Probation confirmed
    Probation --> Terminated : Probation failed
    Active --> OnNotice : Resignation submitted
    Active --> Suspended : Disciplinary action
    Active --> OnLeave : Long-term leave started
    OnLeave --> Active : Leave period ends
    Suspended --> Active : Suspension lifted
    Suspended --> Terminated : Decision to terminate
    OnNotice --> Offboarding : Last working day approached
    Offboarding --> Alumni : Clearance complete
    Terminated --> [*]
    Alumni --> [*]
```

---

## 4. Performance Review States

```mermaid
stateDiagram-v2
    [*] --> NotStarted : Review cycle launched
    NotStarted --> SelfAssessmentOpen : Deadline to self-assess starts
    SelfAssessmentOpen --> SelfSubmitted : Employee submits self-assessment
    SelfAssessmentOpen --> SelfOverdue : Deadline missed
    SelfOverdue --> SelfSubmitted : HR overrides or employee late-submits
    SelfSubmitted --> ManagerReview : Manager begins rating
    ManagerReview --> ManagerSubmitted : Manager submits review
    ManagerSubmitted --> HRCalibration : HR calibration period
    HRCalibration --> Finalized : HR locks ratings
    Finalized --> Released : Ratings released to employee
    Released --> [*]
```

---

## 5. Expense Claim States

```mermaid
stateDiagram-v2
    [*] --> Draft : Employee starts claim
    Draft --> Submitted : Employee submits with receipts
    Submitted --> UnderReview : Manager opens claim
    UnderReview --> Approved : Manager approves
    UnderReview --> Rejected : Manager rejects
    Approved --> ScheduledForPayment : Added to next payroll run
    ScheduledForPayment --> Paid : Payroll run finalized
    Rejected --> [*]
    Paid --> [*]
```

---

## 6. Onboarding Checklist States

```mermaid
stateDiagram-v2
    [*] --> Created : Employee profile created
    Created --> InProgress : First task completed
    InProgress --> PartiallyComplete : Some tasks done
    PartiallyComplete --> InProgress : More tasks completed
    InProgress --> Complete : All mandatory tasks done
    PartiallyComplete --> Overdue : Deadline passed with pending tasks
    Overdue --> InProgress : Tasks resumed
    Overdue --> EscalatedToHR : Auto-escalation
    EscalatedToHR --> Complete : HR force-completes
    Complete --> [*]
```

---

## 7. PIP (Performance Improvement Plan) States

```mermaid
stateDiagram-v2
    [*] --> Draft : Manager creates PIP
    Draft --> PendingHRApproval : Manager submits for HR review
    PendingHRApproval --> Active : HR approves
    PendingHRApproval --> Rejected : HR rejects
    Active --> CheckInDue : Check-in milestone reached
    CheckInDue --> Active : Check-in recorded
    Active --> Extended : Extended by manager/HR
    Active --> Completed : Employee meets objectives
    Active --> Terminated : Employee terminated
    Extended --> Active : Extension period starts
    Completed --> [*]
    Terminated --> [*]
    Rejected --> [*]
```
