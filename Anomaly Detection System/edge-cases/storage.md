# Edge Cases - Storage & Retention

### 5.1. Hot vs Cold Data
* **Scenario**: Queries include long historical ranges.
* **Impact**: Slow responses and high storage costs.
* **Solution**:
	* **Storage**: Tier data into hot and cold storage.
	* **Routing**: Query recent data first and fall back to cold storage.

### 5.2. Partial Writes
* **Scenario**: An anomaly record is saved but alert metadata fails.
* **Impact**: Data inconsistency and missing alerts.
* **Solution**:
	* **Consistency**: Use transactions or an outbox pattern.
	* **Retries**: Reconcile missing alert metadata asynchronously.

### 5.3. Retention Policy Violations
* **Scenario**: Data is not purged on schedule.
* **Impact**: Compliance issues and rising storage costs.
* **Solution**:
	* **Lifecycle**: Scheduled retention jobs with audit logs.
	* **Monitoring**: Alerts on retention drift.

### 5.4. Schema Evolution
* **Scenario**: Schema changes break existing queries.
* **Impact**: Dashboard and API errors.
* **Solution**:
	* **Versioning**: Backward-compatible migrations and versioned schemas.
	* **Testing**: Canary read tests after schema changes.

### 5.5. High-Cardinality Indexes
* **Scenario**: Indexes created on high-cardinality tags.
* **Impact**: Slow queries and large storage footprint.
* **Solution**:
	* **Tuning**: Limit indexes and cap tag cardinality.
	* **Guidance**: Warn on index creation for high-cardinality fields.

## Purpose and Scope
Covers storage edge behavior including tiering, retention conflicts, restore performance, and consistency checks.

## Assumptions and Constraints
- Hot/warm/archive tiers are policy-managed and observable.
- Restores are testable and include integrity verification.
- Retention can vary by data class and jurisdiction.

### End-to-End Example with Realistic Data
Raw stream writes ~1.8 TB/day; lifecycle policy keeps 30 days hot, 180 days warm, archive to year 2. Restore of prefix `2026/02/14` completes in 43 minutes and replay validates checksums.

## Decision Rationale and Alternatives Considered
- Adopted tiered storage to balance cost and forensic readiness.
- Rejected single-tier hot storage due unsustainable cost.
- Added immutable snapshots for case evidence durability.

## Failure Modes and Recovery Behaviors
- Archive retrieval delay exceeds SLA -> prefetch strategy for high-risk periods.
- Retention policy conflict across jurisdictions -> stricter policy wins and compliance ticket created.

## Security and Compliance Implications
- Storage encryption keys are segregated by data class and environment.
- Access to archived evidence requires dual-authorization for sensitive cases.

## Operational Runbooks and Observability Notes
- Storage metrics include object growth, retrieval latency, and restore success rate.
- Runbook details checksum validation and replay reconciliation after restore.
