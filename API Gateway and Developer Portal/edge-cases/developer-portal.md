# Edge Cases: Developer Portal

## Overview

This document covers critical edge cases specific to the Developer Portal, built with Next.js 14 and
TypeScript and backed by PostgreSQL 15, Redis 7, and the API Gateway. The portal serves as the
primary self-service interface for API consumers: creating applications, generating and managing API
keys, exploring documentation, testing APIs in the sandbox, and managing OAuth 2.0 client
credentials.

Portal edge cases differ from gateway edge cases in that they primarily affect the developer
experience rather than live traffic enforcement. Failures here cause confusion, data inconsistencies,
security vulnerabilities, or loss of access for the consumer. The scenarios below cover asynchronous
propagation lag, concurrent write conflicts, destructive operations on live resources, OAuth PKCE
session state loss, stale sandbox responses, and account lifecycle management failures.

---

## Edge Cases

---

### EC-PORTAL-001: Developer Generates API Key but Portal UI Shows Loading State Indefinitely (Async Key Propagation Lag)

**Background:** Asynchronous key propagation introduces an observable lag between when a developer
believes a key is active and when it is actually enforceable. This gap is architecturally
necessary — a synchronous Redis write on every key generation would tightly couple the portal API
to the Redis availability — but it must be made transparent to the developer through clear UI
feedback and bounded wait times. The 15-second SLO for key activation covers 99.5% of cases under
normal operating conditions.

| Field | Detail |
|-------|--------|
| **Failure Mode** | When a developer generates a new API key via the portal, the backend writes the key to PostgreSQL and enqueues a BullMQ job to propagate the key material to the Redis key-validation cache used by the gateway. The Next.js portal UI optimistically transitions to a "loading" state polling for confirmation that the key is active. If the BullMQ propagation job is delayed — due to a queue backlog, a worker crash, or a Redis connectivity blip — the portal's polling endpoint (`GET /api/keys/{keyId}/status`) continues returning `status: "pending"` indefinitely, leaving the developer staring at a spinner with no feedback on how long to wait or whether the operation failed. |
| **Impact** | Developers cannot use their newly generated API key until the loading state resolves. For developers onboarding in real time (e.g., during a sales demo or a hackathon), this creates immediate frustration and erodes trust in the platform. If the developer refreshes the page during the loading state, the portal may not recover the pending key context from server-side state and the developer may believe the key generation failed, leading them to generate duplicate keys or raise urgent support tickets. |
| **Detection** | The polling endpoint records a `key_propagation_pending_duration_seconds` histogram metric in Prometheus. An alert fires when any key remains in `pending` state for more than 15 seconds. Grafana dashboard "Key Propagation Health" shows the 95th-percentile propagation latency with a target of sub-3-seconds. BullMQ queue depth for the `key-propagation` queue is monitored separately; depth exceeding 100 triggers a warning alert. |
| **Mitigation / Recovery** | Add a hard 30-second timeout to the portal polling loop. After timeout, display a user-facing message: "Key activation is taking longer than expected. The key will be active within a few minutes — you can safely close this dialog and check back shortly." Provide a manual "Check Status" button. On the backend, implement a fallback synchronous Redis write path: if the BullMQ job has not been consumed within 10 seconds, the API route handler directly writes the key to Redis as an emergency fallback, bypassing the queue. Alert the SRE on-call to investigate the queue backlog. |
| **Prevention** | For API key propagation, use a synchronous Redis write in the primary request path (not a queue) since key activation is a latency-sensitive user-facing operation. Reserve BullMQ for non-latency-critical background tasks like analytics, audit log enrichment, and email notifications. Add a service-level objective (SLO) of 99.5% of key activations completing within 5 seconds, tracked as a Prometheus metric and reviewed in the weekly SRE review. Conduct end-to-end propagation latency tests in CI for every deployment. |

**Operational Notes:**
- The 15-second key activation SLO must be tracked as a Prometheus SLO metric per deployment.
- The synchronous fallback path (direct Redis write) should log a `KEY_SYNC_FALLBACK` event.
- Monitor the fallback activation rate; frequent fallbacks indicate a systemic queue issue.
- Consider surfacing the propagation status in the portal as a progress bar with elapsed time.
- Test the fallback path explicitly in the integration test suite.

