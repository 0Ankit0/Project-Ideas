# Edge Cases: Distribution and Sharing — Survey and Feedback Platform

## Overview

This document covers edge cases and failure modes in the Survey Distribution and Sharing subsystem, including email campaigns, SMS distribution, embed widgets, shareable links, QR codes, and custom redirect configurations. Distribution is a high-risk area for compliance and reputation issues; failures here can have legal and deliverability consequences.

**Scope**: Email campaign delivery, SendGrid integration, embed widget (CORS), short-link generation, QR codes, SMS via Twilio, bounce management, and custom redirect validation.

**Edge Case IDs**: EC-DIST-001 through EC-DIST-008

---

## EC-DIST-001: Campaign Sent to Unsubscribed Contacts

| Field | Details |
|-------|---------|
| **Failure Mode** | Email campaign is dispatched to contacts who have previously unsubscribed, either because the unsubscribe status was not checked at send time, was cached stale, or a race condition occurred between an unsubscribe event and campaign dispatch. |
| **Impact** | **Critical** — CAN-SPAM and GDPR violations. Fines up to €20M or 4% global annual revenue (GDPR Art. 83). Immediate SendGrid account review and potential suspension. Loss of trust and domain reputation damage. Legal action from affected respondents. |
| **Detection** | Post-send audit: `SELECT COUNT(*) FROM campaign_deliveries cd JOIN contacts c ON cd.contact_id = c.id WHERE c.unsubscribed_at IS NOT NULL AND cd.campaign_id = :campaign_id`. Alert if count > 0. SendGrid webhook delivers `unsubscribe` events that create discrepancy alerts in CloudWatch `UnsubscribedEmailSent` custom metric. Alarm threshold: >0. |
| **Mitigation / Recovery** | 1. Immediately send a follow-up apology email to affected contacts with an easy one-click unsubscribe link. 2. File an internal incident report with timestamp, affected email count, campaign ID. 3. Check SendGrid spam reporting dashboard — if complaints filed, proactively notify SendGrid support. 4. Quarantine the campaign: `UPDATE campaigns SET status='failed', notes='Sent to unsubscribed contacts - incident INC-XXX' WHERE id=:campaign_id`. 5. Audit the contact import pipeline for the audience list to find how unsubscribed contacts were included. 6. If GDPR Art. 17 erasure requests follow, process within 30 days. 7. Review DPA (Data Processing Agreement) obligations with the workspace. |
| **Prevention** | 1. **Hard enforcement at DB layer**: Campaign send query always uses `WHERE unsubscribed_at IS NULL` — never rely on application-level filtering alone. 2. **Pre-send validation gate**: Before any campaign send task runs, run a COUNT query to detect unsubscribed contacts in the batch; abort if count > 0. 3. **Real-time unsubscribe sync**: SendGrid unsubscribe webhook is processed within 60 seconds and writes to `contacts.unsubscribed_at` immediately. 4. **Idempotent unsubscribe**: Contact unsubscribe requests are honoured globally across all audience lists in the workspace. 5. **Audit log**: Every campaign send logs the query used and the contact count to `audit_logs` before dispatch. |

### Testing Scenario
1. Create a contact and add to audience list.
2. Unsubscribe the contact via the unsubscribe endpoint.
3. Create a campaign targeting that audience list.
4. Trigger campaign send.
5. Verify the contact is excluded from the SendGrid batch (inspect Celery worker logs).
6. Verify `campaign_deliveries` table does not contain the unsubscribed contact.

---

## EC-DIST-002: SendGrid Daily Volume Limit Reached Mid-Campaign

