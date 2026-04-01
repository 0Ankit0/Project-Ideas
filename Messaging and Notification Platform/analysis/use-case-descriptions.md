# Use Case Descriptions — Messaging and Notification Platform

**Version:** 1.0
**Status:** Approved
**Last Updated:** 2025-01
**Module:** Analysis / Requirements

---

## Introduction

This document provides structured, detailed descriptions for the eleven highest-priority use cases identified in the Use Case Diagram. Each description follows the standard template: identification metadata, pre/post-conditions, a numbered main success flow, alternative flows for common variants, exception flows for error conditions, and references to governing business rules.

These descriptions are intended to be directly actionable by development squads during sprint planning and acceptance test authoring.

---

## UC-001: Send Transactional Email

| Field | Value |
|-------|-------|
| **ID** | UC-001 |
| **Actor(s)** | Developer / API User |
| **Trigger** | Client application calls `POST /v1/messages` with `channel: email` and a valid `template_id`. |
| **Preconditions** | API key is valid and active; template is in PUBLISHED state; recipient email is present and not on suppression list; tenant has an active email provider configured. |
| **Postconditions** | Message record is created with status `ACCEPTED`; message is enqueued on the transactional topic; delivery status events are published; webhook is triggered if configured. |
| **Priority** | High |

**Main Flow:**
1. Developer submits `POST /v1/messages` with API key, recipient email, template ID, template variables, and optional `idempotency_key`.
2. API gateway authenticates the API key and resolves the tenant context.
3. System validates the request payload: required fields, email format, template existence.
4. System performs idempotency check — if a matching `idempotency_key` already exists, returns the existing message record with `HTTP 200`.
5. System evaluates rate limits for the tenant and recipient; rejects with `HTTP 429` if any limit is exceeded.
6. System queries the suppression list and consent store; if the recipient is suppressed, records a `SUPPRESSED` event and returns `HTTP 202` without dispatch.
7. System resolves the requested template version (defaults to latest PUBLISHED if version not specified).
8. Template Engine renders the template with the provided variables, producing channel-specific content (HTML body, plain-text body, subject line).
9. System persists a message record with status `QUEUED` and publishes it to the `notifications.transactional.email` topic.
10. API returns `HTTP 202 Accepted` with `message_id` and `status: QUEUED`.
11. Delivery worker claims the message, selects the primary email provider, and submits via provider API.
12. On provider acceptance, status is updated to `PROVIDER_ACCEPTED`.
13. Provider asynchronously delivers the email and returns a delivery webhook confirming `DELIVERED`.
14. System publishes `message.delivered` event and triggers tenant webhook if configured.

**Alternative Flows:**
- **AF-1 (Scheduled Send):** If `send_at` is specified in the request, the message is persisted with status `SCHEDULED` and no topic publish occurs until the scheduled time.
- **AF-2 (Multi-locale):** If the recipient's locale differs from the template default, the system resolves the locale variant of the template if one exists; otherwise falls back to the default locale.
- **AF-3 (CC/BCC):** If `cc` or `bcc` fields are present, the system creates subordinate message records linked to the primary and dispatches to each address.

**Exception Flows:**
- **EF-1 (Provider Rejection):** If the email provider returns a permanent rejection (4xx), the system marks the message `FAILED`, records the reason, and does not retry. A `message.failed` event is published.
- **EF-2 (Provider Timeout / Transient Error):** If the provider returns 5xx or times out, the system schedules a retry with exponential backoff. After max retries, the message moves to `FAILED` and is placed on the dead-letter queue.
- **EF-3 (Template Render Failure):** If a required template variable is missing or the template contains a rendering error, the system immediately returns `HTTP 422 Unprocessable Entity` with a validation error listing missing variables.
- **EF-4 (Invalid Recipient):** If the email address is syntactically invalid, the system returns `HTTP 400` with field-level validation detail.

**Business Rules:**
- BR-01: Idempotency keys are valid for 24 hours; duplicate requests within that window return the original response.
- BR-02: Transactional messages have delivery SLA of p95 provider handoff < 5 seconds.
- BR-03: Suppression check takes precedence over all other dispatch logic; suppressed sends must be audit-logged.
- BR-04: Template must be in PUBLISHED state; DRAFT or DEPRECATED templates are rejected at dispatch time.

---

## UC-002: Send SMS Notification

