# Data Flow Diagram — Backend as a Service (BaaS) Platform

## 1. DFD Level 0 — System as a Black Box

This diagram shows all external entities and the data flows crossing the system boundary.

```mermaid
flowchart LR
    DEV["👤 Developer"]
    EU["👤 End User"]
    OPS["👤 Platform Operator"]
    IDP["🔑 Identity Provider"]
    PGEXT["🗄️ PostgreSQL Cluster"]
    OBJEXT["📦 Object Storage"]
    FNEXT["⚡ Function Runtime"]
    EVTEXT["📨 Event Broker"]
    VAULTEX["🔐 Secret Manager"]
    EMAIL["📧 Email / SMS"]
    CDN["🌐 CDN / Edge"]
    BILLING["💳 Billing System"]

    BAAS(["🏛️ BaaS Platform"])

    DEV -->|"API Keys, SDK calls\nProject config, Schema DDL\nFunction artifacts"| BAAS
    EU -->|"Auth credentials\nData queries / mutations\nFile uploads"| BAAS
    OPS -->|"Provider registration\nHealth override commands\nQuota adjustments"| BAAS

    BAAS -->|"JWT tokens, session cookies\nQuery results, file download URLs\nRealtime event messages"| EU
    BAAS -->|"Project stats, audit logs\nSchema versions, deploy statuses"| DEV
    BAAS -->|"System health reports\nUsage metrics, SLO data"| OPS

    BAAS -->|"OAuth2 auth requests\nToken validation calls"| IDP
    IDP -->|"User claims\nAccess tokens"| BAAS

    BAAS -->|"DDL statements\nParameterised SQL queries\nConnection pool requests"| PGEXT
    PGEXT -->|"Query result sets\nConnection acknowledgements"| BAAS

    BAAS -->|"PUT object (bytes)\nGET signed-URL requests\nDELETE object"| OBJEXT
    OBJEXT -->|"Upload confirmations\nETags, checksums"| BAAS

    BAAS -->|"Artifact deploy payload\nFunction invocation requests"| FNEXT
    FNEXT -->|"Execution results\nExit codes, stdout/stderr"| BAAS

    BAAS -->|"Publish domain events\nSubscription registration"| EVTEXT
    EVTEXT -->|"Delivered event messages\nDeadletter notifications"| BAAS

    BAAS -->|"SecretRef resolution requests"| VAULTEX
    VAULTEX -->|"Secret values (in-memory only)"| BAAS

    BAAS -->|"Email send requests\nSMS send requests"| EMAIL

    BAAS -->|"Asset URLs for distribution\nCache invalidation commands"| CDN

    BAAS -->|"Usage records (invocations,\nstorage GB, egress GB)"| BILLING
```

---

## 2. DFD Level 1 — Decomposed into Major Subsystems

