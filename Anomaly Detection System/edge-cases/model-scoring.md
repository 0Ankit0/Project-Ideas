# Edge Cases - Model Scoring

### 3.1. Model Not Ready
* **Scenario**: A model version is not available during deployment or rollback.
* **Impact**: Scoring halts or produces errors.
* **Solution**:
	* **Fallback**: Use rule-based thresholds until model is ready.
	* **Queueing**: Buffer events for later scoring if acceptable.

### 3.2. Concept Drift
* **Scenario**: Data distributions shift over time.
* **Impact**: Accuracy degrades, alert volume spikes.
* **Solution**:
	* **Detection**: Track drift metrics per feature and model.
	* **Automation**: Trigger retraining and shadow deployment.

### 3.3. Threshold Miscalibration
* **Scenario**: Thresholds are too strict or too lax.
* **Impact**: Excessive false positives or missed anomalies.
* **Solution**:
	* **Calibration**: Per-tenant thresholds and dynamic percentile-based thresholds.
	* **Feedback**: Use human labels to tune thresholds.

### 3.4. Unseen Categories
* **Scenario**: New categorical values appear at inference.
* **Impact**: Model errors or unpredictable scores.
* **Solution**:
	* **Encoding**: Map to “unknown” bucket.
	* **Monitoring**: Track frequency and trigger retraining if high.

### 3.5. Scoring Latency Spikes
* **Scenario**: Model inference time exceeds SLA.
* **Impact**: Alert delays and backlog growth.
* **Solution**:
	* **Performance**: Batch scoring, caching, and autoscaling.
	* **Optimization**: Model quantization or distillation.

### 3.6. Numerical Instability
* **Scenario**: Inputs produce NaN/Inf scores.
* **Impact**: Pipeline errors or incorrect anomaly scores.
* **Solution**:
	* **Validation**: Clamp inputs and validate ranges.
	* **Fallback**: Reject malformed events with error telemetry.

## Purpose and Scope
Covers runtime scoring anomalies, model divergence, calibration issues, and safe fallback behavior.

## Assumptions and Constraints
- Primary and shadow model outputs are continuously compared.
- Decision thresholds are policy-managed and versioned.
- Scoring service must return explainability metadata for high-risk decisions.

### End-to-End Example with Realistic Data
Primary `xgb_2026_03` returns 0.83 while shadow `lstm_2026_03` returns 0.62 on same event; divergence over threshold opens governance ticket and increases manual-review sampling for affected cohort.

## Decision Rationale and Alternatives Considered
- Kept shadow scoring in production to detect silent quality regressions.
- Rejected automatic threshold retuning without governance approval.
- Used calibrated probabilities over raw margins for operational stability.

## Failure Modes and Recovery Behaviors
- Model endpoint latency spikes -> fallback model or rules-only path with degraded flag.
- Calibration drift detected -> freeze promotions and trigger retraining workflow.

## Security and Compliance Implications
- Model artifacts are signed and referenced by immutable digest.
- Scoring logs avoid storing raw sensitive inputs; only necessary derived context retained.

## Operational Runbooks and Observability Notes
- Monitor precision/recall proxies, drift, calibration error, and latency.
- Runbook details model rollback, threshold freeze, and communication plan.


### 3.7. Model Rollback Safety
* **Scenario**: Newly promoted model degrades quality or latency and must be reverted quickly.
* **Impact**: Incorrect anomaly decisions and customer-visible alert quality issues.
* **Solution**:
	* **Preparedness**: Keep last-known-good model and manifest digest hot in each region.
	* **Execution**: One-command rollback with automated traffic shift and post-rollback verification.
	* **Validation**: Compare pre/post rollback precision proxy, latency, and alert volume before closing incident.

### 3.8. Schema Drift at Scoring Boundary
* **Scenario**: Feature schema changes (type/order/semantic drift) break model input expectations.
* **Impact**: Runtime errors, NaN outputs, or silent quality degradation.
* **Solution**:
	* **Contract Checks**: Reject incompatible requests using feature schema fingerprint validation.
	* **Fallback**: Route to compatible previous feature set and flag degraded mode.
	* **Escalation**: Block promotions and open schema-governance incident automatically.
