# User Stories

## Employee User Stories

### Account & Profile Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-001 | As an employee, I want to log in to the ESS portal so that I can access my information | - Login with email/password<br>- SSO option available<br>- 2FA supported |
| EMP-002 | As an employee, I want to update my personal contact details so that HR has current information | - Edit phone, address, emergency contact<br>- Changes trigger HR notification<br>- Audit log updated |
| EMP-003 | As an employee, I want to upload my documents so that they are stored centrally | - Upload ID proofs, certificates<br>- File type and size validation<br>- Download available |
| EMP-004 | As an employee, I want to view my employment details so that I know my role and grade | - View designation, department, grade<br>- View reporting manager<br>- View date of joining |

### Leave Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-005 | As an employee, I want to view my leave balance so that I can plan time off | - Balance per leave type shown<br>- Pending and approved leaves shown<br>- Available balance accurate |
| EMP-006 | As an employee, I want to apply for leave so that I can take time off | - Select leave type and dates<br>- Reason field required<br>- Confirmation sent |
| EMP-007 | As an employee, I want to cancel a pending leave request so that I can change my plans | - Cancel before approval<br>- Manager notified<br>- Balance restored |
| EMP-008 | As an employee, I want to view my leave history so that I can track past absences | - History by date range<br>- Status shown (approved/rejected)<br>- Download available |

### Attendance & Timesheet

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-009 | As an employee, I want to view my attendance records so that I can verify correctness | - Daily check-in/out shown<br>- Worked hours calculated<br>- Anomalies flagged |
| EMP-010 | As an employee, I want to submit my weekly timesheet so that my hours are recorded | - Enter hours per project<br>- Submit for approval<br>- Edit before approval |
| EMP-011 | As an employee, I want to regularize a missed attendance entry so that payroll is not affected | - Submit regularization request with reason<br>- Manager approval required<br>- Status visible |
| EMP-012 | As an employee, I want to apply for comp-off so that I am compensated for overtime | - Select overtime date<br>- Specify desired comp-off date<br>- Balance updated on approval |

### Payroll & Payslips

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-013 | As an employee, I want to view my payslips so that I know my earnings and deductions | - Payslip list by month<br>- Detailed breakdown shown<br>- PDF download available |
| EMP-014 | As an employee, I want to submit an expense claim so that I am reimbursed | - Upload receipts<br>- Enter amount and category<br>- Submission confirmation |
| EMP-015 | As an employee, I want to view my Form 16 / tax certificate so that I can file my taxes | - Available after financial year end<br>- PDF download<br>- Email delivery |
| EMP-016 | As an employee, I want to view my tax declaration so that I understand my deductions | - View declared investments<br>- Update during declaration window<br>- Impact on TDS shown |

### Performance & Goals

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-017 | As an employee, I want to set my goals so that my targets are recorded | - Add goals with description and KPIs<br>- Assign weightage<br>- Manager can comment |
| EMP-018 | As an employee, I want to update goal progress so that my manager can track it | - Update percentage complete<br>- Add progress notes<br>- Visible to manager |
| EMP-019 | As an employee, I want to complete my self-assessment so that I contribute to my appraisal | - Rate self per KRA<br>- Add supporting comments<br>- Submit within review window |
| EMP-020 | As an employee, I want to view my final appraisal rating so that I know my performance outcome | - Rating released by HR<br>- Feedback visible<br>- Download appraisal letter |

---

## Manager User Stories

### Team Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| MGR-001 | As a manager, I want to view my team's attendance so that I can monitor punctuality | - Team attendance dashboard<br>- Highlight late arrivals and absences<br>- Export to CSV |
| MGR-002 | As a manager, I want to approve or reject leave requests so that team coverage is maintained | - Pending requests list<br>- Approve/reject with reason<br>- Employee notified |
| MGR-003 | As a manager, I want to approve timesheets so that hours are validated | - Timesheet list per week<br>- Approve/reject individual entries<br>- Bulk approve option |
| MGR-004 | As a manager, I want to view team headcount and org chart so that I understand team structure | - Org chart view<br>- Active/inactive count<br>- Drill-down by sub-team |

### Performance Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| MGR-005 | As a manager, I want to set goals for my team so that expectations are aligned | - Assign goals to employees<br>- Set deadlines and KPIs<br>- Employees notified |
| MGR-006 | As a manager, I want to conduct appraisals so that I evaluate team performance | - Rate each KRA<br>- Write evaluation comments<br>- Recommend action (promotion, PIP, etc.) |
| MGR-007 | As a manager, I want to initiate a PIP for an employee so that performance issues are addressed | - Define PIP objectives and timeline<br>- Schedule check-ins<br>- HR notified |
| MGR-008 | As a manager, I want to provide 360-degree feedback so that reviews are comprehensive | - Submit peer feedback<br>- Rating and narrative fields<br>- Anonymous option |

### Leave & Scheduling

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| MGR-009 | As a manager, I want to view the team leave calendar so that I can plan coverage | - Calendar view with all approved leaves<br>- Conflict highlight<br>- Export option |
| MGR-010 | As a manager, I want to create shift rosters for my team so that coverage is planned | - Assign shifts per employee per day<br>- Conflict detection<br>- Publish roster to team |
| MGR-011 | As a manager, I want to approve shift swap requests so that team operations continue | - View swap request details<br>- Approve/reject<br>- Both employees notified |

