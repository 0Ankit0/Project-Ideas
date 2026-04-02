# Business Rules — Survey and Feedback Platform

## Overview

This document defines all authoritative business rules for the Survey and Feedback Platform. Each rule
carries a unique identifier, name, plain-language description, enforcement point, and priority level.
Rules are the single source of truth for product, engineering, QA, and compliance teams.

**Priority levels:** Critical (hard-blocked at runtime) | High (4xx + audit event) | Medium (soft limit, admin override) | Low (warning only).

---

## Subscription and Limits Rules

#### BR-SUBS-001 — Monthly Response Quota
**Priority:** Critical | **Enforcement:** API middleware + billing service | **Tier Affected:** All

Free-tier workspaces are capped at 100 survey responses per calendar month. Starter: 1,000/month.
Business: 10,000/month. Enterprise: unlimited. The quota resets at midnight UTC on the billing
anniversary date. Workspace admins receive automated email alerts at 80% and 95% utilization. When
the quota is exhausted, new submissions return HTTP 402 and the respondent sees a configurable
"survey closed" message. Survey links remain navigable but submissions are blocked.

#### BR-SUBS-002 — Active Survey Limit
**Priority:** High | **Enforcement:** Survey creation service | **Tier Affected:** Free, Starter

The number of simultaneously active (published, accepting responses) surveys is capped by tier: Free
(3), Starter (25), Business and Enterprise (unlimited). Attempting to publish beyond the limit
returns HTTP 422 with `active_survey_limit_reached` and an upgrade prompt. Draft and archived surveys
are excluded from the count. Pausing a survey reduces the active count immediately.

#### BR-SUBS-003 — Team Member Seat Limits
**Priority:** High | **Enforcement:** Workspace member invitation service | **Tier Affected:** Free, Starter

Free: 1 seat (owner only). Starter: 5 seats. Business: 25 seats. Enterprise: unlimited. Inviting a
member beyond the seat limit returns HTTP 402. If a subscription is downgraded below current seat
count, excess accounts enter a read-only "pending removal" state. The workspace admin has 14 days to
reduce seats before excess accounts are automatically suspended.

#### BR-SUBS-004 — Branching Logic Feature Gate
**Priority:** Critical | **Enforcement:** Survey builder API validation | **Tier Affected:** Free, Starter

Conditional branching logic — skip logic, display logic, and calculated fields — is restricted to
Business and Enterprise tiers. If a Free or Starter payload includes branching rules, the API strips
the logic blocks, saves the survey without them, and returns HTTP 207 with a `feature_gate_warning`
array in the response body. An upgrade prompt is included. UI-level enforcement prevents the builder
from generating branching payloads on restricted tiers.

#### BR-SUBS-005 — Programmatic API Access
**Priority:** Critical | **Enforcement:** API key issuance service | **Tier Affected:** Free, Starter

REST API access, webhook configuration, and SDK integration are restricted to Business and Enterprise
tiers. Free and Starter workspaces cannot create API keys. Grandfathered keys (issued before this
policy) are rate-limited to 100 requests/day and return HTTP 403 on prohibited endpoints with a
tier-upgrade message in the response body. API documentation and sandbox environment access remain
available to all tiers for evaluation.

#### BR-SUBS-006 — File Upload Size Limits
**Priority:** High | **Enforcement:** API request validation before S3 multipart upload | **Tier Affected:** All

Per-file and per-survey upload limits by tier: Free (5 MB / 50 MB), Starter (10 MB / 200 MB),
Business (50 MB / 2 GB), Enterprise (100 MB / 10 GB). Accepted MIME types: PDF, DOCX, XLSX, PNG,
JPG, GIF, MP4, MP3, ZIP. Files violating size constraints return HTTP 413; unsupported MIME types
return HTTP 415. Limits are checked against the Content-Length header before the upload stream
begins to avoid unnecessary S3 partial-upload charges.

#### BR-SUBS-007 — Report Export Retention Period
**Priority:** High | **Enforcement:** S3 lifecycle policy + nightly Celery purge job | **Tier Affected:** All

Generated report exports (PDF, XLSX, CSV) are retained in S3 by tier: Free (7 days), Starter (90
days), Business (1 year), Enterprise (custom up to 7 years). Workspace admins receive email
notification 7 days before a report is permanently deleted. The nightly purge job marks files for
deletion; a 24-hour grace period applies before the S3 object is removed. This policy is independent
of the response data retention policy (BR-DATA-001).

