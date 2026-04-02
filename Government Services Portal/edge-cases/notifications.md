# Edge Cases — Notifications

This document catalogues edge cases for the notification subsystem of the Nepal Government Services Portal. The portal delivers notifications to citizens and officers via three channels: **SMS** (Nepal Telecom / Ncell / Sparrow SMS gateway), **email** (AWS SES), and **in-app notifications** (real-time via WebSocket and persistent via the notification inbox). Notifications are triggered by Celery tasks in response to application state transitions, payment events, officer actions, and scheduled reminders. All Nepali-language SMS templates use UTF-8 Devanagari encoding. Edge cases below cover delivery failures, language errors, race conditions, and reliability hazards in the notification pipeline.

---

## Summary Table

| ID | Title | Component | Severity |
|---|---|---|---|
| EC-NOTIF-001 | SMS OTP delivery failure (NID-linked Nepal Telecom/Ncell number inactive/ported) | SMS Gateway / OTP | Critical |
| EC-NOTIF-002 | Email notification bounce for invalid address | Email / AWS SES | Medium |
| EC-NOTIF-003 | Notification sent in wrong language (Nepali/English preference not applied) | Notification Service / i18n | Medium |
| EC-NOTIF-004 | Duplicate notifications due to Celery retry | Celery / Idempotency | High |
| EC-NOTIF-005 | Notification sent before application status committed to DB (race condition) | Notification Service / DB | High |
| EC-NOTIF-006 | SMS gateway (Sparrow SMS) rate limit exceeded during mass broadcast | SMS Gateway / Rate Limiting | High |
| EC-NOTIF-007 | In-app notification count mismatch after concurrent read | In-App / WebSocket | Low |
| EC-NOTIF-008 | Certificate issuance notification sent but certificate generation failed | Notification Service / Certificate | High |

---

## Edge Cases

---

### EC-NOTIF-001: SMS OTP Delivery Failure (NID-Linked Nepal Telecom/Ncell Number Inactive or Ported)

| Field | Details |
|---|---|
| **Failure Mode** | A citizen registered their account with a phone number that is NID-linked at NASC. The phone number was originally on Nepal Telecom (NT) but the citizen has since ported to Ncell, or the number has been deactivated (SIM not recharged for 90+ days, causing auto-deactivation by the operator). The portal sends an SMS OTP via Sparrow SMS gateway, routing to Nepal Telecom's SMS centre. Nepal Telecom's SMSC accepts the message but cannot deliver it (number ported or inactive) and returns a `UNDELIVERED` delivery report after a 30-second timeout. The citizen never receives the OTP and cannot log in or complete the application. |
| **Impact** | The citizen is locked out of the portal. Any time-sensitive action — completing an application before a deadline, verifying a payment, or downloading a certificate — is blocked. For rural citizens who may have ported networks due to coverage, this is a significant accessibility barrier. The OTP failure rate also impacts the portal's onboarding conversion rate. |
| **Detection** | Sparrow SMS delivery report callback: `status=UNDELIVERED` or `status=REJECTED`. OTP delivery failure rate alarm: `sms_otp_undelivered_rate > 5% for 10 minutes` fires to `#ops-alerts`. Sentry alert on `SMSOTPDeliveryFailure` tagged with `reason=UNDELIVERED`. |
| **Mitigation / Recovery** | 1. On OTP delivery failure, the portal automatically retries via the alternate network route: if NT SMSC fails, retry through Ncell's SMSC integration (Sparrow SMS supports multi-route delivery). 2. If SMS fails on all routes: offer the citizen an alternative second factor — "Unable to deliver SMS to your registered number. Would you like to receive your OTP via email instead?" 3. If the citizen's number is permanently inactive: provide a "Update Phone Number" flow that requires the citizen to verify their NID at a government service centre and update their registered number through the offline channel. |
| **Prevention** | 1. Configure Sparrow SMS with **multi-route delivery**: primary route via NT SMSC; automatic failover to Ncell SMSC if the primary route returns `UNDELIVERED` within 15 seconds. 2. Implement an **email OTP fallback**: if SMS OTP fails twice, automatically send the OTP to the citizen's registered email address (if available) and display a user-friendly message. 3. At registration time, send a test SMS to validate the phone number is reachable and warn the citizen if delivery fails. 4. Monthly check: identify accounts with 3+ consecutive OTP delivery failures and send an in-app notification prompting the citizen to verify their contact details. |

