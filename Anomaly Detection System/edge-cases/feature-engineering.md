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