```mermaid
flowchart TD
    DEV["👤 Developer"]
    EU["👤 End User"]
    OPS["👤 Operator"]

    subgraph GW["API Gateway"]
        JWT_VALIDATE["JWT / API Key\nValidation"]
        RATE_LIMIT["Rate Limiter"]
        ROUTER["Request Router"]
    end

    subgraph CP["Control Plane"]
        TENANT_MGMT["Tenant / Project /\nEnvironment Management"]
        BINDING_MGMT["CapabilityBinding\nManagement"]
        SWITCH_ORCH["Switchover\nOrchestrator"]
        PROV_REG["Provider\nRegistry"]
    end

    subgraph AUTH_SYS["Auth Subsystem"]
        USER_STORE["User Store\n(AuthUser)"]
        SESSION_STORE["Session Store\n(Redis)"]
        TOKEN_ISSUER["JWT Issuer"]
        IDP_BRIDGE["OAuth2 / OIDC\nBridge"]
    end

    subgraph DATA_SYS["Data Subsystem"]
        NS_MGMT["Namespace\nManagement"]
        SCHEMA_ENG["Schema / DDL\nEngine"]
        QUERY_PROXY["Query Proxy\n(RLS-aware)"]
    end

    subgraph STORE_SYS["Storage Subsystem"]
        BUCKET_MGMT["Bucket\nManagement"]
        UPLOAD_ENG["Upload\nEngine"]
        URL_SVC["Signed URL\nService"]
    end

    subgraph FN_SYS["Functions Subsystem"]
        DEPLOY_ENG["Deployment\nEngine"]
        INVOKE_ENG["Invocation\nEngine"]
        SCHED["Cron\nScheduler"]
    end

    subgraph EV_SYS["Events Subsystem"]
        CHAN_MGMT["Channel\nManagement"]
        PUB_ENG["Publish\nEngine"]
        DELIV_ENG["Delivery\nEngine"]
        DLQ_HDLR["Dead-Letter\nHandler"]
    end

    subgraph OPS_SYS["Operations Subsystem"]
        METER_SVC["Metering\nService"]
        AUDIT_SVC["Audit\nService"]
        SECRET_SVC["Secrets\nService"]
        SLO_ENG["SLO\nEngine"]
    end

    subgraph STORES["Data Stores"]
        PGCTL[(Control PG)]
        PGDAT[(Data Plane PG)]
        REDIS_S[(Redis)]
        NATS_S[(NATS)]
        OBJ_S[(Object Store)]
        VAULT_S[(Vault)]
        TSDB_S[(TimescaleDB)]
    end

    DEV -->|"Project setup, schema changes,\nfunction deploys"| GW
    EU -->|"Auth, data ops, file ops,\nrealtime connections"| GW
    OPS -->|"Provider config, quota rules"| GW

    GW --> JWT_VALIDATE --> RATE_LIMIT --> ROUTER

    ROUTER -->|"Control ops"| CP
    ROUTER -->|"Auth ops"| AUTH_SYS
    ROUTER -->|"Data ops"| DATA_SYS
    ROUTER -->|"Storage ops"| STORE_SYS
    ROUTER -->|"Function ops"| FN_SYS
    ROUTER -->|"Event ops"| EV_SYS

    CP --> PGCTL
    CP --> NATS_S
    CP --> SECRET_SVC

    AUTH_SYS --> PGDAT
    AUTH_SYS --> REDIS_S
    IDP_BRIDGE -->|"OAuth2 flows"| IDP_EXT["External IdPs"]

    DATA_SYS --> PGDAT
    STORE_SYS --> OBJ_S
    FN_SYS --> OBJ_S
    EV_SYS --> NATS_S

    NATS_S -->|"UsageSampled events"| METER_SVC
    NATS_S -->|"AuditEntry events"| AUDIT_SVC
    METER_SVC --> TSDB_S
    AUDIT_SVC --> PGCTL
    SECRET_SVC --> VAULT_S
    SLO_ENG --> TSDB_S
```

---

## 3. DFD Level 2 — Control Plane Detail (Provider Binding, Switchover, Audit)

