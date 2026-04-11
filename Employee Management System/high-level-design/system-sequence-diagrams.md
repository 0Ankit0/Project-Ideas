# System Sequence Diagrams

## Overview
System-level sequence diagrams showing interactions between external actors and the Employee Management System as a black box.

---

## 1. Employee Leave Application

```mermaid
sequenceDiagram
    actor Employee
    participant EMS as Employee Management System
    participant Manager

    Employee->>EMS: GET /leave/balance
    EMS-->>Employee: Leave balances by type

    Employee->>EMS: POST /leave/requests {type, start, end, reason}
    EMS-->>Employee: 201 Created {request_id, status: "pending"}

    EMS->>Manager: Email / In-App: "Leave request pending approval"

    Manager->>EMS: PUT /leave/requests/{id}/approve {comment}
    EMS-->>Manager: 200 OK {status: "approved"}

    EMS->>Employee: Email / In-App: "Leave approved for {dates}"
```

---

## 2. Monthly Payroll Run

```mermaid
sequenceDiagram
    actor PayrollOfficer as Payroll Officer
    participant EMS as Employee Management System
    participant Bank as Banking System
    participant Employee

    PayrollOfficer->>EMS: POST /payroll/runs {period}
    EMS-->>PayrollOfficer: 202 Accepted {run_id, status: "processing"}

    EMS->>EMS: Compute salaries, deductions, net pay

    PayrollOfficer->>EMS: GET /payroll/runs/{run_id}/summary
    EMS-->>PayrollOfficer: Payroll summary + exception list

    PayrollOfficer->>EMS: POST /payroll/runs/{run_id}/approve
    EMS-->>PayrollOfficer: 200 OK {status: "finalized"}

    EMS->>Employee: Email: Payslip for {month}
    EMS->>Bank: POST bank transfer file (SFTP/API)
    Bank-->>EMS: Acknowledgement
```

---

## 3. Performance Appraisal Self-Assessment

```mermaid
sequenceDiagram
    actor Employee
    participant EMS as Employee Management System
    actor Manager

    EMS->>Employee: Email / Push: "Self-assessment open for {cycle}"

    Employee->>EMS: GET /appraisals/cycles/{id}/my-review
    EMS-->>Employee: KRA list with goal progress

    Employee->>EMS: PUT /appraisals/reviews/{id}/self {kra_ratings, comments}
    EMS-->>Employee: 200 OK {status: "self_submitted"}

    EMS->>Manager: Email / In-App: "Self-assessment submitted by {employee}"

    Manager->>EMS: GET /appraisals/reviews/{id}
    EMS-->>Manager: Review with self-assessment

    Manager->>EMS: PUT /appraisals/reviews/{id}/manager {kra_ratings, comments, recommendation}
    EMS-->>Manager: 200 OK {status: "manager_submitted"}
```

---

## 4. Employee Onboarding

```mermaid
sequenceDiagram
    actor HR as HR Staff
    participant EMS as Employee Management System
    actor Employee

    HR->>EMS: POST /employees {name, email, department, grade, joining_date}
    EMS-->>HR: 201 Created {employee_id}

    EMS->>EMS: Generate employee ID, assign policies, create checklist
    EMS->>Employee: Email: Welcome + ESS portal credentials

    Employee->>EMS: POST /auth/login {email, temp_password}
    EMS-->>Employee: 200 OK {access_token}

    Employee->>EMS: PUT /employees/me/profile {personal_details}
    EMS-->>Employee: 200 OK

    Employee->>EMS: POST /documents {type, file}
    EMS-->>Employee: 201 Created {document_id}

    HR->>EMS: PUT /onboarding/tasks/{task_id}/complete
    EMS-->>HR: 200 OK
```

---

## 5. Attendance Recording via Biometric

```mermaid
sequenceDiagram
    participant Biometric as Biometric Device
    participant EMS as Employee Management System
    actor Employee

    Biometric->>EMS: POST /attendance/punch {employee_id, timestamp, type: "check_in"}
    EMS-->>Biometric: 201 Created {attendance_id}

    EMS->>EMS: Map to employee shift and flag if late

    Biometric->>EMS: POST /attendance/punch {employee_id, timestamp, type: "check_out"}
    EMS-->>Biometric: 201 Created

    EMS->>EMS: Calculate worked hours and flag anomalies

    Employee->>EMS: GET /attendance/me?date={date}
    EMS-->>Employee: Attendance record with hours and flags
```

---

---

## Process Narrative (System-level interaction paths)
1. **Initiate**: Integration Architect captures the primary change request for **System Sequence Diagrams** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to system-level interaction paths.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Integration Orchestrator executes the approved path and enforces handoff ordering checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm cross-system orchestration.

## Role/Permission Matrix (System Sequence Diagrams)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View system sequence diagrams artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (System-level interaction paths)
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

## Integration Behavior (System Sequence Diagrams)
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

