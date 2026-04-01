# Hotel Property Management System — Implementation Playbook

## Guiding Principles

The HPMS implementation follows a set of non-negotiable principles that govern every sprint, every pull request, and every architectural decision from day one to go-live.

1. **Working software over comprehensive planning.** Each sprint delivers a deployable, tested increment. No sprint ends with "backend done, frontend pending" — features are vertical slices that cut through all layers.
2. **Observability from day one.** OpenTelemetry, structured logging, and metrics are instrumented in Sprint 1 before any business logic. A feature that cannot be observed in production is not done.
3. **Test-first on domain logic.** Unit tests for aggregate methods are written before implementation (TDD). Integration tests for repositories are written alongside the repository code, not deferred to a QA phase.
4. **Security is not a phase.** RBAC, JWT validation, property-level data isolation, and input validation are implemented in the first sprint and maintained throughout. Security is not an activity after feature development.
5. **Infrastructure as Code exclusively.** No manual AWS console changes. All infrastructure is Terraform-managed. Changes to infrastructure go through the same pull request review process as application code.
6. **Feature flags for risk.** Any feature with operational risk (OTA integration, payment capture, night audit) is deployed behind a feature flag (LaunchDarkly) and activated incrementally per property.
7. **Incremental database migrations.** Flyway migrations are additive only (no destructive DDL in production). Column renames and table restructures are executed over two releases: add new, backfill, switch, then drop old.

---

## Team Structure

| Role                      | Count | Responsibilities                                                      |
|---------------------------|-------|-----------------------------------------------------------------------|
| Engineering Manager       | 1     | Sprint planning, stakeholder comms, risk escalation                   |
| Backend Engineers (Java)  | 3     | ReservationService, FolioService, LoyaltyService, RoomService         |
| Backend Engineers (Go)    | 1     | ChannelManagerService, KeycardService                                 |
| Backend Engineers (Node)  | 1     | HousekeepingService, NotificationService                              |
| Backend Engineers (Python)| 1     | RevenueService, NightAuditProcessor                                   |
| Frontend Engineers        | 2     | React Web App (all features), React Native Mobile App                 |
| Platform / DevOps         | 1     | Terraform, EKS, CI/CD, ArgoCD, observability stack                   |
| QA Engineer               | 1     | E2E tests, contract tests, exploratory testing, performance testing   |
| Product Owner             | 1     | Backlog, acceptance criteria, stakeholder demos                       |

Sprint cadence: 2 weeks. Sprint ceremonies: planning (4h), daily standup (15m), mid-sprint sync (1h), review + retrospective (3h). Definition of Done: feature implemented + unit tests passing + integration tests passing + code reviewed + deployed to staging + product owner accepted.

---

## Phase 1 — Reservations and Rooms (Sprints 1–4)

### Duration
4 sprints × 2 weeks = 8 weeks.

### Objectives
Establish the foundational data model, property and room management, and the core reservation lifecycle (create, modify, cancel, and availability search). Deliver a working Web UI that hotel staff can use to make reservations. Prove the multi-property data isolation model end-to-end.

### Sprint Breakdown

**Sprint 1 — Infrastructure and Foundation**

Deliverables:
- AWS environment provisioning via Terraform: VPC, EKS cluster (3 AZs), RDS PostgreSQL (Multi-AZ), ElastiCache Redis (cluster mode), MSK Kafka, S3 buckets, Secrets Manager, KMS keys.
- GitHub Actions CI pipeline: build, unit test, integration test (TestContainers), Docker image build, push to ECR, deploy to dev environment.
- ArgoCD setup: dev, staging, and production application definitions.
- Kong API Gateway deployed with JWT validation plugin.
- Istio service mesh installed with mTLS enabled between all namespaces.
- IdentityService: OAuth2/OIDC compliant (Keycloak), JWT issuance, property scope claims.
- Flyway migration framework configured with baseline migration for all Phase 1 schemas.
- OpenTelemetry Collector DaemonSet: traces → Grafana Tempo, metrics → Prometheus, logs → Loki.
- Base monitoring dashboards in Grafana: service health, error rates, latency.
- Alerting rules in Prometheus: error rate, database connections, Kafka consumer lag.

