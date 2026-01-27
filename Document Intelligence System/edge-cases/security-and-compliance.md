# Edge Cases - Security & Compliance

### 7.1. PII Exposure in Exports
* **Scenario**: Exports include sensitive fields without masking.
* **Impact**: Compliance violations and data leaks.
* **Solution**:
    * **Policy**: Enforce role-based export permissions and masking rules.
    * **Audit**: Log exports and provide traceability.

### 7.2. Access Creep
* **Scenario**: Users retain access after role changes.
* **Impact**: Unauthorized data access.
* **Solution**:
    * **Governance**: Periodic access reviews and SCIM deprovisioning.
    * **Controls**: Short-lived tokens and session revocation.

### 7.3. Data Retention Violations
* **Scenario**: Documents persist beyond retention policy.
* **Impact**: Regulatory risk and storage cost.
* **Solution**:
    * **Lifecycle**: Automated purge jobs with audit logs.
    * **Controls**: Legal hold exceptions with approvals.