# Implementation Guidelines — Identity and Access Management Platform

## Overview

This document provides a phased, week-by-week implementation plan for the IAM platform.
Each phase ships a working, testable vertical slice. Teams must pass all acceptance tests before beginning the next phase.
All work is tracked against the status matrix in `backend-status-matrix.md`.

---

## Phase 1 — Foundation (Weeks 1–6)

### Goals
Establish the security-critical core: user lifecycle, credential management, token issuance, coarse-grained authorization, and the audit backbone. Every subsequent phase builds on these primitives.

### Deliverables

#### 1.1 User CRUD API
- `POST /v1/users` — create user with email, display name, initial role assignment
- `GET /v1/users/{id}` — fetch user profile
- `PUT /v1/users/{id}` — update mutable fields (display name, metadata)
- `DELETE /v1/users/{id}` — soft-delete (sets `deleted_at`, revokes all active sessions)
- `GET /v1/users` — paginated list with cursor-based pagination (keyset on `created_at, id`)
- Password stored as Argon2id hash: `time=3, memory=65536, parallelism=4, tagLength=32`
- Email uniqueness enforced at DB level (`UNIQUE` constraint + partial index on `lower(email)`)
- All write operations emit `user.created`, `user.updated`, `user.deleted` events to Kafka

#### 1.2 Authentication and Token Issuance
- `POST /v1/auth/login` — credential validation + JWT issuance
- JWT access tokens signed with RS256 (2048-bit RSA, rotated every 90 days via Vault)
- Access token TTL: 10 minutes; claims: `sub`, `iss`, `aud`, `iat`, `exp`, `jti`, `roles`, `permissions`
- Opaque refresh tokens: 256-bit CSPRNG, stored as HMAC-SHA256 digest in PostgreSQL
- Refresh token TTL: 7 days; single-use rotation on every `/v1/auth/token` call
- `POST /v1/auth/token` — refresh token exchange
- `POST /v1/auth/logout` — revoke current refresh token + invalidate session

#### 1.3 Basic RBAC
- Schema: `roles`, `permissions`, `role_permissions` junction table
- `POST /v1/roles` — create role with name, description
- `POST /v1/roles/{id}/permissions` — assign permissions to role
- `DELETE /v1/roles/{id}/permissions/{permId}` — remove permission from role
- `POST /v1/users/{id}/roles` — assign role to user
- Permission checks inline with every protected endpoint via middleware
- Permission format: `resource:action` (e.g., `user:read`, `policy:write`)

#### 1.4 Session Management
- Redis-backed session store; session key: `session:{sessionId}` (TTL mirrors access token expiry)
- Session record: `userId`, `roles[]`, `ip`, `userAgent`, `createdAt`, `lastSeenAt`
- Session refreshed on every authenticated request (sliding window)
- `GET /v1/sessions/me` — list caller's active sessions
- `DELETE /v1/sessions/{id}` — force-terminate single session

#### 1.5 Audit Event Emission
- Kafka topic: `iam.audit.events` (partitioned by `tenantId`)
- Event schema (Avro): `eventId`, `tenantId`, `actorId`, `actorType`, `action`, `resourceType`, `resourceId`, `outcome`, `ip`, `userAgent`, `occurredAt`, `metadata`
- Emit on: login success/failure, token issuance, token revocation, user write operations, role assignment changes
- Producer uses `acks=all`, `enable.idempotence=true`, `max.in.flight.requests.per.connection=5`

#### 1.6 Operational Endpoints
- `GET /healthz` — liveness check (returns 200 if process is alive)
- `GET /readyz` — readiness check (verifies DB connection, Redis ping, Kafka producer health)
- `GET /metrics` — Prometheus metrics endpoint (request count, latency histograms, error rates)

### Acceptance Tests — Phase 1

