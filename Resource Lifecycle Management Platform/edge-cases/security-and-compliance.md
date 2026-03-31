# Security and Compliance Edge Cases

Security threats, policy bypass attempts, audit integrity failures, and compliance violations in the **Resource Lifecycle Management Platform**.

---

## EC-SEC-01: Unauthorized Allocation Access (IDOR)

**Description**: A requestor attempts to access or modify another tenant's allocation by guessing or enumerating `allocation_id` values.

| Aspect | Detail |
|---|---|
| **Trigger** | `GET /allocations/{id}` or `POST /allocations/{id}/checkin` where `allocation.tenant_id ≠ jwt.tenant_id` |
| **Detection** | Authorization Middleware checks `tenant_id` match on every entity access; returns `403 Forbidden` if mismatch |
| **Containment** | Request rejected; no data disclosed; `SEC_AUTH_VIOLATION` event logged to SIEM |
| **Recovery** | No recovery needed; expected security enforcement |
| **Evidence** | SIEM alert: repeated 403s from same `user_id` across different tenant entity IDs; potential IDOR scanning pattern |
| **Owner** | Security Team |
| **SLA** | Instant rejection; SIEM alert reviewed within 1 h for repeated patterns |
| **Prevention** | UUID v4 IDs (not sequential); tenant_id check on every entity operation in middleware |

---

## EC-SEC-02: Business Rule Override Abuse

**Description**: An actor with `operations` role grants override after override for the same rule ID without legitimate justification.

| Aspect | Detail |
|---|---|
| **Trigger** | Same `rule_id` overridden more than 3 times in 30 days by the same `actor_id` |
| **Detection** | Compliance report (override review, 90-day window) surfaces the pattern; SIEM correlation rule fires |
| **Containment** | No automatic containment on individual overrides (each is valid at the time); pattern triggers a policy-review workflow |
| **Recovery** | Compliance Officer reviews the override history; if pattern is legitimate (e.g., rule is too strict), the rule is updated; if abuse suspected, actor's override privilege is revoked pending investigation |
| **Evidence** | Override audit records with `rule_id`, `actor_id`, `reason_code`, `expiry`, `approved_at`; SIEM correlation event |
| **Owner** | Compliance Officer |
| **SLA** | Pattern detected within 24 h; review within 5 business days |

---

## EC-SEC-03: Audit Log Gap or Hash Chain Break

**Description**: A direct database mutation (outside the application) or a bug causes an audit event to be missing or the SHA-256 hash chain to break.

| Aspect | Detail |
|---|---|
| **Trigger** | Reconciliation job or compliance query detects: `audit_event.hash ≠ SHA-256(prev_hash + payload)` for a record |
| **Detection** | Audit integrity check job (runs daily) computes expected hash for each record and compares; reports `audit_events_hash_mismatch` metric |
| **Containment** | Affected audit partition is flagged as `INTEGRITY_SUSPECT`; Compliance Officer and SRE are alerted |
| **Recovery** | SRE investigates: (a) check if hash computation bug introduced in a deploy → fix and recompute; (b) check for direct DB mutations (CloudTrail, DB activity monitoring) → forensic investigation; SIEM events for the affected time window are used to reconstruct the timeline |
| **Evidence** | CloudTrail (or RDS activity log) showing any direct DB access; git history for hash computation code changes |
| **Owner** | SRE + Compliance |
| **SLA** | Alert within 1 h of daily job; investigation within 4 h |
| **Prevention** | IAM policy denies direct DB write access except via Vault-issued dynamic credentials with minimal lifetime; DB activity monitoring enabled |

---

## EC-SEC-04: Token Replay Attack

**Description**: An attacker captures a valid JWT and replays it after the user has logged out or the token should be considered invalid.

