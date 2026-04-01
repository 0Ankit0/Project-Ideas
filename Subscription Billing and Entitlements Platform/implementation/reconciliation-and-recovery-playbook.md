# Reconciliation and Recovery Playbook — Subscription Billing and Entitlements Platform

## Overview

This playbook provides step-by-step operational runbooks for the most common failure scenarios in the Subscription Billing and Entitlements Platform. Each runbook defines detection criteria, investigation steps, recovery procedures, escalation paths, and prevention measures.

**Target audience:** On-call engineers, billing operations team, customer success engineers.

**Severity classification:**

| Severity | Description | Response SLA |
|----------|-------------|-------------|
| P1 | Revenue-impacting: payments failing at scale, billing data loss, complete service outage | 15 minutes |
| P2 | Customer-impacting: duplicate invoices, entitlement desyncs, notification failures | 1 hour |
| P3 | Operational: single-account anomalies, non-urgent reconciliation gaps | 4 hours |

**Common tools used in these runbooks:**

- `psql` — PostgreSQL CLI (`$BILLING_DB_URL` environment variable contains connection string)
- `redis-cli` — Redis CLI (`$REDIS_URL`)
- `kafka-consumer-groups.sh` — Kafka consumer group management (available in billing-engine pods)
- `kubectl` — Kubernetes cluster management
- Grafana dashboard: `https://grafana.internal/d/billing-pipeline`
- PagerDuty incident portal: `https://internal.pagerduty.com`

---

## Runbook 1: Failed Payment Recovery

**Severity:** P1 (if affecting > 1% of daily payment volume) / P2 (isolated failures)

**Runbook ID:** REC-001

---

### 1.1 Detection

A payment failure incident is triggered when any of the following conditions are met:

**Automated alerts (PagerDuty):**

- Prometheus alert `PaymentFailureRateHigh`: payment failure rate exceeds 5% over any 5-minute window
- Prometheus alert `DunningQueueBacklog`: dunning queue depth exceeds 500 entries
- Grafana dashboard "Payment Success Rate" drops below 94% (page-level alert)

**Manual detection:**

```sql
-- Find payments that failed with no subsequent success in the last 24 hours
SELECT
    pa.id AS attempt_id,
    pa.subscription_id,
    pa.invoice_id,
    pa.amount_cents,
    pa.currency,
    pa.status,
    pa.gateway,
    pa.gateway_decline_code,
    pa.gateway_message,
    pa.attempted_at,
    pm.last_four,
    pm.exp_month,
    pm.exp_year,
    CURRENT_DATE > make_date(pm.exp_year, pm.exp_month, 1) + interval '1 month - 1 day' AS card_expired
FROM payment_attempts pa
JOIN payment_methods pm ON pa.payment_method_id = pm.id
WHERE pa.status = 'failed'
  AND pa.attempted_at >= now() - interval '24 hours'
  AND NOT EXISTS (
      SELECT 1 FROM payment_attempts pa2
      WHERE pa2.invoice_id = pa.invoice_id
        AND pa2.status = 'succeeded'
  )
ORDER BY pa.attempted_at DESC;
```

---

### 1.2 Investigation

**Step 1: Classify the failure type**

Review `gateway_decline_code` and `gateway_message` from the query above.

| Decline Code Pattern | Likely Cause | Next Step |
|---------------------|-------------|-----------|
| `card_declined`, `do_not_honor` | Bank block or general decline | Check with customer; advise new payment method |
| `insufficient_funds` | Insufficient balance | Dunning cycle will retry; no immediate action |
| `expired_card` | Card expired | Trigger payment method update flow |
| `card_not_supported` | Card type not accepted | Customer needs different payment method |
| `authentication_required` | 3DS2 challenge required | Check if SCA redirect flow is implemented correctly |
| `gateway_timeout`, `processing_error` | Gateway-side issue | Check Stripe/PayPal status page; retry is safe |

**Step 2: Check the dunning cycle status**

