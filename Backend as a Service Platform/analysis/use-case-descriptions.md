# Use Case Descriptions — Backend as a Service (BaaS) Platform

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-01  

---

## UC-001: Tenant Onboarding and Project Setup

**ID:** UC-001  
**Name:** Tenant Onboarding and Project Setup  
**Actors:** Project Owner (Primary), Platform Operator (Secondary — approves enterprise tenants)  
**Related User Stories:** US-001, US-002, US-003, US-004  
**Related Business Rules:** BR-02, BR-03, BR-04, BR-09  

### Preconditions
- The platform is running and the onboarding endpoint is accessible.
- The Project Owner has a valid registration email and organization name.
- If enterprise tier: a Platform Operator has pre-authorized the tenant's domain.

### Main Flow

1. The Project Owner navigates to the sign-up page and submits their name, email, organization name, and desired tenant slug.
2. The Control Plane validates: slug uniqueness, email format, no existing account for the email.
3. The system creates a `Tenant` record (status: `active`, tier: `free`) and a personal admin `AuthUser`.
4. A `TenantCreated` event is emitted. The Notification Service sends a welcome email with an email verification link.
5. The Project Owner verifies their email address (single-use token, 24-hour expiry).
6. The Project Owner logs into the console using their credentials. The Auth Service issues a JWT.
7. The Project Owner clicks "Create Project" and provides a project name and slug.
8. The Control Plane validates slug uniqueness within the tenant and creates the `Project` record.
9. A `ProjectCreated` event is emitted. The Environment Provisioner asynchronously creates three `Environment` records: `development`, `staging`, `production`.
10. For each environment, the provisioner: allocates a PostgreSQL schema, generates a scoped API key, and initializes a `UsageMeter` for each quota dimension.
11. Three `EnvironmentProvisioned` events are emitted.
12. The console displays the new project with all three environments, each showing their API key (last-8 preview) and status `active`.

### Alternate Flows

**AF-001: Slug Already Taken**  
- Step 2 detects slug collision. Returns HTTP 409 with `slug_taken` error. Project Owner adjusts the slug and re-submits. Returns to step 2.

**AF-002: Enterprise Tenant Requires Operator Approval**  
- After step 3, status is set to `pending_approval`. A `TenantApprovalRequested` event is emitted to the Platform Operator queue.
- The Platform Operator reviews and approves via the operator console.
- On approval, status transitions to `active` and the main flow resumes from step 4.

**AF-003: Email Verification Not Completed Within 24 Hours**  
- The verification token expires. Account status remains `pending_verification`.
- The Project Owner can request a new verification email. Original token is invalidated.

### Postconditions
- Tenant and Project records exist in `active` status.
- Three environments are provisioned with valid API keys and initialized usage meters.
- The Project Owner can authenticate and make API calls against all three environments.

### Business Rules Referenced
- BR-02 (Tenant Isolation): All resources created are isolated to this tenant.
- BR-03 (Environment Immutability): The three standard environments cannot be renamed.
- BR-04 (Quota Enforcement): Quota is initialized; project count is incremented in the tenant's UsageMeter.

---

## UC-002: Provider Binding and Environment Configuration

**ID:** UC-002  
**Name:** Provider Binding and Environment Configuration  
**Actors:** Project Owner (Primary), External Provider (Secondary — AWS/GCP/MinIO)  
**Related User Stories:** US-002, US-030, US-031, US-032  
**Related Business Rules:** BR-05, BR-09, BR-11  

### Preconditions
- The Project and its environments are in `active` status.
- The desired provider adapter is registered in the Provider Catalog.
- The Project Owner has credentials for the target provider and has stored them in their secret manager.
- A SecretRef has been created pointing to the credential in the secret manager.

### Main Flow

1. The Project Owner opens the production environment's "Providers" panel in the console.
2. The Project Owner selects the capability (`storage`) and chooses `aws-s3@1.2.0` from the catalog.
3. The console renders a configuration form derived from the adapter's JSON Schema (bucket name, region, SecretRef selector for access credentials).
4. The Project Owner fills in the form, selecting the pre-created SecretRef for AWS credentials.
5. The Project Owner submits the form. The Control Plane creates a `CapabilityBinding` with status `pending_validation`.
6. The Control Plane resolves the SecretRef against AWS Secrets Manager and retrieves the credentials.
7. The Control Plane calls the adapter's `validate()` method, which performs a `HeadBucket` operation using the provided credentials.
8. If validation succeeds within 10 seconds, the binding status transitions to `active`. A `BindingActivated` event is emitted.
9. The Project Owner is shown the active binding with a green status indicator and `last_validated_at` timestamp.

