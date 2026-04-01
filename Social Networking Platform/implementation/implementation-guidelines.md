# Implementation Guidelines — Social Networking Platform

## 1. Technology Stack

### 1.1 Backend Services

| Service | Language | Framework | Rationale |
|---------|----------|-----------|-----------|
| User Service | Go 1.22 | Gin + GORM | Fast auth token validation, low memory footprint; handles 50k req/s per pod |
| Profile Service | Go 1.22 | Gin + GORM | Similar profile to User; shares Go module monorepo |
| Social Graph Service | Go 1.22 | Gin + pgx | High-throughput follow/unfollow; direct pgx for bulk graph queries without ORM overhead |
| Post Service | Go 1.22 | Gin + GORM | Write-heavy with fan-out; goroutines for async Kafka publishing |
| Media Service | Go 1.22 | Gin | S3 presigned URL generation, multipart upload orchestration |
| Feed Service | Python 3.12 | FastAPI | ML model integration with SageMaker SDK; numpy/pandas for score aggregation |
| Notification Service | Go 1.22 | Gin + Kafka consumer | Event-driven; goroutine worker pool for APNs/FCM delivery |
| Messaging Service | Go 1.22 | Gin + Gorilla WebSocket | Long-lived WebSocket connections; actor-model message routing |
| Community Service | Go 1.22 | Gin + GORM | CRUD-heavy with moderator permission checks |
| Moderation Service | Python 3.12 | FastAPI | Rekognition + Comprehend SDK calls; async task queue via Celery |
| Ad Service | Go 1.22 | Gin | Low-latency ad selection; Vickrey auction in-process |
| Analytics Service | Python 3.12 | FastAPI + Pandas | Aggregation queries against Timestream; report generation |
| Search Service | Go 1.22 | Gin + opensearch-go | Query building, autocomplete, multi-index fan-out |
| Story Service | Go 1.22 | Gin + GORM | TTL-based media management; view tracking via DynamoDB |

### 1.2 Frontend

| Layer | Technology | Notes |
|-------|-----------|-------|
| Web App | Next.js 14 (App Router) | Server Components for feed SSR; Client Components for real-time updates |
| State Management | Zustand + React Query v5 | Server state via React Query; client-only UI state via Zustand |
| Styling | Tailwind CSS 3.x + shadcn/ui | Design system built on Radix UI primitives |
| Real-time | Native WebSocket (Messaging) + Server-Sent Events (notifications) | No Socket.io to reduce bundle size |
| Media Upload | Uppy + AWS S3 Multipart | Direct browser-to-S3 upload using presigned multipart URLs |
| Mobile Web | PWA with service worker | Offline feed cache using Background Sync API |
| iOS | Swift 5.9, SwiftUI, Combine | Async/await for all networking; Core Data for offline draft posts |
| Android | Kotlin 1.9, Jetpack Compose, Coroutines | Retrofit 2 + OkHttp for networking; Room for local cache |

### 1.3 Data Stores

| Store | Version | Driver/Client |
|-------|---------|---------------|
| PostgreSQL | 16.x | pgx v5 (Go), asyncpg (Python) |
| Redis | 7.2 Cluster | go-redis v9, redis-py 5.x |
| DynamoDB | — | AWS SDK Go v2, boto3 |
| OpenSearch | 2.x | opensearch-go v4, opensearch-py |
| Kafka (MSK) | 3.5 | confluent-kafka-go, confluent-kafka-python |
| S3 | — | AWS SDK Go v2, boto3 |
| Timestream | — | AWS SDK Go v2, boto3 |

### 1.4 Infrastructure

| Component | Technology |
|-----------|-----------|
| Container Orchestration | AWS EKS 1.29, Karpenter node autoscaling |
| Service Mesh | Istio 1.20 (mTLS, circuit breaking, traffic management) |
| GitOps | ArgoCD 2.10 |
| IaC | Terraform 1.7 + Terragrunt for environment overlays |
| Container Registry | Amazon ECR with automated vulnerability scanning |
| Secrets | AWS Secrets Manager + External Secrets Operator |
| CI | GitHub Actions (build, test, scan, push) |
| Observability | Prometheus + Grafana + Loki + Jaeger (via X-Ray OTLP bridge) |

