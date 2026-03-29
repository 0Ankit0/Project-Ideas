# Edge Cases - Feature Engineering

### 2.1. Cold Start Windows
* **Scenario**: There is insufficient history to compute rolling features.
* **Impact**: Features are noisy and scoring becomes unstable.
* **Solution**:
	* **Baseline**: Use default baselines and warm-up thresholds.
	* **Blending**: Gradually mix learned statistics as data accumulates.

### 2.2. Window Boundary Artifacts
* **Scenario**: Aggregation windows cause spikes at boundaries.
* **Impact**: False positives around bucket changes.
* **Solution**:
	* **Smoothing**: Use overlapping windows and rolling averages.
	* **Policy**: Exclude boundary-only spikes from alerting when possible.

### 2.3. Category Explosion
* **Scenario**: New tags or labels create high-cardinality dimensions.
* **Impact**: Memory growth and degraded model performance.
* **Solution**:
	* **Capping**: Limit top-k categories and bucket the rest as “other”.
	* **Monitoring**: Alert on cardinality growth thresholds.

### 2.4. Feature Leakage
* **Scenario**: Features accidentally include future data.
* **Impact**: Inflated accuracy and poor real-time performance.
* **Solution**:
	* **Validation**: Enforce event-time ordering and strict cutoff.
	* **Testing**: Add unit tests for leakage in feature pipelines.

### 2.5. Zero Variance Features
* **Scenario**: Features remain constant over long periods.
* **Impact**: Scaling issues and model instability.
* **Solution**:
	* **Filtering**: Drop features with variance below a threshold.
	* **Telemetry**: Track variance to detect data stagnation.

### 2.6. Missing Feature Dependencies
* **Scenario**: A dependent feature is missing due to upstream failures.
* **Impact**: Downstream feature calculation fails.
* **Solution**:
	* **Fallback**: Substitute default values and flag partial computation.
	* **Alerting**: Notify on recurring missing dependency events.

## Purpose and Scope
Documents feature computation edge cases: sparsity, late data, skew, and fallback feature policies.

## Assumptions and Constraints
- Online and offline feature definitions are generated from one registry.
- Missingness indicators are explicit features, not implicit null semantics.
- Feature freshness windows are enforced in serving path.

### End-to-End Example with Realistic Data
For account `A-77`, compute `rolling_txn_count_5m=14`, `geo_entropy_24h=2.8`; if geolocation missing, use `UNK` bucket + `geo_missing=true` to preserve model behavior consistency.

## Decision Rationale and Alternatives Considered
- Kept feature parity contract between batch and real-time pipelines.
- Rejected silent imputation because it obscures data quality issues.
- Added drift-sensitive features only with guardrail monitoring.

## Failure Modes and Recovery Behaviors
- Feature registry mismatch online/offline -> block model promotion until parity restored.
- Late data modifies aggregates unexpectedly -> watermark + correction event strategy.

## Security and Compliance Implications
- Features derived from sensitive attributes require policy review and documentation.
- Feature tables carry lineage tags for explainability audits.

## Operational Runbooks and Observability Notes
- Monitor null-rate, freshness, and distribution drift per feature family.
- Runbook includes emergency feature disable flags and fallback set activation.