### Alternate Flows

**AF-001: Validation Fails (Invalid Credentials)**  
- Step 7 returns an auth rejection from AWS. The binding remains in `pending_validation` (not `active`).
- HTTP 422 is returned with reason `auth_rejected`. A `BindingValidationFailed` event is emitted.
- The Project Owner corrects the credentials in their secret manager and re-triggers validation.

**AF-002: Validation Timeout**  
- The adapter's `validate()` call times out after 10 seconds. The binding is rejected with reason `connectivity_timeout`.

**AF-003: Switch Active Binding**  
- If a binding already exists for the capability, it remains `active` (as a secondary binding).
- The Project Owner explicitly marks the new binding as `is_primary = true`, which atomically demotes the old one.

### Postconditions
- A `CapabilityBinding` exists with status `active` and `is_primary = true` for the `storage` capability in the production environment.
- Subsequent file upload operations route to AWS S3 via the new binding.
- A `BindingActivated` entry exists in the Audit Log.

### Business Rules Referenced
- BR-05 (Provider Binding Validation): Connectivity must be verified at creation time.
- BR-09 (Secret Non-Disclosure): Credential values never returned in API responses or logs.

---

## UC-003: User Registration and Authentication

**ID:** UC-003  
**Name:** User Registration and Authentication  
**Actors:** Application End User (Primary), App Developer's Application (Intermediary)  
**Related User Stories:** US-007, US-008, US-019, US-021  
**Related Business Rules:** BR-01, BR-06, BR-09  

### Preconditions
- The BaaS Project and Environment are in `active` status.
- The App Developer has configured the Auth Service (at minimum, email/password is enabled by default).
- The End User has a valid email address.

### Main Flow

1. The End User submits their email and password to the application's registration endpoint.
2. The application calls POST `/v1/auth/register` with the environment API key in the header.
3. The Auth Service validates: email format, password strength (≥ 8 chars, at least one non-alpha character), email uniqueness.
4. The Auth Service creates an `AuthUser` record with `password_hash` (bcrypt, cost 12), `email_verified = false`, `status = pending_verification`.
5. A `UserRegistered` event is emitted. The Notification Service sends a verification email.
6. The API returns HTTP 201 with the user's profile (no password hash), an access token (JWT, 15-min TTL), and a refresh token.
7. The End User completes a subsequent login by POSTing email + password to `/v1/auth/login`.
8. The Auth Service verifies the bcrypt hash and checks `status = active` (or `pending_verification` if the project permits unverified logins).
9. On success: a new `SessionRecord` is created; a JWT access token and refresh token are issued. The response includes both tokens.
10. When the access token expires, the application calls POST `/v1/auth/refresh` with the refresh token.
11. The Auth Service atomically rotates: old refresh token is marked `used`, new refresh token is issued, new access token is issued.
12. The End User logs out by calling POST `/v1/auth/logout`. The session is revoked and the refresh token is invalidated.

### Alternate Flows

**AF-001: OAuth2 Login**  
- Step 1: App redirects user to `GET /v1/auth/oauth2/google/authorize`.
- The Auth Service redirects to Google's authorization endpoint.
- On callback, Auth Service exchanges code for tokens, creates/matches the `AuthUser`, and returns the BaaS JWT pair.

**AF-002: Magic Link Login**  
- User requests magic link via POST `/v1/auth/magic-link` with email.
- Auth Service creates a single-use token (15-min expiry) and emails a link to the user.
- On click, the link exchanges the token for a JWT pair. Token is immediately invalidated.

**AF-003: Rate Limiting Triggered**  
- After 10 failed login attempts in 15 minutes, subsequent attempts return HTTP 429.
- A `RateLimitExceeded` event is emitted. The Project Owner may configure CAPTCHA or lockout.

