# Edge Cases – Provider Selection and Provisioning

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | User selects provider combination with incompatible capability assumptions | High | Project setup fails at runtime | Validate compatibility profiles during binding creation; return `BINDING_COMPATIBILITY_MISMATCH` before activation |
| 2 | Provider adapter passes readiness check but fails under real load | High | Silent partial outage | Health checks use representative probe payloads; probe failures trigger `degraded` binding state with alerting |
| 3 | Two project owners attempt to activate the same provider binding simultaneously | Medium | Duplicate binding activation, race condition | Optimistic concurrency with `version` field; second writer receives `STATE_CONFLICT` error |
| 4 | Adapter version deprecated mid-binding lifecycle | Medium | Future operations fail silently | Adapter deprecation window announced 90 days in advance; bindings on deprecated adapters enter `migration-required` state |
| 5 | Provider requires region-specific endpoint not available in the deployment region | High | Binding activation fails with cryptic error | Validate provider endpoint reachability during binding creation; surface `BINDING_REGION_UNAVAILABLE` |
| 6 | Operator removes a provider from the catalog while active bindings exist | Critical | Active bindings become orphaned | Soft-delete only; active bindings prevent catalog removal; operator must migrate or force-deprecate first |
| 7 | Binding is `active` but provider credentials have expired | High | All requests to that capability fail | Secret expiry monitoring; alert 7 days before expiry; binding moves to `credential-expired` sub-state |
| 8 | Compatibility profile check passes at binding time but provider silently changes its API | High | Runtime failures after a provider update | Adapter contract tests (Pact) run nightly against live provider sandboxes; failures page on-call |

## Deep Edge Cases

### Race Condition: Dual Binding Activation
```
T1: Owner A calls POST /bindings (storage, aws-s3)
T2: Owner A calls POST /bindings (storage, gcs) [accidental double-click]
Both requests hit concurrency guard on (env_id, capability_key) UNIQUE constraint in PostgreSQL.
Second request receives HTTP 409 CONFLICT with current binding state.
```

### Credential Rotation During Active Binding
- Platform polls `secret_refs` for TTL < 7 days.
- Proactive notification sent to Project Owner.
- If expiry is missed, binding health-check fails and capability enters `degraded` state.
- Worker retries capability calls with exponential backoff for 10 minutes before marking `BINDING_CREDENTIAL_EXPIRED`.

### Cascade on Provider Catalog Entry Removal
- Soft-delete sets `deprecated_at` timestamp.
- Job scans active bindings referencing deprecated entry.
- Owners receive in-platform notification + email.
- After 90 days, bindings with no switchover plan are automatically suspended.

## State Impact Summary

| Scenario | Binding State Transition |
|----------|------------------------|
| Compatibility mismatch | `validating` → `failed` |
| Readiness probe failure | `active` → `degraded` |
| Concurrent binding conflict | Second request rejected; no state change |
| Adapter deprecation | `active` → `migration-required` |
| Credential expiry | `active` → `credential-expired` |

---

## Recovery Procedures

### Runbook: Orphaned Binding after Provider Removal

**Trigger:** Catalog entry for a provider is force-deprecated while active bindings exist.

1. Identify affected bindings:
   ```sql
   SELECT b.id, b.project_id, b.env_id, b.capability_key, b.state
   FROM capability_bindings b
   JOIN provider_catalog_entries c ON b.provider_catalog_entry_id = c.id
   WHERE c.deprecated_at IS NOT NULL
     AND b.state NOT IN ('suspended', 'failed');
   ```
2. Notify project owners via in-platform notification and email (automated by `DeprecationNotificationJob`).
3. Set all identified bindings to `migration-required`:
   ```sql
   UPDATE capability_bindings
   SET state = 'migration-required', updated_at = NOW()
   WHERE id = ANY($1::uuid[]);
   ```
4. If no switchover plan exists after 30 days, auto-suspend:
   ```sql
   UPDATE capability_bindings
   SET state = 'suspended', suspension_reason = 'provider_deprecated'
   WHERE state = 'migration-required'
     AND updated_at < NOW() - INTERVAL '30 days';
   ```
5. Operator verifies control-plane UI shows no orphaned `active` bindings referencing deprecated entries.

### Runbook: Credential Expiry Recovery

**Trigger:** `BINDING_CREDENTIAL_EXPIRED` alert fires; binding enters `credential-expired` sub-state.

1. Alert fires when secret TTL drops below 7 days (monitored by `SecretExpiryMonitorJob`).
2. Project Owner navigates to **Project Settings → Capability Bindings → [binding] → Update Credentials**.
3. Owner provides new credential values; platform stores via Secrets Manager:
   ```typescript
   await secretsService.rotateSecret({
     secretRef: binding.credentialSecretRef,
     newValue: newCredentials,
     tenantId,
   });
   ```
4. Binding state transitions: `credential-expired` → `validating` → `active` (on successful health probe).
5. If credential rotation fails, binding remains `credential-expired`; owner receives error with `correlationId`.
6. Operator verifies binding state via:
   ```
   GET /internal/bindings/{bindingId}/health
   ```