```sql
-- Check dunning state for affected subscription
SELECT
    da.id,
    da.subscription_id,
    da.attempt_number,
    da.status,
    da.scheduled_for,
    da.executed_at,
    da.result_code,
    s.status AS subscription_status
FROM dunning_attempts da
JOIN subscriptions s ON da.subscription_id = s.id
WHERE da.subscription_id = '<subscription_id>'
ORDER BY da.attempt_number ASC;
```

Expected: a `scheduled` entry exists for the next retry. If no entry exists, the dunning scheduler may have missed this subscription.

**Step 3: Check for gateway outage**

- Stripe status: `https://status.stripe.com`
- PayPal status: `https://www.paypal-status.com`
- Braintree status: `https://status.braintreepayments.com`

If a gateway outage is confirmed, pause the dunning scheduler for the affected gateway to prevent burning retry attempts during the outage:

```bash
kubectl set env deployment/dunning-scheduler PAUSE_GATEWAY=stripe -n billing
```

**Step 4: Check payment method expiry**

```sql
-- Find subscriptions with expired default payment methods
SELECT
    s.id AS subscription_id,
    a.email AS account_email,
    pm.last_four,
    pm.exp_month,
    pm.exp_year,
    s.current_period_end
FROM subscriptions s
JOIN accounts a ON s.account_id = a.id
JOIN payment_methods pm ON pm.account_id = a.id AND pm.is_default = true
WHERE s.status IN ('active', 'past_due')
  AND make_date(pm.exp_year, pm.exp_month, 1) + interval '1 month' <= CURRENT_DATE;
```

---

### 1.3 Recovery

**Option A: Trigger a manual payment retry**

Use this when the dunning scheduler should have retried but did not (missed schedule or scheduler was paused).

```bash
# Via admin API
curl -X POST https://api-internal.billing.svc/v1/admin/dunning/retry \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "<subscription_id>",
    "invoice_id": "<invoice_id>",
    "reason": "Manual retry initiated by on-call engineer per REC-001"
  }'
```

**Option B: Trigger payment method update flow**

Send the account a payment method update email with a secure, time-limited update link:

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/notifications/payment-method-update \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "<account_id>",
    "reason": "card_expired"
  }'
```

The update link is valid for 48 hours and uses a HMAC-signed token scoped to payment method changes only.

**Option C: Override dunning step (skip to specific attempt)**

Use when an account has resolved the payment issue but the dunning cycle is in a waiting state:

```sql
-- Override: reset dunning to attempt #1 immediately
UPDATE dunning_attempts
SET status = 'scheduled',
    scheduled_for = now(),
    updated_at = now()
WHERE subscription_id = '<subscription_id>'
  AND status = 'scheduled'
  AND attempt_number = (
      SELECT MAX(attempt_number) FROM dunning_attempts
      WHERE subscription_id = '<subscription_id>' AND status IN ('failed', 'scheduled')
  );
```

After updating, trigger the dunning scheduler to pick up the record:

```bash
kubectl rollout restart deployment/dunning-scheduler -n billing
```

**Option D: Collect payment via alternative gateway**

If the primary gateway is experiencing an outage, the payment can be retried against an alternative gateway:

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/payments/retry-with-gateway \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"invoice_id": "<invoice_id>", "gateway": "paypal"}'
```

---

### 1.4 Escalation

If three manual retries fail within a 24-hour window, escalate to the Customer Success team:

1. Open a PagerDuty incident at severity P2 and assign to the `customer-success` escalation policy.
2. Include in the incident: account ID, subscription ID, invoice ID, all attempt IDs with decline codes, account ARR value.
3. Customer Success will contact the account directly to resolve the payment situation.
4. Engineering marks the dunning state as `escalated` to halt automated retries during the Customer Success engagement:

```sql
UPDATE dunning_attempts
SET status = 'escalated',
    escalation_note = 'Escalated to Customer Success per REC-001 after 3 manual retries failed',
    updated_at = now()
WHERE subscription_id = '<subscription_id>'
  AND status = 'scheduled';
```

