# User Stories — API Gateway and Developer Portal

## Document Information

| Field       | Value                              |
|-------------|------------------------------------|
| Project     | API Gateway and Developer Portal   |
| Version     | 1.0.0                              |
| Roles       | API Provider · Developer · Admin · Analyst |

Story format: **As a [role], I want [goal] so that [benefit].**

---

## Role: API Provider

### API Publishing

**US-PROV-001** — Publish an API  
*As an API Provider, I want to upload an OpenAPI 3.x specification so that it is published to the developer portal catalogue.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given a valid OpenAPI 3.x YAML/JSON file, when I submit it via the portal, then it appears in the catalogue within 60 seconds.
- Given an invalid OpenAPI file, when I submit it, then I receive a validation error listing all schema violations.
- Given a published API, when I view it in the catalogue, then the description, endpoints, and version are rendered correctly from the spec.

---

**US-PROV-002** — Manage API versions  
*As an API Provider, I want to publish a new version of my API alongside the existing version so that consumers can migrate at their own pace.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given API v1 is active, when I publish v2, then both versions are live simultaneously.
- Given both versions are live, when a consumer calls `/v1/resource`, then they hit v1 upstream; when they call `/v2/resource`, they hit v2 upstream.
- Given v2 is published, when I choose to deprecate v1, then all v1 responses include the `Deprecation` and `Sunset` headers.

---

**US-PROV-003** — Deprecate and sunset an API version  
*As an API Provider, I want to mark an API version as deprecated with a sunset date so that consumers are given advance notice to migrate.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I set a sunset date, when I save the change, then the portal shows the sunset date on the API version card.
- Given the sunset date is 30 days away, then all active subscribers on that version receive an email notification.
- Given the sunset date has passed, when a consumer calls that version, then the gateway returns HTTP 410 Gone with a migration guide URL in the response body.

---

**US-PROV-004** — Configure route-level plugins  
*As an API Provider, I want to attach transformation and security plugins to specific routes so that I can customise gateway behaviour per endpoint.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I attach a header-strip plugin to a route, when a request arrives, then the specified headers are removed before forwarding to upstream.
- Given I attach a response-cache plugin with TTL=60s, when the same request arrives twice within 60 s, then the second response is served from cache without hitting upstream.
- Given I detach a plugin from a route, when the next request arrives, then the plugin is no longer applied.

---

**US-PROV-005** — View per-API analytics  
*As an API Provider, I want to view request volume, error rate, and latency charts for my APIs so that I can identify performance issues.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given the last 24 h, when I open the analytics page, then I see request count, error rate, p50/p95/p99 latency.
- Given a time range selector (1h/24h/7d/30d), when I change it, then all charts update within 3 s.
- Given an error spike, when I drill down on the chart, then I see a breakdown by status code and route.

---

**US-PROV-006** — Set upstream health check rules  
*As an API Provider, I want to configure health-check parameters for my upstream service so that unhealthy instances are automatically removed.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I set interval=10s, threshold=3, timeout=2s, when the upstream returns 3 consecutive failures, then it is removed from rotation.
- Given the upstream recovers, when it returns 2 consecutive successes, then it is added back to rotation.

---

**US-PROV-007** — Upload backend SSL certificate  
*As an API Provider, I want to configure mutual TLS to my upstream service so that the gateway authenticates itself to my backend.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I upload a PEM certificate and key, when the gateway connects to my upstream, then it presents the certificate.
- Given an expired certificate, when I try to save the route config, then I receive a validation error with the expiry date.

---

**US-PROV-008** — Create a custom subscription plan  
*As an API Provider, I want to create a private subscription plan with custom rate limits so that I can offer different tiers to enterprise clients.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I create a plan with name="Enterprise", requests_per_minute=1000, daily_quota=5_000_000, when I save it, then it appears in my plan list.
- Given the plan is private, when a developer browses the plan catalogue, then they do not see it unless I invite them.

---

### Webhook Events

**US-PROV-009** — Subscribe to API lifecycle events  
*As an API Provider, I want to receive webhook notifications when a consumer subscribes or unsubscribes from my API so that I can manage downstream provisioning.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I register a webhook URL for `subscription.created`, when a developer subscribes, then my endpoint receives a POST within 10 s.
- Given my endpoint returns a non-2xx response, then the system retries with exponential back-off up to 5 times.