```mermaid
flowchart TD
    DEV["👤 Developer"]
    OPS["👤 Operator"]

    subgraph CP["Control Plane Service"]
        ENV_API["Environment\nAPI Handler"]
        BIND_API["CapabilityBinding\nAPI Handler"]
        SWITCH_API["Switchover Plan\nAPI Handler"]
        PROV_PROBE["Provider Health\nProbe Scheduler"]
        BIND_ACT["Binding Activator\n(state machine)"]
        SWITCH_EXEC["Switchover\nExecutor"]
        ROLLBACK["Rollback\nController"]
        AUDIT_PUB["Audit Event\nPublisher"]
    end

    subgraph PROV_REG["Provider Registry"]
        CATALOG["Catalog Store\n(ProviderCatalogEntry)"]
        ADAPTER_LOAD["Adapter Loader\n(plugin registry)"]
        HEALTH_CACHE["Health Result\nCache"]
    end

    subgraph OPS_PLANE["Operations Subsystem"]
        AUDIT_SVC["Audit Service\n(Consumer)"]
        SECRET_SVC["Secrets Service"]
        SLO_ENG["SLO Engine"]
    end

    PGCTL[(Control PG\ncontrol schema)]
    NATS_BUS[(NATS JetStream)]
    VAULT_S[(Vault)]
    TSDB[(TimescaleDB)]

    DEV -->|"POST /environments"| ENV_API
    DEV -->|"POST /bindings"| BIND_API
    DEV -->|"POST /switchover-plans"| SWITCH_API
    OPS -->|"PUT /providers\nregister catalog entry"| CATALOG

    ENV_API -->|"INSERT environment record"| PGCTL
    ENV_API -->|"Publish EnvironmentProvisioned"| NATS_BUS

    BIND_API -->|"Validate config schema\nagainst ProviderCatalogEntry"| CATALOG
    BIND_API -->|"Resolve SecretRef\nfrom config"| SECRET_SVC
    SECRET_SVC -->|"Read secret value"| VAULT_S
    SECRET_SVC -->|"Return resolved config"| BIND_API
    BIND_API -->|"Trigger readiness probe"| PROV_PROBE
    PROV_PROBE -->|"Run probe via adapter"| ADAPTER_LOAD
    ADAPTER_LOAD -->|"Probe result"| HEALTH_CACHE
    HEALTH_CACHE -->|"HealthProbeResult"| BIND_ACT
    BIND_ACT -->|"Transition: PENDING → ACTIVE\nor PENDING → DEGRADED"| PGCTL
    BIND_ACT -->|"Publish BindingActivated\nor BindingDegraded"| NATS_BUS

    SWITCH_API -->|"INSERT switchover plan\n(status: DRAFT)"| PGCTL
    SWITCH_API -->|"Publish SwitchoverPlanCreated"| NATS_BUS
    OPS -->|"PUT /switchover-plans/{id}/approve"| SWITCH_EXEC
    SWITCH_EXEC -->|"UPDATE status: APPROVED → IN_PROGRESS"| PGCTL
    SWITCH_EXEC -->|"Activate toBinding"| BIND_ACT
    SWITCH_EXEC -->|"Shift traffic gradually\n(CANARY: 10% → 50% → 100%)"| ADAPTER_LOAD
    SWITCH_EXEC -->|"Read error-rate metric"| SLO_ENG
    SLO_ENG -->|"Query error_rate > threshold?"| TSDB
    SLO_ENG -->|"RollbackTrigger fired"| ROLLBACK
    ROLLBACK -->|"Re-activate fromBinding"| BIND_ACT
    ROLLBACK -->|"UPDATE status: ROLLED_BACK"| PGCTL
    ROLLBACK -->|"Publish SwitchoverRolledBack"| NATS_BUS

    NATS_BUS -->|"All control events"| AUDIT_PUB
    AUDIT_PUB -->|"Publish AuditEntry\n{actor, action, before, after}"| NATS_BUS
    NATS_BUS -->|"Consume AuditEntry"| AUDIT_SVC
    AUDIT_SVC -->|"INSERT audit_logs (append-only)"| PGCTL
```

---

## 4. Error Signal Flow

This diagram shows how errors propagate from adapter calls through the SLO engine and back to the developer.

```mermaid
flowchart TD
    ADAPTER["Provider Adapter\n(DB / Storage / Function)"]
    CB["Circuit Breaker\n(per adapter instance)"]
    ERR_NORM["Error Normaliser\n(maps provider errors\nto BaaS error codes)"]
    SLO_ENG["SLO Engine\n(error-rate sliding window)"]
    NATS_ERR["NATS\nbaas.{envId}.errors"]
    BIND_SM["CapabilityBinding\nState Machine"]
    DEV_RESP["Developer\n(API Response)"]
    METR["Metering Service\n(error counter)"]
    ALERT["Alertmanager\n(PagerDuty / Slack)"]
    OPS["👤 Operator"]

    ADAPTER -->|"Provider error\n(connection timeout,\nSQL error, HTTP 5xx)"| CB
    CB -->|"OPEN: fast-fail\nCLOSED: pass through"| ERR_NORM
    ERR_NORM -->|"BaaS error code\n+ HTTP status"| DEV_RESP
    ERR_NORM -->|"Emit ErrorOccurred event\n{adapter, code, latencyMs}"| NATS_ERR
    NATS_ERR -->|"Consume error events"| SLO_ENG
    SLO_ENG -->|"error_rate > threshold\n→ BindingDegraded signal"| BIND_SM
    BIND_SM -->|"ACTIVE → DEGRADED\nPublish BindingDegraded"| NATS_ERR
    NATS_ERR -->|"Increment error counters"| METR
    METR -->|"Metric: baas_adapter_errors_total\n> alert threshold"| ALERT
    ALERT -->|"Page on-call engineer"| OPS
    OPS -->|"Investigate, potentially\napprove SwitchoverPlan"| BIND_SM
```

