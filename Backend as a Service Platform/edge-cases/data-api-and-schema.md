# Edge Cases – Data API and Schema

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Developer applies breaking schema migration directly in production | Critical | App outage or data loss | Require dry-run + approval gate; `prod` environment migrations require owner confirmation |
| 2 | RLS policy misconfiguration allows cross-tenant row reads | Critical | Cross-tenant data leak | Automated RLS coverage tests run on every schema change; CI gate blocks deployment if test fails |
| 3 | Two concurrent schema migrations applied to the same namespace | High | Conflicting DDL, indeterminate schema state | Distributed lock per namespace (PostgreSQL advisory lock) before any DDL execution |
| 4 | Query facade generates SQL that bypasses RLS (e.g. via function calls) | Critical | Data leak | Whitelist query AST patterns; disallow `SECURITY DEFINER` functions in tenant namespaces |
| 5 | Schema migration partially applies due to mid-transaction failure | High | Inconsistent schema state | All DDL wrapped in explicit transactions; rollback on any error; record checksum before and after |
| 6 | Developer drops a column used by existing application code | High | Runtime application errors | Column drop requires a 2-step deprecation: mark as `deprecated`, drain references, then drop |
| 7 | Large table migration causes PostgreSQL lock contention | High | Production query timeouts | Use `ALTER TABLE … CONCURRENTLY` patterns; schedule heavy migrations in maintenance windows |
| 8 | Tenant exceeds row/storage quota mid-query | Medium | Partial write committed, quota exceeded after | Quota check before write; soft quota warning at 80%; hard stop at 100% with `QUOTA_EXCEEDED` error |

## Deep Edge Cases

### Concurrent Migration Lock
```sql
-- Acquired before every migration execution
SELECT pg_advisory_xact_lock(hashtext('migration:' || namespace_id));
-- Released automatically at transaction end
```
If the lock cannot be acquired within 10 seconds, the migration job returns `MIGRATION_LOCKED` and the caller retries after a backoff.

### RLS Audit Test Pattern
Every table with multi-tenant data has an automated test:
```typescript
// Attempt to read tenant B's rows with tenant A's session
const result = await dataApiService.executeQuery({
  tenantId: TENANT_A,
  envId: ENV_A,
  sql: `SELECT * FROM ${TENANT_B_TABLE}`,
});
expect(result.rows).toHaveLength(0); // RLS must return empty, not error
```

### Query Facade Allowed Operations
| Operation | Allowed | Notes |
|-----------|---------|-------|
| SELECT with WHERE | ✅ | RLS enforced |
| INSERT / UPDATE / DELETE | ✅ | Audit logged |
| CREATE TABLE / ALTER TABLE | ❌ | Only via migration API |
| DROP TABLE | ❌ | Only via migration API with approval |
| Raw function calls | ❌ | Blocked by query AST validator |
| COPY FROM/TO | ❌ | Use storage API for bulk operations |

## State Impact Summary

| Scenario | Migration / Namespace State |
|----------|---------------------------|
| Breaking migration blocked | `planned` → `rejected` |
| Concurrent migration conflict | Second migration waits for lock |
| Partial failure | `applying` → `failed` → auto-rollback |
| RLS test failure | CI gate blocks deployment |