---

## 2. Coding Standards

### 2.1 General Principles

- **Immutable data transfer objects:** All API request/response structs are read-only after
  construction. No mutations after binding from HTTP body.
- **Explicit error handling:** Errors are never silently swallowed. Every error either returns
  to the caller, is logged with context, or is published to a dead-letter topic.
- **Dependency injection:** All service dependencies (DB, Redis, Kafka producer) are injected
  via constructors. No global variables for infrastructure clients.
- **Context propagation:** `context.Context` is the first parameter of every function that
  performs I/O. Contexts carry request IDs, authenticated user IDs, and OpenTelemetry spans.
- **Module boundaries:** Each microservice is a separate Go module or Python package. Shared
  utilities (JWT parsing, pagination helpers, Kafka schema types) live in `pkg/` under the
  monorepo root and are versioned independently.

### 2.2 API Design Standards

**REST conventions:**
- Resource URLs use plural nouns: `/users`, `/posts`, `/communities`.
- Nested resources limited to two levels: `/posts/{postId}/comments`. Deeper nesting is
  replaced with query parameters: `GET /comments?postId={postId}&parentId={commentId}`.
- HTTP methods map strictly: `POST` = create, `GET` = read, `PUT` = full replace,
  `PATCH` = partial update, `DELETE` = soft delete.
- Response envelope for collections:
  ```json
  {
    "data": [...],
    "pagination": {
      "cursor": "base64-encoded-cursor",
      "hasMore": true,
      "total": null
    }
  }
  ```
- Cursor-based pagination everywhere. Offset pagination is prohibited for large tables.
- HTTP status codes: `200` success, `201` created, `204` no content (delete), `400` client
  error (validation), `401` unauthenticated, `403` forbidden, `404` not found, `409` conflict,
  `422` unprocessable entity (business logic rejection), `429` rate limited, `500` server error.
- Error response format:
  ```json
  {
    "error": {
      "code": "POST_NOT_FOUND",
      "message": "The requested post does not exist or has been deleted.",
      "requestId": "req_01HX..."
    }
  }
  ```

**gRPC (internal service-to-service):**
- Proto files live in `proto/` at monorepo root. Proto3 syntax only.
- All RPC methods use `request_id` and `caller_service` fields in request messages.
- Deadline propagation: every gRPC call sets a deadline inherited from the incoming HTTP
  request context with a 20% reduction floor of 100ms.

**Versioning:**
- URL path versioning: `/v1/`, `/v2/`. Breaking changes require a new version.
- Old versions deprecated with `Sunset` response header (RFC 8594) pointing to migration guide.
  Minimum 6-month deprecation period before removal.

### 2.3 Database Access Patterns

- **Connection pooling:** pgx pool with `MaxConns = 25`, `MinConns = 5`, `MaxConnLifetime = 1h`,
  `MaxConnIdleTime = 30m` per service instance.
- **Read/write split:** All mutation queries route to the primary RDS instance. All read queries
  route to read replica. Read replica connection string is injected via environment variable.
- **Query guidelines:**
  - All queries must use parameterized inputs. String interpolation in SQL is a compile-time error
    caught by the `sqlvet` linter in CI.
  - Queries expected to return large result sets must use keyset pagination with a `LIMIT`.
  - Explain-Analyze is run on all new queries in staging to verify index usage.
  - Index columns used in `WHERE`, `JOIN ON`, and `ORDER BY` clauses.
- **Migrations:** Managed by `golang-migrate`. Migration files are append-only, named
  `{timestamp}_{description}.{up|down}.sql`. All schema changes are backward-compatible;
  column drops are done in a separate migration after the application no longer references them.

### 2.4 Error Handling

- **Go services:** Errors are wrapped with `fmt.Errorf("operation: %w", err)` to preserve
  stack context. Service-layer errors use a custom `AppError` type carrying HTTP status code,
  machine-readable error code, and user-facing message.