#### BR-SUBS-008 — Platform Branding on Free Tier
**Priority:** Medium | **Enforcement:** Survey render service (server-side template injection) | **Tier Affected:** Free

Free-tier surveys display a "Powered by [Platform Name]" footer on the respondent-facing page.
This footer cannot be removed or hidden on Free tier. Starter and above may configure custom logos,
color themes, custom survey domains, and complete branding removal. Attempts to suppress the footer
via custom CSS are detected and overridden server-side during HTML template rendering. Brand
configuration changes take effect within 60 seconds via Redis cache invalidation.

#### BR-SUBS-009 — Multi-Language Survey Gate
**Priority:** Medium | **Enforcement:** Survey builder API | **Tier Affected:** Free, Starter

Multi-language survey variants are restricted to Business and Enterprise. Free and Starter may use
one locale only. The API rejects `translations` arrays on restricted tiers with HTTP 402.
Single-locale surveys fully support Unicode UTF-8 on all tiers.

#### BR-SUBS-010 — SSO and SAML Feature Gate
**Priority:** Critical | **Enforcement:** Authentication service + IdP configuration API | **Tier Affected:** Free, Starter, Business

SAML 2.0 SSO, SCIM directory sync, and custom OIDC identity providers are restricted to Enterprise
tier only. Google OAuth 2.0 social login is available on Starter and above. Magic link and
email/password authentication are available on all tiers. Free tier supports email/password and magic
link only. Attempting to configure a SAML provider on a non-Enterprise workspace returns HTTP 402.

---

## Survey Builder Rules

#### BR-FORM-001 — Maximum Questions Per Survey
**Priority:** Critical | **Enforcement:** Survey builder API + frontend validation | **Tier Affected:** All

Maximum questions per survey by tier: Free (10), Starter (50), Business (soft cap 500, unlimited on
request), Enterprise (unlimited). The counter includes all question types — including display-only
text blocks and page breaks. Exceeding the limit on save returns HTTP 422 with
`max_questions_exceeded`. The frontend disables the "Add Question" button when the limit is reached
and displays a tier-aware upgrade nudge.

#### BR-FORM-002 — Question Type Tier Restrictions
**Priority:** High | **Enforcement:** Survey builder API schema validation | **Tier Affected:** Free

Free tier question types: Multiple Choice, Single Select, Short Text, Long Text, Rating Scale,
Yes/No. Restricted to Starter+: Matrix, Ranking, File Upload, NPS, Slider, Date/Time. Restricted to
Business+: Payment (Stripe), Computed/Formula fields, Signature capture. The API rejects
unsupported question types with HTTP 422 and a `question_type_not_allowed` error code. The survey
builder UI filters the question palette by the workspace's active tier.

#### BR-FORM-003 — Conditional Logic Maximum Depth
**Priority:** High | **Enforcement:** Survey builder validation service | **Tier Affected:** Business, Enterprise

Conditional branching chains are limited to a maximum nesting depth of 10 levels. Circular
dependencies — where Question A's visibility depends on Question B whose visibility depends on
Question A — are detected during save via a directed-graph cycle check and rejected with
`circular_logic_detected`. The visual logic builder warns at depth 7 and hard-blocks save at depth 11.

#### BR-FORM-004 — Required Field Enforcement
**Priority:** High | **Enforcement:** Response submission API | **Tier Affected:** All

Questions marked as required must receive a non-null, non-empty answer before the final page
submission. Server-side validation enforces this regardless of client-side state. For multi-page
surveys, partial saves (page-by-page) store answers in the incomplete session; the final submission
endpoint validates required completeness across all pages before committing the response record.

#### BR-FORM-005 — Survey Expiry Date Rules
**Priority:** High | **Enforcement:** Response submission gateway | **Tier Affected:** All

Surveys may carry an optional expiry datetime (UTC). After expiry, the public survey URL returns a
configurable closure page and the submission API returns HTTP 410 (Gone). Expiry date limits: Free
(max 90 days from publish), Starter (max 1 year), Business and Enterprise (max 5 years). Surveys
without an expiry date remain active until manually closed. Expiry triggers a `survey.expired`
event, visible in the distribution dashboard.

#### BR-FORM-006 — Password-Protected Survey Access
**Priority:** Medium | **Enforcement:** Survey access gateway | **Tier Affected:** Starter+

