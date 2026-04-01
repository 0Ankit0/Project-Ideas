# Implementation Playbook - Restaurant Management System

## Overview

This playbook defines the end-to-end delivery plan for building a production-ready Restaurant Management System (RMS). It covers technology choices, phased delivery milestones, service setup, testing strategy, CI/CD pipeline, monitoring requirements, and a comprehensive go-live checklist. The target system connects front-of-house operations (reservations, table management, POS ordering), kitchen orchestration (KDS, routing, station management), inventory and procurement, billing and settlement, workforce management, and multi-branch reporting into a single cohesive platform.

The system is designed for multi-branch restaurant groups with 10 to 500+ covers per location and must support simultaneous dine-in, takeaway, and delivery channels without service degradation during peak periods.

---

## Technology Stack

### Backend
| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Runtime | Node.js / TypeScript | Node 20 LTS, TS 5.x | Type safety, ecosystem maturity, async I/O performance |
| Framework | NestJS | 10.x | Modular DI, guards, interceptors, CQRS support |
| Alternative | Python / FastAPI | Python 3.12, FastAPI 0.110 | Choose if ML/analytics workloads dominate |
| ORM | TypeORM / Prisma | Latest stable | Schema migrations, type-safe queries |

### Data Stores
| Store | Technology | Version | Usage |
|-------|-----------|---------|-------|
| Primary DB | PostgreSQL | 15.x | All transactional data (orders, billing, inventory) |
| Cache | Redis | 7.x | Session state, real-time slot availability, idempotency keys |
| Message Queue | RabbitMQ | 3.12 or Kafka 3.6 | Kitchen ticket fan-out, notification dispatch, event sourcing |
| Search | Elasticsearch | 8.x | Menu search, order history search, audit log queries |
| Object Store | S3 / MinIO | — | Receipt PDFs, menu images, export archives |

### Frontend
| Surface | Technology | Notes |
|---------|-----------|-------|
| Staff POS | React 18 + TypeScript | Optimised for tablet touch, offline-capable |
| Kitchen Display | React 18 + TypeScript | Auto-refresh, low-latency WebSocket updates |
| Back Office | React 18 + TypeScript | Data-heavy dashboards, reporting, procurement |
| Guest Touchpoints | React 18 + TypeScript | QR menus, reservation widget, order status |
| Mobile (Staff) | React Native 0.73 | Waiter app, manager oversight, inventory counts |

### DevOps & Infrastructure
| Tool | Purpose |
|------|---------|
| Docker | Local development, containerised builds |
| Kubernetes (K8s 1.29) | Production orchestration, auto-scaling |
| GitHub Actions | CI/CD pipelines, automated testing, deployments |
| Helm | K8s chart management per service |
| Terraform | Infrastructure as code (VPC, RDS, EKS, etc.) |
| ArgoCD | GitOps continuous delivery to Kubernetes |
| Datadog / Grafana | Metrics, dashboards, alerting |
| OpenTelemetry | Distributed tracing across services |
| Vault (HashiCorp) | Secrets management |

---

## Phase 1: Foundation (Weeks 1–4)

**Goal:** Establish the technical backbone — infrastructure, identity, branch configuration, and developer tooling — before any business logic is built.

### Deliverables

1. **Monorepo scaffold** — `apps/`, `packages/domain/`, `packages/ui/`, `packages/shared/`, `infra/`, `tests/` directory structure with Turborepo or Nx workspace configuration.
2. **Docker Compose local stack** — PostgreSQL 15, Redis 7, RabbitMQ 3.12, Elasticsearch 8, MinIO; all seeded and health-checked.
3. **Database migration framework** — TypeORM migrations or Flyway; versioned migration files checked into source control; seed scripts for dev/staging.
4. **Authentication service** — JWT-based auth with refresh tokens; staff login with PIN + password; SSO integration scaffold (SAML/OIDC); session-bound to device and shift.
5. **Role-Based Access Control (RBAC)** — Role definitions: `super_admin`, `branch_manager`, `head_chef`, `waiter`, `cashier`, `kitchen_staff`, `inventory_clerk`; permission matrix in database; branch-scoping on every authenticated request.
6. **Branch and outlet configuration** — Branch entity with timezone, currency, tax regime, operating hours, service channels (dine-in/takeaway/delivery) toggles; multi-branch hierarchy.
7. **Device registry** — POS terminal, KDS screen, and printer registration; device-level authentication tokens; heartbeat tracking.
8. **API gateway scaffold** — NestJS API with versioned routes (`/v1/`), request validation (class-validator), rate limiting (per device + per user), Swagger/OpenAPI docs auto-generated.
9. **Shared domain types package** — `OrderStatus`, `TableStatus`, `TicketStatus`, `PaymentStatus`, `StockMovementType` enums; base entity classes; `BranchScopedCommand` interface.
10. **CI pipeline (GitHub Actions)** — Lint (ESLint + Prettier), type-check, unit test, build; runs on every PR; blocking merge on failure.
11. **Developer onboarding runbook** — `make dev` command boots full local stack; seed data creates demo branch with tables, menu, and staff accounts; README updated.
12. **Secret management baseline** — Vault or AWS Secrets Manager integration; no secrets in source code; `.env.example` documented.