**AF-004: Refresh Token Replay Detected**  
- An already-used refresh token is presented. BR-06 triggers: the entire session chain is revoked.
- A `SessionHijackSuspected` event is emitted. The user must re-authenticate.

### Postconditions
- An `AuthUser` record exists with appropriate status.
- The End User holds a valid JWT access token and refresh token.
- A `SessionRecord` exists in `active` status.
- All events recorded in the Audit Log.

### Business Rules Referenced
- BR-01 (Token Scope): Token is scoped to the specific environment.
- BR-06 (Refresh Token Rotation): Replay attack detection and session revocation.

---

## UC-004: Schema Creation and Data Access

**ID:** UC-004  
**Name:** Schema Creation and Data Access  
**Actors:** App Developer (Primary), End User (Indirect — subject to RLS)  
**Related User Stories:** US-009, US-010, US-011, US-017  
**Related Business Rules:** BR-01, BR-02, BR-07  

### Preconditions
- The Environment is `active` with a provisioned PostgreSQL schema.
- The App Developer holds a valid API key for the environment.
- No prior migration version has been applied to this namespace (fresh setup scenario).

### Main Flow

1. App Developer creates a Namespace via POST `/v1/db/namespaces` with name `app`.
2. The Database API creates a PostgreSQL schema (`{env_id}_app`) and inserts a `DataNamespace` record. A `NamespaceCreated` event is emitted.
3. App Developer defines a table via POST `/v1/db/namespaces/app/tables` with a column spec:
   ```json
   { "name": "posts", "columns": [
     {"name": "title", "type": "text", "nullable": false},
     {"name": "body", "type": "text", "nullable": true},
     {"name": "user_id", "type": "uuid", "nullable": false},
     {"name": "published_at", "type": "timestamptz", "nullable": true}
   ]}
   ```
