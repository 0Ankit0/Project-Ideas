# Edge Cases - Operations

### 9.1. Vendor API Outage
* **Scenario**: Vendor systems fail to sync inventory.
* **Impact**: Stale availability and order failures.
* **Solution**:
    * **Fallback**: Temporarily disable vendor listings or require confirmation.
    * **Monitoring**: Alert on sync failures.

### 9.2. Search Index Lag
* **Scenario**: Search index updates lag behind catalog changes.
* **Impact**: Users see outdated results.
* **Solution**:
    * **Pipeline**: Ensure near-real-time indexing.
    * **UI**: Indicate “new” items may take time to appear.

### 9.3. Release Regression
* **Scenario**: A new release breaks checkout or payments.
* **Impact**: Revenue loss.
* **Solution**:
    * **Rollout**: Canary deployments and automated rollback.
    * **Testing**: End-to-end smoke tests post-deploy.