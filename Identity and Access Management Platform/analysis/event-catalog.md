# Event Catalog

| Event | Producer | Consumers | Delivery | Idempotency Key |
|---|---|---|---|---|
| `auth.session.started` | Auth Service | Audit, Risk, Analytics | at-least-once | session_id |
| `auth.step_up.required` | Risk Engine | Auth UI, Alerting | at-least-once | challenge_id |
| `token.revoked` | Token Service | Gateway cache, RP webhooks | at-least-once | token_family_id |
| `identity.deprovision.requested` | Lifecycle Service | Provisioning workers | at-least-once | identity_id + version |
| `policy.bundle.activated` | Policy Admin | PDP cache, Audit | exactly-once logical | policy_version |
| `scim.drift.detected` | Reconciler | Admin Console, Ticketing | at-least-once | external_id + drift_hash |

## Event Handling Requirements
- Every consumer is retry-safe and records dedupe token.
- Dead-letter queues include replay tooling and reason classification.
- Event schema versioning is backward compatible for 2 minor versions.
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

### Event Governance
- Every event schema has an owner, version policy, and deprecation timeline.
- Breaking changes require dual-publish migration window and compatibility report.
- Consumer lag SLOs are monitored per event family with replay readiness indicators.