Acceptance Criteria:
- `GET /health/ready` returns 200 on all deployed services.
- A JWT from IdentityService is accepted by Kong and the property scope is visible in service logs.
- CI pipeline completes green on a trivial code change.
- Terraform plan produces zero drift on a fresh `terraform apply`.

Team Allocation: Platform Engineer (full sprint), 1 Java backend engineer (Flyway + DB schema baseline), EM (stakeholder alignment).

---

**Sprint 2 — PropertyService and RoomService**

Deliverables:
- PropertyService: CRUD for hotel properties (name, address, timezone, currency, room count), property group management.
- RoomService: CRUD for room types (name, description, capacity, amenities), individual room management (room number, floor, status: AVAILABLE/OCCUPIED/DIRTY/MAINTENANCE), room status transitions.
- PostgreSQL schemas: `properties`, `property_groups`, `room_types`, `rooms` with RLS policies.
- REST APIs:
  - `POST /api/v1/properties` — create property
  - `GET /api/v1/properties/{id}` — get property details
  - `POST /api/v1/rooms` — create room
  - `GET /api/v1/rooms?propertyId={id}&roomTypeId={id}&status={status}` — list rooms
  - `PATCH /api/v1/rooms/{id}/status` — update room status
- Unit tests: domain model (property, room), business rules.
- Integration tests: PropertyRepository, RoomRepository (TestContainers PostgreSQL + RLS verification).
- Web UI: Property configuration screen, Room type management, Room inventory board (read-only this sprint).

Acceptance Criteria:
- Cannot retrieve a room from Property A using a JWT scoped to Property B (403 or empty result).
- Room status transitions follow defined state machine: AVAILABLE → OCCUPIED → DIRTY → AVAILABLE; AVAILABLE → MAINTENANCE → AVAILABLE.
- RLS prevents cross-property queries at the database level (verified by integration test that bypasses application layer and queries directly with wrong `app.current_property_id`).

Team Allocation: 2 Java engineers, 1 frontend engineer, QA.

---

**Sprint 3 — ReservationService Core**

Deliverables:
- ReservationService: Create, Modify, Cancel reservation flows.
- Domain model: `Reservation` aggregate, `RoomAllocation` value object, `ReservationStatus`, `ReservationSource` enums.
- Availability Engine: Redis-first cache, PostgreSQL fallback, date-range availability check.
- Redis distributed locking (Redlock) for booking confirmation race condition prevention.
- Kafka integration: `ReservationCreatedEvent`, `ReservationCancelledEvent` published to Kafka topics.
- PostgreSQL schemas: `reservations`, `room_allocations`, `outbox_events`.
- REST APIs:
  - `POST /api/v1/reservations` — create reservation
  - `GET /api/v1/reservations/{id}` — get reservation
  - `PUT /api/v1/reservations/{id}` — modify reservation
  - `POST /api/v1/reservations/{id}/cancel` — cancel reservation
  - `GET /api/v1/availability?propertyId={id}&roomTypeId={id}&checkIn={date}&checkOut={date}` — availability search
- Unit tests: Reservation aggregate (all state transitions, event registration, business rule violations).
- Integration tests: ReservationRepository, InventoryCacheService.
- Outbox pattern: OutboxProcessor scheduled job; Kafka idempotent producer configuration.

Acceptance Criteria:
- Concurrent booking attempts for the same room type and date range result in one success and one `409 Conflict` (load test: 20 concurrent POST /reservations with same parameters).
- `ReservationCreatedEvent` appears on the Kafka topic within 2 seconds of a successful booking.
- Availability cache is invalidated and returns correct count after a new reservation is created.
- Cancel updates status and triggers cache invalidation within the same transaction.

Team Allocation: 2 Java engineers (domain focus), 1 Java engineer (infrastructure/persistence), QA.

---

**Sprint 4 — Web UI for Reservations and Phase 1 Testing**

