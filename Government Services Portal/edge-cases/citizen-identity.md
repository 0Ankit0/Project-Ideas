# Edge Cases: Citizen Identity & Authentication — Government Services Portal

## Overview

This document covers **8 edge cases** in the Citizen Identity & Authentication domain. Authentication is the entry gate to all government services. Failures here can block citizens from accessing entitled services, compromise citizen PII, or create fraudulent dual identities in the system. Given that the portal relies on NASC (National Identity Management Centre) NID OTP, Nepal Document Wallet (NDW) OAuth, and government-issued JWT sessions, edge cases in this domain intersect with legal obligations under the NID Act 2016 and the DPDP Act 2023.

---

## EC-IDENTITY-001: NID OTP Delivery Failure

**Failure Mode:**
The portal initiates an NID OTP request by calling the NASC (National Identity Management Centre) Authentication API (`/auth/otp`) with the citizen's NID number. The NASC (National Identity Management Centre) API either returns an HTTP 5xx error, takes longer than the configured 10-second timeout, or returns a success acknowledgement but the downstream SMS carrier (BSNL/Airtel) fails to deliver the OTP to the citizen's mobile. The citizen waits on the OTP screen, the OTP never arrives, and the frontend timer expires. The citizen is left with no path forward.

**Impact:**
- **Severity: High**
- Citizens are completely blocked from logging in and accessing any government service. Urgency is acute for time-sensitive services such as income certificate applications for scholarship deadlines, caste certificate applications for job applications, or property mutation deadline compliance.
- If the NASC (National Identity Management Centre) API is timing out system-wide, all citizen authentication is unavailable simultaneously — a complete authentication blackout.
- Citizens who repeatedly request OTPs (attempting to work around the issue) may trigger NASC (National Identity Management Centre)'s own rate limits, making the situation worse.
- High call volume to the citizen helpline during NASC (National Identity Management Centre) outages increases operational support cost.

**Detection:**
- **CloudWatch Alarm:** `UIDAPIResponseTime_P99_High` — triggers when the P99 latency of outbound NASC (National Identity Management Centre) API calls exceeds 8 seconds over a 5-minute window.
- **CloudWatch Alarm:** `UIDAPIErrorRate_High` — triggers when 5xx or timeout error rate from NASC (National Identity Management Centre) exceeds 5% over a 3-minute window.
- **CloudWatch Metric:** `OTPSMSDeliveryFailure_Count` — increment this counter whenever an OTP is sent to NASC (National Identity Management Centre) successfully but no delivery receipt is received within 90 seconds from the Nepal Telecom / Sparrow SMS gateway.
- **Structured Log:** Every NASC (National Identity Management Centre) API call logs `uidai_response_code`, `uidai_response_time_ms`, and `sms_delivery_status` to CloudWatch Logs. Log Insights alert queries run every 5 minutes.
- **Synthetic Canary:** A CloudWatch Synthetics canary hits a test endpoint every 2 minutes to check NASC (National Identity Management Centre) connectivity from within the VPC; fires `NASC (National Identity Management Centre)_Connectivity_Canary_Failed` alarm if connectivity drops.
- **Status Page Integration:** NASC (National Identity Management Centre) publishes a status page; a Lambda function polls it every 5 minutes and publishes a metric `NASC (National Identity Management Centre)_External_Status` (1=OK, 0=degraded).

**Mitigation/Recovery:**
1. **Immediate Action — Fallback Auth Method:** When NASC (National Identity Management Centre) OTP fails (after 1 automatic retry with 3-second backoff), the frontend immediately presents the citizen with an alternative: "OTP via Email" (to the registered email address) or re-attempt in 60 seconds. This fallback is configured in `AADHAAR_OTP_FALLBACK_ENABLED=True` in Django settings.
2. **Retry Logic:** The NASC (National Identity Management Centre) API client uses `tenacity` with exponential backoff: 3 attempts, delays of 2s, 4s, 8s. The third failure triggers the fallback auth flow.
3. **Graceful Frontend Message:** Instead of a generic error, the citizen sees: "NID OTP service is experiencing temporary delays. You can receive an OTP on your registered email or try again in 2 minutes." The UI shows a countdown timer.
4. **Session Preservation:** If the citizen was mid-form and needs to re-authenticate (session expired), all form data is preserved in server-side Redis draft (keyed by session cookie + draft ID) before triggering re-auth.
5. **Incident Response:** SRE on call receives PagerDuty alert when `UIDAPIErrorRate_High` fires. Runbook `OPS-RUNBOOK-003` is followed: check NASC (National Identity Management Centre) status page, check VPC DNS resolution, escalate to NASC (National Identity Management Centre) AUA partner contact if systemic.
6. **Communication:** During prolonged NASC (National Identity Management Centre) outages (>15 minutes), the portal's status banner automatically activates, displaying: "NID authentication is temporarily unavailable. Email OTP is available as an alternative."

