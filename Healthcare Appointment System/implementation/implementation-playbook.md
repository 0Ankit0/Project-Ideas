# Implementation Playbook

> **Version:** 2.0 | **Status:** Active | **Owner:** Engineering Leadership  
> **Scope:** End-to-end delivery of the Healthcare Appointment System from project kickoff through production go-live and steady-state operations.

---

## 1. Delivery Goal

Build and launch a production-ready **Healthcare Appointment System** that is secure, observable, and operationally resilient. The system must support real-time slot booking, provider schedule management, automated patient notifications, billing integration, and compliance with HIPAA/regional data-privacy regulations. Every phase ships working, tested software with clear rollback paths.

---

## 2. Tech Stack Decisions

### Rationale Matrix

| Layer | Technology | Rationale |
|---|---|---|
| **Runtime** | Node.js 20 LTS + TypeScript 5 | Async I/O fits high-concurrency scheduling; strict typing enforces domain model correctness at compile time |
| **Framework** | NestJS | Opinionated module system enforces clean-architecture boundaries; first-class DI, interceptors, guards, and pipes reduce boilerplate for RBAC, validation, and logging |
| **ORM / Migrations** | Prisma | Type-safe schema-first ORM; migration history is version-controlled and CI-validated; generated client eliminates raw SQL in application code |
| **Primary Database** | PostgreSQL 16 | ACID transactions critical for slot reservation; row-level locking, advisory locks, and JSONB for audit payloads; strong ecosystem for healthcare workloads |
| **Event Streaming** | Apache Kafka | Durable, replayable event log for appointment lifecycle events; supports exactly-once semantics for billing and notification consumers |
| **Cache / Session** | Redis 7 (Cluster) | Sub-millisecond slot-availability reads; distributed locks for idempotent slot reservation; session store for SSO tokens |
| **Container Orchestration** | Kubernetes (EKS/GKE) | Horizontal pod autoscaling for booking spikes; rolling update and canary strategies; namespace isolation for multi-tenant workloads |
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, JWT validation, and mTLS termination at the edge before traffic reaches services |
| **Observability** | OpenTelemetry + Grafana Stack | Vendor-neutral trace/metric/log collection; Tempo for traces, Loki for logs, Prometheus + Grafana for dashboards |
| **Secret Management** | HashiCorp Vault / AWS Secrets Manager | Dynamic credentials, automatic rotation, audit log for all secret access |
| **CI/CD** | GitHub Actions + ArgoCD | Pull-request gates enforce test and security scan thresholds; ArgoCD GitOps reconciles cluster state declaratively |

---

## 3. Team Structure

### Platform Team (4–5 engineers)
- Owns infrastructure-as-code, Kubernetes cluster configuration, CI/CD pipelines, and shared libraries (logging, auth, event bus clients).
- Defines and enforces architectural standards and security baselines.
- Runs weekly architecture office hours and reviews cross-cutting changes.

### Feature Team — Scheduling (3–4 engineers)
- Owns the Scheduling Service: slot management, provider calendars, conflict resolution, and optimistic locking.
- Collaborates with the Patient team on booking UX contracts.

### Feature Team — Patient (3–4 engineers)
- Owns the Patient Service: registration, identity linking, appointment history, and patient-facing APIs.
- Drives frontend integration contracts and accessibility compliance.

### Feature Team — Billing (2–3 engineers)
- Owns the Billing Service: insurance verification, co-pay capture, claim submission, and payment reconciliation.
- Coordinates with external clearinghouse and EHR integrations.

### Feature Team — Notifications (2–3 engineers)
- Owns the Notification Orchestrator: template management, channel routing, delivery tracking, and retry logic.
- Maintains consent registry integration and TCPA/GDPR compliance controls.

### DevOps / SRE Team (2–3 engineers)
- Owns production reliability, incident response, runbooks, SLO/SLI definitions, and capacity planning.
- Runs quarterly game days and chaos engineering exercises.

---

## 4. CI/CD Pipeline

