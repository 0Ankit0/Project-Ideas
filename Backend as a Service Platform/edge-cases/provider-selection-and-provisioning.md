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