| Test ID | Description | Pass Criterion |
|---------|-------------|----------------|
| P1-T01 | Create user, fetch by ID | 201 + correct body; DB row present |
| P1-T02 | Login with valid credentials | 200 + access token verifiable with public key |
| P1-T03 | Login with invalid password | 401; audit event `login.failed` emitted |
| P1-T04 | Refresh token rotation | New tokens issued; old refresh token rejected on reuse |
| P1-T05 | Access token expiry | Request with 11-min-old token returns 401 |
| P1-T06 | RBAC permission enforcement | User without `user:delete` gets 403 on DELETE endpoint |
| P1-T07 | Session invalidation on logout | Subsequent requests with old session return 401 |
| P1-T08 | Soft-delete user | User row has `deleted_at`; sessions revoked; login returns 401 |
| P1-T09 | Audit events emitted | Kafka consumer confirms events for all write operations |
| P1-T10 | Readiness fails on DB down | `/readyz` returns 503 when PostgreSQL unreachable |

---

## Phase 2 — Core Features (Weeks 7–14)

### Goals
Layer MFA (TOTP + WebAuthn), a full policy decision engine, SCIM inbound provisioning, and hardened token lifecycle management onto the Phase 1 foundation.

### Deliverables

#### 2.1 TOTP MFA
- Enrollment: `POST /v1/mfa/totp/enroll` — generate TOTP secret (160-bit, base32-encoded), return provisioning URI + QR code data
- Verification: `POST /v1/mfa/totp/verify` — validate 6-digit code per RFC 6238 (SHA-1, 30-second window, ±1 window drift tolerance)
- Store encrypted TOTP secret in PostgreSQL using Vault Transit encryption-as-a-service
- Backup codes: 8 single-use 10-character alphanumeric codes generated at enrollment
- `DELETE /v1/mfa/totp` — dis-enroll TOTP; requires re-authentication

#### 2.2 WebAuthn / FIDO2
- Registration: `POST /v1/mfa/webauthn/registration/begin` + `POST /v1/mfa/webauthn/registration/complete`
- Authentication: `POST /v1/mfa/webauthn/authentication/begin` + `POST /v1/mfa/webauthn/authentication/complete`
- Supported authenticators: platform (Touch ID, Windows Hello) + roaming (YubiKey, FIDO2 USB)
- Credential storage: CBOR-encoded public key + credential ID in `webauthn_credentials` table
- Counter tracking to detect cloned authenticators; counter regression triggers forced re-enrollment

#### 2.3 Policy Engine — PDP
- `POST /v1/pdp/evaluate` — evaluate authorization request: `{ subject, resource, action, environment }`
- Decision results: `permit`, `deny`, `not_applicable`, `indeterminate`
- Deny-override combining algorithm: any matching `deny` rule wins over any `permit`
- RBAC evaluation: resolve subject → roles → permissions; check resource:action match
- Policy cache: Redis hash per policy bundle version; TTL 5 minutes; invalidated on bundle activation
- `POST /v1/pdp/simulate` — evaluate against a named policy version without side effects

#### 2.4 ABAC Condition Evaluation
- String operators: `equals`, `startsWith`, `endsWith`, `contains`, `regex`
- IP operators: `ipEquals`, `ipInRange` (CIDR), `ipInList`
- Date/time operators: `before`, `after`, `between`, `dayOfWeek`, `timeOfDay`
- Boolean operators: `isTrue`, `isFalse`
- Conditions composed with `AND` / `OR` / `NOT` logical combinators
- Environment attributes available in conditions: `request.ip`, `request.time`, `request.userAgent`, `session.mfaVerified`

#### 2.5 SCIM 2.0 Inbound Provisioning
- `/scim/v2/Users` — CRUD endpoints per RFC 7644
- `/scim/v2/Groups` — CRUD endpoints; group membership reflects RBAC role assignments
- Bearer token authentication for SCIM clients (separate long-lived service token)
- Attribute mapping: SCIM `userName` maps to IAM `email`; SCIM `name.formatted` maps to IAM `displayName`
- Patch operations: `add`, `remove`, `replace` per RFC 7644 section 3.5.2
- Provisioning events emitted to Kafka: `scim.user.created`, `scim.user.updated`, `scim.user.deprovisioned`