**Prevention:**
- **Circuit Breaker:** The `uidai_client` Django service wraps all NASC (National Identity Management Centre) API calls in a `circuitbreaker` decorator (`pybreaker` library). After 5 consecutive failures, the circuit opens and immediately routes new auth requests to the email OTP fallback without attempting NASC (National Identity Management Centre). Circuit resets after 60 seconds.
- **Dedicated Connection Pool:** The NASC (National Identity Management Centre) HTTP client uses a dedicated `requests.Session` with connection pooling, separate from other external API connections, to avoid noisy-neighbor latency.
- **Pre-Configured Fallback Flow:** The email OTP fallback is not an afterthought — it is a first-class authentication method with its own rate limiting (5 OTP requests per hour per citizen), expiry (10 minutes), and audit logging. It is live and tested in production at all times.
- **NASC (National Identity Management Centre) SLA Monitoring:** A separate CloudWatch dashboard tracks NASC (National Identity Management Centre) API availability over rolling 7-day and 30-day windows, used in quarterly SLA reviews with the NASC (National Identity Management Centre) AUA helpdesk.
- **Chaos Testing:** Monthly chaos test simulates NASC (National Identity Management Centre) API 100% unavailability for 5 minutes; fallback flow is validated end-to-end.

---

## EC-IDENTITY-002: Duplicate NID Registration Attempt

**Failure Mode:**
Two citizen accounts attempt to register with or link to the same NID number. This can happen in several scenarios: (a) a citizen creates two portal accounts with different email addresses, (b) a fraudster knowingly tries to register using someone else's NID number after obtaining their OTP (SIM swap fraud), (c) a race condition during concurrent registration requests for the same NID number. Without enforcement, two accounts share one NID identity, creating duplicate records and enabling one citizen to access another's application history.

**Impact:**
- **Severity: Critical**
- A citizen linked to another's NID can view, modify, or withdraw that person's applications — a direct privacy and legal violation under the NID Act 2016 and DPDP Act 2023.
- In a fraud scenario, an attacker with a victim's NID number and intercepted OTP can register a portal account, take over the citizen's identity on the portal, and receive government benefits intended for the victim.
- Duplicate records cause downstream data reconciliation failures in integration with PFMS (Public Financial Management System) and province department ledgers.
- Regulatory audit findings for non-compliance with NID data security standards could result in portal shutdown by NASC (National Identity Management Centre).

**Detection:**
- **Database Constraint:** A `UNIQUE` constraint on `citizens.aadhaar_hash` (SHA-256 HMAC with server-side secret, never stored in plaintext) ensures the database enforces uniqueness at storage level. Any duplicate triggers an `IntegrityError`.
- **Application Log Alert:** `IntegrityError` on `aadhaar_hash` unique constraint is logged with severity `CRITICAL` and triggers a CloudWatch Log Insights alert within 1 minute.
- **Concurrent Registration Detection:** A Redis lock (`AADHAAR_REG_LOCK:<aadhaar_hash>`) is acquired for 30 seconds during the registration flow. If a second request attempts to acquire the same lock, it is rejected with HTTP 409 and logged as a `DUPLICATE_REGISTRATION_ATTEMPT` event.
- **Security Event Stream:** All duplicate registration attempts are published to an SNS topic `SecurityEvents` which feeds both a SIEM system and the security team's Slack alert channel.
- **Daily Reconciliation:** A scheduled Celery task runs nightly to scan for any accounts sharing the same `aadhaar_hash` — a safety net for any race conditions that bypassed application-level checks.

**Mitigation/Recovery:**
1. **Immediate Rejection:** The registration API returns HTTP 409 Conflict with the message: "An account is already registered with this NID number. If you believe this is an error, please contact support." No information about the existing account is disclosed.
2. **Account Recovery Flow:** The citizen is offered a "Recover My Account" option that sends an OTP to the NID-linked mobile to regain access to the existing account. New account creation is blocked until the conflict is resolved.
3. **Fraud Investigation:** If the existing account was NOT created by the legitimate owner (verified by comparing registration device fingerprint, IP geolocation, and registration timestamp), a fraud case is automatically raised in the Security Operations dashboard and the duplicate account is frozen pending review.
4. **Duplicate Record Cleanup:** In the rare case a duplicate slips through due to a timing bug, the `aadhaar_dedup_cleanup` management command merges the duplicate records (keeping the older account), preserving all applications, then deletes the newer account and notifies both associated email addresses.
5. **Notification:** The legitimate citizen's registered mobile receives an SMS: "A new registration was attempted using your NID on [portal]. If this was not you, call [helpline]."

