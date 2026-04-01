# Requirements — Identity and Access Management Platform

**Document Version:** 1.0  
**Status:** Approved  
**Last Reviewed:** 2025-01-01  
**Owner:** Platform Engineering — Identity Team

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Functional Requirements](#2-functional-requirements)
   - 2.1 [Authentication Domain](#21-authentication-domain)
   - 2.2 [Authorization Domain](#22-authorization-domain)
   - 2.3 [Identity Lifecycle Domain](#23-identity-lifecycle-domain)
   - 2.4 [Federation and SSO Domain](#24-federation-and-sso-domain)
   - 2.5 [Audit and Compliance Domain](#25-audit-and-compliance-domain)
3. [Non-Functional Requirements](#3-non-functional-requirements)
   - 3.1 [Performance](#31-performance)
   - 3.2 [Availability and Resilience](#32-availability-and-resilience)
   - 3.3 [Security](#33-security)
   - 3.4 [Scalability](#34-scalability)
   - 3.5 [Compliance](#35-compliance)
4. [Constraints](#4-constraints)
5. [Assumptions](#5-assumptions)
6. [Acceptance Criteria Matrix](#6-acceptance-criteria-matrix)

---

## 1. Purpose and Scope

This document specifies the functional and non-functional requirements for the Identity and Access Management (IAM) Platform. The platform provides centralized authentication, authorization, identity lifecycle management, federation, and audit capabilities for multi-tenant SaaS deployments.

The requirements in this document are normative. Every SHALL statement constitutes a testable acceptance criterion. SHOULD statements are strong recommendations that may be deferred to a later iteration only with documented justification. MAY statements are optional.

**In scope:** Authentication services, authorization policy engine, identity lifecycle management, SCIM provisioning, SAML/OIDC federation, audit log pipeline, compliance reporting, and developer-facing APIs.

**Out of scope:** Application-level business logic authorization, end-user UI theming beyond accessibility baselines, and non-identity-related data stores.

---

## 2. Functional Requirements

### 2.1 Authentication Domain

**FR-001** — The system shall support username/password authentication with passwords hashed using Argon2id (parallelism=1, memory=64 MB, iterations=3) or bcrypt (cost factor ≥ 12) as a fallback for legacy tenant configurations. Plain-text password comparison is prohibited at all times.

**FR-002** — The system shall support the OIDC Authorization Code flow with PKCE (RFC 7636) as the primary browser-based authentication mechanism. The system shall reject authorization requests that omit `code_challenge` when PKCE is enforced for the client registration. The system shall support both `S256` and `plain` challenge methods but shall default to requiring `S256`.

**FR-003** — The system shall support SAML 2.0 SP-initiated SSO and IdP-initiated SSO. SP-initiated flows shall include the `RelayState` parameter. The system shall validate the SAML Response XML signature, the assertion signature, the `Issuer` element against the registered IdP entity ID, the `Audience` restriction, and the `NotBefore`/`NotOnOrAfter` timestamps within a ±5-minute clock skew window.

**FR-004** — The system shall support the OAuth 2.0 Device Authorization Grant (RFC 8628) for CLI tools, IoT devices, and other input-constrained clients. The device code shall expire after 5 minutes. The user code shall be 8 alphanumeric characters formatted as `XXXX-XXXX`. The polling interval shall be 5 seconds.

**FR-005** — The system shall support the OAuth 2.0 Client Credentials Grant for service accounts and machine-to-machine flows. Client secrets shall be stored as Argon2id hashes. The system shall support rotating client secrets with a configurable overlap window of up to 24 hours to allow rolling deployments.

**FR-006** — The system shall enforce TOTP-based multi-factor authentication as defined in RFC 6238. TOTP tokens shall use a 30-second time step, 6-digit code, and HMAC-SHA1 algorithm. The system shall accept tokens from the current window and one window on each side (−1/+1) to accommodate clock skew. Recovery codes shall consist of 10 single-use 16-character alphanumeric codes presented once at enrollment.

**FR-007** — The system shall support WebAuthn/FIDO2 authenticator registration and assertion verification (W3C WebAuthn Level 2). The system shall support platform authenticators (Touch ID, Windows Hello) and roaming authenticators (YubiKey, security keys). Attestation verification shall be configurable per tenant (none, indirect, direct). The system shall store the credential ID, public key, sign count, and AAGUID for each registered authenticator.

**FR-008** — The system shall support push notification MFA via a registered mobile authenticator application. Push challenges shall expire after 60 seconds. The system shall support approve/deny actions on the push notification. Repeated denied pushes (≥3 in 10 minutes) shall trigger an alert and optionally lock the account pending admin review.

**FR-009** — The system shall enforce adaptive MFA based on a computed risk score. Risk signals shall include: geo-velocity (login from geographically improbable location relative to prior login), new or unrecognized device fingerprint, anomalous login time relative to the user's historical pattern, failed authentication attempts in the preceding 1 hour, and whether the source IP appears on threat intelligence feeds. A risk score ≥ 70 (scale 0–100) shall require step-up MFA before issuing tokens.

**FR-010** — The system shall support passwordless login via a magic link delivered to the user's verified email address. The magic link shall contain a cryptographically random token of at least 128 bits of entropy. The link shall expire after 15 minutes. Each token shall be single-use. The system shall record the IP address and user-agent associated with the request.

**FR-011** — The system shall support step-up authentication for privileged operations, including admin console access, credential rotation, break-glass activation, and any operation tagged with the `require_step_up` obligation. Step-up shall require the user to re-authenticate with a second factor within a fresh authentication window. The step-up assertion shall expire after 5 minutes of inactivity.

**FR-012** — The system shall maintain an active session list per user. Each session record shall include: session ID, device fingerprint (OS, browser, approximate location), authentication factors used, creation timestamp, last-active timestamp, and session state (`active`, `step_up_required`, `revoked`, `expired`, `terminated`). The user and tenant admin shall be able to enumerate and inspect all active sessions.

**FR-013** — The system shall support global logout that terminates all sessions for a given user. Global logout shall be initiatable by the user from the session management UI and by a tenant admin or platform admin via the management API. Global logout shall revoke all active refresh tokens for the user and shall propagate session revocation to all introspection endpoints within the revocation propagation SLA.

**FR-014** — The system shall enforce account lockout after 5 consecutive failed authentication attempts within a rolling 15-minute window. Lockout shall prevent further login attempts and shall send a notification to the user's registered email. The lockout duration shall be 15 minutes by default and configurable per tenant between 5 minutes and 24 hours. Each failed attempt and the lockout event shall be emitted as audit events.

**FR-015** — The system shall issue JWT access tokens with a default TTL of 10 minutes. Access tokens shall be signed with RS256 or ES256 using asymmetric keys. The JWT payload shall include: `iss`, `sub`, `aud`, `exp`, `iat`, `jti`, `tid` (tenant ID), `sid` (session ID), `kid` (key ID), and `policy_hash`. The system shall issue opaque refresh tokens with a 24-hour TTL. Refresh tokens shall be rotatable on use, and refresh token reuse shall trigger immediate revocation of the entire token family.

---

### 2.2 Authorization Domain

**FR-016** — The system shall support Role-Based Access Control (RBAC) with hierarchical role inheritance. Roles may be nested up to 5 levels deep. Permission resolution shall traverse the full inheritance hierarchy and deduplicate the resulting permission set. Role assignments shall take effect within 30 seconds of the assignment event being committed.

**FR-017** — The system shall support Attribute-Based Access Control (ABAC) policy predicates. ABAC predicates shall support comparison operators (`eq`, `neq`, `gt`, `lt`, `gte`, `lte`), membership operators (`in`, `not_in`), string operators (`starts_with`, `ends_with`, `matches`), and logical combinators (`and`, `or`, `not`). Predicates may reference subject attributes, resource attributes, environment attributes (time, IP, device posture), and action attributes.

**FR-018** — The system shall provide a Policy Decision Point (PDP) API that accepts an authorization request (subject, resource, action, environment context) and returns one of four decisions: `permit`, `deny`, `not_applicable`, or `indeterminate`. The response shall include a decision trace payload containing matched policy IDs, matched rule IDs, the resolved permission set, applied obligations, and the policy version hash used during evaluation.

**FR-019** — The system shall support a Policy Administration Point (PAP) for authoring, versioning, and publishing policies. Each policy shall carry a semantic version (major.minor.patch). Policy publication shall require approval from at least one authorized policy approver. The PAP shall maintain a full version history and support rollback to any prior published version.

**FR-020** — The system shall enforce Policy Enforcement Points (PEP) at every service boundary. PEPs shall reject requests when the PDP is unreachable and fail-closed for non-read operations. PEPs shall cache PDP decisions for up to 30 seconds using a cache invalidation mechanism triggered by policy publication events.

**FR-021** — The system shall support resource-level permission grants. A permission grant shall consist of a principal (user, group, service account, or role), an action (e.g., `project:read`, `document:write`), and a resource identifier (e.g., `resource:project-123`). The system shall support both exact-match resource identifiers and hierarchical path-based matching.

**FR-022** — The system shall support temporal access constraints on policy rules. Temporal constraints shall support time-of-day windows (e.g., `09:00–17:00 UTC`), day-of-week restrictions (e.g., `Monday–Friday`), and absolute validity windows with `valid_from` and `valid_until` timestamps. Requests evaluated outside the constraint window shall receive a `deny` decision.

**FR-023** — The system shall provide a policy simulation (dry-run) endpoint that accepts a policy change and an evaluation context and returns the expected decision delta without persisting any changes. The simulation response shall include the decision for each input context, the set of rules that would match, and a diff of the matched rules relative to the currently active policy version.

**FR-024** — The system shall return a policy decision trace in the PDP response for all audit-enabled tenants. The trace shall include: the policy bundle version hash, the list of policy rule IDs evaluated, the first matching rule ID, the final decision, applied obligations (e.g., `require_mfa`, `log_access`), and a correlation ID linking the trace to the originating request in the audit log.

**FR-025** — The system shall support group-based role assignment. A group may be assigned one or more roles. Membership in a group shall confer all roles assigned to that group. Nested group membership shall be resolved transitively. Changes to group membership shall propagate to active session tokens at next token refresh.

**FR-026** — The system shall support wildcard permission patterns in policy rules. The wildcard character `*` shall match any suffix within a permission namespace (e.g., `projects:*` grants all actions within the `projects` namespace). Double-wildcard `**` shall match across namespace boundaries. Wildcard grants shall be recorded with an explicit warning in the policy audit trail.

**FR-027** — The system shall enforce explicit deny override. A `deny` rule matching any predicate shall override any number of `permit` rules for the same principal, resource, and action. The precedence order shall be: explicit deny > explicit permit > not-applicable. An `indeterminate` result (policy evaluation error) shall fail closed for write, delete, and privileged operations.

**FR-028** — The system shall support obligation attachments on `permit` decisions. Supported obligations include: `require_mfa` (enforce step-up before proceeding), `log_access` (emit a high-priority audit event), `notify_owner` (send notification to resource owner), and `rate_limit` (apply a request-rate cap). Obligations shall be returned in the PDP response and enforced by the PEP before granting access.

**FR-029** — The system shall support policy bundles with activation and deactivation workflows. Activating a bundle shall require: policy simulation results acknowledged by the requester, approval from at least one policy approver, and a scheduled or immediate activation time. Deactivation shall follow the same approval workflow. Bundle state transitions shall be fully audited.

**FR-030** — The system shall enforce per-tenant policy isolation. Policies authored within one tenant shall not be visible, executable, or referenceable from another tenant. Cross-tenant access via policy rules is explicitly prohibited. The PDP shall include the tenant ID in every evaluation context and reject requests with a mismatched or absent tenant ID.

---

### 2.3 Identity Lifecycle Domain

**FR-031** — The system shall support invite-based user onboarding. An invite shall be issued by a tenant admin and delivered to the invitee's email address. The invite link shall contain a single-use token of at least 128 bits of entropy. The default invite expiry shall be 72 hours, configurable per tenant between 1 hour and 30 days. Expired or already-accepted invites shall return a clear error and shall prompt the admin to re-issue.

**FR-032** — The system shall support Just-In-Time (JIT) provisioning via federated login. When an authenticated federated identity has no matching local account and JIT provisioning is enabled for the IdP configuration, the system shall create a local account, apply the configured default role bootstrap, and emit a provisioning audit event. JIT provisioning shall be restricted to approved IdP/tenant mappings.

**FR-033** — The system shall support inbound SCIM 2.0 provisioning for the User and Group resource types (RFC 7643, RFC 7644). The SCIM endpoint shall support Create, Read, Update (PATCH and PUT), and Delete operations. SCIM PATCH operations shall be idempotent. The system shall support the `externalId` attribute for correlation with the upstream directory. SCIM operations shall emit provisioning events to the audit pipeline.

**FR-034** — The system shall enforce MFA enrollment within 7 days of account creation for standard users. Users who have not enrolled an MFA factor within the grace period shall be redirected to the MFA enrollment flow at next login and shall be unable to proceed until enrollment is complete. The grace period countdown shall be visible on the user dashboard.

**FR-035** — The system shall enforce immediate MFA enrollment for accounts assigned an administrative role. An admin account without an enrolled MFA factor shall not be able to complete login. The system shall redirect the admin to the MFA enrollment flow and shall not issue access tokens until at least one MFA factor is registered and verified.

**FR-036** — The system shall support user suspension. Suspending a user shall: immediately terminate all active sessions, revoke all active refresh tokens, block all subsequent login attempts, and freeze all entitlements (permissions remain stored but produce `deny` decisions during suspension). Suspension shall be reversible and shall require an actor and reason code to be recorded.

**FR-037** — The system shall support account restoration from the suspended state. Restoration shall re-enable login capability and unfreeze entitlement evaluation. The restoration event shall be recorded in the audit trail with the restoring actor, timestamp, and optional justification. The user's entitlements shall be validated against the current policy state upon restoration and any stale grants shall be flagged for review.

**FR-038** — The system shall support full deprovisioning of a user account. Deprovisioning shall: immediately revoke all active sessions and tokens, queue asynchronous revocation of all entitlements (role assignments, group memberships, direct permission grants), and transition the account to the `deprovisioned` state. The account record shall be retained for the audit retention period before archival.

**FR-039** — The system shall maintain a reconciliation proof after deprovisioning. The reconciliation proof shall be a signed record confirming that all entitlements associated with the deprovisioned account have been removed. The proof shall include the account ID, the list of removed entitlements with removal timestamps, the actor, and the timestamp of proof generation. Proof generation shall complete within 1 hour of the deprovisioning event.

**FR-040** — The system shall support service account lifecycle management. Operations shall include: create (with an assigned owner and scoped permission set), credential issuance, credential rotation (with overlap window), suspension (immediate token revocation), and retirement (permanent deactivation with entitlement cleanup). Service accounts shall not be used interactively and shall be associated with at least one owner.

**FR-041** — The system shall support group membership management. Adding or removing a member from a group shall take effect on the member's next token refresh. The system shall provide bulk add and bulk remove operations for groups. Group membership changes shall be audited with the actor, affected member, and timestamp.

**FR-042** — The system shall detect and alert on orphaned permissions and stale role assignments. An orphaned permission is a resource-level grant referencing a resource that no longer exists. A stale role assignment is one that has not been used in the past 90 days. Detections shall be reported in the compliance dashboard and shall generate alert events. Tenant admins shall be able to bulk-revoke detected stale assignments.

**FR-043** — The system shall support bulk identity lifecycle operations. Bulk operations shall accept a list of identity records and shall process each item independently. The response shall include a per-item status (success, failed, skipped) and an error detail for each failed item. Partial success is acceptable. Bulk operations shall be asynchronous for batches exceeding 100 items and shall provide a job ID for status polling.

**FR-044** — The system shall support identity merging for duplicate account resolution. The merge operation shall designate a primary account and one or more secondary accounts. The merge shall transfer entitlements from secondary accounts to the primary account, deduplicating overlapping grants. Secondary accounts shall be transitioned to `merged` state. The merge action shall be fully audited and require admin authorization.

**FR-045** — The system shall enforce a source-of-truth priority matrix for attribute conflicts during SCIM synchronization. The matrix shall define, for each user attribute (e.g., `displayName`, `email`, `department`), which source system holds authority (SCIM directory, local IAM, LDAP, HR system). Conflicts shall be resolved by the matrix and the losing value shall be discarded with a reconciliation warning emitted to the audit log.

---

### 2.4 Federation and SSO Domain

**FR-046** — The system shall support SAML 2.0 metadata import via URL and via manual XML upload. Metadata URLs shall be refreshed on a configurable schedule (default 24 hours). The system shall validate the metadata XML signature when a signing certificate is provided. Certificate rotation in refreshed metadata shall be handled automatically with a configurable overlap window.

**FR-047** — The system shall validate all elements of an inbound SAML assertion: the `Issuer` element against the registered IdP entity ID, the `Audience` restriction against the SP entity ID, the XML digital signature using the registered IdP certificate, the `NotBefore` and `NotOnOrAfter` timestamps within a ±5-minute clock skew tolerance, and the absence of replay (using a nonce/`InResponseTo` registry with a 5-minute TTL).

**FR-048** — The system shall expose an OIDC discovery endpoint at `/.well-known/openid-configuration` for each tenant. The discovery document shall include: `issuer`, `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`, `jwks_uri`, `registration_endpoint`, `scopes_supported`, `response_types_supported`, `grant_types_supported`, `subject_types_supported`, `id_token_signing_alg_values_supported`, and `claims_supported`.

**FR-049** — The system shall validate all claims of an inbound OIDC ID token: the `iss` claim against the registered IdP issuer URL, the `aud` claim against the registered client ID, the signature against the IdP's JWKS, the `iat` and `exp` claims for temporal validity, and the `nonce` claim against the value stored at authorization request time. Tokens failing any validation check shall be rejected and the failure shall be audited.

**FR-050** — The system shall support configurable claim mapping from SAML attributes or OIDC claims to internal user attributes. Mappings shall be defined per IdP configuration and shall support direct mapping (claim A → attribute B), static default value (if claim absent, set attribute to value X), and transformation expressions for simple string manipulations (prefix, suffix, uppercase, lowercase, regex-replace).

**FR-051** — The system shall support SCIM directory synchronization configuration per tenant. Each configuration shall specify the SCIM endpoint URL, bearer token (stored encrypted), sync schedule (cron expression or fixed interval), provisioning mode (import-only, export-only, bidirectional), and attribute mapping. SCIM sync jobs shall emit events for each created, updated, and deleted identity.

**FR-052** — The system shall support per-tenant federation trust configuration with support for multiple IdPs per tenant. Each IdP configuration shall include an alias, protocol (SAML or OIDC), trust anchors (certificate or JWKS URI), claim mapping rules, JIT provisioning flag, and default role bootstrap. Tenant admins shall be able to enable, disable, and test each IdP configuration independently.

**FR-053** — The system shall detect federation certificate expiry and alert 30 days before expiration. The alert shall be sent to the tenant admin contact email and shall appear in the platform notification center. A secondary alert shall be sent 7 days before expiry. If the certificate expires without renewal, the system shall disable the affected IdP configuration and emit a critical audit event.

**FR-054** — The system shall support SCIM drift reconciliation. A drift reconciliation job shall run every 15 minutes (configurable) and compare the current state of SCIM-managed identities against the authoritative source. Identities found in the source but not locally provisioned shall be created. Identities deprovisioned in the source but still active locally shall be suspended or deprovisioned according to the configured deprovision action.

**FR-055** — The system shall expose an SP-side SAML metadata endpoint per tenant at a stable URL (e.g., `/saml/metadata/{tenant-id}`). The metadata document shall include the SP entity ID, ACS URL, NameID format, and the SP signing certificate. The SP signing certificate shall be automatically renewed before expiry and the metadata endpoint shall serve the current certificate.

---

### 2.5 Audit and Compliance Domain

**FR-056** — The system shall emit an immutable audit event for every authentication attempt (success and failure), every authorization decision, and every identity lifecycle operation. Audit events shall be written to an append-only audit store that prevents modification or deletion within the retention period. Write failures to the audit store shall cause the originating operation to be retried or queued; silent loss of audit events is not permitted.

**FR-057** — Every audit event shall include the following fields: `event_id` (UUID v4), `tenant_id`, `actor_id` (user, service account, or system), `actor_type`, `target_id`, `target_type`, `action`, `decision` (permit/deny/success/failure), `source_ip`, `user_agent`, `device_fingerprint`, `correlation_id`, `request_id`, `timestamp` (RFC 3339 UTC), `policy_version_hash` (for authorization events), and `risk_score` (for authentication events).

**FR-058** — The system shall support audit log export in SIEM-compatible formats. Supported formats shall include JSON Lines (one event per line), CEF (Common Event Format), and LEEF (Log Event Extended Format). Exports shall support filtering by tenant, time range, actor, action type, and decision. Exports shall be deliverable via streaming API, webhook push to a configured SIEM endpoint, and scheduled batch export to object storage.

**FR-059** — The system shall retain audit events for 13 months in hot storage with full-text search capability. Events older than 13 months shall be moved to cold archive storage and retained for a total of 7 years from the event timestamp. Archive retrieval shall complete within 4 hours of request. Both hot and cold storage shall use AES-256-GCM encryption with tenant-scoped keys.

**FR-060** — The system shall support legal hold on audit records. A legal hold shall prevent deletion or archival of covered audit records beyond the normal retention policy. Legal holds shall be applied per tenant and optionally scoped to a time range, actor set, or action type. Active legal holds shall be visible in the compliance dashboard. Attempting to delete a record under legal hold shall result in a rejected operation and an audit event.

**FR-061** — The system shall provide break-glass access capability for emergency situations. Break-glass activation shall require: a written justification, dual approval from two distinct platform admins, and a defined time-bound scope (maximum 4 hours). All actions taken during a break-glass session shall be tagged with the break-glass session ID in the audit log. The break-glass session shall auto-terminate at the end of the authorized window.

**FR-062** — The system shall generate access review reports for entitlement certification campaigns. A campaign shall define the reviewer set, review scope (all users, specific groups, or roles), and deadline. Reviewers shall be able to certify (approve) or revoke each entitlement via the review UI or API. Entitlements not reviewed by the deadline shall be automatically revoked if the campaign is configured for auto-revoke-on-expiry.

**FR-063** — The system shall support IP allowlist enforcement per tenant. An IP allowlist shall consist of one or more CIDR ranges. When an allowlist is configured, authentication attempts from IPs outside the allowlist shall be blocked by default. Tenants may alternatively configure step-up MFA for out-of-allowlist attempts. Allowlist violations shall emit audit events with the source IP and the configured action taken.

**FR-064** — The system shall provide a compliance dashboard for each tenant. The dashboard shall display: current MFA enrollment coverage, stale entitlement count, recent break-glass activations, open access review campaigns and their completion percentage, policy version history, federation certificate expiry status, and a mapping of platform capabilities to SOC 2 Type II (CC6, CC7, CC8, CC9) and ISO 27001 Annex A controls.

**FR-065** — The system shall support cryptographic audit log integrity verification using a hash chain. Each audit event record shall include the SHA-256 hash of the previous record, forming a tamper-evident chain. The system shall expose a verification API that accepts a time range and returns a verification result indicating whether the hash chain is intact for all records in that range. Integrity check failures shall trigger an immediate security alert.

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-001** — The PDP decision API shall achieve P95 latency below 30 ms for cache-hit requests and below 120 ms for cache-miss requests, measured at 10,000 RPS sustained load. Cache invalidation triggered by policy publication shall not cause latency spikes exceeding 200 ms P99 during the invalidation window.

**NFR-002** — The authentication API (login endpoint, end-to-end including MFA factor verification but excluding IdP UI round-trips) shall achieve P95 latency below 800 ms under normal operating load. Argon2id hashing computation is included within this budget and shall be performed asynchronously off the request thread.

**NFR-003** — The token introspection endpoint shall achieve P95 latency below 10 ms. This endpoint is on the critical path for every inter-service API call and must be optimized to use an in-process or co-located cache backed by the session store.

**NFR-004** — The SCIM bulk provisioning pipeline shall sustain a throughput of 1,000 user records per minute with per-item idempotency guarantees. Provisioning jobs exceeding this rate shall be queued and processed without dropping records. Provisioning lag for the 99th percentile record in a batch shall not exceed 10 minutes.

**NFR-005** — Session store read operations shall achieve P99 latency below 5 ms. The session store shall be backed by a distributed in-memory data store with synchronous replication to at least two availability zones before acknowledging a write.

---

### 3.2 Availability and Resilience

**NFR-006** — The authentication service shall achieve a monthly uptime SLA of 99.95%, corresponding to fewer than 22 minutes of unplanned downtime per calendar month. Planned maintenance windows shall not count toward downtime if announced at least 7 days in advance and fall outside peak hours (06:00–22:00 local time for the largest tenant by volume).

**NFR-007** — The PDP service shall achieve a monthly uptime SLA of 99.99%, corresponding to fewer than 4.4 minutes of unplanned downtime per calendar month. The PDP shall be deployable in a sidecar mode co-located with consuming services to eliminate network-induced unavailability at the point of enforcement.

**NFR-008** — The audit event pipeline shall guarantee zero data loss. Audit events shall be durably written to at least two independent storage nodes before the originating operation is confirmed. The pipeline shall use durable queuing with acknowledged delivery and shall replay events on downstream consumer failure without duplicating records in the audit store.

**NFR-009** — The recovery time objective (RTO) for the authentication service shall be below 5 minutes and the recovery point objective (RPO) shall be below 30 seconds. Recovery procedures shall be automated, tested quarterly via chaos engineering exercises, and documented in a runbook accessible to on-call engineers.

**NFR-010** — The authentication service and PDP service shall be deployed in an active-active multi-region configuration with at least two geographically separated regions. Requests shall be routed to the nearest healthy region. A regional failure shall trigger automatic failover with no more than 10 seconds of elevated error rate during the transition.

---

### 3.3 Security

**NFR-011** — All data in transit shall be encrypted using TLS 1.2 or higher. TLS 1.3 shall be preferred and configured as the default. TLS 1.0 and 1.1 shall be disabled. Cipher suites shall be restricted to AEAD suites (AES-GCM, ChaCha20-Poly1305). HSTS shall be enforced with a `max-age` of at least 1 year for all external-facing endpoints.

**NFR-012** — All personally identifiable information (PII) stored at rest shall be encrypted with AES-256-GCM using tenant-scoped encryption keys. Tenant keys shall be managed in a hardware security module (HSM) or HSM-backed key management service. The system shall support Bring Your Own Key (BYOK) for tenants with regulatory requirements.

**NFR-013** — JWT signing keys (asymmetric key pairs) shall be rotated every 30 days. Old keys shall remain in the JWKS for a 72-hour overlap window to allow in-flight token validation before removal. Data encryption keys (DEKs) shall be rotated every 365 days with re-encryption of covered data completed within 7 days of key rotation initiation.

**NFR-014** — Token revocation shall propagate to all introspection endpoints and PEP caches within a P95 of 5 seconds and a P99 of 15 seconds from the time the revocation event is committed. Revocation propagation shall use a push-based invalidation channel (pub/sub) supplemented by a short cache TTL as a fallback.

**NFR-015** — All user passwords and client secrets shall be hashed with Argon2id using the following parameters: parallelism=1, memory=65536 KB (64 MB), iterations=3. The salt shall be a 16-byte cryptographically random value unique per credential. Re-hashing on parameter upgrade shall occur automatically at next successful authentication.

---

### 3.4 Scalability

**NFR-016** — The platform shall support horizontal scaling to 10 million active users per tenant without architectural changes. User attribute stores, session stores, and entitlement indexes shall be sharded by tenant. Onboarding a new tenant shall not require downtime or manual infrastructure provisioning.

**NFR-017** — The policy engine shall support up to 100,000 active policy rules per tenant. Policy evaluation shall scale linearly with the number of matching rules and shall not perform full-scan evaluation of all rules for each request. The policy index shall be maintained in memory with incremental updates on policy publication.

**NFR-018** — The platform shall support 500,000 concurrent active sessions per deployment. Session state shall be stored in a distributed, sharded session store. Session creation and lookup shall not require cross-shard coordination except during rebalancing events.

**NFR-019** — The audit event bus shall sustain a throughput of 50,000 events per second. The bus shall use a partitioned log (e.g., Kafka-compatible) with tenant-based partitioning to ensure ordered delivery per tenant. Consumer lag shall not exceed 30 seconds at sustained peak throughput.

---

### 3.5 Compliance

**NFR-020** — The platform shall implement SOC 2 Type II controls for Common Criteria families CC6 (Logical and Physical Access Controls), CC7 (System Operations), CC8 (Change Management), and CC9 (Risk Mitigation). Evidence artifacts for each control (configuration snapshots, audit reports, access review records) shall be exportable from the compliance dashboard.

**NFR-021** — The platform shall support GDPR data subject access requests (DSAR). Upon receiving an authenticated DSAR, the system shall compile and deliver all PII held for the subject within 72 hours. The DSAR response shall include authentication history, entitlement history, profile attributes, and audit records referencing the subject. Data erasure requests shall be supported with PII pseudonymization in retained audit records.

**NFR-022** — The platform shall support a HIPAA-eligible deployment configuration. The HIPAA configuration shall include: Business Associate Agreement (BAA) support, audit log controls meeting 45 CFR §164.312(b), automatic logoff after 15 minutes of inactivity, and encryption meeting NIST standards for ePHI at rest and in transit.

**NFR-023** — The platform architecture shall support achieving a FedRAMP Moderate authorization baseline. The system shall implement the applicable security controls from NIST SP 800-53 Rev 5 Moderate impact level, including AC, AU, IA, SC, and SI control families. A System Security Plan (SSP) template shall be maintainable from the compliance dashboard.

**NFR-024** — Audit log retention periods shall be configurable per tenant to meet jurisdiction-specific regulatory requirements. Configurable retention profiles shall include: default (13 months hot + 7 years archive), HIPAA (6 years), EU GDPR (limited by data minimization), and FedRAMP (3 years). Retention configuration changes shall require platform admin approval.

**NFR-025** — Federal deployment configurations shall use FIPS 140-2 (Level 1 or higher) validated cryptographic modules for all cryptographic operations including TLS, hashing, symmetric encryption, and asymmetric signing. FIPS mode shall be a deployment-time configuration flag that disables non-compliant algorithms across all services.

---

## 4. Constraints

**CON-001 — Protocol Standards Compliance:** The platform must implement OIDC, OAuth 2.0, SAML 2.0, SCIM 2.0, and WebAuthn/FIDO2 as specified by their respective standards bodies (IETF, OASIS, W3C). Proprietary extensions to standard protocols must be clearly documented and must not break standards-compliant clients.

**CON-002 — Multi-Tenancy Isolation:** Tenant data, policies, configurations, and identities must be strictly isolated at the application and storage layer. Tenant isolation must not rely solely on row-level security; tenant-scoped encryption keys provide a secondary isolation boundary.

**CON-003 — No Vendor Lock-In for Storage:** The session store, audit store, and identity store must support multiple backend implementations (e.g., PostgreSQL, Redis, Kafka) through adapter interfaces. Vendor-specific features may be used for performance but must not be required for correctness.

**CON-004 — API Versioning:** All public APIs must be versioned (e.g., `/v1/`, `/v2/`). Prior major API versions must be supported for a minimum of 18 months after the release of a superseding version. Breaking changes require a major version increment.

**CON-005 — Open Telemetry Observability:** All services must emit traces, metrics, and logs in OpenTelemetry format. Vendor-specific observability SDKs must not be used as the primary instrumentation layer.

**CON-006 — Deployment Environments:** The platform must be deployable on Kubernetes (1.27+) and must expose Helm charts for installation. Platform-specific managed services (e.g., AWS RDS, GCP Cloud Spanner) may be used as optional backends but must not be required for on-premises deployment.

**CON-007 — Team Size:** The engineering team delivering the initial production release consists of a maximum of 12 engineers. Requirements must be prioritized to ensure the most critical security capabilities (authentication, authorization, audit) are delivered before advanced features (entitlement certification campaigns, DSAR automation).

---

## 5. Assumptions

**ASM-001** — Consuming services (relying parties) are responsible for implementing the PEP pattern. The IAM Platform provides the PDP API and SDK; it does not automatically wrap all relying party APIs.

**ASM-002** — The deployment environment provides a TLS-terminating ingress layer. Services within the cluster may use mutual TLS (mTLS) for east-west traffic; the IAM Platform will support mTLS for service-to-service communication.

**ASM-003** — At least one human identity provider (corporate IdP or the platform's native username/password store) is configured per tenant at the time of tenant onboarding. The platform does not support tenants with zero configured authentication methods.

**ASM-004** — Clock synchronization (NTP) is available across all deployment nodes. TOTP and SAML assertion validation depend on system clocks being accurate within ±2 seconds. Deployments operating with larger clock skew may experience elevated authentication failures.

**ASM-005** — Tenants are responsible for managing their own SAML and OIDC IdP configurations. The platform provides tooling and validation but does not operate corporate IdPs on behalf of tenants.

**ASM-006** — The platform's risk scoring engine uses IP geolocation data from a licensed third-party database. Accuracy of geo-velocity signals depends on the quality and freshness of the geolocation database, which will be updated at least weekly.

**ASM-007** — Email delivery for magic links, invite notifications, and MFA alerts relies on a configured outbound SMTP or transactional email provider. Email delivery SLAs are outside the scope of the IAM Platform's availability guarantees.

**ASM-008** — Service accounts created within the platform are used by application workloads running within the same deployment trust boundary. Service account tokens should not be distributed to end users or used in browser-based flows.

**ASM-009** — FIPS 140-2 deployment mode is an opt-in configuration for federal customers. The default deployment does not restrict cryptographic algorithm selection to FIPS-approved algorithms, enabling support for WebAuthn and other modern protocols that may use non-FIPS algorithms.

---

## 6. Acceptance Criteria Matrix

| ID | Capability | Acceptance Criterion | Verification Method |
|----|------------|----------------------|---------------------|
| AC-001 | Password authentication | Successful login with valid credentials returns access token (JWT) and refresh token within 800 ms P95 | Load test + integration test |
| AC-002 | Password hashing | No plaintext or reversibly encoded password stored; Argon2id parameters confirmed in credential record | Security audit + unit test |
| AC-003 | Account lockout | After 5 failed attempts in 15 minutes, login is blocked; audit event emitted; email notification sent | Integration test |
| AC-004 | OIDC PKCE flow | Authorization code cannot be exchanged without the correct `code_verifier`; missing or incorrect verifier returns `invalid_grant` | Integration test |
| AC-005 | SAML assertion validation | Tampered signature, expired assertion, mismatched audience, and replayed assertion each produce distinct denial audit events | Integration test |
| AC-006 | TOTP MFA | Valid TOTP code within ±1 window accepted; expired or reused code rejected; 10 recovery codes generated at enrollment | Integration test |
| AC-007 | WebAuthn registration | Authenticator credential stored with credential ID, public key, sign count, AAGUID; subsequent assertion with wrong sign count rejected | Integration test |
| AC-008 | Adaptive MFA trigger | Login from new device with risk score ≥ 70 redirected to MFA challenge; token not issued without completed challenge | Integration test |
| AC-009 | Magic link expiry | Magic link token rejected after 15 minutes; same token rejected on second use | Integration test |
| AC-010 | JWT claims | Issued JWT contains `iss`, `sub`, `aud`, `exp`, `iat`, `jti`, `tid`, `sid`, `kid`, `policy_hash` | Unit test |
| AC-011 | Refresh token rotation | Refresh token use returns new access token and new refresh token; original refresh token invalid after use | Integration test |
| AC-012 | Refresh token reuse detection | Replaying a consumed refresh token revokes the entire token family; subsequent introspection of any token in the family returns revoked | Integration test |
| AC-013 | PDP permit decision | Valid request matching an explicit permit rule returns `permit` with trace containing matched rule ID and policy version hash | Integration test |
| AC-014 | PDP deny override | Request matching both permit and explicit deny rules returns `deny`; deny takes precedence | Unit test |
| AC-015 | PDP indeterminate fail-close | PDP evaluation error on a write operation produces `deny`; error logged with correlation ID | Unit test |
| AC-016 | Policy simulation | Dry-run endpoint returns expected decision delta without modifying active policy state | Integration test |
| AC-017 | Temporal constraint | Request made outside configured time-of-day window returns `deny` from PDP | Integration test |
| AC-018 | PDP latency SLA | P95 < 30 ms cache hit, P95 < 120 ms cache miss at 10,000 RPS sustained | Performance test |
| AC-019 | User suspension | Session terminated within 5 seconds; login blocked; introspection of former access token returns `revoked` | Integration test |
| AC-020 | Deprovisioning reconciliation | Reconciliation proof generated within 1 hour; lists all removed entitlements with timestamps | Integration test |
| AC-021 | SCIM idempotency | Sending the same PATCH request twice produces no additional grant or duplicate record | Integration test |
| AC-022 | SCIM drift reconciliation | User deprovisioned in source but active locally suspended within one reconciliation cycle (15 minutes) | Integration test |
| AC-023 | Federation certificate alert | Alert email sent to tenant admin 30 days before IdP certificate expiry | Integration test |
| AC-024 | Audit event completeness | Every audit event contains all 16 required fields; missing field causes event to be rejected at ingestion | Unit test + audit schema test |
| AC-025 | Audit hash chain integrity | Verification API confirms unbroken hash chain for a 24-hour window; confirmed by independent chain replay | Integration test |
| AC-026 | Legal hold enforcement | Attempt to delete an audit record under legal hold returns error; deletion event audited | Integration test |
| AC-027 | Break-glass dual approval | Break-glass activation without two distinct approver approvals returns `forbidden`; activation with approvals succeeds and is audited | Integration test |
| AC-028 | IP allowlist block | Authentication attempt from IP outside configured allowlist blocked; audit event emitted with source IP | Integration test |
| AC-029 | Token revocation propagation | Revoked access token returns `invalid_token` from introspection within 5 seconds P95 | Performance test |
| AC-030 | DSAR compilation | DSAR response includes authentication history, entitlement history, profile PII, and audit references for the subject; delivered within 72 hours | Integration test |