---

### EC-PORTAL-002: Two Browser Tabs Simultaneously Submit Application Creation Causing Duplicate Application Records

**Background:** Concurrent form submissions from multiple browser tabs are a common user behaviour
pattern that many web applications fail to handle. The underlying cause is that browser tabs share
no state by default, and a developer opening a new tab to check documentation while completing a
form creates a natural race condition scenario. The fix (database unique constraint + idempotency
key) must be implemented at both the database layer and the API layer to provide defence in depth.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A developer has the "Create Application" form open in two browser tabs simultaneously — a common occurrence when a developer opens a new tab to check documentation while filling out the form in the original tab. Both tabs have the same form state and the developer clicks "Create" in both tabs within a 500ms window. The Next.js API route handler for `POST /api/applications` does not implement an idempotency key, so both HTTP requests reach PostgreSQL and both succeed, creating two application records with identical names, descriptions, and plan selections but different UUIDs. The developer ends up with duplicate applications they did not intend to create. |
| **Impact** | Duplicate application records pollute the developer's application list and cause confusion about which application is "real." Each duplicate application can independently generate API keys, creating orphaned credentials that must be cleaned up manually. If the developer contacts support to delete the duplicates, support agents must verify which application has live traffic attached before deleting, adding operational overhead. In the worst case, the developer deletes the wrong application — the one with active production keys — causing a live traffic outage (see EC-PORTAL-003). |
| **Detection** | The `POST /api/applications` endpoint logs all application creation events with the `developer_id`, `application_name`, and `created_at` timestamp. A PostgreSQL trigger or application-layer check emits a `duplicate_application_created` event when two applications with the same `developer_id` and `application_name` are created within a 10-second window. Grafana tracks this event rate; any non-zero value triggers a warning alert since duplicate creation should be statistically near-zero. |
| **Mitigation / Recovery** | Add a PostgreSQL unique constraint on `(developer_id, application_name)` to prevent true duplicates at the database level — the second INSERT will fail with a unique constraint violation, which the API layer converts to an HTTP 409 Conflict response with a body pointing to the existing application's URL. The portal UI handles the 409 by displaying "An application with this name already exists" and redirecting to the existing record. Existing duplicate records in production are cleaned up via a migration script that identifies pairs by `(developer_id, application_name, created_at WITHIN 10s)` and archives the record with no associated API keys. |
| **Prevention** | Implement idempotency keys for all mutating portal API routes. The frontend generates a UUID `Idempotency-Key` header when the form is first rendered and includes it with every submission. The backend caches the response for this key in Redis for 10 minutes; duplicate requests with the same key return the cached response instead of executing the operation again. The unique constraint on `(developer_id, application_name)` provides a defence-in-depth layer below the idempotency mechanism. Add a Cypress end-to-end test that simulates simultaneous dual-tab submission and asserts only one application is created. |

**Operational Notes:**
- The unique constraint on `(developer_id, application_name)` is a required schema migration.
- The Cypress dual-tab test must be added to the portal E2E test suite before this fix ships.
- The 409 Conflict response body must include the URL of the existing application for UX.
- Review other portal form submissions for the same race condition pattern (e.g., webhook creation).
- Document the idempotency key header contract in the Developer Portal API reference.

---

### EC-PORTAL-003: Developer Deletes Application with Active Production API Key Used by Live Traffic