---

### EC-NOTIF-002: Email Notification Bounce for Invalid Address

| Field | Details |
|---|---|
| **Failure Mode** | A citizen registers with a mistyped email address (e.g., `ram.bahadur@gamil.com` instead of `gmail.com`). AWS SES accepts the message for delivery, attempts delivery, and receives a hard bounce from the recipient's mail server (550 No Such User). SES records the hard bounce and automatically adds the email address to SES's **bounce list** (suppression list). All subsequent emails to this address are suppressed by SES without delivery, including critical notifications (application approval, certificate ready, payment receipt). The citizen never receives any email and may not realise they have a wrong email on file. |
| **Impact** | The citizen misses critical application status updates and certificate-ready notifications. If the portal relies on email for account recovery (password reset, OTP fallback), the citizen is also locked out of account recovery. At scale, a high bounce rate damages the portal's SES sending reputation and may cause SES to throttle or suspend the portal's sending capability, affecting all citizens. |
| **Detection** | AWS SES bounce notification delivered to the bounce SNS topic → Lambda → `update_email_status` function that marks the citizen's `email_bounced=True` in the database. CloudWatch metric `SES BounceRate > 2%` alarm (SES best practice threshold). Monthly bounce report reviewed by the operations team. |
| **Mitigation / Recovery** | 1. When SES reports a hard bounce, immediately set `citizen.email_status='BOUNCED'` in the database. 2. Send an SMS notification to the citizen's phone: "Your email address on govportal.gov.np could not be reached. Please log in to update your email address at [URL]." 3. Disable all future email sends to the bounced address (respect the SES suppression list). 4. For the immediate missed notification: re-deliver via SMS if the content is short enough (e.g., "Your application #12345 has been approved. Log in to download your certificate."). |
| **Prevention** | 1. Implement **email verification at registration**: send a verification email with a confirmation link; the email is not used for notifications until verified. This catches typos at the point of entry. 2. Show a real-time email format validator in the registration form (checks for valid domain + MX record lookup). 3. Process SES bounce notifications in real-time via SNS→Lambda and update the database within 60 seconds of a bounce report. 4. Maintain a **notification channel priority**: if email is bounced, always send via SMS (primary channel for Nepal, where mobile penetration is higher). |

---

### EC-NOTIF-003: Notification Sent in Wrong Language (Nepali/English Preference Not Applied)

| Field | Details |
|---|---|
| **Failure Mode** | A citizen sets their language preference to **Nepali (नेपाली)** in their profile settings. When the application is approved, the `send_approval_notification` Celery task is enqueued with `application_id` as the only argument. The task fetches the citizen's language preference from the database inside the task body. However, due to a Django ORM query issue (the `citizen.language_preference` field is not in the `select_related()` chain and defaults to `None`), the task falls back to English. The citizen receives an English-language SMS and email instead of their preferred Nepali. For citizens with limited English literacy — common in rural areas of Nepal — this notification is unintelligible. |
| **Impact** | Citizen cannot understand the notification. They call the support helpline, increasing support load. Rural citizens and elderly citizens with Nepali-only literacy are disproportionately affected, which is an accessibility and equity issue for a government portal. |
| **Detection** | Manual audit: a weekly sample of 50 notifications is reviewed to check language correctness. Citizen complaints logged in the support ticketing system tagged with `wrong_language`. Integration test failure: the notification test suite includes a test that verifies Devanagari characters appear in SMS body when `language_preference='ne'`. |
| **Mitigation / Recovery** | 1. Resend the notification in the correct language by re-queuing the task with the corrected language preference. 2. Fix the `select_related()` query to always include `language_preference`. 3. Audit the last 30 days of notifications: identify all `language_preference='ne'` citizens who received English notifications and re-send the most recent critical notification (approval/rejection/certificate-ready) in Nepali. |
| **Prevention** | 1. Pass the language preference **explicitly** as a task argument (not fetched inside the task): `send_approval_notification.delay(application_id=app.id, language='ne')`. This prevents any ORM query issues inside the task from affecting the language. 2. Add a database constraint: `citizen.language_preference NOT NULL DEFAULT 'ne'` (default to Nepali since Nepal is the primary locale). 3. Write a test that verifies Devanagari content in the SMS body for `language='ne'` in the notification integration test suite. 4. In the Celery task, if `language` is `None` or missing, default to `'ne'` (not `'en'`). |