### Pipeline Stages and Gates

```
┌──────────────────────────────────────────────────────────────────┐
│  PR / Push Trigger                                               │
│                                                                  │
│  1. LINT & TYPE CHECK                                            │
│     • eslint --max-warnings 0                                    │
│     • tsc --noEmit                                               │
│     Gate: zero lint errors, zero type errors                     │
│                                                                  │
│  2. UNIT TESTS                                                   │
│     • jest --coverage --coverageThreshold global:80              │
│     Gate: ≥80% line/branch coverage; zero test failures          │
│                                                                  │
│  3. INTEGRATION TESTS                                            │
│     • Docker Compose: postgres + redis + kafka test containers   │
│     • jest --testPathPattern=integration                         │
│     Gate: all integration tests pass                             │
│                                                                  │
│  4. CONTRACT TESTS                                               │
│     • Pact provider/consumer verification                        │
│     Gate: all Pact contracts verified against broker             │
│                                                                  │
│  5. SECURITY SCAN                                                │
│     • npm audit --audit-level=high                               │
│     • Snyk container scan on Docker image                        │
│     • Semgrep SAST scan (OWASP ruleset)                          │
│     Gate: zero high/critical CVEs; zero SAST blocking findings   │
│                                                                  │
│  6. BUILD & PUSH IMAGE                                           │
│     • docker buildx build --platform linux/amd64,linux/arm64    │
│     • Push to ECR/GCR with SHA tag + environment tag            │
│     Gate: successful multi-arch build                            │
│                                                                  │
│  7. DEPLOY TO STAGING (ArgoCD sync)                              │
│     • Helm chart values updated with new image tag               │
│     • ArgoCD syncs; health checks pass                           │
│     Gate: all pods healthy; smoke tests pass                     │
│                                                                  │
│  8. E2E TESTS (staging)                                          │
│     • Playwright critical-path suite (booking, check-in, cancel) │
│     Gate: all E2E tests pass                                     │
│                                                                  │
│  9. PERFORMANCE GATE (main branch only)                          │
│     • k6 smoke load: 200 VUs / 2 min                            │
│     Gate: p99 booking latency < 500ms; error rate < 0.1%        │
│                                                                  │
│  10. PROMOTE TO PRODUCTION (manual approval for releases)        │
│      • Canary or blue-green rollout via ArgoCD Rollouts          │
└──────────────────────────────────────────────────────────────────┘
```

### Branch Strategy
- `main` → production; protected; requires 2 approvals + all gates green.
- `staging` → staging environment; auto-deploys on merge.
- `feature/*` → developer branches; PR targets `main`; CI runs on push.
- Release tags follow SemVer (`v1.2.3`); tags trigger production promotion pipeline.

---

## 5. Deployment and Rollout Strategy

### Canary Deployment (default for service updates)
1. ArgoCD Rollouts deploys new version to 5% of pods.
2. Automated analysis monitors error rate, latency p99, and booking success rate for 10 minutes.
3. If all metrics pass thresholds, traffic weight shifts: 5% → 25% → 50% → 100% at 10-minute intervals.
4. If any metric breaches threshold at any step, automated rollback returns 100% traffic to the stable version within 30 seconds.

### Blue-Green Deployment (for schema migrations and breaking changes)
1. Provision the "green" environment with the new version; run database migration against a shadow schema.
2. Execute full regression suite against green.
3. Switch load balancer to green in a single atomic step.
4. Keep blue running for 30 minutes as a hot-standby rollback target.
5. Decommission blue after confirmed stability.

### Feature Flags
- All major user-facing features are gated by LaunchDarkly / Unleash flags.
- Flags allow gradual patient/provider rollout (by tenant, geography, or percentage).
- Kill switches are available for every Kafka consumer and external integration.
- Flag state is audited and tied to release documentation.

### Rollback Procedures by Phase