### Phase 1 Exit Criteria
- New developer can boot full local stack within 15 minutes following onboarding runbook.
- All role-permission combinations tested with automated assertions.
- Branch scoping enforced: querying data from branch B with branch A credentials returns 403.
- CI pipeline runs in under 5 minutes.

---

## Phase 2: Core Operations (Weeks 5–10)

**Goal:** Deliver the primary revenue-generating workflows — table management, ordering, kitchen routing, and basic billing.

### Deliverables

1. **Table and floor plan management** — Floor plan entity with sections and table nodes; table states (`available`, `reserved`, `occupied`, `cleaning`, `blocked`); capacity and shape attributes; merge/split table operations.
2. **Reservation system** — Reservation creation, confirmation, modification, cancellation; party size validation against table capacity; time-slot conflict detection with configurable buffer; walk-in queue alongside reservations.
3. **Waitlist engine** — Party registration; ETA calculation based on real-time turnover; priority rules (VIP, accessibility, prepaid); automated SMS/push notification on table availability.
4. **Menu service** — Menu categories, menu items, modifiers and modifier groups, combo definitions; item availability flags; branch-specific pricing; scheduled availability windows (breakfast/lunch/dinner); image upload to object store.
5. **Order service (core)** — Draft order creation; line-item management with modifiers, course assignments, and seat assignments; version-stamped optimistic locking; submit action with full validation pipeline; order status state machine.
6. **Tax and discount engine** — Tax rate configuration by item category, tax-inclusive/exclusive modes, composite tax rules; discount types (percentage, fixed, item-level, check-level); approval thresholds for manager-authorised discounts.
7. **Kitchen routing service** — Station configuration (grill, cold, pastry, bar, expo); routing rules based on item category and course; ticket grouping by table + course; KDS push via WebSocket; SLA timer per station.
8. **Kitchen Display System (KDS) API** — Real-time ticket subscription; bump/recall controls; refire workflow with reason codes; delay propagation to front-of-house; station performance metrics.
9. **Basic billing** — Bill generation from settled order; single-tender capture (card/cash); receipt generation (PDF); bill void with approval; drawer session open/close.
10. **Printer integration** — Receipt printer and kitchen printer adapters; ESC/POS and Star TSP command formatting; connection health monitoring; fallback to digital receipt.
11. **Real-time POS state sync** — WebSocket hub for table status, order status, and kitchen ticket updates; branch-scoped channels; reconnect and replay on disconnect.
12. **E2E happy-path test suite** — Full dine-in cycle: seat → order → kitchen → serve → bill → settle, automated with Playwright or Cypress against a seeded staging environment.

### Phase 2 Exit Criteria
- Full dine-in happy path from seat to settlement completes under 3 seconds for each step.
- Concurrent order submission by 10 waiters on the same branch produces zero duplicate kitchen tickets.
- KDS receives ticket update within 500ms of order submission under normal load.
- Bill totals (including tax and discount) reconcile to zero variance across 1,000 synthetic orders.

---

## Phase 3: Advanced Features (Weeks 11–16)

**Goal:** Add inventory management, procurement, multi-channel ordering, workforce tools, and advanced reporting.

### Deliverables