**Background:** This is one of the most high-severity self-service actions a developer can take —
it is the API equivalent of accidentally deleting a production database. The 24-hour soft-delete
grace period is the primary safeguard, but it must be complemented by friction in the deletion UI
proportional to the traffic associated with the application. The traffic indicator requirement is
non-negotiable for any application receiving more than zero requests in the past 24 hours.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A developer navigates to their application list in the portal and deletes an application, believing it to be unused. The portal's delete confirmation dialog shows the application name and creation date but does not surface whether any associated API keys have received requests in the past 24 hours. The deletion proceeds, the application record is soft-deleted in PostgreSQL, and a BullMQ job is enqueued to revoke all associated API keys in the Redis key-validation cache. Within seconds, the gateway begins returning HTTP 401 Unauthorized for requests authenticated with those keys. Production traffic — possibly from a partner integration or a mobile application the developer forgot about — immediately starts failing. |
| **Impact** | Complete authentication failure for all API consumers using keys from the deleted application. Depending on the application's traffic volume, this constitutes a self-inflicted production outage. Recovery requires the developer to create a new application, generate new API keys, and redistribute them to all consumers — a process that can take hours to days for partner integrations with long deployment cycles. Every minute of outage represents lost transactions, degraded user experience in the partner's product, and potential SLA breach penalties. |
| **Detection** | The gateway records `auth_failure_api_key_revoked_total` as a Prometheus counter per API key. A spike in 401 responses for a previously healthy API key immediately after a key revocation event triggers a Grafana alert "Unexpected Auth Failure Spike Post-Deletion." The Developer Portal's delete action emits an audit log event `APPLICATION_DELETED` that is cross-referenced with real-time key traffic data for post-incident review. |
| **Mitigation / Recovery** | Implement a 24-hour soft-delete period before API keys are actually revoked in Redis. During the soft-delete period, the portal shows a prominent banner warning: "This application is scheduled for deletion on [date]. API keys will be revoked at that time." Allow the developer to cancel the deletion at any time during the 24-hour window. If a deletion must be immediate (security incident, account termination), provide an admin-only override pathway with a mandatory justification field. For keys already revoked accidentally, allow a one-time emergency re-activation within 1 hour of deletion via a support-gated API endpoint. |
| **Prevention** | Display a live traffic indicator on the application deletion confirmation dialog, pulled from the last 24 hours of analytics: "This application's API keys received N requests in the last 24 hours." If N > 0, require the developer to type the application name to confirm deletion, add a mandatory 24-hour delay, and send an email notification to all account owners. If N > 1,000, block self-service deletion entirely and route through a support ticket requiring human review. Add this check as a required field in the application deletion API endpoint's request validation schema. |

**Operational Notes:**
- The 24-hour soft-delete window must be stored in the `deleted_at` column with a scheduled job.
- The traffic indicator query must use a Redis-cached counter to avoid slow PostgreSQL analytics.
- Send a deletion confirmation email immediately and a reminder email 6 hours before hard deletion.
- The admin override pathway for immediate deletion must be audited and require 2FA confirmation.
- After the 24-hour window, hard deletion must cascade to all associated API keys and webhooks.

---

### EC-PORTAL-004: OAuth PKCE code_verifier Not Stored in Session (Back/Forward Navigation Clears State)

