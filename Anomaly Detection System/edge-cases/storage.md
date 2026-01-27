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