**Prevention:**
- **HMAC-Hashed Storage:** NID numbers are never stored in plaintext. Only a HMAC-SHA256 hash with a KMS-managed key is stored, satisfying NASC (National Identity Management Centre) data storage guidelines. The hash is unique per portal deployment.
- **Database Unique Constraint:** Enforced at DB level as the last line of defense, independent of application logic.
- **Distributed Lock on Registration:** Redis-based lock prevents race conditions in a horizontally scaled environment with multiple ECS tasks.
- **NID OTP Verification Required:** Linking an NID to a portal account requires successful NASC (National Identity Management Centre) OTP verification — the OTP is sent only to the NID-linked mobile, making it infeasible for an attacker who does not control the victim's SIM.
- **Monitoring:** Daily automated reconciliation job, with alerts on any non-zero count of duplicate `aadhaar_hash` values.

---

## EC-IDENTITY-003: NID Number Mismatch with Entered Details

**Failure Mode:**
The citizen completes NASC (National Identity Management Centre) OTP verification successfully (NASC (National Identity Management Centre) authenticates the OTP), but when the portal retrieves the citizen's demographic data from the NASC (National Identity Management Centre) KYC response, the name and/or date of birth returned by NASC (National Identity Management Centre) does not match what the citizen entered in the registration form. For example, the NASC (National Identity Management Centre) record shows "Ramesh Kumar Verma" but the citizen entered "Ramesh Verma" (a common abbreviated form). Or the DOB differs by a year due to a historical data entry error in NASC (National Identity Management Centre)'s records.

**Impact:**
- **Severity: High**
- Citizens who have incorrect or abbreviated names in NASC (National Identity Management Centre) cannot complete identity verification, blocking them from all services that require eKYC.
- Citizens with discrepancies between their NID data and their formal name (as used in educational certificates, property documents) face legal complications if the portal name is propagated to issued certificates.
- The portal cannot reject citizens for minor name variations (nicknames, abbreviated names) without generating massive support volume and exclusion of legitimate citizens.
- If mismatches are not handled gracefully, a citizen with an old NID card entry error is permanently blocked with no recourse.

**Detection:**
- **Application Metric:** `NIDDetailsMismatch_Count` — published to CloudWatch every time a demographic mismatch is detected post-OTP verification.
- **Structured Log:** Log each mismatch event with fields `mismatch_type` (name/dob/address), `levenshtein_distance` (for name comparisons), and `citizen_id` (without logging the actual names to avoid PII in logs).
- **Alert Threshold:** If `NIDDetailsMismatch_Count` exceeds 50 per hour, an alert fires to the product team — may indicate a systemic NASC (National Identity Management Centre) data quality issue or a bug in the comparison logic.
- **User Support Tickets:** Mismatch events automatically create a support ticket in the citizen's account with a pre-filled explanation and guidance.

**Mitigation/Recovery:**
1. **Fuzzy Name Matching:** The portal applies fuzzy string matching (Jaro-Winkler similarity score ≥ 0.90) to compare the citizen-entered name with the NASC (National Identity Management Centre)-returned name, accounting for common abbreviations, middle name omissions, and transliteration differences. If the score meets the threshold, the match is accepted and the NASC (National Identity Management Centre)-returned name is used as the canonical name.
2. **Name Override with Attestation:** If fuzzy matching fails but OTP verification succeeded, the citizen is shown both names (their entered name and the NASC (National Identity Management Centre)-returned name) and asked to confirm: "Your NID records show your name as [NASC (National Identity Management Centre) name]. Would you like to use this as your registered name?" This creates an audit record of the citizen's explicit confirmation.
3. **DOB Tolerance:** For DOB mismatches of ±1 year (common due to historical age rounding in rural NID enrollment), the portal flags the account for manual KYC review but does not block the citizen. A support officer reviews the discrepancy within 2 business days.
4. **NASC (National Identity Management Centre) Data Correction Guidance:** Citizens with significant mismatches are provided a direct link to the NASC (National Identity Management Centre) NID Update portal (ssup.uidai.gov.in) with instructions to correct their NID details before retrying.
5. **Temporary Manual KYC Path:** For urgent cases (verified by support officer via video KYC), a manual identity verification can be performed that bypasses the NID name comparison while flagging the account for a 30-day review period.

