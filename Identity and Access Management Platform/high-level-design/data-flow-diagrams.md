# IAM Platform — Data Flow Diagrams

## 1. Authentication Data Flow

This diagram shows how a credential-based authentication request travels through the system from initial client submission to final token delivery. Data classification labels indicate the sensitivity of each data element in transit.

```mermaid
flowchart TD
    subgraph CLIENT["Client Tier"]
        C["Browser / Mobile App / CLI\n[Data: Username + Password (PII + Credential)]"]
    end

    subgraph EDGE["Edge Tier"]
        GW["API Gateway\n[Kong / AWS API GW]\nTLS Termination · Rate Limit · WAF Rules"]
        RATELIMIT["Rate Limiter\nPer-IP sliding window counter\n[Data: IP address (PII)]"]
    end

    subgraph AUTH_TIER["Authentication Tier"]
        AC["Auth Controller\n[Data: Normalised email, bcrypt hash (Credential)]"]
        CV["Credential Validator\ncompare(bcrypt, hash, cost=12)\n[Data: Password hash (Credential — never stored in plaintext)]"]
        RE["Risk Engine\nDevice fingerprint · IP geo · Velocity\n[Data: Behavioural signals (PII-adjacent)]"]
        MFA_ORCH["MFA Orchestrator\nTOTP · FIDO2 · SMS · Email OTP\n[Data: OTP code (Credential), TOTP seed (Credential — encrypted at rest)]"]
    end

    subgraph SESSION_TOKEN["Session and Token Tier"]
        SM["Session Manager\nCreate session record\n[Data: Session ID (Session Token), user context]"]
        TS["Token Service\nSign JWT via Vault Transit (RS256)\n[Data: JWT (Session Token), Refresh Token (Credential-class token)]"]
    end

    subgraph STORAGE["Storage Tier"]
        PG_USER[("PostgreSQL\nUser Store\n[Data: User record, password hash, MFA config (PII + Credential)]")]
        REDIS_SESSION[("Redis Cluster\nSession + Token Cache\n[Data: Session record (Session Token), revocation list]")]
        VAULT_KEY[("HashiCorp Vault\nJWT Signing Keys\n[Data: RSA/EC private key (Credential — never leaves Vault)]")]
        KAFKA_AUDIT[("Kafka\niam.audit topic\n[Data: Structured audit events (PII + Operational)]")]
    end

    subgraph RESPONSE["Response Tier"]
        RESP["HTTP 200 Response\n[Data: access_token (JWT), refresh_token (Opaque),\ntoken_type, expires_in, session_id]"]
        ERR401["HTTP 401 / 403\n[Data: error code only — no credential detail leaked]"]
    end

    %% Request ingress
    C -->|"POST /auth/login\n{email, password}\nHTTPS · TLS 1.3"| GW
    GW -->|"Check rate limit counter"| RATELIMIT
    RATELIMIT -->|"429 Too Many Requests"| C
    RATELIMIT -->|"Within limit — forward request"| AC

    %% Credential validation
    AC -->|"Fetch user record by normalised email\n[PostgreSQL read replica]"| PG_USER
    PG_USER -->|"User record + password hash\n[Credential — in-memory only]"| AC
    AC -->|"bcrypt.Compare(provided, storedHash)"| CV
    CV -->|"Credential mismatch → increment failed_login_count"| PG_USER
    CV -->|"Mismatch after N attempts → lock account"| PG_USER
    CV -->|"Credential invalid"| ERR401

    %% Risk scoring (parallel with account status check)
    AC -->|"IP, user-agent, device fingerprint\n[Behavioural signals]"| RE
    RE -->|"Risk score (0.0–1.0) + risk signals"| AC

    %% MFA decision
    AC -->|"High risk score OR tenant MFA policy requires it"| MFA_ORCH
    MFA_ORCH -->|"Fetch enrolled MFA devices\n[Credential — encrypted TOTP seed]"| PG_USER
    MFA_ORCH -->|"TOTP: HMAC-SHA1 challenge response\nAnti-replay nonce SETNX in Redis"| REDIS_SESSION
    MFA_ORCH -->|"SMS/Email: OTP delivery request"| C
    MFA_ORCH -->|"MFA failed → 401 with mfa_required context"| ERR401
    MFA_ORCH -->|"MFA verified — assurance level confirmed"| AC

    %% Session creation
    AC -->|"CreateSession(userId, tenantId, assuranceLevel, ip, ua)"| SM
    SM -->|"HSET session:{id} ... EXPIRE 28800\n[Session Token — scoped TTL]"| REDIS_SESSION
    SM -->|"Session ID"| AC

    %% Token issuance
    AC -->|"IssueTokens(userId, sessionId, scopes, tenantId)"| TS
    TS -->|"Sign JWT claims via Transit encrypt\n[Private key never leaves Vault]"| VAULT_KEY
    VAULT_KEY -->|"Signed JWT bytes\n[Session Token — short-lived 15 min]"| TS
    TS -->|"Store refresh token family record\n[Credential-class token]"| PG_USER
    TS -->|"Cache token JTI in revocation set\n[Session Token metadata]"| REDIS_SESSION
    TS -->|"access_token + refresh_token"| AC

    %% Audit event
    AC -->|"Emit LoginSucceeded event\n[PII: userId, tenantId, ip, ua, timestamp]"| KAFKA_AUDIT

    %% Successful response
    AC -->|"HTTP 200 + token payload\n[Session Token — transmitted over TLS only]"| RESP
    RESP -->|"Set-Cookie: refresh_token (HttpOnly, Secure, SameSite=Strict)\nBody: access_token, expires_in"| C
```