Surveys on Starter and above may require a password before displaying content. Passwords are stored
as bcrypt hashes (cost factor 12) and are never returned in API responses or included in exports.
Respondent password attempts are rate-limited to 10 per hour per IP per survey; exceeding this
triggers a 1-hour IP lockout on that survey. Free tier may not enable password protection.

#### BR-FORM-007 — Per-Survey Response Cap
**Priority:** High | **Enforcement:** Response submission service (atomic Redis counter) | **Tier Affected:** All

Survey creators may configure a maximum response count per survey, independent of the monthly
workspace quota (BR-SUBS-001). When the cap is reached, the survey automatically closes and
subsequent access shows the closure page. The cap counter uses an atomic Redis INCR with a Lua script
to prevent race conditions under high concurrency. Default: no cap. Minimum configurable cap: 1.

#### BR-FORM-008 — Anonymous Survey Data Handling
**Priority:** High | **Enforcement:** Response collection service + audit log | **Tier Affected:** All

When a survey is flagged as anonymous, no PII (email, name, IP address, device fingerprint) is
stored with the response record. This flag is set at creation and cannot be changed after the first
response is collected. For deduplication, the system stores a one-way BLAKE2b hash of
(IP + user agent + survey ID + date) — this hash cannot be reversed. The audit log records the
anonymous configuration decision with the creator's identity and timestamp.

#### BR-FORM-009 — Welcome and Thank-You Pages
**Priority:** Low | **Enforcement:** Survey render service | **Tier Affected:** All

All surveys support a welcome page (shown before Question 1) and a thank-you page (shown after
submission). Both pages support Markdown, embedded S3-hosted images, and video embeds. Business and
Enterprise surveys may configure conditional redirect URLs on the thank-you page, routing respondents
to different URLs based on their NPS score or a specific answer value.

#### BR-FORM-010 — Survey Duplication and Templates
**Priority:** Low | **Enforcement:** Survey management service | **Tier Affected:** All

Any survey may be duplicated within the same workspace; copies start in Draft status with a "(Copy)"
suffix. Response data is not included. Platform templates are cloneable into any workspace. Custom
workspace templates are available on Business and Enterprise.

#### BR-FORM-011 — iFrame Embed Domain Whitelist
**Priority:** High | **Enforcement:** HTTP Content-Security-Policy header | **Tier Affected:** Starter+

Surveys embedded via `<iframe>` are restricted to a per-survey allowlist of domains. The CSP
`frame-ancestors` directive is populated from this list. An empty allowlist blocks all embedding. Limits:
Starter (10 domains per survey), Business and Enterprise (unlimited). Free tier surveys cannot be
embedded via iframe and must be accessed via a direct link.

#### BR-FORM-012 — Survey URL Slug Uniqueness
**Priority:** Critical | **Enforcement:** DB unique constraint + application validation | **Tier Affected:** All

Each published survey receives a globally unique 8-character alphanumeric slug for its public URL
(`/s/{slug}`). Custom vanity slugs (e.g., `/s/customer-nps-q4`) are available on Business and
Enterprise. Custom slugs must be 3–80 characters, URL-safe (a-z, 0-9, hyphens), and globally unique
across all workspaces. Conflicts return HTTP 409 with `slug_already_taken`.

---

## Response Collection Rules

#### BR-RESP-001 — One-Response-Per-Email Enforcement
**Priority:** High | **Enforcement:** Response submission service + Redis deduplication set | **Tier Affected:** All

For email-distributed surveys, each recipient email address may submit only one response per survey
by default. The check uses a Redis SET keyed by `dedup:{survey_id}:{sha256(email)}`. A duplicate
attempt returns HTTP 409 and shows the respondent a "You have already responded" message. Survey
creators may disable this rule to allow resubmission (useful for recurring pulse surveys).

#### BR-RESP-002 — IP-Based Deduplication for Anonymous Surveys
**Priority:** Medium | **Enforcement:** Response submission service + Redis sorted set | **Tier Affected:** All

Anonymous surveys limit one response per IP address per survey within a rolling 24-hour window via a
Redis sorted set with score=timestamp and TTL-based cleanup. Known proxy and VPN exit nodes
(MaxMind GeoIP commercial database, refreshed weekly) trigger a reCAPTCHA v3 challenge. Score
threshold: 0.5. Survey creators may disable IP deduplication for kiosk-mode deployments.

#### BR-RESP-003 — Partial Response Timeout
**Priority:** Medium | **Enforcement:** Celery Beat session cleanup job (runs nightly at 02:00 UTC) | **Tier Affected:** All

