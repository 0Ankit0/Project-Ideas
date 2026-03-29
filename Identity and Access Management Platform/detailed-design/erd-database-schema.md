# ERD Database Schema

```mermaid
erDiagram
    IDENTITIES ||--o{ SESSIONS : has
    SESSIONS ||--|| TOKEN_FAMILIES : owns
    IDENTITIES ||--o{ ENTITLEMENTS : granted
    POLICY_BUNDLES ||--o{ POLICY_RULES : contains
    FED_CONNECTIONS ||--o{ CLAIM_MAPPINGS : defines
    SCIM_JOBS ||--o{ SCIM_JOB_EVENTS : emits

    IDENTITIES {
      uuid identity_id PK
      uuid tenant_id
      string status
      timestamptz updated_at
    }
    SESSIONS {
      uuid session_id PK
      uuid identity_id FK
      string status
      timestamptz auth_time
    }
```

## Schema Constraints
- Unique `(tenant_id, subject_ref)` for identity linking.
- Indexes on `sessions(status, updated_at)` and `token_families(revoked_at)`.
- Soft-delete markers only where compliance policy allows.
## Cross-Cutting Implementation Baselines

### Token and Session Standards
- Access tokens: JWT signed with asymmetric keys (kid rotation every 30 days), TTL 10 minutes default, audience-restricted.
- Refresh tokens: opaque, one-time use with rotation; reuse detection revokes the token family and active device session.
- Session store: strongly consistent source of truth for session status (`active`, `step_up_required`, `revoked`, `expired`, `terminated`).
- Revocation SLA: propagation to introspection/cache layers within 5 seconds P95.

### Policy Evaluation Standards
- Decision result set: `permit`, `deny`, `not_applicable`, `indeterminate`.
- Precedence: explicit deny > permit > not-applicable; indeterminate fails closed for write/privileged operations.
- Policy model: hybrid RBAC + ABAC (+ relationship/group expansion where required).
- Explainability: every decision returns policy IDs, matched rules, and obligation set for audit.

### Identity Lifecycle Standards
- Human: `invited -> active -> suspended/locked -> deprovisioned -> archived`.
- Workload: `registered -> attested -> active -> compromised/quarantined -> retired`.
- Mandatory transition fields: actor, reason code, source system, request ID, timestamp.
- Offboarding control: immediate session kill + async entitlement revocation with reconciliation proof.

### Federation and SCIM Assumptions
- Federation protocols: OIDC/SAML inbound; OIDC/OAuth outbound for relying parties.
- Trust controls: metadata signature validation, cert rollover overlap, issuer/audience pinning, nonce/state replay defense.
- SCIM ownership: source-of-truth matrix by attribute domain; drift jobs run every 15 minutes.
- JIT provisioning: allowed only for approved IdP/tenant mappings and minimal role bootstrap.

### Threat Model and Auditability
- High-priority threats: token replay, assertion forgery, privilege escalation, stale entitlement abuse, break-glass misuse.
- Required controls: rate limits, adaptive MFA, device/risk signals, signed admin actions, immutable audit log.
- Audit minimum fields: tenant, actor, target, action, decision, policy hash, client app, IP/device posture, correlation ID.
- Retention: 13 months hot search + 7 years archive (compliance profile dependent).

## Implementation Deep-Dive Addendum

### Migration and Operations
- Use expand/contract migrations with forward and rollback scripts.
- Large-table index builds are online and gated by performance checks.
- Data retention jobs are partition-aware and produce compliance evidence snapshots.