- **Python services:** Custom exception hierarchy rooted at `AppError(Exception)`. FastAPI
  exception handlers convert domain exceptions to JSON responses. Unhandled exceptions are
  caught by a middleware that logs the full traceback and returns a generic 500 response.
- **Kafka consumer errors:** Failed message processing increments a per-topic error counter.
  After 3 consecutive failures on the same message, the message is forwarded to a
  `{topic}.dlq` (dead-letter queue) topic and the consumer commits the offset.
- **Circuit breaker:** Hystrix-style circuit breaker wraps all outbound HTTP and gRPC calls.
  Threshold: 50% error rate over a 10-second window opens the circuit for 5 seconds.

### 2.5 Logging & Observability

- **Structured logging:** All services log JSON using `zap` (Go) or `structlog` (Python).
  Every log entry includes: `timestamp`, `level`, `service`, `version`, `request_id`,
  `user_id` (if authenticated), `trace_id`, `span_id`, `latency_ms` (for request logs).
- **Log levels:** `DEBUG` disabled in production. `INFO` for request lifecycle. `WARN` for
  recoverable anomalies. `ERROR` for unexpected failures requiring investigation.
- **Metrics:** All services expose a `/metrics` endpoint in Prometheus format. Standard metrics:
  `http_requests_total`, `http_request_duration_seconds`, `db_query_duration_seconds`,
  `kafka_messages_consumed_total`, `kafka_consumer_lag`.
- **Tracing:** OpenTelemetry SDK auto-instruments HTTP servers and clients, database drivers,
  and Kafka producers/consumers. Traces are exported to AWS X-Ray via OTLP collector.
- **Alerting rules:** P95 latency > 500ms for 5 minutes → `warning`. Error rate > 1% for
  2 minutes → `critical`. Kafka consumer lag > 50k → `warning`.

---

## 3. Service Communication Patterns

### 3.1 Synchronous (REST/gRPC)

Used only for user-facing request paths where the response depends on the result:

| Caller | Callee | Protocol | Purpose |
|--------|--------|----------|---------|
| API Gateway | All services | REST/HTTPS | External client requests |
| Feed Service | Post Service | gRPC | Hydrate post data for ranked feed |
| Feed Service | Social Graph Service | gRPC | Fetch following list for feed assembly |
| Feed Service | SageMaker | HTTPS | Ranking score inference |
| Ad Service | Feed Service | gRPC | Insert sponsored content into feed |
| Search Service | Profile Service | gRPC | Enrich search results with live profile data |
| Messaging Service | User Service | gRPC | Validate recipient exists and is not blocked |

Timeouts: all synchronous calls have a maximum 2-second timeout with 1 retry on timeout only.

### 3.2 Asynchronous (Kafka Events)

All side effects that do not require synchronous confirmation use Kafka events. Event schemas
are defined in Avro and registered in the Confluent Schema Registry (MSK Schema Registry).

| Topic | Producer | Consumers | Event Types |
|-------|----------|-----------|-------------|
| `user.events` | User Service | Profile, Graph, Search | `UserRegistered`, `UserDeleted`, `UserSuspended` |
| `post.events` | Post Service | Feed, Search, Notification, Analytics | `PostCreated`, `PostDeleted`, `PostReacted` |
| `follow.events` | Graph Service | Feed, Notification, Analytics | `UserFollowed`, `UserUnfollowed` |
| `media.events` | Media Service | Post, Story | `MediaProcessingComplete`, `MediaRejected` |
| `moderation.events` | Moderation Service | Post, User, Community | `ContentFlagged`, `ContentRemoved`, `UserWarned` |
| `story.events` | Story Service | Notification, Analytics | `StoryPublished`, `StoryViewed`, `StoryExpired` |
| `notification.events` | Multiple | Notification Service | `NotificationQueued` |
| `analytics.events` | All services | Analytics Service | `PageViewed`, `FeedImpression`, `AdClicked` |

---

## 4. Security Implementation

