# Implementation Playbook

## Overview

This playbook is the single authoritative guide for engineers joining the Fleet Management System project. It covers everything from setting up a local development environment to deploying changes to production. Follow each section in order for a first-time setup. Experienced contributors can jump directly to the relevant section.

The system is composed of nine Node.js/TypeScript microservices, each independently deployable. All services share a common scaffolding structure, a unified CI/CD pipeline, and a central observability stack. The playbook assumes familiarity with Docker, Kubernetes, and TypeScript but does not require prior experience with the specific tools in this stack.

---

## Prerequisites and Local Setup

### Required Tools

Install the following tools before cloning the repository. Version requirements are strict; mismatches cause build failures.

| Tool | Required Version | Installation |
|---|---|---|
| Node.js | 20.x LTS | `nvm install 20 && nvm use 20` |
| npm | 10.x | Included with Node.js 20 |
| Docker Desktop | 4.28+ | https://www.docker.com/products/docker-desktop |
| kubectl | 1.29.x | `brew install kubectl` |
| Helm | 3.14.x | `brew install helm` |
| AWS CLI | 2.15.x | `brew install awscli` |
| k9s (optional) | Latest | `brew install k9s` |
| Flyway CLI | 10.x | `brew install flyway` |

### Repository Setup

```bash
git clone git@github.com:your-org/fleet-management-system.git
cd fleet-management-system
npm install          # installs root-level tooling (turborepo, eslint, prettier)
npm run bootstrap    # installs dependencies for all services via turborepo
```

### Environment Variables

Copy the provided template and populate values from the team's secrets manager (AWS Secrets Manager, `fleet/dev` path):

```bash
cp .env.example .env.local
```

Required variables:

| Variable | Description | Example Value |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (RDS or local Docker) | `postgresql://fleet:secret@localhost:5432/fleet_dev` |
| `TIMESCALEDB_URL` | TimescaleDB connection string | `postgresql://fleet:secret@localhost:5433/timescale_dev` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `KAFKA_BROKERS` | Comma-separated Kafka broker list | `localhost:9092` |
| `MQTT_BROKER_URL` | MQTT broker endpoint | `mqtt://localhost:1883` |
| `GOOGLE_MAPS_API_KEY` | Google Maps Directions + Geocoding API key | `AIza...` |
| `HERE_MAPS_API_KEY` | HERE Maps Routing API key | `abc123...` |
| `SENDGRID_API_KEY` | SendGrid mail API key | `SG.xxx...` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `ACxxx...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `xxx...` |
| `JWT_SECRET` | HS256 signing secret for local dev | `dev-secret-do-not-use-in-prod` |
| `AWS_REGION` | AWS region for SDK calls | `us-east-1` |
| `S3_GPS_ARCHIVE_BUCKET` | S3 bucket for GPS archive | `fleet-gps-archive-dev` |

---

## Running the Stack Locally

### Starting Infrastructure with Docker Compose

The `docker-compose.yml` at the repository root starts all infrastructure dependencies. Application services run via Node.js outside Docker for faster iteration.

```bash
docker compose up -d
```

Services started:

| Service | Port | Notes |
|---|---|---|
| PostgreSQL 15 | `5432` | Database: `fleet_dev`; credentials: `fleet/secret` |
| TimescaleDB 2.14 | `5433` | Separate container; TimescaleDB extension pre-enabled |
| Redis 7 | `6379` | No auth in local dev |
| Zookeeper | `2181` | Required by Kafka local cluster |
| Kafka (Bitnami) | `9092` | Single broker for local dev |
| MQTT Broker (Mosquitto) | `1883` | No TLS in local dev; TLS available on `8883` with self-signed cert |
| Kafka UI | `8080` | Browse topics and consumer groups at http://localhost:8080 |
| RedisInsight | `8001` | Redis GUI at http://localhost:8001 |

### Running Database Migrations

Migrations must be applied before starting any service:

```bash
npm run migrate:dev
# equivalent to: flyway -url=jdbc:postgresql://localhost:5432/fleet_dev migrate
```

### Seeding Reference Data

```bash
npm run seed:fleet      # creates default tenant, 5 vehicles, 3 drivers
npm run seed:geofences  # creates warehouse and depot geofences for the default tenant
npm run seed:routes     # creates 3 sample routes with waypoints
```

### Starting Services

Each service can be started individually or all at once:

```bash
# Start all services with hot reload
npm run dev