#### 2.6 Token Family Tracking and Reuse Detection
- Each refresh token belongs to a family (UUID assigned at first login)
- On reuse of an already-rotated token: revoke entire family, emit `security.token_reuse_detected` event, force-logout all sessions for that user
- Family lineage stored in PostgreSQL: `token_families(id, userId, createdAt, revokedAt, revocationReason)`
- `token_refresh_chain(id, familyId, tokenDigest, issuedAt, consumedAt, replacedByTokenId)`

#### 2.7 Force Logout
- `DELETE /v1/sessions/{id}` — terminate single session (Phase 1 already covers this)
- `DELETE /v1/users/{id}/sessions` — terminate all sessions for a user
- `DELETE /v1/sessions` (admin) — terminate all sessions matching filter (role, IP range, last-seen range)
- Force logout publishes to Redis Pub/Sub channel `session:revoked:{userId}` for real-time invalidation in gateway

### Acceptance Tests — Phase 2

| Test ID | Description | Pass Criterion |
|---------|-------------|----------------|
| P2-T01 | TOTP enrollment + verification | QR provisioning URI returned; valid code accepted; invalid code rejected |
| P2-T02 | TOTP clock drift tolerance | Code from previous window accepted; code from 2 windows ago rejected |
| P2-T03 | WebAuthn registration + authentication | Full ceremony succeeds with virtual authenticator |
| P2-T04 | WebAuthn counter regression | Counter below stored value triggers re-enrollment prompt |
| P2-T05 | PDP permit decision | Subject with matching role + permission returns `permit` |
| P2-T06 | PDP deny override | Subject has `permit` from role + explicit `deny` rule; result is `deny` |
| P2-T07 | ABAC IP condition | Request from non-allowlisted IP with `ipInRange` condition returns `deny` |
| P2-T08 | SCIM user create + role sync | SCIM POST creates IAM user; group membership assigns role |
| P2-T09 | SCIM PATCH remove member | User removed from SCIM group loses corresponding IAM role |
| P2-T10 | Token reuse detection | Reusing rotated refresh token revokes full family; all sessions terminated |

---

## Phase 3 — Advanced Features (Weeks 15–22)

### Goals
Enterprise federation (SAML + OIDC), just-in-time provisioning, privileged access workflows, policy lifecycle management, and drift detection.

### Deliverables

#### 3.1 SAML 2.0 SP-Initiated SSO
- SP metadata endpoint: `GET /saml/metadata`
- AuthnRequest generation: `GET /saml/login?idpId={id}` — redirect to IdP with signed AuthnRequest
- ACS endpoint: `POST /saml/acs` — validate assertion signature, decrypt EncryptedAssertion, extract attributes
- Assertion validation: issuer check, audience check, `NotBefore`/`NotOnOrAfter` window (±2 min clock skew), `InResponseTo` nonce
- Signature algorithms: RSA-SHA256 minimum; reject RSA-SHA1
- Multiple IdP configurations stored in `saml_identity_providers` table

#### 3.2 OIDC Federation (Authorization Code + PKCE)
- Authorization endpoint: `GET /oauth/authorize` — issue authorization code; enforce PKCE (`code_challenge_method=S256`)
- Token endpoint: `POST /oauth/token` — exchange code for tokens; validate `code_verifier`
- Introspection: `POST /oauth/introspect` (RFC 7662)
- Revocation: `POST /oauth/revoke` (RFC 7009)
- JWKS endpoint: `GET /.well-known/jwks.json`
- Discovery: `GET /.well-known/openid-configuration`
- Supported scopes: `openid`, `profile`, `email`, `offline_access`, `iam:read`, `iam:write`

#### 3.3 JIT User Provisioning
- Triggered on first successful SAML assertion or OIDC token exchange from federated IdP
- Attribute mapping configuration per IdP: maps IdP claims to IAM user attributes
- Configurable default role assignment per IdP
- Re-login updates mutable attributes (displayName, email) from latest IdP assertion
- JIT provisioning event: `federation.user.jit_provisioned` emitted to Kafka