---

## 2. Authorization / Policy Evaluation Data Flow

This diagram shows how a downstream service request is authorised using the Policy Decision Point. The cache-hit path (left branch) and cache-miss path (right branch) are shown distinctly.

```mermaid
flowchart TD
    subgraph CALLER["Calling Service"]
        SVC["Downstream Service\nAPI call with JWT in Authorization header\n[Data: JWT (Session Token), resource path, action]"]
    end

    subgraph PEP_LAYER["Policy Enforcement Point — API Gateway Plugin"]
        PEP["PEP\nExtract subject from JWT\nBuild AuthzRequest(subject, resource, action)\n[Data: Decoded JWT claims (PII), resource descriptor]"]
    end

    subgraph PDP_LAYER["Policy Decision Point (OPA Engine)"]
        PDP["PDP Coordinator\nRoute to cache or evaluation engine"]
        CACHE_CHECK["Redis Cache Lookup\nKey: {tenantId}:{subjectId}:{resource}:{action}\nTTL: 60 s"]
        OPA["OPA Evaluation Engine\nRego policy bundle evaluation\n[Data: Policy rules, subject attrs, resource attrs]"]
        SUB_STORE["Subject Attribute Store\nRoles + group memberships from PostgreSQL\n[Data: User attributes (PII-adjacent)]"]
        RES_STORE["Resource Attribute Store\nResource tags and classifications from PostgreSQL\n[Data: Resource metadata]"]
        POLICY_STORE[("PostgreSQL\nPolicy Store\nVersioned policy bundles\n[Data: Policy definitions]")]
        POLICY_CACHE[("Redis Cluster\nPolicy Decision Cache\n[Data: Decision + obligations, TTL 60 s]")]
    end

    subgraph DECISION_LAYER["Decision Processing"]
        DECISION["Decision Engine\nAllow / Deny / Indeterminate\n[Data: Effect, obligations, matched policy ID]"]
        OBL_HANDLER["Obligation Handler\nEnforce post-decision obligations:\n- require-mfa-step-up\n- log-sensitive-access\n- apply-rate-limit"]
        DEC_LOG["Decision Logger\nPublish PolicyDecision event to Kafka\n[Data: decision, subject, resource, policy ID (Operational)]"]
    end

    subgraph ENFORCE["Enforcement and Response"]
        PEP_ENF["PEP Enforcement\nAllow: forward request to upstream\nDeny: HTTP 403 with policy_code"]
        UPSTREAM["Upstream Service Response\n[Data: Business data — classification varies]"]
        DENIED["HTTP 403 Forbidden\n{error: access_denied, policy_code: P-xxxx}\n[Data: Error code only — no policy detail leaked]"]
    end

    subgraph AUDIT_PATH["Audit Path"]
        KAFKA_DEC[("Kafka\niam.policy.decisions topic\n[Data: Structured decision record (Operational)]")]
        SIEM_FWD["SIEM Forwarder\nReal-time security monitoring"]
    end

    %% Request entry
    SVC -->|"HTTP request with JWT\n[Session Token]"| PEP
    PEP -->|"AuthzRequest(subject, resource, action)"| PDP

    %% Cache check
    PDP -->|"Cache lookup"| CACHE_CHECK
    CACHE_CHECK -->|"CACHE HIT — return cached decision\n(sub-5 ms path)"| DECISION
    CACHE_CHECK -->|"CACHE MISS — evaluate full policy"| OPA

    %% Policy evaluation (cache miss path)
    OPA -->|"Fetch subject roles + group memberships\n[PII-adjacent attribute data]"| SUB_STORE
    SUB_STORE -->|"Query PostgreSQL read replica"| POLICY_STORE
    POLICY_STORE -->|"Subject attributes"| OPA
    OPA -->|"Fetch resource classification + tags"| RES_STORE
    RES_STORE -->|"Query PostgreSQL read replica"| POLICY_STORE
    POLICY_STORE -->|"Resource attributes"| OPA
    OPA -->|"Fetch current policy bundle for tenant"| POLICY_STORE
    POLICY_STORE -->|"Versioned Rego policy bundle"| OPA
    OPA -->|"Evaluated decision + obligations"| DECISION

    %% Cache write on miss
    DECISION -->|"CACHE MISS path: write to Redis\n{tenantId}:{subjectId}:{resource}:{action} TTL=60s"| POLICY_CACHE

    %% Post-decision processing
    DECISION -->|"Process obligations"| OBL_HANDLER
    DECISION -->|"Log decision to Kafka"| DEC_LOG
    DEC_LOG -->|"Publish to iam.policy.decisions"| KAFKA_DEC
    KAFKA_DEC -->|"Forward to SIEM"| SIEM_FWD

    %% Enforcement
    OBL_HANDLER -->|"Obligations satisfied — proceed"| PEP_ENF
    PEP_ENF -->|"Allow: forward to upstream service"| UPSTREAM
    PEP_ENF -->|"Deny: HTTP 403"| DENIED
    UPSTREAM -->|"Response data"| SVC
    DENIED -->|"403 error"| SVC

    %% Policy invalidation path (background)
    POLICY_STORE -.->|"PolicyChanged event via Kafka\ntriggers cache flush"| POLICY_CACHE
```