# Start a single service
cd services/tracking-service && npm run dev
```

Service ports follow the pattern `300{n}`:

| Service | Port |
|---|---|
| Tracking Service | `3001` |
| Trip Service | `3002` |
| Maintenance Service | `3003` |
| Driver Service | `3004` |
| Fuel Service | `3005` |
| Compliance Service | `3006` |
| Reporting Service | `3007` |
| Alert Service | `3008` |
| Notification Service | `3009` |

---

## Service Development Guide

### Adding a New Service

Follow these steps to scaffold a new microservice consistently:

**Step 1 — Scaffold from template**

```bash
npm run scaffold:service -- --name=my-new-service
```

This creates `services/my-new-service/` with the standard structure:

```
services/my-new-service/
├── src/
│   ├── controllers/       # Express.js route handlers
│   ├── application/       # Application services (orchestrators)
│   ├── domain/            # Domain entities, value objects, state machines
│   ├── infrastructure/    # Repositories, Kafka producers/consumers, external clients
│   ├── config/            # Environment variable validation (zod)
│   └── index.ts           # Express app bootstrap
├── test/
│   ├── unit/
│   └── integration/
├── migrations/            # Flyway SQL migrations owned by this service
├── Dockerfile
├── helm/                  # Helm chart for this service
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
└── package.json
```

**Step 2 — Register Kafka topics**

Add any new topics to `infrastructure/kafka/topic-registry.yaml` and apply:

```bash
npm run kafka:topics:apply -- --env=local
```

**Step 3 — Register API Gateway route**

Add a route block to `infrastructure/kong/routes.yaml`:

```yaml
- name: my-new-service
  paths: ["/api/v1/my-new"]
  service: my-new-service
  plugins:
    - name: jwt
    - name: rate-limiting
      config:
        minute: 1000
```

Apply with: `kubectl apply -f infrastructure/kong/routes.yaml`

**Step 4 — Implement health endpoints**

Every service must expose:
- `GET /health/live` — returns `200 { status: "ok" }` if the process is running
- `GET /health/ready` — returns `200 { status: "ok" }` when database and Kafka connections are healthy; `503` otherwise

**Step 5 — Helm chart and Kubernetes deployment**

The scaffold generates a Helm chart. Update `helm/values.yaml` with the correct image name, resource requests, and environment variable references to Kubernetes Secrets. Deploy to local cluster (if using kind/minikube):

```bash
helm upgrade --install my-new-service ./services/my-new-service/helm \
  --namespace fleet \
  --values ./services/my-new-service/helm/values.local.yaml
```

---

## Database Migration Workflow

All schema changes are managed with Flyway. Each service owns its migrations in its own `migrations/` directory. The CI pipeline applies migrations from all services in dependency order before deploying new service versions.

### Naming Convention

```
V{YYYYMMDDHHmmss}__{snake_case_description}.sql
```

Examples:
- `V20240315143022__create_trips_table.sql`
- `V20240401090000__add_vehicle_telematics_columns.sql`
- `V20240510120000__create_maintenance_work_orders_table.sql`

### Writing Migrations

- Always include a `-- Description:` comment at the top of each file
- Create indexes in a separate migration from the table creation (allows `CREATE INDEX CONCURRENTLY` in production)
- Never use `DROP TABLE` or `DROP COLUMN` in a migration without a corresponding deprecation period; use `ALTER TABLE ... RENAME COLUMN` with a compatibility view instead
- All migrations must be backwards compatible with the currently deployed service version (expand-contract pattern)

### Pre-Deploy Migration Check

The CI pipeline runs this check before any service deployment:

```bash
flyway validate -url=${DATABASE_URL}
```

If the check fails (e.g., a migration was edited after being applied), the deployment is blocked and the on-call engineer is paged.

### Rollback Strategy

Flyway does not support automatic rollback. To roll back a migration:
1. Write a new forward migration that reverses the change
2. Name it with a later timestamp: `V{later_timestamp}__rollback_previous_change.sql`
3. Deploy the rollback migration via the normal CI pipeline

For emergency rollbacks in production, the DBA runbook (in `docs/runbooks/database.md`) covers manual pg_dump/restore procedures.

---

## GPS Simulator

The GPS simulator generates realistic vehicle movement for local testing without requiring physical devices. It produces MQTT messages on the same topic structure as production devices.

### Running the Simulator

```bash
npm run simulate-gps -- --vehicles=10 --interval=5s
```

| Flag | Default | Description |
|---|---|---|
| `--vehicles` | `5` | Number of simulated vehicles to generate pings for |
| `--interval` | `5s` | Ping interval per vehicle (e.g., `1s`, `5s`, `30s`) |
| `--tenant` | `default` | Tenant ID to simulate pings for |
| `--route` | `random` | Route file from `simulator/routes/`; `random` picks a random pre-defined route |
| `--broker` | `mqtt://localhost:1883` | MQTT broker URL |
| `--speed-violations` | `false` | Inject random speed violations every 60 seconds |
| `--geofence-exits` | `false` | Simulate vehicles exiting configured geofences |