#### 3.4 Break-Glass Access Workflow
- `POST /v1/break-glass/requests` — submit request with justification, target resource, requested duration
- Dual-approval model: requires approval from 2 distinct administrators
- `POST /v1/break-glass/requests/{id}/approve` — record approval
- Auto-expiry: access automatically revoked at `requestedDuration` end; max duration 4 hours
- All break-glass actions logged with full detail; separate Kafka topic `iam.break-glass.events`
- `GET /v1/break-glass/requests` — list active/pending requests (admin only)

#### 3.5 Policy Simulation and Bundle Deployment
- `POST /v1/pdp/simulate` — evaluate a draft policy bundle without activating it
- Policy bundle: versioned JSON/YAML document containing rules, conditions, and metadata
- `POST /v1/policies/bundles` — upload new bundle (creates draft)
- `POST /v1/policies/bundles/{id}/activate` — promote draft to active; invalidates PDP cache
- `POST /v1/policies/bundles/{id}/rollback` — revert to previous active bundle
- Deployment requires at least one simulation run with no unexpected deny regressions on golden test cases

#### 3.6 IP Allowlist Enforcement
- Per-user and per-service-account IP allowlists stored in `ip_allowlists` table
- Evaluated in authentication middleware before credential validation
- `POST /v1/users/{id}/ip-allowlist` — add CIDR to user's allowlist
- `DELETE /v1/users/{id}/ip-allowlist/{id}` — remove entry
- Enforcement for admin operations: separate, stricter allowlist applied to all `/admin/*` routes
- Allowlist violations emit `security.ip_blocked` audit event

#### 3.7 SCIM Drift Reconciliation
- Scheduled job runs every 15 minutes (Kubernetes CronJob)
- Compares SCIM source-of-truth against IAM state for each connected SCIM client
- Detects: users present in SCIM but deprovisioned in IAM, group membership mismatches, attribute drift
- Reconciliation actions: re-provision, re-sync attributes, re-assign roles
- Drift report emitted to Kafka: `scim.drift.detected` with delta payload
- Manual reconciliation trigger: `POST /v1/scim/reconcile`

### Acceptance Tests — Phase 3

| Test ID | Description | Pass Criterion |
|---------|-------------|----------------|
| P3-T01 | SAML SSO happy path | AuthnRequest to IdP to ACS to session created |
| P3-T02 | SAML assertion replay | Second use of same `InResponseTo` nonce returns 400 |
| P3-T03 | OIDC PKCE flow | Code without matching `code_verifier` rejected |
| P3-T04 | JIT provisioning on OIDC login | New IAM user created with mapped attributes on first federated login |
| P3-T05 | Break-glass dual approval | Access not granted after single approval; granted after second |
| P3-T06 | Break-glass auto-expiry | Elevated access revoked at `expiresAt`; subsequent requests return 403 |
| P3-T07 | Policy bundle simulation | Simulate identifies deny regression before activation |
| P3-T08 | Policy bundle rollback | Active bundle reverts; PDP cache invalidated; previous decisions reproduce |
| P3-T09 | SCIM drift detection | Reconciliation job detects manually deprovisioned user; re-provisions |
| P3-T10 | IP allowlist block | Request from blocked IP returns 403; `security.ip_blocked` event emitted |

---

## Phase 4 — Production Hardening (Weeks 23–30)

### Goals
Achieve production-grade reliability, observability, security assurance, and compliance readiness.

### Deliverables

#### 4.1 High Availability
- All stateless services: minimum 3 replicas, anti-affinity rules across availability zones
- PodDisruptionBudget: `minAvailable: 2` for all critical services
- PostgreSQL: primary + 2 read replicas (streaming replication); Patroni for automatic failover
- Redis: 3-node cluster (1 primary, 2 replicas) with Sentinel; `min-replicas-to-write: 1`
- Kafka: 3-broker cluster, replication factor 3, `min.insync.replicas=2`
- All services register Kubernetes liveness and readiness probes

