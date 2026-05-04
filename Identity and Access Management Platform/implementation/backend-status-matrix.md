# Backend Status Matrix

This matrix is the implementation tracker for the backend workstreams needed to ship a
fully functional IAM platform. A row is not considered complete until design artifacts,
code, automated validation, and operational evidence all exist.

| Capability | Design | Build | Test | Ops readiness | Current implementation gap |
|---|---|---|---|---|---|
| Passwordless login and local credential fallback | ✅ | 🟡 | 🟡 | ⚪ | Recovery-code rotation and anti-enumeration scenarios still need automated tests |
| OIDC and SAML federation | ✅ | 🟡 | ⚪ | ⚪ | Metadata rollover, signed logout, and claim-mapping error paths remain incomplete |
| Adaptive MFA and device posture | ✅ | 🟡 | 🟡 | 🟡 | Device-attestation feeds wired for read path, but fallback and degradation logic needs chaos coverage |
| Session management and concurrent-session policies | ✅ | ✅ | 🟡 | 🟡 | Idle timeout, session freeze, and admin revoke race conditions need end-to-end tests |
| Refresh rotation and reuse detection | ✅ | ✅ | ✅ | 🟡 | Dashboards and paging policy for family-reuse incidents still need production drill evidence |
| Token revocation propagation | ✅ | 🟡 | 🟡 | ⚪ | Gateway watermark sync and replay after regional failover are not yet exercised |
| PDP evaluation and explainability | ✅ | 🟡 | 🟡 | ⚪ | Simulation API, obligation compliance tests, and performance evidence are pending |
| PAP policy publication and rollback | ✅ | 🟡 | ⚪ | ⚪ | Dual control, signed diff manifests, and canary promotion need workflow implementation |
| Hybrid RBAC and ABAC entitlements | ✅ | 🟡 | ⚪ | ⚪ | Entitlement expiration, deny precedence, and recertification batch jobs need build-out |
| Identity lifecycle for humans | ✅ | 🟡 | 🟡 | ⚪ | Offboarding proof package and archive export are not yet complete |
| Workload identity lifecycle | ✅ | ⚪ | ⚪ | ⚪ | Attestation verification, client-certificate rotation, and quarantine automation not started |
| SCIM provisioning and deprovisioning | ✅ | 🟡 | 🟡 | ⚪ | Bulk idempotency and source-of-truth guards require more connector contract tests |
| SCIM and federation drift reconciliation | ✅ | 🟡 | ⚪ | ⚪ | Severity scoring, low-risk auto-fix, and approval queue handling remain partial |
| Break-glass emergency access | ✅ | 🟡 | ⚪ | ⚪ | Dual approval APIs exist on paper only; expiry enforcement and evidence pack need implementation |
| Immutable audit and compliance export | ✅ | ✅ | 🟡 | 🟡 | Chain-hash verification, archive manifest checks, and legal-hold workflows need drills |
| Cloud key management and signing-key rotation | ✅ | ✅ | 🟡 | 🟡 | Automatic retire-after enforcement and key-ceremony runbook signoff are still pending |
| Admin API and UI race safety | ✅ | 🟡 | ⚪ | ⚪ | ETag handling, idempotency coverage, and session-view staleness detection need integration tests |
| Observability, SLOs, and incident automation | ✅ | 🟡 | 🟡 | 🟡 | Token-revocation, policy publish, and SCIM drift SLO dashboards need final alert tuning |

## Exit Criteria to Production
- No open critical or high security findings against authn, authz, token, federation, SCIM, audit, or break-glass paths.
- Every `🟡` or `⚪` row in security-critical capabilities has an approved go-live waiver or is upgraded to production-ready evidence.
- SLO dashboards exist for login latency, PDP latency, revocation propagation, SCIM drift backlog, and audit pipeline lag.
- At least one successful region failover, connector outage drill, and revocation replay exercise has been executed and documented.
- Compliance export proves full audit-chain integrity for a representative tenant and quarter.

## Test Expectations by Capability

| Capability family | Minimum automated evidence |
|---|---|
| Authentication and sessions | Unit tests, API contract tests, replay protection tests, multi-device integration tests |
| Token handling | Concurrency tests for refresh rotation, chaos tests for delayed revocation, signature-key rotation tests |
| Policy platform | Deterministic simulation tests, deny-precedence regression suite, obligation enforcement integration tests |
| Federation and SCIM | Connector contract tests, malformed-assertion tests, drift-detection replay tests |
| Lifecycle and entitlements | Deprovisioning reconciliation tests, expiry tests, conflict-resolution regression suite |
| Audit and compliance | Archive integrity verification, retention-policy tests, export manifest validation |

## Maturity Rubric
- **Design** means architecture, threat model, data contracts, and runbooks are reviewed and accepted.
- **Build** means the happy path plus critical failure handling are implemented behind a releasable flag.
- **Test** means positive, negative, concurrency, and security tests run automatically in CI or scheduled validation.
- **Ops readiness** means dashboards, alerts, runbooks, game-day evidence, and ownership are in place.
