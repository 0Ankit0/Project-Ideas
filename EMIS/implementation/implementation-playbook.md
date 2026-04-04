# Implementation Playbook — Education Management Information System

> **Version:** 1.0 | **Status:** Active | **Owner:** Engineering Leadership
> **Scope:** End-to-end delivery of EMIS from project kickoff through production go-live and steady-state operations.

---

## 1. Delivery Goal

Build and launch a production-ready **Education Management Information System** that is secure, observable, and operationally resilient. The system must support the full student lifecycle from admissions through graduation, academic operations (courses, exams, attendance, timetable), fee management with online payments, an integrated LMS, HR and payroll, library management, hostel and transport management, and analytics dashboards — all operating under a role-based access model for 1,000–5,000 concurrent users. Every phase ships working, tested software with clear rollback paths.

---

## 2. Tech Stack Decisions

### Rationale Matrix

| Layer | Technology | Rationale |
|---|---|---|
| **Runtime** | Python 3.11+ | Mature ecosystem for data-heavy educational applications; strong ORM, admin, and testing tooling; PEP 657 fine-grained error locations aid debugging |
| **Framework** | Django 4.x | Batteries-included framework ideal for institutional systems: built-in admin, auth, ORM, migrations, forms, and session management reduce bespoke code; DRF extends it for API-first workflows |
| **ORM / Migrations** | Django ORM + django-migrations | Schema versioning is code-reviewed and CI-validated; auto-generated migrations reduce drift between schema and models; select_related/prefetch_related cover 95% of query optimization needs |
| **Primary Database** | PostgreSQL 15 | ACID transactions critical for grade submission, fee payment, and enrollment; row-level locking prevents concurrent registration conflicts; JSONB useful for flexible audit payloads and metadata |
| **Cache / Queue Broker** | Redis 7 | Sub-millisecond session reads; distributed locks for idempotent enrollment; Celery task broker; pub/sub for real-time dashboard updates |
| **Task Queue** | Celery 5.x | Async processing for report generation, bulk notifications, payroll runs, and PDF generation; beat scheduler for recurring academic calendar tasks |
| **Frontend** | Bootstrap 5 + HTMX | Progressive enhancement matches institutional IT environments (diverse devices, restricted browsers); HTMX enables SPA-like UX without a JS framework; Summernote for rich-text CMS content |
| **Authentication** | djangorestframework-simplejwt + Django sessions | JWT for API consumers (mobile, integrations); session auth for browser-based portals; shared user model supports both |
| **Web Server** | Gunicorn (WSGI) + Nginx | Gunicorn with multiple workers (2× CPU) handles concurrent requests; Nginx handles SSL termination, static file serving, rate limiting, and upstream load balancing |
| **Containerization** | Docker + Docker Compose (dev), Kubernetes or single-server (prod) | Docker ensures environment parity; Compose simplifies local multi-service setup; K8s optional for larger institutions needing horizontal scaling |
| **CI/CD** | GitHub Actions | Native integration with repository; parallel jobs for lint/test/build; environment secrets management; ArgoCD optional for GitOps |
| **Observability** | Prometheus + Grafana + Sentry | django-prometheus exports metrics; Grafana dashboards for request rate, latency, DB queries; Sentry for real-time exception tracking with full stack traces |

---

## 3. Team Structure

### Platform Team (3–4 engineers)
- Owns infrastructure-as-code, Docker/K8s configuration, CI/CD pipelines, and shared libraries (logging, auth middleware, base models, event bus).
- Defines and enforces architectural standards: no circular imports, services layer ownership of business logic, ORM query budgets per view.
- Reviews cross-cutting schema changes and manages database migration coordination across teams.

### Academic Core Team (4–5 engineers)
- Owns: `students`, `admissions`, `courses`, `timetable`, `faculty` apps.
- Responsible for student lifecycle, program and course catalog, enrollment with prerequisite enforcement, timetable conflict detection, and the admissions workflow from application through enrollment.
- Integrates with Finance team for enrollment-triggered fee invoice generation.

### Assessment & Compliance Team (3–4 engineers)
- Owns: `exams`, `attendance`, `analytics`, `reports` apps.
- Responsible for exam scheduling with invigilation, grade entry and GPA calculation, transcript generation, attendance tracking and academic hold enforcement, analytics dashboards, and custom report builder.
- Ensures data accuracy and audit trail completeness required for accreditation.