| Phase | Rollback Trigger | Procedure | RTO Target |
|---|---|---|---|
| Phase 1 | Foundation service crash / failed health checks | `kubectl rollout undo deployment/<service>` | < 5 min |
| Phase 2 | Booking error rate > 1% sustained 5 min | ArgoCD automated rollback via Rollout analysis | < 2 min |
| Phase 3 | Notification delivery failure > 10% | Feature flag kill switch + manual Kafka consumer pause | < 3 min |
| Phase 4 | Production SLO breach | Blue-green switch back to previous stable environment | < 2 min |

---

## 6. Phase 1 — Foundation (Weeks 1–4)

### Objective
Establish the platform skeleton: repository structure, CI/CD pipelines, database schema, authentication, and core domain models. No user-facing features ship in this phase — only verified infrastructure that all subsequent phases build on.

### Deliverables

| # | Deliverable | Owner | Definition of Done |
|---|---|---|---|
| 1.1 | Mono-repo scaffold (NestJS workspaces, shared libs) | Platform | `pnpm install && pnpm build` succeeds; no circular dependencies |
| 1.2 | PostgreSQL schema v1 (patients, providers, slots, appointments) | Platform | Migration runs cleanly; rollback migration tested |
| 1.3 | Redis cluster config + connection pool | Platform | Health check endpoint returns Redis status; pool metrics exported |
| 1.4 | Kafka topics + consumer groups defined | Platform | Topics created with correct replication factor and retention; consumer lag metric visible |
| 1.5 | Authentication service (JWT + OAuth2 PKCE) | Platform | Token issuance, refresh, and revocation tested; MFA flow implemented |
| 1.6 | RBAC middleware (Patient, Provider, Staff, Admin, SRE roles) | Platform | Role-based route guards pass all permission matrix tests |
| 1.7 | CI/CD pipeline (lint, test, scan, build, deploy to staging) | DevOps | Full pipeline runs < 12 min; all gates enforced |
| 1.8 | Kubernetes manifests + Helm charts for all services | DevOps | `helm install` succeeds in a clean namespace; pods reach Running state |
| 1.9 | Structured logging + distributed tracing baseline | Platform | Every request emits trace_id, correlation_id, service_name in JSON |
| 1.10 | Developer environment (docker-compose, seed scripts) | Platform | `docker compose up` reaches healthy state in < 3 min on clean machine |

### Dependencies
- Cloud provider account with VPC, IAM, and ECR/GCR configured.
- Domain name and TLS certificates provisioned.
- Secrets manager instance with team access policies.
- Architecture Decision Records (ADRs) approved for database, event bus, and auth.

### Testing Approach
- Unit tests for all domain value objects and entity factories (≥90% coverage).
- Integration tests for all repository implementations using Testcontainers (PostgreSQL + Redis).
- Security scan baseline established; all findings triaged before phase close.
- CI pipeline itself tested by intentionally failing each gate and verifying block behavior.

### Exit Criteria
- [ ] All 10 deliverables marked Done.
- [ ] CI pipeline fully operational with all 9 gates passing on `main`.
- [ ] Developer onboarding runbook tested by at least one new team member.
- [ ] No open critical or high security findings.
- [ ] Phase 1 retrospective held; action items logged.

---

## 7. Phase 2 — Core Features (Weeks 5–10)

### Objective
Deliver the primary booking flow end-to-end: patients can search for available slots, book an appointment, receive a confirmation, and cancel or reschedule. Providers can manage their calendars. This phase is the first shippable increment.

### Deliverables