**Prevention:**
- **Normalized Name Storage:** Store both the citizen-entered name and the NASC (National Identity Management Centre)-returned name in the citizen profile, clearly labeled, rather than forcing a single canonical field at registration time.
- **Pre-Registration Guidance:** The registration form includes a note: "Please ensure your name matches your NID card exactly, including middle names. Minor variations will be automatically matched."
- **Localization Testing:** Automated test suite includes name comparison tests for common Nepali name patterns — abbreviated names, father's name inclusion, initials-only first names, transliteration variants.

---

## EC-IDENTITY-004: Expired JWT Token Mid-Session

**Failure Mode:**
A citizen opens a complex application form (e.g., a building construction permit that has 8 sections and 15 required document uploads) and spends 45 minutes filling it in. The portal's JWT access token has a 30-minute expiry. The JWT silently expires while the citizen is on section 6. When the citizen clicks "Save & Continue" or "Submit," the API returns HTTP 401 Unauthorized. The frontend either crashes (if unhandled), shows a generic error, or worst — redirects to login without saving the in-progress form data. The citizen loses all entered data.

**Impact:**
- **Severity: High**
- Citizens lose significant time investment — a 45-minute form fill for a building permit is not unusual.
- Long-form applications for business licenses, social welfare schemes, or construction permits have complex data that is difficult to re-enter exactly as before.
- Citizens who lose data may not retry, abandoning legitimate applications and reducing service delivery effectiveness.
- If the form was in the final stages before document upload, document references may already be stored in S3, creating orphaned S3 objects.

**Detection:**
- **Frontend Detection:** The Next.js API client intercepts every API response with status 401 and checks whether it is a token expiry (by inspecting the `WWW-Authenticate: Bearer error="expired"` header).
- **Background Token Monitoring:** A React context hook (`useTokenLifecycle`) checks the JWT `exp` claim every 60 seconds. When remaining lifetime drops below 5 minutes, it attempts a background silent refresh.
- **CloudWatch Metric:** `JWT_RefreshFailure_Rate` — published when a silent refresh attempt returns 401/403 (refresh token also expired or revoked).
- **Session Duration Anomaly:** Log and alert when a session's active duration exceeds 2× the JWT access token lifetime without a refresh — indicates the silent refresh mechanism may be broken.

**Mitigation/Recovery:**
1. **Silent Refresh Token:** The JWT authentication system issues both an access token (30-minute expiry) and a refresh token (8-hour expiry, stored in an HttpOnly Secure SameSite=Strict cookie, NOT in localStorage). The frontend React context calls `POST /api/v1/auth/token/refresh/` in the background when the access token has less than 5 minutes remaining. The user is never interrupted.
2. **Pre-Submission Draft Save:** Every form implements auto-save to the server every 60 seconds using debounced API calls (`PATCH /api/v1/applications/{draft_id}/draft/`). The draft is server-side (stored in PostgreSQL/Redis), not browser-local-storage-only, so it survives browser refreshes and session changes.
3. **Graceful 401 Handling:** If a silent refresh fails (both tokens expired), the frontend: (a) triggers a final auto-save with whatever data is in the form province (using the last valid token if it can still be sent), (b) stores the form province in sessionStorage as a fallback, (c) redirects to the login page with a query parameter `?next=/applications/{draft_id}/continue`, (d) after re-login, redirects the citizen back to their in-progress form with all data restored.
4. **User Notification:** When silent refresh fails and re-login is required, the toast notification reads: "Your session has expired. Your progress has been saved. Please log in to continue."
5. **Draft Retention:** Server-side drafts are retained for 30 days. Citizens who return after a session lapse find their application exactly where they left it.

**Prevention:**
- **Refresh Token in HttpOnly Cookie:** Refresh tokens are never in localStorage (mitigates XSS theft). The `token/refresh/` endpoint validates the cookie and issues a new access token.
- **Sliding Window Drafts:** Every auto-save extends the draft's TTL in Redis by 30 minutes, ensuring that actively-used drafts are never evicted.
- **Token Lifetime Configuration:** Access token lifetime (30 minutes) and refresh token lifetime (8 hours) are environment variables (`JWT_ACCESS_TOKEN_LIFETIME`, `JWT_REFRESH_TOKEN_LIFETIME`) to allow adjustment without code deployments.
- **Load Test for Long Sessions:** Performance tests simulate sessions lasting 2 hours with periodic API calls to validate that token refresh works correctly throughout.

---

## EC-IDENTITY-005: Nepal Document Wallet (NDW) OAuth Token Revocation