### Finance & HR Team (3–4 engineers)
- Owns: `finance`, `payment`, `hr`, `inventory`, `scholarships`, `recruitment` apps.
- Responsible for fee structure configuration, invoice generation, online payment gateway integration (Stripe/Razorpay), payroll processing, leave management, asset/stock management, scholarship program management with disbursement and stacking rules, and faculty recruitment pipeline from job posting through offer acceptance.
- Coordinates with Platform Team on payment saga idempotency and audit logging.

### LMS & Portal Team (3–4 engineers)
- Owns: `lms`, `library`, `hostel`, `transport`, `portal`, `cms`, `seo`, `calendar`, `files` apps.
- Responsible for course content delivery, assignments, quizzes, certificates, library circulation, hostel/transport management, role-specific portal UX, website CMS, and calendar management.

### Academic Lifecycle Team (3–4 engineers)
- Owns: `graduation`, `academic_standing`, `grade_appeals`, `academic_sessions` apps.
- Responsible for graduation eligibility and degree audit workflows, diploma generation, honors determination, academic standing calculation (probation, dean's list, at-risk alerts), grade dispute escalation (faculty → department head → committee), and academic session/semester lifecycle management including registration windows and calendar events.
- Integrates with Assessment & Compliance Team for grade data and with Finance & HR Team for graduation fee clearance.

### Compliance & Conduct Team (2–3 engineers)
- Owns: `discipline`, `transfer_credits` apps.
- Responsible for student disciplinary case management (filings, hearings, sanctions, appeals, record sealing), transfer credit evaluation, articulation agreement management, and credit equivalency mapping with configurable credit limits.
- Coordinates with Academic Core Team on student record updates and with Legal/Compliance on data retention policies.

### Facilities & Administration Team (2–3 engineers)
- Owns: `facilities`, `departments` apps.
- Responsible for room and facility inventory, booking and conflict detection, utilization analytics, maintenance request workflows, department hierarchy management, curriculum change tracking, and course offering administration.
- Integrates with Academic Core Team for timetable room allocation and with Platform Team for notification dispatch.

### DevOps / SRE Team (2–3 engineers)
- Owns production reliability, incident response, runbooks, SLO/SLI definitions, capacity planning.
- Manages Nginx configuration, Celery worker scaling, PostgreSQL tuning, Redis memory management.
- Runs quarterly load tests and annual disaster recovery drills.

---

## 4. CI/CD Pipeline

### Pipeline Stages and Gates

```
┌──────────────────────────────────────────────────────────────────┐
│  PR / Push Trigger                                               │
│                                                                  │
│  1. LINT & TYPE CHECK                                            │
│     • flake8 --max-line-length=100 --max-complexity=12           │
│     • black --check .                                            │
│     • isort --check-only .                                       │
│     • mypy emis/ --ignore-missing-imports                        │
│     Gate: zero lint errors, zero type errors                     │
│                                                                  │
│  2. UNIT TESTS                                                   │
│     • pytest --cov=apps --cov-report=xml                         │
│     • --cov-fail-under=80                                        │
│     Gate: ≥80% line/branch coverage; zero test failures          │
│                                                                  │
│  3. INTEGRATION TESTS                                            │
│     • Docker Compose: postgres:15 + redis:7 test containers      │
│     • pytest -m integration --reuse-db                           │
│     Gate: all integration tests pass                             │
│                                                                  │
│  4. MIGRATION CHECK                                              │
│     • python manage.py migrate --check                           │
│     • python manage.py makemigrations --check --dry-run          │
│     Gate: no missing migrations; existing migrations unmodified  │
│                                                                  │
│  5. SECURITY SCAN                                                │
│     • safety check -r requirements/prod.txt                      │
│     • bandit -r apps/ -ll (medium and high severity)             │
│     • semgrep --config=auto apps/                                │
│     Gate: zero high-severity CVEs; zero bandit HIGH findings     │
│                                                                  │
│  6. BUILD DOCKER IMAGE                                           │
│     • docker buildx build --platform linux/amd64                │
│     • Push to registry with SHA tag + branch tag                │
│     Gate: successful build under 5 minutes                       │
│                                                                  │
│  7. DEPLOY TO STAGING                                            │
│     • docker-compose -f docker-compose.staging.yml up -d         │
│     • python manage.py migrate                                   │
│     • python manage.py collectstatic --noinput                  │
│     Gate: all containers healthy; /health/ returns 200           │
│                                                                  │
│  8. E2E TESTS (Playwright)                                       │
│     • Student login → course registration → fee payment          │
│     • Faculty login → grade entry → publish grades               │
│     • Admin login → admissions → student enrollment              │
│     Gate: all critical-path E2E tests pass                       │
│                                                                  │
│  9. PERFORMANCE GATE (main branch only)                          │
│     • k6 run scripts/load-test.js                               │
│     • 200 VUs / 3 min; target: course list, dashboard, payment  │
│     Gate: p99 latency < 500ms; error rate < 0.1%               │
│                                                                  │
│ 10. PROMOTE TO PRODUCTION (manual approval required)             │
│     • Notify release channel in Slack                            │
│     • Rolling restart: one container at a time                   │
│     • Health check before next container restart                 │
└──────────────────────────────────────────────────────────────────┘
```

### Branch Strategy
- `main` → production; protected; requires 2 approvals + all pipeline gates green; no direct push.
- `staging` → staging environment; auto-deploys on merge; used for QA and demo.
- `feature/<ticket>-<short-desc>` → individual feature branches; merged to staging via PR.
- `hotfix/<ticket>-<short-desc>` → emergency production fixes; merged directly to main with 1 approval after tests.
- All database migrations must be backward-compatible (additive only) until the previous release is retired.

---

## 5. Phase-by-Phase Delivery Plan

### Phase 0 — Foundation (Weeks 1–4)

**Deliverables:**
- Django project scaffolding with 35-app structure
- `core` app: BaseModel, UUIDs, soft-delete, audit mixin
- `users` app: User model, RBAC, JWT auth, session auth, password policies
- CI/CD pipeline fully operational (lint → test → build → staging deploy)
- Docker Compose development environment
- PostgreSQL + Redis configured and health-checked
- Nginx reverse proxy with TLS in staging
- Prometheus + Sentry integrated
- Django admin customized with institutional branding

**Acceptance Criteria:**
- All team members can run `docker-compose up` and access the system
- JWT login/logout works end-to-end
- 6 roles (Super Admin, Admin, Faculty, Student, Parent, Staff) with RBAC
- CI pipeline passes on every PR within 8 minutes

---

### Phase 1 — Academic Core (Weeks 5–10)

**Deliverables:**
- `admissions` app: online application, document upload, workflow, merit list, acceptance/rejection
- `students` app: student profile, enrollment from admission, academic history, status management
- `courses` app: programs, semesters, course catalog, prerequisites, sections, enrollment with conflict detection
- `timetable` app: slot management, room allocation, conflict detection, timetable publication
- `faculty` app: faculty profiles, teaching load, qualifications, leave

**Acceptance Criteria:**
- Applicant submits application → admin reviews → accept → student enrolled with portal access
- Student registers for courses: prerequisite check, capacity check, timetable conflict check all enforced
- Timetable created for a semester with no room or faculty conflicts
- Faculty can view their teaching schedule

---

### Phase 2 — Assessment & Attendance (Weeks 11–16)

**Deliverables:**
- `exams` app: exam scheduling, hall assignment, invigilation, result entry
- Grade entry with lock/unlock flow; GPA calculation (configurable scale); transcript PDF generation
- `attendance` app: daily marking, bulk mark, leave application/approval, attendance reports, academic hold enforcement
- `analytics` app: student performance dashboard, pass/fail rates, at-risk student identification
- `reports` app: pre-built reports (enrollment, grades, attendance); custom report builder

**Acceptance Criteria:**
- Faculty marks attendance → system flags students below 75% threshold → automated warning sent
- Grades entered and published → GPA updated → transcript downloadable as PDF with institution letterhead
- At-risk student report generated and exportable as Excel

---

### Phase 3 — Finance & HR (Weeks 17–22)

**Deliverables:**
- `finance` app: fee structures, invoice generation per student per semester, installment plans, scholarships
- `payment` app: Stripe/Razorpay integration, online payment flow, receipt PDF, refund processing
- Financial reports: revenue by program, outstanding dues, payment trends
- `hr` app: employee onboarding, payroll (salary components, deductions, net pay), leave management, payslips
- `inventory` app: asset tracking, stock management, purchase orders, reorder alerts

**Acceptance Criteria:**
- Student makes online fee payment → receipt generated → invoice marked paid in real-time
- Payroll runs for a department: salary calculated from components, leave deductions applied, payslips generated as PDF and emailed
- Low-stock alert triggered and purchase order created with vendor notification

---

### Phase 4 — Extended Modules (Weeks 23–28)

**Deliverables:**
- `lms` app: course modules, content upload (PDF/video), assignments, quizzes (MCQ, True/False, short answer), auto-grading, discussion forums, certificates
- `library` app: book catalog, issue/return, reservations, fine calculation, digital resource catalog
- `hostel` app: room allocation, mess management, complaint management, hostel fee integration
- `transport` app: route management, vehicle assignment, student transport allocation, maintenance scheduling
- `notifications` app: email/SMS/in-app notifications, announcement system, notification preferences

**Acceptance Criteria:**
- Faculty creates quiz → students complete → auto-graded → results visible immediately
- Librarian issues book → return triggers fine calculation → fine added to student account
- Hostel room allocated → hostel fee automatically added to student fee invoice

---

### Phase 5 — Portal, CMS & Analytics (Weeks 29–34)

**Deliverables:**
- `portal` app: student portal (dashboard, quick links, personalized feed), faculty portal, parent portal, admin portal
- `cms` app: WYSIWYG page editor, news/announcements, gallery, event management
- `seo` app: meta tag management, sitemap generation, robots.txt, analytics integration
- `calendar` app: academic calendar, exam calendar, event calendar, personal calendars
- `files` app: document storage, versioning, sharing, access permissions
- Final E2E performance benchmarks and load testing

**Acceptance Criteria:**
- Parent portal shows child's grades, attendance, and outstanding fees without student login
- CMS editor publishes news article without developer intervention
- Academic calendar visible to all roles with upcoming exam and holiday markers
- System handles 1,000 concurrent users with p99 response time under 500ms

---

### Phase 6 — Academic Lifecycle (Weeks 35–42)

**Deliverables:**
- `academic_sessions` app: academic year and semester lifecycle management, registration window configuration, calendar event synchronization, semester open/close workflows
- `academic_standing` app: standing determination engine (good standing, probation, suspension, dismissal), dean's list generation, at-risk student alerts, GPA threshold configuration
- `graduation` app: graduation eligibility checks, degree audit engine with requirement matching, diploma PDF generation with institutional branding, honors classification (cum laude, magna cum laude, summa cum laude)
- `grade_appeals` app: multi-level escalation workflow (faculty → department head → appeals committee), evidence submission, resolution tracking, grade amendment integration

**Acceptance Criteria:**
- Academic session created → semesters auto-generated → registration windows open and close on schedule
- Student falls below GPA threshold → academic standing updated to probation → at-risk alert sent to advisor
- Student applies for graduation → degree audit runs → eligible students approved → diploma PDF generated with honors classification
- Student files grade appeal → escalates through faculty, department head, and committee levels → resolution applied to transcript

---

### Phase 7 — Support & Compliance Modules (Weeks 43–50)

**Deliverables:**
- `discipline` app: disciplinary case filing, hearing scheduling, sanction assignment, appeal process, record sealing for expunged cases
- `transfer_credits` app: transfer credit evaluation workflow, articulation agreement management, course equivalency mapping, configurable credit limits per program
- `scholarships` app: scholarship program creation, application and eligibility engine, disbursement processing with installment support, renewal evaluation based on academic standing, stacking rule enforcement to prevent over-award
- `recruitment` app: faculty job posting with department approval, applicant tracking through pipeline stages, interview scheduling with calendar integration, offer generation and acceptance workflow
- `facilities` app: room and facility inventory with capacity and equipment metadata, booking system with conflict detection, utilization analytics dashboard, maintenance request workflow with priority levels
- `departments` app: department hierarchy and organizational structure, program administration, curriculum change tracking with approval workflow, course offering management per semester

**Acceptance Criteria:**
- Discipline case filed → hearing scheduled → sanction applied → student notified; appeal reverses sanction if upheld
- Transfer credits submitted → evaluated against articulation agreements → approved credits mapped to equivalent courses and appear on transcript
- Scholarship awarded → disbursement scheduled → funds applied to student invoice; renewal check runs at semester end based on GPA
- Faculty position posted → applicants tracked → interviews scheduled → offer extended and accepted → onboarding initiated in HR
- Room booked for event → conflict with existing timetable detected and rejected; maintenance request submitted and tracked to resolution
- Department creates new course offering → curriculum change approved → course available for next semester registration

---

## 6. Launch Readiness Checklist

### Functional Readiness
- [ ] All 35 Django apps deployed and smoke-tested
- [ ] All 6 roles can log in and access their respective dashboards
- [ ] End-to-end admissions → enrollment → course registration flow verified
- [ ] Fee payment gateway tested with real sandbox credentials
- [ ] Grade entry, GPA calculation, and transcript generation verified
- [ ] Attendance marking and academic hold enforcement verified
- [ ] Email and SMS notifications delivered in staging
- [ ] Academic session lifecycle tested: year creation → semester open → registration window → semester close
- [ ] Graduation workflow tested end-to-end: eligibility check → degree audit → diploma generation → honors classification
- [ ] Discipline case lifecycle verified: case filing → hearing → sanction → appeal → record sealing
- [ ] Academic standing engine verified: GPA threshold triggers → probation/dean's list assignment → at-risk alerts dispatched
- [ ] Grade appeal escalation tested: faculty → department head → committee resolution → grade amendment applied
- [ ] Transfer credit evaluation verified: submission → equivalency mapping → credit applied to transcript
- [ ] Scholarship lifecycle tested: application → award → disbursement → renewal check → stacking rule enforcement
- [ ] Recruitment pipeline verified: job posting → applicant tracking → interview scheduling → offer management
- [ ] Facility booking tested: room reservation → conflict detection → utilization reporting → maintenance workflow
- [ ] Department administration verified: hierarchy management → curriculum changes → course offering per semester

### Security Readiness
- [ ] HTTPS enforced on all endpoints; HTTP redirects to HTTPS
- [ ] HSTS header set with 1-year max-age
- [ ] All Django `SECURE_*` settings enabled in production config
- [ ] SECRET_KEY not in codebase (loaded from environment/secrets manager)
- [ ] Database password not in codebase
- [ ] File upload validation (type whitelist, size limit, malware scan) verified
- [ ] SQL injection tests run against all filter endpoints
- [ ] CSRF protection verified on all form submissions
- [ ] Rate limiting on auth endpoints (login: 10/minute, password reset: 5/minute)
- [ ] Django admin URL changed from default `/admin/`
- [ ] PII not logged in application logs
- [ ] Dependency audit clean (`safety check`)

### Performance Readiness
- [ ] All list endpoints paginated (max 100 records)
- [ ] N+1 queries eliminated in student dashboard, course list, grade reports
- [ ] Database indexes verified on all FK fields and filtered columns
- [ ] Redis caching enabled for read-heavy views (course catalog, timetable)
- [ ] Celery workers running for async tasks (notifications, report generation, PDF creation)
- [ ] Static files served via Nginx (not Django runserver)
- [ ] `DEBUG=False` in production
- [ ] k6 load test: 500 VUs passes with p99 < 500ms

### Data Readiness
- [ ] Initial data fixtures loaded (programs, courses, academic year, fee structures)
- [ ] Admin accounts created with secure passwords
- [ ] Database backup scheduled and tested (restore verified)
- [ ] Audit log enabled and writing to persistent storage

### Observability Readiness
- [ ] Prometheus metrics endpoint `/metrics` accessible from monitoring subnet only
- [ ] Grafana dashboards deployed: requests/sec, error rate, DB query time, Celery queue depth
- [ ] Sentry DSN configured; test exception verified in Sentry dashboard
- [ ] Application logs shipping to centralized log store
- [ ] Health check endpoints: `/health/` (200 OK), `/health/db/` (DB ping), `/health/cache/` (Redis ping)
- [ ] On-call runbooks written and linked from monitoring alerts

### Legal & Compliance Readiness
- [ ] Privacy policy and terms of service pages published via CMS
- [ ] Data retention policy documented and configured
- [ ] Student data access audit log complete
- [ ] FERPA (or local equivalent) compliance review completed
- [ ] Cookie consent banner implemented

---

## 7. Rollback Procedures

### Code Rollback
```bash
# 1. Identify last known-good Docker image tag (from CI registry)
docker images emis-app --format "{{.Tag}}" | head -20

# 2. Update docker-compose.yml to previous image tag
sed -i 's/image: emis-app:v2.x.y/image: emis-app:v2.x.z/' docker-compose.yml

# 3. Rolling restart (no downtime if replicas > 1)
docker-compose up -d --no-deps --scale web=2 web
# Wait for new container health, then scale down old
docker-compose up -d --no-deps --scale web=1 web

# 4. Verify rollback
curl -f https://emis.institution.edu/health/ && echo "Rollback successful"
```

### Database Migration Rollback
```bash
# 1. Identify migration to roll back to
python manage.py showmigrations students

# 2. Reverse a specific migration
python manage.py migrate students 0005_previous_migration

# NOTE: Rollback only works if migration has a reverse_code defined.
# Always write reversible migrations. If not reversible, restore from backup.
```

### Configuration Rollback
```bash
# All secrets and config stored in environment variables or Secrets Manager
# Revert by updating environment variables in deployment config
# and restarting application containers
docker-compose up -d
```

---

## 8. Post-Launch Operations

### SLO Definitions

| Service | SLI | SLO Target |
|---|---|---|
| Student Portal | p99 page load latency | < 2 seconds |
| API endpoints | p95 response time | < 500ms |
| Fee Payment API | Success rate | ≥ 99.5% |
| Notification delivery | Email delivery rate | ≥ 99% within 5 minutes |
| Grade publication | System availability | 99.9% during exam result week |
| Overall platform | Monthly uptime | ≥ 99.5% |

### Incident Severity Levels

| Level | Definition | Response Time | Example |
|---|---|---|---|
| P1 — Critical | Full platform down; data loss risk; payment failure | 15 minutes | DB connection pool exhausted; payment gateway unavailable |
| P2 — High | Core academic feature unavailable during peak period | 30 minutes | Grade submission broken during exam week; enrollment closed |
| P3 — Medium | Non-critical feature degraded; workaround exists | 2 hours | Report generation failing; notification delays |
| P4 — Low | Minor UX issues; cosmetic bugs | Next business day | Typo in UI; minor display glitch |

### On-Call Rotation
- Primary on-call: 1-week rotation among Platform Team and DevOps/SRE
- Escalation path: On-call engineer → Team Lead → Engineering Manager
- All P1/P2 incidents require post-incident review within 48 hours
- Runbooks stored in `docs/runbooks/` and linked from Grafana alerts

### Academic Calendar Blackout Periods
During the following periods, no non-critical deployments or maintenance windows:
- Exam week (last 2 weeks of each semester)
- First day of course registration (peak concurrent users)
- Fee payment deadline week
- Graduation day

---

## 9. Operational Policy Addendum

### Academic Data Integrity Policies
- Grades once published (locked) can only be changed through a formal grade appeal process requiring department head approval and audit log entry.
- Student academic records (grades, transcripts, enrollment history) are immutable once the semester is closed; amendments require a formal exception workflow.
- All grade submissions must be idempotent; re-submitting the same grade data must not create duplicate records.
- GPA recalculation runs automatically on grade publication and is triggered by any grade amendment.

### Student Data Privacy Policies
- Student PII (name, ID, contact, academic records) is accessible only to authorized roles; parents of minor students may access limited information via the parent portal.
- Adult students (18+) must explicitly consent to parent portal access; consent is recorded with timestamp.
- Bulk exports of student data require admin authorization and are logged to the audit trail.
- Student data is retained for the duration required by the institution's data retention policy (typically 7–10 years after graduation).

### Fee Collection Policies
- Fee invoices are generated automatically at the start of each semester based on the fee structure active at enrollment time.
- Fee structure changes do not retroactively affect existing invoices for the current semester.
- Late fee penalties are applied automatically after the due date; penalty waiver requires finance officer authorization.
- All payment transactions are idempotent; a payment confirmation from the gateway is the sole authoritative record.

### System Availability Policies
- Planned maintenance windows must be announced 48 hours in advance via CMS announcement and in-app notification.
- No maintenance windows during academic blackout periods (exam week, registration day, fee deadline, graduation).
- During partial outages, the system enters read-only mode: portals remain accessible but write operations are queued.
- Recovery from any outage requires data consistency checks before resuming write operations.