---

### 1.5 Prevention

**Proactive card expiry notifications:**

The Notification Service sends an automated email 30 days and 7 days before the default payment method's expiry date. This is triggered by the `CardExpiryChecker` job that runs daily at 09:00 UTC.

Verify the job is running:

```bash
kubectl get cronjob card-expiry-checker -n billing
# Expected output: LAST SCHEDULE shows a timestamp within the last 25 hours
```

If the job has not run, restart it:

```bash
kubectl create job --from=cronjob/card-expiry-checker card-expiry-checker-manual -n billing
```

**Monitoring:** Add Grafana annotation when a gateway outage is detected; use this to correlate with payment failure spikes in post-mortem analysis.

---

## Runbook 2: Duplicate Invoice Detection and Recovery

**Severity:** P2

**Runbook ID:** REC-002

---

### 2.1 Detection

**Automated alert:** Prometheus alert `DuplicateInvoiceDetected` fires when the following query returns any rows (runs every 10 minutes):

```sql
-- Detect duplicate finalized invoices for same subscription and period
SELECT
    i1.account_id,
    i1.subscription_id,
    i1.period_start,
    i1.period_end,
    COUNT(*) AS duplicate_count,
    ARRAY_AGG(i1.id ORDER BY i1.finalized_at) AS invoice_ids,
    SUM(i1.total) AS total_charged
FROM invoices i1
WHERE i1.status IN ('open', 'paid')
  AND i1.finalized_at >= now() - interval '48 hours'
GROUP BY i1.account_id, i1.subscription_id, i1.period_start, i1.period_end
HAVING COUNT(*) > 1;
```

---

### 2.2 Investigation

**Step 1: Identify which invoice was generated first**

```sql
SELECT
    id,
    idempotency_key,
    status,
    total,
    finalized_at,
    created_at
FROM invoices
WHERE subscription_id = '<subscription_id>'
  AND period_start = '<period_start>'
  AND period_end = '<period_end>'
ORDER BY created_at ASC;
```

The first invoice (earliest `created_at`) is the canonical invoice. The subsequent invoice(s) are duplicates.

**Step 2: Check billing scheduler logs for duplicate triggers**

```bash
kubectl logs -n billing -l app=billing-scheduler --since=2h | grep '<subscription_id>' | grep 'invoice_generation'
```

Look for:
- Multiple `"acquired billing lock"` entries for the same subscription within a short time window (indicates Redis lock was not acquired correctly)
- `"lock already held"` entries followed by a retry that proceeded anyway (indicates lock TTL race condition)

**Step 3: Check Redis lock state**

```bash
redis-cli -u $REDIS_URL GET "billing-lock:<subscription_id>"
```

If no key exists, the lock has expired. This is the root cause of the duplicate: two scheduler pods raced to acquire the lock, and one proceeded after the lock expired during a slow billing operation.

**Step 4: Check Kafka consumer offset for potential duplicate trigger**

```bash
# In a billing-engine pod
kafka-consumer-groups.sh --bootstrap-server $KAFKA_BOOTSTRAP \
  --group billing-scheduler \
  --describe | grep billing.events.v1
```

If `LAG` is greater than 0 on `billing.events.v1`, the scheduler may be reprocessing events. Check if the consumer group offset was reset recently.

---

### 2.3 Recovery

**Step 1: Identify which invoice was actually paid**

```sql
SELECT
    i.id AS invoice_id,
    i.status,
    i.total,
    pa.id AS payment_attempt_id,
    pa.status AS payment_status,
    pa.gateway,
    pa.gateway_transaction_id,
    pa.attempted_at
FROM invoices i
LEFT JOIN payment_attempts pa ON pa.invoice_id = i.id AND pa.status = 'succeeded'
WHERE i.subscription_id = '<subscription_id>'
  AND i.period_start = '<period_start>'
ORDER BY i.created_at ASC;
```

