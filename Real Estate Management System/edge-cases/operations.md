# Operational Edge Cases

---

### PostGIS Spatial Query Performance Degradation at Scale

**Failure Mode**

At 100K+ property records, spatial queries using `ST_DWithin`, `ST_Within`, and `ST_Intersects` degrade sharply when the `geometry` column on the `properties` table lacks a GIST index. PostGIS 3.x falls back to sequential scans, examining every row before applying the spatial predicate. Query time crosses 2s at p99 around 80K records, and exceeds 12s at p99 beyond 200K records. The problem compounds when autovacuum falls behind on a high-write table — dead tuple bloat causes the query planner to misestimate row counts, causing it to prefer nested loop joins over hash joins even when a GIST index exists. `EXPLAIN (ANALYZE, BUFFERS)` will show `Seq Scan` on the geometry column and `Rows Removed by Filter` counts in the tens of thousands. A secondary failure mode occurs after a PostgreSQL major version upgrade (e.g., 14 → 15) where GIST index statistics are not automatically refreshed, causing the planner to choose stale plans for at least 24 hours until `ANALYZE` runs. `enable_seqscan=off` at the session level can confirm whether the planner is ignoring a valid index.

**Impact**

Map-based property search becomes unusable. API endpoints returning listings within a geographic radius (`/api/v1/properties/search?lat=&lng=&radius_km=`) time out at the 5s gateway limit, returning `504 Gateway Timeout` to clients. Frontend map tiles fail to populate. Mobile app users see empty search results. Concurrent map searches saturate the PostgreSQL connection pool (typically capped at 100 connections via PgBouncer), causing all other read queries to queue. If the pool exhausts, write operations for lease creation and tenant onboarding also begin failing with `FATAL: remaining connection slots are reserved`.

**Detection**

- `pg_stat_statements` shows `mean_exec_time > 2000ms` for queries containing `ST_DWithin`
- `pg_stat_user_tables` shows `n_dead_tup > 20000` on the `properties` table
- `pg_indexes` confirms absence of an index of type `gist` on `geom` column
- Datadog APM trace duration p99 for `/api/v1/properties/search` exceeds 5000ms
- PgBouncer metric `cl_waiting > 20` sustained for more than 60 seconds
- PostgreSQL log: `duration: XXXXX ms  statement: SELECT ... ST_DWithin(...)` entries appearing at `log_min_duration_statement = 1000`

**Mitigation**

Create the GIST index concurrently to avoid table lock:
```sql
CREATE INDEX CONCURRENTLY idx_properties_geom_gist
    ON properties USING GIST (geom);
```
For tables with mixed 2D/3D geometries, use `geometry_ops_nd`. Force a statistics refresh immediately after index creation:
```sql
ANALYZE properties;
VACUUM ANALYZE properties;
```
Set `work_mem = 64MB` at the session level for spatial queries to prevent spill to disk during geometry intersection operations. Add a bounding-box pre-filter using the `&&` operator before invoking `ST_DWithin` — the `&&` operator uses the GIST index for a cheap envelope check before the exact predicate runs:
```sql
WHERE geom && ST_Expand(ST_MakePoint(:lng, :lat)::geography, :radius_m)
  AND ST_DWithin(geom::geography, ST_MakePoint(:lng, :lat)::geography, :radius_m)
```
Configure autovacuum aggressively on the `properties` table:
```sql
ALTER TABLE properties SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);
```

**Recovery**

If the system is actively degraded: immediately set `statement_timeout = 3000` on the connection pool to shed runaway spatial queries and restore headroom for other operations. Kill long-running spatial queries via `pg_cancel_backend(pid)` for queries exceeding 10s. Create the GIST index concurrently (does not block reads or writes). Run `VACUUM ANALYZE properties` once the index is in place. Re-enable normal statement timeouts after confirming p99 latency is below 500ms in `pg_stat_statements`. Monitor for 24 hours post-recovery to confirm autovacuum is keeping up with write load.

---

### Elasticsearch Full Reindex After Mapping Change

**Failure Mode**

