# User Stories

## Administrator Stories
1. As an IAM admin, I can define policy bundles with dry-run simulation before activation.
   - **Acceptance:** simulation exposes impacted principals/resources and expected permit/deny deltas.
2. As an IAM admin, I can force logout specific users/devices.
   - **Acceptance:** active sessions terminate and refresh reuse is blocked within 5 seconds P95.

## Security Engineer Stories
1. As a security engineer, I can inspect complete auth chain for an incident.
   - **Acceptance:** trace includes login factor results, risk score, policy version, and final decision.
2. As a security engineer, I can configure anomaly-driven controls.
   - **Acceptance:** thresholds trigger alert + optional auto step-up/suspension action.

## Application Owner Stories
1. As an app owner, I can request scoped machine credentials for backend services.
   - **Acceptance:** credentials are rotated, least-privilege scoped, and auditable.
2. As an app owner, I can use standardized decision APIs and receive obligation hints.
   - **Acceptance:** deny responses include actionable remediation code.

## Auditor Stories
1. As an auditor, I can retrieve immutable evidence for identity and entitlement changes.
   - **Acceptance:** export contains actor, approver, reason, timestamp, and ticket correlation.

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

### Story Slicing for Build Planning
- **Slice 1:** login + session APIs + audit event emission.
- **Slice 2:** step-up MFA + risk-adaptive policy obligations.
- **Slice 3:** token rotation/reuse detection + forced logout UI.
- **Slice 4:** policy simulation endpoint + rollout approvals.
- **Slice 5:** SCIM drift reconciliation + escalation workflow.

### Negative Acceptance Cases
- Expired assertion replay must be denied and audited.
- Deprovisioned users must fail both refresh and introspection flows.
- Policy publish without approval metadata must be rejected.
