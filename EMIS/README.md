# Education Management Information System (EMIS) — Complete Design Documentation

> A comprehensive, Django-powered platform for managing the full student lifecycle — from admissions and enrollment through academics, assessments, finance, and graduation — across 35 integrated modules.

## Documentation Structure

```
EMIS/
├── requirements/
│   ├── requirements-document.md      # Functional and non-functional requirements
│   └── user-stories.md               # Role-based user stories (9 actor types)
│
├── analysis/
│   ├── use-case-diagram.md           # UML use case diagram
│   ├── use-case-descriptions.md      # Detailed use case specifications
│   ├── activity-diagram.md           # Activity and flow diagrams
│   ├── bpmn-swimlane-diagram.md      # BPMN process flows
│   ├── system-context-diagram.md     # System context (C4 Level 1)
│   ├── business-rules.md             # Core business rules across all domains
│   ├── data-dictionary.md            # Canonical data dictionary
│   └── event-catalog.md              # Domain event catalog
│
├── high-level-design/
│   ├── architecture-diagram.md       # System architecture overview
│   ├── c4-context-container.md       # C4 Level 1 and Level 2 diagrams
│   ├── data-flow-diagram.md          # Data flow and integration topology
│   ├── domain-model.md               # Bounded context and domain model
│   └── system-sequence-diagram.md    # System-level sequence diagrams
│
├── detailed-design/
│   ├── erd-database-schema.md        # Entity-relationship diagram and schema
│   ├── class-diagram.md              # UML class diagrams (5 domains)
│   ├── sequence-diagram.md           # Request-level sequence diagrams (20 modules)
│   ├── state-machine-diagram.md      # State machines for lifecycle objects
│   ├── component-diagram.md          # Component-level decomposition
│   ├── c4-component.md               # C4 Level 3 component diagrams
│   └── api-design.md                 # Complete REST API reference
│
├── infrastructure/
│   ├── deployment-diagram.md         # ECS Fargate deployment topology
│   ├── cloud-architecture.md         # AWS services, RDS, ElastiCache, S3, SES
│   └── network-infrastructure.md     # VPC, subnets, security groups, DNS, TLS
│
├── edge-cases/
│   ├── README.md                     # Edge case index and methodology
│   ├── academic-operations.md        # EC-ACAD-001 to EC-ACAD-010
│   ├── enrollment-and-registration.md # EC-ENROLL-001 to EC-ENROLL-010
│   ├── finance-and-payments.md       # EC-FIN-001 to EC-FIN-010
│   ├── notifications.md              # EC-NOTIF-001 to EC-NOTIF-008
│   ├── security-and-compliance.md    # EC-SEC-001 to EC-SEC-008
│   ├── api-and-ui.md                 # EC-API-001 to EC-API-007
│   └── operations.md                 # EC-OPS-001 to EC-OPS-008
│
└── implementation/
    ├── implementation-playbook.md    # Sprint-by-sprint delivery roadmap
    ├── code-guidelines.md            # 4-layer architecture, coding standards
    └── c4-code-diagram.md            # C4 Level 4: runtime code-level diagrams
```

## Key Features

- **35 integrated Django apps** covering students, admissions, courses, exams, attendance, timetable, LMS, finance, library, HR, hostel, transport, inventory, analytics, notifications, CMS, graduation, academic standing, discipline, grade appeals, recruitment, department administration, room management, transfer credits, scholarships, and more
- **API-first design** with Django REST Framework, JWT authentication, and comprehensive endpoint coverage
- **Event-driven architecture** using Redis Pub/Sub and Celery for asynchronous workflows and multi-channel notifications
- **Multi-channel notifications** via email (AWS SES), SMS (Twilio), mobile push (FCM), and in-app
- **Payment gateway integration** with Razorpay and Stripe, including webhook handling, idempotency, and automated refunds
- **Plagiarism detection** via Turnitin API integration in the LMS assignment workflow
- **Role-based access control** with 10 actor roles, MFA enforcement, and comprehensive audit logging
- **Production-grade AWS infrastructure** on ECS Fargate, RDS PostgreSQL 15, ElastiCache Redis 7, CloudFront, and WAF

## Primary Roles

| Role | Primary Responsibilities |
|---|---|
| Super Admin | System configuration, override controls, audit access |
| Admin / Registrar | Student records, program management, calendar, reporting |
| Faculty | Course delivery, grade submission, attendance, LMS content |
| Student | Registration, enrollment, assignment submission, fee payment |
| Parent | Read-only portal access to linked student's academic and fee records |
| Finance Staff | Invoice generation, payment reconciliation, refunds, scholarships |
| HR Staff | Faculty/staff onboarding, leave management, payroll data |
| Library Staff | Book issue/return, fine collection, catalog management |
| Hostel Warden | Room allocation, occupancy management |
| Transport Manager | Route and bus seat management |
| Department Head | Program administration, curriculum review, academic standing oversight |
| Scholarship Committee | Scholarship evaluation, award approval, fund management |
| Facilities Manager | Room configuration, facility booking, maintenance coordination |
| Alumni | Transcript requests, degree verification, alumni communications |

## Getting Started

