# API and UI Edge Cases

Edge cases related to API inputs, client behavior, scanner interactions, and rate limiting in the **Resource Lifecycle Management Platform**.

---

## EC-API-01: Malformed or Oversized Payload

**Description**: Client submits a request with a payload that is syntactically invalid JSON, missing required fields, or exceeds the allowed body size.

| Aspect | Detail |
|---|---|
| **Trigger** | `Content-Type: application/json` but body is not valid JSON; or payload > 1 MB |
| **Detection** | API Gateway / HTTP Router rejects before reaching command handler |
| **Containment** | Returns `400 Bad Request` with `error_code: MALFORMED_PAYLOAD`; no processing |
| **Recovery** | Client fixes payload and retries |
| **Evidence** | API Gateway access log records rejected request; no audit entry (no processing) |
| **Owner** | N/A (expected system behavior) |
| **SLA** | Instant |

---

## EC-API-02: Expired or Invalid JWT

**Description**: Client sends a request with a JWT that has expired, been signed with the wrong key, or contains insufficient role claims.

| Aspect | Detail |
|---|---|
| **Trigger** | `Authorization: Bearer <expired_or_invalid_jwt>` |
| **Detection** | Auth Middleware: JWT signature validation fails or `exp` < `now()`; returns `401 Unauthorized` |
| **Containment** | Request rejected before reaching any business logic |
| **Recovery** | Client refreshes token from Identity Provider and retries |
| **Evidence** | Security audit log entry: `AUTH_FAILURE` with `user_agent`, `ip_address`, `correlation_id` |
| **Owner** | N/A |
| **Note** | Three consecutive 401s from the same IP within 1 min trigger a temporary rate-limit block and SIEM alert |

---

## EC-API-03: Idempotency Key Reuse Across Different Operations

**Description**: Client accidentally reuses the same `Idempotency-Key` for two different operations (e.g., checkout for resource A and checkout for resource B).

| Aspect | Detail |
|---|---|
| **Trigger** | Second `POST /allocations` with same `Idempotency-Key` but different `resource_id` |
| **Detection** | IdempotencyStore returns cached response for the first operation; system returns the first response without re-processing |
| **Containment** | No second allocation created; client receives 201 with the **first** allocation's data (incorrect from client's intent) |
| **Recovery** | Client must use a new unique `Idempotency-Key` for the second operation |
| **Evidence** | Cache hit logged; client receives unexpected `resource_id` in response (client-detectable) |
| **Owner** | N/A (client misuse) |
| **Prevention** | Documentation clearly states idempotency keys must be unique per operation; SDK generates keys automatically |

---

## EC-API-04: Rate Limit Breach

**Description**: A tenant or user sends commands at a rate exceeding the configured rate limit (100 write commands per minute per user).

| Aspect | Detail |
|---|---|
| **Trigger** | Request count > limit within sliding window |
| **Detection** | Rate Limit Middleware in API Gateway |
| **Containment** | `429 Too Many Requests` returned with `Retry-After` header |
| **Recovery** | Client implements exponential backoff using the `Retry-After` value |
| **Evidence** | API Gateway access log records rate-limited requests; metric spike visible in dashboard |
| **Owner** | N/A (expected system behavior) |
| **Alert** | If a single tenant exceeds 10× the rate limit consistently, alert ops for potential abuse or misconfigured integration |

---

## EC-API-05: Bulk Import CSV with Encoding Issues

**Description**: Resource Manager uploads a CSV for bulk provisioning with non-UTF-8 encoding or Windows line endings that cause the parser to fail on certain rows.

| Aspect | Detail |
|---|---|
| **Trigger** | CSV file uses Windows-1252 or ISO-8859-1 encoding; parser encounters unexpected byte sequence |
| **Detection** | CSV parser in Provisioning Service detects encoding error; marks affected rows as validation failures |
| **Containment** | Entire batch rolls back (atomic import); per-row error report returned identifying encoding issue rows |
| **Recovery** | Resource Manager re-saves CSV as UTF-8 and re-uploads with new `Idempotency-Key` |
| **Evidence** | Import error report with row numbers and encoding error description |
| **Owner** | N/A (client input issue) |
| **Prevention** | Documentation specifies UTF-8 with LF line endings; CSV template provided |

---

## EC-API-06: Scanner App Version Mismatch

**Description**: An older version of the mobile scanner app sends a checkout request using a deprecated field schema that the API no longer accepts.

| Aspect | Detail |
|---|---|
| **Trigger** | `POST /allocations` from old app version uses deprecated field `equipment_id` instead of `resource_id` |
| **Detection** | API schema validation rejects unknown/deprecated fields; returns `400 VALIDATION_FAILED` with guidance to update app |
| **Containment** | Request rejected; no allocation created |
| **Recovery** | Custodian updates app; or uses web portal for checkout |
| **Evidence** | API access log records request with `User-Agent` header containing old app version |
| **Owner** | Mobile App Team |
| **Prevention** | Deprecation warnings in `Deprecation` header at v1 endpoint 6 months before field removal; minimum app version check at startup |

---

## EC-API-07: Simultaneous Idempotent Requests (Race)

**Description**: Two pods simultaneously receive the same `Idempotency-Key` command and both check the cache at the same time — both cache-miss and both try to process.

| Aspect | Detail |
|---|---|
| **Trigger** | Two requests with same key arrive at different API pods within the same millisecond; both hit Redis cache-miss before either writes the result |
| **Detection** | Both proceed to command execution; DB unique constraint or optimistic lock prevents double-commit |
| **Containment** | One commits successfully; the other receives DB conflict and returns 200 with the first response (after reading from DB); Redis cache is updated by the winner |
| **Recovery** | Automatic; no manual intervention needed |
| **Evidence** | Audit log shows both attempts; one `COMMITTED`, one `CONFLICT_RESOLVED` |
| **Owner** | Platform Engineering |
| **Prevention** | Redis `SET NX` (set-if-not-exists) with a short TTL (1 s) as a pre-lock before processing; reduces window for races |

---

## Cross-References

- Business rules (authorization): [../analysis/business-rules.md](../analysis/business-rules.md)
- API design (error codes): [../detailed-design/api-design.md](../detailed-design/api-design.md)
- Security edge cases: [security-and-compliance.md](./security-and-compliance.md)