**Failure Mode:**
A citizen has connected their Nepal Document Wallet (NDW) account to the portal during registration, granting the portal an OAuth access token and refresh token for retrieving verified documents. Later, the citizen visits Nepal Document Wallet (NDW) directly and revokes the portal's OAuth access from the Nepal Document Wallet (NDW) "Connected Apps" settings. The portal's stored Nepal Document Wallet (NDW) refresh token is now invalid. The next time the citizen (or a background job) attempts to fetch a document from Nepal Document Wallet (NDW), the API returns HTTP 401 or 403. Worse — if a Celery background task is attempting to pull documents for an auto-fill operation, it may silently fail and leave the application in a broken province.

**Impact:**
- **Severity: High**
- Auto-document-fetch operations for application forms break silently, leaving application fields unpopulated without the citizen understanding why.
- Applications that depend on Nepal Document Wallet (NDW) document verification (driving license, class X marksheet) cannot proceed without the citizen manually re-uploading documents.
- If the background task does not handle the error gracefully and retries indefinitely, it consumes Celery worker capacity.
- Batch document verification jobs that include a revoked-token citizen's application will fail partially, potentially causing inconsistent application statuses.

**Detection:**
- **Nepal Document Wallet (NDW) API 401/403 Monitoring:** The Nepal Document Wallet (NDW) API client logs all HTTP 4xx responses. A CloudWatch Log Insights alert fires when the count of 401/403 responses from Nepal Document Wallet (NDW) exceeds 10 per 5-minute window.
- **Celery Task Failure Monitoring:** Celery task failure counts for `fetch_digilocker_document` are published to CloudWatch. An alert fires if this task's failure rate exceeds 5% in a 15-minute window.
- **Token Validity Check:** A daily Celery beat task (`verify_digilocker_tokens`) attempts to refresh all stored Nepal Document Wallet (NDW) tokens and flags any that return 401, updating the `digilocker_connection_status` field on the citizen profile to `REVOKED`.

**Mitigation/Recovery:**
1. **Detect and Mark Revocation:** When a Nepal Document Wallet (NDW) API call returns 401 with error `invalid_token` or `access_denied`, the Nepal Document Wallet (NDW) client catches this, updates the citizen's `digilocker_connection_status` to `REVOKED`, and does NOT retry.
2. **Citizen Notification:** The citizen's dashboard shows a persistent banner: "Your Nepal Document Wallet (NDW) connection has been revoked. Documents that were being fetched automatically are unavailable. Please reconnect Nepal Document Wallet (NDW) or upload documents manually." An email notification is also sent.
3. **Manual Upload Fallback:** All application form fields that were configured for Nepal Document Wallet (NDW) auto-fill gracefully fall back to manual file upload if the connection is revoked. No form fields are left silently empty.
4. **Re-Connect Flow:** The portal provides a single-click "Reconnect Nepal Document Wallet (NDW)" button that initiates the OAuth authorization code flow again, requesting the same scopes. Existing application drafts retain previously-fetched document data if already stored.
5. **Background Task Cleanup:** If a `fetch_digilocker_document` Celery task encounters a revocation error, it marks the task result as `SKIPPED_REVOKED` (not `FAILED`) to avoid polluting failure metrics, and updates the application's document status field accordingly.

**Prevention:**
- **Token Validity Pre-check:** Before any Nepal Document Wallet (NDW) document fetch (both interactive and background), a lightweight token validation step checks the token's expiry claim. If the access token is near expiry, it attempts a token refresh first.
- **Webhook for Revocation (if available):** If Nepal Document Wallet (NDW)'s API exposes a webhook for revocation events, register it to receive real-time notification rather than relying on detection-at-use.
- **Graceful Degradation Design:** No application workflow has a hard dependency on Nepal Document Wallet (NDW) — every Nepal Document Wallet (NDW) document type has a manual upload alternative path, always tested and always available.
- **30-Day Token Refresh Heartbeat:** Even if a citizen has not visited the portal, a background task refreshes Nepal Document Wallet (NDW) tokens every 7 days to prevent gradual expiry of idle tokens.

---

## EC-IDENTITY-006: Biometric Authentication Hardware Failure

**Failure Mode:**
At a government service kiosk (Common Service Centre or government office), the biometric fingerprint scanner becomes unresponsive during a citizen authentication session. This can happen due to USB disconnect, driver crash, Windows service stop, or hardware damage. The kiosk-side software (a Chromium-based frontend with a native biometric bridge process) sends a fingerprint capture request and receives no response or an error from the bridge. The citizen has placed their finger on the scanner but the authentication never progresses.