| Field | Details |
|-------|---------|
| **Failure Mode** | A large email campaign (e.g., 50,000 contacts) is mid-send when the workspace's or platform's SendGrid daily sending limit is reached. SendGrid returns HTTP 429 or a custom quota error. Partially sent campaigns leave some contacts emailed and others not, creating an inconsistent state. |
| **Impact** | **High** — Campaign incompleteness: part of the audience received the survey while the rest did not. Inconsistent data collection. Creator trust impact. If using Free tier SendGrid (100 emails/day), any campaign >100 contacts will partially fail. |
| **Detection** | SendGrid API returns `{"errors": [{"message": "The from address does not match a verified Sender Identity"}]}` or HTTP 429 with `X-RateLimit-Remaining: 0`. Celery task catches `SendGridHTTPError` with status 429. CloudWatch custom metric `CampaignPartialSendFailures` alarm triggers at count > 0. Dead letter queue receives failed Celery tasks. |
| **Mitigation / Recovery** | 1. Celery task catches 429 error and pauses campaign: `UPDATE campaigns SET status='paused', notes='SendGrid limit reached at batch {n}'`. 2. Record the last successfully sent contact ID (`campaign_deliveries.last_contact_cursor`). 3. Send alert email to workspace admin: "Your campaign '{name}' has been paused. {n} of {total} contacts have been reached. Resume tomorrow when sending limits reset." 4. At limit reset (00:00 UTC): workspace admin can trigger "Resume Campaign" which sends to remaining contacts only. 5. The resume query uses: `SELECT contacts WHERE id NOT IN (SELECT contact_id FROM campaign_deliveries WHERE campaign_id=:id)`. |
| **Prevention** | 1. **Pre-send capacity check**: Before queuing campaign, estimate email volume and check available SendGrid quota via API (`GET /v3/user/credits`). Block if insufficient quota. 2. **Plan-based limits**: Enforce per-workspace daily email limits that stay below SendGrid tier limits: Free workspace: 500/day, Business: 50,000/day. 3. **Resumable campaign architecture**: All campaign sends are checkpoint-based — record delivery status per contact, never restart from beginning. 4. **SendGrid sub-account per high-volume workspace**: Enterprise workspaces get dedicated SendGrid sub-accounts. 5. **Rate-controlled batching**: Send in 500-contact batches with 1-second sleep between batches to avoid burst quota exhaustion. |

### Testing Scenario
1. Set up a campaign with 1,000 contacts.
2. Mock SendGrid to return 429 after 500 deliveries.
3. Verify campaign pauses at status='paused' with cursor recorded.
4. Restore mock to return 200.
5. Resume campaign and verify remaining 500 contacts are sent without duplicating the first 500.

---

## EC-DIST-003: Embed Widget CORS Failure

| Field | Details |
|-------|---------|
| **Failure Mode** | A customer embeds the survey widget on their website via the JavaScript snippet. The browser blocks the widget's API requests due to missing or incorrect CORS headers, causing the survey to fail to load or submit. This occurs when the embedding domain is not in the workspace's allowed-origins list, or when the API Gateway's CORS configuration is misconfigured. |
| **Impact** | **High** — Survey completely non-functional on the embedding site. Respondents see no survey or an empty iFrame. Zero response collection from that channel. Creator may be unaware until they check embed analytics. |
| **Detection** | Browser console error: `"Access to fetch at 'https://api.survey-platform.com/...' from origin 'https://customer.com' has been blocked by CORS policy"`. Widget JavaScript catches this and reports to our telemetry endpoint. CloudWatch metric `EmbedCORSFailure` alarm at count > 5 per workspace per hour. |
| **Mitigation / Recovery** | 1. Add the customer's domain to the workspace's allowed origins: `PUT /api/v1/workspaces/{id}/settings {allowed_origins: [..., "https://customer.com"]}`. 2. If misconfigured at API Gateway level, update CORS headers: `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`. 3. Advise customer to test with browser dev tools Network tab after fix. 4. Check if iframe `sandbox` attribute on customer's side is blocking requests (requires `allow-scripts allow-same-origin`). |
| **Prevention** | 1. **Domain validation at embed setup**: When creator copies the embed snippet, the UI prompts them to enter their target domain(s). These are stored in `workspace.settings.allowed_origins`. 2. **Wildcard subdomain support**: Support `*.customer.com` patterns in allowed origins for multi-subdomain setups. 3. **Pre-flight test**: After domain registration, the platform sends a test CORS request from its own backend to the target domain and warns if the domain appears to enforce frame-breaking. 4. **CSP compatibility check**: Warn if customer's Content-Security-Policy may block the widget. 5. **iFrame fallback**: Provide an iFrame embed alternative that is less susceptible to JavaScript CORS restrictions. 6. **CORS headers set at CloudFront level** (not just application): CloudFront response headers policy includes `Access-Control-Allow-Origin: {dynamic from allowlist}`. |

