# Edge Cases – Security and Compliance

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Provider credential leaked in logs or traces | Critical | Account compromise and unauthorized data access | Redact all fields named `password`, `token`, `secret`, `apiKey` at logger middleware level; enforce via ESLint rule |
| 2 | Audit log tampered to cover unauthorized access | Critical | Compliance failure; missed incident detection | Audit log is append-only in PostgreSQL; no UPDATE/DELETE permitted on `audit_logs` table; periodic checksum validation |
| 3 | Privilege escalation via role drift during concurrent role assignment | High | User gains unintended admin access | Role assignments use optimistic concurrency (`version` field); PostgreSQL advisory lock per-project |
| 4 | SSRF via user-controlled webhook URL | High | Internal network scanning or credential theft | Validate webhook URLs against allowlist; block RFC-1918 and loopback addresses; use egress proxy for webhook delivery |
| 5 | JWT secret key rotation causes mass session invalidation | High | All active users logged out simultaneously | Rotate keys gradually with overlap window (old key valid 1 hour after rotation); issue new tokens transparently on next request |
| 6 | SQL injection via query facade payload | Critical | Full database compromise | Query facade uses parameterized queries only; query AST validation whitelist; ESLint `no-sql-injection` rule |
| 7 | CORS misconfiguration allows unauthorized cross-origin reads | High | Credential theft via browser-based attack | CORS origin allowlist configurable per project; wildcard (`*`) only permitted for public read-only endpoints |
| 8 | Tenant discovers another tenant's project ID via enumeration | Medium | Information disclosure | All resource IDs are UUIDs v7; no sequential integers; 403 returned for any cross-tenant resource access (not 404) |

## Deep Edge Cases

### Audit Log Integrity
```sql
-- Append-only enforced by PostgreSQL row-level trigger:
CREATE RULE no_update_audit AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE no_delete_audit AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
-- Periodic checksum job:
-- SHA-256 hash of every 1,000-row batch stored in audit_log_checksums table
-- Nightly job re-computes and compares; alerts on mismatch
```

### Webhook SSRF Prevention
```typescript
function isAllowedWebhookUrl(url: string): boolean {
  const parsed = new URL(url);
  if (!['https:'].includes(parsed.protocol)) return false;
  const ip = dns.lookup(parsed.hostname); // resolve and check
  if (isPrivateIP(ip)) return false; // blocks 10.x, 172.16.x, 192.168.x, 127.x
  if (parsed.hostname === 'localhost') return false;
  return true;
}
```

### JWT Key Rotation Without Mass Logout
1. New key pair generated; stored in Secrets Manager as `jwt-key-v2`.
2. Token issuer begins signing new tokens with `v2`.
3. Token validator accepts both `v1` and `v2` during overlap window (1 hour).
4. After 1 hour, `v1` key removed; only `v2` accepted.
5. Users whose tokens were signed with `v1` are transparently refreshed on next API call if refresh token is still valid.

### Response Code Security Policy
| Situation | Response Code | Reason |
|-----------|-------------|--------|
| Cross-tenant resource access | 403 | Not 404; prevents confirming resource existence |
| Invalid token | 401 | Not 403; client must re-authenticate |
| Existing user registration | 409 | Not 200; prevents silent account takeover |
| Rate limit | 429 | With `Retry-After`; no business data in body |

## State Impact Summary

| Scenario | Security Event Emitted |
|----------|----------------------|
| Credential in log | `CredentialExposureDetected` (SAST/runtime alert) |
| Audit tamper attempt | `AuditIntegrityViolation` (critical alert) |
| Role escalation attempt | `UnauthorizedRoleChange` |
| SSRF webhook blocked | `SSRFAttemptBlocked` |
| Cross-tenant access | `UnauthorizedCrossTenantAccess` |
| SQL injection blocked | `InjectionAttemptBlocked` |
