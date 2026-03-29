# Swimlane Diagrams

## Overview
Swimlane / BPMN diagrams showing cross-department workflows in the Employee Management System.

---

## 1. Leave Approval Swimlane

```mermaid
sequenceDiagram
    participant E as Employee
    participant S as EMS System
    participant M as Manager
    participant HR as HR Staff

    E->>S: Submit Leave Request
    S->>S: Validate policy & balance
    S->>M: Notify - Pending Approval
    M->>S: Review request & team calendar
    alt Approve
        M->>S: Approve with optional comment
        S->>S: Deduct leave balance
        S->>E: Notify - Leave Approved
    else Reject
        M->>S: Reject with reason
        S->>E: Notify - Leave Rejected
    else Delegate
        M->>S: Delegate to HR
        S->>HR: Notify - Approval Delegated
        HR->>S: Approve or Reject
        S->>E: Notify - Decision
    end
```

---

## 2. Payroll Processing Swimlane

```mermaid
sequenceDiagram
    participant PO as Payroll Officer
    participant S as EMS System
    participant HR as HR Staff
    participant E as Employee
    participant Bank as Banking System

    PO->>S: Initiate Payroll Run
    S->>S: Lock attendance & leave data
    S->>S: Calculate gross pay, deductions, net pay
    S->>PO: Display payroll summary & exceptions
    PO->>S: Resolve exceptions & approve payroll
    S->>S: Generate payslips
    S->>E: Deliver payslips via email & ESS
    S->>Bank: Submit bank transfer file
    S->>PO: Generate compliance reports
    S->>HR: Notify payroll finalized
```

---

## 3. Performance Appraisal Swimlane

```mermaid
sequenceDiagram
    participant HR as HR Staff
    participant S as EMS System
    participant E as Employee
    participant M as Manager

    HR->>S: Configure & launch review cycle
    S->>E: Notify - Complete self-assessment
    E->>S: Submit self-assessment with KRA ratings
    S->>M: Notify - Self-assessment ready for review
    M->>S: Rate KRAs, add comments, recommend action
    S->>HR: Notify - Manager review submitted
    HR->>S: Conduct calibration & finalize ratings
    S->>S: Lock ratings & generate appraisal letters
    S->>E: Notify - Appraisal available
    E->>S: View final rating & feedback
```

---

## 4. Employee Onboarding Swimlane

```mermaid
sequenceDiagram
    participant HR as HR Staff
    participant S as EMS System
    participant IT as IT Team
    participant E as New Employee
    participant M as Manager

    HR->>S: Create employee profile
    S->>S: Generate Employee ID & assign policies
    S->>E: Send welcome email with ESS credentials
    S->>IT: Assign IT provisioning tasks
    S->>HR: Assign document collection tasks
    S->>E: Assign profile completion tasks
    S->>M: Assign team introduction tasks
    IT->>S: Complete equipment & access setup
    E->>S: Complete profile & upload documents
    HR->>S: Verify documents & mark complete
    M->>S: Complete team introduction
    S->>HR: All tasks complete - onboarding done
```

---

## 5. Expense Claim Reimbursement Swimlane

```mermaid
sequenceDiagram
    participant E as Employee
    participant S as EMS System
    participant M as Manager
    participant PO as Payroll Officer

    E->>S: Submit expense claim with receipts
    S->>M: Notify - Pending claim approval
    M->>S: Review claim & receipts
    alt Approve
        M->>S: Approve claim
        S->>PO: Add to next payroll run
        PO->>S: Finalize payroll with reimbursement
        S->>E: Notify - Reimbursement processed in payslip
    else Reject
        M->>S: Reject with reason
        S->>E: Notify - Claim rejected with reason
    end
```

---

## 6. PIP (Performance Improvement Plan) Swimlane

```mermaid
sequenceDiagram
    participant M as Manager
    participant S as EMS System
    participant E as Employee
    participant HR as HR Staff

    M->>S: Initiate PIP for employee
    S->>HR: Notify - PIP initiated, review required
    HR->>S: Review & approve PIP objectives
    S->>E: Notify - PIP initiated with objectives
    loop Monthly Check-ins
        M->>S: Record check-in with progress notes
        S->>E: Notify - Check-in recorded
        E->>S: Acknowledge or add comments
    end
    M->>S: Record PIP outcome (completed / extended / terminated)
    S->>HR: Notify - PIP outcome recorded
    HR->>S: Finalize PIP outcome & update employee record
    S->>E: Notify - PIP closed with outcome
```

---

---

## Process Narrative (Swimlane responsibility model)
1. **Initiate**: Process Manager captures the primary change request for **Swimlane Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to swimlane responsibility model.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Workflow Orchestrator executes the approved path and enforces lane assignment rules at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm cross-team handoff.

## Role/Permission Matrix (Swimlane Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View swimlane diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Swimlane responsibility model)
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

## Integration Behavior (Swimlane Diagrams)
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