**Step 2: Void the duplicate invoice**

If neither invoice has been paid, void the second one:

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/invoices/<duplicate_invoice_id>/void \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Duplicate invoice detected per REC-002. Canonical invoice: <canonical_invoice_id>"}'
```

If the duplicate invoice was paid (customer was double-charged), void it **and** issue a credit note:

```bash
# Void the duplicate
curl -X POST https://api-internal.billing.svc/v1/admin/invoices/<duplicate_invoice_id>/void \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Duplicate charge per REC-002. Refund via credit note to follow."}'

# Issue a full credit note for the duplicate amount
curl -X POST https://api-internal.billing.svc/v1/credit-notes \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "account_id": "<account_id>",
    "amount_cents": <duplicate_invoice_total>,
    "currency": "usd",
    "reason": "Duplicate charge refund",
    "source_invoice_id": "<duplicate_invoice_id>",
    "type": "full_refund"
  }'
```

**Step 3: Initiate gateway refund if customer was charged**

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/payments/<payment_attempt_id>/refund \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Duplicate charge per REC-002"}'
```

**Step 4: Notify the customer**

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/notifications/custom \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "account_id": "<account_id>",
    "template": "duplicate_charge_apology",
    "variables": {
      "original_invoice_id": "<canonical_invoice_id>",
      "refund_amount": "<amount>",
      "refund_timeline": "3-5 business days"
    }
  }'