Incomplete sessions (respondent opened the survey but did not submit) are persisted in MongoDB for
7 days. After 7 days of inactivity the partial session is purged. Survey creators may configure a
shorter timeout (minimum 1 hour) per survey. Partial responses are included in completion-rate and
drop-off analytics but excluded from response exports unless the analyst explicitly includes them.

#### BR-RESP-004 — Response Editing Window
**Priority:** Medium | **Enforcement:** Response management service | **Tier Affected:** All

Authenticated respondents may edit their submission within a configurable editing window: Off, 1 hour,
24 hours, 7 days, or always (creator's choice). Each edit creates a new response version in the
audit table. The analytics dashboard reflects the most recent version. Creators on Business and
Enterprise may view the full version history. Editing is unavailable for anonymous surveys.

#### BR-RESP-005 — GDPR Right to Erasure
**Priority:** Critical | **Enforcement:** Privacy API + Celery erasure job | **Tier Affected:** All

Authenticated respondents may request erasure of their personal data via the privacy portal or
directly through the workspace admin. Upon verified request, PII fields are soft-deleted within 24
hours and hard-deleted within 30 days. Derived analytics aggregates are retained; individual response
records are purged. A non-PII tombstone (survey ID, timestamp, erasure request ID) is retained in
the audit log. Erasure requests are honored across all workspaces where the email appears.

#### BR-RESP-006 — Age Verification Gate
**Priority:** High | **Enforcement:** Survey access gateway | **Tier Affected:** All

Survey creators may enable an age verification gate requiring respondents to confirm they meet a
minimum age threshold (default 18, configurable 13–21). Age verification is self-declaration only;
no identity document is collected. Respondents declaring an age below the threshold receive the
survey closure page; no data is collected. Age gate interactions are logged non-attributably for
compliance auditing (timestamp, survey ID, declared outcome — no PII).

#### BR-RESP-007 — Consent Recording
**Priority:** Critical | **Enforcement:** Response submission service (synchronous) | **Tier Affected:** All

When a survey includes a `consent_checkbox` question type, the following fields are recorded
immutably in the audit log at submission time: respondent identifier hash, consent text version ID,
consent state (accepted/declined), ISO 8601 timestamp, IP address, geolocation (city, country code),
and user agent string. Consent records cannot be deleted even under GDPR erasure (retained 7 years
under GDPR Article 6(1)(c)). This record is available to workspace admins as a regulatory evidence
download.

#### BR-RESP-008 — Server-Side Score Computation
**Priority:** Medium | **Enforcement:** Analytics Lambda + DynamoDB | **Tier Affected:** All

All scored question types (NPS, Rating Scale, CSAT, Sentiment) compute scores server-side via the
analytics Lambda function, not in the client browser. NPS classification: 0–6 (Detractor), 7–8
(Passive), 9–10 (Promoter). CSAT: mean of 1–5 scale responses. Scores are stored in DynamoDB and
dashboard counters are refreshed within 2 seconds of each new response (BR-ANLY-001).

#### BR-RESP-009 — Webhook Dispatch on Submit
**Priority:** High | **Enforcement:** Celery webhook dispatcher | **Tier Affected:** Business, Enterprise

A `response.submitted` webhook is dispatched within 5 seconds of response commit (SLA) on Business
and Enterprise tiers. Payloads are signed with HMAC-SHA256 using the workspace webhook secret.
Failed deliveries (non-2xx response or timeout) are retried with exponential backoff at 1 min, 5 min,
30 min, 2 h, and 6 h. After 5 failures the event is moved to the dead-letter queue and the workspace
admin is notified. Webhooks are disabled on Free and Starter.

#### BR-RESP-010 — Bulk Response Import
**Priority:** Low | **Enforcement:** Import service | **Tier Affected:** Business, Enterprise

CSV/XLSX import is available on Business and Enterprise. Rows not conforming to the survey schema
are rejected with a summary. Imported responses are tagged `source:"import"` and excluded from
automated follow-ups. Limits: 50 MB file size, 100,000 rows per operation.

---

## Distribution Rules

#### BR-DIST-001 — Daily Email Send Quotas
**Priority:** Critical | **Enforcement:** Distribution service + SendGrid sub-user quota | **Tier Affected:** All

Daily outbound email send limits per workspace: Free (0 — no email distribution), Starter (5,000),
Business (50,000), Enterprise (custom default 500,000). Limits are validated before campaign
dispatch; campaigns that would exceed the remaining daily quota are either split across days or
rejected based on the workspace preference setting. Monthly aggregate limits apply at the SendGrid
sub-user account level linked to each workspace.

#### BR-DIST-002 — Mandatory Unsubscribe Mechanism
**Priority:** Critical | **Enforcement:** Email template validator + SendGrid suppression webhook | **Tier Affected:** All

Every outbound survey invitation email must contain a valid one-click unsubscribe link. Templates
missing the `{{unsubscribe_link}}` merge tag are rejected by the template validator during campaign
creation. Unsubscribe events received via SendGrid's Event Webhook trigger immediate suppression
(within 10 seconds) via the SendGrid Suppression Groups API. Global unsubscribes are honored across
all campaigns within the same workspace.

#### BR-DIST-003 — Spam Score Threshold
**Priority:** High | **Enforcement:** Distribution service + SpamAssassin scan before send | **Tier Affected:** All

All email templates are scanned with SpamAssassin before dispatch. Templates scoring > 5.0 are hard-
blocked and flagged for creator review with a detailed rule breakdown. Templates scoring 3.0–5.0
trigger a warning that the creator must acknowledge before sending. Score factors include: subject
line patterns, HTML-to-text ratio, link density, SPF/DKIM alignment, and content heuristics.

#### BR-DIST-004 — Sending Domain Verification Required
**Priority:** Critical | **Enforcement:** Domain verification service (DNS polling) | **Tier Affected:** All (email distribution)

Workspaces must verify domain ownership before dispatching email campaigns. Required DNS records:
SPF (`v=spf1 include:sendgrid.net ~all`), DKIM (CNAME to SendGrid signing domain), and DMARC
(`v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@domain.com`). DNS propagation is polled every
5 minutes for up to 48 hours. Campaigns dispatched on an unverified domain return HTTP 400 with
`domain_not_verified`.

#### BR-DIST-005 — Personalized Survey Link Expiry
**Priority:** High | **Enforcement:** Survey access gateway (JWT expiry claim) | **Tier Affected:** All

Personalized survey links delivered via email campaigns embed a signed JWT with an expiry claim.
Default link TTL: 30 days. Creators may configure 1 day to 365 days. Expired links return HTTP 410
with a configurable expiry message. Public (non-personalized) links do not have a link-level expiry
unless the survey itself expires per BR-FORM-005.

#### BR-DIST-006 — QR Code Generation and Validity
**Priority:** Low | **Enforcement:** QR generation service | **Tier Affected:** Starter+

QR codes auto-generated for every published survey on Starter+. Codes encode the public URL and stay
valid while the survey is active; regenerated on URL change. Download formats: SVG, PNG (300 DPI),
PDF. Free tier QR codes available on manual request via support.

#### BR-DIST-007 — Embed Code Domain Enforcement
**Priority:** High | **Enforcement:** CSP header middleware + Origin/Referer validation | **Tier Affected:** Starter+

See also BR-FORM-011. The survey API validates the `Origin` and `Referer` headers on
iframe-loaded endpoints. Requests from non-whitelisted origins return HTTP 403. The JavaScript embed
SDK enforces the same domain whitelist before rendering the survey modal, rejecting unlisted host
origins client-side as a first defense.

#### BR-DIST-008 — SMS Opt-In Compliance
**Priority:** Critical | **Enforcement:** SMS distribution pre-send filter | **Tier Affected:** Starter+

SMS distribution may only target phone numbers with documented prior opt-in consent. Required opt-in
record fields: phone number, consent timestamp, consent source (form URL or event ID), and workspace
ID. Contacts without opt-in records are automatically filtered before any SMS send. TCPA-compliant
consent collection forms are available in the platform's form builder. STOP/HELP replies are
processed via Twilio inbound webhook within 30 seconds.

---

## Analytics Rules

#### BR-ANLY-001 — Real-Time Counter Update Interval
**Priority:** High | **Enforcement:** Analytics Lambda + DynamoDB atomic update | **Tier Affected:** All

Dashboard response counters (total responses, completion rate, NPS, CSAT) must reflect new
submissions within 2 seconds. The Kinesis → Lambda pipeline achieves this via atomic DynamoDB
`ADD` update expressions triggered immediately on `response.submitted` event consumption. FastAPI
dashboard reads use strongly consistent DynamoDB reads to guarantee freshness without a caching layer.

#### BR-ANLY-002 — NPS Score Calculation Formula
**Priority:** High | **Enforcement:** Analytics Lambda | **Tier Affected:** All (NPS question type)

`NPS = (count(scores 9-10) / total) - (count(scores 0-6) / total) * 100`
expressed as an integer in the range -100 to +100. Passives (7–8) are included in the denominator
but not in either group. The platform displays NPS rounded to the nearest integer. NPS requires
a minimum of 10 responses (BR-ANLY-005); below this threshold the widget shows "Insufficient data
(n={count})".

#### BR-ANLY-003 — CSAT Score Calculation Formula
**Priority:** Medium | **Enforcement:** Analytics Lambda | **Tier Affected:** All (CSAT question type)

`CSAT% = (count(responses >= 4 on a 1-5 scale) / total_responses) * 100`
CSAT is expressed as a percentage (0–100%). The analytics widget also displays mean rating, median
rating, standard deviation, and a bar chart of score distribution across all 5 values. Like NPS,
CSAT requires n >= 10 responses before the percentage is displayed.

#### BR-ANLY-004 — Automated Sentiment Analysis
**Priority:** Medium | **Enforcement:** Analytics Lambda + Amazon Comprehend | **Tier Affected:** Business, Enterprise

Open-text responses are analyzed for sentiment using Amazon Comprehend. Classification thresholds:
Positive (confidence > 0.70), Negative (confidence > 0.70 for negative class), Neutral (0.40–0.70
neither positive nor negative), Mixed (positive + negative both > 0.40). Supported languages:
English, Spanish, French, German, Italian, Portuguese, Japanese. Sentiment results are stored as
metadata on the response record and aggregated into the Sentiment Overview analytics widget.

#### BR-ANLY-005 — Minimum Response Count for Statistical Display
**Priority:** High | **Enforcement:** Analytics API response serializer | **Tier Affected:** All

Any computed metric (NPS, CSAT, mean rating, percentage breakdown, sentiment score) for a given
segment is only displayed when n >= 10 responses exist for that segment. Segments below the threshold
display "Responses too few to display (n={count})". The default threshold of 10 may be configured
between 5 and 50 on Enterprise tier. This rule protects respondent anonymity in segmented and
cross-filtered analytics views.

#### BR-ANLY-006 — PII Controls in Data Exports
**Priority:** Critical | **Enforcement:** Export service + RBAC middleware | **Tier Affected:** All

CSV/XLSX exports include PII columns (email, name, phone) only when: (1) the survey is non-anonymous,
(2) the exporting user holds Owner or Admin role, and (3) a valid DPA is on file for the workspace
(Business/Enterprise). Viewer-role exports replace PII columns with `[REDACTED]`. IPv4 addresses are
always truncated to /24; IPv6 to /48 in all exports regardless of role.

#### BR-ANLY-007 — Cross-Filter Report Limits
**Priority:** Medium | **Enforcement:** Report query service + PostgreSQL query timeout | **Tier Affected:** Business, Enterprise

Cross-filter reports (segmenting responses by one question's answer to filter another) are available
on Business and Enterprise. Queries execute against PostgreSQL with a 30-second timeout; queries
exceeding this are enqueued as background jobs with email notification on completion. The report
builder limits simultaneous cross-filter dimensions to 5. Pre-computed DynamoDB aggregates are used
for common filter combinations to reduce PostgreSQL load.

#### BR-ANLY-008 — Trend and Survey Comparison Analysis
**Priority:** Low | **Enforcement:** Analytics service | **Tier Affected:** Business, Enterprise

Trend analysis requires at least 2 data points in separate time periods each with n >= 10 responses.
Survey comparison requires both surveys to share at least one linked question (matched by question
link ID or identical question text). Results render as Recharts time-series line charts and grouped
bar charts in the React frontend with configurable date-range buckets (day/week/month/quarter).

---

## Team and Workspace Rules

#### BR-TEAM-001 — Workspace Role Hierarchy
**Priority:** Critical | **Enforcement:** RBAC middleware on every API request | **Tier Affected:** All

Workspace roles in descending permission order: Owner > Admin > Editor > Analyst > Viewer.
Owner: all permissions including billing and workspace deletion. Admin: all except workspace deletion
and billing management. Editor: create/edit surveys, manage distributions, view own analytics.
Analyst: read-all analytics and exports, no survey editing. Viewer: read-only access to surveys and
basic result summaries. Role is checked on every protected API endpoint via a FastAPI dependency.

#### BR-TEAM-002 — Single Workspace Owner Constraint
**Priority:** Critical | **Enforcement:** Database unique constraint + ownership transfer service | **Tier Affected:** All

Each workspace has exactly one Owner at any time, enforced by a partial unique index
`(workspace_id WHERE role = 'owner')`. Ownership transfer requires email confirmation from both the
current Owner and the new Owner. During transfer, the previous Owner is atomically downgraded to
Admin. Ownership cannot be transferred to a member from a different IdP (e.g., Google SSO to SAML)
without first linking the accounts.

#### BR-TEAM-003 — Workspace Invitation Expiry
**Priority:** Medium | **Enforcement:** Invitation service + nightly expiry job | **Tier Affected:** All

Workspace member invitations expire after 72 hours if not accepted. Expired invitations must be
re-sent by an Admin or Owner. Pending invitations count against the seat limit (BR-SUBS-003). If
the workspace seat limit is reached before the invitation is accepted, the invitation is automatically
voided and the invitee is notified. Resent invitations generate a new JWT-signed invitation token.

#### BR-TEAM-004 — Survey Ownership on Member Deactivation
**Priority:** High | **Enforcement:** Member deactivation service | **Tier Affected:** All

When a workspace member is deactivated, all surveys owned by that member are automatically
transferred to the workspace Owner. Response data, distribution history, and analytics are retained
intact. The original creator is recorded in the survey's audit trail. Deactivated members retain
read-only API access to their own data exports for 30 days before their account is fully archived.

#### BR-TEAM-005 — Immutable Audit Log for Administrative Actions
**Priority:** High | **Enforcement:** Audit log service (async write-behind) | **Tier Affected:** All

All administrative actions are recorded in the audit log: member role changes, survey lifecycle
events (publish/pause/archive/delete), subscription changes, integration configurations, data
exports, and webhook configuration changes. Each entry records: actor user ID, action type, target
resource type and ID, before/after state (JSON diff), IP address, timestamp, and request trace ID.
Audit log rows are written to a write-once append-only PostgreSQL table with row-level security
preventing UPDATE and DELETE for all application roles.

#### BR-TEAM-006 — SSO Enforcement Policy
**Priority:** High | **Enforcement:** Authentication service | **Tier Affected:** Enterprise

Enterprise workspaces may enforce SSO-only login, disabling email/password and magic-link
authentication for non-Owner members. When SSO enforcement is active, members must authenticate via
the configured SAML/OIDC provider. The workspace Owner retains an emergency email/password fallback
protected by TOTP MFA. SSO enforcement changes are audit-logged and require Owner confirmation via
a TOTP-verified session.

#### BR-TEAM-007 — Multi-Factor Authentication
**Priority:** High | **Enforcement:** Authentication service | **Tier Affected:** All (optional); Enterprise (enforceable)

Users may enable TOTP-based MFA on their accounts at any time. Enterprise admins may mandate MFA for
all workspace members; non-enrolled members are blocked from workspace access until enrollment is
complete. Setup generates 10 single-use backup recovery codes displayed once at enrollment. Lost MFA
devices require identity verification with platform support before account recovery proceeds.

---

## Data Retention Rules

#### BR-DATA-001 — Response Data Retention
**Priority:** Critical | **Enforcement:** Data lifecycle service (nightly Celery job at 03:00 UTC) | **Tier Affected:** All

Default raw response retention: 2 years from submission date. Business and Enterprise admins may
configure 30 days – 7 years. Free and Starter are fixed at 2 years. Responses past the retention
date are hard-deleted from PostgreSQL and MongoDB. Associated S3 file uploads are purged via S3
Object Lifecycle rules with matching expiry tags. A deletion summary is logged in the audit trail.
Legal holds (BR-DATA-007) suspend this policy for held records.

#### BR-DATA-002 — Survey Definition Retention
**Priority:** Medium | **Enforcement:** Survey archival service | **Tier Affected:** All

Survey definitions are retained indefinitely while the workspace is active. Deleted surveys enter a
30-day soft-delete grace period (recoverable by Admin/Owner) before hard deletion. Hard deletion of
a survey triggers cascading hard deletion of all associated responses unless a legal hold is active.
Survey JSON export is available at any time before hard deletion for creator-side archival.

#### BR-DATA-003 — Contact and Audience List Retention
**Priority:** Medium | **Enforcement:** Contact management service | **Tier Affected:** All

Audience lists and contact records are retained for the life of the workspace. Unsubscribed contacts
are retained in the suppression list indefinitely to prevent accidental future sends. Workspace
deletion initiates a 30-day soft-delete window; after 30 days all contact PII is purged. Individual
GDPR/CCPA deletion requests replace the contact record with a non-PII tombstone preserving only the
suppression status.

#### BR-DATA-004 — Audit Log Immutability and Retention
**Priority:** Critical | **Enforcement:** Write-once PostgreSQL table with row-level security | **Tier Affected:** All

Audit log entries are retained for 7 years regardless of workspace subscription tier or account
status. The audit table uses a PostgreSQL row security policy granting INSERT to the application
service role and denying UPDATE and DELETE to all roles including Super Admin. Audit data may be
exported by Super Admin for compliance investigations. Workspace deletion does not trigger audit log
purge.

#### BR-DATA-005 — Analytics Aggregate Retention
**Priority:** Medium | **Enforcement:** DynamoDB item TTL | **Tier Affected:** All

Pre-aggregated analytics counters in DynamoDB are retained for 3 years with no TTL set on aggregate
records. When response data is purged per BR-DATA-001, associated DynamoDB aggregates are retained
for an additional 12 months for historical trend continuity before their TTL activates. Raw data
powering custom date-range queries in PostgreSQL follows the response retention policy.

#### BR-DATA-006 — Backup Retention Schedules
**Priority:** Critical | **Enforcement:** AWS RDS automated backup + S3 lifecycle | **Tier Affected:** All

RDS PostgreSQL automated backups: 35-day retention (configurable 7–35 days per tier). DocumentDB
cluster snapshots: 35-day retention. ElastiCache Redis RDB snapshots: daily, 14-day retention. S3
bucket versioning: enabled on all workspace data buckets; non-current versions expire after 90 days.
All backups are encrypted with KMS CMK and stored in an isolated backup AWS account.

#### BR-DATA-007 — Legal Hold
**Priority:** Critical | **Enforcement:** Legal hold service + data lifecycle bypass flag | **Tier Affected:** Business, Enterprise

Enterprise workspace Owners and Super Admins may place a legal hold on a workspace, survey, or
specific respondent's data. Legal holds suspend all data retention, archival, and deletion policies
for the held scope. Holds are logged in the audit trail with requester identity, timestamp, and
stated reason. Legal holds must be explicitly lifted; they do not expire automatically. Legal hold
operations require elevated IAM permissions and trigger a Super Admin notification.

#### BR-DATA-008 — Consent Record Immutability
**Priority:** Critical | **Enforcement:** Immutable consent store + audit log | **Tier Affected:** All

Consent records (survey access consent, data processing consent, marketing opt-in) are stored in an
append-only immutable table. Each record contains: respondent identifier hash, consent type, consent
text version ID, consent state, timestamp (UTC milliseconds), IP address, geolocation
(city, country code), user agent, and survey version ID. Consent records are retained for 7 years
under GDPR Article 6(1)(c) and cannot be deleted by any erasure or purge operation.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies
All response data is processed under applicable data protection law — GDPR (EU/EEA), CCPA
(California), PDPA (Thailand), LGPD (Brazil). The platform provides workspace-level data residency
controls (US, EU, APAC) to ensure data sovereignty compliance. A designated Data Protection Officer
(DPO) is responsible for EU GDPR operations and is the contact for supervisory authority inquiries.
Sensitive-category data surveys require an explicit consent question and a workspace-level sensitive
data declaration before publishing is permitted.

### 2. Survey Distribution Policies
All outbound email distribution must comply with CAN-SPAM Act (US), CASL (Canada), GDPR Articles
13/14 (EU transparency obligations), and applicable local anti-spam laws. Workspace admins
acknowledge these obligations at the time of initial domain verification setup. The platform reserves
the right to suspend email distribution for workspaces with abuse complaint rates exceeding 0.1% or
bounce rates exceeding 5% of total sends in any rolling 7-day period.

### 3. Analytics and Retention Policies
Analytics data is stored in the workspace-selected residency region. Aggregate analytics at n >= 10
do not constitute personal data under GDPR Recital 26. Workspace deletion is irreversible after the
30-day soft-delete window. Downloaded exports become the admin's sole responsibility for downstream
compliance.

### 4. System Availability Policies
Availability is measured at `POST /api/v1/responses` returning HTTP 2xx within 10 s from three
synthetic probes (US-East, EU-West, AP-Southeast). Maintenance windows are excluded from SLA
calculations. Credits are issued per the subscription SLA addendum for verified breaches.
