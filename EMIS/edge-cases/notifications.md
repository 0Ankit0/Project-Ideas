# Edge Cases — Notifications

Domain-specific failure modes, impact assessments, and mitigation strategies for the multi-channel notification system.

Edge case IDs in this file are permanent: **EC-NOTIF-001 through EC-NOTIF-008**.

---

## EC-NOTIF-001 — Notification Storm on Mass Grade Publication

| Field | Detail |
|---|---|
| **Failure Mode** | Exam officer publishes grades for all 2,800 students simultaneously. The `grades.published` event triggers individual email and SMS notifications for every student at once, overwhelming the SES and Twilio sending queues. |
| **Impact** | Delivery latency spikes. SES sending rate limit (14 emails/second on shared IPs) is hit. Twilio rate limits exceeded. Some notifications are dropped or bounced. |
| **Detection** | CloudWatch metric: `ses.send.rate` and `twilio.sms.errors`. Alert at > 80% of sending capacity. Celery queue depth for `email` queue exceeds 1,000 messages. |
| **Mitigation / Recovery** | (1) Notification worker applies a rate-limiter token-bucket (configurable: default 10 emails/s, 5 SMS/s). Celery queue acts as the natural buffer — messages are processed at the throttled rate. (2) In-app notification is delivered instantly (database write); email and SMS follow at the throttled rate. (3) Dedicated SES IP pool is pre-warmed to support higher burst rates. |
| **Prevention** | Grade publication for a large cohort triggers a "batch notification" mode: single digest email per student rather than one email per exam. Notification dispatcher groups events by student within a 5-minute window. |

---

## EC-NOTIF-002 — User Opts Out of All Channels and Misses Critical Alert

| Field | Detail |
|---|---|
| **Failure Mode** | A student opts out of all notification channels (email, SMS, push, in-app) via the preference settings. A critical system message (e.g., exam hall change, emergency campus closure) is issued. The student receives nothing. |
| **Impact** | Student misses critical institutional communication. May show up at the wrong exam hall or be unaware of an emergency. Potential liability for the institution. |
| **Detection** | Channel Router identifies students with no active channels. |
| **Mitigation / Recovery** | (1) Channel Router enforces a list of `MANDATORY_EVENT_TYPES` (e.g., `exam.hall_changed`, `campus.emergency`, `enrollment.cancelled`) for which delivery always occurs on at least one channel — in-app notification cannot be opted out of. (2) After sending, Delivery Log records that the notification was sent to the mandatory in-app channel despite opt-out. |
| **Prevention** | Notification Preferences UI clearly marks certain event types as "mandatory — cannot be disabled." Admin can also define mandatory event types via configuration without code changes. |

---

## EC-NOTIF-003 — Stale Push Token Causing Silent Failure

| Field | Detail |
|---|---|
| **Failure Mode** | A student uninstalls the mobile app and reinstalls it, generating a new FCM device token. The old token remains in the device registry. Push notifications to the old token return FCM error `UNREGISTERED`. |
| **Impact** | Push notifications silently fail for this student. No error is surfaced. Student misses push alerts. Stale tokens accumulate in the database. |
| **Detection** | FCM response includes `UNREGISTERED` error code for each failed push token. Push Sender captures this code and marks the token as invalid. |
| **Mitigation / Recovery** | (1) On FCM `UNREGISTERED` error, Push Sender marks the device token `is_active = False` in the DeviceToken table. (2) Channel Router falls back to email for the same notification. (3) When the student next opens the app, a fresh FCM registration token is sent to EMIS via `PATCH /api/notifications/device-tokens/`, which creates or updates the token record. |
| **Prevention** | App registers a new token on every launch. EMIS upserts the token (update if `user_id + device_id` exists, insert otherwise). Monthly cleanup job removes device tokens inactive for > 90 days. |

---

## EC-NOTIF-004 — Email Bounce Loop

| Field | Detail |
|---|---|
| **Failure Mode** | A student's registered email address is no longer valid (mailbox full, domain expired). SES delivers a bounce notification. EMIS does not process the bounce and continues attempting email delivery to the same invalid address, eventually causing SES to flag the account for high bounce rates. |
| **Impact** | SES account reputation is degraded. Deliverability for all users decreases. Account may be placed on a sending pause by AWS. |
| **Detection** | SES SNS bounce notifications are received at an SQS queue, processed by a Lambda function that marks the email address as `bounced` in the User table. |
| **Mitigation / Recovery** | (1) Lambda bounce handler sets `User.email_bounced = True` and removes the email address from active notification channels. (2) Student is notified via SMS (if available) or in-app to update their email address. (3) Finance/Registrar staff can also manually flag email updates if the student contacts them. |
| **Prevention** | SES bounce and complaint rates are monitored in CloudWatch. Alert triggers at > 2% bounce rate. New user email addresses are validated via a confirmation flow before being set as the primary address. |

---

## EC-NOTIF-005 — Redis Pub/Sub Event Loss During Failover

