# Edge Cases – Storage and File Providers

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Provider exposes eventual consistency for object listing | High | Missing files in immediate read-after-write | Use metadata-backed listing from PostgreSQL; document consistency semantics per adapter |
| 2 | Upload interrupted mid-stream | Medium | Orphaned partial objects in provider storage | Track upload intent in PostgreSQL; background job aborts stale multipart uploads older than 24 hours |
| 3 | Signed URL accessed after expiry | Low | 403 from provider; confusing error to client | Surface `STORAGE_URL_EXPIRED` with expiry timestamp; suggest re-generation |
| 4 | File object metadata in PostgreSQL out of sync with provider after crash | High | Ghost records or missing files | Reconciliation job runs hourly: compares PostgreSQL metadata against provider object list and flags discrepancies |
| 5 | Provider switchover copy fails mid-transfer for large files | Critical | Files not accessible in new provider | Checkpoint per-file copy status; resume from last successful checkpoint; do not activate new binding until parity score ≥ 99.99% |
| 6 | Tenant exceeds storage quota during upload | Medium | Partial upload committed | Quota check against current `usage_meters` before accepting upload; reject with `STORAGE_QUOTA_EXCEEDED` |
| 7 | Two concurrent uploads to the same object key | Medium | Last write wins; first upload silently overwritten | Require explicit `overwrite: true` flag; default rejects duplicate keys with `STORAGE_KEY_EXISTS` |

## Deep Edge Cases

### Stale Multipart Upload Cleanup
```
Every hour, background job queries:
  SELECT * FROM file_objects
  WHERE state = 'upload-in-progress'
    AND created_at < NOW() - INTERVAL '24 hours';
For each: call IStorageAdapter.abortMultipartUpload(providerUploadId)
          UPDATE file_objects SET state = 'abandoned'
```

### Provider Switchover Parity Check
After copy phase completes:
1. List all `file_objects` in PostgreSQL for the environment.
2. Verify each exists in new provider (check object key + size + checksum).
3. Compute `parity_score = verified_count / total_count * 100`.
4. Gate: switchover proceeds only if `parity_score >= 99.99`.
5. If gate fails: surface `SWITCHOVER_PARITY_CHECK_FAILED` with object-level diff report.

### Signed URL Security
- Signed URLs carry HMAC signature bound to `fileId`, `bucketId`, `tenantId`, `expiresAt`.
- URL parameters are validated by the platform before redirecting to the provider-level presigned URL.
- Provider presigned URL has the same or shorter TTL than the platform-level URL.
- Revoked file objects immediately invalidate all outstanding signed URLs (signed_access_grants table `revoked_at` field).

## State Impact Summary

| Scenario | File Object State |
|----------|-----------------|
| Interrupted upload | `upload-in-progress` → `abandoned` (after 24h) |
| Successful upload | `upload-in-progress` → `active` |
| Switchover copy | `active` in old → `active` in new (after parity check) |
| Quota exceeded | Upload rejected; no state change |
| File deleted | `active` → `deleted` (soft delete; purged after retention period) |