```

---

### 2.4 Root Cause and Prevention

**Immediate fix:** Increase the Redis billing lock TTL to accommodate the longest observed invoice generation time plus a safety margin:

```bash
# Current: 3600 seconds (1 hour). Increase to 7200 seconds (2 hours)
kubectl set env deployment/billing-engine BILLING_LOCK_TTL_SECONDS=7200 -n billing
```

**Structural prevention:** Use a PostgreSQL unique constraint as the authoritative idempotency guard. The Redis lock is a performance optimization; the database is the source of truth:

```sql
-- Verify this constraint exists (it should per schema v1.0)
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'invoices'::regclass AND conname = 'invoices_idempotency_key_key';
```

If the constraint is missing, add it:

```sql
ALTER TABLE invoices
ADD CONSTRAINT invoices_idempotency_key_unique UNIQUE (idempotency_key);
```

With this constraint, the second invoice generation attempt will receive a unique constraint violation, log the error, and return the existing invoice — preventing the duplicate from ever reaching `finalized` state.

---

## Runbook 3: Usage Data Loss Recovery

**Severity:** P1 (if affecting current billing period) / P2 (historical periods)

**Runbook ID:** REC-003

---

### 3.1 Detection

**Automated alert:** Prometheus alert `UsageIngestionLagCritical` fires when Kafka consumer lag on `usage.deduplicated.v1` exceeds 5 minutes.

**Manual detection — missing usage records:**

```sql
-- Compare expected daily usage record count against historical baseline
WITH daily_counts AS (
    SELECT
        DATE(event_timestamp) AS event_date,
        COUNT(*) AS event_count
    FROM usage_events
    WHERE event_timestamp >= now() - interval '14 days'
    GROUP BY DATE(event_timestamp)
)
SELECT
    event_date,
    event_count,
    AVG(event_count) OVER (ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS rolling_7d_avg,
    event_count / NULLIF(AVG(event_count) OVER (ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING), 0) AS ratio
FROM daily_counts
ORDER BY event_date DESC;
```

A ratio below 0.7 (70% of the 7-day rolling average) for any day indicates a potential data loss event.

---

### 3.2 Investigation

**Step 1: Check Kafka consumer lag**

```bash
# Run inside a billing-engine pod
kafka-consumer-groups.sh \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --group usage-dedup \
  --describe

kafka-consumer-groups.sh \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --group usage-aggregator \
  --describe
```

Note the `LAG` column for each partition. A non-zero lag means events are queued but not yet processed. A lag of 0 with missing records means events were never produced to Kafka (ingestion-side failure) or were lost before consumption (Kafka topic misconfiguration).

**Step 2: Check ingestion API error rates**

```bash
kubectl logs -n billing -l app=usage-ingestion-api --since=6h \
  | grep '"level":"error"' \
  | jq -r '.msg' \
  | sort | uniq -c | sort -rn \
  | head -20
```

Also check Prometheus metric `usage_ingestion_errors_total` by error type over the investigation window.

**Step 3: Check deduplication Redis TTL**

If the `idempotency_key` TTL was inadvertently reduced below 24 hours (minimum for same-day duplicate protection), legitimate duplicate events may be re-ingesting while dedup misses them, creating inflated counts. Alternatively, if the Redis instance was flushed, all dedup keys were lost and re-submitted events would be re-ingested.

```bash
# Check a sample idempotency key TTL
redis-cli -u $REDIS_URL TTL "idempotency:$(echo -n 'sample_key' | sha256sum | cut -d' ' -f1)"
# Expected: a value between 1 and 7776000 (90 days in seconds)
```

**Step 4: Check S3 usage backup files**

Usage events are written to S3 in 1-hour batch files as a backup. Verify that backup files exist for the missing period:

```bash
aws s3 ls s3://billing-usage-backups/raw/<account_id>/<year>/<month>/<day>/ \
  --recursive | awk '{print $1, $2, $3, $4}'
```

If S3 files exist but events are missing from the database, the Kafka producer was healthy but the consumer pipeline failed.

**Step 5: Determine the exact gap**

```sql
SELECT
    period_start,
    period_end,
    feature_key,
    SUM(quantity) AS recorded_quantity
FROM usage_aggregates
WHERE subscription_id = '<subscription_id>'
  AND period_start >= '<gap_start>'
  AND period_end <= '<gap_end>'
GROUP BY period_start, period_end, feature_key
ORDER BY period_start;
```

Compare this against the expected event volume from the S3 backup files.

---

### 3.3 Recovery

**Option A: Replay Kafka events from a known-good offset**

Use this when events are present in Kafka but were not consumed due to consumer failure.

```bash
# Identify the last successfully processed offset before the gap
kafka-consumer-groups.sh \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --group usage-aggregator \
  --describe | grep "usage.deduplicated.v1"

# Reset consumer group offset to the offset corresponding to the start of the gap
# Note: partitions and offsets must be identified per-partition
kafka-consumer-groups.sh \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --group usage-aggregator \
  --topic usage.deduplicated.v1 \
  --reset-offsets \
  --to-offset <gap_start_offset> \
  --partition <partition_id> \
  --execute
```

Restart the aggregator to begin reprocessing:

```bash
kubectl rollout restart deployment/usage-aggregator -n billing
```

Monitor the reprocessing progress by watching Kafka lag drop to zero.

**Option B: Re-process usage files from S3 backup**

Use this when events were never produced to Kafka (ingestion failure) but S3 backup files exist.

```bash
# Trigger the S3 replay job for a specific account and time window
curl -X POST https://api-internal.billing.svc/v1/admin/usage/replay \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "account_id": "<account_id>",
    "replay_start": "<gap_start_iso8601>",
    "replay_end": "<gap_end_iso8601>",
    "source": "s3_backup",
    "dry_run": true
  }'
```

Review the dry-run output to confirm the expected records before executing for real:

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/usage/replay \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "account_id": "<account_id>",
    "replay_start": "<gap_start_iso8601>",
    "replay_end": "<gap_end_iso8601>",
    "source": "s3_backup",
    "dry_run": false
  }'
```

The replay job produces events to `usage.raw.v1` with a `replay: true` flag. The dedup consumer processes them normally; new dedup keys are registered. Aggregates are upserted.

**Option C: Recalculate aggregates directly from source system**

If neither Kafka replay nor S3 backup is available, request a raw usage export from the upstream source system (the application that reports usage events). Import the export file using the admin bulk ingestion endpoint.