Deliverables:
- React Web UI: Reservation calendar view, create reservation form (guest details, dates, room type, rate plan), reservation detail view, cancel reservation workflow.
- Availability calendar widget: colour-coded date selector showing available/limited/soldout states.
- TanStack Query integration: server state management, optimistic updates on cancel.
- Rate plan display: show nightly rate breakdown, total amount, cancellation policy summary.
- Basic rate plan management: `RatePlanServiceClient` stub (rate plans hardcoded for Sprint 4; replaced in Phase 3).
- E2E test (Playwright): full reservation create → view → cancel flow.
- Performance test baseline: Gatling script for availability search; target 200 RPS at this stage (full 1000 RPS target in Phase 3).
- Security review: OWASP ZAP scan on all Phase 1 endpoints; Snyk dependency scan.

Acceptance Criteria:
- Hotel staff can create a reservation from the Web UI without developer assistance.
- Playwright E2E test passes on staging with real PostgreSQL, Redis, and Kafka.
- OWASP ZAP scan reports zero high-severity findings on Phase 1 API surface.
- All integration tests pass with TestContainers; no mocked database in integration tests.

**Phase 1 Risks and Mitigations:**

| Risk                                        | Probability | Impact | Mitigation                                                |
|---------------------------------------------|-------------|--------|-----------------------------------------------------------|
| Terraform complexity delays infrastructure  | Medium      | High   | Platform engineer unblocks others using Docker Compose locally |
| RLS complexity causes data isolation bugs   | Medium      | High   | ArchUnit tests enforce layer separation; integration tests verify RLS directly |
| Redis cluster mode unfamiliar to team       | Low         | Medium | Spike in Sprint 1 with proof-of-concept script            |
| Availability search race condition hard to test | Medium  | High   | Dedicated concurrency unit test + load test in Sprint 4  |

---

## Phase 2 — Check-In, Check-Out, and Folio Billing (Sprints 5–8)

### Duration
4 sprints × 2 weeks = 8 weeks.

### Objectives
Complete the guest stay lifecycle: check-in with keycard encoding, in-stay folio charge posting, check-out with payment capture, invoice generation, and housekeeping task creation. Integrate with Stripe for payment processing.

### Dependencies on Phase 1
- ReservationService at CONFIRMED status is a prerequisite for check-in.
- Room status from RoomService must reflect AVAILABLE for room assignment.
- Kafka topics from Phase 1 (`reservation.created`) must be live.

### Sprint Breakdown

**Sprint 5 — Check-In Workflow and KeycardService**

Deliverables:
- ReservationService: `CheckInCommand` handler — room assignment via RoomService, status transition to `CHECKED_IN`, `CheckInCompletedEvent` to Kafka.
- KeycardService (Go): REST API to encode keycard (`POST /api/v1/keycard/encode`), revoke keycard (`POST /api/v1/keycard/revoke`); integration with ASSA ABLOY VISIONLINE simulator in dev.
- Site-to-Site VPN Terraform module: provisions VPN gateway, customer gateway resource; tested with a simulated on-premise environment using a VM in a separate VPC.
- Web UI: Check-in screen (room assignment, keycard encoding trigger, early check-in surcharge display).
- Integration tests: CheckInCommand with TestContainers, KeycardService HTTP client tests.

**Sprint 6 — FolioService (Charges and Taxes)**

Deliverables:
- FolioService: folio creation on reservation confirmed (triggered via Kafka `reservation.created`), room charge posting (nightly rate), supplementary charges (minibar, room service), tax calculation engine (VAT, city tax, service charge per property tax profile), folio settlement.
- PostgreSQL schema: `folios`, `folio_line_items`, `tax_profiles`, `payment_records`.
- REST APIs:
  - `GET /api/v1/folios/{reservationId}` — get current folio
  - `POST /api/v1/folios/{id}/charges` — post manual charge
  - `POST /api/v1/folios/{id}/payments` — apply payment
- Kafka consumer: `reservation.created` → create folio; `checkout.completed` → finalise folio.
- Unit tests: tax calculation (all edge cases: VAT-exempt guests, corporate rates, split-stay tax).