---

### EC-NOTIF-004: Duplicate Notifications Due to Celery Retry

| Field | Details |
|---|---|
| **Failure Mode** | The `send_status_update_notification` Celery task successfully sends an SMS via Sparrow SMS and successfully sends an email via AWS SES. It then attempts to update the `NotificationLog` database record from `SENDING` to `SENT`. The database write fails with a transient `OperationalError` (e.g., connection pool timeout). The Celery task's `except` block does not distinguish between "notification sent but DB write failed" and "notification not sent". It retries the entire task. On the next retry, the task sends the SMS and email again (second time), then successfully writes `SENT` to the DB. The citizen receives duplicate notifications — two identical SMS messages and two identical emails. |
| **Impact** | Citizen confusion and annoyance from duplicate messages. For time-sensitive notifications (e.g., "You have 24 hours to respond to a clarification request"), duplicates may cause citizens to panic or double-respond. At scale, during a Celery retry storm (e.g., during a DB overload event), hundreds or thousands of citizens receive duplicate notifications simultaneously, damaging trust in the portal. |
| **Detection** | Duplicate notification detected in `notification_logs`: two records with the same `(citizen_id, application_id, notification_type, created_at_date)`. Sparrow SMS delivery reports show two messages to the same number in the same minute. Citizen support tickets tagged `duplicate_notification`. |
| **Mitigation / Recovery** | 1. Implement an idempotency check at the start of every notification task: check Redis for a key `notification_sent:{notification_type}:{application_id}:{citizen_id}:{date}`. If the key exists, skip sending and return immediately. 2. For already-sent duplicates: add a public notice to the portal's announcement banner if the duplicate affected a large number of citizens. No action is needed per-citizen unless the duplicate caused material harm. |
| **Prevention** | 1. **Split the notification task into two phases**: (a) `reserve_notification_slot` — write a `NotificationLog(status='RESERVED')` record in an atomic DB transaction using `get_or_create` with an idempotency key. (b) Only proceed to send SMS/email if the `get_or_create` returned `created=True`. If `created=False`, the notification was already sent or reserved — skip. (c) After sending: update the record to `SENT`. 2. Use a Redis idempotency key as an additional guard: `SET notif:{idempotency_key} "1" NX EX 86400`. 3. Set `acks_late=True` on notification tasks to prevent message re-delivery on worker crash when the notification was already sent. |

---

### EC-NOTIF-005: Notification Sent Before Application Status Committed to DB (Race Condition)

| Field | Details |
|---|---|
| **Failure Mode** | The officer approval endpoint executes the following sequence inside a `transaction.atomic()` block: (1) update `application.status = 'APPROVED'`, (2) create a `WorkflowStep` audit record, (3) emit `application_state_changed` Django signal. The signal handler for `application_state_changed` immediately enqueues a `send_approval_notification` Celery task. The task begins executing on a Celery worker **before the Django transaction commits** (Celery tasks enqueued inside a transaction may start before the transaction is committed if the broker receives the task message before the DB commit). The Celery task fetches the application from the DB and sees `status='UNDER_REVIEW'` (the old status, because the transaction has not yet committed). The task sends a notification saying "Your application is under review" instead of "Your application has been approved." |
| **Impact** | The citizen receives an incorrect notification at a critical moment (approval). They log into the portal and see "Approved" (because by then the transaction has committed), but their SMS/email said "Under Review". This is confusing and erodes trust. Worse: if the task sends an "Approved" notification (optimistically, before DB commit) but the transaction rolls back due to a subsequent error, the citizen receives a false approval notification. |
| **Detection** | Notification content mismatch detected in integration tests: a test that sends an approval and captures the notification content asserts the correct status. Citizen support tickets: "My SMS says approved but the portal says something different." |
| **Mitigation / Recovery** | 1. Pass the new status explicitly as a task argument: `send_approval_notification.delay(application_id=app.id, new_status='APPROVED', language='ne')`. The task uses the passed status rather than re-fetching from DB. 2. For the more dangerous case (pre-commit notification): use `transaction.on_commit()` to enqueue the Celery task only after the DB transaction commits successfully. |
| **Prevention** | 1. **Always use `transaction.on_commit()` for notification task enqueuing**: `transaction.on_commit(lambda: send_approval_notification.delay(application_id=app.id, new_status='APPROVED'))`. This guarantees the task is only enqueued if the transaction commits. If the transaction rolls back, the task is never sent. 2. **Pass state as task arguments**: do not re-fetch the status from the DB inside the notification task. Use the state that was confirmed at the time the task was enqueued. 3. Add a smoke test to the CI pipeline: enqueue a notification task inside a transaction that is then rolled back; assert that no notification is sent. |

