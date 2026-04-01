# C4 Component Diagrams

## 1. Auth Service — Level 3 Component Diagram

The Auth Service is the entry point for all authentication flows: password login, OIDC/SAML federation, OAuth 2.0 token exchange, MFA step-up, and session management. It issues and rotates tokens, evaluates risk signals, and publishes every auth decision to the audit stream.

```mermaid
C4Component
  title Auth Service — Component Diagram

  Container_Boundary(auth_svc, "Auth Service") {

    Component(auth_ctrl, "AuthController", "Go / net/http", "Routes inbound auth requests to the correct flow. Validates request schema. Returns structured error responses.")

    Component(cred_validator, "CredentialValidator", "Go / argon2id", "Verifies password hashes using Argon2id. Enforces brute-force lockout thresholds. Calls AccountStatusChecker before verifying credentials.")

    Component(acct_checker, "AccountStatusChecker", "Go", "Loads user or service account record. Checks status (active/suspended/locked/deprovisioned). Reads lockout expiry and MFA requirement flags.")

    Component(risk_eval, "RiskEvaluator", "Go / gRPC client", "Assembles risk signal payload (IP, device fingerprint, geo, time-of-day). Calls RiskEngine gRPC service. Returns risk score and adaptive action (allow/challenge/deny).")

    Component(mfa_orch, "MFAOrchestrator", "Go", "Determines required MFA method(s). Issues short-lived MFA challenge tokens. Delegates challenge generation and response verification to TOTP and WebAuthn adapters.")

    Component(totp_adapter, "TOTPAdapter", "Go / otp library", "Generates and validates RFC 6238 TOTP codes. Applies ±1 step drift tolerance. Records last-used counter to prevent replay.")

    Component(webauthn_adapter, "WebAuthnAdapter", "Go / go-webauthn", "Implements WebAuthn Level 2. Generates PublicKeyCredentialCreationOptions and PublicKeyCredentialRequestOptions. Verifies authenticator assertions against stored credential records.")

    Component(session_mgr, "SessionManager", "Go / Redis", "Creates and updates sessions in PostgreSQL. Caches active session state in Redis with 5-second TTL. Enforces monotonic state transitions. Handles concurrent revocation with optimistic locking.")

    Component(token_issuer, "TokenIssuer", "Go / jose v2", "Mints RS256-signed access tokens and RS256-signed ID tokens. Issues opaque refresh tokens. Manages key rotation using kid-tagged JWKS. Enforces per-client TTL overrides.")

    Component(audit_pub, "AuditPublisher", "Go / Kafka producer", "Builds structured audit events with all required fields. Publishes to the audit Kafka topic with at-least-once delivery. Handles Kafka unavailability with a local write-ahead buffer.")
  }

  Container_Ext(db, "PostgreSQL", "Database", "Sessions, users, tokens, token families")
  Container_Ext(redis, "Redis", "Cache", "Session state, nonce cache, lockout counters")
  Container_Ext(kafka, "Kafka", "Event Stream", "audit-events topic")
  Container_Ext(risk_svc, "Risk Engine", "gRPC Service", "Risk score calculation")
  Container_Ext(jwks_store, "JWKS Store", "KMS / Vault", "RSA private keys for token signing")

  Rel(auth_ctrl, cred_validator, "Dispatches password flows", "internal call")
  Rel(auth_ctrl, mfa_orch, "Dispatches MFA flows", "internal call")
  Rel(auth_ctrl, session_mgr, "Creates / reads sessions", "internal call")
  Rel(auth_ctrl, token_issuer, "Requests token issuance", "internal call")
  Rel(auth_ctrl, audit_pub, "Publishes auth events", "internal call")

  Rel(cred_validator, acct_checker, "Checks account status", "internal call")
  Rel(cred_validator, risk_eval, "Evaluates risk after credential check", "internal call")

  Rel(mfa_orch, totp_adapter, "TOTP challenge/verify", "internal call")
  Rel(mfa_orch, webauthn_adapter, "WebAuthn register/authenticate", "internal call")
  Rel(mfa_orch, redis, "Stores challenge nonces", "Redis SET with TTL")

  Rel(session_mgr, db, "Reads/writes session rows", "pgx/v5")
  Rel(session_mgr, redis, "Caches session state", "Redis SET/GET")

  Rel(token_issuer, jwks_store, "Retrieves signing keys", "Vault Transit API")
  Rel(token_issuer, db, "Records token metadata", "pgx/v5")

  Rel(risk_eval, risk_svc, "Requests risk score", "gRPC TLS")

  Rel(audit_pub, kafka, "Produces audit events", "Kafka producer")

  Rel(acct_checker, db, "Loads principal record", "pgx/v5")
  Rel(acct_checker, redis, "Reads lockout counter", "Redis GET")
```

