# Edge Cases - Security & Compliance

### 6.1. PII in Feature Store
* **Scenario**: Sensitive user attributes are stored in features.
* **Impact**: Compliance and privacy risk.
* **Solution**:
    * **Policy**: Pseudonymize user identifiers and restrict feature access.
    * **Audit**: Access logs and periodic reviews.

### 6.2. Training Data Leakage
* **Scenario**: Data used for training includes private events.
* **Impact**: Legal and trust issues.
* **Solution**:
    * **Governance**: Data lineage and consent checks.
    * **Controls**: Exclude opted-out users.

## Implementation Mitigation Blueprint
### Detection Signals
- Define concrete metrics/log signatures for security and compliance failures, with alert thresholds and pager routes.

### Automated Mitigations
- Feature flags, circuit breakers, and policy filters should mitigate user impact before manual intervention.

### Verification
- Add chaos/simulation tests reproducing top failure patterns and confirm fallback quality remains within baseline thresholds.