Elasticsearch 8.x does not allow in-place mapping changes that alter field types (e.g., promoting a `text` field to `keyword`, or changing a `float` to `integer`). This situation arises when MLS data feeds (RESO Web API) introduce new required fields — such as `ListingKey`, `StandardStatus`, or `LivingAreaUnits` — that conflict with existing dynamic mappings inferred from earlier IDX feed ingestion. A naive `PUT /properties/_mapping` request with a type conflict returns `illegal_argument_exception: mapper [price] of different type`. Developers then attempt a forced reindex by deleting and recreating the index, which causes a search outage lasting the duration of the reindex — typically 15–45 minutes for 100K documents with nested `amenities` objects and `geo_point` fields. During this window, all listing search APIs return `index_not_found_exception` (HTTP 404), and the frontend search bar is completely non-functional.

**Impact**

All property search, autocomplete, and faceted filtering is unavailable. Users cannot search by city, ZIP code, bedroom count, or price range. Direct links to search result pages return errors. MLS-synced listing pages show stale data or fail entirely. If the reindex is triggered during business hours without a maintenance window, support ticket volume spikes 300–500% within the first 10 minutes. SEO-critical search pages return 5xx, potentially impacting Google crawl budget and search ranking.

**Detection**

- Elasticsearch cluster health transitions from `green` to `yellow` or `red` during reindex
- `GET /_cat/indices?v` shows the old index in `red` state or absent
- Application logs: `ResponseException: index_not_found_exception` from the `elasticsearch-py` or `@elastic/elasticsearch` client
- Kibana index management panel shows index in `reindex` state
- Datadog monitor: `elasticsearch.search.query.total` drops to zero
- API error rate monitor: `/api/v1/search/*` 5xx rate exceeds 10% for 2 consecutive minutes

**Mitigation**

Use the index alias + zero-downtime reindex pattern. The live index is always accessed via an alias (`properties_live`), never directly. To perform a mapping change:
1. Create a new index with the corrected mapping: `PUT /properties_v2 { "mappings": { ... } }`
2. Start the reindex from old to new in the background: `POST /_reindex?wait_for_completion=false { "source": { "index": "properties_v1" }, "dest": { "index": "properties_v2" } }`
3. Monitor reindex task: `GET /_tasks/<task_id>`
4. Once complete, atomically swap the alias: `POST /_aliases { "actions": [ { "remove": { "index": "properties_v1", "alias": "properties_live" } }, { "add": { "index": "properties_v2", "alias": "properties_live" } } ] }`
5. All reads and writes continue against `properties_live` throughout — zero downtime.

For text→keyword conflicts: add the new field as `price_keyword` temporarily and migrate query logic before removing the old field. For MLS field additions, use `dynamic: false` on the root mapping and explicitly map all RESO-standard fields in the index template to prevent future dynamic mapping drift.

**Recovery**

If an outage has already begun due to a dropped index: restore from the most recent Elasticsearch snapshot (configure daily snapshots to S3 via `repository-s3` plugin, retention 7 days). Run `POST /_snapshot/s3_backup/snapshot_latest/_restore`. While restore is in progress, serve cached search results from Redis (TTL 300s) for common queries. Return `Cache-Control: stale-while-revalidate=600` on search API responses to allow browsers to serve stale content. After restore, immediately apply the alias strategy to prevent recurrence.

---

### Payment Reconciliation Failures at Month-End Rent Cycle

**Failure Mode**

On the first of each month, the batch rent collection job processes ACH debit initiations for all active leases. Three failure modes converge: (1) ACH returns arrive 2–3 banking days after initiation with `R01` (Insufficient Funds), `R02` (Account Closed), or `R10` (Customer Advises Not Authorized) return codes, which must be matched back to the original payment record — but if the Stripe webhook for `payment_intent.payment_failed` fires and the idempotency key has already been consumed by a prior retry, the webhook handler returns `200 OK` without updating the ledger, leaving the payment marked `pending` indefinitely. (2) The midnight UTC batch job and the webhook handler both attempt to update the same payment row simultaneously, causing a lost update when optimistic locking is not enforced — one process reads `status=pending`, the other writes `status=failed`, and the first overwrites it back to `pending`. (3) Month-end ACH volume causes Stripe to delay webhook delivery by 15–30 minutes, meaning the batch job and webhook arrive within the same database transaction window, triggering a deadlock on the `payments` table.

**Impact**