---

## HR Staff User Stories

### Employee Lifecycle

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| HR-001 | As an HR staff, I want to create a new employee profile so that they are onboarded | - Fill personal and employment details<br>- Generate employee ID<br>- Send welcome email |
| HR-002 | As an HR staff, I want to manage onboarding checklists so that new hires complete required steps | - Create and assign tasks<br>- Track completion<br>- Send reminders |
| HR-003 | As an HR staff, I want to manage employee transfers so that org changes are reflected | - Update department/location/manager<br>- Effective date set<br>- History maintained |
| HR-004 | As an HR staff, I want to initiate the offboarding process so that departures are managed | - Trigger offboarding workflow<br>- Assign clearance tasks<br>- Generate final settlement |

### HR Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| HR-005 | As an HR staff, I want to configure leave policies so that entitlements are correct | - Define leave types<br>- Set entitlement rules<br>- Assign to employee groups |
| HR-006 | As an HR staff, I want to manage the holiday calendar so that leave calculations are accurate | - Add national and regional holidays<br>- Assign to locations<br>- Publish to employees |
| HR-007 | As an HR staff, I want to configure performance review cycles so that appraisals run on schedule | - Set cycle type and dates<br>- Select participating employees<br>- Enable notifications |
| HR-008 | As an HR staff, I want to manage organizational structure so that hierarchy is up to date | - Add/edit departments and designations<br>- Assign cost centers<br>- Update reporting lines |

### Compliance & Reporting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| HR-009 | As an HR staff, I want to generate headcount reports so that workforce data is available | - Filter by department, location, grade<br>- Export to CSV/PDF<br>- Schedule delivery |
| HR-010 | As an HR staff, I want to view attrition reports so that trends are visible | - Monthly attrition rate shown<br>- Voluntary vs involuntary split<br>- Exit reason analysis |
| HR-011 | As an HR staff, I want to track document expiry so that compliance is maintained | - Alert 30 days before expiry<br>- View expiring document list<br>- Notify employee |

---

## Payroll Officer User Stories

### Payroll Processing

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| PAY-001 | As a payroll officer, I want to run the monthly payroll so that salaries are processed | - Initiate payroll run<br>- Review computed values<br>- Approve and finalize |
| PAY-002 | As a payroll officer, I want to review payroll exceptions so that errors are corrected | - Exception list with reasons<br>- Override individual values<br>- Re-compute and validate |
| PAY-003 | As a payroll officer, I want to process off-cycle payments so that bonuses and corrections are paid | - Select employees<br>- Enter payment details<br>- Generate payslips |
| PAY-004 | As a payroll officer, I want to generate payslips so that employees receive their pay statements | - Bulk generate for all employees<br>- Email delivery<br>- Portal availability confirmed |

### Compliance & Reporting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| PAY-005 | As a payroll officer, I want to generate statutory compliance reports so that filings are on time | - PF, ESI, TDS reports<br>- Download in required format<br>- Filing deadlines tracked |
| PAY-006 | As a payroll officer, I want to process tax declarations so that TDS is accurate | - Employee declarations imported<br>- TDS recalculated<br>- Employees notified |
| PAY-007 | As a payroll officer, I want to generate Form 16 for all employees so that tax certificates are issued | - Bulk generation after year end<br>- Email delivery<br>- Acknowledgement tracked |
| PAY-008 | As a payroll officer, I want to view cost center payroll reports so that budget utilization is visible | - Breakdown by cost center<br>- Month-over-month variance<br>- Export available |

---

## Admin User Stories

### System Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to manage roles and permissions so that access is controlled | - Create and edit roles<br>- Assign granular permissions<br>- Assign roles to users |
| ADM-002 | As an admin, I want to configure system settings so that the platform works per company policy | - Set company name, logo, timezone<br>- Configure email templates<br>- Set fiscal year dates |
| ADM-003 | As an admin, I want to view audit logs so that I can monitor system activity | - Filter by user, action, module<br>- Date range filter<br>- Export to CSV |
| ADM-004 | As an admin, I want to manage integrations so that EMS connects to external systems | - Configure HRMS/ERP sync<br>- Set up biometric device integration<br>- Test connectivity |

### Reporting & Analytics

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-005 | As an admin, I want to view an executive dashboard so that leadership has key workforce metrics | - Headcount, attrition, payroll cost<br>- Real-time data<br>- Drill-down capability |
| ADM-006 | As an admin, I want to schedule automated reports so that stakeholders receive regular updates | - Configure report and recipients<br>- Set frequency<br>- Delivery confirmation |
| ADM-007 | As an admin, I want to manage the company org structure so that hierarchies are maintained | - Add/edit/remove departments<br>- Manage locations<br>- Publish org chart |

---

---

## Process Narrative (User-story operationalization)
1. **Initiate**: Product Owner captures the primary change request for **User Stories** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to user-story operationalization.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Backlog System executes the approved path and enforces story readiness checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm delivery intent.

## Role/Permission Matrix (User Stories)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View user stories artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (User-story operationalization)
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

## Integration Behavior (User Stories)
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

