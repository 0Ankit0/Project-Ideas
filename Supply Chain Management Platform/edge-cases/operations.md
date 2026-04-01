# Supply Chain Management Platform - Operations Edge Cases

## Scenario 1: ERP SAP Integration Failure During PO Sync

**Failure Mode**: PO created in platform. Automatic sync job attempts to post PO to SAP GL account. SAP API returns 500 error (temporary outage). PO remains in "SentToSupplier" state, but cost center GL account not updated in SAP. Finance can't see PO commitment. Subledger and GL out of sync.

**Symptoms**:
- PO status in platform: "SentToSupplier"
- SAP GL account: no cost center posting (PO not visible)
- Sync job logs: "SAP API 500 error" at timestamp
- Finance report: PO commitment missing from budget report

**Impact**:
- Finance Impact: Budget commitment invisible. Can't track spending against budget.
- Reconciliation: GL-to-subledger mismatch discovered during month-end close.
- Severity: 🟠 High (financial reporting error)

**Detection**:
- Monitor SAP sync job: alert if >3 failures in 1 hour
- Reconciliation job: nightly GL-PO matching, alert on mismatches
- Finance dashboard: show pending GL posts

**Mitigation**:
1. Retry logic: exponential backoff (1s, 2s, 4s, 8s, 60s, 300s)
2. Circuit breaker: if SAP failing, queue POs locally, batch retry hourly
3. Compensating transaction: if sync fails, create manual journal entry in SAP with next-day batch
4. Dual-write: capture GL posting intent in local DB, SAP updates it asynchronously

**Recovery**:
1. Auto-retry completes successfully after 5 minutes
2. If manual intervention needed: finance team manually posts journal entry to GL
3. Reconciliation: next nightly job detects post was made, clears mismatch alert

---

## Scenario 2: Peak Renewal Season — Simultaneous Mass RFQ Processing

**Failure Mode**: January contract renewal season. 500 RFQs generated for annual contracts. All sent to suppliers simultaneously. Notification service overwhelmed: can't send 500 emails in real-time. 100 suppliers don't receive RFQ. 50 RFQs generate duplicate notifications. Suppliers confused, submission deadline missed for some.

**Symptoms**:
- RFQ database: 500 RFQs created, status="IssuedToSuppliers"
- Notification service: email send queue backlog grows to 1000+ messages
- Supplier portal: only 400 suppliers see pending RFQ
- Email logs: some RFQs sent 3 times, others 0 times (idempotency failure)

**Impact**:
- Suppliers: confusion, missed deadlines
- Procurement: RFQ responses incomplete, can't make decisions
- Severity: 🟠 High (procurement process disrupted)

**Detection**:
- Monitor notification queue depth: alert if >100 pending
- Track email delivery rate: alert if failures >5%
- Supplier portal: track which suppliers see RFQ (query notification delivery status)

**Mitigation**:
1. Batch RFQ generation: spread 500 RFQs over 2 hours (250/hour), not all at once
2. Async notifications: queue to Kafka, process at steady rate (50 emails/minute)
3. Idempotency: use notification_id to prevent duplicates
4. Backpressure: if queue >200, API call to generate RFQ returns 429, user retries later

**Recovery**:
1. Automatic: queue drains, suppliers gradually receive RFQs
2. Manual: procurement team identifies suppliers who didn't receive, manually resend

---

## Scenario 3: Supplier Portal Bulk Upload Failure (10K Items)

**Failure Mode**: Large supplier attempts bulk upload of 10,000 line items for quotation (for a large RFP). File processing starts, but hits error at item #8,000 (data validation fails). Entire upload rejected. Supplier loses 2 hours of work entering data.

**Symptoms**:
- Upload progress: 8000/10000
- Error message: "Validation failed at row 8001" (no helpful detail)
- All 10,000 items rejected (all-or-nothing)
- Supplier frustrated: has to re-enter everything

**Impact**:
- Supplier Experience: terrible UX
- Procurement Impact: supplier misses RFP deadline due to frustration/time lost
- Severity: 🟡 Medium (affects individual supplier, but impacts RFQ response rate)

