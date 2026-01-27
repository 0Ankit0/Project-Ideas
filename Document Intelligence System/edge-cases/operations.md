# Edge Cases - Operations

### 8.1. OCR Vendor Outage
* **Scenario**: External OCR service becomes unavailable.
* **Impact**: Processing pipeline halts or slows.
* **Solution**:
    * **Failover**: Switch to backup OCR engine.
    * **Queueing**: Buffer jobs until service recovers.

### 8.2. GPU Resource Exhaustion
* **Scenario**: GPU capacity is saturated during peak load.
* **Impact**: Increased latency and backlog.
* **Solution**:
    * **Scaling**: Autoscale GPU nodes and apply workload prioritization.
    * **Fallback**: Route non-critical workloads to CPU.

### 8.3. Model Version Drift
* **Scenario**: Production uses mixed model versions.
* **Impact**: Inconsistent extraction quality.
* **Solution**:
    * **Deployment**: Version pinning and rollout controls.
    * **Audit**: Track model version per document.