---

## 2. Policy Engine — Level 3 Component Diagram

The Policy Engine provides both a Policy Decision Point (PDP) for real-time authorization and a Policy Administration Point (PAP) for lifecycle management. The PDP is a stateless, hot-path service. The PAP manages the policy lifecycle from draft through activation.

```mermaid
C4Component
  title Policy Engine — Component Diagram

  Container_Boundary(pdp, "Policy Decision Point (PDP)") {

    Component(pdp_ctrl, "PDPController", "Go / net/http", "Accepts POST /decide and POST /simulate requests. Validates context payload schema. Returns structured Decision with matched statements, obligations, and explain trace.")

    Component(policy_repo, "PolicyRepository", "Go / pgx", "Loads active policy bundles from PostgreSQL by tenant. Supports version-pinned reads for simulation. Serves as authoritative source on cache miss.")

    Component(policy_cache, "PolicyCache", "Go / Redis", "Caches compiled policy bundles per tenant keyed by (tenant_id, policy_hash). Invalidated on policy activation or deprecation via pub/sub. TTL 60 seconds as safety net.")

    Component(rule_engine, "RuleEngine", "Go", "Evaluates compiled policy statements in priority order. Applies Deny-overrides algorithm. Expands principal wildcards and group memberships. Returns Decision with full explain trace.")

    Component(subject_attr, "SubjectAttributeProvider", "Go / gRPC", "Resolves subject attributes from the runtime context: user profile, effective roles (direct + group-derived), assurance level, MFA status, session risk score.")

    Component(resource_attr, "ResourceAttributeProvider", "Go / gRPC", "Resolves resource attributes by calling the resource-owning service via gRPC. Results are cached per-request. Failures return Indeterminate if resource data is required by any condition.")

    Component(oblig_handler, "ObligationHandler", "Go", "Processes obligations returned in Allow decisions: log_access, notify_owner, require_audit_trail. Dispatches side-effect tasks asynchronously so the decision latency is unaffected.")

    Component(decision_logger, "DecisionLogger", "Go / Kafka producer", "Publishes every decision (including non-applicable) to the policy-decisions Kafka topic. Payload includes full explain trace, context snapshot hash, and policy version.")
  }

  Container_Boundary(pap, "Policy Administration Point (PAP)") {

    Component(pap_ctrl, "PAPController", "Go / net/http", "CRUD endpoints for policy and statement management. Enforces lifecycle state machine: draft → review → approved → active → deprecated.")

    Component(bundle_mgr, "PolicyBundleManager", "Go", "Compiles policy DSL into normalized statement AST. Assigns deterministic hash to each bundle version. Manages bundle activation: writes to DB, publishes cache-invalidation event.")

    Component(sim_engine, "SimulationEngine", "Go", "Executes dry-run evaluation using the same RuleEngine as the PDP but against a shadow context. Returns per-statement match trace without side effects or audit obligations.")
  }

  Container_Ext(pdb, "PostgreSQL", "Database", "policies, policy_statements tables")
  Container_Ext(pred, "Redis", "Cache", "Policy bundle cache + pub/sub invalidation")
  Container_Ext(pkafka, "Kafka", "Event Stream", "policy-decisions, cache-invalidation topics")
  Container_Ext(user_svc, "User Service", "gRPC Service", "Subject attribute resolution")
  Container_Ext(resource_svc, "Resource Services", "gRPC Services", "Resource attribute resolution (per domain)")

  Rel(pdp_ctrl, policy_cache, "Loads compiled bundle", "cache lookup")
  Rel(policy_cache, policy_repo, "Fetches on cache miss", "internal call")
  Rel(policy_repo, pdb, "Reads active policies", "pgx/v5")

  Rel(pdp_ctrl, rule_engine, "Runs evaluation", "internal call")
  Rel(rule_engine, subject_attr, "Resolves subject", "internal call")
  Rel(rule_engine, resource_attr, "Resolves resource", "internal call")

  Rel(subject_attr, user_svc, "Fetches roles, profile, risk", "gRPC TLS")
  Rel(resource_attr, resource_svc, "Fetches resource metadata", "gRPC TLS")

  Rel(pdp_ctrl, oblig_handler, "Dispatches obligations", "async goroutine")
  Rel(pdp_ctrl, decision_logger, "Publishes decision", "internal call")
  Rel(decision_logger, pkafka, "Produces decision event", "Kafka producer")

  Rel(pap_ctrl, bundle_mgr, "Activates/deprecates bundles", "internal call")
  Rel(bundle_mgr, pdb, "Writes policy rows", "pgx/v5")
  Rel(bundle_mgr, pred, "Publishes invalidation", "Redis pub/sub")
  Rel(policy_cache, pred, "Subscribes to invalidation", "Redis sub")

  Rel(pap_ctrl, sim_engine, "Runs simulations", "internal call")
  Rel(sim_engine, rule_engine, "Reuses evaluation logic", "internal call")
  Rel(sim_engine, policy_repo, "Loads version-pinned bundle", "internal call")
```