**Detection**:
- Monitor bulk upload failures: alert if >10 per day
- Track upload file size: identify problematic large uploads
- User support tickets: "Bulk upload failed"

**Mitigation**:
1. Partial success: upload 8000 items, show error with detail for item #8001
2. Detailed validation errors: "Row 8001: Unit Price must be > 0. Provided: -5.00"
3. Download template: pre-formatted Excel with data validation rules (catches errors before upload)
4. Staged rollback: save progress every 100 items, allow resume from failure point
5. Batch size limit: warn if >1000 items, suggest chunking into multiple uploads

**Recovery**:
1. Supplier fixes item #8001 in downloaded error file, re-uploads just corrected items
2. Platform merges corrected items with already-uploaded items 8000

---

## Scenario 4: Invoice Matching Batch Job Timeout at Month-End

**Failure Mode**: Month-end 3-way matching batch job processes 50,000 invoices. Matching logic is O(n²) for each invoice (searches POs and GRNs). Job running 4+ hours. Database connection pool exhausted. Subsequent invoices received can't be processed. Month-end close delayed.

**Symptoms**:
- Batch job: started 10 PM, still running at 2 AM (>4 hours)
- Database connections: pool at 100/100 (exhausted)
- New invoice receipts: "Cannot connect to database" (timeout)
- Finance: can't close month-end

**Impact**:
- Financial: month-end close delayed by 1+ days
- Severity: 🔴 Critical (financial operations blocked)

**Detection**:
- Monitor batch job duration: alert if >2 hours
- Database connection pool: alert if utilization >80%
- Invoice inflow during batch: alert if unable to process new invoices

**Mitigation**:
1. Optimize matching query: use indexed lookups (not full table scans)
   - Index: (supplier_id, po_number, quantity) for fast lookup
   - Indexed join: PO ↔ GRN ↔ Invoice (3-way join)
2. Partition by supplier: run matching for each supplier in parallel (8 workers)
3. Batch size: process 1000 invoices per transaction, commit frequently (release connections)
4. Stagger month-end: process previous 2 days' invoices during off-peak (5 PM), finish remaining at month-end (10 PM)

**Recovery**:
1. Kill batch job if running >2 hours, restart with optimized logic
2. Run invoice matching incrementally: 10,000 invoices at a time
3. Delay month-end close by a few hours if necessary

---

## Scenario 5: 3-Way Match Failure Due to Goods Receipt Data Corruption

**Failure Mode**: Goods receipt operator enters GRN quantity = 100, but due to typo, data saved as qty = 10000. Invoice arrives for qty = 100. 3-way match fails: GRN qty (10000) ≠ Invoice qty (100). Invoice goes to "OnHold" status. Finance can't process payment. Supplier's cash flow impacted.

**Symptoms**:
- Invoice status: "OnHold" for 3-way match failure
- Variance: 9900 units difference (variance >99%)
- GRN record shows qty = 10000 (clearly wrong)
- Finance: invoice unpaid, vendor complains

**Impact**:
- Supplier Impact: payment delayed, cash flow impact
- Procurement Impact: GRN incorrect, inventory wrong
- Severity: 🟠 High (payment delayed, inventory incorrect)

**Detection**:
- 3-way match variance: alert if variance >50% (likely data error)
- GRN quantity sanity check: alert if qty > PO qty * 110% (over-receipt >10%)
- Warehouse manager: verifies actual goods received matches GRN

**Mitigation**:
1. Data validation on GRN entry: qty must be ≤ PO qty (hard constraint)
2. GRN supervisor approval: manager must approve GRN before posting to inventory
3. Variance tolerance: allow ±5% variance (normal for goods receipt)
4. Manual investigation: variance >20% goes to supervisor for review before match approval

**Recovery**:
1. Identify corrupted GRN: qty = 10000 is obviously wrong
2. Correct GRN: operator corrects to qty = 100
3. Re-trigger 3-way match: now passes
4. Invoice automatically approved for payment

---

## Scenario 6: Elasticsearch Reindex Blocking Supplier Search