---

### EC-NOTIF-006: SMS Gateway (Sparrow SMS) Rate Limit Exceeded During Mass Broadcast

| Field | Details |
|---|---|
| **Failure Mode** | The portal's Super Admin uses the "Mass Notification" feature to send an SMS announcement to all 50,000 active citizens about a new welfare scheme. The `send_mass_notification` Celery task generates 50,000 individual SMS API calls to Sparrow SMS in rapid succession. Sparrow SMS imposes a rate limit of 100 messages per second per account. The portal's implementation does not implement rate limiting or batching, and submits all 50,000 messages within 30 seconds. Sparrow SMS rejects messages above the rate limit with HTTP 429 (`Too Many Requests`). 35,000 of the 50,000 messages are rejected and never delivered. The portal's Celery worker logs 35,000 `SparrowSMSRateLimitError` exceptions. |
| **Impact** | 70% of citizens do not receive the announcement. If the announcement is time-sensitive (e.g., a subsidy scheme with a registration deadline), affected citizens may miss the opportunity. The mass notification feature is effectively unreliable. Sparrow SMS may temporarily suspend the portal's account if rate limit violations are persistent. |
| **Detection** | Sparrow SMS HTTP 429 response spike in Sentry. `sms_rejected_rate` CloudWatch metric alarm. Mass notification task completion report (available in the Admin panel) shows `delivered=15000 / 50000`. |
| **Mitigation / Recovery** | 1. Cancel the current mass notification Celery task group. 2. Re-queue the rejected 35,000 messages using a rate-limited Celery task: use `celery_throttle` or a custom Redis token bucket to send at 80 messages/second (20% below the limit for safety margin). 3. Estimate completion time: 35,000 / 80 = ~437 seconds (~7 minutes). Monitor the `notification_logs` table for delivery confirmation. |
| **Prevention** | 1. Implement a **Redis token bucket rate limiter** for all outbound SMS sends: `RATE_LIMIT_PER_SECOND = 80`. The `send_sms` service checks the token bucket before each API call and sleeps if the bucket is empty. 2. Use Celery **canvas** with a `chord` + `rate_limit` per-task setting: `send_sms_task.s(phone, message).set(rate_limit='80/s')`. 3. Implement SMS **batching**: Sparrow SMS supports batch submission (up to 100 numbers per API call); use the batch endpoint to submit 100 numbers per HTTP request, reducing API call volume by 100×. 4. Add a mass notification preview step in the Admin panel that shows estimated delivery time based on the rate limit and recipient count before sending. |

---

### EC-NOTIF-007: In-App Notification Count Mismatch After Concurrent Read