| # | Deliverable | Owner | Definition of Done |
|---|---|---|---|
| 2.1 | Slot availability API (search by specialty, date range, location) | Scheduling | p99 < 200ms under 500 concurrent users; cache-hit rate > 80% |
| 2.2 | Appointment booking command with optimistic locking + idempotency | Scheduling | Double-booking impossible under concurrent load test; idempotent retries safe |
| 2.3 | Appointment cancellation and reschedule flows | Scheduling | State machine transitions tested; downstream events published correctly |
| 2.4 | Provider calendar management (block, unblock, leave) | Scheduling | Calendar changes trigger revalidation of affected bookings |
| 2.5 | Patient registration and profile API | Patient | PII fields encrypted at rest; GDPR data export endpoint functional |
| 2.6 | Appointment history and status API for patients | Patient | Pagination, filtering, and audit trail accessible |
| 2.7 | Confirmation and reminder notifications (email + in-app) | Notifications | Delivery tracked; retry logic verified with failure simulation |
| 2.8 | Basic admin dashboard APIs (slot utilization, booking counts) | Platform | Metrics consistent with source-of-truth database counts |
| 2.9 | API contract tests (Pact) for all public endpoints | Platform | Pact broker populated; all consumer/provider tests green |
| 2.10 | OpenAPI spec auto-generated and published to developer portal | Platform | Spec passes lint; breaking-change detection integrated in CI |

### Dependencies
- Phase 1 exit criteria met.
- UX wireframes approved for patient booking flow and provider calendar.
- Notification template copy reviewed and approved by clinical communications team.
- EHR sandbox credentials available for provider directory sync.

### Testing Approach
- Unit tests for all booking and cancellation command handlers (≥85% branch coverage).
- Integration tests for the full booking transaction: slot lock → appointment create → event publish → notification enqueue.
- Concurrency tests: 50 simultaneous booking requests for the same slot — exactly one succeeds.
- Contract tests for all API consumers.
- Manual exploratory testing of booking and cancellation UX flows.

### Exit Criteria
- [ ] All 10 deliverables marked Done.
- [ ] End-to-end booking and cancellation flow demonstrated in staging with real patient and provider data.
- [ ] Zero P1/P2 bugs open.
- [ ] Performance gate: booking API p99 < 300ms at 200 concurrent users.
- [ ] Notification delivery rate ≥ 98% in staging over a 48-hour window.
- [ ] Phase 2 demo delivered to stakeholders.

---

## 8. Phase 3 — Advanced Features (Weeks 11–16)

### Objective
Extend the platform with billing integration, SMS notifications, advanced provider matching (multi-specialty, telehealth), waitlist management, check-in workflows, and EHR data exchange. The system reaches feature parity with the product specification.

### Deliverables

| # | Deliverable | Owner | Definition of Done |
|---|---|---|---|
| 3.1 | Billing service: insurance eligibility verification | Billing | Real-time eligibility check < 4 s; fallback to cached result on timeout |
| 3.2 | Billing service: co-pay capture and payment processing | Billing | PCI-DSS compliant tokenization; no raw card data in logs or DB |
| 3.3 | Claim submission to clearinghouse (HL7/X12) | Billing | Round-trip test with clearinghouse sandbox; acknowledgment parsed |
| 3.4 | SMS notifications with consent registry | Notifications | TCPA opt-in/opt-out respected; consent history auditable |
| 3.5 | Waitlist management (join, promote, expire) | Scheduling | Automatic promotion tested end-to-end; SLA for promotion < 5 min after slot opens |
| 3.6 | Multi-provider / multi-location search and matching | Scheduling | Relevance scoring documented and tested; results consistent |
| 3.7 | Telehealth appointment type with video link generation | Scheduling | Video link delivered in confirmation; link valid for appointment window only |
| 3.8 | Patient check-in workflow (QR code, kiosk, mobile) | Patient | Check-in state machine tested; EHR encounter updated on check-in |
| 3.9 | EHR integration: patient demographics sync and appointment write-back | Platform | HL7 FHIR R4 resources validated; sync idempotent on replay |
| 3.10 | Reporting API: utilization, no-show rate, revenue cycle metrics | Platform | Reports match warehouse data within 1% tolerance |

### Dependencies
- Phase 2 exit criteria met.
- Clearinghouse API credentials and test environment access.
- SMS provider account (Twilio/AWS SNS) with short code or toll-free number approved.
- FHIR server endpoint and OAuth2 credentials for EHR integration.
- PCI-DSS scoping review completed by security team.

