# EMIS Edge Cases — Master Index

> **Authoritative reference for all non-happy-path scenarios in the Education Management Information System.**
>
> This index catalogues every identified edge case, failure mode, and boundary condition across all EMIS modules. Engineers, QA teams, support staff, and SREs should consult this document before implementing any feature that touches critical academic, financial, or compliance workflows. Every edge case here has been derived from real failure patterns observed in production educational systems, regulatory breach post-mortems, and security audits.

---

## Table of Contents

1. [Coverage Map](#coverage-map)
2. [Top Critical Edge Cases](#top-critical-edge-cases)
3. [Cross-Cutting Edge-Case Principles](#cross-cutting-edge-case-principles)
4. [Edge Case Testing Strategy](#edge-case-testing-strategy)
5. [Monitoring and Alert Coverage](#monitoring-and-alert-coverage)
6. [Document Conventions](#document-conventions)
7. [Contributing Guidelines](#contributing-guidelines)

---

## Coverage Map

| Domain File | Business Impact | Likelihood | Primary File | Critical EC Count |
|-------------|-----------------|------------|--------------|-------------------|
| Academic Operations | 🔴 Critical — affects graduation, GPA, transcripts | Medium–High | `academic-operations.md` | 6 |
| Enrollment & Registration | 🔴 Critical — affects course access, student standing | High (peak: add/drop) | `enrollment-and-registration.md` | 5 |
| Finance & Payments | 🔴 Critical — revenue, audit, student holds, compliance | High (peak: semester start) | `finance-and-payments.md` | 7 |
| Notifications | 🟠 High — FERPA risk, deadline misses, consent | Medium | `notifications.md` | 4 |
| Security & Compliance | 🔴 Critical — data breach, FERPA/PDPA, regulatory fine | Low–Medium (high severity) | `security-and-compliance.md` | 8 |
| API & UI | 🟠 High — double payments, data loss, injection | Medium–High | `api-and-ui.md` | 4 |
| Operations | 🔴 Critical — data loss, RPO breach, downtime | Low (catastrophic if hit) | `operations.md` | 5 |

**Total documented edge cases: 63** across 7 domain files.

---

## Top Critical Edge Cases

### Academic Operations (`academic-operations.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-ACAD-001 | Concurrent registration for last seat | Race condition assigns same seat to multiple students; course over-capacity triggers compliance issues and manual resolution during peak load |
| EC-ACAD-003 | GPA with repeated/remedial courses | Wrong GPA calculation can incorrectly trigger academic probation, affect scholarship eligibility, or produce invalid transcripts — all legally actionable |
| EC-ACAD-008 | Curriculum change mid-enrollment | Students can be silently blocked from graduation if new graduation requirements apply retroactively; requires grandfathering logic |

### Enrollment & Registration (`enrollment-and-registration.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-ENROLL-001 | Accepted application enrollment deadline missed | Auto-expiry with no recovery path creates enrolment loss and re-admission complexity; affects revenue and accreditation headcounts |
| EC-ENROLL-010 | System crash during bulk enrollment | Partial commits leave students in unknown states — some enrolled, some not — with no transactional rollback visibility |
| EC-ENROLL-006 | Batch import with duplicates | Duplicate student records create split academic histories, GPA miscalculation, and financial account confusion that can persist for years |

### Finance & Payments (`finance-and-payments.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-FIN-001 | Payment gateway timeout — money debited, not confirmed | Student charged without EMIS acknowledging payment; leads to double payment, financial hold blocking exams, support escalation |
| EC-FIN-002 | Double payment for same invoice | Duplicate charge triggers chargebacks; refund path may have accounting period mismatches; auditor flagging |
| EC-FIN-010 | Audit trail gap during migration | Financial records without complete audit trail fail regulatory and accreditation audits; can require full manual reconstruction |

### Notifications (`notifications.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-NOTIF-001 | Grade sent before official publication | Premature grade disclosure violates FERPA; if grade is wrong and then corrected, student has documentary evidence of original — legal risk |
| EC-NOTIF-004 | Bulk announcement to wrong group | Sending a private communication (e.g., disciplinary notice) to all 5,000 students is a severe privacy breach |
| EC-NOTIF-005 | SMTP outage during critical deadline | Students miss fee or registration deadlines because notifications never arrived; institution liable for deadline extensions |

### Security & Compliance (`security-and-compliance.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-SEC-001 | PII in error response body | Stack traces with student data can be scraped by any user who triggers an error; FERPA/PDPA breach reportable within 72 hours |
| EC-SEC-003 | Parent accesses adult student data without consent | Direct FERPA violation; institution can lose federal funding; student must be notified |
| EC-SEC-007 | Audit log write failure silently dropped | Compliance-required events missing from audit trail mean the institution cannot prove compliance — catastrophic in an audit |

### API & UI (`api-and-ui.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-API-001 | Double-submit on fee payment | Student charged twice; second charge may succeed at gateway even if EMIS tries to prevent it; requires immediate reversal path |
| EC-API-006 | Search query injection in student name filter | SQL/ORM injection can expose entire student database; FERPA breach + data destruction risk |
| EC-API-007 | Session expiry during multi-step registration | Students lose course selections mid-registration during peak add/drop; frustration, re-entry under contention for seats |

### Operations (`operations.md`)

| EC-ID | Name | Why Critical |
|-------|------|-------------|
| EC-OPS-001 | DB failover during active fee payment | In-flight transaction may commit at DB level but not at application level — or vice versa; financial inconsistency |
| EC-OPS-004 | DB migration failure mid-deployment | Partial schema change leaves DB in inconsistent state; rollback may not be possible without data loss |
| EC-OPS-006 | Backup fails 7 days undetected | RPO breach means a failure could result in up to 7 days of unrecoverable academic and financial data loss |

---

## Cross-Cutting Edge-Case Principles

These principles apply universally across all EMIS modules and must be respected in every implementation decision.

### P-01 — Idempotency for All Mutating Operations

Every mutating API endpoint (grade submission, payment, enrollment, attendance marking) **must** be idempotent. Clients must supply an `Idempotency-Key` header; the server must store the response for at least 24 hours keyed by this value. Replaying the same request must return the same result without side-effects.

```python
# Django middleware pattern
class IdempotencyMiddleware:
    def __call__(self, request):
        if request.method in ('POST', 'PUT', 'PATCH'):
            key = request.headers.get('Idempotency-Key')
            if key:
                cached = cache.get(f'idempotency:{key}')
                if cached:
                    return JsonResponse(cached['body'], status=cached['status'])
```

### P-02 — Deterministic Error Codes

All errors must return a machine-readable `error_code` field alongside the HTTP status. Error codes must be stable across releases. Internal server errors must never expose stack traces, SQL queries, or PII to the client.

```json
{
  "error_code": "ENROLLMENT_CAPACITY_EXCEEDED",
  "message": "Course capacity has been reached.",
  "request_id": "req_01J..."
}
```

### P-03 — Immutable Audit Trail

Every change to a student academic record, financial transaction, or access control decision must be written to an append-only audit log. Audit records must include: actor (user ID + role), timestamp (UTC), resource (entity type + ID), action, before-state hash, after-state hash, and IP address. Audit records are **never** updated or deleted — corrections are new records that reference the original.

### P-04 — Human Override with Accountability

Any system-enforced rule (enrollment cap, grade lock, fee hold) must have a documented override path requiring elevated privilege, a mandatory written justification, and automatic notification to at least one additional authority (e.g., department head + registrar). Overrides are prominently flagged in audit logs and reports.

### P-05 — Student Data Protection at Every Boundary

PII leaves EMIS only through explicitly approved export paths. API responses must strip fields not relevant to the calling role. Error messages must never include student names, IDs, grades, financial data, or health information. Logging must use `student_id` (internal hash) rather than national ID or name.

### P-06 — Graceful Degradation

When a non-critical dependency (email, SMS, analytics, LMS CDN) fails, EMIS core operations (grade viewing, enrollment, payment) must continue. Failures must be queued for later delivery. A circuit breaker must open after 5 consecutive failures in 60 seconds and half-open after 30 seconds.

### P-07 — Retry Safety

All retried operations (Celery tasks, webhook callbacks, payment polling) must be idempotent. Tasks must carry an `attempt_number` and a `max_attempts` limit. Exponential backoff with jitter must be used. Dead-letter queues must exist for all task queues; DLQ depth is a monitored alert.

### P-08 — Compensation Transactions

Complex multi-step operations (enrollment + fee generation + LMS access provisioning) must define a compensation path for each step. If step N fails, steps 1 through N-1 must be compensated in reverse order. Compensation steps must be logged separately. The saga pattern or two-phase commit must be chosen explicitly per workflow.

### P-09 — Observability-First

Every critical operation must emit a structured log event at completion (success or failure), a metrics counter increment (tagged by module, operation, outcome), and a distributed trace span. Alert thresholds must be defined before a feature goes to production. "Silent success" is not acceptable for financial or academic operations.

### P-10 — Policy Versioning

Academic policies (fee structures, graduation requirements, grading scales, enrollment rules) must be versioned with an effective date. When a policy changes, existing records must retain a reference to the policy version under which they were created. This ensures historical correctness even after policy updates.

### P-11 — Timezone Handling

All timestamps stored in PostgreSQL must be `TIMESTAMPTZ` (UTC). Business logic deadlines (enrollment close, fee due, exam start) must be stored with explicit timezone offset and displayed in the user's local timezone. Deadline enforcement must compare UTC-to-UTC; never assume server timezone equals user timezone.

```python
# Always use timezone-aware datetimes
from django.utils import timezone
deadline = timezone.now()  # NOT datetime.now()
```

### P-12 — Eventual Consistency Acknowledgement

Certain EMIS operations are eventually consistent (grade propagation to transcripts, payment confirmation from gateway, enrollment headcount in analytics). Every eventually-consistent flow must have: a defined SLA for convergence, a reconciliation job that detects and corrects divergence, and a user-visible status indicator ("Processing — results may take up to 5 minutes").

---

## Edge Case Testing Strategy

### Chaos Engineering Experiments

| Experiment | Target Component | Trigger | Expected Behaviour | Cadence |
|-----------|-----------------|---------|-------------------|---------|
| Kill primary DB during payment | PostgreSQL primary | `pg_ctl stop` mid-transaction | Failover within 30s; payment idempotent on reconnect | Monthly |
| Redis flush during enrollment | Redis cache | `FLUSHALL` during add/drop peak sim | Cache miss fallback to DB; no data loss; latency spike < 3s | Monthly |
| Kill Celery worker mid-task | Celery notification worker | `kill -9 <pid>` | Task requeued from Redis; notification delivered exactly once | Weekly |
| SMTP server down | Email service | Block port 587 | Notifications queued; no exception propagated to user | Weekly |
| Payment gateway 30s timeout | Stripe/Razorpay mock | Nginx delay rule | Timeout detected; payment status set to `PENDING_VERIFICATION`; alert fired | Monthly |
| Disk full on app server | Application filesystem | `fallocate` fill to 95% | 503 with graceful error; DB writes unaffected; alert < 2min | Quarterly |
| Certificate expiry in 7 days | TLS certificate | Rotate to near-expiry cert | Alert fires on day 30 and day 7; no user impact | Quarterly |

### Load and Concurrency Tests

| Scenario | Tool | Target | Pass Criteria |
|---------|------|--------|--------------|
| 500 concurrent course registrations for 1 seat | Locust | Enrollment endpoint | Exactly 1 succeeds; 499 receive 409; no duplicate enrollments |
| 1,000 concurrent fee payments | k6 | Payment endpoint | 0 duplicate charges; p99 latency < 5s; idempotency key deduplication works |
| Bulk grade import (10,000 records) | Locust | Grade import API | Completes < 120s; partial failure report accurate; no duplicate grades |
| Timetable generation for 200 courses | pytest-benchmark | Timetable algorithm | Generates conflict-free schedule < 30s; detects 100% of injected conflicts |
| Report generation under load | k6 | Analytics endpoints | Long queries do not block OLTP queries; report timeout at 60s |

### Contract Tests

All external integrations must have contract tests that run in CI:

- **Payment gateways** (Stripe, Razorpay): Verify webhook signature validation, refund response schema, timeout behaviour.
- **SMTP relay**: Verify EHLO response, auth failure handling, bounce callback parsing.
- **SMS gateway**: Verify delivery receipt schema, opt-out callback format.
- **S3/object storage**: Verify multipart upload completion, pre-signed URL expiry, access-denied error format.

### Regression Suite Tagging

All tests related to edge cases in this document must be tagged:

```python
@pytest.mark.edge_case
@pytest.mark.ec_id("EC-FIN-001")
def test_payment_gateway_timeout_idempotency():
    ...
```

CI must run `pytest -m edge_case` on every PR that touches a critical module. The tag-to-EC-ID mapping is maintained in `tests/edge_case_index.json`.

---

## Monitoring and Alert Coverage

| Alert Name | Condition | Severity | Notification Channel | Runbook |
|-----------|-----------|----------|---------------------|---------|
| `emis.payment.pending_verification_count` | > 5 in 10 min | 🔴 Critical | PagerDuty + Slack #finance-ops | EC-FIN-001 |
| `emis.payment.duplicate_invoice_attempt` | Any occurrence | 🔴 Critical | PagerDuty | EC-FIN-002 |
| `emis.enrollment.over_capacity` | Any occurrence | 🔴 Critical | Slack #academic-ops + Registrar email | EC-ACAD-001 |
| `emis.grade.submission_after_lock` | Any occurrence | 🟠 High | Slack #academic-ops | EC-ACAD-002 |
| `emis.notification.dlq_depth` | > 0 | 🟠 High | Slack #platform | EC-NOTIF-005 |
| `emis.notification.premature_grade_send` | Any occurrence | 🔴 Critical | PagerDuty + Slack #compliance | EC-NOTIF-001 |
| `emis.security.pii_in_error_response` | Any occurrence | 🔴 Critical | PagerDuty + Slack #security | EC-SEC-001 |
| `emis.security.stale_jwt_access` | Any occurrence | 🔴 Critical | PagerDuty + Slack #security | EC-SEC-002 |
| `emis.audit.write_failure` | Any occurrence | 🔴 Critical | PagerDuty | EC-SEC-007 |
| `emis.db.replication_lag` | > 30s | 🟠 High | Slack #platform | EC-OPS-001 |
| `emis.celery.dlq_depth` | > 0 | 🟠 High | Slack #platform | EC-OPS-002 |
| `emis.cache.hit_rate` | < 50% for 5 min | 🟠 High | Slack #platform | EC-OPS-003 |
| `emis.disk.usage_percent` | > 85% | 🔴 Critical | PagerDuty | EC-OPS-005 |
| `emis.backup.last_success_hours` | > 25h | 🔴 Critical | PagerDuty + Email DBA | EC-OPS-006 |
| `emis.db.long_running_query_seconds` | > 30s | 🟠 High | Slack #platform | EC-OPS-007 |
| `emis.enrollment.batch_partial_failure` | Any occurrence | 🟠 High | Slack #academic-ops | EC-ENROLL-006 |
| `emis.api.idempotency_collision` | > 10 in 1 min | 🟠 High | Slack #platform | EC-API-001 |
| `emis.lms.upload_orphan_count` | > 0 for 1h | 🟡 Medium | Slack #platform | EC-API-003 |

---

## Document Conventions

Every edge case in this repository follows a strict 5-section format. Deviations require a PR comment justification.

### Section 1 — Header
```
### EC-[DOMAIN]-[NNN]: [Descriptive Name]
```
- `DOMAIN`: 4–6 uppercase letters identifying the domain (`ACAD`, `ENROLL`, `FIN`, `NOTIF`, `SEC`, `API`, `OPS`)
- `NNN`: Zero-padded 3-digit sequence within the domain
- Name: Imperative verb phrase describing the failure (not the component)

### Section 2 — Failure Mode
What exactly goes wrong. Include the specific sequence of events, the system components involved, and any preconditions. Be precise enough that an engineer unfamiliar with the system can reproduce the failure in a test environment.

### Section 3 — Impact
Business and user impact. Quantify where possible: number of affected users, financial exposure, regulatory consequence, SLA breach duration. Distinguish between immediate impact and downstream cascade effects.

### Section 4 — Detection
Must include at least two of: monitoring query (Prometheus/PromQL or SQL), alert name from the monitoring table above, specific log pattern with log level and message template, metric threshold.

### Section 5 — Mitigation/Recovery
Numbered step-by-step procedure executable by an on-call engineer with normal production access. The first step is always "confirm the incident" and the last step is always "write incident report and update this document if new findings."

### Section 6 — Prevention
The specific code change, infrastructure configuration, or process change that eliminates recurrence. Must be actionable and specific — not generic advice. Link to the relevant Django model, view, or configuration file where the change should be made.

---

## Contributing Guidelines

### Adding a New Edge Case

1. Identify the correct domain file from the Coverage Map.
2. Assign the next sequential EC-ID within that domain.
3. Fill in **all 5 sections** completely. PRs with placeholder text will be rejected.
4. Add the EC-ID to `tests/edge_case_index.json` with the corresponding test tag.
5. If the edge case requires a new monitoring alert, add it to the Monitoring and Alert Coverage table above.
6. Update the "Critical EC Count" in the Coverage Map if the new EC is critical (🔴 impact).

### Reviewing an Edge Case PR

- Verify all 5 sections are complete and EMIS-specific.
- Check that the detection method is actually implemented (metric exists, log pattern is real).
- Verify the prevention code snippet is syntactically correct Django/Python.
- Confirm the EC-ID does not collide with an existing one.

### When an Edge Case is Resolved

Move the EC entry under a `## Resolved Edge Cases` section at the bottom of the domain file. Add a `**Resolved:**` line with the date, the PR/commit that fixed it, and a brief summary of the prevention measure applied. Keep resolved ECs in the file for historical reference.

### Ownership

| Domain | Owner Team | Escalation |
|--------|-----------|-----------|
| Academic Operations | Registrar Engineering | VP Academic Affairs |
| Enrollment & Registration | Registrar Engineering | Registrar |
| Finance & Payments | Finance Engineering | CFO + External Auditor |
| Notifications | Platform Engineering | DPO |
| Security & Compliance | Security Engineering | DPO + Legal |
| API & UI | Frontend + Platform Engineering | CTO |
| Operations | SRE | CTO + DBA |
