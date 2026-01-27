# Edge Cases - Security & Compliance

### 7.1. PII Leakage in Logs
* **Scenario**: Sensitive fields appear in application logs.
* **Impact**: Compliance violations and breach risk.
* **Solution**:
	* **Redaction**: Use allowlist logging and PII scrubbing.
	* **Storage**: Send logs to secure, access-controlled sinks.

### 7.2. Secret Rotation Failures
* **Scenario**: Integrations fail after secret rotation.
* **Impact**: Alerting or ingestion outages.
* **Solution**:
	* **Overlap**: Support dual-secret windows during rotation.
	* **Verification**: Automated revalidation after rotation.

### 7.3. Access Creep
* **Scenario**: Users retain access after role changes.
* **Impact**: Unauthorized data exposure.
* **Solution**:
	* **Governance**: Periodic access reviews.
	* **Provisioning**: SCIM-based automatic deprovisioning.

### 7.4. Tenant Data Isolation
* **Scenario**: Cross-tenant data visibility.
* **Impact**: Severe compliance and security risk.
* **Solution**:
	* **Isolation**: Row-level security and tenant-bound tokens.
	* **Testing**: Automated tests for tenant boundaries.

### 7.5. Audit Log Tampering
* **Scenario**: Audit records are missing or altered.
* **Impact**: Loss of compliance evidence.
* **Solution**:
	* **Immutability**: Write-once storage and hash chaining.
	* **Monitoring**: Alerts on audit log gaps.