---

## 3. SCIM Provisioning Data Flow

This diagram shows how user and group lifecycle events from an upstream SCIM 2.0 directory flow through the platform to update user records, synchronise group memberships, and publish downstream events.

```mermaid
flowchart TD
    subgraph UPSTREAM_DIR["Upstream Directory"]
        SCIM_DIR["SCIM 2.0 Directory\n(Okta / Azure AD / OneLogin)\n[Data: User attributes (PII), Group membership]"]
    end

    subgraph SCIM_TIER["SCIM Adapter Tier"]
        SCIM_AUTH["SCIM Request Authenticator\nValidate Bearer token or mTLS cert\n[Data: Bearer token (Credential)]"]
        SCHEMA_VAL["Schema Validator\nValidate SCIM 2.0 resource schema\nCheck required attributes: userName, name.formatted\n[Data: SCIM User / Group resource (PII)]"]
        IDEM_CHECK["Idempotency Checker\nLookup externalId + etag\nDetect duplicate requests\n[Data: externalId, etag, operation hash]"]
        CONFLICT_RES["Conflict Resolver\nLast-write-wins by modifiedAt timestamp\nConflict logged to Kafka if tie\n[Data: Conflicting attribute values (PII)]"]
    end

    subgraph USER_REPO["User Repository Tier"]
        USER_SVC["User Service\nApply SCIM operation: Create / Update / Deactivate / Delete\n[Data: User record (PII + Credential — password hash excluded from SCIM)]"]
        PG_USER[("PostgreSQL\nUser Store\n[Data: Canonical user record (PII)]")]
        SCIM_STATE[("PostgreSQL\nSCIM Sync State\n[Data: externalId → internalId map, etag, cursor]")]
    end

    subgraph SYNC_WORKERS["Synchronisation Workers"]
        GROUP_SYNC["Group Sync Worker\nReconcile group memberships:\nAdd / remove User ↔ Group associations\n[Data: Group memberships (PII-adjacent)]"]
        ENTITL_EVAL["Entitlement Evaluator\nDerive role assignments from group-to-role mapping\nApply tenant provisioning policy\n[Data: Role assignments (Authorisation data)]"]
    end

    subgraph EVENT_TIER["Event Publishing Tier"]
        EVENT_PUB["Event Publisher\nSerialise domain events to Avro\nPublish to Kafka topics\n[Data: Domain events (PII in user fields — encrypted at topic level)]"]
        KAFKA_PROV[("Kafka\niam.provisioning topic\n[Data: UserCreated, UserUpdated, UserDeprovisioned, GroupSyncCompleted events]")]
    end

    subgraph DOWNSTREAM_CONSUMERS["Downstream Consumers"]
        AUDIT_CONS["Audit Consumer\nWrite SCIMProvisionEvent to iam.audit\n[Data: Audit record (PII + Operational)]"]
        SESS_NOTIFY["Session Manager Notification\nRevoke active sessions on UserDeprovisioned\n[Data: userId, tenantId]"]
        ANALYTICS["Analytics Pipeline\nAggregate provisioning metrics\n[Data: Anonymised counters — no PII]"]
    end

    subgraph SCIM_RESPONSE["SCIM Response Tier"]
        RESP_200["HTTP 200/201\nSCIM resource representation + etag\n[Data: Created / updated SCIM resource (PII)]"]
        RESP_409["HTTP 409 Conflict\nSCIM error response\n[Data: Error message, no internal detail]"]
        RESP_422["HTTP 422 Unprocessable Entity\nSchema validation error\n[Data: Attribute path + error description]"]
    end

    %% SCIM request ingress
    SCIM_DIR -->|"POST /scim/v2/Users\nPUT /scim/v2/Users/{id}\nDELETE /scim/v2/Users/{id}\n[PII: firstName, lastName, email, phone, managerId]"| SCIM_AUTH
    SCIM_AUTH -->|"Token invalid → HTTP 401"| SCIM_DIR
    SCIM_AUTH -->|"Authenticated — forward request"| SCHEMA_VAL

    %% Validation
    SCHEMA_VAL -->|"Schema violation → HTTP 422"| RESP_422
    SCHEMA_VAL -->|"Schema valid"| IDEM_CHECK

    %% Idempotency check
    IDEM_CHECK -->|"Lookup externalId in SCIM state table"| SCIM_STATE
    SCIM_STATE -->|"Duplicate detected — return cached response\n[etag match]"| RESP_200
    IDEM_CHECK -->|"Conflict on concurrent update"| CONFLICT_RES
    CONFLICT_RES -->|"Unresolvable conflict → HTTP 409"| RESP_409
    IDEM_CHECK -->|"New or valid update — proceed"| USER_SVC

    %% User persistence
    USER_SVC -->|"INSERT / UPDATE user record\n[PostgreSQL primary write]"| PG_USER
    USER_SVC -->|"Update SCIM sync state (externalId, etag, cursor)"| SCIM_STATE
    PG_USER -->|"Confirmed write"| USER_SVC

    %% Group sync (async after user write)
    USER_SVC -->|"Trigger group membership reconciliation"| GROUP_SYNC
    GROUP_SYNC -->|"Fetch group-to-role mapping for tenant"| PG_USER
    GROUP_SYNC -->|"Apply membership delta (add/remove)"| PG_USER
    GROUP_SYNC -->|"Resolve new entitlements"| ENTITL_EVAL
    ENTITL_EVAL -->|"Apply role assignments via provisioning policy"| PG_USER

    %% Event publishing
    USER_SVC -->|"Publish UserCreated / UserUpdated / UserDeprovisioned"| EVENT_PUB
    GROUP_SYNC -->|"Publish GroupSyncCompleted"| EVENT_PUB
    EVENT_PUB -->|"Write to iam.provisioning topic\n[Avro encoded, tenant-keyed partition]"| KAFKA_PROV

    %% Downstream consumers
    KAFKA_PROV -->|"Consume SCIMProvisionEvent"| AUDIT_CONS
    KAFKA_PROV -->|"Consume UserDeprovisioned"| SESS_NOTIFY
    KAFKA_PROV -->|"Consume all events"| ANALYTICS
    SESS_NOTIFY -->|"Revoke sessions for deprovisioned user"| SESS_NOTIFY

    %% Success response
    USER_SVC -->|"Provisioning complete"| RESP_200
    RESP_200 -->|"SCIM resource + ETag header"| SCIM_DIR
```