- **Authentication:** All external APIs require a Bearer JWT issued by the User Service.
  JWTs are RS256-signed (4096-bit RSA key managed in KMS), valid for 15 minutes.
  Refresh tokens are opaque 256-bit random strings stored in Redis with a 30-day TTL.
- **Authorization:** Each service implements its own authorization checks. There is no central
  authorization service to avoid a single point of failure. Permissions are encoded in the JWT
  `claims` field and validated without a database lookup.
- **Rate limiting:** Enforced at the NGINX Ingress layer using `nginx.ingress.kubernetes.io/limit-rps`
  annotations, and additionally at the application layer via Redis sliding-window counters.
  Limits: anonymous = 20 req/s per IP; authenticated = 100 req/s per user.
- **Input validation:** All request bodies are validated using JSON Schema (OpenAPI) before
  reaching service logic. Validation is enforced by middleware; services never process
  unvalidated input.
- **Secrets rotation:** Database credentials and API keys are rotated every 90 days via
  AWS Secrets Manager automatic rotation. Services reload secrets on the next request after
  detecting a rotation via a Kubernetes secrets sync interval of 60 seconds.
- **mTLS:** All service-to-service communication within the cluster uses Istio-enforced mTLS
  in STRICT mode. No plaintext traffic is permitted between pods.
- **OWASP compliance:** WAF rules cover OWASP Top 10. Penetration testing conducted quarterly
  by third-party security firm. Results tracked in GitHub Security Advisories.

---

## 5. Testing Strategy

### 5.1 Unit Tests

- Target: 80% line coverage on service-layer and repository-layer code.
- Go: `testing` package + `testify/mock` for interface mocks. Table-driven tests for all
  pure functions. `go test -race` enabled to catch data races.
- Python: `pytest` + `unittest.mock`. `pytest-asyncio` for async FastAPI endpoints.
- All tests run in < 30 seconds total. No external dependencies in unit tests.

### 5.2 Integration Tests

- Each service has an integration test suite that spins up real dependencies using
  `testcontainers-go` (PostgreSQL, Redis, LocalStack for S3/DynamoDB).
- Kafka integration tests use an embedded Kafka broker (Redpanda in Docker).
- Run on every PR in GitHub Actions. Parallel execution across services.
- Aim: verify the full request path from HTTP handler to database and back.

### 5.3 E2E Tests

- Playwright test suite targeting the Next.js web app.
- Covers 30 critical user journeys: registration, login, post creation, follow, feed load,
  DM send, story view, community join, notification receive.
- Run on every merge to `main` against the staging environment.
- Visual regression screenshots stored in S3; diff alerts sent to Slack.

### 5.4 Load Tests

- Tool: k6 with scenarios defined per service.
- Baseline scenario: 10k virtual users, ramp-up 5 minutes, steady state 30 minutes.
- Feed Service target: P99 < 200ms at 50k req/s.
- Post creation target: P99 < 300ms at 5k req/s.
- Messaging (WebSocket): 100k concurrent connections, message delivery P99 < 50ms.
- Load tests run weekly against a dedicated performance environment (same spec as production).

---

## 6. CI/CD Pipeline

```
PR Opened → GitHub Actions:
  1. Lint (golangci-lint / ruff)
  2. Unit Tests (go test -race / pytest)
  3. Integration Tests (testcontainers)
  4. Build Docker image
  5. ECR image scan (Trivy — fail on CRITICAL CVEs)
  6. SAST (Semgrep — fail on HIGH severity findings)

PR Merged to main → GitHub Actions:
  1. All above checks
  2. Push image to ECR with git-SHA tag
  3. Update Helm values file (image tag) in infra GitOps repo
  4. ArgoCD detects change → applies rolling update to staging

Staging validation (automated):
  1. Smoke tests (Playwright — 10 critical paths)
  2. Chaos test: random pod kill, verify recovery < 30s
  3. If all pass → ArgoCD syncs to production (manual approval gate via ArgoCD UI)

Production deploy:
  1. Argo Rollouts canary: 10% → 30% → 100%
  2. Automatic rollback if error rate > 0.5% at any canary stage
  3. Deploy notification to #deployments Slack channel
```