**Sprint 7 — Check-Out and Payment Gateway Integration**

Deliverables:
- ReservationService: `CheckOutCommand` handler, `CheckOutCompletedEvent`.
- Stripe payment integration in FolioService: PaymentIntent creation, authorisation at check-in, capture at check-out, refund on cancellation with refund fee calculation.
- FolioService: folio finalisation (all charges posted, tax computed, balance settled), PDF invoice generation (JasperReports or iText), S3 upload, pre-signed URL delivery via email.
- NotificationService: Kafka consumer for `checkout.completed` → send folio email with pre-signed URL.
- Web UI: Check-out screen (folio preview, payment capture, email invoice option).
- Security: Stripe webhook signature verification (Stripe uses its own HMAC-SHA256 variant via `Stripe-Signature` header).
- PCI DSS scope review: confirm no card data passes through HPMS application code.

**Sprint 8 — HousekeepingService and Phase 2 E2E Testing**

Deliverables:
- HousekeepingService (Node.js/Fastify): task management (create, assign, complete housekeeping tasks), WebSocket endpoint for real-time task updates to housekeeper mobile app.
- Kafka consumer: `checkout.completed` → generate housekeeping task (room clean), `checkin.completed` → update room status to OCCUPIED.
- React Native mobile app (housekeeping module): task list, task detail, mark-complete flow, real-time push updates via WebSocket.
- E2E test (Playwright): full check-in → post charge → check-out → verify folio email flow.
- Performance test: FolioService tax calculation under 500 concurrent requests.

**Phase 2 Acceptance Criteria:**
- A guest can check in via the Web UI, receive a keycard encoding confirmation, check out, and receive a PDF folio via email within 3 minutes of check-out action.
- Stripe PaymentIntent is captured at check-out without manual intervention.
- Housekeeping task appears in the mobile app within 10 seconds of check-out completion.
- PDF invoice contains correct room charges, taxes, and payment receipt.
- FolioService E2E Playwright test passes on staging.

**Phase 2 Risks and Mitigations:**

| Risk                                          | Probability | Impact | Mitigation                                              |
|-----------------------------------------------|-------------|--------|---------------------------------------------------------|
| Keycard vendor API documentation incomplete   | High        | Medium | Use ASSA ABLOY sandbox environment; engage vendor support early Sprint 5 |
| Tax calculation rules vary per jurisdiction   | High        | Medium | Tax profiles configurable per property; initial rules for Singapore/Thailand |
| Stripe API rate limits in test environment    | Low         | Low    | Use Stripe test mode with test clock for date-sensitive scenarios |
| PDF generation memory overhead on JVM         | Medium      | Low    | Benchmark with 50-page folios; use streaming PDF if needed |

---

## Phase 3 — OTA Channel Sync and Revenue Management (Sprints 9–12)

### Duration
4 sprints × 2 weeks = 8 weeks.

### Objectives
Integrate with Booking.com and Expedia OTA APIs for ARI (Availability, Rates, Inventory) push and pull, implement RevenueService with dynamic pricing, BAR, and rate restrictions, and deliver the NightAuditProcessor for daily financial close.

### Dependencies on Phase 2
- ReservationService stable with idempotent create (OTA reservations use same create flow).
- FolioService operational (night audit posts folio charges).
- Kafka topics from Phase 1 and 2 live.

### Sprint Breakdown

**Sprint 9 — ChannelManagerService Architecture and Booking.com Integration**

Deliverables:
- ChannelManagerService (Go): OTA webhook ingestion server, HMAC-SHA256 signature verification (per OTA), idempotent OTA reservation upsert, Kafka producer for `hpms.ota.events.inbound`, ARI push worker (rate/inventory updates to OTA extranet APIs).
- Booking.com integration: Availability API (pull), Rates API (pull), Reservations API (webhook receive + push acknowledge), OTA reservation mapping to HPMS Reservation domain model.
- Redis deduplication: 24-hour TTL dedup key per OTA event ID.
- Dead-letter queue worker: alert on DLQ messages, write to `ota_sync_errors` table.
- OTA IP allowlist management: WAF IP sets for Booking.com IP ranges.
- Web UI: OTA connection management screen (connect/disconnect OTA, sync status, last sync timestamp, error count).