**Failure Mode**: Add new field to supplier index (supplier_quality_score). Elasticsearch reindexing 100,000 suppliers takes 4 hours. During reindex, search service is unavailable (or extremely slow). Procurement manager can't search for suppliers. RFQ creation delayed.

**Symptoms**:
- Search endpoint: returns 503 "Service Unavailable" or times out after 30s
- Elasticsearch logs: reindexing in progress
- User: can't find supplier by name during critical RFQ creation

**Impact**:
- Procurement delay: can't search suppliers, delays RFQ process
- Severity: 🟠 High (search unavailable during reindex)

**Detection**:
- Monitor Elasticsearch query latency: alert if p99 > 5s
- Search endpoint: alert if 503 or timeout >1% of requests

**Mitigation**:
1. Blue-green deployment: create new index, reindex to new index, switch alias (no downtime)
2. Schedule reindex off-peak: after 6 PM when procurement team not using system
3. Background reindex: reindex at low priority, users can still search old index
4. Async field population: don't reindex, add new field with lazy evaluation

**Recovery**:
- Reindex completes, search returns to normal

---

## Scenario 7: Document Storage S3 Failure During Contract Signing

**Failure Mode**: Contract finalization flow: operator uploads signed contract PDF to S3. S3 service degradation: put_object returns 503. Contract upload fails. Operator retries 3 times, then gives up. Contract not stored. Contract status remains "Pending Signing" forever. Financial controller can't see final contract terms.

**Symptoms**:
- Contract status: "Pending Signing" (stuck)
- S3 logs: 503 Service Unavailable errors
- Operator: "Upload failed, please try again"
- Finance: contract missing from system

**Impact**:
- Contract tracking: missing signed contract
- Audit trail: incomplete contract history
- Severity: 🟡 Medium (contract missing, but not critical until audit/dispute)

**Detection**:
- Monitor S3 put_object errors: alert if failure rate >1%
- Contract status: alert if >1 contract stuck in "Pending Signing" for >24h
- Retry logic: alert if 3 consecutive upload failures

**Mitigation**:
1. Retry with exponential backoff (1s, 2s, 4s, 8s)
2. Upload to backup S3 region if primary fails
3. Local cache: save to local disk if S3 fails, sync batch later
4. User notification: show retry progress, don't immediately fail

**Recovery**:
1. S3 recovers → manual retry succeeds
2. Batch sync job: upload locally-cached contracts to S3 nightly

---

## Scenario 8: Kafka Consumer Lag During Mass Notification Storm

**Failure Mode**: Month-end invoice processing spike: 50,000 invoices sent to payment approval flow. Kafka topic "invoice-approved-for-payment" gets 50,000 messages in 5 minutes. Notification consumer processes at 100 msg/min. Consumer lag grows to 40,000 messages. Notifications to finance team delayed by 6+ hours.

**Symptoms**:
- Kafka consumer lag: 40,000 messages queued
- Notifications: finance team doesn't get alerts about approved invoices for 6 hours
- Finance: can't initiate payments in timely manner

**Impact**:
- Finance Impact: delayed payment processing, cash flow
- Supplier Impact: invoices paid late
- Severity: 🟠 High (payment delayed)

**Detection**:
- Monitor Kafka consumer lag: alert if lag > 5000 messages
- Alert if lag growing rate > 1000 messages/minute for >5 minutes

**Mitigation**:
1. Batch notifications: send 100 invoices in single message (reduce msg count 100x)
2. Sampling: if lag >10,000, send notification only to 10% of finance team (show count)
3. Prioritize: urgent invoices (>$100K) get immediate notification, others batched
4. Increase consumers: spawn 5 notification workers instead of 1 (5x throughput)
5. Async notifications: don't block invoice approval on notification delivery

**Recovery**:
- Consumer catches up when lag < 1000 messages, scale down workers

---

## Summary

These 8 operations edge cases cover:
- ERP integration failures and recovery
- Notification system load management
- Data quality and validation
- Performance optimization under load
- Document storage reliability
- Asynchronous processing reliability
- Cost and efficiency during peak periods

All scenarios include detection mechanisms, mitigation strategies, and recovery procedures. Most are preventable with proper design and monitoring.
