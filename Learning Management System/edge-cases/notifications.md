# Edge Cases — Notifications

> **Scope:** Covers duplicate delivery, premature grade notifications, channel disablement, late reschedule alerts, provider failures on certificate issuance, template rendering crashes, notification storms, unsubscribe compliance, deactivated accounts, and deadline-past notifications.

---

## 1. Learner Receives Duplicate Enrollment Confirmation Emails

**Failure Mode:** The enrollment service publishes an `enrollment.created` event to a message queue. Due to at-least-once delivery semantics, the event is delivered twice within 500 ms. The notification worker processes both, dispatching two identical emails to the learner.

**Impact:** Learner receives two copies of the same email within seconds. Repeated occurrences damage sender reputation and reduce open rates. If the email contains a "click to activate" link, the learner may attempt both links and create a confusing double-session state.

**Detection:**
- Monitor `notification_sent` events: alert if the same `(learner_id, template_id, course_id)` tuple appears more than once within a 60-second window.
- Track `duplicate_notification_suppressed` counter; an unexpected drop to zero may indicate the deduplication guard is broken.
- ESP (Email Service Provider) bounce/complaint dashboard: sudden spike in duplicate complaints.

**Mitigation/Recovery:**
- Notification worker: compute a deduplication key = `SHA-256(learner_id + template_id + course_id + date)`; check Redis before sending; mark key as sent with TTL = 24 h.
- Idempotent send: `POST /notifications/send` accepts an `idempotency_key` header; returns `200 OK` with the existing send record on duplicate.
- If duplicates are already sent: send a single follow-up apology email only if >2 duplicates were received by the same learner.

---

## 2. Grade Notification Fires Before All Rubric Criteria Are Scored

**Failure Mode:** A rubric has 5 criteria. Grader scores criteria 1–4 and saves. A background job polls for "grading complete" using the heuristic `scored_criteria_count > 0`; it fires a grade-ready notification. Learner opens grade view to see an incomplete score with criterion 5 blank.

**Impact:** Learner sees a partial grade and may act on incorrect information (e.g., assume they failed). Instructor receives a complaint. Grade must be re-notified after criterion 5 is scored, potentially causing confusion.

**Detection:**
- Alert on `grade_notification_sent` events where `scored_criteria_count < total_criteria_count`.
- Monitor learner-opened grade views where `incomplete_rubric = true` within 30 minutes of a notification.

**Mitigation/Recovery:**
- Grade-ready notification fires only when `scored_criteria_count = total_criteria_count AND grade.state = PUBLISHED`.
- Use a workflow lock: set `grading_session.notification_eligible = true` only when the instructor explicitly clicks "Submit Grades".
- If a premature notification was sent: send a correction notification with subject "Updated grade available — [Course Name]" within 5 minutes of final score publication.

---

## 3. Tenant Disables Email Channel Mid-Course

**Failure Mode:** A tenant admin disables the email notification channel for cost reasons while a cohort is 60% through a 12-week course. Learners enrolled before the change no longer receive deadline reminders, feedback notifications, or certificate delivery emails.

**Impact:** Learner completion rates drop 15–25% due to missed deadline reminders. Certificate email delivery fails silently. The tenant may not realize the downstream impact until learners complain.

**Detection:**
- When a notification channel is disabled, run an impact query: `SELECT COUNT(DISTINCT learner_id) FROM enrollments WHERE course.has_pending_notifications = true AND tenant_id = ?`.
- Alert on `channel_disabled` event if `affected_active_learner_count > 100`.
- Monitor `notification_delivery_rate` per tenant; alert if rate drops by >30% within a 1-hour window.

**Mitigation/Recovery:**
- Channel disable requires confirmation modal listing: "X learners will stop receiving deadline reminders. Alternative channel required."
- Fall back to in-app notifications automatically when email is disabled; mark in-app alerts as high priority.
- Tenant admin receives a weekly digest of suppressed notifications so they can assess impact.
- Certificates are delivered via in-app notification and downloadable from the learner dashboard regardless of email channel state.

---

## 4. Live Session Reschedule Notification Sent <30 Minutes Before Session

**Failure Mode:** An instructor reschedules a live session at 1:35 PM for a session originally at 2:00 PM. The notification system dispatches the reschedule alert, but 40% of enrolled learners do not receive it in time to join the new session time (especially if it moved earlier).

