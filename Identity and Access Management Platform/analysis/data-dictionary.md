# Data Dictionary

| Entity | Key Fields | Notes |
|---|---|---|
| Identity | `identity_id`, `tenant_id`, `status`, `subject_ref` | Human/workload principal record |
| Session | `session_id`, `identity_id`, `status`, `auth_time`, `device_id` | Session source of truth |
| TokenFamily | `family_id`, `session_id`, `latest_refresh_hash`, `revoked_at` | Rotation and reuse detection |
| PolicyBundle | `policy_version`, `bundle_hash`, `activated_at`, `activated_by` | Immutable policy artifact metadata |
| DecisionLog | `decision_id`, `policy_version`, `result`, `obligations` | Explainability and forensic evidence |
| FederationConnection | `connection_id`, `protocol`, `issuer`, `jwks_uri`, `status` | Trust config |
| ScimJob | `job_id`, `external_system`, `object_ref`, `attempt`, `result` | Provisioning pipeline telemetry |

## Field Constraints
- `tenant_id` is mandatory on all entities.
- PII-bearing fields must be encrypted-at-rest and access-controlled.
- Immutable fields are append-only through event sourcing patterns.
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

### Data Stewardship
- Ownership is defined per entity for schema changes and data quality alarms.
- PII classification tier is stored for each field with masking/redaction policy.
- Lineage tags link user-facing decisions back to source entities and policy versions.