The simulator prints a summary line per vehicle every 10 pings:

```
[SIM] Vehicle veh-001 | Pings: 10 | Lat: 40.7128 Lon: -74.0060 | Speed: 55 mph | Route: NYC→Newark
```

To test the full pipeline end-to-end, start the stack, run migrations, seed data, start all services, then run the simulator. Open the Kafka UI at http://localhost:8080 and watch messages flowing through `gps.pings.raw` and `fleet.tracking.processed`.

---

## CI/CD Pipeline

The pipeline runs on GitHub Actions and is defined in `.github/workflows/ci-cd.yml`. Every push to a feature branch runs the full pipeline except the production deploy stage.

### Pipeline Stages

| Stage | Trigger | Tool | Pass Criteria |
|---|---|---|---|
| **Lint** | Every push | ESLint + Prettier | Zero lint errors; formatting diff is empty |
| **Type Check** | Every push | TypeScript `tsc --noEmit` | Zero type errors across all services |
| **Unit Tests** | Every push | Jest | All unit tests pass; coverage ≥80% per service |
| **Integration Tests** | Every push | Jest + Testcontainers | All integration tests pass with real PostgreSQL + Kafka containers |
| **Build Docker Images** | `main` branch + PR | Docker BuildKit (multi-stage) | Images build successfully; no layer cache misses on unchanged layers |
| **Security Scan** | `main` branch + PR | Trivy (image) + npm audit | No critical CVEs in image layers; no high-severity npm vulnerabilities |
| **Push to ECR** | `main` branch | AWS CLI | Images tagged with Git SHA and pushed to ECR |
| **Deploy to Staging** | `main` branch | Helm + kubectl | All Helm releases upgrade without error; all pods reach `Running` state within 5 minutes |
| **Smoke Tests** | After staging deploy | k6 smoke test script | Health endpoints return 200; GPS ping ingest end-to-end test completes in <30s |
| **Promote to Production** | Manual approval | Helm + kubectl (with PodDisruptionBudget) | Rolling update completes; zero 5xx errors in CloudWatch during rollout |

### Deployment Strategy

Services are deployed with a **RollingUpdate** strategy: `maxSurge: 1`, `maxUnavailable: 0`. This ensures at least the current replica count is always available during a rollout. Database migrations are applied as a Kubernetes Job before the service deployment is initiated, using an `initContainer` that runs `flyway migrate`.

### Rollback

To roll back a production deployment:

```bash
helm rollback {service-name} -n fleet
# Example: helm rollback tracking-service -n fleet
```

Helm retains the last 10 release revisions. For database rollback, refer to the Database Migration Rollback section above.

---

## Monitoring Setup

### Prometheus Metrics

Each service exposes Prometheus metrics at `GET /metrics`. The following custom metrics are defined across the fleet:

| Metric | Type | Service | Alert Threshold |
|---|---|---|---|
| `gps_ping_rate` | Gauge (pings/sec) | Tracking | Alert if <10/sec for >2 min (device connectivity issue) |
| `gps_ping_processing_latency_ms` | Histogram | Tracking | p99 >500ms triggers P2 alert |
| `trip_active_count` | Gauge | Trip | No threshold; informational dashboard metric |
| `trip_completion_rate` | Counter | Trip | Alert if completion rate drops >20% vs 24h baseline |
| `hos_violation_count` | Counter (per tenant) | Driver | Alert if >5 violations/hour for a single tenant |
| `maintenance_overdue_count` | Gauge (per tenant) | Maintenance | Alert if >10% of fleet is overdue |
| `kafka_consumer_lag` | Gauge (per topic/group) | All services | Alert if >50,000 messages for sustained 5 min |
| `notification_delivery_failure_rate` | Counter | Notification | Alert if failure rate >5% in rolling 10-min window |
| `geofence_breach_count` | Counter (per tenant) | Tracking | Informational; used in tenant dashboard |
| `api_request_duration_ms` | Histogram (by route) | All services | p99 >2000ms triggers P3 alert |

### Grafana Dashboard Setup

Grafana is deployed to the `monitoring` namespace in EKS. Dashboards are provisioned as code via ConfigMaps in `infrastructure/grafana/dashboards/`:

```bash
kubectl apply -f infrastructure/grafana/dashboards/ -n monitoring
```

Pre-built dashboards:
- **Fleet Overview** — active trips, vehicle states, GPS ping rate, HOS violations
- **GPS Pipeline Health** — Kafka consumer lag, ping processing latency, dead-letter queue depth
- **Service SLOs** — p50/p95/p99 API latency per service, error rates, availability
- **Infrastructure** — EKS node CPU/memory, RDS connections, TimescaleDB chunk sizes, Redis hit rate