**Background:** Browser bfcache (Back-Forward Cache) is a browser optimisation that preserves a
snapshot of a page in memory for instant back-forward navigation. Pages restored from bfcache do
not re-execute JavaScript, meaning any `sessionStorage` writes that occurred after page load are
not visible in the restored context. This is a well-documented incompatibility with OAuth PKCE
flows that store the `code_verifier` in `sessionStorage` after the authorization redirect begins.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The Developer Portal implements OAuth 2.0 with PKCE (Proof Key for Code Exchange) for user authentication. The `code_verifier` and `state` parameters generated at the start of the OAuth flow are stored in `sessionStorage` in the browser. If the developer navigates backward in browser history after initiating the login flow — returning to the portal landing page — and then navigates forward again to the OAuth callback URL, the `sessionStorage` entry created in the original tab context may have been cleared by the browser's back-forward cache (bfcache) page restoration, or the `code_verifier` may simply not be present in the restored page's JavaScript context. The PKCE validation at the callback endpoint fails because the `code_verifier` cannot be retrieved, resulting in an `invalid_grant` error and a broken login loop. |
| **Impact** | Developers attempting to log in via standard browser navigation patterns (using the back button after accidentally navigating away mid-flow) receive an opaque "Authentication failed" error with no actionable recovery path. The broken state persists until the developer clears their browser session storage or opens a new tab, which is a non-obvious remediation step. First-time users encountering this during onboarding are likely to abandon the platform entirely, interpreting the error as a fundamental product quality issue. |
| **Detection** | The OAuth callback endpoint (`/api/auth/callback`) logs `oauth_pkce_verification_failed` events with the error code and the request's session identifier. A Prometheus counter `oauth_callback_pkce_failure_total` differentiated by `reason: verifier_missing` vs. `reason: verifier_mismatch` tracks this specifically. An alert fires when the `verifier_missing` failure rate exceeds 1% of total OAuth callback attempts over a 5-minute window, indicating a systemic storage issue rather than isolated user error. |
| **Mitigation / Recovery** | Redirect developers who encounter PKCE failures to a dedicated `/auth/retry` page that clears all stale OAuth state (sessionStorage, cookies) and initiates a fresh login flow with a new `code_verifier`. The error page must display a clear human-readable message ("Your login session expired — click here to try again") rather than an error code. Log the failure event server-side with enough context (user agent, referring URL) to diagnose the bfcache interaction pattern. |
| **Prevention** | Store the `code_verifier` and `state` in an `httpOnly` session cookie with `SameSite=Lax` and a short TTL of 10 minutes instead of `sessionStorage`. Cookie-based storage is immune to bfcache page restoration issues because cookies persist across bfcache navigations. Add a `Cache-Control: no-store` header to the OAuth initiation page to prevent it from being bfcache-eligible entirely. Add an end-to-end Playwright test that simulates a back-forward navigation sequence during the OAuth flow and asserts successful authentication. |

**Operational Notes:**
- The `SameSite=Lax` cookie attribute is sufficient for PKCE; `Strict` would break redirect flows.
- Add `Cache-Control: no-store` to the OAuth initiation page to prevent bfcache eligibility.
- The Playwright test should simulate the back-forward navigation using `page.goBack()/goForward()`.
- Review all other OAuth state parameters (e.g., `state`, `nonce`) for the same bfcache issue.
- Update the portal security audit checklist to include bfcache compatibility review.

---

### EC-PORTAL-005: Sandbox Environment Returns Stale Mock Responses After API Schema Update

**Background:** Sandbox environments create a permanent tension between stability (developers expect
consistent mock responses) and accuracy (mocks should reflect the current production schema). The
resolution is to make schema propagation fast and automatic rather than manual. A 5-minute cache
TTL is a reasonable balance: it absorbs the load from polling-based clients while ensuring schema
updates are reflected within one business task's switching time.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The Developer Portal provides an integrated sandbox environment that returns mock API responses based on a cached copy of the OpenAPI schema. When the upstream API team publishes a breaking schema change — for example, renaming a response field from `user_id` to `userId`, adding a required request parameter, or changing an enum value — the sandbox's mock response generator continues serving responses based on the old schema. This is because the sandbox schema cache in Redis is set to a 24-hour TTL and has not yet expired. Developers testing against the sandbox build integrations against the outdated response structure, then discover breakage only when they switch to the production gateway. |
| **Impact** | Developers waste integration effort building code against incorrect response structures. The discovery of the mismatch typically happens late in the development cycle — during production testing or after a partner goes live — at which point remediation requires significant rework. Trust in the Developer Portal as an accurate representation of the API is fundamentally undermined. For partners with long release cycles, the incorrect sandbox behaviour may propagate into shipped client code, requiring emergency patches in production. |
| **Detection** | The API schema publication pipeline emits a `schema_published` event to an SNS topic with the schema version hash. The sandbox service subscribes to this topic; a CloudWatch alarm fires if the sandbox Redis cache version hash does not match the latest published hash within 60 seconds of a publication event. Grafana dashboard "Sandbox Schema Freshness" displays the age of the currently served schema alongside the age of the latest published schema. Alert fires if the divergence exceeds 5 minutes. |
| **Mitigation / Recovery** | Upon receiving a `schema_published` event, immediately invalidate the sandbox schema cache in Redis by deleting the `sandbox:schema:{version}` key and re-fetching the schema from the schema registry. Publish a portal notification banner: "API schema updated — sandbox responses reflect the latest version." For breaking changes specifically, display a changelog diff in the sandbox UI highlighting changed fields. Re-run any queued sandbox requests that were submitted in the 24 hours prior to the schema update to give developers visibility into which of their test cases are affected. |
| **Prevention** | Set the sandbox schema cache TTL to 5 minutes instead of 24 hours to bound the maximum staleness window. Implement schema-version-aware caching: the cache key includes the schema version hash, so a new schema publication automatically creates a new cache entry and old entries expire naturally. Integrate the sandbox schema invalidation step directly into the CI/CD pipeline for API schema publications as a required post-deployment step. Add a contract test in the sandbox service that fetches the live schema and asserts the sandbox mock responses match within a 2-minute window. |