**Step: Re-rate affected invoices after usage recovery**

If the usage gap falls within a billing period for which an invoice has already been finalized, a credit note or supplemental invoice must be issued:

```sql
-- Find finalized invoices covering the gap period
SELECT id, account_id, subscription_id, status, total, period_start, period_end
FROM invoices
WHERE subscription_id = '<subscription_id>'
  AND period_start <= '<gap_end>'
  AND period_end >= '<gap_start>'
  AND status IN ('open', 'paid');
```

For each affected invoice, use the admin API to issue a supplemental invoice line item:

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/invoices/<invoice_id>/supplemental-line-item \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "description": "Usage recovery adjustment: <feature_key> usage for <gap_start> to <gap_end>",
    "amount_cents": <recovered_usage_charge>,
    "type": "usage",
    "notes": "Recovered per REC-003 incident <incident_id>"
  }'
```

---

### 3.4 Prevention

**SLA enforcement:** The Usage Ingestion SLA requires that 99.9% of usage events be ingested and aggregated within 5 minutes of receipt. This is monitored by Prometheus and alerted via PagerDuty.

**Consumer lag alerting:** Alert `UsageIngestionLagWarning` fires at 2-minute lag; `UsageIngestionLagCritical` fires at 5-minute lag. These fire well before data loss occurs.

**Dedup TTL monitoring:** A daily job validates that dedup key TTLs are within the expected range. Alert if any TTL is below 86,400 seconds (24 hours).

**S3 backup verification:** A nightly job confirms that S3 backup files exist for every hour of the previous day for all active accounts. Missing files trigger a P3 alert.

---

## Runbook 4: Entitlement Desync Recovery

**Severity:** P2 (single account) / P1 (widespread desync across many accounts)

**Runbook ID:** REC-004

---

### 4.1 Detection

**Automated detection:** A reconciliation job runs every 15 minutes and compares Redis entitlement cache state against PostgreSQL `entitlements` table. Mismatches are recorded in `entitlement_reconciliation_log` and fire a Prometheus alert `EntitlementDesyncDetected`.

```sql
-- View recent desync events
SELECT
    erl.account_id,
    erl.feature_key,
    erl.redis_value,
    erl.postgres_value,
    erl.detected_at,
    erl.resolved_at
FROM entitlement_reconciliation_log erl
WHERE erl.detected_at >= now() - interval '1 hour'
  AND erl.resolved_at IS NULL
ORDER BY erl.detected_at DESC;
```

**Manual detection:** Customer reports that they can access a feature that should be blocked (over-entitlement) or cannot access a feature they should have (under-entitlement).

For under-entitlement (feature incorrectly blocked):

```bash
# Check Redis cache value for the entitlement
redis-cli -u $REDIS_URL HGETALL "entitlement:<account_id>:<feature_key>"
```

```sql
-- Check PostgreSQL source of truth
SELECT
    id,
    account_id,
    subscription_id,
    feature_key,
    enforcement,
    limit_value,
    current_usage,
    reset_at,
    updated_at
FROM entitlements
WHERE account_id = '<account_id>'
  AND feature_key = '<feature_key>';
```

If Redis and PostgreSQL show different values, a desync exists.

---

### 4.2 Investigation

**Step 1: Determine the last cache population time**

```bash
redis-cli -u $REDIS_URL OBJECT IDLETIME "entitlement:<account_id>:<feature_key>"
# Returns number of seconds since the key was last accessed or updated
```

```bash
redis-cli -u $REDIS_URL DEBUG OBJECT "entitlement:<account_id>:<feature_key>"
# Returns encoding and serialized length; use with OBJECT ENCODING for cache health checks
```

**Step 2: Check entitlement event delivery failures**

Entitlement state changes are propagated from PostgreSQL to Redis via the Kafka topic `entitlement.events.v1`. Check if the consumer group is processing events:

```bash
kafka-consumer-groups.sh \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --group entitlement-cache-updater \
  --describe