#### 4.2 Observability — RED Metrics
- Request rate, error rate, duration histograms per service and per endpoint
- Prometheus scrape annotations on all pods; metric naming: `iam_{service}_{metric}_{unit}`
- Custom metrics: `iam_pdp_evaluation_duration_seconds`, `iam_token_issuance_total`, `iam_mfa_failures_total`, `iam_scim_sync_lag_seconds`
- Grafana dashboards: per-service RED dashboard, token lifecycle dashboard, PDP decision distribution, SCIM sync health
- Alert rules in `prometheusrules.yaml` committed to the infra repo

#### 4.3 Distributed Tracing
- OpenTelemetry SDK instrumented in all services (Go: `go.opentelemetry.io/otel`)
- Trace context propagated via W3C `traceparent` header
- Spans emitted for: DB queries, Redis operations, Kafka produce/consume, external IdP calls
- Jaeger as trace backend; traces sampled at 10% in production (100% in staging)
- Trace IDs included in all structured log entries and error responses

#### 4.4 SLO Alerting
- SLOs defined for: auth success rate (99.9%), token issuance latency p99 < 200ms, PDP latency p99 < 50ms, SCIM sync lag < 60s
- Alertmanager routes: SEV-1 to PagerDuty (immediate); SEV-2 to Slack + PagerDuty (5-min delay); SEV-3 to Slack only
- Multi-window, multi-burn-rate alerting following Google SRE burn rate methodology
- Silencing and inhibition rules for planned maintenance windows

#### 4.5 SOC 2 Compliance
- Control mapping document: maps IAM platform controls to SOC 2 Trust Service Criteria (CC6, CC7, CC8)
- Automated evidence collection: daily export of audit log statistics, access review reports, failed authentication counts
- Access review workflow: quarterly automated report of all role assignments for human review
- Data retention: audit logs retained 1 year in hot storage (PostgreSQL), 7 years in cold storage (S3 Glacier)

#### 4.6 Penetration Testing
- Scope: all API endpoints, SAML/OIDC flows, WebAuthn ceremonies, admin console
- Tooling: OWASP ZAP (DAST), Semgrep + gosec (SAST), Trivy (container scanning), Snyk (dependency scanning)
- All Critical and High findings remediated before production launch
- Re-test confirming remediation before sign-off

#### 4.7 Audit Log Export
- S3 export: daily batch job compresses and ships audit logs to S3; Parquet format; partitioned by `tenantId/year/month/day`
- SIEM integration: Kafka sink connector ships `iam.audit.events` topic to Splunk/Elastic in real time
- Log integrity: each S3 object includes SHA-256 checksum in metadata; chain-of-custody log maintained
- Retention policy enforced via S3 lifecycle rules

#### 4.8 Runbooks
- SEV-1: Primary DB failover, Redis cluster split-brain, Kafka unavailable, complete auth outage
- SEV-2: Elevated authentication error rate, PDP latency spike, SCIM sync failure, break-glass system unavailable
- Each runbook: symptom description, immediate triage steps, escalation path, remediation steps, post-incident actions

### Acceptance Tests — Phase 4

| Test ID | Description | Pass Criterion |
|---------|-------------|----------------|
| P4-T01 | Pod disruption budget enforcement | Rolling update does not drop below `minAvailable` replicas |
| P4-T02 | PostgreSQL failover | Primary loss; Patroni promotes replica within 30s; no data loss |
| P4-T03 | Redis Sentinel failover | Primary loss; Sentinel promotes replica within 10s; sessions preserved |
| P4-T04 | RED metrics present | All required metrics visible in Prometheus for all services |
| P4-T05 | Trace propagation | Single auth request traceable end-to-end in Jaeger |
| P4-T06 | SLO burn rate alert fires | Inject error rate; Alertmanager fires SEV-1 within 2 minutes |
| P4-T07 | Audit log export integrity | S3 object SHA-256 checksum matches locally computed hash |
| P4-T08 | SAST scan passes | `gosec` and Semgrep report zero Critical or High findings |
| P4-T09 | Load test meets NFRs | k6 at 10k RPS: p99 auth < 200ms, p99 PDP < 50ms, error rate < 0.1% |
| P4-T10 | Runbook drill | SEV-1 DB failover runbook executed in staging; RTO within 5 minutes |