---

## 4. Data Protection Controls

### 4.1 Authentication Data Flow — Controls

| Data Element | Classification | In-Transit Control | At-Rest Control | Handling Constraint |
|---|---|---|---|---|
| Username (email) | PII | TLS 1.3 mandatory | Stored as normalised lowercase; not additionally encrypted | Never logged to application logs in plaintext |
| Password (raw) | Credential | TLS 1.3 mandatory | Never persisted; compared in-memory only | Zeroed from memory after bcrypt.Compare returns; not included in any log or trace |
| Password hash (bcrypt) | Credential | TLS 1.3 (DB wire) | Stored as bcrypt hash (cost 12) in PostgreSQL; column encrypted via Vault Transit | Never returned in any API response |
| TOTP seed | Credential | TLS 1.3 (DB wire) | AES-256-GCM via Vault Transit; stored as ciphertext | Never exposed outside the MFA Service; not included in audit events |
| Session ID | Session Token | TLS 1.3 · HttpOnly Secure cookie | Redis value encrypted with per-tenant key | 128-bit random; no user-inferrable data |
| JWT (access token) | Session Token | TLS 1.3 | Not stored; verified via public key | Claims must not include raw PII beyond `sub`, `email` (if requested scope) |
| Refresh token | Credential-class Token | TLS 1.3 · HttpOnly Secure cookie | PostgreSQL token family record; token value is SHA-256 hashed before storage | Rotated on every use; family revoked on reuse detection |
| Risk signals (IP, UA, fingerprint) | PII-adjacent | TLS 1.3 internal | Not persisted beyond risk score evaluation | Risk score stored; raw signals retained in audit only |