| Field | Value |
|-------|-------|
| **ID** | UC-002 |
| **Actor(s)** | Developer / API User |
| **Trigger** | Client application calls `POST /v1/messages` with `channel: sms` and a valid `template_id`. |
| **Preconditions** | API key is valid; template is PUBLISHED and has an SMS body variant; recipient phone number is in E.164 format and not suppressed; tenant has an SMS provider configured. |
| **Postconditions** | SMS message is queued and dispatched; delivery status is tracked; opt-out keywords in replies are processed asynchronously. |
| **Priority** | High |

**Main Flow:**
1. Developer submits `POST /v1/messages` with API key, recipient phone (E.164), template ID, and variables.
2. API gateway authenticates and resolves tenant.
3. System validates phone number format (E.164 strict), template existence, and SMS channel availability.
4. System performs idempotency check.
5. System evaluates rate limits (per recipient, per tenant, per country code if configured).
6. System queries SMS suppression list (includes opt-outs received via SMS STOP keywords).
7. Template Engine renders the SMS body, applying character encoding rules (GSM-7 or UCS-2) and splitting into segments if length exceeds 160/70 characters.
8. System persists the message and publishes to `notifications.transactional.sms` topic.
9. Returns `HTTP 202 Accepted` with `message_id`.
10. Delivery worker claims message, selects SMS provider (Twilio primary), submits via REST API.
11. Provider sends message and returns a message SID.
12. Provider webhook asynchronously reports delivery receipt (`delivered`, `undelivered`, `failed`).
13. System updates message status and publishes delivery event.

**Alternative Flows:**
- **AF-1 (Long Message):** If rendered content exceeds single-segment length, the system creates a concatenated SMS (UDH) and records segment count for billing reconciliation.
- **AF-2 (Alphanumeric Sender):** If the tenant has configured an alphanumeric sender ID, the system selects a supported provider route and validates country compatibility.

**Exception Flows:**
- **EF-1 (Invalid Phone Number):** Provider rejects the number as invalid (e.g., unallocated range). System marks `FAILED` with error code `INVALID_RECIPIENT`.
- **EF-2 (Provider Outage):** Primary provider returns 5xx. System retries on secondary provider in the configured failover chain.
- **EF-3 (Country Restriction):** Tenant's provider configuration does not support the destination country code. System rejects with `HTTP 422` and error code `UNSUPPORTED_DESTINATION`.

**Business Rules:**
- BR-05: SMS opt-out via STOP keyword must be honoured immediately across all tenants sharing the same long code or short code.
- BR-06: Message content must not exceed 1600 characters after rendering (10 segments maximum).
- BR-07: NDNC/TCPA compliance checks apply for US phone numbers; carrier lookups are performed for regulatory destinations.

---

## UC-003: Send Push Notification

| Field | Value |
|-------|-------|
| **ID** | UC-003 |
| **Actor(s)** | Developer / API User |
| **Trigger** | Client application calls `POST /v1/messages` with `channel: push` and a device token or contact ID. |
| **Preconditions** | Device token is registered and active; template is PUBLISHED with a push variant; tenant has FCM or APNS credentials configured; app bundle ID is registered in platform settings. |
| **Postconditions** | Push notification is delivered to the device or marked undeliverable if token is stale; stale tokens trigger automatic token invalidation. |
| **Priority** | High |

**Main Flow:**
1. Developer submits request with device token (or contact ID for multi-device lookup), template ID, variables, and optional `ttl` (time-to-live).
2. System authenticates API key and validates the push channel payload (title, body, badge count, deep-link URL, custom data).
3. If contact ID is provided, system resolves all active device tokens for the contact.
4. System checks suppression and notification permission status (user may have revoked OS-level permission).
5. Template Engine renders the push payload: notification title, body, image URL, action buttons, and custom data key-value pairs.
6. System publishes to `notifications.transactional.push` topic with provider routing metadata (iOS vs Android).
7. Delivery worker routes to FCM for Android tokens or APNS for iOS tokens.
8. Provider accepts and delivers notification; returns delivery acknowledgement.
9. System updates message status; publishes `message.delivered` or `message.failed` event.

**Alternative Flows:**
- **AF-1 (Multi-Device Fan-out):** If the contact has multiple active tokens, the system dispatches individual push messages to each device and aggregates the delivery statuses under the parent message ID.
- **AF-2 (Silent / Data Push):** If the template is configured as a data-only push, no visible notification is displayed; used for background refresh triggers.

