# Policy Engine and Federation

## Policy Engine Internals
- Context normalization stage merges subject claims, group graph expansion, resource metadata, and environment signals.
- Rule compiler transforms author-authored DSL to deterministic evaluation graph with partial-eval caching.
- Decision engine emits explain trace with rule hit list, condition values, and obligation directives.

## Federation Processing
- OIDC adapter validates issuer, audience, signature, nonce, and auth_time.
- SAML adapter validates assertion signature, audience restrictions, `NotOnOrAfter`, and replay cache.
- Mapping engine applies transformation rules and collision handling against local identity linking keys.

## Failure and Recovery
- On federation metadata failure, connection enters degraded mode; login denied and admin alerted.
- On mapping failures, flow returns actionable errors without partial account creation.
- Drift reconciliation compares authoritative attributes and emits correction plans.

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

### Policy Compiler and Runtime
- Compilation emits normalized AST and precomputed selector indexes.
- Runtime supports shadow-evaluation mode for safe policy rollout analysis.
- Explain traces include sanitized context snapshots for forensic debugging.

### Federation Trust Operations
- Metadata refresh job validates cert chain and expiry thresholds.
- Emergency trust disable path exists per federation connection.