| Field | Details |
|---|---|
| **Failure Mode** | A citizen opens the portal on two browser tabs simultaneously. Both tabs show the notification bell with the same unread count (e.g., 3 unread). The citizen clicks the notification in Tab 1, which marks all notifications as read via `PATCH /api/v1/notifications/mark-all-read/` and updates the bell to 0. Simultaneously, Tab 2's polling mechanism (polling every 30 seconds) fetches the unread count and still receives 3 (the DB update from Tab 1 has not propagated to the Redis cache that the count endpoint reads from). Tab 2 still shows 3 unread. When the citizen clicks the bell in Tab 2, they see an empty notification list (all marked read) but the count badge still shows 3. |
| **Impact** | Minor UX inconsistency: the notification count badge shows a stale value. The citizen may repeatedly click the notification bell expecting to find unread items. This is a cosmetic issue with no data integrity or service impact. However, if not handled gracefully, it degrades the portal's perceived quality. |
| **Detection** | The mismatch is typically self-correcting within 30 seconds (the next polling cycle). No automated detection is required for this low-severity issue. It is captured in user feedback and UI testing sessions. |
| **Mitigation / Recovery** | 1. The notification list API (`GET /api/v1/notifications/`) always returns the accurate unread count from the database, not from cache. When the tab refreshes, the count corrects itself. 2. On the `mark-all-read` API response, include the new unread count (`{"unread_count": 0}`) in the response body. The frontend updates all open tabs via a `BroadcastChannel` API message (cross-tab synchronisation). |
| **Prevention** | 1. Implement **BroadcastChannel-based cross-tab sync** on the frontend: when `mark-all-read` succeeds in any tab, broadcast `{type: "NOTIFICATIONS_READ", unread_count: 0}` to all other tabs. All tabs update their bell counter on receipt. 2. Store the unread count in the DB (not Redis cache) as the source of truth. Use a short (5-second) cache TTL for the count endpoint; this bounds the maximum staleness. 3. Add a WebSocket push for notification count updates: when a new notification is created or notifications are marked as read, push the new count to all active sessions for that citizen. This eliminates polling entirely and makes the count always accurate. |

---

### EC-NOTIF-008: Certificate Issuance Notification Sent but Certificate Generation Failed

| Field | Details |
|---|---|
| **Failure Mode** | The officer approves an application. The workflow engine transitions the application from `APPROVED` to `CERTIFICATE_GENERATING` and enqueues two Celery tasks: `generate_certificate.delay(application_id)` and `send_certificate_ready_notification.delay(application_id)`. Due to task scheduling non-determinism in Celery, the `send_certificate_ready_notification` task executes first (within seconds). It sends the citizen an SMS: "अभिनन्दन! तपाईंको सिटिजनशिप प्रमाणपत्र तयार छ। डाउनलोड गर्नुहोस्: [link]" ("Congratulations! Your citizenship certificate is ready. Download here: [link]"). The citizen clicks the link. Meanwhile, `generate_certificate` fails (e.g., due to a Jinja2 template error for that specific district). The download link returns HTTP 404 (no PDF in S3). |
| **Impact** | The citizen receives a "certificate ready" notification, clicks the link immediately, and finds no certificate. This is a severe UX failure: the citizen believes their application was approved and their certificate is available, but they cannot download it. Trust in the portal is severely damaged. For time-sensitive certificates (e.g., business registration for a deadline), this is a P1 incident. |
| **Detection** | The citizen clicks the certificate download link and receives HTTP 404. Download error rate spike on the certificate endpoint in CloudWatch. Sentry: `CertificateNotFoundError` logged when the download is attempted. The `generate_certificate` task's Sentry error is correlated with the notification sent for the same `application_id`. |
| **Mitigation / Recovery** | 1. Immediately enqueue a retry of `generate_certificate` for the failed application. 2. Send a corrective SMS: "We apologise — your certificate link encountered an issue. It will be ready within the next 30 minutes. We will notify you again once it is available." 3. Monitor the retry; once successful, re-send the "certificate ready" notification with the correct link. 4. Add a `certificate_id` null check to the download endpoint: if no certificate exists for the application, return HTTP 202 with body `{"status": "generating", "estimated_ready_in_minutes": 15}` rather than HTTP 404. |
| **Prevention** | 1. **Never send a "certificate ready" notification before the certificate exists in S3.** Redesign the task ordering: (a) `generate_certificate` runs first and completes; (b) Only after a successful S3 upload does `generate_certificate` enqueue the `send_certificate_ready_notification` task. Remove `send_certificate_ready_notification` from the workflow engine's direct task list. 2. Use a Celery **chain**: `(generate_certificate.s(application_id) | send_certificate_ready_notification.s()).delay()`. In a chain, the second task only runs if the first completes successfully. 3. The `send_certificate_ready_notification` task must receive the `s3_key` as an argument (returned by `generate_certificate`), and validate that the S3 object exists (`s3.head_object(...)`) before sending the notification. If the S3 object doesn't exist, delay by 60 seconds and retry. |

