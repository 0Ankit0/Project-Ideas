# Edge Cases — Operations

## EC-OPS-001: DLQ Overflow

**Scenario:** EventBridge consumers fail repeatedly, flooding the dead letter queue.

**Trigger:** Downstream service outage (e.g., Notification Service down).

**Expected Behaviour:**
- SQS DLQ depth monitored via CloudWatch: alarm at > 10 messages for 15 min
- DLQ messages retain original event payload and failure metadata
- Automated redrive runbook: CloudWatch Alarm → SNS → Lambda → redrive DLQ to source queue
- If redrive also fails → SEV-2 alert to on-call engineer
- DLQ retention: 14 days (SQS maximum)

---

## EC-OPS-002: RDS Primary Failure

**Scenario:** RDS primary instance crashes or becomes unreachable.

**Trigger:** Hardware failure, storage corruption, or AZ outage.

**Expected Behaviour:**
- Multi-AZ automatic failover: standby promoted to primary (< 2 min RTO)
- DNS endpoint (`oms-db.cluster-xxx.rds.amazonaws.com`) remains unchanged
- Application connections dropped; connection pool retries with backoff
- During failover window (60-120 s):
  - Read operations route to read replica (degraded but functional)
  - Write operations queue and retry
- CloudWatch alarm triggers SEV-1 page to on-call engineer

---

## EC-OPS-003: Lambda Cold Start Impact on Checkout

**Scenario:** First request after idle period hits Lambda cold start latency (3-5 s), causing checkout to feel slow.

**Trigger:** Low-traffic periods followed by burst.

**Expected Behaviour:**
- Order and Payment Lambda functions use provisioned concurrency (10 instances each)
- Provisioned instances are always warm; no cold start for critical paths
- Non-critical functions (Notification, Search Sync) accept cold start trade-off
- CloudWatch alarm: if Lambda duration P95 > 10 s for 5 min → SEV-2

---

## EC-OPS-004: OpenSearch Cluster Failure

**Scenario:** OpenSearch cluster becomes unavailable, breaking product search.

**Trigger:** Node failure, storage full, or JVM out of memory.

**Expected Behaviour:**
- Product search degrades to RDS `LIKE` query fallback (slower but functional)
- API response includes `X-Search-Degraded: true` header
- Customer experience: search results may be less relevant; sort-by-relevance unavailable
- OpenSearch alerts: cluster health → RED → SEV-2 page
- Recovery: automated snapshot restore (hourly snapshots, 14-day retention)

---

## EC-OPS-005: EventBridge Bus Throttling

**Scenario:** Event publish rate exceeds EventBridge quota during flash sale.

**Trigger:** > 10,000 events/second sustained.

**Expected Behaviour:**
- EventBridge default quota: 10,000 PutEvents/second (soft limit, can be increased)
- If throttled → Lambda receives ThrottlingException; retries with backoff
- Critical events (payment, order) use dedicated event bus with higher quota
- Non-critical events (analytics, audit) batched and published at reduced rate
- Pre-flash-sale preparation: request quota increase 72 hours in advance

---

## EC-OPS-006: S3 Upload Failure During Spike

**Scenario:** Multiple delivery staff uploading POD photos simultaneously overwhelms the upload path.

**Trigger:** End-of-day delivery completion surge.

**Expected Behaviour:**
- S3 handles virtually unlimited concurrent uploads (no capacity concern)
- Bottleneck is mobile network bandwidth, not S3
- POD uploads use S3 presigned URLs — each staff uploads directly to S3, bypassing API Gateway
- API Gateway and Lambda not involved in the upload data path (only in URL generation)
- Presigned URL validity: 15 minutes; max file size enforced in URL policy

---

## EC-OPS-007: CDK Deployment Failure Mid-Stack

**Scenario:** CDK deployment fails halfway through (e.g., IAM policy error), leaving stack in `UPDATE_ROLLBACK_IN_PROGRESS`.

**Trigger:** Configuration error, resource limit, or service quota exceeded.

**Expected Behaviour:**
- CloudFormation automatic rollback restores previous stable state
- No manual intervention needed for standard rollbacks
- If rollback itself fails (rare) → stack enters `UPDATE_ROLLBACK_FAILED`
- Recovery: `aws cloudformation continue-update-rollback` with problematic resources skipped
- All deployments go through staging first; production uses manual approval gate in CodePipeline
