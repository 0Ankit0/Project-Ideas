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