### Alert Thresholds and Routing

Alertmanager routes alerts to PagerDuty based on severity:

| Severity | Definition | Response Target | Example |
|---|---|---|---|
| P1 | Complete loss of a core capability | On-call engineer in <5 min | All GPS tracking down; API gateway returning 5xx for >50% of requests |
| P2 | Significant degradation, partial data loss risk | On-call engineer in <30 min | Kafka consumer lag >50,000; TimescaleDB write errors >1% |
| P3 | Performance degradation, no data loss | Engineering team in <2 hours | API p99 latency >2s; maintenance overdue count spike |
| P4 | Informational anomaly | Next business day | Report generation >5 min; GPS archive compaction delayed |

---

## Incident Runbook

### P1 — All GPS Tracking Down

**Symptoms:** Live map shows no vehicle positions updating; `gps_ping_rate` drops to zero; IoT Core CloudWatch metric `PublishIn.Success` is flat.

**Diagnosis steps:**
1. Check AWS IoT Core Service Health Dashboard for regional outage
2. Check MSK broker status: `aws kafka describe-cluster --cluster-arn ${MSK_ARN}`
3. Check Tracking Service pod logs: `kubectl logs -l app=tracking-service -n fleet --tail=100`
4. Check Kafka consumer group lag: open Kafka UI at internal ALB → Consumer Groups → `tracking-service-gps-consumer`
5. Verify IoT Core Rule is enabled: AWS Console → IoT Core → Message Routing → Rules → `gps-to-kafka-rule`

**Resolution paths:**
- If IoT Core outage: devices will reconnect automatically; pings are buffered on device; monitor MSK lag as messages drain
- If MSK down: scale down Tracking Service to prevent connection thrash; restore MSK; scale back up
- If Tracking Service pods crashing: check for OOM (`kubectl describe pod`); increase memory limit in Helm values and redeploy

### P2 — Kafka Consumer Lag >50,000

**Symptoms:** `kafka_consumer_lag` Prometheus metric exceeds threshold; Grafana GPS Pipeline Health dashboard shows growing lag on `gps.pings.raw`.

**Diagnosis steps:**
1. Check if Tracking Service pods are healthy: `kubectl get pods -l app=tracking-service -n fleet`
2. Check TimescaleDB write latency: query `pg_stat_activity` on TimescaleDB for long-running writes
3. Check if lag is growing or stable: a stable high lag may self-resolve; growing lag requires immediate action
4. Review pod CPU/memory usage in Grafana Service SLOs dashboard

**Resolution paths:**
- Scale up Tracking Service replicas: `kubectl scale deployment tracking-service --replicas=10 -n fleet`
- If TimescaleDB writes are slow: check `gps_pings` hypertable chunk compression is not running during peak hours; defer compression job if needed
- If a single partition has disproportionate lag, check partition key distribution for hot-partition issue

### P3 — Maintenance Overdue Count Spike

**Symptoms:** `maintenance_overdue_count` metric increases sharply; fleet managers receive bulk overdue notifications.

**Diagnosis steps:**
1. Query PostgreSQL: `SELECT COUNT(*) FROM maintenance_records WHERE status = 'overdue' AND tenant_id = $1;`
2. Check if `ScheduleEngine` cron job ran correctly: `kubectl logs -l app=maintenance-service -n fleet | grep "ScheduleEngine"`
3. Verify the spike is real (actual overdue records) vs. a metrics/alerting bug

**Resolution paths:**
- If legitimate spike (e.g., after a fleet import): notify fleet managers; bulk-schedule maintenance via API batch endpoint `POST /maintenance/bulk-schedule`
- If cron job bug: manually trigger schedule evaluation via `POST /internal/maintenance/run-schedule-check` (internal admin endpoint)

### P4 — Report Generation Slow

**Symptoms:** Fleet managers report reports taking >5 minutes; Reporting Service logs show slow TimescaleDB queries; SQS queue depth for report jobs is growing.

**Diagnosis steps:**
1. Check active queries on TimescaleDB: `SELECT query, duration FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;`
2. Check if continuous aggregates are stale: `SELECT view_name, last_run_started_at FROM timescaledb_information.continuous_aggregate_stats;`
3. Check Reporting Service pod count and CPU utilization in Grafana

**Resolution paths:**
- If TimescaleDB queries are slow: run `ANALYZE gps_pings;` to refresh statistics; refresh continuous aggregates manually: `CALL refresh_continuous_aggregate('gps_hourly_summary', NULL, NULL);`
- If SQS queue depth is growing: scale Reporting Service replicas: `kubectl scale deployment reporting-service --replicas=4 -n fleet`
- If a single large report is blocking others: identify the job via SQS message attributes; cancel and re-queue via admin endpoint