Landlord ledger balances are incorrect: units show rent as collected when the tenant's payment actually failed. Automated late fee triggers fire incorrectly (or fail to fire). Property managers receive inaccurate end-of-month financial reports. If NSF payments are not flagged within 5 banking days, re-presentation windows close. Regulatory reporting (e.g., 1099 generation) uses ledger data and will be incorrect. Stripe disputes and chargeback rates increase if failed payments are not communicated to tenants promptly.

**Detection**

- Stripe Dashboard: `payment_intent.payment_failed` events without a corresponding `updated_at` change in the local `payments` table within 60 seconds
- Ledger reconciliation job (run nightly at 02:00 UTC): `SELECT COUNT(*) FROM payments WHERE stripe_status != local_status` exceeds 0
- PagerDuty alert: `payments.ledger_mismatch_count > 0` for more than 15 minutes
- Database slow query log: deadlock errors (`ERROR: deadlock detected`) on `payments` and `ledger_entries` tables around 00:00–00:30 UTC on the 1st
- Stripe webhook delivery failure rate: `> 1%` for the `payment_intent.*` event type

**Mitigation**

Enforce idempotency at the handler level using the Stripe `idempotencyKey` plus a database-level unique constraint on `(stripe_event_id)` in the `webhook_events` table — insert before processing, rollback if duplicate. Use `SELECT ... FOR UPDATE SKIP LOCKED` when the batch job claims payment rows to process, preventing the webhook handler from touching the same row simultaneously. Separate the ACH initiation batch (runs at 00:00 UTC) from the reconciliation batch (runs at 06:00 UTC, after most webhooks have arrived). Store ACH return codes in a `payment_returns` table keyed by `(ach_trace_number, return_code)` and process re-presentation logic separately from the main payment flow. Implement an explicit outbox pattern: write payment status changes to an `outbox` table inside the same transaction as the ledger update, then publish asynchronously.

**Recovery**

Run the reconciliation script: compare `payments.stripe_payment_intent_id` against the Stripe API (`GET /v1/payment_intents/:id`) for all records in `pending` status older than 6 hours. Patch mismatched records. Re-trigger the late fee evaluation job after reconciliation is confirmed clean. For NSF returns received after the 5-day window, flag for manual property manager review rather than automated re-presentation. Send tenant notification emails for all confirmed failed payments within 1 hour of ledger correction.

---

### Database Failover During Active Lease Signing Workflow

**Failure Mode**

The lease signing workflow integrates with DocuSign via webhooks (`envelope.completed`, `envelope.voided`, `envelope.declined`). When a primary PostgreSQL instance fails mid-transaction (e.g., during a disk I/O saturation event or a cloud provider AZ outage), the RDS/Aurora failover promotes the standby in approximately 30–60 seconds. During this window, any in-flight HTTP requests to the lease signing API receive `ECONNREFUSED` or `connection to server was lost` errors. The critical failure: DocuSign's webhook delivery system retries every 30 seconds for up to 48 hours. If the webhook endpoint returns `5xx` during the failover window, DocuSign retries the `envelope.completed` callback — but by the time the retry arrives, the application has reconnected to the new primary. If the original transaction that created the `lease_envelopes` row was rolled back during failover, the retry attempts to update a row that no longer exists, silently succeeding with `UPDATE 0` — leaving the envelope in a state where DocuSign considers it complete but the application considers it pending. The lease state machine (`draft → sent → signed → active`) becomes corrupted: the signing UI shows "Awaiting Signature" while DocuSign shows "Completed."

**Impact**

Tenants cannot move forward with their lease. Property managers see conflicting status between the DocuSign dashboard and the platform. If a second applicant is waitlisted for the unit, the system may erroneously release it. Move-in date coordination breaks down. Legal exposure if a signed lease document exists in DocuSign but no corresponding active lease record exists in the database. Orphaned `envelope_id` values accumulate in DocuSign with no matching record in the platform.

**Detection**

- Application health check: `GET /healthz` returns `200` but `GET /api/v1/leases/:id/signing-status` returns `409 Conflict` (DocuSign says complete, DB says pending)
- CloudWatch metric: `RDS FailoverTime` event fires; correlate with lease signing API error rate spike
- DocuSign Connect log: `envelope.completed` webhook delivered, got `503`, followed by successful `200` on retry — but no corresponding `leases.signed_at` update in database
- Orphaned envelope detector (scheduled job, runs hourly): `SELECT * FROM lease_envelopes WHERE docusign_status = 'completed' AND lease_status != 'active'`
- Datadog distributed trace shows `UPDATE leases SET status='signed'... rows affected: 0`