**Operational Notes:**
- The SNS-to-sandbox invalidation subscriber must have a dead-letter queue for failed deliveries.
- Schema version hashes should be included in the sandbox response headers for client debugging.
- The 5-minute cache TTL applies only to the full schema; individual endpoint mock configs are live.
- Add a "Schema last updated" timestamp to the sandbox UI to communicate freshness to developers.
- Contract test should run as a post-deployment check in the CI/CD pipeline after schema publishes.

---

### EC-PORTAL-006: Developer Account Email Verification Link Expires Before User Clicks It (24-Hour TTL)

**Background:** The 24-hour email verification TTL is a legacy constraint from systems that assumed
email delivery was near-instantaneous and developers checked email frequently. Enterprise and
regulated environments often impose email access policies (e.g., no personal device access to
corporate email) that make 24-hour TTLs incompatible. A 72-hour TTL with a 48-hour reminder email
is the minimum viable configuration for enterprise-grade developer onboarding.

| Field | Detail |
|-------|--------|
| **Failure Mode** | When a developer registers a new account, the portal sends an email verification link containing a signed JWT token with a 24-hour expiry. If the developer does not click the link within 24 hours — due to a busy schedule, a spam filter delay, or the email arriving in a corporate inbox with a 48-hour access policy — the JWT expires and the verification endpoint returns HTTP 410 Gone. The portal's verification failure page offers no self-service way to request a new verification email, requiring the developer to create a new account or submit a support ticket. Additionally, if the developer tries to log in with an unverified account, they receive a cryptic "Account not verified" error with no guidance on next steps. |
| **Impact** | Developers who do not verify within 24 hours are permanently locked out of their account until they receive support. For enterprise onboarding flows where new developer accounts are provisioned by an IT administrator and the developer first logs in days later, the 24-hour TTL is fundamentally incompatible with the workflow. Account creation abandonment rates increase for any developer group with delayed email access. Support volume for "I can't log in" tickets rises in proportion to the percentage of developers who do not complete verification promptly. |
| **Detection** | The verification endpoint logs `email_verification_expired_token` events per account. A Prometheus counter `account_email_verification_failure_total{reason="expired"}` tracks this metric. An alert fires when the expiry failure rate exceeds 5% of all verification attempts in a rolling 1-hour window. The email delivery service (Amazon SES) bounce and delivery tracking is monitored separately to identify cases where the email was never delivered, which would explain a disproportionately high expiry rate. |
| **Mitigation / Recovery** | When a developer hits an expired verification link, the portal must immediately display a prominent "Resend Verification Email" button that triggers a new verification email with a fresh 72-hour TTL. Rate-limit resend requests to 3 per hour per account to prevent abuse. The new email includes a short explanation: "Your previous verification link expired. This new link is valid for 72 hours." For accounts that have been unverified for more than 7 days, send an automatic reminder email with a new link and flag the account in the admin dashboard for potential cleanup. |
| **Prevention** | Increase the verification link TTL from 24 hours to 72 hours to accommodate enterprise and delayed-access workflows. Send a reminder email at the 48-hour mark (before expiry at 72 hours) if the account remains unverified. Implement a self-service resend flow accessible from the login page: if a developer attempts to log in with an unverified account, the portal automatically offers to resend the verification email rather than displaying an error. Use a database-backed token store (PostgreSQL `verification_tokens` table) instead of a JWT-based approach, allowing tokens to be revoked and reissued without requiring a new account. |