---

## Tech Stack

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| Language | Go | 1.22 | Strong concurrency primitives, static typing, excellent crypto stdlib, low memory footprint |
| Web Framework | Chi | 5.0 | Lightweight, idiomatic Go HTTP router; no magic, easy middleware composition |
| Auth Libraries | go-jose | 4.0 | RFC-compliant JWK/JWT/JWS implementation; actively maintained |
| WebAuthn | go-webauthn/webauthn | 0.10 | Full FIDO2/WebAuthn Level 2 implementation in pure Go |
| SAML | crewjam/saml | 0.4 | Production-grade SAML 2.0 SP library |
| Database | PostgreSQL | 16 | ACID transactions, row-level security, native JSON support, pgcrypto |
| DB Driver | pgx | v5 | High-performance native Go PostgreSQL driver; prepared statement caching |
| Migrations | golang-migrate | 4.17 | SQL-based migrations with up/down support; CI integration |
| Cache | Redis | 7.2 | Sub-millisecond latency; cluster mode; Pub/Sub for session invalidation |
| Redis Client | go-redis | v9 | Full Redis 7 feature support; automatic cluster routing |
| Message Bus | Kafka | 3.6 | Durable, ordered event log; exactly-once semantics for audit events |
| Kafka Client | confluent-kafka-go | 2.4 | librdkafka bindings; production-proven; schema registry support |
| Schema Registry | Confluent Schema Registry | 7.6 | Avro schema enforcement; schema evolution with compatibility rules |
| Key Management | HashiCorp Vault | 1.15 | Transit encryption, PKI secrets engine for JWT signing keys, dynamic DB credentials |
| Vault SDK | vault/api | 1.12 | Official Go client for Vault; token renewal, lease management |
| Container Runtime | Docker | 25 | OCI-compliant image builds; multi-stage builds for minimal images |
| Orchestration | Kubernetes | 1.29 | Production orchestration; HPA, PDB, NetworkPolicy, RBAC |
| IaC | Terraform | 1.7 | Declarative cloud resource provisioning; state locking via S3 + DynamoDB |
| Helm | Helm | 3.14 | Kubernetes application packaging; values-based environment configuration |
| Observability | Prometheus + Grafana | 2.50 / 10.3 | Industry-standard metrics collection and visualization |
| Tracing | OpenTelemetry + Jaeger | 1.25 / 1.55 | Vendor-neutral distributed tracing |
| Alerting | Alertmanager | 0.27 | Alert routing, deduplication, silencing; PagerDuty + Slack integrations |
| Password Hashing | Argon2id (stdlib) | — | Memory-hard, side-channel resistant; OWASP recommended |
| OTP | pquerna/otp | 1.4 | RFC 6238 TOTP implementation; used for enrollment and verification |

---

## Testing Strategy

### Unit Tests
- Coverage target: 80% line coverage for all business logic packages
- State machine transitions: user lifecycle, token lifecycle, break-glass workflow states
- Policy precedence: deny override, not_applicable fallback, indeterminate handling
- TOTP validation: clock drift edge cases, counter window boundary conditions
- Claim mapping: SAML attribute to IAM claim, OIDC claim to IAM claim, null/missing attribute handling
- Go test conventions: table-driven tests, `testify/assert` for assertions, `testify/mock` for interfaces

### Integration Tests
- `testcontainers-go` spins up real PostgreSQL 16, Redis 7, and Kafka 3.6 containers per test suite
- Tests exercise full stack: HTTP handler to service to repository to database
- Covers: concurrent refresh token rotation, SCIM batch import, audit event delivery confirmation
- Run in CI on every pull request; parallel execution across test suites

### Contract Tests
- **Event schema validation**: Confluent Schema Registry compatibility check on every schema change
- **API contract tests**: Pact consumer-driven contracts between federation-service and token-service
- Contract tests run before integration tests in CI to fail fast on interface drift