**Mitigation**

Make the DocuSign webhook handler fully idempotent: before updating lease status, verify the `envelope_id` exists in `lease_envelopes`; if not, perform a DocuSign API lookup (`GET /v2.1/accounts/:id/envelopes/:envelopeId`) and reconcile. Use a two-phase commit pattern: write to `signing_events` outbox table atomically with the lease status update, then process outbox records asynchronously. Implement a distributed lock (Redis `SET NX EX 30`) keyed on `envelope_id` before processing any webhook to prevent duplicate processing during the retry window. Route DocuSign webhooks to a dedicated endpoint that queues events into SQS with deduplication enabled (`MessageDeduplicationId = envelope_id + event_type`) — process from SQS once DB connectivity is restored. Write a compensating transaction: if `UPDATE leases SET status='signed' WHERE envelope_id=:eid` returns `rowcount=0`, log a `signing_discrepancy` record and trigger an alert rather than silently succeeding.

**Recovery**

Run the orphaned envelope reconciliation job manually: for each `envelope_id` in DocuSign with status `completed` that has no matching `active` lease, reconstruct the lease record from the DocuSign envelope metadata (tenant, unit, term dates, rent amount are embedded in the envelope tags). Prompt property manager to confirm before activating the reconstructed lease. Void any envelopes that cannot be reconciled and restart the signing workflow. Audit all leases created within the 2-hour window surrounding the failover event.

---

### Mass Lease Expiry Processing at Month-End

**Failure Mode**

At the end of each month, the lease expiry scheduler fires for all leases with `end_date = CURRENT_DATE`. In a portfolio of 10,000+ active leases, it is common for 500–2,000 leases to expire on the same day (month-end clustering). The scheduler spawns one Sidekiq/Celery job per lease, causing a thundering herd that saturates the job queue within 90 seconds of midnight. Workers contend for the same database rows: the auto-renewal job reads `status='active'` and attempts `UPDATE leases SET status='renewed'`, while a tenant cancellation request (submitted at 11:59 PM) writes `status='cancelled'` — both operations read the same initial row state, and the last write wins without a version check, resulting in a lease that is marked `renewed` despite a valid cancellation request. Separately, the `renewal_offers` table is locked by the bulk insert of renewal records (one per expiring lease), which escalates to a table-level lock when the batch exceeds PostgreSQL's `lock_escalation` threshold. This blocks the property management UI from loading unit availability for 3–8 minutes.

**Impact**

Landlords see incorrect occupancy rates. Auto-renewed leases for tenants who cancelled generate erroneous rent charges for the following month. Units are not released to the available inventory pool, preventing new applications. The maintenance scheduling system, which reads lease `end_date` to coordinate move-out inspections, misses inspection scheduling triggers. If auto-renewal generates invoices before the conflict is detected, tenants receive rent invoices they are not obligated to pay — creating a support and legal escalation.

**Detection**

- Job queue depth: Sidekiq `busy` workers at 100% capacity, `enqueued` count exceeds 5,000 jobs, `latency` (time from enqueue to start) exceeds 120 seconds
- Database: `pg_locks` shows `relation` locks on `leases` and `renewal_offers` tables with `granted=false` wait queue > 10
- Application log: `ActiveRecord::StaleObjectError` or `UPDATE 0 rows affected` for lease status transitions
- Conflict monitor: `SELECT COUNT(*) FROM leases WHERE status='renewed' AND cancelled_at IS NOT NULL` returns non-zero
- PagerDuty: unit availability API p99 > 3000ms, triggered by lock wait timeout errors in the property search service

**Mitigation**