**Operational Notes:**
- The `verification_tokens` table approach allows admin token inspection and early revocation.
- Rate-limit the resend endpoint at 3 requests/hour/account to prevent email flooding.
- Send verification emails via a high-priority SES configuration set to minimise delivery delay.
- Track the verification completion rate as a developer onboarding funnel metric in analytics.
- Review the unverified account cleanup policy (7-day flag) with the legal team for GDPR compliance.

---

## Summary Table

| ID | Title | Severity | Primary Component | Developer Impact | Recovery Time |
|----|-------|----------|-------------------|------------------|---------------|
| EC-PORTAL-001 | API Key Propagation Indefinite Loading | High | BullMQ + Redis propagation | Cannot use new key | 3–30 min |
| EC-PORTAL-002 | Duplicate Application Creation | Medium | PostgreSQL + API idempotency | Duplicate records, confusion | 5–30 min |
| EC-PORTAL-003 | Delete Application with Live Keys | Critical | Key revocation pipeline | Production outage | Hours–days |
| EC-PORTAL-004 | OAuth PKCE Verifier Lost in bfcache | High | OAuth 2.0 PKCE flow | Broken login loop | 1–5 min |
| EC-PORTAL-005 | Stale Sandbox Mock Responses | Medium | Sandbox schema cache (Redis) | Wasted integration effort | Up to 24 hr |
| EC-PORTAL-006 | Email Verification Link Expiry | Medium | Email + JWT verification | Account access blocked | 1 hr–days |

---

## Testing and Validation

The following scenarios must be executed in staging before any portal release that touches
authentication, application management, or developer account lifecycle flows.

| Test Scenario | Target Edge Case | Expected Outcome | Frequency |
|---------------|-----------------|------------------|-----------|
| Trigger key generation with BullMQ workers paused | EC-PORTAL-001 | Synchronous fallback activates; key active within 5s | Per queue-change |
| Submit application creation form from 2 tabs simultaneously | EC-PORTAL-002 | Second request returns 409; one application created | Per deployment |
| Attempt to delete application with >0 requests in last 24h | EC-PORTAL-003 | Traffic indicator shown; 24h delay enforced | Per deletion-flow change |
| Navigate back during OAuth flow, then forward to callback | EC-PORTAL-004 | Authentication completes successfully on retry | Per auth-flow change |
| Publish schema update; check sandbox within 5 minutes | EC-PORTAL-005 | Sandbox reflects new schema within 5 minutes | Per schema publish |
| Attempt verification after 48h with 72h TTL | EC-PORTAL-006 | Verification succeeds; reminder email received at 48h | Per email-flow change |

---

## Revision History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2025-01-01 | Platform Engineering | Initial developer portal edge cases |
| 1.1 | 2025-01-20 | Platform Engineering | Added EC-PORTAL-004 bfcache scenario |

---

## Related Edge Cases

The developer portal edge cases are tightly coupled to other subsystem failures. The table below
maps each portal edge case to the related cases in other edge-case documents.

| Portal Edge Case | Related Cross-Document Edge Case | Relationship |
|-----------------|----------------------------------|--------------|
| EC-PORTAL-001 (Key propagation lag) | EC-RATELIMIT-006 (BullMQ queue backlog) | Shared BullMQ infrastructure |
| EC-PORTAL-003 (Delete live application) | EC-RATELIMIT-007 (Plan downgrade in-flight) | Key revocation pathway |
| EC-PORTAL-004 (PKCE bfcache) | EC-SEC-004 (JWT algorithm confusion) | OAuth 2.0 flow integrity |
| EC-PORTAL-005 (Stale sandbox schema) | EC-OPS-008 (CloudFront stale config) | Shared CloudFront cache layer |
| EC-PORTAL-006 (Verification link expiry) | EC-SEC-003 (PII in logs) | Email content logging risk |