**Exception Flows:**
- **EF-1 (Invalid/Stale Token):** FCM returns `NOT_REGISTERED` or APNS returns `BadDeviceToken`. System marks the token inactive in the device registry and records `FAILED` status.
- **EF-2 (Rate Limit by Provider):** FCM enforces per-device send rates. System backs off and retries with jitter.
- **EF-3 (TTL Expiry):** If the device is offline and TTL expires before delivery, provider discards the notification. System records `EXPIRED` status.

**Business Rules:**
- BR-08: Stale token invalidation must be propagated to the device registry within 5 minutes of provider rejection.
- BR-09: Push TTL defaults to 86400 seconds (24 hours) unless overridden in the request.

---

## UC-004: Create and Publish Template

| Field | Value |
|-------|-------|
| **ID** | UC-004 |
| **Actor(s)** | Marketing User, Approver (for regulated templates) |
| **Trigger** | Marketing User selects "New Template" in the management console or calls `POST /v1/templates`. |
| **Preconditions** | User has template editor role; tenant account is active; the intended channel is enabled for the tenant. |
| **Postconditions** | A new template version is created in PUBLISHED state (or REVIEW state if approval is required); the template is immediately available for message dispatch. |
| **Priority** | High |

**Main Flow:**
1. Marketing User opens the template editor and specifies: template name, description, channel (email / SMS / push), category, and default locale.
2. User authors the template body using Handlebars/Jinja2 syntax. For email: HTML body + plain-text fallback + subject line.
3. User declares template variables in the variable schema panel (name, type, required flag, default value).
4. User clicks "Validate" — system performs schema validation: required fields present, variable syntax valid, HTML safe (no script injection), subject line length within provider limits.
5. System renders a preview using sample variable values.
6. User reviews the rendered preview across email clients (desktop, mobile, dark mode).
7. User clicks "Save as Draft" — system creates template version 1 in DRAFT state.
8. User clicks "Submit for Publish" — if no approval policy applies, status transitions directly to PUBLISHED.
9. System publishes a `template.published` event; the template is now available for sends.

**Alternative Flows:**
- **AF-1 (Approval Required):** If the template category requires approval (e.g., financial, medical), step 8 transitions the template to REVIEW state. An approver is notified via internal notification. Approver reviews and approves or rejects.
- **AF-2 (Multi-locale):** After initial creation, user adds locale variants (e.g., `fr-FR`, `de-DE`) by cloning the default content and translating. Each locale variant shares the same template ID but has locale-scoped content.
- **AF-3 (API-Driven Creation):** Developer calls the REST API to create and publish a template programmatically, bypassing the visual editor. Variable schema is passed as JSON. Approval workflow still applies.

**Exception Flows:**
- **EF-1 (Schema Validation Failure):** System returns validation errors listing each failing rule (e.g., "variable `user_name` referenced in body but not declared in schema"). Template is not saved.
- **EF-2 (Duplicate Name):** A template with the same name and channel already exists in the tenant. System returns a conflict error with a link to the existing template.
- **EF-3 (Approval Rejection):** Approver rejects the template with a comment. Status returns to DRAFT. Author receives a rejection notification.

**Business Rules:**
- BR-10: Template version numbers are immutable once published. Edits create a new version.
- BR-11: A template must have at least one PUBLISHED version before it can be used in a send request.
- BR-12: HTML content is sanitised server-side using an allow-list before storage; script tags, iframes, and javascript: URIs are stripped.
- BR-13: Subject lines must be 10–998 characters (RFC 2822 compliance) and must not contain newlines.

---

## UC-005: Batch Message Send

| Field | Value |
|-------|-------|
| **ID** | UC-005 |
| **Actor(s)** | Developer / API User, System (Scheduler) |
| **Trigger** | Client calls `POST /v1/batches` with a recipient list (inline or audience segment ID), template ID, and optional scheduling parameters. |
| **Preconditions** | Template is PUBLISHED; recipient list or segment is defined; tenant has sufficient quota for the batch size; provider capacity is within limits. |
| **Postconditions** | All eligible recipients in the batch have individual message records created; suppressed recipients are excluded and logged; delivery progresses asynchronously. |
| **Priority** | High |