### Runbook: Compatibility Mismatch Resolution

**Trigger:** `BINDING_COMPATIBILITY_MISMATCH` returned during binding creation or after adapter update.

1. Retrieve the compatibility report:
   ```
   GET /api/v1/bindings/compatibility-check
   Body: { "capabilityKey": "storage", "providerKey": "aws-s3", "adapterVersion": "2.1.0" }
   ```
2. Review the `incompatibleFeatures` array to identify unsupported capability flags.
3. Either: (a) choose a compatible provider, or (b) disable the unsupported features in the project's capability config.
4. Re-attempt binding creation with updated configuration.
5. If mismatch persists after adapter upgrade, escalate to Adapter Maintainer with the full compatibility report.

---

## Observability and Alerting

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `baas_binding_state_total` | Gauge | Count of bindings per state (active, degraded, migration-required, etc.) |
| `baas_binding_health_check_duration_seconds` | Histogram | Duration of adapter health probe execution |
| `baas_binding_credential_expiry_days` | Gauge | Days until credential expiry per binding |
| `baas_provider_compatibility_check_failures_total` | Counter | Total compatibility validation failures |
| `baas_adapter_circuit_breaker_state` | Gauge | 0=closed, 1=half-open, 2=open per adapter |
| `baas_catalog_deprecated_entries_total` | Gauge | Count of deprecated provider catalog entries |

### Alert Thresholds

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| `BindingDegraded` | `baas_binding_state_total{state="degraded"} > 0` | High | PagerDuty |
| `CredentialExpiryImminent` | `baas_binding_credential_expiry_days < 7` | High | Slack + Email |
| `AdapterCircuitOpen` | `baas_adapter_circuit_breaker_state == 2` | Critical | PagerDuty |
| `OrphanedBindings` | `baas_binding_state_total{state="migration-required"} > 0` sustained 24h | Medium | Slack |
| `CompatibilityCheckSpiking` | `rate(baas_provider_compatibility_check_failures_total[5m]) > 5` | Medium | Slack |

### Binding State Flow

```mermaid
stateDiagram-v2
    [*] --> validating : POST /bindings
    validating --> active : health probe passes
    validating --> failed : compatibility mismatch or probe failure
    active --> degraded : 3 consecutive health check failures
    active --> credential-expired : secret TTL = 0
    active --> migration-required : adapter deprecated
    degraded --> active : probe recovers
    credential-expired --> validating : credentials rotated
    migration-required --> active : switchover completed
    migration-required --> suspended : no plan after 30 days
```

### Dashboard Panels

- **Binding Health Overview**: pie chart of bindings by state across all environments.
- **Credential Expiry Timeline**: sorted list of bindings with expiry < 30 days.
- **Adapter Circuit Breaker Status**: heatmap of open/half-open circuits per adapter per hour.
- **Provider Availability**: rolling 1-hour health check pass rate per provider adapter.

---

## Testing Strategies

### Contract Tests (Pact)

Every `IProviderAdapter` implementation must pass consumer-driven contract tests:

```typescript
// packages/adapters/storage/s3-adapter.pact.spec.ts
describe('S3Adapter contract', () => {
  it('satisfies IStorageAdapter.getPresignedUploadUrl contract', async () => {
    pact.addInteraction({
      state: 'bucket exists and credentials are valid',
      uponReceiving: 'a presigned upload URL request',
      withRequest: { method: 'POST', path: '/presign', body: { key: 'test.txt', ttlSeconds: 300 } },
      willRespondWith: { status: 200, body: { url: like('https://'), expiresAt: iso8601DateTime() } },
    });
    const result = await s3Adapter.getPresignedUploadUrl({ key: 'test.txt', ttlSeconds: 300 });
    expect(result.isOk()).toBe(true);
  });
});
```

### Integration Tests for Binding State Machine

```typescript
describe('ProvisioningService – binding lifecycle', () => {
  it('transitions to degraded after 3 consecutive health probe failures', async () => {
    const binding = await createBinding({ capabilityKey: 'storage', providerKey: 'aws-s3' });
    mockAdapter.healthCheck.mockResolvedValue(err(new HealthCheckError('timeout')));

    for (let i = 0; i < 3; i++) {
      await healthCheckJob.runForBinding(binding.id);
    }

    const updated = await bindingRepository.findById(binding.id);
    expect(updated.state).toBe('degraded');
  });
});
```

### Chaos Tests: Credential Expiry Simulation

```yaml
# Litmus chaos experiment: provider credential expiry simulation
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: binding-credential-expiry-chaos
spec:
  experiments:
    - name: rotate-secret-mid-operation
      spec:
        components:
          env:
            - name: TARGET_SECRET
              value: "baas/storage/aws-s3-credentials"
            - name: CHAOS_DURATION
              value: "300"
  # Expected: binding moves to credential-expired; circuit breaker opens;
  # requests return BINDING_CREDENTIAL_EXPIRED; auto-recovery after re-validation.
```