```

If there is lag on `entitlement.events.v1`, the cache updater is behind and the cache contains stale data.

**Step 3: Check for recent subscription state changes**

```sql
-- Check if a subscription event (upgrade, cancellation, plan change) was recently processed
SELECT
    sel.id,
    sel.subscription_id,
    sel.event_type,
    sel.payload,
    sel.created_at
FROM subscription_event_log sel
WHERE sel.subscription_id = (
    SELECT subscription_id FROM entitlements
    WHERE account_id = '<account_id>' LIMIT 1
)
ORDER BY sel.created_at DESC
LIMIT 10;
```

A recent `plan_changed` or `canceled` event that did not propagate the entitlement update is the most common cause of desync.

**Step 4: Check for Redis eviction or flush events**

```bash
# Check Redis keyspace info for eviction counters
redis-cli -u $REDIS_URL INFO keyspace
redis-cli -u $REDIS_URL INFO stats | grep evicted_keys
```

If `evicted_keys` is increasing, the Redis instance is under memory pressure and evicting entitlement keys. This causes cache misses that should trigger a cache-warm from PostgreSQL — but if the cache-warm code has a bug, the miss is served as "no entitlement" (denial of service for the feature).

**Step 5: Assess blast radius**

```sql
-- Count the number of accounts with a desync in the last hour
SELECT COUNT(DISTINCT account_id) AS affected_accounts
FROM entitlement_reconciliation_log
WHERE detected_at >= now() - interval '1 hour'
  AND resolved_at IS NULL;
```

If this count exceeds 50 accounts, escalate to P1 and page the on-call engineering lead immediately.

---

### 4.3 Recovery

**Option A: Single-account cache rebuild**

Use when the desync affects one account or a small number of known accounts.

```bash
# Trigger a cache rebuild for a specific account
curl -X POST https://api-internal.billing.svc/v1/admin/entitlements/rebuild-cache \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "account_id": "<account_id>",
    "reason": "Desync detected per REC-004 incident <incident_id>"
  }'
```

This endpoint:
1. Deletes all Redis entitlement keys for the account (`DEL entitlement:<account_id>:*`)
2. Reads current entitlement state from PostgreSQL
3. Repopulates Redis with correct values and fresh TTLs
4. Logs the rebuild in `entitlement_reconciliation_log`

Verify the rebuild:

```bash
redis-cli -u $REDIS_URL HGETALL "entitlement:<account_id>:<feature_key>"
```

**Option B: Bulk cache rebuild for multiple accounts**

Use when the desync affects many accounts (e.g., after a Redis flush or widespread Kafka consumer failure).

```bash
# Trigger bulk rebuild for all accounts with open desyncs
curl -X POST https://api-internal.billing.svc/v1/admin/entitlements/bulk-rebuild-cache \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "scope": "desynced_only",
    "reason": "Bulk rebuild per REC-004 incident <incident_id>"
  }'
```

Monitor rebuild progress:

```bash
# Watch the rebuild progress counter in Prometheus
curl -s https://prometheus.internal/api/v1/query \
  --data-urlencode 'query=entitlement_cache_rebuild_progress' | jq '.data.result'
```

**Option C: Full cache rebuild (nuclear option)**

Use only when the entire Redis entitlement keyspace is compromised (e.g., after an unintended `FLUSHALL` on the entitlement namespace).

```bash
curl -X POST https://api-internal.billing.svc/v1/admin/entitlements/full-cache-rebuild \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Confirmation-Token: $REBUILD_CONFIRMATION_TOKEN" \
  -d '{"reason": "Full rebuild: Redis keyspace compromised per REC-004"}'