**Impact:**
- **Severity: High**
- Citizens visiting a physical kiosk often lack digital access at home and depend entirely on kiosk authentication. A kiosk biometric failure makes the service completely inaccessible to this demographic — exactly the segment the kiosk was designed to serve.
- Kiosk failures during peak hours (morning of deadline days) create queues and citizen distress, often escalating to complaints against the service delivery mechanism.
- Kiosk operators may attempt workarounds (bypassing auth) that create security vulnerabilities.
- NASC (National Identity Management Centre)-mandated biometric authentication for NID services requires certified biometric hardware — failure cannot simply be bypassed.

**Detection:**
- **Kiosk Heartbeat:** Each kiosk runs a local agent that publishes a heartbeat metric to CloudWatch every 60 seconds, including biometric device status (`BIO_DEVICE_STATUS`: `OK`, `ERROR`, `DISCONNECTED`).
- **CloudWatch Alarm:** `Kiosk_BioDevice_Error` — triggers when a kiosk reports non-OK biometric status for more than 2 consecutive minutes.
- **Failed Authentication Attempt Log:** When the biometric bridge returns error code `DEVICE_NOT_FOUND` or `CAPTURE_TIMEOUT`, the event is logged with kiosk ID, timestamp, and citizen session ID.
- **Kiosk Dashboard:** A real-time operations dashboard shows all kiosks and their current biometric device status, visible to the district-level kiosk coordinator.

**Mitigation/Recovery:**
1. **OTP Fallback Authentication:** The kiosk frontend automatically offers NID OTP authentication as a fallback when biometric capture fails after 2 attempts. The citizen can receive OTP on their NID-linked mobile and authenticate via OTP instead.
2. **Kiosk Operator Override (Supervised):** With a kiosk supervisor's credential (a second-factor token), the kiosk operator can enable a 15-minute "supervised session" where the citizen's identity is verified by the operator visually checking a physical government ID, logged with the supervisor's digital signature.
3. **Hardware Restart Procedure:** The kiosk displays a "Biometric device error" message to the citizen along with an instruction for the operator to reconnect the scanner. A 60-second reconnect-and-retry cycle is initiated automatically.
4. **Incident Ticket Creation:** The kiosk agent automatically creates a support ticket in the asset management system with the kiosk ID, device model, and error code. The district IT coordinator is notified via SMS and email.
5. **Citizen Appointment Preservation:** If the citizen had a scheduled appointment for a kiosk service, the failed biometric authentication does not consume the appointment slot. The appointment is marked `BIOMETRIC_FAILURE` and the citizen is offered a same-day rescheduling option.

**Prevention:**
- **Certified Hardware List:** Only NASC (National Identity Management Centre)-certified biometric devices from the approved vendor list are deployed, reducing driver and compatibility issues.
- **Daily Hardware Self-Test:** Each kiosk runs an automated daily test at 6 AM (before operating hours) — a synthetic fingerprint capture using a test artifact. Failure triggers an automatic ticket and technician dispatch.
- **Spare Device Program:** Each kiosk center maintains one spare biometric scanner. The operations runbook `KIOSK-RUNBOOK-001` documents the 5-minute hot-swap procedure.
- **Firmware Version Management:** Biometric device firmware is managed via a central MDM system; updates are tested in a 5-kiosk pilot before rollout to the full fleet.

---

## EC-IDENTITY-007: Multiple Active Sessions Conflict

**Failure Mode:**
A citizen logs in from their mobile phone and begins filling an application. Simultaneously, they also log in from their home computer (e.g., to upload a scanned document). Both sessions are valid and active. The mobile session has draft province version 3 (has filled sections 1–4), while the desktop session has draft province version 5 (has filled sections 1–7). Both submit the draft within seconds of each other. Without conflict detection, the later write overwrites the earlier one, silently discarding data from one of the sessions.

**Impact:**
- **Severity: Medium**
- Data loss in one session — whichever session writes second wins, potentially overwriting more complete data with less complete data.
- The citizen is unaware of the conflict; they believe the full form data has been saved.
- If the application is submitted (not just drafted), a submitted application with incorrect/partial data could proceed through the workflow and issue an incorrect certificate.
- Session token conflicts could also cause confusing UX (e.g., "Application not found" error on mobile after it was submitted from desktop).

**Detection:**
- **Version Mismatch Log:** Every draft save request includes a `draft_version` field. If the server's current version differs from the submitted version, a `DRAFT_VERSION_CONFLICT` event is logged.
- **CloudWatch Metric:** `DraftVersionConflict_Count` — published per conflict event. Spike in this metric indicates a systemic issue (e.g., auto-save firing too frequently from multiple tabs).
- **Session Count Tracking:** Redis tracks active session count per `citizen_id`. A count > 2 triggers a `MultipleActiveSessions` log event (informational, not alert level).

