# Edge Cases – Auth and Tenancy

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Auth provider supports different identity semantics than facade contract | High | Inconsistent signup or session behavior | Define required auth contract and capability flags; adapters declare which optional features are supported |
| 2 | Cross-tenant token accepted by wrong project | Critical | Severe data leak | Scope every token/session to `tenantId` + `projectId` + `envId`; validate all three claims on every request |
| 3 | Password reset or verification flow differs by provider | Medium | Broken user experience | Normalize user-facing outcomes at facade layer; provider-specific internals are hidden |
| 4 | Auth provider outage during login storm | High | Availability risk | Cache project-level auth config in Redis; rate-limit requests during degraded state; surface `AUTH_PROVIDER_UNAVAILABLE` |
| 5 | Session invalidation after provider migration | High | Users retain stale access post-switchover | Force coordinated session revocation or session rebinding per switchover policy |
| 6 | Token with stale environment claim after environment deletion | Critical | Cross-env access with deleted scope | Validate environment existence on every request; deleted environments invalidate all tokens immediately |
| 7 | Tenant admin role drift via concurrent role assignment | High | Privilege escalation | Role assignment uses optimistic lock; concurrent assignments serialized via PostgreSQL advisory lock |
| 8 | Shared device with cached session reused by different user | High | Cross-user session leakage | Tenant-bound refresh token + re-auth challenge after idle timeout |
| 9 | MFA bypass during provider switchover window | Critical | Authentication security gap | MFA state is owned by the platform, not the provider; switchover does not reset MFA enrollment |

## Deep Edge Cases

### Cross-Tenant Token Validation
Every JWT is validated with a 3-clause check:
```
ASSERT token.claims.tenantId == request.tenantId
ASSERT token.claims.projectId == request.projectId
ASSERT token.claims.envId    == request.envId
```
Any mismatch returns `AUTHZ_SCOPE_MISMATCH` (HTTP 403) and emits a `UnauthorizedAccess` security event.

### Session Revocation After Provider Migration
1. Switchover plan includes a `sessionRevocationPolicy` field (choices: `immediate`, `graceful-30m`, `graceful-24h`).
2. At cutover completion, the migration orchestrator publishes `SwitchoverSessionRevocationRequested`.
3. Session manager worker processes revocation in batches, invalidating Redis session keys.
4. Affected users receive a re-authentication prompt on next request.

### Auth Storm Handling
- Rate limit: 10 login attempts per user per minute, 1,000 per project per minute.
- Soft lockout after 5 failed attempts: exponential backoff starting at 1 second.
- Hard lockout after 20 consecutive failures: account suspended, owner notified.
- Circuit breaker on IAuthAdapter: opens after 10 consecutive errors in 60 seconds.

## State Impact Summary

| Scenario | Auth/Session State Transition |
|----------|------------------------------|
| Cross-tenant token | Request rejected, security event emitted |
| Provider outage | Auth subsystem → `degraded` |
| Session post-switchover | `active` → `revoked` (per policy) |
| Stale env claim | Token rejected, env validated on every call |
| MFA bypass attempt | Request rejected, `MFABypassAttempted` event emitted |
