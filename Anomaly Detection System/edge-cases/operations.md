# Edge Cases - Operations & Deployment

### 8.1. Failed Deployments
* **Scenario**: A new release increases error rates.
* **Impact**: Service degradation and missed detections.
* **Solution**:
	* **Rollout**: Canary deployments with automated rollback.
	* **Monitoring**: Error budgets and regression alerts.

### 8.2. Model/Code Version Mismatch
* **Scenario**: Scoring uses an incompatible model artifact.
* **Impact**: Runtime failures or incorrect scores.
* **Solution**:
	* **Compatibility**: Version pinning and compatibility checks.
	* **Registry**: Enforce model metadata validation before deploy.

### 8.3. Multi-Region Failover
* **Scenario**: Regional outage impacts ingestion.
* **Impact**: Alert gaps and data loss risk.
* **Solution**:
	* **Architecture**: Active-active ingestion with shared model registry.
	* **Failover**: Automated traffic routing and replay queues.

### 8.4. Clock Skew
* **Scenario**: Node clocks drift out of sync.
* **Impact**: Incorrect event ordering and windowing.
* **Solution**:
	* **Time Sync**: Enforce NTP on all nodes.
	* **Validation**: Reject or flag large timestamp skew.

### 8.5. Long Rebuild Times
* **Scenario**: Recovery after outage is slow.
* **Impact**: Prolonged downtime and backlog growth.
* **Solution**:
	* **Preparedness**: Pre-warmed nodes and immutable images.
	* **Automation**: IaC templates and fast bootstrap scripts.