**Mitigation/Recovery:**
1. **Optimistic Locking on Draft:** The `ApplicationDraft` model has a `version` integer field. Every save operation includes `WHERE version = {expected_version}` in the UPDATE query. If the version has changed (another session saved first), the update affects 0 rows, and the server returns HTTP 409 Conflict.
2. **Conflict Resolution UI:** On receiving HTTP 409, the frontend shows the citizen: "Your application was updated from another device. [View latest version] [Keep this version] [Merge manually]." The citizen can compare the two versions side by side.
3. **Last-Write-Wins Option:** For lower-stakes sections (contact information), the system defaults to last-write-wins after presenting a non-blocking notification: "Your changes were saved. A previous version from another session was overwritten."
4. **Session Isolation for Final Submission:** Final application submission (not draft save) requires a session lock: a Redis lock is acquired for the `application_id` for the duration of the submit transaction. A second concurrent submit attempt for the same application is rejected with HTTP 409.
5. **Cross-Device Notification:** When a draft is saved from one device, an in-app notification (via WebSocket or next-page-load polling) is sent to other active sessions: "This application was updated from another device. Refresh to see the latest."

**Prevention:**
- **Encourage Single Active Session:** The portal shows a banner when more than one active session is detected: "You are logged in on another device. Working simultaneously may cause conflicts."
- **Soft Session Limit:** By default, a citizen can have up to 3 active sessions. Additional logins trigger a prompt: "You have 3 active sessions. Logging in here will invalidate the oldest session. Continue?"
- **Draft Locking During Critical Operations:** Document upload steps and payment steps acquire a 10-minute application lock in Redis, preventing another session from modifying the application during these critical phases.

---

## EC-IDENTITY-008: Account Lockout After Failed OTP Attempts

**Failure Mode:**
A citizen attempting to log in enters the wrong OTP 5 times within a 10-minute window (misread OTP, slow connection causing OTP to expire before entry, or accidental keystroke error). The account is locked for 30 minutes as a brute-force protection measure. The citizen, who may have an urgent pending application (e.g., a court submission deadline, scholarship application closing today), is now completely blocked from accessing the portal.

**Impact:**
- **Severity: High**
- Time-sensitive service access is blocked during the lockout window. For deadline-driven applications, this can mean missing a legal or administrative deadline.
- Citizens who do not understand why they are locked out (especially less digitally-literate users) may give up entirely, abandoning their application.
- A support desk overwhelmed by lockout calls during deadline days (end of month, last day of scheme) cannot resolve all cases within the 30-minute window.
- Adversely affects citizen satisfaction metrics and portal adoption in rural areas.

**Detection:**
- **CloudWatch Metric:** `AccountLockout_Count_5Min` — tracks lockout events per 5-minute rolling window. A spike (e.g., >100 in 5 minutes) indicates either a bot attack or a systemic OTP delivery issue causing mass wrong-entry.
- **CloudWatch Alarm:** `AccountLockout_Spike` — fires when `AccountLockout_Count_5Min` > 100, triggering investigation for whether lockouts are due to attack or OTP delivery failure.
- **Per-Citizen Log:** Failed OTP attempts are logged with `citizen_id`, `attempt_count`, `ip_address`, and `user_agent`. An alert fires if a single citizen account has > 3 lockout events in 24 hours (possible bot activity).
- **Support Ticket Auto-Creation:** When an account is locked, a support ticket is created automatically with a pre-filled description and the citizen is notified via SMS: "Your portal account is temporarily locked. It will automatically unlock at [time]. Reference: [ticket ID]."

**Mitigation/Recovery:**
1. **Progressive Lockout:** Rather than a hard 30-minute lockout at 5 failures, the policy is graduated: 1st lockout (5 failures) = 10 minutes, 2nd lockout = 30 minutes, 3rd lockout = 2 hours, 4th lockout = 24 hours + mandatory support call. This reduces impact for genuine misentry cases.
2. **Immediate Self-Unlock via Alternative Identity:** The citizen can self-unlock immediately by completing identity verification through an alternative channel: (a) email OTP to registered email, (b) answering a pre-set security question (if configured), or (c) mobile OTP to the NID-linked mobile (different path from login OTP).
3. **Priority Support Queue:** Accounts in lockout province with pending applications in status `PENDING_PAYMENT` or `ACTION_REQUIRED_BY_TODAY` are automatically escalated to a priority support queue. Support agents can manually unlock these accounts after verbal identity verification via phone.
4. **OTP Resend with Delay:** After 3 failed attempts (before lockout), the frontend offers an "OTP not received?" option to resend a fresh OTP. The new OTP invalidates the previous one. The failure counter does NOT reset on OTP resend — it tracks wrong-entry attempts, not resend attempts.
5. **Automatic Unlock Notification:** When the lockout expires (natural timeout), the citizen receives an SMS and email: "Your account has been unlocked. You can now log in."

