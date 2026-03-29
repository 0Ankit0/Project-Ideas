# Use Case Descriptions

## UC-01 Authenticate and Establish Session
- **Primary flow:** user initiates login -> IdP auth -> IAM callback validation -> risk checks -> session creation -> token issuance.
- **Alternate flow:** MFA required due to risk score or policy obligation.
- **Failure handling:** invalid nonce/state, stale code replay, lockout threshold exceeded.

## UC-02 Evaluate Authorization Policy
- **Input context:** subject claims, groups, device posture, resource tags, action verb, tenant policy version.
- **Output:** decision, obligations, decision trace hash.
- **Error semantics:** indeterminate if dependency unavailable; enforcement is fail-closed for write/admin actions.

## UC-03 Identity Deprovisioning
- **Primary flow:** HR termination event -> immediate disable -> revoke sessions/tokens -> entitlement removal jobs -> reconciliation report.
- **Edge cases:** downstream API outage, stale SCIM etag conflict, orphaned group grants.

## UC-04 Federated JIT Provisioning
- **Primary flow:** first SSO -> issuer trust validation -> claim mapping -> account link or create -> baseline role grant.
- **Constraints:** deny if required claims missing or source domain mismatch.
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

### UC Traceability Hooks
- Each use case maps to API contract IDs, event IDs, and dashboard IDs.
- Exception paths define operator action, automated compensation, and escalation target.
- For every irreversible action, a rollback or remediation path is explicitly defined.