**Main Flow:**
1. Client submits batch request with: template ID, channel, recipient list or segment ID, variable overrides per recipient (optional), batch name, and optional `send_at`.
2. System validates the batch request, confirms template is PUBLISHED, and records a batch job record with status `ACCEPTED`.
3. System resolves the recipient list (inline array or segment evaluation against contact database).
4. System evaluates suppression and consent for all recipients in bulk; marks ineligible recipients as `SUPPRESSED` in the batch recipient table.
5. System splits the eligible recipient list into worker-size chunks (configurable, default 500 per chunk).
6. System enqueues chunks onto the `notifications.promotional` topic (lower priority than transactional).
7. Returns `HTTP 202` with `batch_id` and initial `accepted_count`.
8. Delivery workers claim chunks, render each message individually (personalisation variables applied per recipient), and dispatch.
9. Batch progress is updated as workers complete chunks: `dispatched_count`, `delivered_count`, `failed_count`.
10. When all chunks are processed, batch status transitions to `COMPLETED` or `COMPLETED_WITH_ERRORS`.
11. Batch completion event is published; summary webhook fires if configured.

**Alternative Flows:**
- **AF-1 (Segment-based Audience):** Recipient list is resolved dynamically from an audience segment definition. Segment is evaluated at batch creation time and snapshotted; late-joining contacts are not included.
- **AF-2 (Scheduled Batch):** `send_at` is in the future. Batch is persisted with `SCHEDULED` status; scheduling service publishes chunks to the topic at the specified time.

**Exception Flows:**
- **EF-1 (Quota Exceeded):** Requested batch size exceeds tenant's daily or monthly send quota. System returns `HTTP 429` with remaining quota information.
- **EF-2 (Empty Recipient List after Suppression):** All recipients are suppressed. System transitions batch to `COMPLETED` with zero dispatches and logs a suppression summary.

**Business Rules:**
- BR-14: Promotional batches are processed on a lower-priority queue to prevent starvation of transactional messages.
- BR-15: Maximum inline recipient list size per API request is 10,000 records; larger batches must use segment IDs.
- BR-16: Batch jobs are retained for 90 days; detailed per-recipient status is available for 30 days.

---

## UC-006: Configure Provider with Failover

| Field | Value |
|-------|-------|
| **ID** | UC-006 |
| **Actor(s)** | System Administrator |
| **Trigger** | Administrator opens Provider Settings in the management console and adds or updates a provider configuration. |
| **Preconditions** | Administrator has system-admin role; provider API credentials are available; the provider type is supported by the platform. |
| **Postconditions** | Provider is active and included in routing decisions; failover chain is persisted; health probes are started for the new provider. |
| **Priority** | High |

**Main Flow:**
1. Administrator navigates to Settings > Providers > Add Provider.
2. Administrator selects the provider type (SendGrid, Twilio, FCM, etc.) and enters credentials (API key, account SID, etc.).
3. System validates credentials by performing a lightweight test call (e.g., send a system verification email to a platform-owned address or a dry-run SMS).
4. Administrator configures routing parameters: priority rank (1 = primary), weight percentage, channels supported, geographic regions.
5. Administrator enables failover and adds a secondary provider of the same channel type with rank 2.
6. Administrator configures failover trigger thresholds: error rate % and observation window (e.g., "fail over when error rate exceeds 5% in a 2-minute window").
7. Administrator configures recovery policy: gradual ramp-back percentages and hold time before full recovery.
8. Administrator saves configuration; system writes the provider record and failover policy.
9. Health probe scheduler begins polling the provider's status endpoint at the configured interval.
10. System emits a `provider.configured` audit event.

**Alternative Flows:**
- **AF-1 (Credential Rotation):** Existing provider credentials are rotated without changing routing configuration. Validation test is re-run before the new credentials become active.
- **AF-2 (Disable Provider):** Administrator marks a provider as inactive; it is immediately removed from routing decisions. In-flight messages are completed on the current provider; new messages skip it.

**Exception Flows:**
- **EF-1 (Credential Validation Failure):** Test call to provider returns an authentication error. Configuration is not saved; administrator is shown the provider error response.
- **EF-2 (Duplicate Priority Rank):** Two providers for the same channel have the same priority rank. System returns a conflict error and asks administrator to resolve the priority order.