1. **Recipe and ingredient management** — Ingredient master with unit-of-measure; recipe definitions linked to menu items; ingredient-level yield factors; recipe versioning with effective dates; sub-recipe support.
2. **Real-time inventory depletion** — Stock deduction on order submit (or kitchen fire, configurable); compensating reversal on void/cancel; low-stock alerts via notification service; par level and reorder point configuration.
3. **Stock count sessions** — Scheduled and ad-hoc physical count workflows; variance calculation against system stock; variance approval before adjustment posting; full audit trail per count session.
4. **Procurement module** — Supplier master; purchase order creation, approval workflow, submission to supplier; goods received note (GRN) creation; partial receipt handling; price variance detection and exception queue.
5. **Waste and transfer management** — Waste recording with category codes (spoilage, breakage, over-prep, theft); inter-branch stock transfer with in-transit state; transfer receiving confirmation.
6. **Delivery channel integration** — Webhook ingestion from Uber Eats / DoorDash / Talabat; order normalisation to internal order model; menu availability sync push; platform-level financial reconciliation.
7. **Takeaway and curbside workflow** — Takeaway order creation at POS; estimated ready time; customer notification (SMS/push) on ready; handoff confirmation; integration with third-party aggregators.
8. **Shift scheduling** — Shift template library; weekly schedule publishing; staff availability management; schedule conflict detection; shift swap workflow with manager approval.
9. **Attendance and timesheet** — Clock-in/out via POS terminal or manager app; break tracking; shift variance reporting; export for payroll systems.
10. **Advanced billing — split checks** — Bill split by seat, by item, by percentage, or custom; multi-tender per sub-check; partial payment support; rounding allocation rules; tip handling.
11. **Loyalty and promotions** — Loyalty programme configuration (points, tiers, rewards); promotion engine (happy hour, combo deals, loyalty redemptions); promotion eligibility rules; member lookup at POS.
12. **Operational reporting** — Revenue by period (hourly, daily, weekly); covers and average spend; item sales mix; kitchen SLA compliance; inventory variance; staff performance; branch comparison dashboards.

### Phase 3 Exit Criteria
- Inventory depletion audit for 500 orders shows zero unexplained variances.
- Purchase order to stock receipt end-to-end workflow completes with correct GRN and ledger entries.
- Delivery platform webhook round-trip (order in → kitchen ticket) completes within 2 seconds.
- Split bill with 10 sub-checks and 3 tender types reconciles to zero penny variance.
- Shift schedule published to 50 staff members triggers notifications within 30 seconds.

---

## Phase 4: Optimisation and Launch (Weeks 17–20)

**Goal:** Harden the system for production load, complete security review, finalise runbooks, and execute go-live.

### Deliverables

1. **Performance optimisation** — Database query profiling; index review and optimisation; N+1 query elimination; Redis caching for hot read paths (slot availability, menu, item prices); connection pool tuning.
2. **Load testing** — k6 or Artillery load tests at 2× expected peak per branch; identify and fix bottlenecks; validate Kubernetes HPA scaling policies; document capacity model per branch tier.
3. **Security audit** — OWASP Top 10 review; pen test on auth, RBAC, and payment flows; PCI DSS scoping assessment; secrets rotation verification; dependency vulnerability scan (Snyk/Dependabot).
4. **Data backup and recovery validation** — PostgreSQL PITR configured; recovery drill to staging environment; RTO/RPO measurements documented; backup alert rules configured.
5. **Observability stack** — Metrics (Prometheus/Datadog), distributed traces (OpenTelemetry → Jaeger/Tempo), structured logs (JSON → Loki/CloudWatch); SLO dashboards; alerting rules with PagerDuty/OpsGenie routing.
6. **Runbook library** — Runbooks for: branch network outage, KDS failure, payment gateway outage, database failover, high-CPU incident, cache eviction storm, delivery platform webhook failure, end-of-day close failure.
7. **Staff training materials** — POS operation guide; KDS guide; back-office guide; manager day-close guide; video walkthroughs for core workflows.
8. **Staged rollout** — Pilot with 1 branch for 2 weeks; feedback loop; bug-fix sprint; expand to 5 branches; full rollout.

### Phase 4 Exit Criteria
- System sustains 2× peak load for 30 minutes with p95 API latency ≤ 500ms.
- All P0 and P1 security findings remediated.
- Recovery drill completes within RTO target of 30 minutes.
- All runbooks reviewed and signed off by operations team.
- Pilot branch NPS from staff ≥ 7/10.

---

## Database Setup

### Migration Strategy
```bash
# Run all pending migrations
npm run db:migrate

# Roll back last migration
npm run db:migrate:revert

# Generate migration from schema diff
npm run db:migrate:generate -- --name=add_loyalty_tier_column

# Seed development data
npm run db:seed:dev

# Seed staging data (anonymised production subset)
npm run db:seed:staging
```