---

## Appendix: Configuration and Code Snippets

### Celery Task Idempotency (Notification Deduplication)

```python
# apps/notifications/tasks.py
import hashlib
from celery import shared_task
from django.core.cache import cache
from django.db import transaction

def _build_idempotency_key(notification_type: str, application_id: str, citizen_id: str) -> str:
    raw = f"{notification_type}:{application_id}:{citizen_id}"
    return f"notif_sent:{hashlib.sha256(raw.encode()).hexdigest()}"

@shared_task(
    bind=True, acks_late=True, max_retries=3, default_retry_delay=30,
    queue='notifications', name='notifications.send_status_update'
)
def send_status_update_notification(
    self, application_id: str, new_status: str, citizen_id: str, language: str = 'ne'
):
    """
    Sends an SMS + email notification for an application status update.
    Fully idempotent: safe to retry without producing duplicate notifications.
    """
    idem_key = _build_idempotency_key('status_update', application_id, citizen_id)

    # Check Redis idempotency key (fast path)
    if cache.get(idem_key):
        logger.info("Notification already sent for key %s, skipping.", idem_key)
        return {'status': 'skipped', 'reason': 'already_sent'}

    try:
        with transaction.atomic():
            log, created = NotificationLog.objects.get_or_create(
                idempotency_key=idem_key,
                defaults={
                    'application_id': application_id,
                    'citizen_id': citizen_id,
                    'notification_type': 'status_update',
                    'status': 'SENDING',
                }
            )
            if not created:
                return {'status': 'skipped', 'reason': 'db_record_exists'}

        # Send notifications outside the transaction
        citizen = Citizen.objects.get(id=citizen_id)
        template = NotificationTemplate.get(
            notification_type='status_update',
            new_status=new_status,
            language=language,
        )

        sms_result = SparrowSMS.send(
            to=citizen.phone_number,
            message=template.sms_body,
        )
        email_result = AWSEmail.send(
            to=citizen.email,
            subject=template.email_subject,
            body=template.email_body,
        )

        log.status = 'SENT'
        log.sms_message_id = sms_result.message_id
        log.email_message_id = email_result.message_id
        log.save(update_fields=['status', 'sms_message_id', 'email_message_id'])

        # Set Redis idempotency key to prevent future duplicates (24-hour TTL)
        cache.set(idem_key, '1', timeout=86400)

        return {'status': 'sent'}

    except Exception as exc:
        logger.error("Notification task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
```

### Sparrow SMS Integration with Rate Limiter

```python
# apps/notifications/sms_gateway.py
import time
import redis
from dataclasses import dataclass
from django.conf import settings
import requests

@dataclass
class SMSResult:
    success: bool
    message_id: str | None
    error: str | None

class SparrowSMSGateway:
    """
    Sparrow SMS gateway client with Redis-backed token bucket rate limiter.
    Rate limit: 80 messages/second (20% below the 100/s Sparrow SMS limit).
    """
    BASE_URL = 'https://api.sparrowsms.com/v2'
    RATE_LIMIT_KEY = 'sparrow_sms_rate_limit'
    MAX_TOKENS = 80  # per second
    REFILL_RATE = 80  # tokens per second

    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.token = settings.SPARROW_SMS_TOKEN

    def _acquire_token(self) -> None:
        """Blocks until a rate limit token is available."""
        while True:
            tokens = self.redis.incr(self.RATE_LIMIT_KEY)
            if tokens == 1:
                self.redis.expire(self.RATE_LIMIT_KEY, 1)  # Reset every second
            if tokens <= self.MAX_TOKENS:
                return
            time.sleep(0.01)  # 10ms wait before retry

    def send(self, to: str, message: str) -> SMSResult:
        """
        Sends a single SMS. Enforces rate limiting.
        Supports UTF-8 Devanagari encoding for Nepali language messages.
        """
        self._acquire_token()
        try:
            response = requests.post(
                f'{self.BASE_URL}/sms/',
                json={
                    'token': self.token,
                    'from': settings.SPARROW_SMS_FROM,
                    'to': to,
                    'text': message,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return SMSResult(
                success=data.get('response_code') == 200,
                message_id=data.get('message_id'),
                error=data.get('message') if data.get('response_code') != 200 else None,
            )
        except requests.RequestException as e:
            return SMSResult(success=False, message_id=None, error=str(e))
```

