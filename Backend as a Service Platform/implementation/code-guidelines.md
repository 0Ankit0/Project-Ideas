# Code Guidelines – Backend as a Service Platform

## 1. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| API services | TypeScript (Node.js / Fastify) | TS 5.x, Node 20 LTS |
| High-throughput adapters & workers | Go | 1.22+ |
| Primary data store | PostgreSQL | 16+ |
| Cache / idempotency store | Redis | 7.x |
| Message bus | Apache Kafka (via MSK) | 3.x |
| Container orchestration | Kubernetes (EKS) | 1.29+ |
| IaC | Terraform + Helm | TF 1.7+, Helm 3 |
| Monorepo tooling | Turborepo + pnpm | pnpm 9+ |

---

## 2. Monorepo Structure

```
/
├── apps/
│   ├── api/                    # Fastify REST + WebSocket API gateway
│   ├── control-plane/          # Control plane UI (Next.js)
│   └── worker/                 # Go background worker binary
├── packages/
│   ├── domain/                 # Aggregates, value objects, domain events (TS)
│   ├── application/            # Command/query handlers, application services (TS)
│   ├── infrastructure/         # Repositories, message bus clients, secret clients (TS)
│   ├── common/                 # Logger, tracer, error types, pagination, Result<T,E> (TS)
│   └── sdk/                    # Public developer SDK (TS, published to npm)
├── adapters/
│   ├── auth/                   # IAuthAdapter + implementations (oauth2, jwt-local)
│   ├── storage/                # IStorageAdapter + S3Adapter, GCSAdapter
│   ├── functions/              # IFunctionsAdapter + LambdaAdapter, DockerAdapter
│   └── events/                 # IEventsAdapter + KafkaAdapter, NATSAdapter
├── infra/
│   ├── terraform/              # AWS infrastructure as code
│   └── helm/                   # Kubernetes Helm charts
├── scripts/                    # CI helpers, migration runners, seed scripts
└── docs/                       # Architecture decision records
```

**Dependency rules (enforced by `eslint-plugin-import` and Turborepo boundaries):**
- `apps/*` may depend on `packages/*` and `adapters/*`
- `packages/application` may depend on `packages/domain` and `packages/common` only
- `packages/domain` may depend on `packages/common` only
- `adapters/*` may depend on `packages/domain` and `packages/common` only
- No circular dependencies permitted; lint gate blocks PR on violation

---

## 3. TypeScript Conventions

- **Strict mode**: `"strict": true` in all `tsconfig.json` files; `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes` all enabled.
- **No `any`**: use `unknown` and narrow with type guards; `// eslint-disable` for `any` requires a ticket reference.
- **Branded IDs**: all entity IDs are branded types to prevent accidental swaps:
  ```typescript
  type TenantId = string & { readonly __brand: 'TenantId' };
  type ProjectId = string & { readonly __brand: 'ProjectId' };
  const tenantId = 't_abc' as TenantId;
  ```
- **Result type**: use `neverthrow` `Result<T, E>` for all fallible operations; `throw` only for truly unrecoverable programmer errors.
  ```typescript
  import { ok, err, Result } from 'neverthrow';
  async function createProject(cmd: CreateProjectCommand): Promise<Result<Project, DomainError>> { ... }
  ```
- **Immutability**: prefer `readonly` arrays and `Readonly<T>` objects in domain layer.
- **Zod for validation**: all inbound request payloads validated with Zod schemas at the HTTP boundary; never trust raw `req.body`.

---

## 4. Go Conventions

- **Explicit error returns**: every fallible function returns `(T, error)`; never panic in library code.
- **Context propagation**: every function that does I/O accepts `context.Context` as the first parameter.
- **Interface-first**: define interfaces in the consumer package, not the implementor:
  ```go
  // In worker package:
  type JobQueue interface {
      Consume(ctx context.Context, topic string) (<-chan Job, error)
  }
  ```
- **Structured errors**: wrap errors with `fmt.Errorf("operation: %w", err)` for traceability.
- **No global state**: pass dependencies via constructor injection; avoid `init()` side effects.
- **Table-driven tests**: all unit tests use table-driven patterns with `t.Run` sub-tests.

---

## 5. Database Conventions

- **Migrations**: use `golang-migrate` (Go workers) and `node-pg-migrate` (TypeScript services); migrations live in `packages/infrastructure/migrations/`.
- **No raw SQL in business logic**: use typed query builders (`pg` + hand-rolled repository classes in TS; `pgx` + `sqlc` in Go).
- **Parameterized queries only**: string interpolation into SQL is a hard lint violation.
- **Row-Level Security**: all multi-tenant tables enable RLS; services connect with `SET LOCAL app.tenant_id = $1` at the start of each transaction.
- **Transactions**: use explicit transactions for all multi-step writes; never rely on implicit auto-commit for business operations.
- **Schema versioning**: `schema_migrations` table tracks applied migrations; CI gate fails if uncommitted migration files exist.