---

## 5. Data Store Summary Table

| Store Name | Type | Data Owner | Access Pattern | Retention Policy |
|---|---|---|---|---|
| PostgreSQL — control schema | OLTP Relational | Control Plane Service | Point queries by ID; joins for tenant hierarchy | Until explicit deletion; soft-delete with 30-day purge |
| PostgreSQL — audit schema | Append-only Relational | Audit Service | Append writes; bulk reads for compliance export | 90 days (FREE), 1 year (PRO/ENTERPRISE); partition drop |
| PostgreSQL — metering schema | OLTP Relational (aggregated) | Metering Service | Write aggregates per window; read for billing | 13 months rolling |
| PostgreSQL — data plane schema | OLTP Relational (per env) | Data Service (developer-owned data) | Developer-defined queries; RLS-filtered | Developer-controlled; soft-delete + 7-day grace |
| Redis Cluster | In-memory Key-Value | Auth Service (sessions); API Gateway (idempotency, rate-limit) | GET/SET/DEL by key; sliding window counters | Sessions: TTL = access token expiry; Idempotency keys: 24h TTL |
| NATS JetStream | Distributed Message Log | Platform-wide (event bus) | Publish by subject; consume by consumer group | Stream retention: 7 days or 10 GB per stream |
| Object Storage (S3/R2/GCS) | Blob Store | Storage Service (file objects); Functions Service (artifacts) | PUT/GET/DELETE by key; presigned URL | FileObjects: per-Bucket `retentionDays` setting; Artifacts: until function deleted |
| TimescaleDB | Time-Series | Metering Service; SLO Engine | INSERT time-series rows; continuous aggregates; range queries | Hypertable retention: 13 months; compressed chunks after 7 days |
| HashiCorp Vault | Encrypted KV Store | Secrets Service | Read by path (`baas/{tenantId}/{alias}`); lease renewal | Per-secret TTL; no auto-purge; manual rotation |

---

## 6. Data Classification Table

| Data Category | Examples | Classification Level | Encryption at Rest | Encryption in Transit |
|---|---|---|---|---|
| Tenant credentials | API keys, billing info | **Confidential** | AES-256 (Vault-managed) | TLS 1.3 mandatory |
| Auth user credentials | Password hashes, MFA secrets | **Confidential** | Argon2id hash + DB encryption | TLS 1.3 mandatory |
| Session tokens (access) | JWT bearer tokens | **Confidential** | Stored encrypted in Redis | TLS 1.3; short TTL (15 min) |
| Session tokens (refresh) | Opaque refresh tokens | **Confidential** | Hashed in DB (HMAC-SHA256) | TLS 1.3 |
| CapabilityBinding config | DB passwords, S3 keys | **Confidential** | SecretRef only; values in Vault | Vault API uses TLS 1.3 |
| Developer schema / table definitions | Column names, types, RLS policies | **Internal** | PostgreSQL transparent encryption | TLS 1.3 |
| Developer data rows | Application domain data | **Varies (developer-defined)** | PostgreSQL TDE; column-level encryption option | TLS 1.3 |
| File object bytes | User uploads, documents | **Varies (developer-defined)** | SSE-S3 / SSE-KMS at storage layer | TLS 1.3; signed URL HTTPS |
| Function artifacts | OCI images, ZIP bundles | **Internal** | Registry encryption at rest | TLS 1.3 |
| Execution logs | Function stdout/stderr | **Internal** | Object storage SSE | TLS 1.3 |
| Audit log entries | Actor, action, before/after snapshots | **Confidential** | AES-256 at PostgreSQL level; before/after JSON encrypted | TLS 1.3 |
| Usage metrics | Invocation counts, storage GB | **Internal** | TimescaleDB standard encryption | TLS 1.3 |
| Public file objects | Developer-designated public assets | **Public** | SSE (transparent) | HTTPS via CDN; HTTP allowed if explicitly enabled |