### Security Tests
- **SAST**: `gosec` + Semgrep with OWASP ruleset run on every pull request
- **DAST**: OWASP ZAP active scan against staging environment on every release candidate
- **Dependency scanning**: Trivy + Snyk scan all Go modules and container base images on every build
- **Secret scanning**: `gitleaks` in pre-commit hook and CI; blocks merge if secrets detected

### Chaos Tests
- Redis primary failure: validate session reads fall back to replica; measure latency degradation
- Kafka broker loss: validate audit events queue locally and flush on reconnect; no event loss
- DB replica lag injection: validate PDP cache hit rate prevents latency spike during replica catch-up
- Chaos experiments run in staging weekly using Chaos Mesh

### Load Tests
- Tooling: k6 with custom IAM scenario scripts
- **Auth scenario**: 10,000 RPS sustained; target p99 < 200ms; error rate < 0.1%
- **PDP scenario**: 10,000 RPS; target p99 < 50ms; measures cache hit rate
- **SCIM scenario**: 1,000 RPS bulk import; validates no data loss under load
- Load tests run against production-equivalent staging before every major release

---

## Definition of Done

A feature is considered done when **all** of the following are true:

- [ ] All acceptance tests for the phase pass in CI
- [ ] Unit test coverage is 80% or higher for the feature's package
- [ ] Integration tests exist and pass with testcontainers
- [ ] API documentation (OpenAPI 3.1) updated and validated
- [ ] Database migration scripts reviewed and reversible
- [ ] Prometheus metrics instrumented for the new endpoint or operation
- [ ] Structured log entries include `traceId`, `userId`, `action`, `outcome`
- [ ] Audit events emitted for all state-changing operations
- [ ] Feature flag in place if the change is behind a rollout gate
- [ ] Runbook updated if the feature introduces a new failure mode
- [ ] Security review sign-off from security team or peer reviewer
- [ ] No new Critical or High findings from SAST scan
- [ ] Load test baseline not regressed (p99 within 10% of previous baseline)
- [ ] PR approved by at least 2 engineers, including one with security background

---

## Security Review Checklist

Every pull request touching authentication, token handling, or authorization logic must pass this checklist before merge.

### Cryptography
- [ ] No use of MD5, SHA-1, or DES for security purposes
- [ ] No hardcoded secrets, keys, or passwords in source code
- [ ] Random values use `crypto/rand`; never `math/rand`
- [ ] Argon2id parameters meet OWASP minimums (`time>=1`, `memory>=64MiB`)
- [ ] JWT signing keys sourced from Vault; never from environment variables

### Input Validation
- [ ] All user-supplied inputs validated for type, length, and character set before processing
- [ ] Email addresses normalized to lowercase before comparison and storage
- [ ] Redirect URIs validated against strict allowlist (no wildcard matching)
- [ ] SCIM attribute values sanitized before writing to DB
- [ ] JSON depth and size limits enforced (max 1MB body, max 10-level nesting)

### Authorization
- [ ] Every HTTP endpoint has explicit permission check; no implicit allow-by-default
- [ ] Administrative endpoints require MFA-verified session
- [ ] Tenant isolation enforced at DB query level (row-level security policy or explicit `tenantId` predicate)
- [ ] Service accounts cannot escalate their own permissions

### Token Security
- [ ] JWT `aud` claim validated against expected audience list
- [ ] JWT `iss` claim validated against configured issuer
- [ ] `jti` claim checked against revocation list for sensitive operations
- [ ] Refresh token stored as HMAC digest; plaintext never persisted
- [ ] Token family revocation revokes all members, not just the reused token

### Audit and Logging
- [ ] Authentication failures logged with reason (but not with password or token values)
- [ ] No PII or secrets in log messages (email addresses hashed in debug logs)
- [ ] Audit events cannot be suppressed by application logic; emitted before response is sent
- [ ] Break-glass access logged with full detail including approvers

### Dependencies
- [ ] All Go module updates reviewed for breaking changes and CVEs
- [ ] Container base image is minimal (`distroless` or `alpine`); no unnecessary tools
- [ ] Trivy scan shows zero Critical CVEs in container image