### Notification Template Examples (Nepali and English)

```python
# apps/notifications/templates/status_update.py

TEMPLATES = {
    ('status_update', 'APPROVED', 'ne'): {
        'sms_body': (
            "अभिनन्दन! तपाईंको {service_name} आवेदन (सन्दर्भ: {application_ref}) "
            "स्वीकृत भएको छ। प्रमाणपत्र डाउनलोड गर्न: {portal_url}/applications/{application_id}/certificate/"
        ),
        'email_subject': "तपाईंको आवेदन स्वीकृत भयो — {service_name}",
        'email_body': (
            "प्रिय {citizen_name},\n\n"
            "तपाईंको {service_name} आवेदन (सन्दर्भ नम्बर: {application_ref}) "
            "सरकारी सेवा पोर्टलद्वारा स्वीकृत गरिएको छ।\n\n"
            "प्रमाणपत्र डाउनलोड गर्नुहोस्: {certificate_url}\n\n"
            "नेपाल सरकार सेवा पोर्टल"
        ),
    },
    ('status_update', 'APPROVED', 'en'): {
        'sms_body': (
            "Congratulations! Your {service_name} application (Ref: {application_ref}) "
            "has been approved. Download certificate: {portal_url}/applications/{application_id}/certificate/"
        ),
        'email_subject': "Your Application Approved — {service_name}",
        'email_body': (
            "Dear {citizen_name},\n\n"
            "Your {service_name} application (Reference: {application_ref}) "
            "has been approved by the Nepal Government Services Portal.\n\n"
            "Download your certificate: {certificate_url}\n\n"
            "Nepal Government Services Portal"
        ),
    },
    ('status_update', 'REJECTED', 'ne'): {
        'sms_body': (
            "खेद छ! तपाईंको {service_name} आवेदन (सन्दर्भ: {application_ref}) "
            "अस्वीकृत भएको छ। कारण: {rejection_reason}। "
            "पुनः आवेदन गर्न: {portal_url}"
        ),
        'email_subject': "तपाईंको आवेदन अस्वीकृत भयो — {service_name}",
        'email_body': (
            "प्रिय {citizen_name},\n\n"
            "दुर्भाग्यवश, तपाईंको {service_name} आवेदन (सन्दर्भ: {application_ref}) "
            "अस्वीकृत भएको छ।\n\n"
            "कारण: {rejection_reason}\n\n"
            "थप जानकारीको लागि: {portal_url}/applications/{application_id}/\n\n"
            "नेपाल सरकार सेवा पोर्टल"
        ),
    },
    ('status_update', 'REJECTED', 'en'): {
        'sms_body': (
            "Sorry, your {service_name} application (Ref: {application_ref}) "
            "was rejected. Reason: {rejection_reason}. "
            "To re-apply: {portal_url}"
        ),
        'email_subject': "Your Application Rejected — {service_name}",
        'email_body': (
            "Dear {citizen_name},\n\n"
            "Unfortunately, your {service_name} application (Reference: {application_ref}) "
            "has been rejected.\n\n"
            "Reason: {rejection_reason}\n\n"
            "For more information: {portal_url}/applications/{application_id}/\n\n"
            "Nepal Government Services Portal"
        ),
    },
    ('certificate_ready', 'CERTIFICATE_ISSUED', 'ne'): {
        'sms_body': (
            "तपाईंको {service_name} प्रमाणपत्र तयार छ। "
            "डाउनलोड गर्नुहोस्: {certificate_url} "
            "(म्याद: {expiry_date})"
        ),
        'email_subject': "प्रमाणपत्र तयार छ — {service_name}",
        'email_body': (
            "प्रिय {citizen_name},\n\n"
            "तपाईंको {service_name} प्रमाणपत्र अब डाउनलोडका लागि उपलब्ध छ।\n\n"
            "डाउनलोड: {certificate_url}\n"
            "वैधता समाप्त मिति: {expiry_date}\n\n"
            "यो प्रमाणपत्र सुरक्षित राख्नुहोस्।\n\n"
            "नेपाल सरकार सेवा पोर्टल"
        ),
    },
    ('certificate_ready', 'CERTIFICATE_ISSUED', 'en'): {
        'sms_body': (
            "Your {service_name} certificate is ready. "
            "Download: {certificate_url} "
            "(Valid until: {expiry_date})"
        ),
        'email_subject': "Certificate Ready — {service_name}",
        'email_body': (
            "Dear {citizen_name},\n\n"
            "Your {service_name} certificate is now available for download.\n\n"
            "Download: {certificate_url}\n"
            "Valid Until: {expiry_date}\n\n"
            "Please keep this certificate safe.\n\n"
            "Nepal Government Services Portal"
        ),
    },
}
```