---

**US-PROV-010** — Rotate webhook signing secret  
*As an API Provider, I want to rotate the webhook signing secret without missing deliveries so that I can remediate a potential secret leak.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I initiate a rotation, when the new secret is issued, then both the old and new secrets are accepted for 30 minutes.
- Given 30 minutes have elapsed, when the old secret is used to verify a delivery, then verification fails.

---

## Role: Developer

### Onboarding

**US-DEV-001** — Register for a developer account  
*As a Developer, I want to sign up using my email or GitHub SSO so that I can access the developer portal.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I provide a valid email and password, when I submit the form, then I receive a verification email within 2 minutes.
- Given I click the verification link, when it is valid (< 24 h old), then my account is activated and I am redirected to the portal home.
- Given I use GitHub SSO, when I authorise the OAuth app, then I am logged in without a separate email verification step.

---

**US-DEV-002** — Browse the API catalogue  
*As a Developer, I want to search and filter the API catalogue so that I can discover APIs relevant to my use case.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I type a keyword, when I search, then APIs matching name or description are shown within 500 ms.
- Given I filter by tag (e.g., "payments"), when I apply the filter, then only tagged APIs are shown.
- Given an API is deprecated, when it appears in results, then it shows a "Deprecated" badge.

---

**US-DEV-003** — View interactive API documentation  
*As a Developer, I want to view interactive docs for an API so that I can understand the endpoints and try them out.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I open an API's documentation page, when the page loads, then I see Redoc-rendered docs from the OpenAPI spec.
- Given I expand an endpoint, when I view the request schema, then all required fields are marked.
- Given I click "Try it out" and provide valid parameters, when I submit, then the sandbox response is displayed.

---

**US-DEV-004** — Provision an API key  
*As a Developer, I want to generate an API key for a subscribed plan so that I can authenticate my API calls.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I am subscribed to a plan, when I click "Create Key", then a new API key is shown once (full plaintext).
- Given the key is created, when I refresh the page, then only a masked version (last 4 chars) is shown.
- Given the key is created, when I make a request using it, then the gateway authenticates me within 100 ms.

---

**US-DEV-005** — View my API key usage  
*As a Developer, I want to view real-time usage metrics for my API key so that I can track my consumption against my quota.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I open the key dashboard, when it loads, then I see requests used today, remaining quota, and a 24 h sparkline chart.
- Given my quota is > 80% consumed, then a warning banner is displayed.
- Given I have exceeded my quota, then the dashboard shows "Quota exhausted" and the reset time.

---

**US-DEV-006** — Test APIs in the sandbox  
*As a Developer, I want to test API calls in the sandbox environment so that I do not consume production quota during development.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I have a sandbox key, when I call the sandbox base URL, then the request is routed to mock responses, not the real upstream.
- Given the sandbox is used, when I check usage metrics, then sandbox requests do not count against my production quota.

---

**US-DEV-007** — Revoke an API key  
*As a Developer, I want to revoke an API key so that I can immediately invalidate a compromised key.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I click "Revoke", when I confirm, then the key is invalidated within 5 s.
- Given the key is revoked, when a request is made using it, then the gateway returns HTTP 401 within 100 ms.

---

**US-DEV-008** — Register a webhook endpoint  
*As a Developer, I want to register a webhook URL so that I receive event notifications from the gateway.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I provide a valid HTTPS URL and select events, when I save, then the endpoint appears in my webhook list.
- Given I trigger a test event, when the test delivery is made, then the delivery log shows the attempt and response code within 10 s.

---

**US-DEV-009** — Manage subscriptions  
*As a Developer, I want to upgrade my subscription plan so that I get higher rate limits for my production workload.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I am on the Free plan, when I choose to upgrade to Pro and pay, then my rate limit is updated immediately.
- Given the upgrade is successful, when I check my key limits, then the new limits are reflected.

---