---

## 3. Component Interface Specifications

### 3.1 AuthController

| Attribute | Value |
|---|---|
| **Listens on** | `HTTP :8080` |
| **Input** | JSON request body, `Authorization` header, `X-Request-ID`, `X-Idempotency-Key` |
| **Output** | JSON response (token set, challenge, or error) |
| **Dependencies** | CredentialValidator, MFAOrchestrator, SessionManager, TokenIssuer, AuditPublisher |
| **SLO** | p99 < 300ms for password login, p99 < 150ms for token refresh |

### 3.2 CredentialValidator

| Attribute | Value |
|---|---|
| **Input** | `email`, `password` (plaintext), `tenant_id`, `client_ip` |
| **Output** | `{valid: bool, user_id, lockout_remaining_seconds}` or error |
| **Dependencies** | AccountStatusChecker, RiskEvaluator |
| **Algorithm** | Argon2id with `m=65536, t=3, p=4`; constant-time comparison |
| **Side effects** | Increments `failed_login_count`; sets `locked_until` on threshold breach |

### 3.3 AccountStatusChecker

| Attribute | Value |
|---|---|
| **Input** | `principal_id`, `principal_type`, `tenant_id` |
| **Output** | `{status, mfa_required, locked_until, assurance_level}` or `PrincipalNotFoundError` |
| **Dependencies** | PostgreSQL (read), Redis (lockout counter cache) |
| **Cache TTL** | 5 seconds in Redis; bypassed for step-up and revocation checks |

### 3.4 RiskEvaluator

| Attribute | Value |
|---|---|
| **Input** | `{ip, user_agent, device_fingerprint, geo, user_id, tenant_id}` |
| **Output** | `{score: 0.0–1.0, action: "allow" | "challenge" | "deny", signals: []}` |
| **Dependencies** | Risk Engine gRPC service |
| **Timeout** | 200ms; on timeout returns `{score: 0.5, action: "challenge"}` (fail-safe) |

### 3.5 MFAOrchestrator

| Attribute | Value |
|---|---|
| **Input** | `{user_id, tenant_id, method, stage: "begin" | "verify", payload}` |
| **Output** | `{challenge_id, method, expires_in}` on begin; `{verified: bool}` on verify |
| **Dependencies** | TOTPAdapter, WebAuthnAdapter, Redis (nonce store) |
| **Challenge TTL** | 300 seconds stored in Redis with automatic expiry |

### 3.6 SessionManager

| Attribute | Value |
|---|---|
| **Input** | `{principal_id, principal_type, tenant_id, auth_method, assurance_level, ip, user_agent, device_fingerprint, risk_signals}` |
| **Output** | `Session` object with `session_id`, `token_family_id`, `expires_at` |
| **Dependencies** | PostgreSQL (write), Redis (session cache) |
| **Consistency** | PostgreSQL is source of truth; Redis cache is write-through with 5-second TTL |
| **Revocation SLA** | Session state change propagates to Redis within 5 seconds P95 |

