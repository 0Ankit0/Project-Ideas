# System Context Diagram

```mermaid
flowchart LR
    User[End User] -->|OIDC/OAuth| Channel[Web/Mobile/App]
    Admin[Identity Admin] --> Console[Admin Console]
    SecOps[Security Engineer] --> Console

    Channel --> APIGW[API Gateway/PEP]
    Console --> APIGW

    APIGW --> IAM[IAM Control Plane]
    IAM --> IdP[External IdP]
    IAM --> SCIM[SCIM Providers]
    IAM --> Notify[Notification Service]
    IAM --> SIEM[SIEM/SOAR]

    IAM --> RP[Relying Party APIs]
```

## Trust Boundaries
- Boundary A: internet client to gateway (DDoS/WAF/rate controls).
- Boundary B: control plane to external federation systems (signed assertions, pinned metadata).
- Boundary C: control plane to telemetry/compliance systems (tamper-evident audit export).

## Context Assumptions
- IAM is authentication broker and local authorization authority.
- External IdP is trusted for credential verification but not for local risk overrides.
- All external dependencies are considered partially trusted and monitored.

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

### Boundary-Specific Threat Notes
- Internet ingress boundary: DDoS, credential stuffing, CSRF and replay concerns.
- Federation boundary: signature bypass, metadata poisoning, clock-skew abuse.
- Telemetry boundary: evidence tampering, dropped alerts, delayed incident visibility.