Replace the per-lease job fanout with a chunked batch processor: divide expiring leases into batches of 50, process each batch sequentially within a single job, with a 500ms sleep between batches to avoid queue saturation. Use `SELECT ... FOR UPDATE SKIP LOCKED` when claiming lease rows for renewal processing — this ensures cancelled leases are not claimed by the renewal job if they are already locked by the cancellation handler. Enforce optimistic locking via a `lock_version` column on the `leases` table: renewal and cancellation both include `WHERE id=:id AND lock_version=:v`, and retry with exponential backoff (max 3 retries, base delay 200ms) on version conflict. Pre-generate `renewal_offers` records during the preceding 7 days (scheduled nightly), so month-end processing only needs to activate pre-existing records rather than bulk-inserting new ones. Stagger job dispatch using a rate limiter (e.g., Sidekiq Enterprise's `throttle`, or a Redis token bucket): cap at 100 lease transitions per minute.

**Recovery**

Run the conflict resolution script: identify all leases where `status='renewed'` and `cancellation_requested_at < end_date`. For each conflict, soft-revert the renewal (`status='cancelled'`), void the generated invoice, and notify the property manager for manual review. Re-run the unit availability calculation for all affected properties to correct inventory counts. Trigger the move-out inspection scheduler for units that missed the transition.

---

### Email Notification Backlog During Peak Renewal Season

**Failure Mode**

During peak renewal season (October–December, when 60–70% of annual lease renewals occur), the platform sends a surge of transactional emails: renewal offer notices, signing reminders (sent at 30, 14, 7, and 3 days before expiry), payment confirmations, and late payment warnings. AWS SES enforces a sending rate limit (default: 14 emails/second for sandbox, 200/second for production) and a daily sending quota (typically 50,000–200,000 depending on account standing). If the hourly batch renewal-reminder job enqueues 15,000 emails at once without rate limiting, SES returns `Throttling: Maximum sending rate exceeded` errors. The retry logic in the email worker retries immediately (no backoff), amplifying the error rate and triggering SES's abuse detection, which can temporarily reduce the account's sending quota or suspend sending for up to 24 hours. Separately, if bounce rate exceeds 5% or complaint rate exceeds 0.1% (AWS SES thresholds), SES places the account in a `ReviewStatus: UnderReview` state and may pause sending entirely. Template rendering failures (e.g., a Jinja2/Handlebars template referencing a missing `tenant.preferred_name` field) cause `500` errors in the rendering service, blocking the entire notification queue — not just the affected tenant — if the queue processor does not dead-letter malformed messages.

**Impact**

Tenants do not receive renewal offers in time to make decisions before the deadline. Automated late payment notices are not delivered, weakening the legal documentation trail for eviction proceedings. Property managers receive complaints about missed communications. If SES suspension occurs, all transactional emails (password resets, document delivery, maintenance confirmations) are also blocked — not just notification emails. Bounce rate accumulation from outdated tenant email addresses degrades long-term sender reputation.

**Detection**

- AWS CloudWatch: `SES/Reputation/BounceRate > 0.04` alarm
- AWS CloudWatch: `SES/Send/Throttled` metric non-zero for more than 60 seconds
- SES Sending Statistics dashboard: `Rejects` count increasing
- Application log: `botocore.exceptions.ClientError: An error occurred (Throttling) when calling the SendEmail operation`
- Email worker dead-letter queue (SQS DLQ): message count increasing at `> 10/minute`
- Datadog monitor: `email.sent.rate < 50/minute` during a period when `email.queued.count > 1000`
- Template error: `TemplateRenderError` in worker logs with `KeyError: 'preferred_name'`

**Mitigation**

Implement a token bucket rate limiter in the email worker (e.g., using Redis with `INCR` + `EXPIRE`): cap at 180 emails/second to stay below the 200/second SES limit with a 10% safety margin. Spread the renewal reminder batch over 4 hours rather than firing at :00 — use a staggered cron schedule based on the first letter of the tenant's last name or a hash of `lease_id % 4`. Validate all template variables before enqueuing — fail fast with a dead-letter to the `notification_failures` table rather than blocking the queue. Enable SES event publishing to SNS for `Bounce` and `Complaint` events; automatically suppress email addresses after one hard bounce or complaint, updating `tenants.email_suppressed = true`. Configure SendGrid as a fallback SMTP relay: if SES error rate exceeds 5% over 5 minutes, route new messages through SendGrid (`smtp.sendgrid.net:587`) using the same template payload. Set `Content-Type: multipart/alternative` with both HTML and plain-text versions to reduce spam classification.

**Recovery**

If SES is throttled or suspended: immediately switch to SendGrid relay via a feature flag (`notifications.provider = 'sendgrid'`). Replay dead-lettered messages from SQS DLQ in batches of 10/second. Audit bounce list and remove hard-bounced addresses from the active tenant email list. Submit a sending quota increase request to AWS Support if the account quota is the root cause. Once SES is restored, run the missed-notification backfill job: identify all notification records with `status='failed'` or `status='queued'` and `created_at < NOW() - INTERVAL '1 hour'`, re-enqueue with priority flag.

---

### Image CDN Failure Causing All Property Photos to 404

**Failure Mode**

Property listing photos are stored in S3 and served through CloudFront. Three distinct failure modes exist: (1) CloudFront origin fetch errors occur when S3 bucket policy changes (e.g., a tightened IAM policy or accidental public-access block re-enablement) cause CloudFront to receive `403 Forbidden` from S3, which CloudFront caches as an error response for the configured `error_caching_minimum_ttl` (default: 300 seconds). Every request for any image returns `403` until the cache TTL expires, even if the S3 issue is resolved immediately. (2) S3 presigned URLs generated for private listing photos expire (default TTL: 3600 seconds). If the URL is embedded in the HTML at render time and a browser caches the page, the presigned URL expires before the user's next visit — the `<img>` src returns `403 Access Denied` with an XML body, which browsers display as a broken image. (3) A cache invalidation storm occurs when a property photo is re-uploaded (e.g., after a virtual staging edit): the application issues `POST /2020-11-02/distribution/:id/invalidation` for `/*` (wildcard) rather than the specific object path. CloudFront processes invalidations at 1,000 paths/minute maximum; a wildcard counts as one path but triggers a full-cache purge, causing cache miss spikes that hit S3 directly — at 500+ concurrent users, this generates `SlowDown: Please reduce your request rate` (HTTP 503) errors from S3.

**Impact**

All property photos display as broken images across listing detail pages, search results, and the marketing site. Conversion rates drop measurably — A/B test data in comparable outages shows 40–60% reduction in listing inquiry submissions when photos fail. Virtual tour links that reference CDN-served images also break. If the 403 response is cached by browsers (via `Cache-Control: no-store` misconfiguration), some users see broken images for hours after the CDN recovers. MLS syndicators that scrape property images for IDX display may cache the 404/403 responses and propagate broken images across partner sites.

**Detection**

- CloudFront access logs (streamed to S3, queried via Athena): `sc-status = 403` or `sc-status = 503` rate exceeds 0.5% over 5 minutes
- Synthetic monitor (Datadog or Pingdom): HEAD request to a known stable image URL returns non-`200`
- S3 CloudWatch metric: `5xxErrors` on the image bucket spikes above baseline
- Application error tracker: `ImageLoadError` client-side event (reported via browser telemetry) rate exceeds 10/minute
- CloudFront console: error rate metric breaches 1% threshold
- S3 CloudWatch: `SlowDown` error count in `GetObject` operations

**Mitigation**

Set CloudFront's `error_caching_minimum_ttl` to 0 for `4xx` responses from the image origin, so that S3 policy fixes propagate to CDN within one request cycle rather than waiting 300 seconds. For private listing images, generate presigned URLs with a 24-hour TTL and store the URL alongside its expiry in Redis; regenerate before serving if expiry is within 30 minutes. Never use wildcard invalidations (`/*`): always invalidate specific object paths (`/listings/:id/photos/*`) via a targeted invalidation. Add CloudFront as a custom origin with an Origin Access Control (OAC) policy so that S3 never needs to be public and bucket policy changes cannot accidentally break CDN access. Configure a CloudFront Origin Failover group: primary origin is S3, secondary origin is a read-only S3 replica in a second region. Serve a placeholder SVG (stored as a CloudFront function response) for any image that returns `4xx`, so users see a "photo unavailable" state rather than a broken image icon.

**Recovery**

Immediate: run `aws s3api put-bucket-policy` to restore the correct bucket policy, then issue a targeted CloudFront invalidation for affected paths. If the OAC policy is misconfigured, update it via `aws cloudfront update-distribution`. Purge browser-side 403 cache by changing the CDN URL path (e.g., append `?v=2` to image URLs via a deploy-time asset version bump). For presigned URL expiry: redeploy with corrected TTLs, then trigger a cache warming job that pre-generates URLs for all active listing photos. Communicate status to MLS syndication partners via the RESO API `ListingUpdateTimestamp` field so partner sites know to re-fetch.

---

### MLS Data Feed Disruption

**Failure Mode**

MLS data is ingested via RETS (legacy) or RESO Web API (ODATA-based), depending on the MLS board. Disconnections occur due to: expired API credentials (RETS sessions expire after 30 minutes of inactivity; RESO tokens expire after 3600 seconds without refresh), MLS board maintenance windows (typically Saturday 02:00–06:00 local time, often unannounced), rate limit enforcement (`429 Too Many Requests` with `Retry-After` header), and protocol version deprecations (RETS 1.5 EOL with no advance notice). During a disconnection, the feed sync job fails silently if the error handling only logs the exception without marking the feed as `stale` — listings that have been sold, price-reduced, or withdrawn from the market continue to display with stale data. Price update lag is particularly damaging: a property listed at $450,000 that was reduced to $420,000 in the MLS continues to display at $450,000, misleading buyers and creating IDX compliance violations under NAR rules (listings must reflect MLS status within 24 hours). After reconnection, the reconciliation strategy matters: a naive "sync all listings since last successful sync" may miss deletions (withdrawn/sold listings) if the MLS RESO API does not reliably return deletions in the `$filter=ModificationTimestamp ge :datetime` query.

**Impact**

Stale listing data violates IDX compliance agreements with MLS boards; repeated violations result in IDX feed termination, which removes the platform's right to display MLS listings entirely. Buyers contact agents about properties that are already under contract. Price discrepancies trigger buyer complaints and potential fair housing audit exposure. Sold properties remain in active search results, degrading search quality and user trust. If the feed disruption lasts more than 24 hours, the platform is in technical breach of IDX data license terms. Feed reconciliation after reconnection typically takes 2–4 hours for a large MLS (50,000+ listings), during which data may be partially inconsistent.

**Detection**

- Feed health monitor: `SELECT MAX(last_synced_at) FROM mls_feed_runs WHERE status='success'` — alert if result is older than 30 minutes
- RETS/RESO client log: `ReplyCode=20036` (No Records Found — may indicate credential expiry), `HTTP 401`, `HTTP 429`
- Listing staleness detector: `SELECT COUNT(*) FROM listings WHERE mls_last_updated < NOW() - INTERVAL '2 hours' AND status='active'` — alert if count exceeds 100
- IDX compliance check (runs every 4 hours): compare `ListingModificationTimestamp` from RESO API against local `updated_at` — flag records where delta exceeds 23 hours
- Datadog integration monitor: `mls_feed.sync_duration_seconds` not reported for more than 20 minutes (dead-man's switch pattern)
- HTTP client: `429` response with `Retry-After: 3600` — alert if cumulative 429s exceed 5 in 10 minutes

**Mitigation**

Implement a circuit breaker on the MLS feed client: after 3 consecutive failures, open the circuit for 5 minutes before retrying. Store RESO OAuth2 tokens with their `expires_in` value and proactively refresh 60 seconds before expiry using a background token refresh job. Use the RESO Web API `DeletedListingKey` endpoint or `StandardStatus=Withdrawn` + `StandardStatus=Closed` filter to explicitly detect sold/withdrawn listings — do not rely solely on `ModificationTimestamp` to infer deletions. Maintain a `feed_snapshot` table: on each successful sync, record the set of `ListingKey` values returned; on reconnection, diff against the current active set to identify listings that disappeared (were deleted/withdrawn) during the outage. Mark listings as `data_stale` after 2 hours without a successful sync and suppress them from public search results (replace with a "contact us for current status" CTA) to maintain IDX compliance. Store MLS board maintenance windows in the scheduler and skip alerting during known windows.

**Recovery**

On reconnection: run a full reconciliation sync (`$filter=ModificationTimestamp ge :last_successful_sync_time`) to capture all changes. Use the `feed_snapshot` diff to identify and deactivate listings that were active before the outage but are absent from the reconnection response. For each deactivated listing, set `status='pending_verification'` and trigger a property manager review notification rather than immediately removing from the site. Apply price updates immediately upon ingestion, with a `price_change_log` entry for audit purposes. Verify IDX compliance by re-running the compliance checker against all listings modified or re-activated during the recovery sync. If the outage exceeded 24 hours, file a proactive disclosure with the MLS board's IDX compliance officer to document the technical failure and remediation steps.
