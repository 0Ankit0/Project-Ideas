# Edge Cases - Alerting

### 4.1. Alert Storms
* **Scenario**: A burst of anomalies generates hundreds of alerts.
* **Impact**: On-call fatigue and missed critical alerts.
* **Solution**:
	* **Aggregation**: Deduplicate and batch alerts by source and severity.
	* **Throttling**: Apply rate limits per channel and tenant.

### 4.2. Flapping Alerts
* **Scenario**: Alerts toggle between open and closed repeatedly.
* **Impact**: Noisy notifications and unclear status.
* **Solution**:
	* **Hysteresis**: Use upper/lower thresholds and cool-down timers.
	* **Rules**: Require N consecutive breaches before alerting.

### 4.3. Silent Failures
* **Scenario**: Alert delivery silently fails.
* **Impact**: Missed incidents and SLA breaches.
* **Solution**:
	* **Health Checks**: Track delivery success rate per channel.
	* **Reliability**: Retries with exponential backoff and DLQ.

### 4.4. Escalation Loops
* **Scenario**: Alerts keep escalating without resolution.
* **Impact**: Escalation fatigue and noise.
* **Solution**:
	* **Limits**: Cap escalation depth and duration.
	* **Automation**: Auto-suppress with owner notification after threshold.

### 4.5. Quiet Hours Violations
* **Scenario**: Alerts are sent during quiet hours.
* **Impact**: Violates on-call policy and reduces trust.
* **Solution**:
	* **Validation**: Test schedule rules before activation.
	* **Fallback**: Send only critical alerts during quiet hours.

### 4.6. Duplicate Notifications
* **Scenario**: Multiple channels send the same alert repeatedly.
* **Impact**: Alert spam and confusion.
* **Solution**:
	* **Idempotency**: Use message fingerprinting and idempotent webhooks.
	* **Tracking**: Store per-channel delivery keys.