### Testing Scenario
1. Create workspace with allowed origin set to `https://example.com`.
2. Load embed widget from `https://other-domain.com` (different domain).
3. Verify browser CORS error in console.
4. Add `https://other-domain.com` to allowed origins.
5. Reload and verify survey loads and submits successfully.

---

## EC-DIST-004: Survey Short-Link Token Collision

| Field | Details |
|-------|---------|
| **Failure Mode** | Two surveys are assigned the same 8-character alphanumeric short-link token (slug). This can occur under high creation volume or with a poor entropy source. When a respondent follows the link, they may see the wrong survey. |
| **Impact** | **High** — Wrong survey delivered to respondents. Data collected for wrong survey. Creator confusion and trust loss. Potential compliance issue if sensitive surveys are misdirected. |
| **Detection** | PostgreSQL `UNIQUE` constraint on `surveys.slug` will raise `UniqueViolationError` on INSERT. Application catches this and retries with a new token (up to 5 attempts). If 5 attempts fail, a `SlugGenerationFailure` exception is logged to CloudWatch. Alert threshold: >1 per hour indicates entropy issue. |
| **Mitigation / Recovery** | 1. If slug collision is detected post-deployment (surveys already using same slug — edge case from a migration), identify the duplicate: `SELECT slug, COUNT(*) FROM surveys GROUP BY slug HAVING COUNT(*) > 1`. 2. Re-generate slug for the newer survey (by creation date): use longer slug (12 chars) and update all campaign links. 3. Notify affected survey creators via email with updated link. 4. Redirect old links via HTTP 301 to new URL using a migration table in Redis. |
| **Prevention** | 1. **PostgreSQL UNIQUE constraint** on `surveys.slug` as the primary guard. 2. **Slug generation with retry loop**: Use `secrets.token_urlsafe(6)` (8 chars) with up to 5 regeneration attempts on collision. 3. **Longer slugs for high-volume workspaces**: Enterprise workspaces get 12-character slugs. 4. **Slugification of survey title**: Prefer title-based slugs (e.g., "employee-survey-2024") over random tokens, with numeric suffix for deduplication. 5. **Monitor collision rate**: Track generation attempts per survey in application metrics. If average attempts > 1.5, increase token length. |

### Testing Scenario
1. Mock `secrets.token_urlsafe` to return a fixed value to force collision.
2. Create two surveys in the same workspace.
3. Verify the second survey gets a different slug (retry succeeded).
4. Mock to fail 5 times — verify `SlugGenerationFailure` exception is raised and 500 returned.

---

## EC-DIST-005: QR Code Points to Archived Survey

| Field | Details |
|-------|---------|
| **Failure Mode** | A QR code is generated and printed in physical materials (event banners, flyers, business cards). The survey it points to is later archived or deleted. Respondents scanning the QR code are directed to a non-existent or closed survey page. |
| **Impact** | **Medium** — Poor respondent experience. Data collection opportunity lost. Especially impactful for event surveys where QR codes are physically distributed and cannot be recalled. |
| **Detection** | Survey status check at link resolution time. When a respondent visits `/s/{slug}` and the survey status is `archived`, `closed`, or `deleted_at IS NOT NULL`, the platform returns a 410 Gone. CloudWatch logs count of QR accesses to archived surveys. Custom metric `ArchivedSurveyAccess` alarm if count > 10/day. |
| **Mitigation / Recovery** | 1. When a creator attempts to archive a survey that has active QR codes, display a warning: "This survey has an active QR code. Archiving will prevent new responses. Do you want to redirect to a new survey instead?" 2. QR Redirect feature: Allow creators to configure a replacement survey URL that the QR resolves to. Store in Redis: `SET qr:{slug}:redirect {new_slug}`. 3. For printed materials that cannot be recalled, provide a QR redirect override that can be updated without reprinting. |
| **Prevention** | 1. **QR redirect layer**: All QR codes point to `https://survey-platform.com/qr/{qr_code_id}` (our redirect service), not directly to the survey URL. The QR code ID resolves dynamically to the current target URL. 2. **Creator warning on archive**: Before archiving, show count of QR code scans in last 30 days as a warning. 3. **QR expiry option**: Allow creators to set QR code validity duration (e.g., "valid until end of event date"). 4. **Graceful survey closed page**: When survey is closed/archived, show a branded "This survey is no longer accepting responses. Thank you!" page instead of a 404. |