**Business Rules:**
- BR-17: At least one active provider must be configured per channel before messages of that channel type can be dispatched.
- BR-18: Failover policies must define both a trigger threshold and a recovery policy; incomplete policies are not saved.
- BR-19: Provider credentials are encrypted at rest using the platform's secret management service; they are never returned in plain text via the API after initial save.

---

## UC-007: Process Opt-Out Request

| Field | Value |
|-------|-------|
| **ID** | UC-007 |
| **Actor(s)** | Recipient / End User, External Provider (via webhook), Developer / API User |
| **Trigger** | Recipient clicks an unsubscribe link, sends SMS STOP, or client calls `POST /v1/suppressions`. |
| **Preconditions** | Recipient is identifiable by email, phone, or contact ID; the opt-out scope (global, channel, or list-level) is determinable from the request. |
| **Postconditions** | Suppression record is created; all future sends to the affected recipient/channel/list are blocked; opt-out event is audit-logged; confirmation message is optionally sent. |
| **Priority** | High |

**Main Flow:**
1. Opt-out signal arrives via one of three paths: (a) unsubscribe link click in email, (b) SMS STOP keyword reply received by provider webhook, (c) direct API call from client.
2. System identifies the recipient from the signal: email address from link token, phone number from SMS sender, or contact ID from API.
3. System determines opt-out scope: global (all messages), channel-level (email only or SMS only), or list-level (specific subscription list).
4. System writes a suppression record: `{recipient_id, channel, scope, source, timestamp, request_id}`.
5. System updates the contact's subscription status for affected lists to `UNSUBSCRIBED`.
6. System invalidates any cached opt-in status for the recipient in the rate-limit and routing layers (TTL flush).
7. System publishes `contact.opted_out` event for downstream processing (CRM sync, analytics).
8. If the opt-out source was an email link, system redirects the recipient to a branded opt-out confirmation page.
9. System audit-logs the full opt-out event including source IP, timestamp, and signal type.

**Alternative Flows:**
- **AF-1 (Preference Centre Opt-Down):** Recipient uses the preference centre to opt out of specific channels or lists rather than globally. Each selection is processed as a list-level opt-out.
- **AF-2 (Re-subscribe):** If a previously opted-out recipient explicitly re-subscribes via the preference centre, the suppression record is soft-deleted and a `contact.resubscribed` event is published.

**Exception Flows:**
- **EF-1 (Unidentifiable Recipient):** The opt-out link token has expired or the phone number is not in the system. System logs the attempt and returns the confirmation page to avoid leaking information.
- **EF-2 (Concurrent Opt-Out):** Two opt-out signals for the same recipient arrive simultaneously. System uses optimistic locking; the second write is a no-op if a suppression record already exists.

**Business Rules:**
- BR-20: Opt-out requests must be honoured within 10 seconds of receipt for all future sends.
- BR-21: Suppression records are permanent unless explicitly rescinded by the recipient via re-subscribe; they are never deleted by operator action alone.
- BR-22: Unsubscribe links must be valid for at least 60 days after the message is delivered.
- BR-23: SMS STOP keyword processing applies globally across all lists for the given phone number on the given short/long code.

---

## UC-008: Schedule Campaign

| Field | Value |
|-------|-------|
| **ID** | UC-008 |
| **Actor(s)** | Marketing User |
| **Trigger** | Marketing User completes campaign configuration and clicks "Schedule" in the campaign builder. |
| **Preconditions** | Template is PUBLISHED; audience segment is defined and has at least one eligible contact; tenant has sufficient quota; `send_at` is at least 5 minutes in the future. |
| **Postconditions** | Campaign is persisted in `SCHEDULED` state; scheduling service holds the campaign; the batch is dispatched at the configured time. |
| **Priority** | High |

**Main Flow:**
1. Marketing User creates a campaign: name, description, template, audience segment, channel, scheduled send time, and timezone.
2. User configures sender details: from name, reply-to address, UTM tracking parameters.
3. System estimates audience size by evaluating the segment definition against the contact database (excluding suppressed contacts).
4. User reviews the estimated size and confirms scheduling.
5. System validates: template status, segment validity, quota sufficiency, and `send_at` being at least 5 minutes ahead.
6. System persists the campaign record with status `SCHEDULED`.
7. Returns campaign ID and estimated audience size to the UI.
8. At `send_at` time, the scheduler triggers batch job creation (UC-005) for the campaign.
9. Batch is executed as per UC-005 Batch Message Send flow.
10. Campaign status transitions: `SCHEDULED` → `RUNNING` → `COMPLETED`.
11. Post-send analytics begin populating: open rate, click rate, bounce rate, unsubscribe rate.

