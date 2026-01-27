# Edge Cases - Security & Compliance

### 6.1. Unauthorized Provider Access
* **Scenario**: A provider accesses another provider’s bookings.
* **Impact**: Data leakage and compliance risk.
* **Solution**:
    * **Authorization**: Enforce tenant and provider-level RBAC.
    * **Audit**: Log all access to booking records.

### 6.2. PII in Logs
* **Scenario**: Sensitive data is logged unintentionally.
* **Impact**: Compliance violations.
* **Solution**:
    * **Redaction**: Mask PII in logs.
    * **Controls**: Restricted log access and retention limits.