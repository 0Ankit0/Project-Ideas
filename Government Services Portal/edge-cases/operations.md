# Edge Cases — Operations & Reliability

This document catalogues operational and reliability edge cases for the Nepal Government Services Portal. Each case describes a failure mode that has been identified through architecture review, load testing, or production incident analysis. Cases are prioritised by severity and mapped to the component most likely to exhibit the failure. Runbook snippets and configuration examples are provided in the Appendix for on-call engineers.

---

## Summary Table

| ID | Title | Component | Severity |
|---|---|---|---|
| EC-OPS-001 | Celery worker crash during application processing | Celery / Task Queue | High |
| EC-OPS-002 | Database connection pool exhaustion during peak filing season | PostgreSQL / PgBouncer | Critical |
| EC-OPS-003 | ConnectIPS callback webhook arrives after application timeout | Payment / Webhook Handler | High |
| EC-OPS-004 | ECS task scaling lag during government scheme announcement surge | ECS Fargate / Auto-scaling | High |
| EC-OPS-005 | Redis cache invalidation failure with stale service fee data | Redis / Cache Layer | Medium |
| EC-OPS-006 | Scheduled batch certificate generation partial failure | Celery Beat / Certificate Service | High |
| EC-OPS-007 | NASC NID verification API degraded mode | NID Integration / Auth Service | Critical |
| EC-OPS-008 | Nepal Document Wallet (NDW) document fetch timeout | NDW Integration / Document Service | Medium |

---

## Edge Cases

---

### EC-OPS-001: Celery Worker Crash During Application Processing