### Celery Beat Schedule for Notification Tasks

```python
# settings/celery_beat.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Notification health checks and cleanup
    'cleanup-expired-notification-logs': {
        'task': 'notifications.cleanup_old_notification_logs',
        'schedule': crontab(hour=3, minute=0),  # 03:00 NST daily
        'kwargs': {'older_than_days': 90},
    },
    'retry-failed-notifications': {
        'task': 'notifications.retry_failed_notifications',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
        'kwargs': {'max_age_hours': 24},
    },
    'sla-breach-reminder-notifications': {
        'task': 'notifications.send_sla_breach_reminders',
        'schedule': crontab(hour=9, minute=0),  # 09:00 NST weekdays
    },
    'pending-clarification-reminders': {
        'task': 'notifications.send_clarification_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10:00 NST daily
        'kwargs': {'reminder_after_hours': 48},
    },
}
```

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policy

- Phone numbers and email addresses collected for notification purposes are used exclusively for sending notifications related to the citizen's own government service applications. They are never shared with third parties, used for marketing, or disclosed in any form.
- Notification content is kept minimal: it contains the application reference number, the service name, the status change, and a portal deep link. Sensitive personal details (NID numbers, full addresses, document contents) are never included in SMS or email notification bodies.
- Citizens may opt out of email notifications at any time via their profile settings. SMS notifications for application status changes are mandatory (they are part of the statutory service delivery obligation) and cannot be fully opted out, but citizens may opt out of marketing announcements.
- All notification logs (SMS delivery reports, email bounce records) are retained for 12 months for operational purposes, then purged.

### 2. Service Delivery SLA Policy

- Critical notifications (application approved, rejected, certificate ready, payment confirmed) must be delivered within **5 minutes** of the triggering event for 99% of citizens.
- SMS delivery is the primary channel for all SLA-critical notifications, given Nepal's high mobile penetration versus email access, particularly in rural areas.
- If the Sparrow SMS gateway is unavailable for more than 15 minutes, an automatic failover to the backup SMS provider (Nepal Telecom bulk SMS API) is activated.
- The portal must maintain notification delivery logs for all SLA-critical notifications, and the monthly SLA compliance report must include notification delivery success rates by channel (SMS, email, in-app).

### 3. Fee and Payment Policy

- Payment confirmation notifications (sent after ConnectIPS/eSewa/Khalti webhook is processed) must include the exact amount paid in NPR (रू), the transaction reference number, and the application reference number.
- Refund notifications must be sent via both SMS and email within 1 working day of the refund being processed, specifying the refund amount in NPR and the expected credit timeline (7 working days).
- No notification should ever state that a fee has been charged or a payment received unless the `PaymentTransaction` record in the database shows `status='COMPLETED'` and the amount has been verified against the fee snapshot.

### 4. System Availability Policy

- The Celery notification worker pool must maintain a minimum of 2 active workers at all times (monitored via Celery worker health-check in CloudWatch).
- The Sparrow SMS integration must be smoke-tested every 5 minutes via a synthetic monitor (a test message to a dedicated test number). If delivery fails for two consecutive checks, a P2 alert is raised and the backup SMS provider is activated.
- AWS SES sending quota utilisation is monitored daily. If utilisation exceeds 80% of the daily sending limit, the operations team requests a quota increase from AWS.
- The notification subsystem's Redis instance (used for idempotency keys and rate limiting) has Multi-AZ replication enabled. Redis failure falls back to database-only idempotency checks (no Redis dependency for correctness, only for performance).