4. The Database API executes the `CREATE TABLE` DDL, adds `id UUID DEFAULT gen_random_uuid()`, `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at TIMESTAMPTZ`. A `TableCreated` event is emitted.
5. App Developer defines an RLS policy: only the post's `user_id` can read their own posts.
6. The Database API applies the RLS policy using `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and `CREATE POLICY`.
7. End User creates a post: POST `/v1/db/namespaces/app/tables/posts/records` with JWT in `Authorization`. Returns the created record with auto-generated `id` and `created_at`.
8. End User queries their posts: GET `/v1/db/namespaces/app/tables/posts/records?filter={"published_at":{"$neq":null}}&limit=20`. The RLS policy filters to only their own published posts.
9. App Developer evolves the schema: creates a migration adding `tags TEXT[]` column, uploads `up.sql` and `down.sql`.
10. The Migration Orchestrator applies the migration in the development environment. `MigrationApplied` event emitted.
11. After testing in staging, App Developer promotes the migration to production (after approver sign-off per BR-07).

### Alternate Flows

**AF-001: RLS Policy Blocks Cross-User Access**  
- User B attempts to GET a record owned by User A. The RLS predicate filters the row. API returns empty result (not HTTP 403) — RLS is transparent.

**AF-002: Migration Promotion Fails Gate Check**  
- Promotion to production without staging application returns HTTP 409 with `staging_not_applied` reason.

**AF-003: Column Type Not Supported**  
- Step 3 with an unsupported column type (e.g., `money`) returns HTTP 422 with `unsupported_column_type`.

### Postconditions
- `DataNamespace`, `TableDefinition` records exist.
- PostgreSQL table with RLS policy is active.
- Records can be created, queried, and filtered via the API.

### Business Rules Referenced
- BR-02 (Tenant Isolation): All queries are scoped to the environment's schema.
- BR-07 (Migration Promotion Gate): Production migration requires staging confirmation and approver sign-off.

---

## UC-005: File Upload and Access Control

**ID:** UC-005  
**Name:** File Upload and Access Control  
**Actors:** App Developer (Primary), End User (Secondary), Storage Provider (External)  
**Related User Stories:** US-012  
**Related Business Rules:** BR-04, BR-08, BR-09  

### Preconditions
- A `CapabilityBinding` for `storage` is active in the environment.
- The App Developer has created at least one `Bucket`.
- The End User is authenticated with a valid JWT.

### Main Flow

1. End User initiates a file upload via the application. The app calls POST `/v1/storage/buckets/{bucketId}/files` with the file as a multipart body.
2. The Storage Facade validates: API key scope, bucket existence, MIME type allowed by bucket policy, file size ≤ bucket's `max_file_size_bytes`.
3. The Storage Facade generates a `file_id` (UUID v4), computes a SHA-256 checksum, and streams the file to the provider adapter (AWS S3 / MinIO etc.) using the bucket's `binding_id`.
4. On successful provider write, the Storage Facade inserts a `FileObject` record in PostgreSQL with status `scan_pending` (if virus scan is enabled) or `active`.
5. A `FileUploaded` event is emitted. If `virus_scan_enabled = true` on the bucket, the Virus Scanner Service receives the event.
6. The API returns HTTP 201 with the `FileObject` metadata (no signed URL yet by default).
7. End User requests access to the file: POST `/v1/storage/files/{fileId}/signed-url?expiry=3600`.
8. The Storage Facade checks the file's access policy (`private`), verifies the requesting user is the file owner (or has sufficient role), and generates an HMAC-SHA256 signed URL.
9. The End User uses the signed URL to download the file. The Storage Facade validates the signature and expiry before proxying the stream from the provider.
10. After 3,600 seconds, the signed URL returns HTTP 403.

### Alternate Flows

**AF-001: File Exceeds Size Limit**  
- Step 2 rejects with HTTP 413 and error `file_too_large`.

**AF-002: Multipart Upload for Large Files**  
- For files > 100 MB, the client initiates a multipart upload: POST `/v1/storage/buckets/{bucketId}/files/multipart/start`.
- The server returns an `upload_id` and pre-signed part URLs.
- The client uploads parts directly to the provider.
- Client calls POST `.../multipart/complete` with the part checksums.
- The Storage Facade calls the provider's `CompleteMultipartUpload` and then records the `FileObject`.

**AF-003: Virus Scan Detects Infection**  
- The Virus Scanner Service returns `infected`. File status → `quarantined`.
- A `FileScanCompleted` event with `scan_result=infected` is emitted.
- The file is inaccessible; a notification is sent to the project owner.

**AF-004: Unauthorized Access Attempt**  
- A user without ownership or admin role requests a signed URL. Returns HTTP 403.
- A `UnauthorizedAccess` security event is logged.

### Postconditions
- `FileObject` record exists in PostgreSQL with status `active` or `scan_pending`.
- Binary content is stored in the provider under `storage_provider_key`.
- Signed URL access is enforced by the Storage Facade on every request.

### Business Rules Referenced
- BR-04 (Quota): Storage bytes counter incremented in `UsageMeter`.
- BR-08 (Signed URL Expiry): Expiry validated on every request, not once at proxy layer.

---

## UC-006: Function Deployment and Invocation

**ID:** UC-006  
**Name:** Function Deployment and Invocation  
**Actors:** App Developer (Primary), Scheduler (Secondary — for cron), Worker (Internal)  
**Related User Stories:** US-013, US-014, US-018  
**Related Business Rules:** BR-01, BR-09, BR-10  

### Preconditions
- A `CapabilityBinding` for `functions` is active in the environment.
- The App Developer has a ZIP artifact or container image reference.
- Any required SecretRefs are created in the environment.

### Main Flow

1. App Developer posts a function deployment: POST `/v1/functions` with runtime (`node20`), entrypoint (`src/index.handler`), a ZIP artifact (multipart), and optional trigger configuration and secret env var mappings.
2. The Functions Service validates the runtime, artifact size (max 250 MB), and parses the trigger config.
3. The artifact is uploaded to the platform's internal storage (separate from the tenant's storage).
4. A `FunctionDefinition` record is created with status `deploying`.
5. A `FunctionDeployed` event is emitted. The provider adapter (Lambda adapter, GCP Functions adapter, etc.) receives the event and provisions the function in the provider.
6. Once the provider confirms readiness, the function status transitions to `active`. The App Developer is notified.
7. End User triggers the function via HTTP: POST `/v1/functions/{functionId}/invoke`.
8. The Functions Service checks the concurrency semaphore in Redis. If under limit, it increments the counter and routes to the worker.
9. The worker resolves all SecretRefs to their actual values, constructs the execution environment, and invokes the function in the provider.
10. The function executes. stdout/stderr are streamed to the log aggregator.
11. On completion, the worker emits `ExecutionCompleted` with duration and exit code. The semaphore is decremented. The response is returned to the caller.
12. Execution logs are stored in object storage and linked in the `ExecutionRecord`.

### Alternate Flows

**AF-001: Cron-Triggered Invocation**  
- The Scheduler Service fires at the scheduled slot, emitting `CronScheduleTriggered`.
- The Functions Service creates an `ExecutionRecord` with the cron's `idempotency_key`.
- If a duplicate trigger arrives within the same slot, it is deduplicated by the unique constraint on `(function_id, idempotency_key)`.

**AF-002: Execution Timeout**  
- At T=timeout, the worker sends SIGTERM; if the process doesn't exit in 5s, SIGKILL.
- `ExecutionFailed` event with error_code `execution_timeout`. HTTP 504 returned to caller.

**AF-003: Secret Resolution Failure**  
- The worker cannot resolve a SecretRef (expired credentials, missing permission).
- Execution fails before invocation with `secret_resolution_failed` error. No execution time is billed.

**AF-004: Concurrency Limit Exceeded**  
- Redis semaphore shows limit reached. The invocation is queued (if `queue_mode = true`) or rejected with HTTP 429.

### Postconditions
- `FunctionDefinition` in `active` status.
- `ExecutionRecord` in `completed` or `failed` status.
- Logs available via `/v1/functions/executions/{id}/logs`.
- Usage meter incremented for function invocation count and compute minutes.

### Business Rules Referenced
- BR-10 (Timeout/Concurrency): Hard timeout enforced at OS level; distributed semaphore for concurrency.
- BR-09 (Secret Non-Disclosure): Resolved secrets never stored in ExecutionRecord.

---

## UC-007: Realtime Channel Subscription and Message Publishing

**ID:** UC-007  
**Name:** Realtime Channel Subscription and Message Publishing  
**Actors:** App Developer (Channel Setup), End User (Subscriber/Publisher)  
**Related User Stories:** US-015, US-016  
**Related Business Rules:** BR-01, BR-12, BR-15  

### Preconditions
- The Environment is `active`.
- An `EventChannel` exists with `visibility = private`.
- The End User is authenticated.

### Main Flow

1. App Developer creates a channel: POST `/v1/realtime/channels` with `name = "notifications"`, `visibility = "presence"`, `publish_policy = "authenticated_users"`.
2. End User's client establishes a WebSocket connection: `wss://api.baas.example.com/v1/realtime?token={jwt}`.
3. The Realtime Service validates the JWT: signature, expiry, environment scope.
4. On successful handshake, the WebSocket connection is assigned a `session_id` and registered in Redis.
5. End User sends a subscribe frame: `{"action": "subscribe", "channel": "notifications"}`.
6. The Realtime Service evaluates the channel's auth policy for the user's roles. On success, adds the subscriber to the channel's fan-out list in Redis. Sends `{"status": "subscribed", "channel": "notifications"}`.
7. For presence channels, a `PresenceMemberJoined` event is broadcast to all existing subscribers.
8. Another user (or server-side process) publishes a message: POST `/v1/realtime/channels/notifications/publish` with a payload.
9. The Realtime Service validates the publisher's auth (API key or JWT with correct scope).
10. The message is pushed to the Redis pub/sub topic for the channel. All Realtime Service replicas pick up the message and push it to their locally-connected subscribers via WebSocket.
11. A `MessagePublished` event is emitted (metadata only, not full payload).
12. For webhook subscriptions matching the event filter, the Webhook Delivery Service enqueues a delivery job.
13. End User disconnects. A `PresenceMemberLeft` event is broadcast. Subscription record status → `closed`.

