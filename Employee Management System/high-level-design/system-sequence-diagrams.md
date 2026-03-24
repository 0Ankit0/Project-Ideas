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

    EMS->>EMS: Map to employee shift; flag if late

    Biometric->>EMS: POST /attendance/punch {employee_id, timestamp, type: "check_out"}
    EMS-->>Biometric: 201 Created

    EMS->>EMS: Calculate worked hours; flag anomalies

    Employee->>EMS: GET /attendance/me?date={date}
    EMS-->>Employee: Attendance record with hours and flags
```