### Testing Approach
- Billing unit tests: eligibility response parsing, claim serialization, error code mapping.
- Integration tests for billing against clearinghouse sandbox (contract-verified responses).
- FHIR integration tests using synthetic patient data that mirrors production structure.
- Waitlist promotion load test: 1,000 waitlist entries, slot opens, verify promotion cascade.
- End-to-end telehealth booking: book → receive link → join call (stub) → complete → write-back.
- Security penetration test covering billing endpoints and PHI export APIs.

### Exit Criteria
- [ ] All 10 deliverables marked Done.
- [ ] Billing integration tested with clearinghouse sandbox; claim acceptance rate > 95%.
- [ ] EHR write-back verified with FHIR validator (zero schema errors).
- [ ] Penetration test report reviewed; all critical findings remediated.
- [ ] SMS delivery rate ≥ 97% in staging; consent controls verified by compliance team.
- [ ] Phase 3 sign-off from clinical operations and compliance officer.

---

## 9. Phase 4 — Production Hardening (Weeks 17–20)

### Objective
Validate production readiness: load testing at peak capacity, chaos engineering, security audit, backup and recovery drills, SLO definition and alerting, runbook completion, and a formal go-live rehearsal. No new features — only hardening, tuning, and operational verification.

### Deliverables

| # | Deliverable | Owner | Definition of Done |
|---|---|---|---|
| 4.1 | Load test at 2× projected peak (1,000 concurrent bookings) | DevOps/SRE | p99 booking < 500ms; error rate < 0.1%; no resource exhaustion |
| 4.2 | Chaos engineering: pod kill, network partition, DB failover | DevOps/SRE | System recovers automatically within SLO; no data loss observed |
| 4.3 | Full security audit (OWASP Top 10, HIPAA Technical Safeguards) | Security | All critical/high findings remediated; medium findings have mitigations |
| 4.4 | Backup and restore drill (RTO ≤ 1 h, RPO ≤ 15 min) | DevOps/SRE | Restore completed and verified within documented RTO/RPO |
| 4.5 | SLO/SLI definitions and alerting rules deployed | DevOps/SRE | Alerts fire correctly in staging; PagerDuty routing tested |
| 4.6 | Runbooks for all Tier-1 incidents | DevOps/SRE | Each runbook walked through by on-call rotation; feedback incorporated |
| 4.7 | Data migration plan and dry-run (legacy → new system) | Platform | Dry-run completes without data loss; reconciliation report clean |
| 4.8 | HIPAA compliance review and BAA execution | Compliance | BAA signed with all sub-processors; audit log reviewed by compliance |
| 4.9 | Monitoring dashboards: booking funnel, error rates, SLOs | DevOps/SRE | Dashboards reviewed and approved by engineering leads |
| 4.10 | Go-live rehearsal (full cutover simulation in staging) | All teams | Rehearsal completes within the maintenance window; rollback tested |

### Dependencies
- Phase 3 exit criteria met and sign-off received.
- Production infrastructure provisioned and load-tested independently.
- Legacy data extract available for migration dry-run.
- External auditor engaged for HIPAA technical safeguards review.
- Maintenance window agreed with clinical operations (typically Sunday 02:00–06:00 local).

### Testing Approach
- **Load testing:** k6 scripts simulate booking, search, cancellation, and check-in at 2× peak for 30 minutes. Metrics exported to Grafana in real time.
- **Chaos testing:** Chaos Monkey / Chaos Toolkit scenarios: pod termination, CPU spike, network latency injection, Kafka broker restart, Redis eviction.
- **Backup drill:** Automated daily snapshot restore to an isolated RDS/Cloud SQL instance; application smoke tests confirm data integrity.
- **Security regression:** Automated DAST scan (OWASP ZAP) against staging; manual review of results.
- **Accessibility:** Automated axe-core scan + manual screen reader walkthrough of patient booking flow.

