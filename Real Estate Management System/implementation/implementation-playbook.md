# Real Estate Management System — Implementation Playbook

## Overview

This playbook is the authoritative guide for engineers developing, testing, and operating the Real Estate Management System (REMS). All engineers onboarding to the project must complete the local setup steps in order and verify a running stack before opening their first pull request.

REMS manages the full real-estate operations lifecycle: property listings, tenant screening, lease creation and renewal, maintenance work orders, rent collection via Stripe Connect, and the landlord owner portal. The backend is built in **Node.js 20 / TypeScript**, persisted in **PostgreSQL 15**, cached and queued via **Redis 7**, with **Stripe Connect** for landlord payouts, **SendGrid** for transactional email, and **MinIO/S3** for document storage. The platform is deployed on **Kubernetes (EKS, AWS)** and managed with Helm and ArgoCD.

---

## Prerequisites and Local Setup

### Required Tools

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Node.js | 20 LTS | `nvm install 20 && nvm use 20` |
| Docker Desktop | 4.x | https://docs.docker.com/desktop/ |
| kubectl | 1.28 | `brew install kubectl` |
| Helm | 3.13 | `brew install helm` |
| Flyway CLI | 9.x | `brew install flyway` |
| Stripe CLI | Latest | `brew install stripe/stripe-cli/stripe` |
| AWS CLI | v2 | `brew install awscli` |

Verify versions before proceeding:

```bash
node --version && docker --version && kubectl version --client && flyway -v && stripe version
```

### Environment Variables

Copy `.env.example` to `.env.local` and fill in every value. The table below documents each variable's purpose and where to obtain it.

| Variable | Purpose | Source |
|----------|---------|--------|
| `DATABASE_URL` | PostgreSQL connection string | docker-compose default: `postgresql://rems:rems_local@localhost:5432/rems_development` |
| `REDIS_URL` | Redis connection string | docker-compose default: `redis://localhost:6379` |
| `STRIPE_SECRET_KEY` | Stripe API key (test mode) | Stripe Dashboard → Developers → API Keys |
| `STRIPE_PUBLISHABLE_KEY` | Client-side Stripe key | Stripe Dashboard |
| `STRIPE_CONNECT_WEBHOOK_SECRET` | Webhook signature verification | Output of `stripe listen` |
| `STRIPE_CONNECT_CLIENT_ID` | OAuth client for Connect onboarding | Stripe Dashboard → Connect → Settings |
| `SENDGRID_API_KEY` | Transactional email | SendGrid Dashboard → API Keys |
| `GOOGLE_MAPS_API_KEY` | Geocoding and address validation | Google Cloud Console |
| `S3_ENDPOINT` | Document storage endpoint | `http://localhost:9000` for local MinIO |
| `S3_BUCKET` | Storage bucket name | `rems-documents-local` |
| `AWS_REGION` | AWS region for EKS and SES | `us-east-1` |
| `JWT_SECRET` | JWT signing secret (≥32 chars) | Generate: `openssl rand -hex 32` |

All production secrets are injected from **AWS Secrets Manager** via the External Secrets Operator. Never commit real credentials to source control.

---

## Running the Stack Locally

### docker-compose Services

The `docker-compose.yml` at the repo root provisions all infrastructure dependencies:

| Service | Port(s) | Purpose |
|---------|---------|---------|
| `postgres` | 5432 | Primary database |
| `redis` | 6379 | Cache, job queues, session store |
| `minio` | 9000 / 9001 | S3-compatible document storage |
| `mailhog` | 1025 / 8025 | SMTP sink for local email testing |

```bash
# Start all infrastructure
docker-compose up -d

# Install Node dependencies
npm install

# Apply all Flyway migrations
npm run migrate

# Seed reference data in order (each seed is idempotent)
npm run seed:landlords    # 5 landlords with Stripe Connect test accounts
npm run seed:properties   # 20 properties spread across 3 landlords
npm run seed:units        # 2–6 units per property with varying status
npm run seed:tenants      # 30 tenants with mixed application states

# Start the API with hot-reload
npm run dev
```

### Verifying the Stack

```bash
# API health (expects 200)
curl http://localhost:3000/health
# {"status":"ok","db":"connected","redis":"connected","storage":"connected"}

# MinIO console
open http://localhost:9001    # minioadmin / minioadmin

# MailHog inbox
open http://localhost:8025
```

### Common Local Issues

| Problem | Resolution |
|---------|-----------|
| Postgres port 5432 already in use | `lsof -ti :5432 \| xargs kill` or change the mapped port in docker-compose |
| Migration fails with "schema already exists" | Run `npm run migrate:repair` then retry |
| MinIO bucket not found | Run `npm run storage:init` which creates required buckets |
| Seed fails on unique constraint | Seeds are idempotent; run `npm run db:reset` to truncate and re-seed |

---

## Feature Development Workflow

### Branch Naming

All branches must follow `<type>/JIRA-XXX-short-description`:

- `feature/REMS-123-lease-renewal-notifications`
- `bugfix/REMS-456-stripe-webhook-idempotency`
- `hotfix/REMS-789-payment-double-charge`
- `chore/REMS-101-update-node-dependencies`

### Pull Request Requirements

Every PR must include:

1. Link to the JIRA ticket in the PR description
2. Summary of the change and the reasoning behind it
3. Test coverage for all new code paths (minimum **80% line coverage** for changed files)
4. Migration script if the change touches the database schema
5. Updated OpenAPI spec if new endpoints are added or request/response shapes changed
6. Green CI pipeline before requesting review

### Required Reviewers

PRs touching any of the following require review from the **property-domain team** (@rems/property-domain):

- `src/leases/`
- `src/payments/`
- `src/tenants/screening/`
- `src/properties/listings/`
- `db/migrations/`

All other PRs require at least one approval from any team member. Squash-merge only; feature branches are deleted after merge.

---

## Database Migration Workflow

REMS uses **Flyway** for schema migrations. All migration files live in `db/migrations/`.

### File Naming

```
V{timestamp}__{description}.sql
```

Generate the timestamp:

```bash
date "+%Y%m%d_%H%M%S"
# Example output: 20240315_143022
# Resulting filename: V20240315_143022__add_lease_renewal_reminder_table.sql
```

### Migration Policy

**Additive-only**: The live production application may be running against the migrated schema before old pods are fully rotated out. Migrations must never remove or rename columns the current production code still reads. Use the two-phase pattern:

- **Phase 1 migration**: Add new nullable column or new table, deploy application code that writes to both old and new columns.
- **Phase 2 migration** (next sprint or after full rollout): Backfill data, add NOT NULL constraint, drop deprecated column.

**Blue-green safe**: Both old and new application versions must be able to operate correctly while the migration is applied.

**No data manipulation in DDL files**: Data backfills belong in separate `R__` repeatable migration files or standalone scripts.

### Running Migrations

```bash
npm run migrate              # Apply all pending migrations
npm run migrate:info         # Show applied vs. pending migrations
npm run migrate:validate     # Validate checksums of applied migrations
npm run migrate:repair       # Clear failed migration state (use with care)
```

---

## Stripe Connect Integration Testing

### Test Mode Setup

1. Log in to the Stripe Dashboard and switch to **Test Mode**.
2. Enable Stripe Connect and set the redirect URI to `http://localhost:3000/landlords/stripe/callback`.
3. Copy `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, and `STRIPE_CONNECT_CLIENT_ID` to `.env.local`.

### Webhook Forwarding

```bash
stripe listen \
  --forward-to localhost:3000/webhooks/stripe \
  --events payment_intent.succeeded,payment_intent.payment_failed,\
account.updated,transfer.created,transfer.failed,\
charge.dispute.created,charge.dispute.closed
```

Copy the signing secret printed by `stripe listen` into `STRIPE_CONNECT_WEBHOOK_SECRET`.

### Test Landlord Onboarding Flow

```bash
# 1. Seed a test landlord
npm run seed:landlords

# 2. Start the Stripe Connect OAuth flow
open "http://localhost:3000/landlords/stripe/onboard?landlordId=test-landlord-1"

# 3. Complete onboarding in the Stripe test UI
#    SSN: 000-00-0000
#    Bank account: 000123456789  Routing: 110000000

# 4. Verify account.updated webhook received in API logs
# 5. Check MailHog for "Payout account connected" confirmation email
```

### Test Payment Scenarios

| Scenario | Test Card / Account |
|----------|-------------------|
| Successful ACH payment | Account `000123456789`, routing `110000000` |
| Payment failure — insufficient funds | Account `000111111113` |
| Payment disputed | Trigger via `stripe payment_intents trigger payment_intent.payment_failed` |

---

## Lease State Machine Testing

REMS leases follow a strict finite state machine. Every transition must be covered by unit tests before merging.

```
draft → pending_signature → active → renewal_pending → active
                                   → termination_pending → terminated
                                   → expired