### Testing Scenario
1. Create survey and generate QR code.
2. Archive the survey.
3. Access the QR redirect URL.
4. Verify user sees graceful "Survey closed" page, not 404.
5. Set a redirect target and verify QR now resolves to new survey.

---

## EC-DIST-006: SMS Distribution to Invalid or Ported Numbers

| Field | Details |
|-------|---------|
| **Failure Mode** | Twilio SMS delivery fails for phone numbers that are disconnected (Twilio error 30003), invalid format (30007), or ported to a carrier that does not support the originating number type (e.g., short code vs. long code restriction). Campaign stats show high undelivered count. |
| **Impact** | **Medium** — Reduced reach for SMS campaigns. Twilio charges for attempted delivery regardless of success. High failure rates can trigger Twilio account review. Creators see low open rates and draw incorrect conclusions about audience engagement. |
| **Detection** | Twilio webhook delivers status callback to `/api/v1/webhooks/twilio/sms-status`. Error code 30003 (Unreachable) or 30006 (Landline) increments `contact.bounce_count`. CloudWatch metric `SMSDeliveryFailureRate` alarm if >15% of SMS batch returns errors. |
| **Mitigation / Recovery** | 1. Mark contacts with 2+ SMS delivery failures as `sms_undeliverable=true`. 2. Exclude `sms_undeliverable` contacts from future SMS campaigns. 3. Notify workspace admin in campaign report: "{n} messages were undeliverable. These contacts have been flagged." 4. For landline numbers (30006), suggest contact cleanup: offer CSV export of undeliverable contacts for admin to review. 5. Twilio 30003 is transient — retry once after 24h before flagging as undeliverable. |
| **Prevention** | 1. **Phone number validation at import**: Use libphonenumber to validate and normalize phone numbers to E.164 format during CSV import. Reject invalid formats before they reach the campaign. 2. **Twilio Lookup API**: For high-value campaigns (Enterprise tier), use Twilio Lookup to pre-validate phone type (mobile vs. landline) before sending. 3. **Configurable undeliverable threshold**: Auto-exclude contacts after N failures (default: 2). 4. **Number porting awareness**: Use A2P 10DLC registered numbers for US SMS to reduce filtering by carriers. 5. **Rate limit SMS sends**: Maximum 10 SMS/second per workspace to stay within Twilio rate limits. |

### Testing Scenario
1. Import contact list with mix of valid mobile, landline, and invalid numbers.
2. Send SMS campaign.
3. Simulate Twilio 30006 webhook for landline number.
4. Verify contact is flagged `sms_undeliverable=true`.
5. Create second campaign to same list — verify landline contact is excluded.

---

## EC-DIST-007: Email Bounce Rate Exceeds 5% Threshold

