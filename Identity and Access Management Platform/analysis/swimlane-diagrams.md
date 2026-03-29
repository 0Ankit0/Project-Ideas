# Swimlane Diagrams

```mermaid
flowchart LR
    subgraph User
      U1[Submit login]
      U2[Complete MFA]
    end

    subgraph IAM_Channel[App Channel]
      C1[Redirect to IdP]
      C2[Send callback to IAM]
    end

    subgraph IAM_Core[IAM Core]
      I1[Validate assertion]
      I2[Evaluate policy/risk]
      I3[Create session + issue token]
      I4[Emit audit events]
    end

    subgraph External[IdP + Risk + SIEM]
      E1[Authenticate user]
      E2[Return claims]
      E3[Ingest audit/alerts]
    end

    U1 --> C1 --> E1 --> E2 --> C2 --> I1 --> I2 --> U2 --> I3 --> I4 --> E3
```

## RACI Highlights
- User controls credential and MFA action.
- IAM Core owns trust validation, policy decisions, token/session lifecycle.
- External systems provide assertions/signals but do not bypass IAM policy enforcement.
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

### Ownership and Handoffs
- Lane transitions must include contract objects (payload schema + correlation ID).
- Human-in-the-loop lane transitions must specify SLA and escalation timing.
- Security-sensitive handoffs (admin actions) require dual-audit stamps.