**US-DEV-010** — Download usage report  
*As a Developer, I want to download a CSV of my API usage so that I can analyse it in my own tools.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I request a report for the last 30 days, when the job completes (≤ 2 min), then I receive an email with a download link.
- Given I click the link (valid 24 h), when the download starts, then I receive a valid CSV with headers: timestamp, endpoint, method, status, latency_ms.

---

**US-DEV-011** — View webhook delivery logs  
*As a Developer, I want to view the delivery history for my webhooks so that I can diagnose failed deliveries.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I open the webhook delivery log, when it loads, then I see each delivery: timestamp, event, attempt #, response code.
- Given a failed delivery, when I click "Retry", then a new delivery attempt is triggered immediately.

---

**US-DEV-012** — Reset password  
*As a Developer, I want to reset my password via email so that I can recover access if I forget it.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I request a password reset, when I submit my email, then I receive a reset link within 5 minutes.
- Given I click the link (valid 1 h), when I set a new password, then I am logged in automatically.

---

**US-DEV-013** — View API changelog  
*As a Developer, I want to see breaking changes between API versions so that I can plan migration work.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given a provider uploads a diff for v2, when I view the API changelog page, then I see added, removed, and changed endpoints highlighted.

---

**US-DEV-014** — Set up two-factor authentication  
*As a Developer, I want to enable TOTP-based 2FA on my account so that it is protected even if my password is compromised.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I open security settings, when I enrol a TOTP app, then I must verify with a code before 2FA is activated.
- Given 2FA is enabled, when I log in, then I am challenged for a TOTP code after password entry.

---

## Role: Admin

**US-ADM-001** — Approve an API publishing request  
*As an Admin, I want to review and approve API publishing requests so that only vetted APIs appear in the catalogue.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given a provider submits an API for review, when I open the review queue, then I see the API spec and metadata.
- Given I approve the request, when the status changes, then the API is visible in the catalogue and the provider receives an email.
- Given I reject the request, when I provide a rejection reason, then the provider receives an email with the reason.

---

**US-ADM-002** — Revoke any consumer's API key  
*As an Admin, I want to revoke any consumer's API key so that I can respond immediately to a security incident.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I search for a consumer, when I view their keys, then I can revoke any key with a single click.
- Given the key is revoked, when the consumer uses it, then they get HTTP 401 within 5 s.

---

**US-ADM-003** — Manage subscription plans  
*As an Admin, I want to create and modify subscription plans so that I can offer the right pricing tiers.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I create a plan with limits, when I save, then new subscribers can choose that plan immediately.
- Given I modify an existing plan's quota, when I save, then existing subscribers' limits are updated at their next quota reset.

---

**US-ADM-004** — Configure global plugins  
*As an Admin, I want to enable a global IP blacklist plugin so that blocked IPs are rejected before any routing logic.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I add an IP CIDR to the blacklist, when a request arrives from that IP, then the gateway returns HTTP 403 before auth checks.
- Given I remove a CIDR, when the next request arrives from that IP, then it proceeds normally.

---

**US-ADM-005** — View system audit log  
*As an Admin, I want to search the audit log by actor, action, and date so that I can investigate incidents.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I filter by actor email and date range, when I search, then matching entries are returned within 2 s.
- Given an audit entry, when I view it, then I see: timestamp, actor, action, resource type, resource ID, before/after values, IP address.

---

**US-ADM-006** — Configure alert thresholds  
*As an Admin, I want to configure error-rate and latency alert thresholds so that I am notified of degraded gateway performance.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I set error_rate_threshold=5%, when the 5-minute error rate exceeds 5%, then a Slack and PagerDuty alert fires within 60 s.
- Given the condition recovers, when error rate drops below threshold, then a recovery notification is sent.

---

**US-ADM-007** — Onboard a new API provider  
*As an Admin, I want to create a provider account and assign organisation so that providers can log in and publish APIs.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I provide the provider's email and organisation name, when I submit, then the provider receives an invitation email.
- Given the provider accepts the invitation and sets a password, then they can log in and access the provider dashboard.

---

**US-ADM-008** — Configure OIDC SSO for admin login  
*As an Admin, I want to configure OIDC SSO (Okta/Azure AD) for admin accounts so that admins use centralised identity.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I provide the issuer URL and client credentials, when I save, then the "Sign in with SSO" button appears on the login page.
- Given an admin uses SSO to log in, then their session is created without needing a local password.