### Alternate Flows

**AF-001: Auth Policy Denies Subscribe**  
- Step 6 fails policy evaluation. The subscriber receives `{"status": "error", "code": "authorization_denied"}`. Connection remains open; user can subscribe to other channels.

**AF-002: WebSocket Reconnect with Replay**  
- After a disconnect, the client reconnects within 60 seconds with the same JWT and a `since_message_id`.
- The Realtime Service replays any messages retained within the channel's `retention_seconds` window.

**AF-003: Webhook Delivery Failure**  
- The webhook endpoint returns HTTP 500. The Webhook Delivery Service schedules retries per BR-15.
- After 5 failures, `WebhookDeliveryFailed` event is emitted and the subscription is suspended.

### Postconditions
- Subscription record exists (or is closed if user disconnected).
- Messages delivered to all active subscribers within SLA.
- Webhook delivery tracked with attempt count.

### Business Rules Referenced
- BR-12 (Channel Auth): Re-evaluated on each subscribe message for `strict_auth` channels.
- BR-15 (Webhook Retry): Exponential backoff, max 5 attempts.

---

## UC-008: Provider Switchover Orchestration

**ID:** UC-008  
**Name:** Provider Switchover Orchestration  
**Actors:** Project Owner (Primary), Migration Orchestrator (System), Source Provider (External), Target Provider (External)  
**Related User Stories:** US-006  
**Related Business Rules:** BR-05, BR-11  