| Field | Details |
|-------|---------|
| **Failure Mode** | An email campaign experiences >5% hard bounce rate. SendGrid automatically suppresses the domain or triggers an account review, potentially suspending the shared sending IP pool, which affects ALL workspaces on the platform. |
| **Impact** | **Critical** — Platform-wide email deliverability impact. All workspaces' campaigns paused. SendGrid account review process can take 2-5 business days. Creator SLA breach. Potential domain blocklisting by major email providers (Gmail, Outlook). |
| **Detection** | SendGrid webhook sends `bounce` events in real time. CloudWatch metric `EmailHardBounceRate` calculated as `bounces / delivered × 100`. Alarm at 3% (warning), 5% (critical). PagerDuty alert to on-call and engineering lead. SendGrid sends email notification to platform admin account for bounce rate spikes. |
| **Mitigation / Recovery** | 1. Auto-pause ALL active campaigns when bounce rate > 5%: `UPDATE campaigns SET status='paused' WHERE status='sending'`. 2. Identify the problematic audience list: query highest bounce rate by campaign → trace to source audience list or contact import. 3. Run bounce cleanup: `UPDATE contacts SET hard_bounced=true, unsubscribed_at=NOW() WHERE email IN (SELECT email FROM bounce_log WHERE bounce_type='hard')`. 4. Contact SendGrid support proactively with explanation and remediation plan. 5. Request IP warmup on dedicated IP (if not already on one). 6. Resume campaigns only after bounce rate calculated on cleaned list is below 2%. |
| **Prevention** | 1. **Double opt-in for new audiences**: Newly imported contacts require email verification (double opt-in) before they can be used in campaigns. 2. **Bounce suppression at import**: Cross-check new imports against global bounce suppression list before saving. 3. **Email age validation**: Warn creators about audience lists that haven't been mailed in >12 months (high staleness = high bounce risk). 4. **Campaign preview bounce risk score**: Before sending, calculate estimated bounce risk based on list freshness and previous bounce history. Block if risk score > medium. 5. **Dedicated sending domains**: Each workspace gets a subdomain (e.g., `mail.{workspace}.survey-platform.com`) for campaign emails, isolating bounce reputation. |

### Testing Scenario
1. Import a contact list with 60% invalid email addresses.
2. Send campaign.
3. Simulate bounce webhooks from SendGrid for invalid addresses.
4. Verify campaign auto-pauses at 5% bounce threshold.
5. Verify affected contacts are flagged hard_bounced and excluded from future sends.

---

## EC-DIST-008: Open Redirect via Custom Thank-You Page URL