**Alternative Flows:**
- **AF-1 (Immediate Send):** User selects "Send Now"; `send_at` is set to the current time and batch execution begins immediately.
- **AF-2 (Recurring Campaign):** User configures a recurrence rule (daily, weekly). Scheduler creates new campaign runs at each interval. Each run snapshots the audience freshly.

**Exception Flows:**
- **EF-1 (Campaign Cancelled):** User cancels the scheduled campaign before dispatch. If batch has not yet been enqueued, status transitions to `CANCELLED`. In-progress chunks cannot be recalled.
- **EF-2 (Quota Exceeded at Run Time):** Tenant's remaining quota at run time is less than the batch size. Campaign transitions to `FAILED`; administrator is alerted.

**Business Rules:**
- BR-24: Campaign scheduling requires the `send_at` to be at least 5 minutes in the future to allow quota checks and pre-flight validation.
- BR-25: Audience snapshot is taken at schedule creation time; contacts added to the segment after scheduling are not included in the current run.

---

## UC-009: Process Bounce Record

| Field | Value |
|-------|-------|
| **ID** | UC-009 |
| **Actor(s)** | External Provider (via inbound webhook), Inbound Webhook Handler |
| **Trigger** | Provider posts a bounce notification to the platform's inbound webhook endpoint. |
| **Preconditions** | Provider is configured with the platform's webhook URL; the bounce contains a valid provider message ID that maps to a platform message record. |
| **Postconditions** | Message status is updated; hard bounces result in suppression; bounce rate metrics are updated; threshold alerts are evaluated. |
| **Priority** | High |

**Main Flow:**
1. Provider (e.g., SendGrid) posts a bounce event to `POST /v1/inbound/provider-callbacks/{provider_id}`.
2. Inbound Webhook Handler verifies the provider's webhook signature (HMAC or shared secret).
3. Handler maps the provider message ID to the platform message record using the provider message ID index.
4. Handler classifies the bounce type: `hard` (permanent, e.g., address does not exist) or `soft` (transient, e.g., mailbox full).
5. **If hard bounce:** System adds the recipient email to the suppression list with reason `HARD_BOUNCE`. Message status transitions to `FAILED`.
6. **If soft bounce:** System increments the soft bounce counter for the recipient. If threshold reached (configurable, e.g., 3 consecutive soft bounces), escalates to hard bounce treatment.
7. System updates delivery analytics: bounce rate for the campaign/batch, sender domain, and sending IP.
8. System publishes `message.bounced` event with classification metadata.
9. System evaluates bounce rate thresholds; if sender domain's bounce rate exceeds the alert threshold, publishes an `alert.bounce_threshold_exceeded` event.
10. Incident alert is triggered to platform administrators if bounce rate crosses critical threshold.

**Alternative Flows:**
- **AF-1 (Unknown Provider Message ID):** The provider message ID in the callback does not match any platform record (possible for messages sent outside the platform). Handler logs the unmatched event and discards.

**Exception Flows:**
- **EF-1 (Invalid Signature):** Webhook signature verification fails. Handler returns `HTTP 401` and logs a security event. No state changes are made.
- **EF-2 (Duplicate Callback):** Same bounce event is delivered twice (provider retry). Idempotency check using event ID prevents duplicate suppression writes.

**Business Rules:**
- BR-26: Hard bounce suppression is permanent; only the recipient can remove it via an explicit re-subscribe action.
- BR-27: Bounce callback processing must complete within 30 seconds of receipt to maintain provider webhook timeout compliance.
- BR-28: Sender domain bounce rate exceeding 2% triggers a platform alert; exceeding 5% triggers automatic pause of new sends from that domain until investigated.

---

## UC-010: View Delivery Analytics

| Field | Value |
|-------|-------|
| **ID** | UC-010 |
| **Actor(s)** | Marketing User, System Administrator |
| **Trigger** | User navigates to the Analytics dashboard in the management console. |
| **Preconditions** | User is authenticated and has the analytics viewer role; delivery events exist for the selected time range. |
| **Postconditions** | Dashboard displays up-to-date delivery metrics; user can drill down to message and recipient level; data can be exported. |
| **Priority** | High |