### Exit Criteria
- [ ] All 10 deliverables marked Done.
- [ ] Load test passed at 2× peak with no SLO breaches.
- [ ] Chaos recovery verified for all tested failure modes.
- [ ] Security audit closed with zero open critical or high findings.
- [ ] HIPAA compliance sign-off received from compliance officer.
- [ ] Go-live rehearsal completed within maintenance window; rollback drill successful.

---

## 10. Go-Live Checklist

> Complete all items before flipping the production traffic switch. Each item requires a named owner sign-off.

### Infrastructure and Deployment
- [ ] Production VPC, subnets, and security groups reviewed by security team
- [ ] TLS certificates installed and auto-renewal configured (cert-manager)
- [ ] DNS records (A/CNAME, health-check endpoints) verified
- [ ] Kubernetes cluster autoscaler enabled and tested
- [ ] HorizontalPodAutoscaler policies set for all services (min/max replicas defined)
- [ ] PodDisruptionBudgets configured for zero-downtime rolling updates
- [ ] Secrets rotation schedule activated in Vault / Secrets Manager

### Data and Database
- [ ] Production database provisioned with Multi-AZ failover enabled
- [ ] Read replica deployed and lag monitoring active
- [ ] Schema migrations applied and verified on production schema (not yet live data)
- [ ] Database connection pool limits tuned per service load test data
- [ ] PITR (point-in-time recovery) enabled; backup retention set to 35 days
- [ ] Data migration dry-run reconciliation report reviewed and signed off

### Security and Compliance
- [ ] HIPAA BAA signed with all cloud sub-processors
- [ ] RBAC roles and permission matrix verified in production IAM
- [ ] MFA enforced for all admin, SRE, and privileged support roles
- [ ] Audit logging active for all PHI create/read/update/export operations
- [ ] Penetration test report reviewed; all critical/high findings closed
- [ ] Vulnerability scan on production container images — zero high/critical CVEs
- [ ] API rate limiting and WAF rules active

### Observability
- [ ] All services emitting structured JSON logs to centralized log aggregator
- [ ] Distributed tracing sampling rate set (100% errors, 10% success)
- [ ] SLO dashboards deployed with 30-day burn rate alerts
- [ ] PagerDuty escalation policies configured and tested with a live alert
- [ ] Synthetic monitors (Grafana Synthetic / Checkly) running booking and availability checks every 60 s

### Operational Readiness
- [ ] Runbooks for top-10 incident scenarios reviewed and accessible
- [ ] On-call rotation schedule published; all engineers have completed on-call onboarding
- [ ] Rollback procedure rehearsed and documented with timing benchmarks
- [ ] Feature flags reviewed; all Phase 4 launch flags set to intended initial state
- [ ] Communication plan approved: patient notification copy, status page template, escalation contacts
- [ ] Clinic staff training completed; downtime SOP printed and distributed
- [ ] Hypercare schedule (24/7 on-call coverage for first 7 days post-launch) confirmed

---

## 11. Post-Launch Monitoring Plan

### Week 1 (Hypercare)
- 24/7 on-call coverage with 30-minute response SLA for any alert.
- Daily standup with SRE, feature team leads, and clinical operations representative.
- Booking funnel dashboard reviewed every 4 hours.
- Manually verify 5% sample of appointment confirmations and notifications.
- Any P1 incident triggers a 48-hour hotfix SLA.

### Weeks 2–4 (Stabilization)
- On-call transitions to standard business-hours primary + 24/7 pager for critical alerts.
- Weekly SLO review: booking success rate, API error rate, notification delivery rate.
- Performance trend analysis: compare week-over-week p95/p99 latencies.
- Review Kafka consumer lag trends; tune partition counts if necessary.
- Database query performance review (slow query log analysis).

### Month 2–3 (Steady State)
- Monthly capacity review: CPU, memory, DB IOPS, Kafka throughput vs. growth projections.
- Quarterly chaos engineering exercise.
- Quarterly backup/restore drill.
- Continuous security scanning: weekly Snyk/Dependabot dependency updates reviewed.
- SLO quarterly review with product and clinical stakeholders.