1. Start with `requirements/requirements-document.md` to understand scope and constraints
2. Review `analysis/use-case-descriptions.md` for actor-level workflows
3. Study `high-level-design/architecture-diagram.md` for the overall system topology
4. Explore `detailed-design/erd-database-schema.md` for the data model
5. Implement APIs from `detailed-design/api-design.md`
6. Validate the deployment via `infrastructure/cloud-architecture.md`
7. Execute delivery using `implementation/implementation-playbook.md`

## Documentation Status

- ✅ Requirements complete
- ✅ Analysis complete
- ✅ High-level design complete
- ✅ Detailed design complete
- ✅ Infrastructure complete
- ✅ Edge cases complete
- ✅ Implementation complete

### New Module Documentation
- ✅ Academic Session & Semester Management
- ✅ Graduation & Degree Conferral
- ✅ Student Discipline & Conduct
- ✅ Academic Standing & Progress
- ✅ Grade Dispute & Appeal
- ✅ Faculty Recruitment & Onboarding
- ✅ Department & Program Administration
- ✅ Room & Facility Management
- ✅ Transfer Credits & Course Equivalency
- ✅ Scholarship & Financial Aid

## Delivery Blueprint

| Phase | Focus | Key Outputs |
|---|---|---|
| Phase 1 | Core Platform | User auth, student records, program/course management |
| Phase 2 | Academic Operations | Enrollment, timetable, attendance, exam scheduling |
| Phase 3 | Assessment and LMS | Grade submission, GPA engine, LMS content and assignments |
| Phase 4 | Finance and Payments | Invoice generation, gateway integration, scholarships, refunds |
| Phase 5 | Support Services | Library, HR, hostel, transport, inventory |
| Phase 6 | Analytics and Portal | Reports, dashboards, CMS, SEO, calendar |
| Phase 7 | Hardening | Edge case mitigations, security audit, load testing, DR validation |
| Phase 8 | Graduation & Progress | Degree audits, academic standing, transfer credits, grade appeals |
| Phase 9 | HR & Recruitment | Faculty recruitment, onboarding, department administration |
| Phase 10 | Facilities & Scheduling | Room booking, facility management, maintenance tracking |
| Phase 11 | Scholarship & Aid | Aid applications, eligibility evaluation, disbursement, stacking rules |
| Phase 12 | Discipline & Conduct | Conduct tracking, disciplinary hearings, sanctions, appeal processing |

## Operational Policy Addendum

### Academic Integrity Policies
Grade amendments require dual approval (faculty + HOD) and are permanently logged in the audit trail with old/new values, actor identity, IP address, and reason code. No grade may be amended more than 60 days after semester end without SUPER_ADMIN override. Every such override triggers an automated notification to the Academic Standards Committee. All prerequisite enforcement, attendance thresholds, and academic hold rules are enforced at the service layer and cannot be bypassed by client-side manipulation.

### Student Data Privacy Policies
Student personally identifiable information (PII) is classified as Sensitive Personal Data under PDPA and FERPA. Access is strictly role-gated: PARENT role can only view data for linked students who have granted explicit, revocable consent. Faculty can only query grade and attendance data within their assigned sections. All data access is audited. PII is never included in aggregate analytics without pseudonymisation. Data is retained for 10 years post-graduation and deleted after 15 years in accordance with institutional records policy.

### Fee Collection Policies
Academic holds (blocking enrollment) are applied only for overdue invoices beyond a 7-calendar-day grace period. Holds cannot be applied during an active exam period. All fee waivers, scholarship applications, and invoice adjustments require Finance Staff or Admin approval and are permanently logged. A maximum late-fee cap is configured per program. Refunds of more than INR 10,000 require Finance Staff review before gateway processing.

### System Availability During Academic Calendar
EMIS is classified as Mission-Critical during `REGISTRATION_WINDOW`, `EXAM_PERIOD`, `GRADE_SUBMISSION_WINDOW`, and `MERIT_LIST_DATE` calendar events. No planned maintenance windows are scheduled during these periods. Emergency maintenance requires explicit sign-off from the Registrar and CTO. ECS task counts are pre-scaled before each registration window to handle peak concurrency. A deployment freeze is in effect during all Mission-Critical calendar windows; only emergency security patches may be deployed with three-way approval.

### Graduation & Academic Standing Policies
Degree conferral requires successful completion of a degree audit confirming all program requirements are met, including minimum GPA, total credit hours, and mandatory course completion. Academic standing is evaluated automatically at the end of each semester based on cumulative GPA thresholds: Good Standing (≥ 2.0), Academic Probation (1.5–1.99), and Academic Dismissal (< 1.5 for two consecutive semesters). Transfer credits are evaluated by the Registrar and require a minimum grade of C (2.0) at the originating institution. All standing changes and graduation decisions are permanently logged in the audit trail.

### Recruitment & Onboarding Policies
Faculty recruitment postings require Department Head approval before publication. All applications are tracked through a standardized pipeline: Received → Screening → Shortlisted → Interview → Offer → Accepted/Rejected. Interview panels must include at least one member from outside the hiring department. Onboarding checklists are auto-generated based on position type and must be completed within 30 days of hire date. System access is provisioned only after all mandatory onboarding tasks (background verification, policy acknowledgment, IT orientation) are marked complete.