**Sprint 10 — Expedia Integration and ARI Push**

Deliverables:
- Expedia integration: EQC (Expedia QuickConnect) API for availability, rates, restrictions; webhook for new reservations and modifications.
- ARI push Kafka consumer: `hpms.inventory.updated` → push to all connected OTA APIs for the affected property/room type/date range.
- Rate plan management REST API: create/update/deactivate rate plans, BAR (Best Available Rate) configuration.
- Stop-sell and minimum stay restriction management: REST API + Web UI.
- OTA conflict resolution: implement resolution rules (OTA wins for price, PMS wins for room assignment) in `OtaConflictResolver`.

**Sprint 11 — RevenueService and Dynamic Pricing**

Deliverables:
- RevenueService (Python/FastAPI): dynamic pricing engine (demand-based price adjustments using occupancy thresholds), BAR ladder (tiered rates by occupancy band), rate restrictions (minimum stay, close-to-arrival, advance purchase).
- Pricing rule management REST API.
- Scheduled ARI push: nightly pricing recalculation for the next 365 days → push updated rates to all connected OTAs.
- Revenue reporting REST API: occupancy rate, ADR (average daily rate), RevPAR, pickup report.
- PostgreSQL schema: `pricing_rules`, `rate_plans`, `rate_plan_dates`, `revenue_reports`.
- Web UI: Rate plan management dashboard, pricing rule editor, revenue summary widgets.

**Sprint 12 — NightAuditProcessor and Performance Testing**

Deliverables:
- NightAuditProcessor (Spring Batch): nightly job triggered at 23:55 hotel local time by a Kubernetes CronJob; steps: close day, post nightly room charges for all checked-in folios, compute no-shows (mark reservations as NO_SHOW if not checked in by 23:59), roll forward date for next day operations, generate daily revenue report.
- Night audit idempotency: `night_audit_runs` table with date + property as unique key; job is re-runnable safely.
- Performance test (Gatling): availability search endpoint target 1,000 RPS, p99 < 200 ms; test must pass on staging before Phase 3 is considered complete.
- Load test: OTA webhook ingestion at 500 events/minute sustained for 30 minutes.
- Feature flags: wrap night audit and ARI push behind LaunchDarkly flags for phased activation per property.

**Phase 3 Acceptance Criteria:**
- A booking made on Booking.com appears in HPMS within 30 seconds of OTA webhook receipt.
- ARI update pushed from HPMS appears in Booking.com extranet within 5 minutes.
- Duplicate OTA webhooks for the same booking are idempotent (no duplicate reservation).
- Night audit job completes for a 200-room property in under 5 minutes.
- Gatling performance test: 1,000 RPS availability search, p99 < 200 ms sustained for 10 minutes.

**Phase 3 Risks and Mitigations:**

| Risk                                             | Probability | Impact | Mitigation                                                   |
|--------------------------------------------------|-------------|--------|--------------------------------------------------------------|
| OTA API sandbox certification takes longer than expected | High | Medium | Start OTA developer portal registration in Sprint 8 (parallel to Phase 2) |
| OTA IP ranges change without notice              | Medium      | Medium | WAF IP set update process documented; monthly review calendar reminder |
| Dynamic pricing rules cause rate parity violations | Medium    | High   | Rate parity validation logic in RevenueService; alert if channel rates diverge > 5% |
| Night audit failure mid-run on large property    | Low         | High   | Spring Batch restart-from-failed-step; idempotency table prevents double posting |
| Performance test exposes Redis cluster bottleneck | Medium     | High   | Redis cluster already sized for 156 GiB; tune pipeline commands for multi-key operations |

---

## Phase 4 — Loyalty Programme and Analytics (Sprints 13–16)

### Duration
4 sprints × 2 weeks = 8 weeks.

### Objectives
Deliver the loyalty points engine (earn, redeem, tier management), multi-property group reporting (occupancy, RevPAR, pickup), an analytics data pipeline, and the housekeeping staff mobile app. Conclude with a security audit, penetration test, and production go-live preparation.