**Impact:** Learners miss the live session; instructor has low attendance; learners who miss may not be able to make up the session if it is not recorded, impacting their certification eligibility.

**Detection:**
- Alert when `reschedule_notification_sent_at - new_session_time < 1800 seconds` (within 30 minutes of the session).
- Track `session_attendance_rate` post-reschedule; alert if attendance drops >30% compared to historical average for the same course.

**Mitigation/Recovery:**
- Block reschedule if `new_session_time - now < 3600` (within 1 hour); require admin override with mandatory notification confirmation.
- For late reschedules: send multi-channel alert (email + in-app + SMS if configured) immediately; mark the session's calendar invite as updated.
- Policy: learners who miss a session due to a reschedule notified <2 hours in advance are granted automatic attendance credit or a re-sit opportunity.

---

## 5. Certificate Issued but Notification Provider Returns 5xx

**Failure Mode:** The certificate record is created and `certificate.state = ISSUED`. The notification service calls the ESP `POST /messages` endpoint and receives `503 Service Unavailable`. The retry queue exhausts 5 retries over 30 minutes and drops the job. The learner never receives their certificate email.

**Impact:** Learner does not know they earned a certificate; may not download it for job applications or compliance records. Support ticket load increases.

**Detection:**
- Alert on `notification_delivery_failed` events with `final_state = EXHAUSTED` (all retries consumed).
- Monitor ESP error rate: alert if `5xx_rate > 1%` over a 5-minute window.
- Daily report: `SELECT COUNT(*) FROM certificates WHERE state = 'ISSUED' AND notification_sent = false AND issued_at < NOW() - INTERVAL '1 hour'`.

**Mitigation/Recovery:**
- Retry with exponential backoff (1 s, 2 s, 4 s, 8 s, 16 s); after exhaustion, route to a dead-letter queue for manual inspection.
- Learner can always access and download their certificate from the "My Certificates" dashboard regardless of email delivery state.
- Daily recovery job: scan `certificates WHERE notification_sent = false AND issued_at < NOW() - INTERVAL '1 hour'`; re-queue notification.

---

## 6. Notification Template Renders to Null Field Crash

**Failure Mode:** A grade notification template contains `{{ learner.preferred_name }}`. A learner record has `preferred_name = null` (field introduced after the learner was created). The template engine throws a `NullReferenceException`; the entire notification batch fails, leaving all learners in the batch without grade notifications.

**Impact:** All learners in the notification batch (potentially hundreds) do not receive grade notifications. The error may go unnoticed if the template engine silently swallows the exception.

**Detection:**
- Alert on `template_render_error` events; surface template name, field name, and affected `notification_job_id`.
- Monitor `notification_batch_failed` counter; alert on any non-zero count.
- Template validation test: run each template against a learner record with all nullable fields set to null before deployment.

**Mitigation/Recovery:**
- Template engine uses safe navigation: `{{ learner.preferred_name | default: learner.first_name }}` — falls back to a non-null field.
- Template deployment pipeline: run a rendering smoke test with null-filled fixtures; reject templates that throw on null inputs.
- If a batch fails mid-send: re-queue failed notifications with a patched template; do not re-send notifications already successfully delivered.

---

## 7. Notification Storm: 500 Learners Complete Course Simultaneously

**Failure Mode:** A deadline-driven course has 500 learners submit their final assessment within a 10-minute window. Each completion triggers an individual certificate email. The ESP receives 500 requests/minute, exceeding the tenant's rate limit (200/minute). The ESP returns `429 Too Many Requests`; notifications queue up and are delayed by 40+ minutes.

**Impact:** Certificate emails are delayed; learners who need certificates for same-day compliance reporting are blocked. ESP rate-limit violations may result in account suspension.

**Detection:**
- Monitor ESP `429` response rate; alert if `429_rate > 5%` over a 2-minute window.
- Track `notification_delivery_latency_p95`; alert if > 10 minutes for certificate notifications (SLO = 5 minutes).

**Mitigation/Recovery:**
- Batch certificate emails into groups of 50–100 using a delayed batch aggregation window (2 minutes); send with ESP bulk endpoint.
- Implement token-bucket rate limiter per tenant in the notification dispatcher; queue excess notifications for smooth delivery.
- For burst events (course deadlines, cohort completions), allow pre-planned "bulk send" jobs that bypass the per-event pipeline and use the ESP bulk API directly.