### 3.7 TokenIssuer

| Attribute | Value |
|---|---|
| **Input** | `{session_id, principal, tenant_id, scopes, audience, client_id, token_types}` |
| **Output** | `{access_token, refresh_token, id_token, expires_in}` |
| **Dependencies** | JWKS Store (Vault Transit), PostgreSQL (token metadata) |
| **Key rotation** | `kid` rotates every 30 days; two keys active during overlap window |
| **Access token TTL** | 600 seconds (default); configurable per OAuth client |

### 3.8 AuditPublisher

| Attribute | Value |
|---|---|
| **Input** | `AuditEvent` struct (all required fields must be populated before publish) |
| **Output** | `{event_id, offset}` on success |
| **Dependencies** | Kafka producer (topic: `audit-events`) |
| **Delivery guarantee** | At-least-once via Kafka producer `acks=all` |
| **Fallback** | On Kafka unavailability: writes to PostgreSQL write-ahead buffer table; drained by background job |

### 3.9 PDPController

| Attribute | Value |
|---|---|
| **Listens on** | `HTTP :8081` (internal), `gRPC :9090` |
| **Input** | `{subject, action, resource, environment}` context |
| **Output** | `{decision, matched_statements, obligations, explain_trace, evaluation_time_ms}` |
| **SLO** | p99 < 20ms for cached policy bundles; p99 < 50ms with cache miss |

### 3.10 PolicyBundleManager

| Attribute | Value |
|---|---|
| **Input** | Policy document (DSL JSON); target status transition |
| **Output** | `{bundle_hash, version, activated_at}` |
| **Dependencies** | PostgreSQL (policy writes), Redis (pub/sub invalidation) |
| **Invariant** | Only one bundle version per tenant can have `status = 'active'` at a time |

### 3.11 SimulationEngine

| Attribute | Value |
|---|---|
| **Input** | `{policy_id, version, subject_context, action, resource_context, environment}` |
| **Output** | Per-statement match trace; final decision; no side effects emitted |
| **Dependencies** | PolicyRepository (version-pinned read), RuleEngine |
| **Isolation** | Runs in a read-only transaction; cannot trigger ObligationHandler or DecisionLogger |

---

## 4. Technology Choices

### Auth Service

| Component | Technology | Justification |
|---|---|---|
| HTTP framework | `net/http` + `chi` router | Minimal allocations on hot path; no reflection-based routing overhead |
| Password hashing | `argon2id` via `golang.org/x/crypto` | OWASP-recommended; tunable memory/time parameters; side-channel resistant |
| JWT signing | `github.com/go-jose/go-jose/v3` | RFC 7515/7519 compliant; explicit algorithm selection prevents `alg:none` attacks |
| WebAuthn | `github.com/go-webauthn/webauthn` | WebAuthn Level 2 spec compliance; maintained by the Go security community |
| Session cache | Redis 7 (Sentinel) | Sub-millisecond reads; TTL-based expiry; Lua scripting for atomic revocation |
| Database driver | `github.com/jackc/pgx/v5` | Prepared statement caching; binary protocol; context-based cancellation |
| Kafka producer | `github.com/segmentio/kafka-go` | Pure-Go; supports `acks=all` with configurable retry; no CGo dependency |

### Policy Engine

| Component | Technology | Justification |
|---|---|---|
| HTTP/gRPC | `net/http` + `google.golang.org/grpc` | gRPC for internal service mesh (low latency, typed contracts); HTTP for external REST API |
| Policy cache | Redis 7 (Cluster) | Policy bundles are read-heavy and ~10–50 KB per tenant; Redis fits the working set entirely in memory |
| Cache invalidation | Redis Pub/Sub | Low-latency fan-out to all PDP replicas on policy activation without polling |
| Rule evaluation | Custom AST evaluator (Go) | Deterministic; no dynamic dispatch; allows precompiled condition indexes; fully testable |
| Obligation dispatch | Go channels + worker pool | Obligations are fire-and-forget; decoupled from decision latency via buffered channel |