### Dependencies on Phase 3
- Reservation and folio lifecycle complete.
- OTA channel sync live (loyalty points earned on OTA bookings).
- Revenue reports data available for analytics pipeline seeding.

### Sprint Breakdown

**Sprint 13 — LoyaltyService**

Deliverables:
- LoyaltyService (Java/Spring Boot): guest profile management, loyalty tier definition (Bronze/Silver/Gold/Platinum with earn/redeem multipliers), points accrual on folio settlement, points redemption against folio balance.
- PostgreSQL schema: `loyalty_accounts`, `loyalty_transactions`, `loyalty_tiers`.
- REST APIs:
  - `GET /api/v1/loyalty/{guestId}/account` — get loyalty account and tier
  - `POST /api/v1/loyalty/{guestId}/redeem` — redeem points
  - `GET /api/v1/loyalty/{guestId}/transactions` — points transaction history
- Kafka consumer: `checkout.completed` → calculate points earned from folio amount, post to `loyalty_transactions`.
- Points expiry: points older than 24 months expire; daily CronJob processes expirations.
- Web UI: Loyalty account lookup at check-in, points balance display on folio, redemption flow.

**Sprint 14 — ReportingService and Analytics Pipeline**

Deliverables:
- ReportingService (Java/Spring Boot): pre-built report queries on RDS read replica (occupancy report, RevPAR report, daily pickup report, channel production report), cached report results in Redis (30-minute TTL).
- Analytics data pipeline: daily export from PostgreSQL → Amazon Redshift (via AWS Glue ETL job) for complex historical queries and trend analysis.
- Multi-property dashboard Web UI: group-level occupancy heatmap, RevPAR comparison across properties, loyalty member contribution report.
- Report scheduling: hotel GMs receive scheduled PDF reports via email (daily/weekly/monthly cadence configurable per property).

**Sprint 15 — Mobile App and Multi-Property Features**

Deliverables:
- React Native mobile app — full feature set: housekeeping task list, task detail + complete, room status board, push notifications via FCM/APNs for new task assignments.
- Multi-property management: hotel group admin screens (switch property context, group-level user management, group-level rate plan inheritance).
- Mobile app distribution: TestFlight (iOS) and Google Play Internal Testing track.
- Offline mode for HousekeepingService: tasks cached locally in SQLite; sync when connectivity is restored.

**Sprint 16 — Security Audit, Performance, and Go-Live Preparation**

Deliverables:
- External penetration test (OWASP ZAP automated + manual): coverage of all API endpoints, authentication flows, OTA webhook endpoints, payment flows.
- Snyk full-codebase vulnerability scan: zero high-severity findings before go-live sign-off.
- Chaos engineering: Chaos Mesh experiments — kill a single AZ (verify traffic redistributes), kill Redis shard (verify failover and cache miss fallback), kill primary RDS (verify Multi-AZ promotion and RDS Proxy reconnect).
- Disaster recovery drill: full DR failover to ap-southeast-2, validate reservation creation works in DR region, measure actual RTO.
- Load test: end-to-end production simulation — 500 concurrent guests browsing availability, 50 concurrent check-ins, 20 concurrent OTA webhook events per second.
- Documentation finalisation: runbooks for all on-call scenarios, DR runbook, night audit manual override procedure.
- Go-live readiness review: EM, QA, Platform Engineer, Product Owner sign off on readiness checklist.

**Phase 4 Acceptance Criteria:**
- Loyalty points are credited to a guest's account within 10 seconds of folio settlement.
- Multi-property dashboard loads group RevPAR data for 12 months in under 3 seconds.
- Penetration test report: zero critical, zero high findings.
- DR drill: system operational in DR region within 15 minutes of simulated primary failure.
- React Native app approved for TestFlight distribution.

---

## Cross-Phase Concerns

### CI/CD Pipeline (GitHub Actions + ArgoCD)

Applied from Sprint 1 and maintained throughout:

```
PR Opened:
  1. Lint (Checkstyle / ESLint / golangci-lint / ruff)
  2. Unit tests
  3. Integration tests (TestContainers)
  4. Contract tests (Pact)
  5. Docker image build (multi-stage, non-root user)
  6. Snyk vulnerability scan
  7. OWASP dependency check

PR Merged to main:
  8. Docker image tag with Git SHA → push to ECR
  9. ArgoCD sync to dev environment (automatic)
  10. Smoke tests on dev (health check, basic API call)

Manual promotion to staging:
  11. ArgoCD sync to staging (manual approval)
  12. E2E tests (Playwright)
  13. Performance tests (Gatling, on staging only, weekly)

Manual promotion to production:
  14. ArgoCD sync to production (manual approval + Change Request)
  15. Canary deployment (5% traffic for 15 minutes → 100%)
  16. PagerDuty alert suppression window during deployment
```

### Infrastructure as Code (Terraform)

All AWS resources are defined in `infra/terraform/`. Module structure:

```
infra/terraform/
├── modules/
│   ├── eks/          — EKS cluster, node groups, IRSA
│   ├── rds/          — RDS PostgreSQL, RDS Proxy, parameter groups
│   ├── elasticache/  — Redis cluster, subnet groups
│   ├── msk/          — Kafka cluster, ACLs
│   ├── s3/           — Buckets, policies, replication
│   ├── networking/   — VPC, subnets, route tables, security groups
│   ├── waf/          — WAF rules, IP sets
│   └── monitoring/   — CloudWatch dashboards, alarms, SNS topics
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── global/
    └── iam/          — IAM roles, IRSA policies
```

Terraform state is stored in S3 (`hpms-terraform-state-{accountId}`) with DynamoDB table for state locking. `terraform plan` runs on every PR touching `infra/terraform/`. `terraform apply` requires manual approval by the Platform Engineer.

### Database Migrations (Flyway)

- Migration files: `V{n}__{description}.sql` (e.g., `V1__init_reservations_schema.sql`)
- Each migration is a single transaction where possible; long DDL operations (index creation on large tables) use `CREATE INDEX CONCURRENTLY` outside the transaction block.
- Rollback migrations are maintained for the last 3 versions (`U{n}__{description}.sql`).
- Migrations are applied automatically on service startup in dev and staging. In production, migrations are applied via a pre-deployment Kubernetes Job to decouple migration from service rollout.

### API Contract Testing (Pact)

Pact consumer-driven contract tests are written by the consumer service (the service making the API call) and verified by the provider service. This prevents API breaking changes from reaching production undetected.

- ChannelManagerService (consumer) defines contracts for ReservationService (provider) upsert endpoint.
- Web App (consumer) defines contracts for all backend services it consumes.
- Pact Broker is self-hosted in the `hpms-shared` namespace. Contract verification is a required CI check before any provider service is merged.

### Security Scanning Schedule

| Scan Type           | Tool          | Frequency         | Failure Action                          |
|---------------------|---------------|-------------------|-----------------------------------------|
| Dependency CVEs     | Snyk          | Every PR          | Block merge on high/critical CVEs       |
| Container image     | ECR Scanning  | Every image push  | Block deployment on critical CVEs       |
| DAST                | OWASP ZAP     | Weekly (staging)  | P2 alert; fix within sprint             |
| Penetration test    | External firm | Phase 4 + annually| Block go-live on critical findings      |
| Secret scanning     | GitHub secret scanning | Every push | Block push on detected secrets  |

---

## Go-Live Checklist

### Infrastructure Readiness
- [ ] All Terraform modules applied to production without drift.
- [ ] RDS Multi-AZ failover tested (manual failover in production, non-peak hours, with RDS Proxy reconnect verified).
- [ ] ElastiCache Redis failover tested (shard primary killed; automatic failover within 60 seconds confirmed).
- [ ] MSK Kafka broker failure tested (one broker terminated; producer continues without error after partition leader re-election).
- [ ] Site-to-Site VPN to pilot hotel property verified (both tunnels active; offline mode tested).
- [ ] CloudFront distribution configured for production domain (HTTPS enforced, HSTS header, cache policies correct).
- [ ] VPC Flow Logs active and queryable in Athena.
- [ ] GuardDuty enabled with high-severity findings alert to PagerDuty.