---

**US-ADM-009** — Perform a hot-reload of gateway configuration  
*As an Admin, I want to reload gateway routes and plugin config without restarting pods so that changes are applied with zero downtime.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I publish a config change, when I trigger a reload, then in-flight requests complete normally and new requests use the new config.
- Given a reload fails validation, then the old config remains active and an error is logged.

---

**US-ADM-010** — Monitor system health dashboard  
*As an Admin, I want a real-time health dashboard showing pod status, Redis, Postgres, and queue depth so that I can triage incidents quickly.*  
**Priority:** P0  
**Acceptance Criteria:**
- Given I open the health dashboard, when it loads, then I see: ECS task count, Redis memory usage, Postgres connection pool utilisation, BullMQ job depth, and last-5-min error rate.
- Given a component is degraded, then its tile displays a red/amber indicator.

---

**US-ADM-011** — Export all consumer data for GDPR request  
*As an Admin, I want to export all data for a specific consumer on demand so that I can fulfil GDPR data subject access requests.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I search for a consumer by email, when I click "Export Data", then a ZIP of JSON files is generated and available for download within 5 minutes.
- Given the export is complete, when I review it, then it contains: account info, API keys (masked), usage events, webhook config, subscription history.

---

**US-ADM-012** — Delete a consumer account  
*As an Admin, I want to delete a consumer account and all associated data so that I can fulfil GDPR right-to-erasure requests.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I confirm account deletion, when I submit, then all PII is erased and API keys are immediately revoked.
- Given the account is deleted, when usage events reference the consumer, then the consumer field is replaced with an anonymised token.

---

## Role: Analyst

**US-ANA-001** — View platform-wide traffic trends  
*As an Analyst, I want to view platform-wide API traffic charts over time so that I can identify growth trends and peak usage windows.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I open the analytics overview, when it loads, then I see total requests per day over the last 30 days as a line chart.
- Given I hover over a data point, then I see exact request count, error count, and average latency for that day.

---

**US-ANA-002** — Compare API performance across versions  
*As an Analyst, I want to compare error rates and latency for v1 vs v2 of the same API so that I can validate that a new version is performing better.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I select an API and two versions, when I view the comparison chart, then error rate and p95 latency for both versions are overlaid on the same chart.

---

**US-ANA-003** — Identify top consumers by request volume  
*As an Analyst, I want to see a leaderboard of consumers by request volume so that I can understand who the heaviest API users are.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I open the top consumers report, when it loads, then I see the top 20 consumers ranked by request count for the selected period.
- Given I click a consumer, then I navigate to their detailed usage profile.

---

**US-ANA-004** — View error breakdown by status code  
*As an Analyst, I want a pie/bar chart of response status codes so that I can understand the distribution of errors.*  
**Priority:** P1  
**Acceptance Criteria:**
- Given I select a time range, when I view the error breakdown chart, then I see counts and percentages for 2xx, 4xx, 5xx grouped by status code.

---

**US-ANA-005** — Export analytics report as CSV  
*As an Analyst, I want to download a CSV of aggregated API usage for a date range so that I can build custom reports in Excel or BI tools.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I select a date range and granularity (hourly/daily), when I request the export, then the file is emailed to me within 5 minutes.
- Given the CSV is downloaded, when I open it, then it contains: date, api_id, route, method, request_count, error_count, p50_latency_ms, p95_latency_ms, p99_latency_ms.

---

**US-ANA-006** — Set up a custom alert  
*As an Analyst, I want to create an alert rule for a specific API's error rate so that I am notified when it degrades.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I create an alert for API X with error_rate > 10%, when the condition is met, then I receive a Slack message within 60 s.
- Given the condition clears, then I receive a recovery notification.

---

**US-ANA-007** — View subscription plan revenue breakdown  
*As an Analyst, I want to see monthly revenue by subscription plan so that I can evaluate plan profitability.*  
**Priority:** P2  
**Acceptance Criteria:**
- Given I open the revenue report, when it loads, then I see a bar chart of collected subscription fees per plan per month.
- Given I export the data, then the CSV contains: month, plan_name, subscriber_count, mrr_inr.

---
