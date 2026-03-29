# Requirements

## Functional Requirements (Normative)
### Authentication and Session
- Support OIDC Authorization Code + PKCE, Device Code, and service-account client-credentials.
- Enforce step-up MFA for privileged scopes and elevated risk scores.
- Provide global session view and admin session termination APIs.

### Authorization and Policy
- PDP must evaluate request context in <30ms P95 for cache-hit and <120ms P95 for cache-miss.
- Policies support role grants, attribute predicates, resource tags, temporal constraints, and obligations.
- All mutating operations require authorization with explicit policy evaluation trace.

### Identity Lifecycle and Provisioning
- Support invite, JIT provision, suspend, lock, restore, and deprovision flows.
- Deprovisioning must revoke sessions/tokens immediately and clean entitlements asynchronously with reconciliation proof.
- SCIM updates must be idempotent and version-aware.

### Federation
- Support OIDC and SAML federation with configurable claim/attribute mapping.
- Require issuer, audience, signing cert, and ACS/redirect URI validation.
- Capture federation health signals (clock skew errors, signature failures, mapping failures).

## Non-Functional Requirements
- Availability: 99.95% monthly for auth/policy APIs.
- Durability: no silent loss of lifecycle or audit events.
- Security: encryption in transit and at rest, least privilege identities, hardened key management.
- Compliance: tamper-evident audit records, retention and legal hold support.

## Acceptance Criteria Matrix
| Capability | Acceptance Criteria |
|---|---|
| Token issuance | Includes policy hash, tenant, subject, expiry, and key version |
| Policy decision | Explain payload includes matched rules and obligations |
| SCIM sync | Retries deterministic; duplicate patch does not create duplicate grants |
| Revocation | Access denied within propagation SLA across API and UI channels |

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

### Regulatory/Control Mapping
| Requirement Area | Control Families | Evidence |
|---|---|---|
| Authentication & MFA | NIST IA / SOC2 CC6 | auth policy config snapshots + auth event logs |
| Authorization decisions | NIST AC / SOC2 CC6 | decision traces + policy approval history |
| Audit retention | SOC2 CC7 / ISO A.12 | retention policy + immutable storage configuration |
| Provisioning lifecycle | NIST AC-2 | joiner/mover/leaver reports + reconciliation results |

### Performance Budgets
- Login end-to-end (excluding IdP UI): **P95 < 800ms**.
- Decision API: **P95 < 30ms cache-hit**, **P95 < 120ms cache-miss**.
- Revocation propagation: **P95 < 5s**, **P99 < 15s**.