| Field | Details |
|---|---|
| **Failure Mode** | A Celery worker processing a `generate_certificate` or `send_notification` task is killed mid-execution (OOM kill, SIGKILL during ECS task replacement, or an unhandled exception that is not caught by the task's retry decorator). The task is in the `STARTED` state in Redis but never transitions to `SUCCESS` or `FAILURE`. The application's status may have already been updated to `CERTIFICATE_GENERATING` in the database before the crash. |
| **Impact** | The citizen's application is stuck in `CERTIFICATE_GENERATING` state indefinitely. No certificate PDF is produced and no download link is available. The citizen sees an unresponsive "Processing" status in the portal. If the application involves a time-sensitive permit (e.g., business registration), this can block the citizen from proceeding. |
| **Detection** | Celery task visibility timeout alarm (CloudWatch alarm on `celery_task_unacked_count > 50 for 5 minutes`). Dead Letter Queue (DLQ) depth alarm on SQS DLQ for `certificate_queue`. Sentry alert for `WorkerLostError`. Periodic health check job (`check_stuck_applications` Celery Beat task, runs every 10 minutes) queries applications in `CERTIFICATE_GENERATING` for more than 30 minutes and raises a PagerDuty alert. |
| **Mitigation / Recovery** | 1. Identify stuck applications via `SELECT id, status, updated_at FROM applications WHERE status='CERTIFICATE_GENERATING' AND updated_at < NOW() - INTERVAL '30 minutes'`. 2. Re-enqueue the certificate generation task for each stuck application via the Admin panel (`Retry Certificate Generation` button on the Application Detail admin page). 3. If the admin action is unavailable, run the management command: `python manage.py retry_stuck_certificates --older-than-minutes=30`. 4. Monitor CloudWatch logs for the re-enqueued tasks to confirm completion. |
| **Prevention** | 1. Set `acks_late=True` on all critical Celery tasks so the message is only acknowledged after successful completion. 2. Set `task_reject_on_worker_lost=True` so the task is requeued if the worker dies. 3. Use task idempotency keys (stored in Redis with a 24-hour TTL) so re-enqueued tasks do not produce duplicate certificates. 4. Limit ECS task stop timeout to allow in-flight tasks to complete before container replacement. 5. Use `max_retries=5` with exponential backoff for all certificate generation tasks. |

---

### EC-OPS-002: Database Connection Pool Exhaustion During Peak Filing Season

| Field | Details |
|---|---|
| **Failure Mode** | At Nepal's fiscal year deadline (end of Ashadh / start of Shrawan, typically mid-July), a large number of citizens file applications simultaneously. The ECS auto-scaler adds new Django API tasks, but PgBouncer's `max_client_conn` limit is reached before the database connection pool is saturated. New API requests cannot acquire a database connection and fail with `OperationalError: FATAL: too many connections` or a PgBouncer `pool_mode=transaction` timeout. |
| **Impact** | All API endpoints requiring a database connection begin returning HTTP 503. Authentication, application submission, payment initiation, and status checks all fail simultaneously. This is a full-service outage affecting all citizens and officers. The impact is highest during the Ashadh filing deadline when demand may be 20–50× normal. |
| **Detection** | CloudWatch metric `RDS DatabaseConnections` approaching `max_connections` limit. PgBouncer metric `cl_waiting > 100` (more than 100 clients waiting for a connection). API error rate alarm: `5xx_rate > 5% for 2 minutes`. Django `OperationalError` spike in Sentry. |
| **Mitigation / Recovery** | 1. Immediately increase PgBouncer `max_client_conn` parameter and restart PgBouncer sidecars (rolling restart, no downtime). 2. Enable RDS Read Replica routing for read-heavy endpoints (application list, status check) to reduce primary DB load. 3. Scale down the number of ECS tasks to reduce concurrent connection demand if PgBouncer cannot be scaled fast enough. 4. Activate the "queue mode" feature flag which places citizens in a virtual queue and staggers request processing. |
| **Prevention** | 1. Capacity plan for Ashadh peak: 2× PgBouncer `max_client_conn` and 1.5× RDS instance size two weeks before fiscal year end. 2. Use PgBouncer `pool_mode=transaction` (not `session`) to maximise connection reuse. 3. Set `CONN_MAX_AGE=0` in Django to avoid holding idle connections open. 4. Implement connection pool metrics dashboard reviewed weekly. 5. Run an annual load test simulating Ashadh peak load in a staging environment in Jestha (two months before). |

---

### EC-OPS-003: ConnectIPS Callback Webhook Arrives After Application Timeout

| Field | Details |
|---|---|
| **Failure Mode** | A citizen initiates payment via ConnectIPS. The application's `payment_deadline` (set to 24 hours after payment initiation) expires and the system transitions the application to `PAYMENT_EXPIRED` via the `expire_stale_payments` Celery Beat task. Minutes later, the delayed ConnectIPS webhook arrives confirming `PAYMENT_SUCCESS`. The webhook handler attempts to transition the payment to `COMPLETED` and the application to `PAYMENT_VERIFIED`, but the application is now in the terminal `PAYMENT_EXPIRED` state. |
| **Impact** | The citizen's money has been deducted from their ConnectIPS/bank account but the application is marked expired. The citizen receives no approval. The payment is captured but not applied to any active application. This leads to a citizen complaint, a manual refund process, and reputational damage. |
| **Detection** | Payment webhook handler catches `InvalidStateTransitionError` when trying to move `PAYMENT_EXPIRED` application. This exception is caught, logged to Sentry with tag `payment_conflict=true`, and enqueued to the `payment_conflicts` SQS queue for manual review. A CloudWatch alarm fires if `payment_conflicts` queue depth exceeds 5. |
| **Mitigation / Recovery** | 1. Operations team reviews the `payment_conflicts` queue daily. 2. For each conflict: verify the ConnectIPS transaction ID against the ConnectIPS merchant dashboard to confirm the payment is genuine. 3. If genuine: reactivate the application by transitioning it back to `SUBMITTED` via the Admin panel, then re-apply the payment, and re-trigger the workflow to continue processing. 4. Notify the citizen via SMS and email explaining the delay and confirming their application is active. |
| **Prevention** | 1. Extend `payment_deadline` from 24 hours to 72 hours for ConnectIPS payments to accommodate delayed callbacks. 2. Before expiring an application, check with ConnectIPS API (polling endpoint) whether a payment was made against the order ID. Only expire if the API confirms no payment. 3. Implement a 30-minute grace window after the `payment_deadline` before running expiry: applications in `PAYMENT_PENDING` for up to 30 minutes past deadline are not expired until a secondary check is performed. 4. Store `gateway_order_id` separately from application status so it can always be looked up even after expiry. |

---

### EC-OPS-004: ECS Task Scaling Lag During Government Scheme Announcement Surge

| Field | Details |
|---|---|
| **Failure Mode** | The Government of Nepal announces a new subsidy scheme or welfare program via television/radio (common during public holidays or budget day). Thousands of citizens attempt to log in and submit applications simultaneously within a 5–10 minute window. ECS Auto Scaling reacts to CPU and request count metrics, but there is an inherent 2–5 minute lag between the metric breach and new tasks becoming healthy and in-service. During this lag, the load balancer target group has insufficient capacity and requests begin timing out or returning HTTP 502/503. |
| **Impact** | Citizens attempting to access the portal during the announcement surge experience slow responses, timeouts, or errors. This undermines trust in the government's digital services. Officers may also be unable to access their dashboards. If the scheme has a limited-seat enrollment (first-come-first-served), the scaling lag may prevent eligible citizens from registering. |
| **Detection** | ALB `TargetResponseTime_p99 > 3s for 1 minute` alarm. ALB `HTTPCode_Target_5XX_Count > 100 per minute` alarm. ECS `CPUUtilization > 85%` alarm with notification to #ops-alerts Slack channel. |
| **Mitigation / Recovery** | 1. Pre-scale: When a new scheme is known in advance (budget day, gazetted holidays), manually set ECS `desired_count` to 2× normal 30 minutes before the expected announcement. 2. If reacting to an unexpected surge: manually trigger a scale-out via the ECS console or the `scale_ecs.sh` runbook script. 3. Enable CloudFront caching for the scheme information page (informational, read-only) to absorb static content requests and reduce origin load. 4. Activate the application submission rate limiter (Redis token bucket, configurable per-minute limit) to prevent a single citizen from overwhelming the queue. |
| **Prevention** | 1. Maintain a "scheme launch runbook" that the communications team fills in 48 hours before any public announcement, triggering the ops team to pre-scale. 2. Configure Application Auto Scaling with a step scaling policy that reacts within 60 seconds of a metric breach (not 5-minute average). 3. Use target tracking scaling on `ALBRequestCountPerTarget` in addition to CPU. 4. Implement SQS-based submission buffering: application submissions are placed in a queue and processed asynchronously, decoupling the API from the database write latency during peaks. |

---

### EC-OPS-005: Redis Cache Invalidation Failure with Stale Service Fee Data (NPR Amounts)

| Field | Details |
|---|---|
| **Failure Mode** | A government administrator updates the fee schedule for a service (e.g., birth certificate fee changed from NPR 100 to NPR 200 as part of the annual budget). The fee schedule update triggers a `cache.delete('service_fee_{service_id}')` call. However, due to a Redis cluster failover or a network partition between the Django API server and the Redis cluster, the delete call fails silently (the exception is caught and logged but does not raise to the caller). Citizens are served the stale NPR 100 fee for up to the TTL duration (default 1 hour). |
| **Impact** | Citizens who initiate payment during the TTL window are charged the old fee (NPR 100 instead of NPR 200). When the ConnectIPS payment callback arrives with the amount matching the old fee, the payment amount validator rejects it as `AMOUNT_MISMATCH`. The citizen's payment is captured but not applied. Citizens receive confusing error messages and must contact support. Revenue leakage occurs for the government. |
| **Detection** | Payment amount mismatch errors spike in Sentry (`PaymentAmountMismatchError` tagged with `service_id`). Cache invalidation failure logged at `ERROR` level in CloudWatch Logs Insights. Admin activity log shows a fee update that was not followed by a cache invalidation confirmation event. |
| **Mitigation / Recovery** | 1. Immediately flush the affected service's cache keys: `redis-cli DEL service_fee_{service_id} service_detail_{service_id}`. 2. Identify all payments made during the stale window via `SELECT * FROM payments WHERE created_at BETWEEN fee_update_time AND cache_flush_time AND service_id = X AND status = 'FAILED' AND failure_reason = 'AMOUNT_MISMATCH'`. 3. For each affected payment: refund in full via ConnectIPS refund API; notify citizen via SMS with new correct fee amount; provide a direct payment link. |
| **Prevention** | 1. Fee schedule write operations must use a write-through cache pattern: the database update and cache delete are performed inside a transaction with a post-commit hook ensuring the cache delete is retried up to 3 times. 2. Set a maximum TTL of 15 minutes for fee data (not 1 hour). 3. Add a fee amount snapshot to the `ServiceApplication` record at submission time (already implemented per FR-FEE-003); this snapshot is used for payment validation, not the current cache. 4. Use `cache.set` (overwrite) in addition to `cache.delete` when updating fees: write the new value directly rather than relying on re-population on next miss. |

---

### EC-OPS-006: Scheduled Batch Certificate Generation Partial Failure

| Field | Details |
|---|---|
| **Failure Mode** | The `generate_daily_certificates` Celery Beat task runs nightly (02:00 NST) and processes all approved applications that have not yet had their PDF certificate generated. The task fetches a batch of 200 applications, spawns a Celery chord (`chord(generate_certificate.s(app_id) for app_id in batch) | batch_completion_callback.s()`). If 10 of the 200 tasks fail (e.g., PDF template rendering error for a specific district name with special Devanagari characters), the `chord` callback never fires (Celery chord requires all tasks to succeed for the callback to execute by default). The remaining 190 successfully generated certificates are never marked as complete in the database because the callback did not run. |
| **Impact** | 190 citizens have their PDFs generated in S3 but the database still shows `status=CERTIFICATE_GENERATING`. Citizens cannot download their certificates. The certificates are "orphaned" in S3. The nightly run the following night re-generates the same 190 PDFs (duplicate S3 objects). The 10 failed applications are not individually retried. |
| **Detection** | Celery Beat task completion time alarm: `generate_daily_certificates` must complete within 2 hours. If still running at 04:00 NST, PagerDuty alert fires. Sentry `ChordError` alert. Custom health check: `SELECT COUNT(*) FROM applications WHERE status='CERTIFICATE_GENERATING' AND approved_at < NOW() - INTERVAL '12 hours'` — if > 0, alert. |
| **Mitigation / Recovery** | 1. Switch from `chord` to individual task dispatching with a per-task completion callback that updates the DB record atomically. 2. Run the `retry_orphaned_certificates` management command: `python manage.py retry_orphaned_certificates --dry-run` first, then without `--dry-run`. 3. Manually update the 190 completed applications to link the S3 key: `python manage.py link_orphaned_certificates`. |
| **Prevention** | 1. Replace `chord` with a `group` + per-task `on_success` callback pattern so each certificate is independently committed to the database on success. 2. Use `chord_error` callback to handle partial failures and send individual retry tasks for each failed item. 3. Add per-item error handling: wrap each `generate_certificate` task in a try/except that catches rendering errors and writes a `CertificateGenerationError` record to the DB without blocking other items. 4. Validate all certificate templates against the full district/municipality name list in a nightly template smoke test. |

---

### EC-OPS-007: NASC NID Verification API Degraded Mode

| Field | Details |
|---|---|
| **Failure Mode** | The NASC (National Identity Management Centre) NID verification API (`https://nid.nasc.org.np/api/verify`) becomes intermittently unavailable or returns HTTP 503 / timeout errors. This API is called during citizen registration (NID number verification) and during officer login (identity re-verification for high-privilege actions). The circuit breaker (`pybreaker` library with threshold=5 failures in 60 seconds) trips to OPEN state, and all subsequent NID verification calls immediately return a `CircuitBreakerError` without reaching NASC. |
| **Impact** | New citizen registrations that require NID verification are blocked. Citizens with existing accounts can still log in if their NID was previously verified (stored in `citizens.nid_verified=True`). Officers attempting sensitive operations requiring re-verification (e.g., bulk certificate approval) are blocked. The portal's onboarding funnel is effectively paused. If NASC outage persists more than 4 hours during business hours, this constitutes a P1 incident. |
| **Detection** | Circuit breaker state change event logged to CloudWatch. Sentry alert on `CircuitBreakerError` with tag `service=nasc_nid`. External synthetic monitor (AWS Canary) polls the NASC NID verification endpoint every 5 minutes and publishes `nasc_nid_health` metric. PagerDuty P1 alert if `nasc_nid_health=0` for more than 15 consecutive minutes. |
| **Mitigation / Recovery** | 1. Activate the "Degraded Mode" feature flag in the Feature Flag service: `NASC_NID_DEGRADED_MODE=true`. In degraded mode: new citizen registrations are accepted with a `nid_verified=False` flag; citizens are informed that NID verification is temporarily unavailable and will be completed within 24 hours. 2. Notify NASC operations team via the emergency contact protocol (phone + email to `ops@nasc.org.np`). 3. Monitor the `nasc_nid_health` CloudWatch metric for recovery. 4. Once NASC recovers, run the `backfill_nid_verification` Celery task to verify all pending `nid_verified=False` registrations. |
| **Prevention** | 1. Implement a `NID_VERIFICATION_CACHE` in Redis: cache successful NID verifications for 30 days. On re-registration attempt, check cache before calling NASC. 2. Maintain a Memorandum of Understanding with NASC requiring advance notice of planned maintenance. 3. Request a dedicated NASC API quota for the portal to avoid being affected by other consumers. 4. Implement a secondary verification path using the citizen's phone number (OTP via Nepal Telecom / Sparrow SMS gateway) as a fallback when NASC is unavailable. |

---

### EC-OPS-008: Nepal Document Wallet (NDW) Document Fetch Timeout

| Field | Details |
|---|---|
| **Failure Mode** | A citizen initiates document pre-fill during application submission by authorising the portal to fetch documents from Nepal Document Wallet (NDW). The NDW OAuth token exchange succeeds and the portal calls the NDW document fetch API (`GET /api/v1/documents/{doc_type}`). The API call exceeds the 10-second timeout (configured in `NDW_API_TIMEOUT` setting) due to NDW infrastructure load or a large document file. The `requests.Timeout` exception is raised and bubbles up to the API view, returning HTTP 504 to the citizen's browser. |
| **Impact** | The citizen cannot use the "Auto-fill from NDW" feature. The application form remains empty and the citizen must manually enter information and upload documents. This degrades the user experience but does not prevent the citizen from completing their application. If the citizen is unaware they can proceed manually, they may abandon the application. |
| **Detection** | `requests.Timeout` exception in Sentry tagged with `integration=ndw`. CloudWatch metric `ndw_api_timeout_count` incremented per timeout. If `ndw_api_timeout_count > 50 per hour`, alert fires to `#integration-alerts` Slack channel. |
| **Mitigation / Recovery** | 1. The portal UI displays a user-friendly message: "Document pre-fill is temporarily unavailable. Please enter your information manually or try again in a few minutes." with a "Retry" button. 2. The retry button re-initiates the NDW OAuth flow. 3. Operations team monitors the CloudWatch dashboard for NDW timeout rate and contacts NDW operations if the rate is sustained. |
| **Prevention** | 1. Implement async document pre-fill: the portal initiates the NDW fetch in a Celery task after form load; the citizen sees a "Fetching your documents..." spinner and can proceed to fill the form manually. When the Celery task completes, it pushes the pre-filled data to the browser via a WebSocket or polling endpoint. The citizen can accept or reject the auto-filled data. 2. Set a per-document-type timeout (small docs: 5s, large PDFs: 15s). 3. Cache fetched NDW documents in S3 (with the citizen's consent) for 1 hour so repeat fetches within a session do not re-call the NDW API. |

---

## Appendix: Runbook Snippets and Configuration Examples

### Celery Retry Configuration

```python
# apps/certificates/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=5,
    default_retry_delay=60,  # seconds; exponential backoff applied below
    queue='certificate_queue',
)
def generate_certificate(self, application_id: str) -> dict:
    """
    Generates a PDF certificate for an approved application.
    Idempotent: if certificate already exists in S3 for this application,
    returns the existing S3 key without regenerating.
    """
    from apps.applications.models import ServiceApplication
    from apps.certificates.services import CertificateGeneratorService

    try:
        app = ServiceApplication.objects.select_for_update().get(id=application_id)
        result = CertificateGeneratorService.generate(app)
        return {"status": "success", "s3_key": result.s3_key}
    except CertificateGeneratorService.AlreadyGeneratedError as e:
        logger.info("Certificate already generated for %s: %s", application_id, e)
        return {"status": "already_exists", "s3_key": str(e)}
    except Exception as exc:
        retry_delay = 60 * (2 ** self.request.retries)  # exponential backoff
        logger.warning(
            "Certificate generation failed for %s (attempt %d): %s",
            application_id, self.request.retries + 1, exc
        )
        raise self.retry(exc=exc, countdown=retry_delay)
```

### Database Connection Pool Configuration (PgBouncer)

```ini
# pgbouncer.ini
[databases]
govportal = host=rds.ap-south-1.amazonaws.com port=5432 dbname=govportal

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3
max_db_connections = 100
server_idle_timeout = 600
client_idle_timeout = 0
log_connections = 0
log_disconnections = 0
log_pooler_errors = 1
stats_period = 60
# Increase during Ashadh peak (managed via SSM Parameter Store)
# max_client_conn = 2000
# default_pool_size = 50
```

### Django Database Settings

```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': '127.0.0.1',  # PgBouncer sidecar
        'PORT': '5432',
        'CONN_MAX_AGE': 0,  # Do not reuse connections; let PgBouncer manage pooling
        'OPTIONS': {
            'connect_timeout': 5,
            'options': '-c statement_timeout=30000',  # 30s query timeout
        },
    }
}
```

### Redis Cache TTL Configuration

```python
# settings/cache.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 2,
            'SOCKET_TIMEOUT': 2,
            'IGNORE_EXCEPTIONS': True,  # Degrade gracefully on Redis failure
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'govportal',
        'TIMEOUT': 900,  # Default 15 minutes
    }
}

# Specific TTLs (seconds)
CACHE_TTL = {
    'service_fee': 900,          # 15 minutes — short to catch fee updates quickly
    'service_detail': 3600,      # 1 hour
    'district_list': 86400,      # 24 hours — rarely changes
    'application_status': 30,    # 30 seconds — real-time status display
    'ndw_document': 3600,        # 1 hour — citizen-consented document cache
}
```

### Stuck Application Recovery Script

```bash
#!/bin/bash
# runbooks/recover_stuck_certificates.sh
# Usage: ./recover_stuck_certificates.sh [--dry-run]

CONTAINER=$(aws ecs list-tasks --cluster govportal-prod --family govportal-api \
  --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster govportal-prod \
  --task "$CONTAINER" \
  --container api \
  --interactive \
  --command "python manage.py retry_stuck_certificates \
    --older-than-minutes=30 \
    --queue=certificate_queue \
    ${1:-}"
```

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policy

- All personally identifiable information (PII) collected by the Nepal Government Services Portal — including NID numbers, phone numbers, addresses, and document images — is governed by the **Nepal Privacy Act 2018 (Goptaniyata Sambandhi Ain, 2075)** and its implementing regulations.
- PII fields are encrypted at rest using AES-256 (AWS RDS encryption) and in transit using TLS 1.2+. NID numbers are stored as salted SHA-256 hashes in the primary database; the plaintext value is never logged.
- Citizens have the right to request access to their personal data, correct inaccurate data, and request deletion of data related to withdrawn or rejected applications, subject to the mandatory 7-year e-governance audit retention period.
- Data is never shared with third parties except: (a) NASC for NID verification, (b) NDW for document retrieval (citizen-authorised), and (c) ConnectIPS/eSewa/Khalti for payment processing. Each integration uses the minimum required data scope.
- Data breach incidents must be reported to the relevant ministry within 72 hours per the Nepal Privacy Act 2018.

### 2. Service Delivery SLA Policy

- Standard service applications must be processed (approved, rejected, or returned for correction) within the statutory processing time defined for each service type (typically 7–21 working days depending on service).
- Applications breaching the SLA trigger automated escalation: the application is reassigned to the senior officer pool and the citizen is notified via SMS (Nepal Telecom / Sparrow SMS gateway) and email.
- The SLA clock is paused during periods when the citizen has been requested to provide additional information (`PENDING_CLARIFICATION` state) and resumes when the citizen responds.
- SLA compliance is reported to the Ministry of Federal Affairs and General Administration (MoFAGA) on a monthly basis via the built-in analytics dashboard.
- The portal itself must maintain 99.5% monthly uptime for citizen-facing endpoints and 99.9% for internal government endpoints, measured by the AWS Route 53 health check.

### 3. Fee and Payment Policy

- Service fees are denominated in Nepalese Rupees (NPR / रू) and are set by gazette notification. The portal's fee schedule is updated by Super Admin within one working day of gazette publication.
- Fee amounts are frozen at the time of application submission (see FR-FEE-003). Citizens are protected from fee increases during application processing.
- Payments are accepted via ConnectIPS, eSewa, and Khalti. Offline challan payment at designated bank counters is also supported for citizens without internet banking access.
- Successful payments are non-refundable except in cases of: (a) application rejection by the government, (b) duplicate payment (double charge), or (c) service unavailability preventing completion.
- Approved refunds are processed within 7 working days through the original payment channel. Refund status is visible in the citizen's payment history.

### 4. System Availability Policy

- The production environment runs on AWS ECS Fargate with multi-AZ deployment across two Availability Zones in the `ap-south-1` (Mumbai) region, providing infrastructure redundancy.
- Planned maintenance windows are scheduled during non-business hours (11:00 PM – 5:00 AM NST, Saturday nights preferred) and communicated to citizens at least 48 hours in advance via the portal's announcement banner and SMS notification.
- Unplanned outages are communicated via the status page (`status.govportal.gov.np`) within 15 minutes of detection. Citizens are notified via SMS if the outage is expected to exceed 30 minutes.
- The Recovery Time Objective (RTO) for a full system failure is 2 hours; the Recovery Point Objective (RPO) is 15 minutes (matching the RDS automated backup interval and point-in-time recovery capability).
- Annual Disaster Recovery (DR) drills are conducted in the first quarter of the fiscal year (Shrawan) to verify the RTO/RPO targets.