| Field | Detail |
|---|---|
| **Failure Mode** | ElastiCache Redis undergoes a primary-to-replica failover. During the brief failover window (typically 30–60 seconds), domain events published to Redis Pub/Sub channels are lost because Pub/Sub does not persist messages. |
| **Impact** | Notifications for events during the failover window are never sent. Affected events: enrollment confirmations, grade alerts, payment receipts — depending on timing. |
| **Detection** | Delivery Log coverage gap: events published within the failover window have no corresponding `notification.sent` record. |
| **Mitigation / Recovery** | (1) Domain services write a `DomainEvent` record to the PostgreSQL database before publishing to Redis. (2) A background reconciliation job runs every 5 minutes: finds `DomainEvent` records with no matching `notification.sent` entry older than 10 minutes, and re-publishes them. (3) Reconciliation prevents duplicate notifications via idempotency keys on the notification payload. |
| **Prevention** | Event sourcing pattern: every domain event is persisted to the DB first (outbox pattern), then published to Redis. This decouples event durability from Redis availability. |

---

## EC-NOTIF-006 — SMS OTP Delivered to Wrong Number Due to Reassignment

| Field | Detail |
|---|---|
| **Failure Mode** | A student's phone number was previously registered by another person who has since relinquished it. The number has been reassigned by the telecom provider to a new subscriber. The new subscriber receives OTP or sensitive academic notification SMS intended for the original student. |
| **Impact** | Privacy breach. New subscriber receives personal academic information. Original student cannot receive OTPs. |
| **Detection** | Difficult to detect automatically; typically discovered via student complaint or by Twilio error code `21614` (number not capable of receiving SMS) if the number type changed. |
| **Mitigation / Recovery** | (1) When a student reports non-receipt of OTPs, support staff can trigger a phone number re-verification flow. (2) Student must re-verify via email OTP before changing phone number. (3) Old phone number is deactivated for all future notifications immediately on update. |
| **Prevention** | Phone number verification is required on every update (not just initial registration). Phone numbers are hashed before storage; plaintext is used only for sending. Rate-limiting on OTP sends (max 5 OTP requests per number per hour) prevents abuse. |

---

## EC-NOTIF-007 — Notification Template Rendering Failure

| Field | Detail |
|---|---|
| **Failure Mode** | A notification template references a context variable that is absent from the event payload (e.g., a template uses `{{ student.full_name }}` but the event payload only contains `student_id`). Template rendering raises an exception, the Celery task fails, and no notification is sent. |
| **Impact** | Student does not receive a notification. If the missing variable is for a critical event (exam hall change), the impact is significant. |
| **Detection** | Template rendering exceptions are caught in the Celery task, logged to CloudWatch with event type and payload, and trigger an alert. |
| **Mitigation / Recovery** | (1) Template rendering exception is caught. The task records the failure in DeliveryLog with `status=RENDER_FAILED`. (2) A fallback plain-text notification is sent: "You have a new notification from EMIS. Please log in to view details." (3) Engineering team is alerted to fix the template or event payload schema. |
| **Prevention** | Template rendering is unit-tested for every event type with representative payloads. A CI pipeline step renders all templates against their schemas and fails the build on any rendering error. Event schemas are validated with `pydantic` before publishing to Redis. |

---

## EC-NOTIF-008 — Notification Preference Reset After Account Merge

| Field | Detail |
|---|---|
| **Failure Mode** | A student has two accounts (one created during the application process and one as an enrolled student). When the accounts are merged by admin, the notification preferences from the application account (which had different settings) overwrite the student account's preferences. |
| **Impact** | Student's carefully configured preferences are silently reset. They may start receiving notifications they had disabled or lose notifications they had enabled. |
| **Detection** | Account merge triggers a PreferenceMerge event. The merge strategy is logged. Student receives a notification: "Your account has been merged. Review your notification preferences." |
| **Mitigation / Recovery** | (1) Account merge presents admin with a UI to choose which preference set to retain (or merge by taking the most permissive settings). (2) Post-merge, student receives in-app notification prompting them to review their preferences. (3) Both pre-merge preference snapshots are saved in AuditLog for reference. |
| **Prevention** | Account merges are rare and require ADMIN action. The merge workflow includes a mandatory "preference conflict resolution" step. Integration tests cover merge scenarios. |

---

## Operational Policy Addendum

### Academic Integrity Policies
Notification templates for grade-related events (grade.published, grade.dispute.resolved) are reviewed and approved by the Registrar before deployment. No grade information is included in notification emails by default — only a prompt to log in and view results in the portal, to prevent accidental data exposure via email forwarding.

### Student Data Privacy Policies
Notification content containing personal data (student name, fee amounts, grade values) is never logged in plaintext. Log entries contain only `event_type`, `user_id`, `channel`, and `status`. Notification delivery logs are retained for 1 year and then deleted. Email addresses and phone numbers in transit are treated as sensitive data — HTTPS/TLS is used for all API calls to SES and Twilio.

### Fee Collection Policies
Payment confirmation notifications are sent immediately on successful gateway webhook receipt. Overdue fee reminder notifications follow a tiered schedule (configured in Celery Beat): 7 days before due → reminder; on due date → reminder; 3 days after due → final warning; 7 days after due → hold notification.

### System Availability During Academic Calendar
The Notification Container (Celery workers) is not classified as Mission-Critical for uptime purposes — its failure does not block student or faculty operations. However, notification queue backlog is monitored. If queue depth exceeds 5,000 messages, additional Celery worker tasks are scaled up automatically.