---

## 8. Unsubscribe Request Not Honored Within Legally Required Timeframe

**Failure Mode:** A learner clicks "unsubscribe" in an email. The unsubscribe webhook is received but the preference update is queued behind 10,000 other preference operations and is not processed for 48 hours. During that window, the learner receives 3 additional emails. CAN-SPAM/GDPR requires processing within 10 business days (CAN-SPAM) but best practice is 24–48 hours.

**Impact:** Legal/compliance risk: regulators can fine up to $50,120 per CAN-SPAM violation. Learner trust is damaged.

**Detection:**
- Alert on `unsubscribe_queue_lag > 3600` seconds (>1 hour unprocessed).
- Monitor `emails_sent_after_unsubscribe`: alert immediately on any occurrence.
- Daily audit: `SELECT COUNT(*) FROM email_sends e JOIN unsubscribes u ON e.learner_id = u.learner_id WHERE e.sent_at > u.unsubscribed_at`.

**Mitigation/Recovery:**
- Unsubscribe writes are processed with highest priority; bypass normal queue, write directly to `email_preferences` in the primary DB synchronously.
- Pre-send check: all outgoing emails are gated on a real-time `email_preferences` lookup; never read from a potentially stale cache for suppression checks.
- Unsubscribe confirmations are sent immediately via the same email; provide re-subscribe link and preference center URL.

---

## 9. Notification Sent to Deactivated Learner Account

**Failure Mode:** A learner's account is deactivated by their employer (SCIM-provisioned tenant). A background notification job that was enqueued before deactivation fires 4 hours later and sends a grade notification email. The email is sent to an address the learner may no longer control (corporate email deprovisioned by the employer).

**Impact:** PII sent to a potentially deprovisioned mailbox; possible data privacy incident. Former employee receives work communications after leaving.

**Detection:**
- Pre-send account status check: query `accounts.state` at send time (not at enqueue time); skip send if `state = DEACTIVATED`.
- Alert on `notification_sent_to_inactive_account` events.
- Daily audit: `SELECT COUNT(*) FROM notification_sends WHERE sent_at > (SELECT deactivated_at FROM accounts WHERE id = learner_id)`.

**Mitigation/Recovery:**
- Notification dispatcher performs a real-time account status check before every send (not just at job creation).
- On deactivation, cancel all pending notification jobs for the learner in the notification queue.
- Retain the notification record in `notification_history` as suppressed for audit purposes.

---

## 10. Push Notification with Deadline Arrives After Deadline Has Passed

**Failure Mode:** A push notification reminding a learner of a course deadline at 5 PM is enqueued at 4:30 PM. Due to FCM/APNs delivery delays and device inactivity, the notification is delivered at 5:45 PM — 45 minutes after the deadline.

**Impact:** The notification is useless and confusing; learner opens the app to find the deadline has passed. Learner may lose motivation or trust in the platform's communication reliability.

**Detection:**
- Track `notification_received_after_deadline` events: log `deadline_at`, `notification_sent_at`, and `notification_delivered_at` (via read receipt if available).
- Alert if `delivered_at - deadline_at > 0` for deadline-related notifications.

**Mitigation/Recovery:**
- Set a notification expiry (`time_to_live`) on all deadline-reminder push notifications equal to the time remaining before the deadline.
- If TTL = 0 at delivery time (deadline already passed), FCM/APNs will not deliver the notification.
- Scheduling logic: do not enqueue deadline reminders if `deadline_at - now < 900` seconds (15 minutes); the window is too narrow to be useful.
- Provide learners with a "Upcoming Deadlines" widget in the app that shows live countdowns regardless of push notification delivery.
| Grade published before feedback artifacts are ready | Learner sees incomplete outcome | Delay learner notification until publication bundle is complete |
| Tenant disables some channels mid-course | Message delivery becomes inconsistent | Respect tenant-level preferences with fallback-channel rules |
| Live session rescheduled close to start time | Learners miss session | Escalate urgent schedule-change notifications across multiple channels |
| Certificate issued but notification provider fails | Learner unaware of completion | Retry asynchronously and surface in-app status regardless of email delivery |


## Implementation Details: Notification Reliability

- Notification intent is written transactionally before provider dispatch.
- Deduplicate sends by recipient+template+context hash over policy window.
- For provider outages, show in-app fallback notices for critical events.