| Field | Details |
|-------|---------|
| **Failure Mode** | A malicious survey creator (or compromised account) configures a custom post-submission redirect URL pointing to a phishing site, malware download, or social engineering page. Respondents who complete the survey are redirected to the malicious destination. |
| **Impact** | **Critical** — Security: Respondents (often employees or customers of the workspace's clients) are redirected to malicious sites. Platform reputation damage. Potential phishing liability. Browser security tools may blocklist the platform domain if it regularly redirects to malicious sites. Regulatory implications if respondent data is subsequently harvested by the redirect target. |
| **Detection** | URL validation at save time: Pydantic validator checks redirect URL. Safe browsing API check (Google Safe Browsing lookup): `POST https://safebrowsing.googleapis.com/v4/threatMatches:find`. CloudWatch alarm if any `UnsafeRedirectBlocked` event logged. Security team review of flagged URLs. |
| **Mitigation / Recovery** | 1. Immediately disable the survey: `UPDATE surveys SET status='closed', settings=jsonb_set(settings, '{redirect_url}', 'null')`. 2. Notify all respondents who submitted and were redirected (if identifiable from response_sessions). 3. File abuse report with Google Safe Browsing if URL is not already flagged. 4. Suspend workspace pending investigation if malicious intent is confirmed. 5. Audit all other surveys in the workspace for similar redirect configurations. 6. Report to relevant authorities if phishing targeting financial data. |
| **Prevention** | 1. **URL allowlist by protocol**: Only `https://` URLs accepted; `javascript:`, `data:`, `http://` rejected at Pydantic validation layer. 2. **Domain blocklist**: Maintain list of known malicious/phishing domains; check redirect URL against blocklist on save. 3. **Google Safe Browsing API check**: Async check against Safe Browsing Lookup API on every redirect URL save; reject and alert if threat found. 4. **Domain ownership verification**: Optionally require creators to add a verification meta tag to the target domain (DNS TXT record) for custom redirects — prevents arbitrary external redirects. 5. **Rate limit redirect URL changes**: Maximum 5 redirect URL changes per survey per 24 hours to detect bulk abuse. 6. **Intermediate redirect page**: Instead of direct JS redirect, show a branded "You're being redirected to {domain}" page with 3-second delay and cancel option, so respondents can abort suspicious redirects. |

### Testing Scenario
1. Attempt to set redirect URL to `http://evil.example.com`.
2. Verify 422 error: HTTP protocol rejected.
3. Attempt to set redirect URL to a Google Safe Browsing-flagged URL (use test URL from Google's documentation).
4. Verify the URL is blocked and `UnsafeRedirectBlocked` event is logged.
5. Set valid `https://` URL — verify it saves successfully.

---

## Distribution Compliance Checklist

| Standard | Requirement | Implementation | Status |
|----------|------------|----------------|--------|
| **CAN-SPAM (US)** | Physical address in commercial emails | Platform footer includes workspace physical address or platform address | ✅ Enforced |
| **CAN-SPAM** | One-click unsubscribe mechanism | `List-Unsubscribe-Post` header + unsubscribe link in every email | ✅ Enforced |
| **CAN-SPAM** | No deceptive subject lines | AI content moderation flag on subject lines with deceptive patterns | ⚠️ Advisory |
| **CASL (Canada)** | Express consent required | Double opt-in for Canadian contacts (detected by phone country code +1 CA) | ✅ Enforced |
| **CASL** | Identification of sender | From name and email validated and displayed | ✅ Enforced |
| **GDPR Art. 6 (EU)** | Lawful basis for processing | Consent recorded at contact import with source and timestamp | ✅ Enforced |
| **GDPR Art. 17** | Right to erasure | Unsubscribe + contact deletion removes from all campaigns | ✅ Enforced |
| **GDPR Art. 20** | Data portability | Contact export available as CSV from audience management | ✅ Enforced |
| **PECR (UK)** | Opt-in for electronic marketing | Required for email campaigns to individuals; legitimate interest allowed for B2B | ⚠️ Workspace responsibility |
| **TCPA (US SMS)** | Prior express written consent for SMS | Consent checkbox required before adding contacts to SMS lists | ✅ Enforced |

---

## Operational Policy Addendum

### Response Data Privacy Policies

Distribution channels (email, SMS) require explicit consent from each contact before sending survey invitations. GDPR lawful basis for campaign distribution is consent (Article 6(1)(a)) or legitimate interests (Article 6(1)(f)) — workspace administrators must select the applicable basis for each campaign. Respondent email addresses collected via email campaigns are associated with response sessions but are not shared with other workspaces. Contact metadata (email, name, custom fields) imported via CSV is processed exclusively for survey distribution purposes and is not used for cross-workspace analytics or advertising.

### Survey Distribution Policies

All email campaigns must originate from a verified sender domain with SPF and DKIM records configured. Unsubscribe requests are honoured globally within 60 seconds of processing. The platform enforces CAN-SPAM, CASL, and GDPR compliance at the infrastructure level. Bounce rates are monitored hourly; campaigns auto-pause at 5% bounce rate. SMS campaigns require prior opt-in consent stored in the contact record. Bulk SMS sends are rate-limited to 10 messages/second per workspace.

### Analytics and Retention Policies

Campaign delivery analytics (open rates, click rates, completion rates, bounce counts) are retained for 24 months and then archived. Email engagement events (open, click) from SendGrid webhooks are stored in the campaigns table and in a separate `campaign_events` table for detailed analysis. Contact-level engagement history is retained per the workspace's subscription data retention period. Campaign analytics aggregations are retained indefinitely.

### System Availability Policies

Distribution service availability target: 99.5% (planned maintenance windows excluded). Email delivery is handled asynchronously via Celery workers, meaning API availability is decoupled from actual delivery. Campaign sends are retried on Celery worker failure (max 3 retries with exponential backoff). SendGrid outage fallback: Queue campaigns with status='pending' and retry when SendGrid API health check passes. SMS delivery uses Twilio's global network with 99.95% uptime SLA. QR code redirect service is served from CloudFront edge with 99.9% SLA.