**Prevention:**
- **OTP Input Assistance:** The OTP input field on the frontend uses large, clearly spaced digit boxes (6 individual input boxes, auto-advancing), reducing misentry from small mobile keyboards. A countdown timer shows OTP validity remaining.
- **CAPTCHA Before 3rd Attempt:** After 2 failed OTP attempts, a CAPTCHA (hCaptcha, GDPR-compliant) is presented before the third attempt, slowing down bot attacks without locking out genuine users.
- **OTP Delivery Confirmation:** After OTP is sent, the frontend confirms: "OTP sent to mobile number ending in XXXX" (last 4 digits of NID-linked mobile, masked). If the citizen does not recognize this number, they are guided to the email OTP path immediately.
- **Smart Rate Limiting:** AWS WAF rate-based rule limits OTP submit requests to 10 per minute per IP. Separate limit of 5 OTP requests per NID number per hour prevents bot enumeration.

---

## Operational Policy Addendum

The following operational policies govern the identity and authentication domain of the Government Services Portal. These policies are binding on all system operators, developers, and support staff.

### Citizen Data Privacy Policies

- **NID Storage Prohibition:** NID numbers are never stored in plaintext in any database, log file, cache, or analytics system. Only HMAC-SHA256 hashes (with KMS-managed keys) are stored. This is a legal requirement under the NID (Data Security) Regulations 2016.
- **OTP Non-Logging:** OTP values are never logged, even in debug logs. Only OTP request events (sent/failed) and OTP verification events (success/failure) are logged, without the OTP value.
- **Session Data Isolation:** Citizen session data in Redis is stored under keys that include the citizen's session token, not their NID number or citizen ID, to prevent enumeration attacks on the cache.
- **JWT Payload Minimization:** JWT tokens contain only the minimum required claims: `citizen_id` (internal UUID), `role`, `exp`, `iat`, `jti`. No PII (name, NID, mobile number) is included in JWT payloads.
- **Audit Log Retention:** Authentication audit logs (login success/failure, OTP requests, session creation/destruction) are retained for 5 years in a tamper-evident CloudWatch Logs log group with CloudTrail enabled, satisfying IT Act 2000 audit requirements.

### Service Delivery SLA Policies

- **Authentication Availability:** The authentication subsystem (OTP delivery, NASC (National Identity Management Centre) integration, session management) must maintain 99.5% availability on a rolling monthly basis, measured by synthetic canary success rate.
- **OTP Delivery SLA:** 95% of OTPs must be delivered to the citizen's mobile within 30 seconds of request. Failure to meet this SLA triggers escalation to the Nepal Telecom / Sparrow SMS gateway vendor and NASC (National Identity Management Centre) AUA helpdesk.
- **Account Unlock SLA:** Priority support queue unlocks for accounts with pending time-sensitive applications must be completed within 15 minutes of ticket creation during business hours, and within 60 minutes after hours.
- **Kiosk Uptime SLA:** Government kiosk biometric authentication availability must be 98% or greater per calendar month per district. Districts with lower availability receive expedited hardware support.

### Fee and Payment Policies

- **Authentication is Free:** There is no fee for citizen authentication, OTP delivery, session creation, or account recovery. These are not chargeable government services.
- **Kiosk Service Fee:** Where applicable, kiosk service facilitation fees (charged by CSC operators) are governed by the CSC SPV rate card and are not collected through this portal's payment system.

### System Availability Policies

- **Planned Maintenance Windows:** Authentication system maintenance must be scheduled between 2 AM and 5 AM IST. No maintenance affecting citizen login is permitted during 8 AM–8 PM IST on any weekday or on the last 3 days of any month.
- **Degraded Mode Operation:** In the event of NASC (National Identity Management Centre) API unavailability, the portal must continue to offer email OTP as an alternative authentication method without requiring any operator intervention. This degraded mode must be operational within 60 seconds of NASC (National Identity Management Centre) failure detection.
- **Multi-Region Consideration:** Authentication services (JWT signing, OTP delivery, session management) must be resilient to single AZ failure. Multi-AZ deployment is mandatory for all authentication-related Redis and RDS resources.
- **Recovery Time Objective (RTO):** Authentication service RTO is 5 minutes. Recovery Point Objective (RPO) for session data is 1 minute (Redis AOF persistence). Achieving these objectives must be validated in quarterly DR drills.
