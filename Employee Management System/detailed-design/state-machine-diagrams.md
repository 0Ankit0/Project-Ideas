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

---

---

## Process Narrative (Formal lifecycle state machines)
1. **Initiate**: Workflow Architect captures the primary change request for **State Machine Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to formal lifecycle state machines.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: State Engine executes the approved path and enforces transition guard evaluator at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm state correctness.

## Role/Permission Matrix (State Machine Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View state machine diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Formal lifecycle state machines)
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

## Integration Behavior (State Machine Diagrams)
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