### Key SLOs

| Service | SLO Metric | Target |
|---|---|---|
| Booking API | Success rate | ≥ 99.5% |
| Booking API | p99 latency | < 500ms |
| Availability Search | p99 latency | < 200ms |
| Notification Delivery | Email delivery rate | ≥ 99% |
| Notification Delivery | SMS delivery rate | ≥ 97% |
| System Availability | Uptime (monthly) | ≥ 99.9% |
| Data Recovery | RPO | ≤ 15 min |
| Data Recovery | RTO | ≤ 1 h |

---

## 12. Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prohibited per provider, location, and time-slot. All slot reservation writes enforce an optimistic concurrency check on `slot_version` plus a per-request `idempotency_key`.
- When two booking requests race for the same slot, the first committed transaction wins. All subsequent requests receive `409 SLOT_ALREADY_BOOKED` with the top three alternative slots.
- Provider calendar changes (leave, overrun, emergency block) trigger an automatic revalidation pass that transitions impacted bookings to `REBOOK_REQUIRED` and initiates patient outreach workflows.
- Unresolved conflicts older than 15 minutes are escalated to operations via PagerDuty for manual intervention and direct patient contact.

### Patient/Provider Workflow States
- Patient appointment lifecycle: `DRAFT → PENDING_CONFIRMATION → CONFIRMED → CHECKED_IN → IN_CONSULTATION → COMPLETED` with terminal branches `CANCELLED`, `NO_SHOW`, and `EXPIRED`.
- Provider schedule lifecycle: `AVAILABLE → RESERVED → LOCKED_FOR_VISIT → RELEASED`; exceptional states include `BLOCKED` (planned unavailability) and `SUSPENDED` (incident or compliance hold).
- Every state transition is event-driven and immutably auditable; each transition record captures actor ID, timestamp, source channel, reason code, and correlation ID.
- Invalid transitions are rejected with deterministic error codes and never mutate downstream billing, notification, or reporting projections.

### Notification Guarantees
- Supported channels: in-app, email, and SMS (when patient consent is on record). Delivery policy is at-least-once; consumers enforce idempotency using message keys.
- Critical events (`CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `REBOOK_REQUIRED`) retry with exponential backoff (base 30 s, max 1 h) for up to 24 hours.
- If all automated retries are exhausted, a `NOTIFICATION_ATTENTION_REQUIRED` task is created for support-assisted outreach.
- Template rendering and localization are version-pinned to the event schema version that triggered the notification, ensuring compliance review consistency.

### Privacy Requirements
- All PHI/PII is encrypted in transit (TLS 1.2+ minimum, TLS 1.3 preferred) and at rest (AES-256 or cloud-provider equivalent with customer-managed keys for regulated tenants).
- Access control follows least-privilege RBAC/ABAC with MFA enforced for privileged roles and just-in-time elevation for production support access.
- Full audit logging covers all create, read, update, and export actions on medical or billing data, including actor identity, purpose classification, and source IP.
- Data minimization is mandatory for notification payloads, analytics exports, and non-production datasets; retention schedules are enforced by automated TTL policies.
- All integrations must use signed requests, scoped service-account credentials, and a defined key-rotation schedule. Sandbox and test environments must use fully de-identified data.

### Downtime Fallback Procedures
- During partial outages, the system enters degraded mode: read-only schedule and appointment views remain available while write commands are queued with durable ordering guarantees.
- Clinics maintain a printable/offline daily roster and manual check-in sheet generated at the start of each day. Staff continue visits using downtime SOPs and reconcile once service is restored.
- Recovery pipeline replays queued commands in order, revalidates all slot conflicts, and dispatches reconciliation notifications for any appointments affected during the outage window.
- Incident closure criteria: successful backlog drain verified, data consistency checks pass, post-incident review completed, and affected patients and providers notified of any changes within 2 hours of resolution.

