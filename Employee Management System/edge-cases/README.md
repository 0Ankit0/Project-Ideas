# Edge Cases — Employee Management System

## Introduction

Employee Management Systems handle three categories of highly sensitive data: **Personally Identifiable Information (PII)**, **financial compensation data**, and **compliance-regulated HR records**. Edge cases in these domains are not minor inconveniences — they carry real business and legal consequences:

- **PII breaches** can trigger GDPR/CCPA fines up to 4% of global annual turnover
- **Incorrect payroll** exposes the company to labor law violations, employee lawsuits, and tax penalties
- **Compliance gaps** (missed audit trails, improper data retention, unauthorized access) can result in regulatory sanctions
- **Workflow failures** (broken offboarding, orphaned approvals) create operational risk and legal liability

This document catalogs every known edge case category across the Employee Management System, their criticality ratings, and cross-references to business rules that govern their resolution.

---

## Edge Case File Index

| File | Domain | Edge Cases | Criticality | Business Impact |
|------|--------|-----------|-------------|-----------------|
| [onboarding-and-offboarding.md](./onboarding-and-offboarding.md) | Onboarding & Offboarding | 15 | CRITICAL–HIGH | Compliance, employee experience, data integrity |
| [attendance-and-leave.md](./attendance-and-leave.md) | Attendance & Leave | 15 | HIGH–MEDIUM | Labor law compliance, payroll accuracy |
| [payroll-and-benefits.md](./payroll-and-benefits.md) | Payroll & Benefits | 15 | CRITICAL | Financial accuracy, tax compliance, legal liability |
| [performance-and-review-cycles.md](./performance-and-review-cycles.md) | Performance & Reviews | 15 | HIGH–MEDIUM | Employee relations, legal challenges, data integrity |
| [api-and-ui.md](./api-and-ui.md) | API & UI | 15 | HIGH–MEDIUM | System reliability, data integrity, user experience |
| [security-and-compliance.md](./security-and-compliance.md) | Security & Compliance | 14 | CRITICAL | Regulatory fines, breach liability, trust |
| [operations.md](./operations.md) | Operations & Reliability | 14 | CRITICAL–HIGH | System availability, SLA compliance, recovery |

---

## Edge Case Criticality Ratings

### CRITICAL
Scenarios that result in one or more of the following:
- **Data loss** — permanent loss of employee, payroll, or audit records
- **Wrong pay** — employee receives incorrect salary, bonus, or deductions
- **Compliance breach** — violation of GDPR, CCPA, FLSA, labor law, or tax regulations
- **Security breach** — unauthorized access to PII or financial data
- **Payroll system downtime** on a pay date

**Response SLA:** Immediate escalation. Incident commander assigned within 15 minutes. Resolution or mitigation within 4 hours.

### HIGH
Scenarios that result in:
- **User experience degradation** — workflows blocked, incorrect UI state
- **Data integrity issues** — orphaned records, inconsistent state across services
- **Audit gaps** — missing or incomplete audit log entries
- **Approval workflow failures** — approvals lost, reassignment not triggered

**Response SLA:** Escalation within 1 hour. Resolution within 24 hours.

### MEDIUM
Scenarios that result in:
- **Performance degradation** — slow queries, timeouts on non-critical paths
- **Minor calculation errors** that are auto-corrected in the next cycle
- **UI/UX inconsistencies** that do not block primary workflows
- **Non-critical sync delays** (e.g., reporting data 1-hour stale)

**Response SLA:** Ticket filed. Resolution within 5 business days.

### LOW
Scenarios that result in:
- **Cosmetic issues** — label misalignment, minor formatting errors
- **Non-blocking UX annoyances** — extra click required, suboptimal flow
- **Edge case in rarely-used report** — affects less than 1% of users

**Response SLA:** Backlog. Resolution in next sprint or quarterly release.

---

## Business Rules Reference Matrix

The following business rules are defined in the system's core domain model. Edge cases that trigger violations of these rules require special handling workflows.

| Rule ID | Rule Name | Description |
|---------|-----------|-------------|
| BR-01 | Minimum Onboarding Period | Employee must complete mandatory onboarding tasks within 30 days of hire |
| BR-02 | Leave Balance Integrity | Approved leave cannot exceed available balance + projected accruals |
| BR-03 | Attendance Data Immutability Window | Attendance records older than 7 days require HR Admin approval to correct |
| BR-04 | Payroll Cutoff Enforcement | No changes to employee records allowed within 2 business days of payroll run |
| BR-05 | Review Cycle Completion | All direct reports must have reviews submitted before manager's own review closes |
| BR-06 | Reviewer Eligibility | Reviewer must have worked with the reviewee for at least 90 days in the review period |
| BR-07 | Data Retention Minimum | PII must be retained 7 years post-termination; financial data 7 years; performance 5 years |
| BR-08 | Final Pay Calculation | Separation pay = (years of service x monthly salary / 12) + prorated unused leave |
| BR-09 | Dual Approval Threshold | Salary changes >20% or bonuses >50% of monthly salary require dual HR approval |
| BR-10 | GDPR Erasure Constraint | Erasure requests cannot delete data under active legal hold or within retention window |

---

## Edge Case Trigger Matrix

This matrix shows which business rules (BR-01 to BR-10) are triggered by edge cases across each domain file.

| Domain | BR-01 | BR-02 | BR-03 | BR-04 | BR-05 | BR-06 | BR-07 | BR-08 | BR-09 | BR-10 |
|--------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| Onboarding & Offboarding | Y | | | | | | Y | Y | | Y |
| Attendance & Leave | | Y | Y | | | | | | | |
| Payroll & Benefits | | | | Y | | | Y | Y | Y | |
| Performance & Reviews | Y | | | | Y | Y | Y | | | |
| API & UI | | Y | Y | Y | | | | | | |
| Security & Compliance | | | | | | | Y | | | Y |
| Operations | | | | Y | | | Y | | | |

---

## Testing Guidance for Edge Cases

### Unit Test Coverage
Each edge case marked **CRITICAL** must have a corresponding unit test that:
1. Sets up the triggering condition (e.g., `leave_balance = -1`)
2. Calls the relevant service method
3. Asserts the correct system behavior (error thrown, event emitted, record created)
4. Verifies that audit log entry was created

### Integration Test Coverage
Edge cases that span multiple services (e.g., payroll + leave + attendance) must have integration tests using a real (test) database and message broker, validating the complete data flow from trigger to resolution.

### Test Data Requirements
- Use deterministic test fixtures (seed data) for financial calculations
- Never use production data in test environments
- For payroll edge cases, use isolated test ledger accounts
- For GDPR edge cases, use synthetic PII that is clearly marked as test data

### Regression Tagging
All edge case tests must be tagged with their Edge Case ID (e.g., `@edge-case OB-001`) so they can be run as a dedicated regression suite before each production release.

### Chaos Engineering
For **CRITICAL** operational edge cases (SEV-1, SEV-2), quarterly chaos tests should simulate:
- Database primary failover during payroll run
- Message broker unavailability during leave approval
- Cache eviction during bulk attendance import

---

## Document Maintenance

| Field | Value |
|-------|-------|
| Last Updated | 2025-01-01 |
| Owner | Platform Engineering / HR Systems Team |
| Review Cadence | Quarterly or after any SEV-1/SEV-2 incident |
| Related Documents | `infrastructure/deployment-diagram.md`, `infrastructure/network-infrastructure.md` |