### Key Indexes (Performance Critical)
```sql
-- Orders: branch + status queries (most frequent)
CREATE INDEX CONCURRENTLY idx_orders_branch_status
  ON orders(branch_id, status) WHERE status NOT IN ('settled','voided');

-- Kitchen tickets: station + active tickets
CREATE INDEX CONCURRENTLY idx_kitchen_tickets_station_active
  ON kitchen_tickets(station_id, created_at) WHERE status NOT IN ('complete','cancelled');

-- Inventory stock: branch + ingredient lookup
CREATE INDEX CONCURRENTLY idx_stock_ledger_branch_ingredient
  ON stock_ledger_entries(branch_id, ingredient_id, created_at DESC);

-- Reservations: date-range queries
CREATE INDEX CONCURRENTLY idx_reservations_branch_date
  ON reservations(branch_id, reservation_date, status);

-- Sessions: staff lookup by token
CREATE INDEX CONCURRENTLY idx_staff_sessions_token
  ON staff_sessions(token_hash) WHERE expires_at > NOW();
```

### Database Partitioning
- `kitchen_tickets` partitioned by `created_at` (monthly range) — archived after 90 days.
- `stock_ledger_entries` partitioned by `branch_id` + `created_at` — supports per-branch archival.
- `audit_log` partitioned by `created_at` (monthly range) — retained 7 years for compliance.

---

## Service Setup

### Docker Compose (Local Development)
```yaml
# docker-compose.yml
version: '3.9'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rms_dev
      POSTGRES_USER: rms
      POSTGRES_PASSWORD: rms_dev_secret
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rms"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports: ["5672:5672", "15672:15672"]
    environment:
      RABBITMQ_DEFAULT_USER: rms
      RABBITMQ_DEFAULT_PASS: rms_dev_secret

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
    ports: ["9200:9200"]
    mem_limit: 1g

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: rmsadmin
      MINIO_ROOT_PASSWORD: rms_dev_secret
```

### Environment Variables
```bash
# Application
NODE_ENV=development
PORT=3000
API_VERSION=v1
BRANCH_ID_HEADER=x-branch-id

# Database
DATABASE_URL=postgresql://rms:rms_dev_secret@localhost:5432/rms_dev
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=20
DATABASE_STATEMENT_TIMEOUT=30000

# Redis
REDIS_URL=redis://localhost:6379
REDIS_KEY_PREFIX=rms:
REDIS_TTL_SLOT_AVAILABILITY=30
REDIS_TTL_MENU_CACHE=300
REDIS_TTL_IDEMPOTENCY_KEY=86400

# Message Queue
RABBITMQ_URL=amqp://rms:rms_dev_secret@localhost:5672
QUEUE_KITCHEN_TICKETS=kitchen.tickets
QUEUE_NOTIFICATIONS=notifications.dispatch
QUEUE_ACCOUNTING_EXPORTS=accounting.exports
QUEUE_STOCK_PROJECTIONS=inventory.projections

# Auth
JWT_SECRET=change_me_in_production
JWT_ACCESS_TTL=900
JWT_REFRESH_TTL=86400
JWT_ALGORITHM=RS256

# Payment
PAYMENT_GATEWAY_URL=https://sandbox.payment-provider.com
PAYMENT_GATEWAY_API_KEY=sandbox_key
PAYMENT_IDEMPOTENCY_TTL=86400

# Object Storage
S3_ENDPOINT=http://localhost:9000
S3_BUCKET_RECEIPTS=rms-receipts
S3_BUCKET_MENU_IMAGES=rms-menu-images
S3_ACCESS_KEY=rmsadmin
S3_SECRET_KEY=rms_dev_secret
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \         E2E Tests (5%)
       /    \        - Full dine-in cycle
      /------\       - Delivery webhook round-trip
     /        \      - Day-close workflow
    /  Integ.  \     Integration Tests (25%)
   /   Tests    \    - Service-to-service flows
  /--------------\   - DB + queue interactions
 /                \
/   Unit Tests     \  Unit Tests (70%)
/------------------\  - Business logic
                      - Tax/discount calculations
                      - Routing rules
                      - Recipe depletion math
```

