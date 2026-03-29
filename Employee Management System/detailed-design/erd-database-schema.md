# ERD / Database Schema

## Overview
This ERD defines the complete database schema for the Employee Management System, covering all core modules.

---

## Full System ERD

```mermaid
erDiagram
    users {
        int id PK
        varchar email
        varchar hashed_password
        bool is_active
        bool is_superuser
        bool otp_enabled
        bool otp_verified
        datetime created_at
        datetime updated_at
    }

    employees {
        int id PK
        int user_id FK
        varchar employee_id
        varchar first_name
        varchar last_name
        varchar phone
        date date_of_birth
        date date_of_joining
        date date_of_leaving
        varchar employment_status
        int department_id FK
        int designation_id FK
        int grade_id FK
        int reporting_manager_id FK
        varchar location_code
        datetime created_at
        datetime updated_at
    }

    departments {
        int id PK
        varchar name
        varchar code
        int parent_department_id FK
        int cost_center_id FK
        int head_employee_id FK
    }

    designations {
        int id PK
        varchar title
        int grade_id FK
        varchar level
    }

    grades {
        int id PK
        varchar code
        varchar name
        decimal min_salary
        decimal max_salary
    }

    cost_centers {
        int id PK
        varchar code
        varchar name
        int department_id FK
    }

    employee_documents {
        int id PK
        int employee_id FK
        varchar document_type
        varchar file_url
        date expiry_date
        datetime uploaded_at
    }

    onboarding_checklists {
        int id PK
        int employee_id FK
        datetime completed_at
    }

    onboarding_tasks {
        int id PK
        int checklist_id FK
        varchar title
        varchar assigned_role
        int assigned_user_id FK
        bool is_completed
        date due_date
        datetime completed_at
    }

    leave_policies {
        int id PK
        varchar name
        varchar applicable_to
    }

    leave_types {
        int id PK
        int policy_id FK
        varchar name
        varchar code
        decimal annual_entitlement
        bool is_paid
        bool carry_forward_allowed
        decimal max_carry_forward
        bool encashment_allowed
        int min_notice_days
        int max_consecutive_days
    }

    leave_balances {
        int id PK
        int employee_id FK
        int leave_type_id FK
        int year
        decimal entitled
        decimal accrued
        decimal used
        decimal pending
        decimal lapsed
        decimal carried_forward
    }

    leave_requests {
        int id PK
        int employee_id FK
        int leave_type_id FK
        date start_date
        date end_date
        decimal calculated_days
        text reason
        varchar status
        int approver_id FK
        text approver_comment
        datetime submitted_at
        datetime decided_at
    }

    holiday_calendars {
        int id PK
        varchar name
        varchar location_code
        int year
    }

    holidays {
        int id PK
        int calendar_id FK
        date date
        varchar name
        bool is_optional
    }

    shifts {
        int id PK
        varchar name
        time start_time
        time end_time
        varchar shift_type
        decimal overtime_multiplier
    }

    shift_assignments {
        int id PK
        int employee_id FK
        int shift_id FK
        date effective_from
        date effective_to
    }

    attendance_records {
        int id PK
        int employee_id FK
        date date
        datetime check_in
        datetime check_out
        decimal worked_hours
        varchar status
        bool is_regularized
    }

    attendance_regularizations {
        int id PK
        int attendance_record_id FK
        int employee_id FK
        text reason
        varchar status
        int approver_id FK
        datetime submitted_at
        datetime decided_at
    }

    timesheets {
        int id PK
        int employee_id FK
        date week_start
        varchar status
        decimal total_hours
        int approver_id FK
        datetime submitted_at
        datetime decided_at
    }

    timesheet_entries {
        int id PK
        int timesheet_id FK
        date date
        varchar project_code
        decimal hours
        text notes
    }

    comp_off_requests {
        int id PK
        int employee_id FK
        date overtime_date
        date comp_off_date
        decimal hours
        varchar status
        int approver_id FK
        datetime submitted_at
        datetime decided_at
    }

    salary_structures {
        int id PK
        int employee_id FK
        decimal basic_pay
        decimal hra
        decimal transport_allowance
        decimal medical_allowance
        decimal special_allowance
        decimal gross_ctc
        date effective_from
        date effective_to
    }

    payroll_runs {
        int id PK
        varchar period
        date period_start
        date period_end
        varchar status
        int initiated_by FK
        datetime initiated_at
        datetime finalized_at
    }

    payroll_records {
        int id PK
        int run_id FK
        int employee_id FK
        decimal basic_pay
        decimal hra
        decimal other_allowances
        decimal gross_pay
        decimal lop_days
        decimal lop_deduction
        decimal overtime_pay
        decimal pf_employee
        decimal pf_employer
        decimal esi_employee
        decimal esi_employer
        decimal tds
        decimal reimbursements
        decimal bonuses
        decimal total_deductions
        decimal net_pay
    }

    payslips {
        int id PK
        int record_id FK
        varchar pdf_url
        datetime generated_at
        bool is_delivered
        datetime delivered_at
    }

    tax_declarations {
        int id PK
        int employee_id FK
        int financial_year
        decimal section_80c
        decimal hra_exemption
        decimal other_exemptions
        decimal total_declared
        varchar status
        datetime submitted_at
    }

    expense_claims {
        int id PK
        int employee_id FK
        varchar category
        decimal amount
        varchar receipt_url
        varchar status
        int approver_id FK
        int payroll_run_id FK
        text rejection_reason
        datetime submitted_at
        datetime decided_at
    }

    bonuses {
        int id PK
        int employee_id FK
        varchar bonus_type
        decimal amount
        text remarks
        int payroll_run_id FK
        datetime created_at
    }

    appraisal_cycles {
        int id PK
        varchar name
        varchar cycle_type
        date start_date
        date end_date
        date self_assessment_deadline
        date manager_review_deadline
        varchar status
    }

    goals {
        int id PK
        int employee_id FK
        int cycle_id FK
        varchar title
        text description
        decimal weightage
        decimal progress_percent
        varchar status
        date deadline
    }

    kras {
        int id PK
        int cycle_id FK
        varchar name
        decimal weightage
    }

    performance_reviews {
        int id PK
        int cycle_id FK
        int employee_id FK
        int reviewer_id FK
        decimal self_score
        decimal manager_score
        decimal final_score
        varchar status
        varchar manager_recommendation
        datetime self_submitted_at
        datetime manager_submitted_at
        datetime finalized_at
    }

    kra_ratings {
        int id PK
        int review_id FK
        int kra_id FK
        decimal self_rating
        text self_comment
        decimal manager_rating
        text manager_comment
        decimal final_rating
    }

    pips {
        int id PK
        int employee_id FK
        int initiated_by FK
        date start_date
        date end_date
        text objectives
        varchar status
        text outcome
        datetime closed_at
    }

    pip_checkins {
        int id PK
        int pip_id FK
        int recorded_by FK
        text notes
        datetime recorded_at
    }

    benefit_plans {
        int id PK
        varchar name
        varchar type
        text description
        decimal employer_contribution
        bool is_active
    }

    benefit_enrolments {
        int id PK
        int employee_id FK
        int plan_id FK
        date enrolment_date
        date end_date
        decimal employee_contribution
        decimal employer_contribution
        varchar status
    }

    notifications {
        int id PK
        int user_id FK
        varchar event_type
        varchar title
        text body
        bool is_read
        json payload_json
        datetime created_at
    }

    audit_logs {
        int id PK
        int user_id FK
        varchar module
        varchar action
        int resource_id
        json before_json
        json after_json
        varchar ip_address
        datetime created_at
    }

    users ||--o{ employees : linked_to
    employees }o--|| departments : belongs_to
    employees }o--|| designations : holds
    designations }o--|| grades : mapped_to
    employees }o--o| employees : reports_to
    employees ||--o{ employee_documents : has
    employees ||--o| onboarding_checklists : has
    onboarding_checklists ||--o{ onboarding_tasks : contains

    leave_policies ||--o{ leave_types : defines
    employees ||--o{ leave_balances : holds
    leave_types ||--o{ leave_balances : type_of
    employees ||--o{ leave_requests : submits
    leave_types ||--o{ leave_requests : type_of
    holiday_calendars ||--o{ holidays : contains

    employees ||--o{ shift_assignments : assigned
    shifts ||--o{ shift_assignments : used_in
    employees ||--o{ attendance_records : has
    attendance_records ||--o{ attendance_regularizations : may_have
    employees ||--o{ timesheets : submits
    timesheets ||--o{ timesheet_entries : contains
    employees ||--o{ comp_off_requests : applies

    employees ||--o{ salary_structures : has
    payroll_runs ||--o{ payroll_records : contains
    employees ||--o{ payroll_records : included_in
    payroll_records ||--|| payslips : generates
    employees ||--o{ tax_declarations : files
    employees ||--o{ expense_claims : submits
    employees ||--o{ bonuses : receives

    appraisal_cycles ||--o{ goals : tracks
    appraisal_cycles ||--o{ kras : defines
    appraisal_cycles ||--o{ performance_reviews : contains
    employees ||--o{ goals : has
    employees ||--o{ performance_reviews : has
    performance_reviews ||--o{ kra_ratings : contains
    kras ||--o{ kra_ratings : rated_in
    employees ||--o{ pips : subject_of
    pips ||--o{ pip_checkins : has

    benefit_plans ||--o{ benefit_enrolments : enrolled_in
    employees ||--o{ benefit_enrolments : has

    users ||--o{ notifications : receives
    users ||--o{ audit_logs : generates
```

---

## Schema Notes

### Leave Balance Tracking
`leave_balances` tracks entitled, accrued, used, pending, lapsed, and carried-forward balances per employee per leave type per year. Available balance is computed as: `accrued - used - pending`.

### Attendance & Payroll Integration
`attendance_records` feeds into payroll via LOP calculation. Approved `timesheet_entries` provide project-level hour tracking for billable clients.

### Payroll Immutability
Once a `payroll_run` is finalized, `payroll_records` are immutable. Corrections require a new off-cycle run.

### Performance Review Score Computation
`kra_ratings.final_rating` is weighted by `kras.weightage` to produce `performance_reviews.final_score`.

### Audit Trail
`audit_logs` captures all write operations across all modules with before/after JSON snapshots for compliance.

---

---

## Process Narrative (Database schema design)
1. **Initiate**: Database Architect captures the primary change request for **Erd Database Schema** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to database schema design.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Migration Engine executes the approved path and enforces relational constraint checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm data persistence.

## Role/Permission Matrix (Erd Database Schema)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View erd database schema artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Database schema design)
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

## Integration Behavior (Erd Database Schema)
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