### Application Readiness
- [ ] All Phase 1–4 acceptance criteria verified on staging.
- [ ] All E2E Playwright tests passing on staging (100% pass rate, no flaky tests in last 10 runs).
- [ ] Gatling performance test: 1,000 RPS availability search, p99 < 200 ms (last run ≤ 7 days ago).
- [ ] Night audit tested with production-scale data (200-room property, 150 in-house guests).
- [ ] OTA integration tested on Booking.com and Expedia sandbox with end-to-end booking flow.
- [ ] PDF invoice generation tested for multi-room, multi-night, multi-tax-type scenarios.
- [ ] Loyalty points calculation verified for all tier transitions.

### Security Readiness
- [ ] External penetration test completed; zero critical and high findings outstanding.
- [ ] Snyk scan: zero high/critical CVEs in production Docker images.
- [ ] PCI DSS scope review signed off: no card data in HPMS application code or logs confirmed.
- [ ] All Secrets Manager secrets rotated within last 30 days.
- [ ] IAM role policies reviewed for least-privilege (no `*` actions on any role).
- [ ] HMAC verification active on all OTA webhook endpoints (tested with invalid signature → 401).

### Operational Readiness
- [ ] On-call runbooks written for all P1/P2 alert scenarios.
- [ ] PagerDuty escalation policy configured: on-call engineer → EM → CTO.
- [ ] Grafana dashboards reviewed by on-call engineers; no "what does this metric mean" confusion.
- [ ] ArgoCD sync health: all production applications Synced and Healthy.
- [ ] Rollback procedure tested on staging (previous Git SHA deployed via ArgoCD in under 5 minutes).
- [ ] Backup restore tested: RDS point-in-time recovery to 1 hour prior verified on staging.
- [ ] First hotel property onboarded in staging with real reservation data.
- [ ] Hotel staff trained on Web UI (reservation management, check-in/out, folio review).

---

## Rollback Strategy

### Application Rollback (ArgoCD)

Rollback is performed by reverting the Git SHA in the ArgoCD application definition:

```bash
# Identify the last stable deployment tag
argocd app history hpms-reservation-service --namespace hpms-sunshinehotels

# Rollback to previous Git SHA
argocd app rollback hpms-reservation-service --revision {previous-sha}
```

ArgoCD applies the rollback within 2 minutes (rolling update, zero-downtime). The rollback triggers the CI pipeline health checks; PagerDuty alerts are suppressed for 15 minutes during planned rollbacks.

### Database Rollback

Application code is rolled back independently of the database schema. Flyway rollback migrations (`U{n}__rollback.sql`) are executed manually if a schema change is being reverted. This is intentionally a manual step to force deliberate decision-making.

**Key principle:** If a migration cannot be safely rolled back (e.g., a column was dropped and data was lost), it is classified as a "point of no return" migration and the deployment plan must account for a forward-only rollback (roll forward with a fix, not backward).

### Feature Flag Rollback

For high-risk features (OTA sync, night audit, dynamic pricing), the feature is disabled via LaunchDarkly in under 60 seconds without a code deployment:

```
LaunchDarkly Flag: hpms.ota-sync.enabled
  → Targeting: property-group = "SunshineHotels"
  → Toggle OFF: disables OTA webhook processing; webhooks are queued in SQS for up to 4 days
  → Toggle ON: SQS consumer resumes; processes backlog in order
```

This allows hot-disabling a misbehaving feature for a specific property group without affecting others.

### Partial Rollout Strategy

New properties are onboarded one at a time. The first production property uses 5% of the production infrastructure capacity. This limits blast radius: if a production bug emerges on property 1, it affects only that property while the rest remain on stable state.

Each OTA integration (Booking.com, Expedia) is activated per property via LaunchDarkly, not as a global switch. This allows properties to go live with OTA sync independently on their own readiness timeline.