### Unit Testing (Jest)
- Coverage targets: **branches 80%, functions 90%, statements 85%**
- Focus areas: tax calculation, discount stacking, recipe yield math, routing rule evaluation, rounding allocation, refund eligibility checks.
- Use table-driven tests for policy matrix coverage (role × action × expected permission).
- Mock all I/O (database, queue, HTTP calls) with Jest mocks or ts-mockito.

### Integration Testing (Jest + Supertest)
- Run against Docker Compose stack with real PostgreSQL and Redis.
- Cover: order submission → kitchen ticket creation, payment capture → ledger entry, stock deduction → low-stock alert, GRN receipt → stock increment.
- Use database transactions that roll back after each test to maintain isolation.

### Contract Testing (Pact)
- POS → API contracts for order submission, table status, and bill retrieval.
- Delivery platform webhook contracts for order creation and cancellation events.
- KDS → API contracts for ticket subscription and bump actions.

### E2E Testing (Playwright)
- Scenarios: full dine-in cycle, delivery order cycle, shift open/close, day-close with reconciliation.
- Run nightly against staging environment.
- Screenshot capture on failure; stored in GitHub Actions artifacts.

### Load Testing (k6)
```javascript
// k6 scenario: order submission at 2x peak
export const options = {
  scenarios: {
    peak_orders: {
      executor: 'ramping-arrival-rate',
      startRate: 10, timeUnit: '1s',
      preAllocatedVUs: 50, maxVUs: 200,
      stages: [
        { target: 50, duration: '2m' },   // ramp up
        { target: 50, duration: '5m' },   // sustain peak
        { target: 0,  duration: '1m' },   // ramp down
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed:   ['rate<0.01'],
  },
};
```

---

## Deployment Pipeline

### GitHub Actions — CI Workflow
```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v4

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env: { POSTGRES_DB: rms_test, POSTGRES_USER: rms, POSTGRES_PASSWORD: rms_test }
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci && npm run db:migrate
        env: { DATABASE_URL: postgresql://rms:rms_test@localhost:5432/rms_test }
      - run: npm run test:integration
        env: { DATABASE_URL: postgresql://rms:rms_test@localhost:5432/rms_test, REDIS_URL: redis://localhost:6379 }

  build-docker:
    needs: [lint-and-type-check, unit-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          push: false
          tags: rms-api:${{ github.sha }}
```

### GitHub Actions — CD Workflow (Staging)
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/org/rms-api:${{ github.sha }}
      - name: Deploy to staging cluster
        run: |
          helm upgrade --install rms-api ./charts/rms-api \
            --namespace staging \
            --set image.tag=${{ github.sha }} \
            --set env=staging \
            --wait --timeout=5m
      - name: Run smoke tests
        run: npm run test:smoke -- --env=staging