### Preconditions
- Both source and target `CapabilityBindings` exist with status `active`.
- No ongoing switchover plan for the same capability/environment combination.
- The Project Owner has `environment:switchover` permission.

### Main Flow

1. Project Owner creates a SwitchoverPlan: POST `/v1/switchover-plans` with `source_binding_id`, `target_binding_id`, `capability = "storage"`.
2. The Control Plane validates both bindings are active and creates the plan with status `draft`.
3. Project Owner advances the plan to `ready` via PATCH `.../status` with `{"status": "ready"}`.
4. The Migration Orchestrator runs pre-flight checks (safety gates BR-11):
   a. **Quiesce Check**: Queries in-flight write operations on the source provider. Waits up to 5 minutes for quiescing.
   b. **Target Connectivity**: Re-runs `validate()` on the target binding.
   c. Updates `safety_gates` JSONB field with check results.
5. If all gates pass, the plan advances to `in_progress`. `SwitchoverStarted` event emitted.
6. The Orchestrator begins copying all objects from source to target provider, updating `progress_pct` every 30 seconds.
7. New write operations during copy are routed to BOTH providers (write-through mode).
8. After copy completes, the Orchestrator performs a reconciliation checksum comparison.
9. If checksums match: the target binding is set as `is_primary`. Source becomes secondary (read-only fallback). Plan status → `completed`. `SwitchoverCompleted` event emitted.
10. After a 24-hour grace period, the source binding can be deactivated by the Project Owner.

### Alternate Flows

**AF-001: Checksum Mismatch**  
- Step 8 detects mismatch. Orchestrator triggers rollback: target binding demoted to inactive, source binding confirmed as primary.
- `SwitchoverRolledBack` event emitted with `rollback_reason = "checksum_mismatch"`.

**AF-002: Quiesce Timeout**  
- Source provider still has in-flight operations after 5 minutes. Orchestrator aborts the switchover.
- Plan returns to `ready` status; Project Owner is notified to retry.

**AF-003: Manual Rollback**  
- At any point during `in_progress`, Project Owner calls PATCH `.../status` with `{"status": "rolled_back", "reason": "..."}`.
- Orchestrator restores original routing, emits `SwitchoverRolledBack`.

**AF-004: Target Provider Becomes Unavailable Mid-Copy**  
- Target provider connectivity is lost during copy. Orchestrator pauses and emits `SwitchoverPaused`.
- After connectivity is restored (max 1 hour), the copy resumes from the last checkpoint.
- If connectivity is not restored within 1 hour, automatic rollback is triggered.

### Postconditions
- If completed: target binding is `is_primary = true`; all new operations route to target provider.
- If rolled back: source binding is `is_primary = true`; no data loss.
- SwitchoverPlan in terminal state (`completed` or `rolled_back`).
- All state transitions recorded in the Audit Log.

### Business Rules Referenced
- BR-05 (Provider Validation): Target provider validated before and during switchover.
- BR-11 (Safety Gates): Quiesce, connectivity, and checksum checks are mandatory before `in_progress`.
