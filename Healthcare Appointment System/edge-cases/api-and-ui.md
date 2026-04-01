# API and UI Edge Cases

This document catalogues ten high-impact failure modes at the API and user-interface layers of the Healthcare Appointment System. Each case covers the precise failure mode, business and user impact, detection signals, step-by-step mitigation and recovery, and permanent prevention measures. These edge cases apply to both the patient-facing React SPA and the administrative portal, and inform contract testing, API gateway configuration, and frontend resilience patterns.

---

## Table of Contents

1. [EC-API-001: Duplicate POST Creating a Second Appointment After Client Retry](#ec-api-001)
2. [EC-API-002: Idempotency-Key Collision Between Two Different Patients](#ec-api-002)
3. [EC-API-003: Stale Slot Shown in UI After Reservation by Another User](#ec-api-003)
4. [EC-API-004: Optimistic UI Confirming Appointment Before Server Commit](#ec-api-004)
5. [EC-API-005: JWT Expiry During Multi-Step Booking Flow](#ec-api-005)
6. [EC-API-006: CORS Misconfiguration Allowing Unauthorised Origin](#ec-api-006)
7. [EC-API-007: WebSocket Disconnection During Real-Time Slot Availability Update](#ec-api-007)
8. [EC-API-008: Rate Limit Triggered During High-Volume Clinic Opening](#ec-api-008)
9. [EC-API-009: API Version Sunset Breaking Mobile App Clients on Deprecated v1](#ec-api-009)
10. [EC-API-010: Response Schema Change Breaking Contract Tests and Downstream Integrations](#ec-api-010)

---

### EC-API-001: Duplicate POST Request Due to Client Retry After Network Timeout — Second Request Creates Second Appointment {#ec-api-001}

- **Failure Mode:** A patient submits a booking request. The network connection drops after the server receives and commits the request but before the HTTP 201 response reaches the client. The client's fetch/axios retry logic retransmits the identical POST to `POST /appointments`. The server, having no record of the original transaction being "in flight" from this client, processes it as a new request and creates a second appointment for the same patient, same slot, same provider. The patient has two confirmed appointments and receives two confirmation notifications; the provider's slot appears double-booked.
- **Impact:** Duplicate appointments consume scarce provider slots, blocking other patients from booking. The patient is confused and may attempt to cancel one — potentially cancelling the wrong one. Billing systems may generate two charges or two insurance claims for the same visit. Resolving the duplicate requires manual staff intervention, typically 10–15 minutes per incident; at scale (100 duplicates/day), this equals 1,500–2,500 staff-minutes daily.
- **Detection:**
  - Monitoring query: `SELECT patient_id, provider_id, slot_start, COUNT(*) AS booking_count FROM appointments WHERE status = 'CONFIRMED' AND created_at > NOW() - INTERVAL '5 minutes' GROUP BY patient_id, provider_id, slot_start HAVING COUNT(*) > 1;`
  - Alert threshold: Any patient-provider-slot combination with ≥ 2 `CONFIRMED` appointments within a 5-minute window triggers `SEV-2 DUPLICATE_BOOKING_DETECTED`.
  - Log pattern: `[IDEMPOTENCY] DUPLICATE_REQUEST idempotency_key=<key> existing_appointment_id=<id> returning_cached_response=true`
- **Mitigation/Recovery:**
  1. The idempotency layer detects the duplicate key on the second request and returns the original 201 response body (cached in Redis) without creating a new record.
  2. If duplication occurred before the idempotency layer was in place, query for duplicates using the monitoring query above.
  3. For each duplicate pair, retain the earlier `appointment_id` (first committed); set the later one to `CANCELLED` with `cancellation_reason = SYSTEM_DUPLICATE` and `cancelled_by = SYSTEM`.
  4. Re-release the slot consumed by the cancelled duplicate back to `AVAILABLE`.
  5. Suppress the cancellation notification to the patient (no need to alarm them); send a single consolidated confirmation for the retained appointment.
  6. Refund any duplicate charge processed by the payment service within the same business day.
- **Prevention:**
  - Require a client-generated `Idempotency-Key` header (UUID v4) on all `POST /appointments` requests. The API Gateway validates its presence; requests without it receive `400 MISSING_IDEMPOTENCY_KEY`.
  - On the server, hash the idempotency key and store it in Redis with a 24-hour TTL alongside the serialised response: `SET idempotency:<sha256(key)> <response> EX 86400`. On a duplicate request, return the cached response immediately without executing the command handler.
  - Add a unique database constraint: `UNIQUE (patient_id, provider_id, slot_start)` on the `appointments` table so that even if the idempotency layer is bypassed, the database itself rejects the duplicate with a constraint violation.
  - On the frontend, disable the submit button immediately on first click and show a loading state; re-enable only if the server returns an error (not on success or timeout — let the user refresh to check status instead of retrying blindly).

---

### EC-API-002: Idempotency-Key Collision Between Two Different Patients Using the Same Key Value {#ec-api-002}

- **Failure Mode:** Two different patients happen to send the same `Idempotency-Key` value in their concurrent booking requests — either due to a client-side UUID generation bug (e.g., seeded with the same timestamp in milliseconds on low-entropy mobile devices), or a frontend that reuses a fixed key per session rather than generating a fresh UUID per request. Patient A's booking is committed; Patient B's request hits the idempotency cache, receives Patient A's 201 response body (including Patient A's `appointmentId` and PHI), and the UI erroneously shows Patient B that they have booked Patient A's appointment.
- **Impact:** PHI cross-contamination — Patient B receives Patient A's appointment ID, potentially seeing provider name, slot time, and appointment reason. This is a HIPAA impermissible disclosure. Operationally, Patient B has no actual booking. If Patient B attempts to check in using the returned appointment ID, they are admitted under the wrong patient identity, creating a patient safety risk. Each collision is a reportable breach.
- **Detection:**
  - Log pattern: `[IDEMPOTENCY] KEY_COLLISION key=<key> owner_patient_id=<A> requesting_patient_id=<B> — MISMATCH`
  - Alert: Any idempotency key used by a `patient_id` other than the one who originally created it fires `SEV-1 IDEMPOTENCY_COLLISION` immediately.
  - Monitoring query: `SELECT idempotency_key, COUNT(DISTINCT patient_id) AS distinct_patients FROM idempotency_log GROUP BY idempotency_key HAVING COUNT(DISTINCT patient_id) > 1;`
- **Mitigation/Recovery:**
  1. Immediately invalidate the colliding idempotency key from the cache.
  2. Treat the event as a potential PHI disclosure: identify both patients, document what data was returned to Patient B, and begin OCR breach assessment.
  3. Ensure Patient B's booking was not committed; if a record was created, cancel and re-release the slot.
  4. Patient B must re-initiate the booking flow with a newly generated key.
  5. Notify Patient B that their booking did not complete and prompt them to try again.
- **Prevention:**
  - Scope idempotency keys to the authenticated patient: the server stores `(patient_id, idempotency_key_hash)` as a composite primary key in the idempotency table. A collision check validates that the requesting `patient_id` matches the stored owner — if not, it returns `409 IDEMPOTENCY_KEY_CONFLICT` rather than the cached response.
  - The frontend generates idempotency keys server-side: `GET /idempotency-keys` returns a cryptographically signed, single-use token bound to the authenticated session. This eliminates client-side entropy issues entirely.
  - Idempotency tokens expire after 30 minutes unused; the booking flow prompts the user to refresh if they take longer than 20 minutes.

---

### EC-API-003: Stale Slot Shown in UI After Reservation by Another User in the Same Second {#ec-api-003}

- **Failure Mode:** Two patients load the slot picker simultaneously at T=0 and both see slot `2025-09-15 10:00 AM` as `AVAILABLE`. Patient A clicks the slot at T=5s. The UI tentatively highlights the slot but has not yet hit the reservation API. Patient B also clicks the slot at T=5s from a different browser. Both requests reach the server at nearly the same time. The slot is reserved for one patient (whichever request is committed first via optimistic locking). The other patient's UI still shows the slot as selected and bookable — until they attempt to proceed to the next step and receive a `409 SLOT_ALREADY_BOOKED` error on a step that felt irreversible to the user.
- **Impact:** Poor user experience: the patient has already entered insurance details and a visit reason before discovering the slot is gone. Form abandonment rate increases by an estimated 25–40% when users encounter late-stage booking conflicts. At high traffic volumes (Monday morning appointment rush for a popular specialist), this may affect hundreds of patients simultaneously.
- **Detection:**
  - Client-side telemetry: track `SLOT_STALE_ON_CONFIRM` events — fired when the booking confirmation step returns `409` after a slot was displayed as available. Threshold: > 5% of booking attempts in a 5-minute window.
  - Server log pattern: `[SLOT] RESERVATION_CONFLICT slot_id=<id> winner=<patientA_id> loser=<patientB_id> delta_ms=<ms_between_requests>`
- **Mitigation/Recovery:**
  1. Return a `409 SLOT_ALREADY_BOOKED` response with a body containing the top 3 available alternative slots (`alternatives: [SlotDTO]`) so the patient can immediately rebook without returning to the slot picker.
  2. The UI presents an inline modal: "This slot was just taken. Here are the next available times:" with one-click selection for each alternative.
  3. Log the conflict for capacity planning: if a particular provider's slots are consistently experiencing race conditions, surface this to clinic operations as a signal to open additional slots or add a provider.
- **Prevention:**
  - Implement a short-lived slot hold (soft lock): when a patient selects a slot, issue `POST /slots/{id}/hold` which marks the slot as `HELD` for 5 minutes in Redis (`SET slot:hold:<slotId> <patientId> EX 300`). The slot is unavailable to other patients during the hold.
  - The slot picker polls `GET /slots/available` every 15 seconds (or uses WebSocket push, see EC-API-007) so that held/reserved slots disappear from the UI in near real-time.
  - On the confirmation step (just before final commit), perform a server-side slot availability re-check as part of the transaction. If the hold has lapsed or been taken, fail fast with alternatives.
  - Display a "Slot reserved for X:XX remaining" countdown timer in the UI to create urgency and prevent idle sessions from holding slots indefinitely.

---

### EC-API-004: Optimistic UI Confirming Appointment Before Server Has Committed Transaction {#ec-api-004}

- **Failure Mode:** The frontend immediately transitions to a "Booking Confirmed" screen upon receiving a `202 Accepted` (asynchronous processing) or even before receiving any server response (pure optimistic update). The server-side command handler subsequently fails — due to a slot conflict, a payment decline, an insurance verification failure, or a database transaction rollback. The patient believes their appointment is confirmed; no actual booking exists. They may take time off work, arrange childcare, or travel to the clinic based on a confirmation that was never real.
- **Impact:** Patient arrives at the clinic without a valid appointment — direct patient safety and satisfaction issue. No-show penalty may be incorrectly applied to the patient. The provider's schedule appears full when it is not, blocking other patients from booking. Trust damage is severe: patients who experience a phantom confirmation are significantly less likely to use the platform again (estimated 60% churn for affected patients). Regulatory risk: if a patient misses critical medical care due to a phantom confirmation, liability exposure is significant.
- **Detection:**
  - Client-side event: `BOOKING_PHANTOM_CONFIRM` — fired when the UI has shown a confirmed state but a subsequent poll to `GET /appointments/{id}` returns a non-`CONFIRMED` status.
  - Server log pattern: `[BOOKING] COMMAND_FAILED command=CreateAppointment correlation_id=<id> reason=SLOT_CONFLICT after_202_issued=true`
  - Alert: Any `202 Accepted` response for `POST /appointments` not followed by a `CONFIRMED` appointment record within 30 seconds triggers `SEV-2 ASYNC_BOOKING_FAILURE`.
- **Mitigation/Recovery:**
  1. Immediately send an in-app, email, and SMS notification to the patient: "Your booking did not complete. Please try again." Include a direct link to the slot picker with the patient's previously selected criteria pre-filled.
  2. Ensure no charge was processed; if a payment intent was created, void it within the same API call.
  3. Release any slot hold associated with the failed booking.
  4. Log the failure with the correlation ID for support lookup; include in the patient's booking history as `BOOKING_FAILED`.
- **Prevention:**
  - Never show a "Confirmed" UI state based on a `202 Accepted` or before receiving a terminal success response. The booking flow must receive a `201 Created` with `status: CONFIRMED` (or a WebSocket `APPOINTMENT_CONFIRMED` event) before displaying the confirmation screen.
  - Use a polling or WebSocket strategy for async flows: after posting the booking command, the UI enters a "Processing…" state and polls `GET /appointments/pending/{correlationId}` every 2 seconds (max 30 seconds) until the appointment transitions to `CONFIRMED` or a terminal error state.
  - Display a neutral "We're processing your booking" screen with a spinner — not a confirmation — until the server confirms success.
  - Implement a dead-letter handler: if the booking command fails after `202`, the command handler publishes a `BookingFailedEvent` which triggers the patient notification and slot release flow.

---

### EC-API-005: JWT Expiry During Multi-Step Booking Flow — Token Expires Between Step 2 and Step 3 {#ec-api-005}

- **Failure Mode:** The patient booking flow spans 4 steps: (1) slot selection, (2) insurance/reason details, (3) payment, (4) confirmation. Each step takes 2–5 minutes for a distracted or thorough patient. The JWT access token has a 15-minute expiry. If the patient spends 8 minutes on step 2 (entering insurance details) and 8 minutes on step 3 (reviewing payment), the token expires mid-flow. When step 3 submits, the API returns `401 Unauthorized`. The patient loses all form data and must log in again — with no guarantee their slot hold has been preserved.
- **Impact:** Booking abandonment: ~15–20% of patients who encounter a mid-flow session expiry do not complete their booking. The clinic loses an estimated $150–$400 in appointment revenue per abandoned booking. Patients with low digital literacy or accessibility needs (elderly patients, those using screen readers) are disproportionately affected. The slot hold expires while the patient is re-authenticating, potentially forcing them to restart from slot selection.
- **Detection:**
  - Client-side event: `BOOKING_SESSION_EXPIRED step=<step_number> patient_id=<id>` — emitted whenever a `401` is received during the booking flow.
  - Alert threshold: > 3% of active booking sessions encountering a `401` within the booking flow in a 15-minute window.
  - Monitoring query: `SELECT COUNT(*) FROM booking_sessions WHERE status = 'ABANDONED_AUTH_EXPIRED' AND created_at > NOW() - INTERVAL '1 hour';`
- **Mitigation/Recovery:**
  1. The API Gateway returns `401` with `WWW-Authenticate: Bearer error="token_expired"`.
  2. The frontend intercepts `401` responses during the booking flow and attempts a silent token refresh using the refresh token (HTTP-only cookie): `POST /auth/refresh`.
  3. If the silent refresh succeeds, the original failed request is automatically retried with the new access token — transparent to the user.
  4. If the refresh token has also expired (user has been idle > 7 days), the frontend serialises the current booking form state to `sessionStorage` before redirecting to the login page. After login, the flow is restored from `sessionStorage` and the patient continues from the step they were on.
  5. On restoration, check if the slot hold is still valid; if expired, attempt to re-acquire it. If the slot is now taken, present alternatives.
- **Prevention:**
  - Implement silent token refresh: the access token (15-min TTL) is refreshed proactively 60 seconds before expiry using the refresh token, so a long-running booking session never encounters a `401` mid-step.
  - Extend slot holds to 20 minutes (matching the outer bound of a reasonable booking session); reset the hold TTL on each inter-step API call.
  - On the backend, the booking session command (`CreateBookingSession`) stores the partial booking state (slot ID, reason, insurance details) server-side, scoped to the authenticated user. If the session expires and the user re-authenticates, the frontend can call `GET /booking-sessions/active` to restore state rather than relying on `sessionStorage`.

---

### EC-API-006: CORS Misconfiguration Allowing Unauthorised Origin to Make Credentialed Requests {#ec-api-006}

- **Failure Mode:** The API Gateway or NestJS CORS middleware is configured with `origin: '*'` (wildcard) while also setting `credentials: true`. In practice, browsers do not allow both simultaneously — but if the server instead echoes the incoming `Origin` header without validation (`origin: (origin, cb) => cb(null, origin)`), any website can make credentialed cross-origin requests to the API using the patient's session cookies. A malicious website can perform CSRF-like attacks: booking, cancelling, or reading appointments on behalf of the authenticated user without their knowledge.
- **Impact:** A malicious actor hosting a phishing site can silently cancel a patient's appointment (causing them to miss critical care) or book fraudulent appointments against their account. In a targeted attack against a clinic's patient base, this can affect hundreds of patients in minutes. The attack exploits the patient's authenticated session without compromising their credentials — a CSRF-by-CORS vector that is difficult for patients to detect.
- **Detection:**
  - CORS policy audit: automated test in CI sends a preflight `OPTIONS` request with `Origin: https://evil.example.com` and asserts that the response does NOT include `Access-Control-Allow-Origin: https://evil.example.com` or `Access-Control-Allow-Credentials: true`.
  - Alert: Any response with `Access-Control-Allow-Origin` set to a value not in the configured allowlist fires `SEV-1 CORS_POLICY_VIOLATION` in the security monitoring dashboard.
  - Log pattern: `[CORS] REFLECTED_ORIGIN origin=https://evil.example.com allowed=true — POLICY_VIOLATION`
- **Mitigation/Recovery:**
  1. Immediately update the CORS configuration to use an explicit allowlist: `origin: ['https://app.healthclinic.com', 'https://admin.healthclinic.com']`.
  2. Audit access logs for the past 24 hours for requests with non-allowlisted `Origin` headers that received `Access-Control-Allow-Credentials: true` — these may represent exploitation attempts.
  3. Force rotation of all session cookies / refresh tokens to invalidate any sessions that may have been hijacked.
  4. Notify the security team and begin incident assessment.
- **Prevention:**
  - Configure CORS with an explicit string array allowlist; never reflect the incoming `Origin` value. Use a review-gated environment variable (`CORS_ALLOWED_ORIGINS=https://app.healthclinic.com`) that is audited at deploy time.
  - Add an integration test to the CI pipeline: `assert(preflightResponse.headers['access-control-allow-origin']).not.toContain('evil.example.com')`.
  - Enable CSRF tokens for all state-mutating requests (alternatively, use the `SameSite=Strict` cookie attribute on session cookies, which prevents cross-origin cookie transmission in all modern browsers without requiring explicit CSRF tokens).
  - Run OWASP ZAP or a similar DAST tool against the staging environment on every release; include CORS misconfiguration as a mandatory check.

---

### EC-API-007: WebSocket Disconnection During Real-Time Slot Availability Update Leaving UI in Unknown State {#ec-api-007}

- **Failure Mode:** The slot picker uses a WebSocket connection (`wss://api.healthclinic.com/slots/live`) to receive real-time availability updates. A patient loads the slot picker at T=0 with 5 available slots. At T=30s, the WebSocket connection drops silently (mobile network switch, proxy timeout, server-side pod restart). Between T=30s and T=5m, three slots are taken by other patients. The frontend still displays 5 available slots (the state at T=30s) and does not know that the WebSocket is disconnected. The patient selects one of the three now-taken slots and proceeds to the booking confirmation — only discovering the conflict at the final API call.
- **Impact:** High booking abandonment rate for patients on mobile networks or behind enterprise proxies that aggressively terminate idle connections. An unknown-state UI is worse than a clearly stale UI — the patient has no signal that the availability shown is unreliable. If the platform has high concurrent traffic, 10–20% of booking attempts during peak hours may encounter a stale-slot conflict due to WebSocket reliability issues.
- **Detection:**
  - Client-side event: `WEBSOCKET_DISCONNECT reason=<close_code> slot_picker_active=true` — emitted whenever the WebSocket closes unexpectedly while the slot picker is visible.
  - Client-side event: `SLOT_STALE_AFTER_WS_DISCONNECT` — emitted when a booking attempt returns `409` and the client was in a disconnected state.
  - Alert threshold: `WEBSOCKET_DISCONNECT` events exceeding 5% of active sessions per minute triggers `SEV-3 WS_STABILITY_DEGRADED`.
- **Mitigation/Recovery:**
  1. On `WebSocket.onclose` or `WebSocket.onerror`, the client immediately switches to HTTP polling mode: `GET /slots/available?providerId=<id>&date=<date>` every 15 seconds.
  2. The UI displays a non-blocking banner: "Live updates paused — showing latest available slots." with a "Refresh" button.
  3. On reconnect (`WebSocket.onopen`), the client requests a full state sync by sending a `SYNC_REQUEST` message; the server responds with the current availability snapshot, replacing the stale client state.
  4. After 3 failed reconnect attempts with exponential backoff (5s, 10s, 20s), fall back permanently to polling for the remainder of the session.
- **Prevention:**
  - Implement WebSocket heartbeat ping/pong: the server sends a `PING` frame every 30 seconds; the client must respond with `PONG` within 5 seconds, otherwise the connection is considered stale and the client initiates reconnection.
  - The client maintains a `connectionState` flag (`CONNECTED`, `RECONNECTING`, `POLLING_FALLBACK`) and renders appropriate UI feedback for each state.
  - All slot availability data includes a `lastUpdatedAt` timestamp in the WebSocket message payload; the UI displays "As of X:XX" to set user expectations about data freshness.
  - The backend WebSocket handler broadcasts slot updates to a Redis Pub/Sub channel; any new server pod joining the cluster subscribes to the channel, ensuring continuity across pod restarts without client reconnection.

---

### EC-API-008: Rate Limit Triggered During High-Volume Clinic Opening (Appointment Rush on Popular Specialist) {#ec-api-008}

- **Failure Mode:** A highly sought-after specialist (e.g., a paediatric cardiologist) opens their schedule for the next quarter at 8:00 AM on a Monday. Within 60 seconds, 2,000 patients simultaneously attempt to book appointments. The API Gateway's rate limiter (configured at 500 requests/minute per service) triggers for `POST /appointments` and returns `429 Too Many Requests` to 1,500 patients — roughly 75% of patients who attempted to book are rejected, even though available slots still exist. The clinic's phone lines are flooded with complaints, and social media erupts with negative feedback.
- **Impact:** Revenue loss: each rejected appointment is an average of $200–$600 in visit revenue. For 1,500 rejections: $300,000–$900,000 in lost bookings if patients do not successfully retry. Brand damage: a "sold out in 60 seconds" experience with poor error handling leads to patient frustration and media coverage disproportionate to the actual capacity. Operational impact: front-desk staff are overwhelmed with complaint calls.
- **Detection:**
  - Alert: `429` response rate for `POST /appointments` exceeding 20% of requests in a 1-minute window fires `SEV-2 BOOKING_RUSH_RATE_LIMIT`.
  - Monitoring metric: `http_responses_total{status="429", path="/appointments"}` > 100 in 60 seconds.
  - Log pattern: `[RATE_LIMIT] LIMIT_HIT service=booking-service client_ip=<ip> limit=500/min current=2000/min`
- **Mitigation/Recovery:**
  1. The `429` response includes a `Retry-After` header with a randomised jitter value (5–30 seconds) to spread retry traffic and prevent a thundering herd on the next tick.
  2. On `429`, the UI presents a "Queue position" screen: "You're in a virtual queue. We'll hold your spot and let you know when you can proceed." — backed by a Redis sorted-set queue.
  3. The patient's slot selection is preserved in the virtual queue; when their turn arrives (within the rate limit window), the booking is submitted automatically and the patient is notified.
  4. On-call engineering receives the `SEV-2` alert; evaluates whether to temporarily increase the rate limit or scale out the booking service horizontally (Kubernetes HPA triggers on CPU/RPS metrics).
- **Prevention:**
  - Implement a virtual waiting room for high-demand clinic openings: when a provider's schedule is published, the system detects that available slots < projected demand (based on waitlist size) and automatically routes booking traffic through a fair-access queue rather than a first-come-first-served rate limiter.
  - Configure adaptive rate limits by endpoint: `POST /appointments` has a higher burst allowance (2,000/min with token bucket) than administrative endpoints (100/min).
  - Use Kubernetes HPA with custom RPS-based scaling metrics for the booking service so that pod count scales out within 60 seconds of a traffic spike.
  - Offer email/SMS "slot opening notifications" to patients on the waitlist, staggering the notification delivery over 10 minutes to spread the traffic wave rather than triggering a simultaneous rush.

---

### EC-API-009: API Version Sunset Breaking Mobile App Clients Still on Deprecated v1 Endpoints {#ec-api-009}

- **Failure Mode:** The platform deprecates `v1` API endpoints in favour of `v2` (which introduces breaking changes: renamed fields, new required parameters, different authentication flows). Deprecation was announced via changelog and developer email 6 months prior. The sunset date arrives; `v1` endpoints are decommissioned. However, 15% of active mobile app installs are still on an old version that calls `v1` endpoints — patients who have not updated their app, are using app stores with delayed auto-updates, or are on enterprise MDM-managed devices. These patients cannot book, cancel, or view appointments — the app shows only a generic error screen.
- **Impact:** 15% of the mobile patient base is completely locked out from the platform. An estimated 500–2,000 patients per day are unable to access care management features. Each locked-out patient requiring manual staff assistance costs ~$8–$12 in support time. App store reviews drop sharply; a 1-star review wave can reduce organic download rates by 20–30% for months. Patients with chronic conditions who rely on the app for regular booking face disproportionate care access disruption.
- **Detection:**
  - API log metric: count of `404` or `410 Gone` responses on `v1` endpoints in production after sunset date: `SELECT COUNT(*) FROM request_log WHERE path LIKE '/v1/%' AND status_code IN (404, 410) AND timestamp > '<sunset_date>';`
  - Alert threshold: > 50 requests per minute to sunsetted `v1` endpoints triggers `SEV-3 V1_CLIENT_DETECTED`.
  - Mobile analytics: `app_version` dimension on booking funnel events — alert when any app version using `v1` API has more than 100 active sessions per day.
- **Mitigation/Recovery:**
  1. Immediately reinstate `v1` endpoints in compatibility mode (read-only or full, depending on risk) for a 30-day emergency extension to avoid patient lockout.
  2. Push an urgent app update via all app stores with expedited review requests; increase the in-app "update available" banner to a blocking modal for `v1` clients.
  3. Send push notifications and SMS to patients on old app versions: "Action required: please update the app to continue booking appointments."
  4. For enterprise/MDM-managed deployments, contact IT administrators directly.
  5. Identify and grandfather the most common `v1` client scenarios via a `v1`→`v2` translation proxy layer so that `v1` requests are internally translated to `v2` calls.
- **Prevention:**
  - Implement a versioned API deprecation lifecycle with mandatory stages: `ACTIVE` → `DEPRECATED` (6-month warning) → `SUNSET` (30-day grace) → `DECOMMISSIONED`.
  - During `DEPRECATED` stage, return `Deprecation: true` and `Sunset: <date>` HTTP headers on every `v1` response so that monitoring tools (Stoplight, API documentation portals) can surface alerts to integration owners.
  - Add a minimum app version gate on the backend: if `User-Agent` indicates an app version using `v1` and the sunset date is within 14 days, return a `426 Upgrade Required` response with an upgrade prompt — before full decommission, allowing proactive client updates.
  - Design APIs for forward compatibility: use additive changes (new optional fields) before breaking changes; breaking changes always increment the major version.

---

### EC-API-010: Response Schema Change (Field Renamed) Breaking Contract Test and Downstream Integrations {#ec-api-010}

- **Failure Mode:** A backend developer renames the `appointmentDateTime` field to `scheduledAt` in the `AppointmentResponseDTO` during a refactoring. The REST API response now returns `scheduledAt` instead of `appointmentDateTime`. The change is backwards-incompatible: the EHR integration service, the SMS notification service, and the patient mobile app all parse `appointmentDateTime`. Contract tests existed for the `GET /appointments/{id}` endpoint but were not updated. The contract test passes because the test was not regenerated after the schema change. At 2:00 AM, the SMS notification service fails to send appointment reminders because `appointment.appointmentDateTime` is `undefined`.
- **Impact:** Silent notification failure: patients do not receive their 24-hour reminder SMS for appointments scheduled that night. No-show rate increases — each no-show costs the clinic $150–$400 in lost revenue and wastes the provider's time. The EHR integration service may display incorrect appointment times, creating patient safety risk if care teams rely on the EHR for scheduling context. Debugging a silent field-rename failure at 2 AM takes 45–90 minutes on average.
- **Detection:**
  - Contract test failure in CI: Pact consumer-driven contract test asserts that `GET /appointments/{id}` response includes `appointmentDateTime` as an ISO 8601 string. The build fails on the rename.
  - Alert: SMS notification service logs `[NOTIFICATION] FIELD_MISSING field=appointmentDateTime appointment_id=<id> skipping_send=true` — fires `SEV-2 NOTIFICATION_FIELD_MISSING` alert.
  - Monitoring query: `SELECT COUNT(*) FROM notification_log WHERE status = 'SKIPPED' AND reason = 'MISSING_FIELD' AND created_at > NOW() - INTERVAL '1 hour';` — alert if count > 10.
- **Mitigation/Recovery:**
  1. Immediately revert the field rename in the DTO or add a backwards-compatible alias: include both `appointmentDateTime` (deprecated) and `scheduledAt` (new) in the response for a transition period.
  2. Identify all notifications that failed due to the missing field: `SELECT appointment_id FROM notification_log WHERE status = 'SKIPPED' AND reason = 'MISSING_FIELD' AND notification_type = 'REMINDER_24H';`
  3. Re-enqueue all affected reminder notifications with immediate priority if appointments are within the next 24 hours.
  4. For appointments already missed (within the past 2 hours), send an apology SMS with a rebooking link.
  5. Update all consumer contract tests and integration tests to use `scheduledAt`; remove `appointmentDateTime` only after all consumers confirm migration.
- **Prevention:**
  - Adopt Consumer-Driven Contract Testing (Pact): each downstream consumer (mobile app, SMS service, EHR adapter) publishes a Pact contract specifying the fields it depends on. The provider (appointment API) runs Pact verification in CI; any schema change that breaks a consumer contract fails the build before merge.
  - Enforce an API evolution policy: field renames are always backwards-incompatible breaking changes and require a major API version bump. Within a version, only additive changes (new optional fields) are permitted.
  - Use an OpenAPI schema registry (Swagger Hub, Stoplight) as the source of truth; enforce that the generated `AppointmentResponseDTO` TypeScript type is derived from the OpenAPI spec (not the other way around) using `openapi-typescript` code generation in CI.
  - Add a deprecation lifecycle for fields: mark `appointmentDateTime` as `deprecated: true` in the OpenAPI spec; publish a 3-month migration timeline to all integration owners before removal.

---

## Cross-Cutting API and UI Quality Standards

| Concern | Standard | Enforcement |
|---|---|---|
| Idempotency | All `POST`/`PATCH`/`DELETE` endpoints require `Idempotency-Key` header | API Gateway validation; 400 on missing key |
| Correlation tracing | All responses include `X-Correlation-ID` header | Global NestJS interceptor |
| Error response format | RFC 7807 Problem Details (`type`, `title`, `status`, `detail`, `instance`) | Global exception filter |
| Rate limiting | Per-user and per-IP limits; `Retry-After` header on all 429s | API Gateway policy |
| API versioning | Semver major for breaking changes; `Deprecation` + `Sunset` headers for deprecated versions | API Gateway routing |
| Contract testing | Pact consumer-driven contracts for all integration consumers | CI gate on provider build |
| CORS | Explicit allowlist; `SameSite=Strict` cookies; no wildcard + credentials | NestJS CORS config; CI assertion test |
| Frontend state | No optimistic success state; all confirmations require server-verified terminal status | React booking flow design rule |
| Schema governance | OpenAPI spec is source of truth; DTOs generated from spec | Code generation in CI (`openapi-typescript`) |
| Observability | P50/P95/P99 latency, error rate, and 4xx/5xx breakdown per endpoint tracked in Datadog | Auto-instrumented by API Gateway |