```

---

## Monitoring and Observability

### Key SLOs
| Service | SLO | Alert Threshold |
|---------|-----|----------------|
| Order Submission API | p95 < 300ms, error rate < 0.5% | p95 > 400ms or errors > 1% |
| Kitchen Ticket Push | Delivery within 500ms of submit | Delivery > 800ms |
| Bill Generation | < 1s for up to 50-item check | > 2s |
| Payment Capture | < 3s end-to-end | > 5s or timeout |
| Stock Depletion Job | < 30s queue lag | > 60s lag |

### Dashboards
1. **Branch Operations Dashboard** — Active tables, open orders, kitchen SLA, cash drawer status.
2. **API Health Dashboard** — Request rate, error rate, p50/p95/p99 latency per endpoint.
3. **Kitchen Performance Dashboard** — Ticket age by station, bump rate, refire rate, SLA breach count.
4. **Financial Dashboard** — Revenue by hour, settlement status, unreconciled intents, refund volume.
5. **Infrastructure Dashboard** — CPU/memory per pod, DB connection pool usage, Redis hit rate, queue depth.

### Alert Runbook Links
| Alert | Severity | Runbook |
|-------|----------|---------|
| `KitchenTicketDeliveryHigh` | P1 | `runbooks/kitchen-ticket-latency.md` |
| `PaymentGatewayTimeoutRate` | P1 | `runbooks/payment-gateway-outage.md` |
| `DatabaseConnectionPoolExhausted` | P0 | `runbooks/db-pool-exhaustion.md` |
| `OrderSubmitErrorRateHigh` | P1 | `runbooks/order-submit-errors.md` |
| `StockProjectionLagHigh` | P2 | `runbooks/stock-lag.md` |

---

## Launch Checklist

### Infrastructure
- [ ] Production Kubernetes cluster provisioned and hardened (RBAC, network policies, pod security)
- [ ] RDS PostgreSQL 15 Multi-AZ with PITR enabled and tested
- [ ] Redis 7 with cluster mode; eviction policy set to `allkeys-lru`
- [ ] RabbitMQ / Kafka cluster with durable queues and dead-letter queues configured
- [ ] SSL/TLS certificates provisioned (Let's Encrypt or ACM); auto-renewal configured
- [ ] CDN configured for static assets; cache-busting headers set
- [ ] WAF rules deployed; OWASP Core Rule Set enabled
- [ ] DNS records configured; health check routing active
- [ ] VPN / private access for admin and database subnets
- [ ] Secrets rotated from development values; Vault or Secrets Manager populated

### Application
- [ ] All database migrations run successfully on production database
- [ ] Seed data verified (branch config, menu, roles, devices)
- [ ] Feature flags configured; all Phase 1–3 features enabled for pilot branch
- [ ] Payment gateway production credentials configured and tested with a live transaction
- [ ] Delivery platform webhooks registered with production endpoint URLs and verified signatures
- [ ] Email/SMS notification templates reviewed and tested
- [ ] PDF receipt template reviewed; logo and branding applied
- [ ] Printer firmware and connectivity validated on pilot branch devices
- [ ] KDS devices registered and receiving real-time updates

### Security
- [ ] All P0/P1 security findings from audit closed
- [ ] PCI DSS scope documented; card data tokenisation verified
- [ ] RBAC matrix reviewed by operations lead and signed off
- [ ] Penetration test completed; report archived
- [ ] Audit log retention policy configured (7 years)
- [ ] GDPR / data privacy obligations documented; erasure workflow tested
- [ ] Staff accounts created with correct roles; shared accounts eliminated
- [ ] Two-factor authentication enabled for manager and admin accounts

### Monitoring
- [ ] All production SLO dashboards deployed and showing data
- [ ] Alert rules tested (trigger synthetic alerts; verify PagerDuty routing)
- [ ] On-call rotation configured for P0/P1 alerts
- [ ] Distributed tracing sampling rate configured (10% production)
- [ ] Log retention configured (90 days hot, 1 year cold)
- [ ] Synthetic monitoring configured for critical paths (order submission, payment)

### Operations
- [ ] All runbooks reviewed and accessible to on-call team
- [ ] Backup restore drill completed; RTO/RPO targets met
- [ ] Branch network outage simulation completed; degraded mode validated
- [ ] Day-close workflow tested end-to-end on staging with full order volume
- [ ] Staff training completed for POS, KDS, and back-office roles
- [ ] Escalation contact list populated and distributed
- [ ] Post-launch support rota established for first 4 weeks
- [ ] Rollback plan documented and rehearsed

---

## Post-Launch Operations

### Week 1–2 (Hypercare)
- On-site support at pilot branch during peak service hours.
- Daily stand-up with branch manager to capture feedback.
- Monitor all P1/P2 alerts; target 15-minute response time.
- Patch deployment cycle: bug fixes deployed within 24 hours; hotfixes within 4 hours.

### Week 3–4
- Transition to remote support model.
- Review KPI dashboard: order-to-ticket latency, settlement reconciliation accuracy, stock variance rate.
- Identify and prioritise top 10 usability improvements from staff feedback.
- Conduct first post-launch retrospective; update runbooks based on real incidents.

### Ongoing Operations
- Monthly backup restore drill.
- Quarterly penetration test review.
- Semi-annual capacity review and load test refresh.
- Annual DR failover drill.
- Dependency updates: monthly security patches, quarterly framework updates.

### Operational KPIs
| KPI | Target | Review Cadence |
|-----|--------|----------------|
| Order-to-kitchen ticket latency (p95) | < 500ms | Daily |
| Settlement reconciliation accuracy | > 99.9% | Daily |
| Unresolved payment intents at day-close | 0 | Daily |
| System uptime (excluding planned maintenance) | > 99.9% | Monthly |
| Mean time to detect P1 incident (MTTD) | < 3 minutes | Monthly |
| Mean time to recover P1 incident (MTTR) | < 20 minutes | Monthly |
| Stock variance rate (unexplained) | < 0.5% by value | Weekly |