**Main Flow:**
1. User opens the Analytics dashboard and selects a date range, channel filter, and campaign/template filter.
2. System queries the analytics store (pre-aggregated metrics) for the selected dimensions.
3. Dashboard renders summary metrics: total sent, delivered rate, open rate (email), click rate (email), bounce rate, unsubscribe rate, complaint rate, failed rate.
4. User views time-series charts: delivery volume by hour/day, delivery rate trend, bounce rate trend.
5. User views top-performing templates and campaigns ranked by delivery rate and engagement rate.
6. User drills into a specific campaign to see per-recipient delivery status.
7. User views provider health summary: sent per provider, failure rate per provider.
8. User can export data (UC-024) or configure alert thresholds from the analytics view.

**Alternative Flows:**
- **AF-1 (Real-Time View):** User selects the "Live" mode to see delivery events streaming in the last 15 minutes with 30-second refresh.

**Exception Flows:**
- **EF-1 (No Data):** No messages were sent in the selected date range. Dashboard displays an empty state with a prompt to send a campaign.
- **EF-2 (Analytics Lag):** Analytics store may lag up to 5 minutes behind real-time delivery events. A staleness indicator is shown if lag exceeds 10 minutes.

**Business Rules:**
- BR-29: Analytics data is retained at full granularity for 90 days; summary aggregations are retained for 2 years.
- BR-30: Open and click tracking requires that the recipient's email client does not block tracking pixels; rates reflect only measured events, not total deliveries.

---

## UC-011: Manage Contact Preferences (Preference Centre)

| Field | Value |
|-------|-------|
| **ID** | UC-011 |
| **Actor(s)** | Recipient / End User |
| **Trigger** | Recipient clicks the "Manage Preferences" link in an email footer or navigates directly to the preference centre URL. |
| **Preconditions** | Preference centre is enabled for the tenant; the link contains a valid signed token identifying the contact; contact record exists in the platform. |
| **Postconditions** | Contact's subscription statuses are updated per the recipient's choices; suppression records are created or removed accordingly; a preference-change audit record is saved. |
| **Priority** | High |

**Main Flow:**
1. Recipient follows the "Manage Preferences" link which contains a signed JWT identifying the contact and tenant.
2. Platform validates the JWT signature and expiry (tokens valid for 90 days post-send).
3. Preference Centre UI loads, displaying the contact's current subscription status per list and channel.
4. Recipient reviews all subscription lists they are enrolled in (e.g., "Weekly Newsletter", "Account Alerts", "Promotional Offers").
5. Recipient toggles lists on/off or changes preferred channel (e.g., switch from email to SMS for account alerts).
6. Recipient optionally selects "Unsubscribe from all" for a global opt-out.
7. Recipient clicks "Save Preferences".
8. System processes each change: opt-outs write suppression records; opt-ins remove suppression records and update subscription status.
9. If double opt-in is required for a list, recipient receives a confirmation email; subscription activation is pending until the link in the confirmation email is clicked.
10. System displays a confirmation page acknowledging the saved preferences.
11. Preference-change events are published for CRM and analytics sync.

**Alternative Flows:**
- **AF-1 (Global Unsubscribe):** Recipient selects "Unsubscribe from all marketing". System creates a global suppression record covering all promotional lists for that contact. Transactional messages (e.g., password reset) remain unaffected.
- **AF-2 (Re-subscribe After Global Opt-Out):** Recipient navigates to the preference centre and explicitly re-subscribes to individual lists. System removes the relevant suppression records and re-activates subscriptions.

**Exception Flows:**
- **EF-1 (Expired Token):** JWT token has expired (> 90 days after send). System displays an "expired link" page with a form to enter the contact's email address and receive a fresh preference centre link.
- **EF-2 (Revoked Token):** Contact has unsubscribed globally; their tokens are revoked. Preference centre shows a minimal page confirming global opt-out status with option to re-subscribe.

**Business Rules:**
- BR-31: Transactional messages (password reset, account security, legal notices) are exempt from list-level opt-outs and can only be suppressed by hard-bouncing or an explicit global opt-out.
- BR-32: Preference centre tokens are single-audience scoped; a token from one tenant cannot access preferences for another tenant.
- BR-33: All preference changes are audit-logged with timestamp, source IP, and the specific changes made.

---

## Revision History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2025-01 | Platform Team | Initial detailed use case descriptions for UC-001 through UC-011 |
