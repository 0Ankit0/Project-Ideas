# Business Rules

## Authorization Rules
- BR-01: Default deny when no policy matches.
- BR-02: Deny overrides permit for the same action/resource tuple.
- BR-03: Privileged actions require recent MFA (`auth_time <= 15m`).
- BR-04: Break-glass grants require dual approval and auto-expire within configured TTL.

## Identity and Lifecycle Rules
- BR-05: A suspended or locked identity cannot receive new tokens.
- BR-06: Deprovisioned identities must have zero active sessions.
- BR-07: Workload identity secrets/certs must rotate before `rotation_due`.

## Federation and Provisioning Rules
- BR-08: Federated login denied if issuer or audience mismatch.
- BR-09: Missing required mapping claims blocks JIT provisioning.
- BR-10: SCIM source priority matrix decides attribute conflict winners.

## Audit and Compliance Rules
- BR-11: Critical admin changes require ticket reference and immutable event.
- BR-12: Any policy publication must include approval metadata and diff checksum.
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

### Rule Conflict Test Matrix
- Deny-overrides with mixed policy sets.
- Time-windowed policies across DST/timezone boundaries.
- Group hierarchy cycles and maximum expansion depth protection.