```

### Unit Tests

```bash
npm run test -- --testPathPattern="lease-state-machine"
```

Tests live in `src/leases/__tests__/lease-state-machine.test.ts` and cover every valid transition and every invalid transition (which should throw a `LeaseTransitionError`).

### Property-Based Tests

REMS uses **fast-check** for property-based testing. Tests in `src/leases/__tests__/lease-properties.test.ts` assert the following invariants across randomly generated lease data:

- A lease can never move from `draft` directly to `active` without passing through `pending_signature`.
- A `terminated` lease can never be reactivated.
- `security_deposit_amount` is always ≥ 0 and ≤ 3× `monthly_rent`.
- `end_date` is always strictly after `start_date`.
- A lease in `renewal_pending` must return to `active` or move to `expired`; it cannot move to `terminated` without passing through `termination_pending`.

```bash
npm run test -- --testPathPattern="lease-properties"
```

---

## CI/CD Pipeline

Every push to a feature branch triggers the following pipeline in GitHub Actions:

```
lint → test → build → scan → push → deploy-staging → e2e → promote-prod
```

| Stage | Tool | On Failure |
|-------|------|-----------|
| lint | ESLint + Prettier | Block merge |
| test | Jest (unit + integration) | Block merge |
| build | Docker multi-stage | Block merge |
| scan | Trivy (container), Snyk (deps) | Block if CRITICAL CVE |
| push | Amazon ECR | Auto on `main` only |
| deploy-staging | Helm + ArgoCD | Auto on `main` only |
| e2e | Playwright against staging | Block production promotion |
| promote-prod | ArgoCD sync | Manual approval required |

### Rollback Procedure

```bash
# ArgoCD rollback to the previous revision
argocd app rollback rems-production --revision <previous-revision>

# Verify rollback is healthy
argocd app wait rems-production --health --timeout 120

# If a migration must also be rolled back (only if undo scripts exist)
npm run migrate:undo
```

---

## Monitoring and Alerting

### Key Metrics (Prometheus + Grafana)

| Metric | Type | Alert Threshold |
|--------|------|----------------|
| `rent_payment_success_rate` | Gauge | < 99% over 5 min → P1 |
| `maintenance_sla_breach_count` | Counter | > 5 per hour → P2 |
| `lease_renewal_rate` | Gauge | < 60% monthly → P3 |
| `stripe_webhook_processing_latency_p99` | Histogram | > 10 s → P2 |
| `background_check_queue_depth` | Gauge | > 100 pending → P3 |
| `db_connection_pool_utilization` | Gauge | > 85% → P2 |
| `search_index_lag_seconds` | Gauge | > 300 s → P3 |

### Grafana Dashboards

All dashboards are maintained as code in `infra/grafana/dashboards/`:

- `payments-overview.json` — Rent collection rates, payout timing, Stripe webhook latency
- `lease-operations.json` — Active leases, renewals, upcoming expirations, occupancy rate
- `maintenance-ops.json` — Open work orders by SLA tier, resolution time P50/P95
- `platform-health.json` — API error rates, database pool utilization, Redis memory

---

## Incident Runbook

### P1: Payment Processing Down

**Symptoms**: `rent_payment_success_rate` drops below 95%, or the Stripe webhook endpoint is returning 5xx errors.

**Immediate Actions**:
1. Check https://status.stripe.com for upstream incidents.
2. Inspect API server logs: `kubectl logs -l app=rems-api -n production --since=10m | grep -i stripe`
3. Verify Redis connectivity (idempotency keys are stored here).
4. Check the `payments` circuit breaker status in the `/admin/circuit-breakers` internal endpoint.
5. Roll back the last deployment if the issue coincides with a recent release.

**Resolution**: After restoring service, run the reconciliation job to detect any timed-out payments: `kubectl exec -it <rems-jobs-pod> -- npm run jobs:reconcile-payments`

---

### P2: Lease Renewal Job Failed

**Symptoms**: `lease_renewal_batch_last_success` metric is stale; renewal notification emails not delivered.

**Immediate Actions**:
1. Check pod logs: `kubectl logs -l app=rems-jobs -n production --since=1h | grep "lease-renewals"`
2. Identify unprocessed leases:
   ```sql
   SELECT id, unit_id, end_date FROM leases
   WHERE renewal_notified_at IS NULL
     AND end_date BETWEEN NOW() AND NOW() + INTERVAL '60 days'
     AND status = 'active';
   ```
3. Manually trigger the job: `kubectl exec -it <rems-jobs-pod> -- npm run jobs:lease-renewals`
4. Verify delivery via SendGrid Activity log.

---

### P3: Maintenance SLA Breach Spike

**Symptoms**: `maintenance_sla_breach_count` exceeds threshold within a 1-hour window.

**Immediate Actions**:
1. Query breached orders: `SELECT * FROM work_orders WHERE sla_deadline < NOW() AND status != 'completed' ORDER BY sla_deadline ASC;`
2. Notify affected property managers via in-app alert and email.
3. Check whether the vendor dispatch API integration is degraded.
4. Determine if a bulk import caused dispatch queue backup.

---

### P4: Listing Sync Delay

**Symptoms**: Search results do not reflect recent property updates; `search_index_lag_seconds` gauge is elevated.

**Immediate Actions**:
1. Check OpenSearch cluster health: `curl -u admin:admin https://opensearch.internal/_cluster/health`
2. Verify the listing-sync worker pod is running: `kubectl get pods -l app=rems-listing-sync -n production`
3. Trigger a manual re-index: `kubectl exec -it <rems-jobs-pod> -- npm run jobs:reindex-listings`
4. If the cluster is degraded, enable the PostgreSQL full-text search fallback: set feature flag `SEARCH_FALLBACK_POSTGRES=true` in the feature flag service.