| Aspect | Detail |
|---|---|
| **Trigger** | Stolen/replayed JWT used for allocation or checkout commands |
| **Detection** | Identity Provider token revocation list check; short JWT TTL (15 min); session revocation on logout stored in Redis blacklist |
| **Containment** | Auth Middleware checks revocation list (Redis) on every request; revoked tokens return `401 TOKEN_REVOKED` |
| **Recovery** | Affected user forced to re-authenticate; any allocations initiated with the stolen token are flagged for review |
| **Evidence** | SIEM alert: same `jti` (JWT ID) used from two different IP addresses within short window; revocation audit entry |
| **Owner** | Security Team |
| **SLA** | Token blacklist check is real-time; SIEM alert reviewed within 30 min |
| **Prevention** | Short JWT TTL (15 min access token, 8 h refresh); logout endpoint invalidates refresh token; suspicious concurrent session alert |

---

## EC-SEC-05: Compliance Retention Lock Bypass Attempt

**Description**: A Resource Manager attempts to decommission a resource that has an active compliance retention lock, either by exploiting an API bug or by directly modifying the DB.

| Aspect | Detail |
|---|---|
| **Trigger** | Decommission command submitted while `retention_lock.expires_at > NOW()` |
| **Detection** | Decommission Orchestrator checks retention lock before any state transition; returns `409 RETENTION_LOCK_ACTIVE`; Direct DB attempts: captured by DB activity monitoring |
| **Containment** | Decommission command rejected with lock expiry date; resource state unchanged |
| **Recovery** | No recovery needed (expected enforcement); if direct DB attempt detected, security incident raised |
| **Evidence** | `DECOMMISSION_BLOCKED` audit entry with `lock_expires_at`; DB activity monitoring log for direct access |
| **Owner** | Compliance Officer + Security Team (if direct DB access) |
| **SLA** | Instant API rejection; DB access alert within 5 min |

---

## EC-SEC-06: Data Exposure via Search (Cross-Tenant)

**Description**: A search query unintentionally returns resources from another tenant because the Elasticsearch query is missing the `tenant_id` filter.

| Aspect | Detail |
|---|---|
| **Trigger** | Bug in Search Service omits `tenant_id` filter in Elasticsearch query; returns cross-tenant results |
| **Detection** | Elasticsearch query audit shows documents from `tenant_id ≠ jwt.tenant_id` in response; SIEM data access alert |
| **Containment** | Immediately deploy hotfix that adds `tenant_id` filter; disable search endpoint if hotfix cannot be deployed within 30 min |
| **Recovery** | Audit which tenants' data was exposed and to whom; notify affected tenants per data breach notification policy |
| **Evidence** | Elasticsearch query log; SIEM data access events |
| **Owner** | Security Team + Platform Engineering |
| **SLA** | Containment within 30 min; notification within 72 h (per GDPR/data protection obligations) |
| **Prevention** | Integration tests assert that search results never contain documents from any tenant other than the authenticated one; unit tests for all Search queries include `tenant_id` filter assertion |

---

## Security Incident Response Flow

```mermaid
flowchart TD
  Detect[Security Signal Detected\n(SIEM alert / compliance report)] --> Classify{Classify Severity}
  Classify -->|"Critical (data exposure, active attack)"| ImmediateContain[Immediate Containment\n• Revoke affected tokens\n• Disable compromised endpoint\n• Block attacker IP in WAF]
  Classify -->|"High (policy bypass, audit gap)"| HighContain[High Severity Response\n• Alert Security + Compliance\n• Freeze affected operations\n• Forensic log pull]
  Classify -->|"Medium (suspicious pattern)"| MediumContain[Medium Response\n• SRE + Compliance review\n• No immediate service impact]
  ImmediateContain --> Investigate[Forensic Investigation\nCloudTrail + SIEM + DB logs]
  HighContain --> Investigate
  MediumContain --> Investigate
  Investigate --> RootCause[Determine Root Cause]
  RootCause --> Remediate[Remediate\n(code fix / policy update / access revoke)]
  Remediate --> Postmortem[Postmortem\n(timeline, impact, lessons, actions)]
  Postmortem --> Notify{Regulatory Notification Required?}
  Notify -->|Yes| DataBreachNotification[Notify affected users\nwithin 72 h per GDPR]
  Notify -->|No| End([Close Incident])
  DataBreachNotification --> End
```
