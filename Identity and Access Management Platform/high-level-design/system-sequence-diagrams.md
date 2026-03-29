# System Sequence Diagrams

## Interactive Login Sequence
```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant I as IAM
    participant P as External IdP
    participant R as Risk Engine

    U->>C: Start login
    C->>I: Auth request (PKCE)
    I->>P: Redirect/auth challenge
    P-->>I: Auth code/assertion
    I->>R: Evaluate risk context
    alt high risk
      I-->>C: Require MFA step-up
      C->>I: MFA response
    end
    I-->>C: Session + tokens
```

## API Authorization Sequence
```mermaid
sequenceDiagram
    participant App
    participant PEP
    participant PDP
    participant PolicyStore

    App->>PEP: API call + token
    PEP->>PDP: Evaluate(subject, resource, action, env)
    PDP->>PolicyStore: Fetch policy version
    PolicyStore-->>PDP: Rules
    PDP-->>PEP: Decision + obligations
    PEP-->>App: Permit/Deny result
```

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

### Sequence Validation Rules
- Each sequence path has explicit idempotency and retry behavior.
- Negative paths include client-facing error contracts and operator telemetry emission.
- Cross-service latency budgets are annotated and monitored.