---

## 6. API Conventions

- **Error envelope**: every error response follows the canonical shape:
  ```json
  { "error": { "code": "AUTH_TOKEN_EXPIRED", "category": "auth", "message": "...", "retryable": false, "correlationId": "corr_xyz" } }
  ```
- **Idempotency**: all state-mutating endpoints accept `Idempotency-Key` header; the key is stored in Redis with a 24-hour TTL; duplicate requests return the cached response.
- **Pagination**: cursor-based using an opaque `nextCursor` token (base64-encoded composite key); limit default 20, max 100.
- **Versioning**: URL-prefixed (`/api/v1/`, `/api/v2/`); breaking changes require a new version; sunset headers added 6 months before removal.
- **Correlation IDs**: API gateway generates `X-Correlation-Id` if absent; propagated through all downstream calls and included in all log entries.

---

## 7. Testing Strategy

| Level | Framework | Coverage Target | Notes |
|-------|-----------|----------------|-------|
| Unit (TS) | Vitest | ≥ 90% domain + application | No I/O; mock adapters with `vi.fn()` |
| Unit (Go) | `testing` + `testify` | ≥ 85% | Table-driven, no external deps |
| Integration (TS) | Vitest + Testcontainers | All repository classes | Real PostgreSQL container per suite |
| Integration (Go) | `testing` + Testcontainers-Go | All Kafka consumers/producers | Real Kafka container |
| Contract (adapters) | Pact | All IAdapter implementations | Consumer-driven contract tests |
| E2E | Playwright + k6 | Critical user journeys | Run in staging environment |
| Load | k6 | P99 latency SLOs | Nightly run in staging |

- CI blocks merge on any test failure or coverage drop below threshold.
- Integration tests run in Docker Compose locally; use `pnpm test:integration`.

---

## 8. Security Coding Standards

- **Input validation**: every HTTP handler validates with Zod before touching business logic; invalid input returns `400` with a structured error.
- **Parameterized queries**: enforced by `sqlc` (Go) and ESLint rule `no-sql-injection` (TS).
- **Secret redaction**: logger middleware automatically redacts fields named `password`, `token`, `secret`, `apiKey`, `authorization` from log output.
- **No secrets in env vars**: secrets come from mounted files via External Secrets Operator; `process.env` access to secret values is a lint violation.
- **OWASP Top 10 checklist**: reviewed per major feature; tracked in ADR-009.
- **Dependency scanning**: Dependabot + `npm audit` + `govulncheck` run on every PR.
- **SAST**: CodeQL analysis on every PR for both TypeScript and Go.

---

## 9. Observability

| Signal | Library | Format | Destination |
|--------|---------|--------|-------------|
| Structured logs | Pino (TS) / zerolog (Go) | JSON | CloudWatch Logs |
| Distributed traces | OpenTelemetry SDK | OTLP | Jaeger → CloudWatch X-Ray |
| Metrics | `prom-client` (TS) / `prometheus/client_golang` | Prometheus | Prometheus → Grafana |
| Error tracking | Sentry SDK | — | Sentry Cloud |

Every log entry **must** include: `correlationId`, `tenantId`, `projectId`, `envId`, `service`, `level`, `timestamp`.

---

## 10. Git and PR Conventions

- **Branch naming**: `feat/<ticket>-short-description`, `fix/<ticket>-...`, `chore/<ticket>-...`
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- **PR requirements**: at least 1 approval, all CI checks green, no merge conflicts, description filled in with the PR template
- **PR template sections**: Summary, Type of Change, Testing Done, Migration Notes, Security Notes
- **Merge strategy**: Squash merge to main; feature flags for large features to avoid long-lived branches

---

## 11. CI/CD Pipeline Gates

| Stage | Gate | Failure Action |
|-------|------|---------------|
| Lint | ESLint + `golangci-lint` | Block PR |
| Type-check | `tsc --noEmit` | Block PR |
| Unit tests | Vitest + Go test | Block PR |
| Coverage | Below threshold | Block PR |
| Integration tests | Testcontainers suite | Block PR |
| Contract tests | Pact | Block PR |
| Security scan | CodeQL + `npm audit` + `govulncheck` | Block PR (HIGH/CRITICAL) |
| Image build | Docker buildx | Block deploy |
| Staging deploy | Helm upgrade | Block prod deploy |
| Smoke tests | k6 smoke suite | Block prod deploy |
| Prod deploy | Helm upgrade + canary | Auto-rollback on error budget breach |