```

This job reads all active entitlements from PostgreSQL and repopulates Redis in batches of 1,000 accounts. Estimated time: 15–30 minutes for 100,000 active accounts. During the rebuild, the entitlement service falls back to PostgreSQL for cache misses (automatic fallback via circuit breaker).

**Step: Resolve the Kafka consumer lag (if applicable)**

If the desync was caused by Kafka consumer lag:

```bash
# Restart the entitlement cache updater consumer
kubectl rollout restart deployment/entitlement-cache-updater -n billing

# Monitor lag recovery
watch -n 5 'kafka-consumer-groups.sh --bootstrap-server $KAFKA_BOOTSTRAP \
  --group entitlement-cache-updater --describe 2>/dev/null | grep entitlement.events.v1'
```

---

### 4.4 Prevention

**Periodic reconciliation job:**

The `EntitlementReconciler` CronJob runs every 15 minutes and compares Redis state against PostgreSQL for all active accounts modified in the last 30 minutes. Mismatches are auto-corrected and logged.

```bash
# Verify the reconciler is scheduled and running
kubectl get cronjob entitlement-reconciler -n billing
kubectl get jobs -n billing -l app=entitlement-reconciler --sort-by='.status.startTime' | head -5
```

**Cache TTL hygiene:**

Entitlement cache keys are set with a 1-hour TTL. Any key not refreshed within 1 hour will expire and be re-populated from PostgreSQL on the next access. This self-healing behavior limits the maximum desync window to 1 hour in a worst-case scenario where the Kafka consumer is completely stopped.

**Memory pressure prevention:**

Redis is configured with `maxmemory-policy allkeys-lru` as a safety net, but the entitlement keyspace is sized to hold all active account entitlements with 40% headroom. Monitor `redis_memory_used_bytes` and alert at 70% of `maxmemory` to trigger capacity expansion before eviction occurs.

**Write-through pattern enforcement:**

All PostgreSQL writes to the `entitlements` table go through the `EntitlementService`, which performs a write-through to Redis immediately after the DB write. The Kafka event is a second-path update for eventual consistency; it is not the primary cache update mechanism. This dual-write pattern means that a single Kafka consumer failure does not immediately cause a desync — only if the write-through also fails (e.g., Redis unavailable during the write) will a desync occur.

**Post-incident checklist:**

After resolving any entitlement desync incident:

- [ ] Confirm `entitlement_reconciliation_log` shows zero open desyncs for affected accounts
- [ ] Verify affected customers can access entitled features correctly
- [ ] Review Kafka consumer lag history to identify root cause window
- [ ] Check Redis memory metrics for eviction events
- [ ] Document the incident in the incident management system with timeline, impact, and RCA
- [ ] Update this runbook if new failure modes were discovered during the incident

---

## Appendix: Common Queries Reference

```sql
-- Account billing overview
SELECT
    a.id, a.email, a.name,
    s.status AS subscription_status,
    p.name AS plan_name,
    s.current_period_start,
    s.current_period_end,
    (SELECT COUNT(*) FROM invoices i WHERE i.account_id = a.id AND i.status = 'open') AS open_invoices,
    (SELECT SUM(cn.amount_cents) FROM credit_notes cn WHERE cn.account_id = a.id AND cn.status = 'open') AS available_credit_cents
FROM accounts a
JOIN subscriptions s ON s.account_id = a.id AND s.status NOT IN ('canceled')
JOIN plan_versions pv ON s.plan_version_id = pv.id
JOIN plans p ON pv.plan_id = p.id
WHERE a.id = '<account_id>';

-- Dunning funnel summary (last 30 days)
SELECT
    attempt_number,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) AS succeeded,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    ROUND(100.0 * SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM dunning_attempts
WHERE scheduled_for >= now() - interval '30 days'
GROUP BY attempt_number
ORDER BY attempt_number;

-- Revenue at risk (past_due subscriptions)
SELECT
    COUNT(*) AS past_due_count,
    SUM(i.total) AS revenue_at_risk_cents
FROM subscriptions s
JOIN invoices i ON i.subscription_id = s.id AND i.status = 'open'
WHERE s.status = 'past_due';
```