### 4.2 Authorization Data Flow — Controls

| Data Element | Classification | In-Transit Control | At-Rest Control | Handling Constraint |
|---|---|---|---|---|
| JWT claims (subject, tenant, scope) | PII + Session Token | mTLS between PEP and PDP | Not stored in PDP; passed as evaluation context | JWT must be re-validated on every request; PDP must not cache raw tokens |
| Policy rules (Rego bundles) | Operational | mTLS (PostgreSQL wire) | PostgreSQL encryption at rest | Policy bundles may not be returned in API responses to non-admin callers |
| Policy decision (Allow/Deny) | Operational | mTLS (gRPC) | Stored in Redis cache (60 s), then Kafka | Decision record must include policy ID for auditability |
| Resource path and parameters | Operational | mTLS | Included in Kafka decision record | Must be normalised before cache key generation to prevent cache-key injection |

### 4.3 SCIM Provisioning Data Flow — Controls

| Data Element | Classification | In-Transit Control | At-Rest Control | Handling Constraint |
|---|---|---|---|---|
| SCIM User resource (name, email, phone) | PII | TLS 1.3 (external) · mTLS (internal) | PostgreSQL column-level encryption for sensitive fields | PII fields must not appear in Kafka event payloads in plaintext; events use opaque IDs |
| SCIM Bearer token | Credential | TLS 1.3 | Stored as SHA-256 hash | Rotated every 90 days or on suspected compromise |
| External user ID (externalId) | PII-adjacent | TLS 1.3 (DB wire) | PostgreSQL; hashed for use as cache key | Must never be used as an authentication credential |
| SCIM sync cursor | Operational | TLS 1.3 (DB wire) | PostgreSQL | Cursor value is opaque; not derived from user data |
| Group membership delta | PII-adjacent | mTLS (internal) | Derived from user/group records; not independently stored | Group names must not be PII (e.g., do not name groups after individuals) |
