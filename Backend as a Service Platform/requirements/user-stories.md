# User Stories — Backend as a Service (BaaS) Platform

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-01  

---

## Table of Contents

1. [Actor Overview](#1-actor-overview)
2. [Project Owner / Tenant Admin Stories](#2-project-owner--tenant-admin-stories)
3. [App Developer Stories](#3-app-developer-stories)
4. [Application End User Stories](#4-application-end-user-stories)
5. [Platform Operator Stories](#5-platform-operator-stories)
6. [Security / Compliance Admin Stories](#6-security--compliance-admin-stories)
7. [Adapter Maintainer Stories](#7-adapter-maintainer-stories)
8. [Story Summary Table](#8-story-summary-table)

---

## 1. Actor Overview

| Actor | Description |
|-------|-------------|
| **Project Owner / Tenant Admin** | The organization or individual that owns a Tenant. Creates projects, manages environments, configures providers, controls billing and quotas. |
| **App Developer** | A developer building an application on top of the BaaS Platform. Interacts with Auth, Database, Storage, Functions, and Realtime APIs. |
| **Application End User** | The human user of an application built on the platform. Does not interact directly with the BaaS Platform but is subject to its auth policies, data access controls, and privacy settings. |
| **Platform Operator** | The DevOps/SRE team responsible for deploying, monitoring, and maintaining the BaaS Platform itself. |
| **Security / Compliance Admin** | Responsible for audit logs, RBAC policies, secret rotation, and compliance reporting across all tenants. |
| **Adapter Maintainer** | Platform Engineering team member who builds, tests, and publishes provider adapters to the Provider Catalog. |

---

## 2. Project Owner / Tenant Admin Stories

---

### US-001 — Create a New Project

**As a** Project Owner,  
**I want** to create a new Project with development, staging, and production environments in a single workflow,  
**so that** my development team has isolated, properly configured environments from day one without manual setup.

**Acceptance Criteria:**
- Submitting a valid project creation request returns a Project resource with three pre-created Environment objects within 30 seconds.
- Each Environment has a unique, scoped API key generated automatically.
- A `ProjectCreated` and three `EnvironmentProvisioned` events are visible in the Audit Log.
- The project is immediately accessible via the web console and API with the owner's credentials.
- Attempting to create a second project when the tenant's project quota is exhausted returns HTTP 429 with a descriptive quota-exceeded error.

---

### US-002 — Configure a Storage Provider Binding

**As a** Project Owner,  
**I want** to bind my production environment's storage capability to an AWS S3 bucket I control,  
**so that** all file uploads from my application are stored in my own S3 account under my own access policies.

**Acceptance Criteria:**
- I can create a CapabilityBinding by specifying the provider type (`aws-s3`), region, bucket name, and a SecretRef pointing to my IAM credentials in AWS Secrets Manager.
- The platform performs a connectivity check (list-bucket test) at binding creation time and rejects the binding if it fails.
- The raw IAM secret value never appears in any API response or log.
- The binding is environment-scoped; the production binding does not affect staging.
- A `BindingActivated` event is recorded in the Audit Log with the actor's identity.

---

### US-003 — Rotate an API Key Without Downtime

**As a** Project Owner,  
**I want** to rotate an environment's API key using a two-key overlap window,  
**so that** I can issue a new key to my team before invalidating the old one, avoiding service disruption.

**Acceptance Criteria:**
- A key rotation request generates a new API key while keeping the old key valid for a configurable overlap period (default 24 hours).
- After the overlap period, the old key is automatically invalidated.
- Both keys are simultaneously valid during the overlap window.
- An API call using the old key after invalidation returns HTTP 401 with a `key_rotated` error code.
- A `ApiKeyRotated` event is logged with actor, timestamp, and the old key's last-four characters (not the full value).

---

### US-004 — Enforce Resource Quotas

**As a** Project Owner,  
**I want** to set monthly limits on storage usage and function invocations for my project,  
**so that** unexpected spikes in usage do not result in runaway cloud costs.

**Acceptance Criteria:**
- Quota limits can be configured per environment via the Control Plane API.
- When 80% of a quota is reached, a `QuotaWarning` event is emitted and an email notification is sent to the billing contact.
- When 100% is reached, further operations in that category return HTTP 429 until the next billing period or until the limit is raised.
- Quota usage is visible in near-real-time (< 60-second lag) on the console dashboard.
- Quota changes take effect within 5 minutes of API call.

---

### US-005 — Soft-Delete a Project

**As a** Project Owner,  
**I want** to soft-delete a project and have a 30-day window to recover it,  
**so that** accidental deletion does not result in immediate irreversible data loss.

**Acceptance Criteria:**
- Soft-deleting a project sets its status to `frozen`; all API calls against it return HTTP 423 (Locked).
- The project and all its resources remain readable by the owner in the console during the 30-day window.
- The owner can restore the project within 30 days, returning it to `active` status.
- After 30 days, the project and all associated resources are permanently deleted in a background job.
- A `TenantDeleted` event is emitted at permanent deletion time and is retained in the immutable audit log even after resource cleanup.

---

### US-006 — Initiate a Provider Switchover

**As a** Project Owner,  
**I want** to migrate my production storage capability from AWS S3 to GCP Cloud Storage using a guided switchover plan,  
**so that** I can change cloud providers without downtime or data loss.

**Acceptance Criteria:**
- I can create a SwitchoverPlan specifying the source binding and target binding.
- The platform validates that the target binding is active and the provider is healthy before allowing the plan to move to `ready` state.
- The plan can be executed, paused, and rolled back through the API.
- During execution, the platform blocks new write operations on the source provider and copies data to the target.
- A rollback restores the original binding and re-enables the source provider within 5 minutes.
- All state transitions emit corresponding events: `SwitchoverStarted`, `SwitchoverCompleted`, `SwitchoverRolledBack`.

---

## 3. App Developer Stories

---

### US-007 — Register a User via Email/Password

**As an** App Developer,  
**I want** to register new users in my app using email and password through the BaaS Auth API,  
**so that** I don't need to implement and maintain my own authentication system.

**Acceptance Criteria:**
- A POST to `/v1/auth/register` with email and password creates a new user and returns a JWT access token and refresh token.
- Passwords are validated for minimum length (8 characters) and must include at least one non-alphabetic character.
- Attempting to register with an already-registered email returns HTTP 409 with error code `email_taken`.
- The user's password hash (bcrypt, cost ≥ 12) is stored but the plaintext password is never logged or returned.
- A `UserRegistered` event is emitted and recorded in the Audit Log.

---

### US-008 — Implement OAuth2 Login

**As an** App Developer,  
**I want** to enable Google OAuth2 login for my app using the BaaS Auth API,  
**so that** users can sign in with their existing Google account without creating a new password.

**Acceptance Criteria:**
- Configuring a Google OAuth2 provider requires only a client ID and a SecretRef to the client secret.
- The platform handles the OIDC redirect, code exchange, and token validation.
- On first OAuth2 login, a user account is created automatically.
- On subsequent logins, the existing account is matched by provider subject ID.
- The returned JWT includes the same claims structure as email/password login for consistent client-side handling.

---

### US-009 — Define a Database Table via API

**As an** App Developer,  
**I want** to define a database table with typed columns using the BaaS API,  
**so that** I can store and query structured data without writing raw SQL or managing migrations manually.

**Acceptance Criteria:**
- POST `/v1/db/namespaces/{ns}/tables` with a column schema creates the table in the underlying PostgreSQL schema.
- Supported column types include: `text`, `integer`, `bigint`, `boolean`, `uuid`, `jsonb`, `timestamptz`, `numeric`, and their array variants.
- Table creation returns the table definition including auto-generated `id` (UUID), `created_at`, and `updated_at` columns.
- Attempting to create a table with an unsupported column type returns HTTP 422 with a descriptive error.
- The table is immediately queryable via the CRUD API.

---

### US-010 — Query Records with Filters

**As an** App Developer,  
**I want** to query records using structured filter expressions via the BaaS Database API,  
**so that** I can retrieve only the data relevant to my use case without downloading and filtering client-side.

**Acceptance Criteria:**
- GET `/v1/db/namespaces/{ns}/tables/{table}/records` accepts a `filter` query parameter as a JSON-encoded filter object.
- Filters support: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `in`, `is_null` operators.
- Compound filters with `$and` / `$or` are supported up to 3 levels of nesting.
- Pagination is supported via `limit` (max 1000) and `cursor` (keyset pagination) parameters.
- Results include a `next_cursor` field when more pages exist.
- A request with a filter referencing a non-existent column returns HTTP 422.

---

### US-011 — Apply a Schema Migration

**As an** App Developer,  
**I want** to apply a versioned schema migration to my development environment,  
**so that** I can evolve my database schema iteratively and promote changes to production safely.

**Acceptance Criteria:**
- Uploading a migration with `up` and `down` SQL scripts creates a `MigrationPending` record.
- The platform validates SQL syntax before accepting the migration; syntactically invalid SQL is rejected with HTTP 422.
- Applying the migration in development executes the `up` script and records a `MigrationApplied` event.
- Attempting to apply the same migration version twice returns HTTP 409.
- The migration cannot be promoted to production unless it has been applied in staging first.

---

### US-012 — Upload a File to Storage

**As an** App Developer,  
**I want** to upload files to a private bucket and retrieve them via signed URLs,  
**so that** my application can store user-generated content securely without exposing raw provider credentials.

**Acceptance Criteria:**
- POST `/v1/storage/buckets/{bucketId}/files` with a multipart form upload stores the file in the configured provider.
- File metadata (name, size, MIME type, SHA-256 checksum, owner user ID) is stored in PostgreSQL.
- The API returns the file's metadata record and a pre-signed URL valid for 1 hour.
- Accessing the file via a signed URL after expiry returns HTTP 403.
- A second request to `/v1/storage/files/{fileId}/signed-url` generates a new signed URL with configurable expiry.

---

### US-013 — Deploy and Invoke a Serverless Function

**As an** App Developer,  
**I want** to deploy a Node.js function as a ZIP artifact and invoke it via HTTP,  
**so that** I can run custom server-side logic without managing servers.

**Acceptance Criteria:**
- POST `/v1/functions` with a ZIP artifact and runtime specification (`node18`, `python311`, `go121`) creates a FunctionDefinition.
- The function becomes invokable within 60 seconds of deployment.
- GET `/v1/functions/{functionId}/invoke` (or POST for HTTP-trigger functions) executes the function and returns its response.
- The function's stdout/stderr are captured and accessible via GET `/v1/functions/executions/{executionId}/logs`.
- Invocations exceeding the timeout return HTTP 504 with error code `execution_timeout`.

---

### US-014 — Schedule a Recurring Job

**As an** App Developer,  
**I want** to schedule a function to run every day at midnight UTC,  
**so that** I can perform nightly data processing without an external scheduler.

**Acceptance Criteria:**
- A cron schedule is defined with a CRON expression (`0 0 * * *`) and associated with a FunctionDefinition.
- The function fires within ±30 seconds of the scheduled time.
- Each scheduled execution has a unique `execution_id`; duplicate firings within the same scheduled slot are deduplicated.
- Failed scheduled executions are retried up to 3 times with exponential backoff.
- The execution history (status, duration, logs) is queryable for the past 7 days.

---

### US-015 — Subscribe to Realtime Events

**As an** App Developer,  
**I want** to subscribe to a private EventChannel via WebSocket,  
**so that** my application can push real-time updates to connected clients without polling.

**Acceptance Criteria:**
- A WebSocket connection to `wss://api.baas.example.com/v1/realtime` with a valid JWT in the `Authorization` header succeeds.
- Sending a `subscribe` message for a private channel the user is authorized for results in a `subscribed` acknowledgement.
- Messages published to the channel are received by all subscribers within 500 ms.
- A subscriber attempting to join a channel they are not authorized for receives an `authorization_denied` message and the connection remains open.
- The WebSocket connection is automatically resumed with message replay on reconnect within 60 seconds.

---

### US-016 — Register a Webhook

**As an** App Developer,  
**I want** to register a webhook endpoint to receive notifications when new files are uploaded to a specific bucket,  
**so that** my backend can react to storage events without polling.

**Acceptance Criteria:**
- POST `/v1/realtime/webhooks` with a target URL, event filter (`storage.file.uploaded`), and bucket ID creates a Webhook Subscription.
- The platform delivers a POST request to the webhook URL within 10 seconds of the triggering event.
- Each delivery includes an `X-BaaS-Signature` header containing an HMAC-SHA256 of the payload with the subscription's secret.
- Failed deliveries are retried up to 5 times with exponential backoff.
- After 5 failures, the subscription is marked `suspended` and a `WebhookDeliveryFailed` event is logged.

---

### US-017 — Configure Row-Level Security

**As an** App Developer,  
**I want** to define an RLS policy that restricts users to viewing only their own records in the `posts` table,  
**so that** users cannot access each other's data even if they craft arbitrary filter requests.

**Acceptance Criteria:**
- POST `/v1/db/namespaces/{ns}/tables/{table}/policies` accepts a policy name, role, and SQL predicate (e.g., `user_id = current_user_id()`).
- The policy is applied to the PostgreSQL table immediately after creation.
- A request authenticated as `user-A` cannot return rows where `user_id = user-B` regardless of filter parameters.
- A project admin with the `admin` role bypasses RLS by default (configurable).
- Attempting to define a policy with an invalid SQL predicate returns HTTP 422.

---

### US-018 — Inject Secrets into Functions

**As an** App Developer,  
**I want** to inject a third-party API key into my function as an environment variable sourced from AWS Secrets Manager,  
**so that** the secret is never hardcoded in my code or visible in the platform API.

**Acceptance Criteria:**
- A SecretRef is created pointing to a path in AWS Secrets Manager.
- The SecretRef can be associated with a FunctionDefinition as an environment variable mapping.
- At invocation time, the platform resolves the secret value and injects it into the function's environment.
- The resolved secret value does not appear in the ExecutionRecord, logs, or any API response.
- If the secret cannot be resolved at invocation time, the invocation fails with error code `secret_resolution_failed`.

---

## 4. Application End User Stories

---

### US-019 — Register and Log In to an Application

**As an** Application End User,  
**I want** to register with my email address and log in to the application,  
**so that** I can access my personal data and features securely.

**Acceptance Criteria:**
- The registration form accepts email and password; the BaaS Auth API creates my account within 1 second.
- After login, I receive a session token that keeps me authenticated for the configured session duration.
- My password is never transmitted in plaintext (only over HTTPS) and is not visible to the application developer.
- I can log out, which immediately invalidates my session.
- If I forget my password, I can request a password reset link that is valid for 1 hour and single-use.

---

### US-020 — Control My Personal Data

**As an** Application End User,  
**I want** to request deletion of all my personal data from an application,  
**so that** I can exercise my GDPR right to erasure.

**Acceptance Criteria:**
- Submitting a deletion request marks my account for erasure.
- Within 30 days, all PII fields (email, name, profile data) are purged from the platform database.
- Files I own in private buckets are deleted.
- My user ID in non-PII tables is replaced with a tombstone placeholder, preserving referential integrity.
- A deletion certificate event is emitted to the Audit Log confirming completion.

---

### US-021 — Use Passwordless (Magic Link) Login

**As an** Application End User,  
**I want** to log in using a magic link sent to my email,  
**so that** I don't have to remember a password.

**Acceptance Criteria:**
- Requesting a magic link sends an email within 5 seconds.
- The magic link is valid for exactly 15 minutes and for a single use.
- Clicking the link authenticates me and redirects to the application with a valid session token.
- Attempting to use the same link a second time returns an `invalid_or_expired_token` error.
- If I request a new magic link, all previous links for my account are invalidated.

---

## 5. Platform Operator Stories

---

### US-022 — Deploy the Platform to a Kubernetes Cluster

**As a** Platform Operator,  
**I want** to deploy all BaaS Platform services to a Kubernetes cluster using Helm charts,  
**so that** I can manage the platform lifecycle with standard Kubernetes tooling.

**Acceptance Criteria:**
- A `helm install baas ./charts/baas` with a values file completes without error and all pods reach `Running` state within 5 minutes.
- Each service's Deployment exposes a `/health` endpoint; readiness probes prevent traffic before the service is ready.
- The Helm chart supports configuring external PostgreSQL, Redis, and secret store endpoints via values.
- A `helm upgrade` with a new image tag performs a rolling update with zero-downtime.
- Resource requests and limits are defined for every container.

---

### US-023 — Monitor Platform Health and SLOs

**As a** Platform Operator,  
**I want** to monitor real-time request rates, error rates, and latency percentiles for all services in a Grafana dashboard,  
**so that** I can detect and respond to SLO breaches before they impact tenants.

**Acceptance Criteria:**
- Each service exposes a `/metrics` endpoint in Prometheus text format.
- A pre-built Grafana dashboard is included in the repository showing p50/p95/p99 latency, request rate, and error rate per service.
- Alerts are configured for: error rate > 1% for 5 minutes, p99 latency > 1 s for 5 minutes, any service pod restart.
- Metrics are available with < 15-second scrape lag.
- The platform's SLO burn-rate alert fires when the 1-hour error budget is 5% consumed.

---

### US-024 — Rotate the Platform's Internal Signing Keys

**As a** Platform Operator,  
**I want** to rotate the RSA key pair used to sign JWTs without invalidating existing active sessions,  
**so that** I can maintain cryptographic hygiene without forcing user logouts.

**Acceptance Criteria:**
- A new RSA key pair can be added to the Auth Service's key set via the operator API.
- New tokens are signed with the new key; existing tokens signed with the old key continue to be validated during a configurable overlap period.
- After the overlap period, the old key is removed from the validation set.
- The JWKS endpoint (`/.well-known/jwks.json`) is updated to include both keys during the overlap period.
- Key rotation is recorded in the Audit Log.

---

### US-025 — Scale a Service Under Load

**As a** Platform Operator,  
**I want** to horizontally scale the Realtime Service to handle a traffic spike,  
**so that** WebSocket connection quality is maintained during high-load events.

**Acceptance Criteria:**
- Increasing the replica count of the Realtime Service Deployment routes new WebSocket connections to new pods.
- Existing connections are not dropped during scaling events.
- WebSocket message delivery across pods is synchronized via the shared Redis pub/sub layer.
- Scaling down to the original replica count after the spike drains connections gracefully.
- Horizontal Pod Autoscaler (HPA) based on CPU/memory can be enabled via Helm values.

---

## 6. Security / Compliance Admin Stories

---

### US-026 — Review the Audit Log for a Security Incident

**As a** Security Admin,  
**I want** to query the Audit Log for all actions performed by a specific user in a specific time window,  
**so that** I can investigate a suspected unauthorized access incident.

**Acceptance Criteria:**
- GET `/v1/audit-log` supports filtering by: actor user ID, resource type, date range, and action type.
- Results are returned in descending time order and support pagination.
- Each entry includes: timestamp, actor ID, actor IP, resource type, resource ID, action, and a before/after snapshot.
- Audit log entries cannot be deleted or modified via any API call.
- The query returns results within 2 seconds for date ranges up to 90 days.

---

### US-027 — Rotate All Secrets for a Compromised Environment

**As a** Security Admin,  
**I want** to trigger a bulk secret rotation for all SecretRefs in a compromised environment,  
**so that** I can revoke access for any attacker who obtained secrets before the compromise was detected.

**Acceptance Criteria:**
- POST `/v1/environments/{envId}/rotate-secrets` triggers asynchronous rotation of all SecretRefs in the environment.
- The rotation status is queryable and shows a per-secret status (pending / rotated / failed).
- Functions that reference rotated secrets automatically pick up the new values on the next invocation.
- A `SecretRotated` event is logged for each rotated secret.
- The API key for the environment is also invalidated and a new one issued as part of the rotation.

---

### US-028 — Export Audit Logs to SIEM

**As a** Security Admin,  
**I want** to continuously stream audit log events to our SIEM (Splunk) via a webhook sink,  
**so that** we have a unified security event view across all our systems.

**Acceptance Criteria:**
- I can configure an audit log export destination with a Syslog/webhook endpoint and authentication credentials.
- Events are delivered to the SIEM within 60 seconds of being recorded.
- Each event is structured JSON conforming to the platform's event schema.
- Delivery failures are retried; if the SIEM is unreachable for more than 1 hour an alert is raised.
- The SIEM export configuration itself is recorded in the Audit Log.

---

### US-029 — Configure GDPR Data Retention Policies

**As a** Security/Compliance Admin,  
**I want** to configure automatic data retention and purge policies for each project,  
**so that** we comply with GDPR data minimization requirements without manual intervention.

**Acceptance Criteria:**
- Retention policies can be set for: execution logs (default 7 days), audit logs (minimum 1 year), file metadata (configurable), user PII (requires explicit retention period).
- Purge jobs run daily and delete data exceeding the configured retention period.
- A `DataPurgeCompleted` event is emitted after each purge run with a count of records deleted per category.
- Retention policy changes are logged in the Audit Log.
- It is not possible to set an audit log retention period of less than 1 year via the API.

---

## 7. Adapter Maintainer Stories

---

### US-030 — Publish a New Storage Adapter

**As an** Adapter Maintainer,  
**I want** to publish a new MinIO storage adapter to the Provider Catalog,  
**so that** tenants can bind their storage capability to a self-hosted MinIO instance.

**Acceptance Criteria:**
- An adapter is registered in the catalog by submitting a `ProviderCatalogEntry` with: type (`storage`), name (`minio`), version, configuration schema (JSON Schema), and adapter image reference.
- The catalog entry is validated: configuration schema must be a valid JSON Schema, required fields must include `endpoint`, `access_key_id`, and `secret_access_key_ref`.
- Once registered, the adapter is immediately available for use in CapabilityBindings.
- The adapter's connectivity check method is invoked during CapabilityBinding creation to validate credentials.
- Deprecating an adapter version prevents new bindings but does not affect existing active bindings.

---

### US-031 — Version and Deprecate an Adapter

**As an** Adapter Maintainer,  
**I want** to release a new version of the AWS S3 adapter with support for S3 Transfer Acceleration,  
**so that** tenants can opt into the new capability without being forced to migrate.

**Acceptance Criteria:**
- A new catalog entry `aws-s3@2.0.0` is registered alongside the existing `aws-s3@1.x`.
- Existing bindings continue to use their pinned version.
- Tenants can voluntarily upgrade their binding to the new version.
- The old version can be deprecated with a sunset date; tenants with active bindings on a deprecated version receive a deprecation warning.
- After the sunset date, bindings on the deprecated version are blocked from creating new operations.

---

### US-032 — Validate Adapter Configuration Schema

**As an** Adapter Maintainer,  
**I want** to define a JSON Schema that validates all required and optional configuration fields for my adapter,  
**so that** tenants receive immediate, clear validation errors when they misconfigure a binding.

**Acceptance Criteria:**
- The JSON Schema is validated by the catalog service at registration time using a JSON Schema validator.
- When a tenant submits a CapabilityBinding with a configuration that fails schema validation, the response includes a detailed list of validation errors with field paths.
- Optional fields have documented defaults in the schema.
- The schema distinguishes between fields that are plain values and fields that must be SecretRefs.
- Schema changes to existing catalog entries require a new adapter version (minor or patch bump).

---

## 8. Story Summary Table

| ID | Actor | Title | Priority | FR Refs |
|----|-------|-------|----------|---------|
| US-001 | Project Owner | Create a New Project | Must | FR-001–FR-004 |
| US-002 | Project Owner | Configure Storage Provider Binding | Must | FR-051–FR-052 |
| US-003 | Project Owner | Rotate API Key Without Downtime | Must | FR-006 |
| US-004 | Project Owner | Enforce Resource Quotas | Must | FR-005 |
| US-005 | Project Owner | Soft-Delete a Project | Should | FR-007 |
| US-006 | Project Owner | Initiate Provider Switchover | Must | FR-053–FR-055 |
| US-007 | App Developer | Register User via Email/Password | Must | FR-009 |
| US-008 | App Developer | Implement OAuth2 Login | Must | FR-010 |
| US-009 | App Developer | Define Database Table via API | Must | FR-019–FR-020 |
| US-010 | App Developer | Query Records with Filters | Must | FR-021–FR-022 |
| US-011 | App Developer | Apply Schema Migration | Must | FR-024–FR-026 |
| US-012 | App Developer | Upload File to Storage | Must | FR-029–FR-031 |
| US-013 | App Developer | Deploy and Invoke Serverless Function | Must | FR-036–FR-037 |
| US-014 | App Developer | Schedule Recurring Job | Should | FR-037, FR-043 |
| US-015 | App Developer | Subscribe to Realtime Events | Must | FR-044–FR-046 |
| US-016 | App Developer | Register Webhook | Must | FR-047–FR-048 |
| US-017 | App Developer | Configure Row-Level Security | Must | FR-023 |
| US-018 | App Developer | Inject Secrets into Functions | Must | FR-041, FR-057 |
| US-019 | End User | Register and Log In | Must | FR-009–FR-010 |
| US-020 | End User | Control Personal Data (GDPR) | Must | NFR-023 |
| US-021 | End User | Passwordless Magic Link Login | Should | FR-011 |
| US-022 | Platform Operator | Deploy to Kubernetes | Must | NFR-015, NFR-020 |
| US-023 | Platform Operator | Monitor Health and SLOs | Must | FR-064, FR-067 |
| US-024 | Platform Operator | Rotate JWT Signing Keys | Must | FR-006, NFR-017 |
| US-025 | Platform Operator | Scale Service Under Load | Must | NFR-007–NFR-008 |
| US-026 | Security Admin | Review Audit Log | Must | FR-058 |
| US-027 | Security Admin | Rotate Secrets for Compromised Environment | Must | FR-057, NFR-016 |
| US-028 | Security Admin | Export Audit Logs to SIEM | Should | FR-062 |
| US-029 | Security Admin | Configure GDPR Retention Policies | Must | FR-059, NFR-023 |
| US-030 | Adapter Maintainer | Publish New Storage Adapter | Must | FR-050 |
| US-031 | Adapter Maintainer | Version and Deprecate Adapter | Should | FR-050 |
| US-032 | Adapter Maintainer | Validate Adapter Config Schema | Must | FR-051–FR-052 |
