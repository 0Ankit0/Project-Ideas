# Use Case Descriptions — Identity and Access Management Platform

**Document Version:** 1.0
**Status:** Approved
**Last Updated:** 2025-01-15
**Owner:** Platform Architecture Team

---

## Overview

This document provides detailed structured use case descriptions for the twelve core use cases of the IAM Platform. Each entry follows the Cockburn template and serves as a contractual specification between product, engineering, and QA. All business rules referenced below are defined in `business-rules.md`. All audit events referenced are defined in `event-catalog.md`.

---

## UC-001: Authenticate with Username/Password and MFA

**Use Case ID:** UC-001
**Name:** Authenticate with Username/Password and MFA
**Primary Actor:** End User
**Secondary Actors:** Risk Engine (internal), MFA Service (internal), Audit Service (internal)
**Goal:** The user establishes a verified session and receives a JWT access token and a refresh token, having proven both knowledge factor (password) and possession factor (MFA device).

**Preconditions:**
1. The user account exists in the tenant with status `active`.
2. The user has at least one enrolled MFA device if the tenant MFA policy is `required`.
3. The tenant is active and not suspended.
4. The client application is a registered OAuth 2.0 client or the native login form.
5. The request originates from an IP address not on the tenant denylist.

**Main Success Scenario:**
1. The user submits `username` and `password` to `POST /v1/auth/token` with `grant_type=password`.
2. The platform looks up the user record by `username` within the resolved tenant (via `tenant_id` header or subdomain).
3. The platform verifies the submitted password against the stored Argon2id hash; the hash parameters meet the minimum cost policy (memory 64 MiB, iterations 3, parallelism 4).
4. The platform checks the account status — if `active`, proceeds; increments `failed_attempts` counter on failure.
5. The risk engine evaluates the login event: device fingerprint, IP reputation score, geolocation delta from last login, and login velocity. A risk score between 0–100 is computed.
6. Because the tenant MFA policy is `required` (or risk score exceeds the `mfa_trigger_threshold`), the platform returns HTTP 200 with a short-lived `mfa_session_token` (10-minute TTL) and an MFA challenge descriptor listing available authenticator types.
7. The user selects an MFA method and submits the one-time code to `POST /v1/mfa/challenge/totp`.
8. The platform verifies the TOTP code using RFC 6238 with a ±1 step tolerance window. Replay is prevented by recording the used counter value.
9. The platform creates a session record with a UUID session ID, stores device info, IP, and expiry.
10. The platform issues a signed RS256 JWT access token (15-minute TTL) containing `sub`, `tid`, `roles`, `permissions`, `jti`, `iat`, `exp`, and a rotating refresh token (7-day TTL, HTTP-only secure cookie or response body per client type).
11. The platform emits an `auth.login.success` audit event containing actor ID, tenant ID, IP address, device fingerprint, MFA method used, risk score, and session ID.
12. The access token is returned to the client; the user is redirected to the originally requested resource.

**Alternative Flows:**

- **AF-01 — MFA Enrollment Required:** At step 6, if the tenant MFA policy is `required` but the user has no enrolled MFA device, the platform returns a `mfa_enrollment_required` status along with a temporary enrollment token. The user is redirected to the MFA enrollment flow (UC-004 or UC-005). After successful enrollment, the flow resumes from step 7.

- **AF-02 — Remember Device:** At step 12, if the user checks "remember this device" and the tenant policy permits device trust, the platform registers a device trust token (30-day TTL, tied to device fingerprint). On subsequent logins from the same device within the trust period, the MFA challenge step (steps 6–8) is skipped.

- **AF-03 — Risk-Based Step-Down:** At step 5, if the risk score is below `low_risk_threshold` (default: 10) and the tenant policy is `adaptive`, the MFA challenge is omitted entirely. The session is tagged `risk_skipped_mfa=true` for audit purposes.

**Exception Flows:**

- **EF-01 — Invalid Credentials:** At step 3, if the password does not match, the platform increments the `failed_attempts` counter. If `failed_attempts >= lockout_threshold` (default: 5 within 15 minutes), the account status transitions to `locked` and an `auth.account.locked` audit event is emitted. HTTP 401 is returned with a generic "Invalid credentials" message; the specific failure reason is never disclosed to the caller.

- **EF-02 — Account Locked or Suspended:** At step 4, if account status is `locked`, HTTP 403 is returned with `error_code: ACCOUNT_LOCKED`. If status is `suspended`, HTTP 403 is returned with `error_code: ACCOUNT_SUSPENDED`. The admin must use UC-006 to unlock or reactivate the account.

- **EF-03 — MFA Code Invalid or Expired:** At step 8, if the TOTP code is incorrect or expired, HTTP 401 is returned. After three consecutive MFA failures the `mfa_session_token` is invalidated and the user must restart the login flow. An `auth.mfa.failed` event is emitted.

- **EF-04 — High Risk Score Block:** At step 5, if risk score exceeds `block_threshold` (default: 85), the login is rejected regardless of credential validity. HTTP 403 is returned with `error_code: HIGH_RISK_BLOCKED`. An `auth.login.risk_blocked` audit event is emitted and an alert is sent to the tenant's configured SIEM webhook.

**Postconditions:**
- A session record exists in the session store, associated with the user, tenant, device, and IP.
- A valid JWT access token has been issued; the `jti` is recorded in the token registry.
- A refresh token has been issued and stored hashed in the refresh token table.
- An `auth.login.success` audit event has been persisted.

**Business Rules Referenced:**
- BR-AUTH-001: Password must meet minimum complexity (12 characters, mixed case, digit, symbol) unless SSO-only tenant.
- BR-AUTH-002: Account lockout after N consecutive failures within a rolling window (configurable per tenant).
- BR-AUTH-003: MFA is mandatory for all admin-role users regardless of tenant MFA policy.
- BR-AUTH-004: Refresh tokens rotate on every use; the previous token is immediately invalidated.
- BR-AUTH-005: Access tokens must not contain sensitive PII beyond `sub` (user ID).

**Audit Events Emitted:**
- `auth.login.initiated` — on receipt of credentials, before validation.
- `auth.login.success` — on successful token issuance.
- `auth.login.failed` — on credential mismatch.
- `auth.login.risk_blocked` — on high-risk score block.
- `auth.mfa.challenged` — when MFA challenge is issued.
- `auth.mfa.success` — on successful MFA verification.
- `auth.mfa.failed` — on MFA verification failure.
- `auth.account.locked` — when lockout threshold is reached.

---

## UC-002: SSO Login via SAML 2.0

**Use Case ID:** UC-002
**Name:** SSO Login via SAML 2.0
**Primary Actor:** End User
**Secondary Actors:** External IdP (SAML), SAML Validation Service (internal), Session Service (internal)
**Goal:** The user authenticates against an external SAML Identity Provider and receives an IAM platform session and tokens, without entering an IAM-managed password.

**Preconditions:**
1. A SAML 2.0 federation provider has been configured for the tenant (UC-009) with a valid signing certificate.
2. The user's email domain matches the tenant's configured SAML domain hint, or the user explicitly selects the SAML provider.
3. The external IdP is reachable and its signing certificate is valid (not expired, not revoked).
4. The IAM platform's SP metadata has been registered in the external IdP.

**Main Success Scenario:**
1. The user navigates to the IAM-protected application and is redirected to `GET /v1/sso/saml/{provider_id}/init`.
2. The IAM platform constructs a signed SAML 2.0 `AuthnRequest` with a unique `ID` attribute, `IssueInstant`, `Destination` (IdP SSO URL), and `AssertionConsumerServiceURL`. The request is signed using the platform's private key (RSA-SHA256).
3. The platform stores the `AuthnRequest ID` and a `RelayState` token (random opaque value tied to the original requested URL) in a short-lived (10-minute TTL) state store.
4. The user's browser is redirected to the IdP SSO endpoint via HTTP-Redirect binding with the deflate-encoded, base64-encoded `SAMLRequest` and `RelayState` query parameters.
5. The external IdP authenticates the user (via its own credential flow, which may include its own MFA).
6. The external IdP constructs a signed `SAMLResponse` containing an `Assertion` with `Subject`, `Conditions` (`NotBefore`, `NotOnOrAfter`, `AudienceRestriction`), `AuthnStatement`, and `AttributeStatement`. The response is signed and optionally encrypted.
7. The IdP posts the `SAMLResponse` and `RelayState` to the IAM platform ACS endpoint: `POST /v1/sso/saml/{provider_id}/acs`.
8. The platform decodes the base64 `SAMLResponse` and validates it: (a) XML signature verified against the stored IdP certificate; (b) `Issuer` matches the configured IdP entity ID; (c) `AudienceRestriction` contains the IAM platform SP entity ID; (d) `NotBefore <= now <= NotOnOrAfter` with a 2-minute clock skew tolerance; (e) `InResponseTo` matches a stored, unused `AuthnRequest ID`; (f) the `AuthnRequest ID` is marked used immediately to prevent replay.
9. The platform resolves the local user account via the `NameID` or configured attribute mapping (e.g., `email` attribute). If JIT provisioning is enabled and no local account exists, one is created.
10. The platform evaluates the tenant MFA policy. If step-up MFA is required post-SAML, the flow branches to UC-004.
11. A session record is created and the platform issues a JWT access token and refresh token using the same token issuance logic as UC-001.
12. The user is redirected to the original requested URL via the `RelayState` mapping.

**Alternative Flows:**

- **AF-01 — IdP-Initiated SSO:** The user authenticates at the IdP portal first and the IdP posts an unsolicited `SAMLResponse` to the ACS endpoint (no `InResponseTo`). The platform validates all other assertion fields; `InResponseTo` check is skipped. The `RelayState` is used to determine the target application, falling back to the tenant default landing URL.

- **AF-02 — JIT User Provisioning:** At step 9, if the local account does not exist and JIT provisioning is enabled, the platform creates a new user with attributes mapped from the SAML assertion (`email`, `givenName`, `surname`, `groups`). The user is assigned the tenant's default JIT role. A `user.provisioned.jit` audit event is emitted.

**Exception Flows:**

- **EF-01 — Invalid SAML Signature:** At step 8(a), if signature verification fails (wrong certificate, tampered payload), the platform rejects the response, emits `sso.saml.signature_invalid`, and returns HTTP 400.

- **EF-02 — Expired Assertion:** At step 8(d), if `NotOnOrAfter` is in the past (accounting for clock skew), the platform rejects the response with `error_code: SAML_ASSERTION_EXPIRED` and emits `sso.saml.assertion_expired`.

- **EF-03 — Replay Attack Detected:** At step 8(e), if `InResponseTo` does not match any stored request ID, or the request ID has already been used, the platform rejects the response with `error_code: SAML_REPLAY_DETECTED` and emits `sso.saml.replay_detected` with a security alert.

**Postconditions:**
- A session record exists linked to the external IdP assertion ID.
- A JWT access token and refresh token have been issued.
- If JIT provisioning fired, a new local user record exists.
- An `sso.login.success` audit event has been persisted with the assertion ID, IdP entity ID, and NameID.

**Business Rules Referenced:**
- BR-SSO-001: SAML assertions must be signed with RSA-SHA256 or stronger; SHA-1 signatures are rejected.
- BR-SSO-002: Clock skew tolerance is a maximum of 2 minutes.
- BR-SSO-003: Each `AuthnRequest ID` may be used only once (anti-replay); used IDs are retained for 24 hours.
- BR-SSO-004: Unencrypted SAML assertions are accepted only when the IdP-to-platform channel is TLS 1.2+.

**Audit Events Emitted:**
- `sso.saml.authn_request_sent` — when AuthnRequest is generated.
- `sso.saml.response_received` — on ACS POST receipt.
- `sso.saml.signature_invalid` — on signature validation failure.
- `sso.saml.assertion_expired` — on timing validation failure.
- `sso.saml.replay_detected` — on anti-replay failure.
- `sso.login.success` — on successful session establishment.
- `user.provisioned.jit` — on JIT user creation.

---

## UC-003: SSO Login via OIDC

**Use Case ID:** UC-003
**Name:** SSO Login via OIDC
**Primary Actor:** End User
**Secondary Actors:** External OIDC IdP, Token Validation Service (internal), Session Service (internal)
**Goal:** The user authenticates against an external OIDC Identity Provider using the Authorization Code flow with PKCE and receives an IAM platform session and tokens.

**Preconditions:**
1. An OIDC federation provider has been configured for the tenant with a valid `client_id`, `client_secret`, and discovery URL.
2. The platform has successfully fetched and cached the IdP's JWKS from the `jwks_uri`.
3. The IAM platform redirect URI is registered in the external OIDC IdP's client configuration.
4. The user's identity exists at the external IdP.

**Main Success Scenario:**
1. The user initiates login; the IAM platform resolves the OIDC provider from the tenant configuration.
2. The platform generates a `code_verifier` (43–128 random characters, unreserved ASCII), computes `code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))`, and generates a `state` nonce and a `nonce` claim value.
3. The platform stores `state`, `nonce`, and `code_verifier` in a short-lived (10-minute TTL) session-bound state store.
4. The user is redirected to the IdP authorization endpoint with parameters: `response_type=code`, `client_id`, `redirect_uri`, `scope=openid email profile`, `state`, `nonce`, `code_challenge`, `code_challenge_method=S256`.
5. The external IdP authenticates the user and issues an authorization code.
6. The IdP redirects the user to the IAM platform callback URL with `code` and `state`.
7. The platform validates that the returned `state` matches the stored value (CSRF protection).
8. The platform exchanges the authorization code for tokens: `POST {token_endpoint}` with `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret`, `code_verifier`.
9. The platform validates the received ID token: `iss` matches the IdP issuer, `aud` contains the platform `client_id`, `exp` is in the future, `iat` is within 5 minutes of now, `nonce` matches the stored value, signature verified against the JWKS.
10. The platform resolves the local user from the `sub` or configured attribute (typically `email`). JIT provisioning fires if no local account exists.
11. Platform emits a session and issues IAM JWT access token and refresh token.
12. The user is redirected to the original application URL.

**Alternative Flows:**

- **AF-01 — ID Token Signing Key Rotation:** At step 9, if the `kid` in the ID token header is not in the cached JWKS, the platform re-fetches the JWKS from `jwks_uri` once and retries validation before failing.

**Exception Flows:**

- **EF-01 — State Mismatch (CSRF):** At step 7, if `state` does not match, the platform aborts with `error_code: INVALID_STATE` and emits `sso.oidc.state_mismatch`.

- **EF-02 — Invalid ID Token:** At step 9, if any claim validation fails (expired, wrong issuer, wrong audience, bad signature), HTTP 400 is returned and `sso.oidc.token_invalid` is emitted.

**Postconditions:**
- IAM session, access token, and refresh token issued.
- OIDC `id_token` claims stored for the session lifetime (for logout hint on OIDC logout).
- `sso.oidc.login.success` audit event persisted.

**Business Rules Referenced:**
- BR-SSO-005: PKCE is mandatory for all OIDC flows; plain `code_challenge_method` is rejected.
- BR-SSO-006: ID token `nonce` must match; missing nonce is treated as an error when the platform included one in the request.

**Audit Events Emitted:**
- `sso.oidc.authorization_initiated`
- `sso.oidc.code_exchanged`
- `sso.oidc.token_invalid`
- `sso.oidc.state_mismatch`
- `sso.oidc.login.success`
- `user.provisioned.jit`

---

## UC-004: Enroll MFA Device — TOTP

**Use Case ID:** UC-004
**Name:** Enroll MFA Device (TOTP)
**Primary Actor:** End User
**Secondary Actors:** MFA Service (internal), Audit Service (internal)
**Goal:** The user registers a TOTP authenticator application as a second factor, verifying successful enrollment before it becomes active.

**Preconditions:**
1. The user is authenticated with a valid access token (or an enrollment-scoped temporary token issued during forced enrollment).
2. The tenant MFA policy allows TOTP as an acceptable MFA method.
3. The user has fewer than the maximum allowed MFA devices (default: 10).

**Main Success Scenario:**
1. The user requests TOTP enrollment: `POST /v1/mfa/enroll/totp`.
2. The platform generates a 20-byte random TOTP secret using a CSPRNG and encodes it as base32.
3. The platform constructs an `otpauth://totp/` URI with issuer (tenant display name), account (user email), secret, algorithm (SHA1), digits (6), and period (30).
4. The platform returns the secret and a QR code as a base64-encoded PNG; the secret is stored server-side in the `pending` state (not yet active).
5. The user scans the QR code with their authenticator application and submits a verification code: `POST /v1/mfa/enroll/totp/verify` with `{ "code": "123456" }`.
6. The platform validates the TOTP code using the pending secret with ±1 step tolerance; if valid, transitions the device state to `active`.
7. The platform generates ten single-use backup codes (8 random alphanumeric characters each), stores them hashed (SHA-256), and returns them to the user in plaintext once. This is the only time they are shown.
8. The platform emits a `mfa.device.enrolled` audit event with device type, device ID, and user ID.
9. The user is prompted to store the backup codes securely.

**Alternative Flows:**

- **AF-01 — Re-enrollment (Replace Existing TOTP):** If the user already has an active TOTP device, the new enrollment creates a `pending` record. The existing device remains active until the new enrollment is verified. On verification, the old device is archived.

**Exception Flows:**

- **EF-01 — Verification Code Invalid:** At step 6, if the code does not match, the platform increments the enrollment attempt counter. After 5 failed verification attempts, the pending enrollment is cancelled and a new one must be started.

- **EF-02 — Enrollment Session Expired:** If the user does not complete verification within 10 minutes, the pending secret is deleted server-side and the enrollment must be restarted.

**Postconditions:**
- A TOTP MFA device record exists with status `active`.
- Ten backup codes exist in the hashed backup code table.
- `mfa.device.enrolled` audit event persisted.

**Business Rules Referenced:**
- BR-MFA-001: TOTP secrets must be generated with at least 160 bits of entropy (20 bytes).
- BR-MFA-002: Backup codes are shown exactly once and cannot be retrieved; users must generate new codes if lost (invalidating old ones).
- BR-MFA-003: Used TOTP counter values are stored for 90 seconds to prevent replay within the same time step.

**Audit Events Emitted:**
- `mfa.device.enrollment_initiated`
- `mfa.device.enrolled`
- `mfa.device.enrollment_failed`

---

## UC-005: Enroll MFA Device — WebAuthn/FIDO2

**Use Case ID:** UC-005
**Name:** Enroll MFA Device (WebAuthn/FIDO2)
**Primary Actor:** End User
**Secondary Actors:** WebAuthn Service (internal), Browser WebAuthn API, Audit Service (internal)
**Goal:** The user registers a FIDO2 hardware key or platform authenticator as a phishing-resistant second factor using the W3C WebAuthn Level 2 protocol.

**Preconditions:**
1. The user is authenticated with a valid access token.
2. The user's browser supports the WebAuthn API (`window.PublicKeyCredential`).
3. The tenant policy allows WebAuthn as an acceptable MFA method.

**Main Success Scenario:**
1. The user initiates WebAuthn enrollment: `POST /v1/mfa/enroll/webauthn/options`.
2. The platform generates a `PublicKeyCredentialCreationOptions` object: `challenge` (32 random bytes), `rp.id` (platform RP ID, e.g., `iam.example.com`), `rp.name`, `user.id` (user UUID as bytes), `user.name`, `pubKeyCredParams` (ES256 and RS256 algorithm IDs), `timeout` (60000 ms), `attestation: "indirect"`, `authenticatorSelection: { residentKey: "preferred", userVerification: "preferred" }`.
3. The platform stores the `challenge` with a 60-second TTL.
4. The browser calls `navigator.credentials.create()` with the options; the user interacts with the authenticator (touch, PIN, biometric).
5. The authenticator creates a credential key pair; the public key, credential ID, attestation statement, and authenticator data are returned to the browser.
6. The browser submits the `PublicKeyCredential` response to `POST /v1/mfa/enroll/webauthn/verify`.
7. The platform validates the attestation: verifies the challenge, verifies the RP ID hash in authenticator data, checks the `origin` in `clientDataJSON`, parses the CBOR-encoded attestation statement, and (for non-none attestation) verifies the attestation signature.
8. The platform stores the credential ID, COSE-encoded public key, sign counter (0 at enrollment), attestation format, and AAGUID.
9. The platform emits a `mfa.device.enrolled` audit event with device type `webauthn`, AAGUID, and user ID.
10. Ten backup codes are generated as with TOTP enrollment.

**Alternative Flows:**

- **AF-01 — Platform Authenticator (Touch ID / Windows Hello):** The flow is identical; the `authenticatorSelection` `authenticatorAttachment` may be set to `platform` for platform-bound authenticators or `cross-platform` for roaming keys. Both are supported.

**Exception Flows:**

- **EF-01 — Challenge Expired:** At step 7, if the challenge has expired (> 60 seconds), the enrollment is rejected and the user must start again.

- **EF-02 — RP ID Mismatch:** At step 7, if the `rpIdHash` in the authenticator data does not match `SHA-256(rp.id)`, the enrollment is rejected as a potential phishing attempt. An alert is emitted.

**Postconditions:**
- A WebAuthn credential record exists: credential ID, public key, sign counter = 0, status `active`.
- `mfa.device.enrolled` audit event persisted.

**Business Rules Referenced:**
- BR-MFA-004: The RP ID must match the effective domain of the IAM login page.
- BR-MFA-005: Sign counter must be stored and checked on each assertion to detect cloned authenticators.
- BR-MFA-006: none attestation is accepted only when attestation conveyance is administratively set to permissive; enterprise deployments enforce direct or indirect attestation.

**Audit Events Emitted:**
- `mfa.device.enrollment_initiated`
- `mfa.device.enrolled`
- `mfa.device.enrollment_failed`
- `mfa.webauthn.rp_id_mismatch` (security alert)

---

## UC-006: Provision User via SCIM

**Use Case ID:** UC-006
**Name:** Provision User via SCIM
**Primary Actor:** SCIM Directory (External System)
**Secondary Actors:** SCIM Gateway (internal), User Service (internal), Audit Service (internal)
**Goal:** The external directory creates, updates, or deactivates a user account in the IAM platform via SCIM 2.0 API calls, maintaining synchronization between the authoritative directory and the IAM platform.

**Preconditions:**
1. SCIM has been configured for the tenant (UC-010) with a valid bearer token.
2. The SCIM directory has been granted the `scim:users:write` scope.
3. The IAM platform's SCIM endpoint is reachable by the directory.

**Main Success Scenario (Create):**
1. The SCIM directory sends `POST /scim/v2/Users` with a SCIM User resource body containing `schemas`, `externalId`, `userName`, `name`, `emails`, `active`, and optionally `groups`.
2. The platform authenticates the request by validating the Bearer token against the tenant's stored SCIM credential.
3. The platform parses the SCIM resource against RFC 7643 schema. Required fields: `userName`, `emails[primary]`.
4. The platform checks for an existing record with the same `externalId`; if found, updates instead of creating (idempotency).
5. The platform checks for `userName` and `emails[primary]` conflicts within the tenant. If a conflict exists and `externalId` differs, HTTP 409 is returned.
6. The platform creates the user record with status `active` (if `active=true`) or `inactive`.
7. If `groups` attribute is present, the platform synchronizes group memberships for the new user.
8. The platform returns HTTP 201 with the created SCIM User resource, including the IAM-assigned `id` and `meta.location`.
9. The platform emits a `user.provisioned` audit event.

**Alternative Flows:**

- **AF-01 — Update (PATCH):** On `PATCH /scim/v2/Users/{id}` with a SCIM Patch operation body, the platform applies the specified attribute changes (add, replace, remove) atomically. If the `active` attribute is set to `false`, the user's account is deactivated and all active sessions are revoked (UC-019).

- **AF-02 — Replace (PUT):** On `PUT /scim/v2/Users/{id}`, the entire user resource is replaced. Attributes not in the payload default to null (except system-managed fields). Session revocation rules apply as in AF-01.

**Exception Flows:**

- **EF-01 — Schema Validation Failure:** At step 3, if required attributes are missing or data types are invalid, HTTP 400 is returned with a SCIM error response (`scimType: invalidValue` or `scimType: invalidSyntax`) and a `detail` message identifying the invalid field.

- **EF-02 — Conflict:** At step 5, HTTP 409 is returned with `scimType: uniqueness` if `userName` or primary email is already in use.

- **EF-03 — Authentication Failure:** At step 2, if the Bearer token is invalid or expired, HTTP 401 is returned. If the token is valid but lacks required scope, HTTP 403 is returned.

**Postconditions:**
- User record created or updated in the IAM user store.
- Group memberships synchronized if provided.
- `user.provisioned` or `user.updated` audit event persisted.
- SCIM `meta.lastModified` timestamp updated.

**Business Rules Referenced:**
- BR-SCIM-001: `externalId` is the idempotency key; duplicate `externalId` within a tenant is not allowed.
- BR-SCIM-002: `userName` must be unique within a tenant and must match the email format.
- BR-SCIM-003: Deactivating a user via SCIM immediately revokes all active sessions.

**Audit Events Emitted:**
- `user.provisioned`
- `user.updated`
- `user.deprovisioned`
- `scim.auth.failed`
- `scim.schema.validation_failed`

---

## UC-007: Deprovision User — Offboarding

**Use Case ID:** UC-007
**Name:** Deprovision User (Offboarding)
**Primary Actor:** Tenant Admin (or SCIM Directory for automated offboarding)
**Secondary Actors:** Session Service, Token Service, Audit Service, Notification Service
**Goal:** A user account is completely and irrecoverably disabled, all active sessions are terminated, and all access tokens are invalidated. The user record is retained for compliance but access is permanently revoked.

**Preconditions:**
1. The target user exists in the tenant with status `active` or `locked`.
2. The actor has the `iam:users:delete` or `iam:users:write` scope.
3. The target user is not the sole Platform Admin of the tenant (to prevent lockout).

**Main Success Scenario:**
1. The actor sends `POST /v1/tenants/{tid}/users/{uid}/deactivate` or the SCIM directory sends `PATCH /scim/v2/Users/{id}` with `active=false`.
2. The platform sets the user's account status to `deactivated` atomically.
3. The platform queries the session store for all active sessions belonging to this user.
4. The platform revokes all sessions: updates session status to `revoked` in the session store and adds all associated access token `jti` values to the token denylist (TTL equal to their remaining lifetime).
5. The platform invalidates all refresh tokens for the user by marking them `revoked` in the refresh token table.
6. The platform removes the user from all group memberships.
7. The platform sends an `account_deactivated` notification to the user's registered email if the tenant notification policy is enabled.
8. A `user.deactivated` audit event is emitted containing the actor ID, target user ID, timestamp, and reason (if provided).
9. HTTP 200 is returned (admin flow) or the SCIM response returns the updated user resource with `active=false`.

**Alternative Flows:**

- **AF-01 — Hard Delete (GDPR Right to Erasure):** On `DELETE /v1/tenants/{tid}/users/{uid}`, the platform performs a logical delete followed by a PII erasure job: user PII fields (`name`, `email`, `phone`) are overwritten with a deterministic hash, and audit events referencing this user have the PII fields redacted. The user ID is retained for referential integrity in audit records. A `user.erased` event is emitted.

**Exception Flows:**

- **EF-01 — Last Admin Guard:** At step 1, if the target user is the last active admin in the tenant, HTTP 409 is returned with `error_code: LAST_ADMIN_DEACTIVATION_BLOCKED`.

- **EF-02 — User Not Found:** HTTP 404 with `error_code: USER_NOT_FOUND`.

**Postconditions:**
- User status is `deactivated`; no login is possible.
- All sessions revoked; all access tokens on the denylist; all refresh tokens invalidated.
- `user.deactivated` audit event persisted.

**Business Rules Referenced:**
- BR-USER-001: Deactivated users cannot authenticate; account status is checked before every credential evaluation.
- BR-USER-002: The last active admin of a tenant cannot be deactivated without first promoting another user.
- BR-GDPR-001: PII erasure must complete within 30 days of a verified erasure request.

**Audit Events Emitted:**
- `user.deactivated`
- `user.sessions.revoked_all`
- `user.tokens.revoked_all`
- `user.erased` (hard delete path)

---

## UC-008: Configure Federation Provider

**Use Case ID:** UC-008
**Name:** Configure Federation Provider
**Primary Actor:** Tenant Admin
**Secondary Actors:** Metadata Fetcher (internal), Certificate Store (internal), Policy Service (internal), Audit Service
**Goal:** The tenant admin registers or updates an external SSO provider (SAML 2.0 or OIDC) so that users can authenticate via that provider.

**Preconditions:**
1. The actor has the `iam:sso:write` scope.
2. For SAML: a valid SAML metadata XML document or metadata URL is available from the IdP.
3. For OIDC: the IdP discovery URL (`/.well-known/openid-configuration`) is accessible and returns a valid document.
4. The tenant is active.

**Main Success Scenario:**
1. The actor sends `POST /v1/tenants/{tid}/sso/providers` with a provider configuration body specifying `type` (`saml` or `oidc`), `display_name`, and type-specific fields.
2. **For SAML:** The platform fetches and parses the metadata XML (or accepts inline metadata). It extracts: `EntityID`, `SingleSignOnService` URLs (HTTP-Redirect and HTTP-POST bindings), `SingleLogoutService` URLs, and X.509 signing certificates. Certificate expiry is validated; a warning is logged if expiry is within 30 days.
3. **For OIDC:** The platform fetches the discovery document from the `issuer/.well-known/openid-configuration` URL, validates required fields (`issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`), and fetches the initial JWKS.
4. The actor configures attribute/claim mapping rules: source attribute name, transformation (direct, regex extract, static value), and target IAM field (email, display_name, groups, custom attributes).
5. The actor configures JIT provisioning settings: enabled/disabled, default role for JIT-provisioned users, attribute-driven group assignment rules.
6. The platform validates the entire configuration (reachability check, certificate validity, required field presence).
7. The configuration is stored in the tenant's SSO provider table. An authentication policy entry is created binding this provider to the tenant's login page.
8. The platform generates the SP metadata for this tenant/provider combination and makes it available at `GET /v1/tenants/{tid}/sso/providers/{pid}/sp-metadata`.
9. An `sso.provider.created` audit event is emitted.

**Alternative Flows:**

- **AF-01 — Update Provider:** On `PUT /v1/tenants/{tid}/sso/providers/{pid}`, existing sessions established via this provider remain valid. The new configuration takes effect for subsequent logins. Signing certificate rotation is handled transparently.

**Exception Flows:**

- **EF-01 — Metadata Unreachable:** At step 2/3, if the metadata URL returns HTTP error or times out, the platform returns HTTP 422 with `error_code: METADATA_FETCH_FAILED`.

- **EF-02 — Invalid Certificate:** If the signing certificate is expired or malformed, HTTP 422 is returned with `error_code: INVALID_CERTIFICATE` and the exact validation error.

**Postconditions:**
- SSO provider record stored and associated with the tenant.
- SP metadata available for download.
- Authentication policy entry created.
- `sso.provider.created` audit event persisted.

**Business Rules Referenced:**
- BR-SSO-007: A maximum of 5 SSO providers may be configured per tenant on the standard plan; 20 on enterprise.
- BR-SSO-008: Certificate expiry warnings are generated 30 days before expiry; automatic rotation is supported for OIDC (via JWKS refresh).

**Audit Events Emitted:**
- `sso.provider.created`
- `sso.provider.updated`
- `sso.provider.deleted`
- `sso.provider.certificate_expiry_warning`

---

## UC-009: Evaluate Authorization Policy

**Use Case ID:** UC-009
**Name:** Evaluate Authorization Policy
**Primary Actor:** Resource Server (internal caller, e.g., API Gateway)
**Secondary Actors:** Policy Engine (internal), Cache Service, Audit Service
**Goal:** The policy engine evaluates whether a given principal is authorized to perform a specific action on a specific resource, returning an allow or deny decision with reasoning.

**Preconditions:**
1. The requesting principal holds a valid, non-expired JWT access token.
2. Authorization policies exist for the tenant and are in an `active` state.
3. The resource and action are defined in the IAM resource registry.

**Main Success Scenario:**
1. The resource server calls `POST /v1/authz/evaluate` with body: `{ "principal": { "sub": "user_id", "tenant_id": "...", "roles": [...], "attributes": {...} }, "resource": { "type": "document", "id": "doc_123", "tenant_id": "..." }, "action": "document:read", "context": { "ip": "...", "time": "..." } }`.
2. The platform validates the JWT bearer token from the Authorization header, extracts claims.
3. The policy engine identifies all applicable policies for the combination of principal roles, resource type, and action. Policies are loaded from the cache (Redis, 60-second TTL) with a fallback to the database.
4. The engine evaluates each applicable policy in priority order. Policies support OPA-style Rego conditions with access to principal attributes, resource attributes, and request context.
5. The evaluation applies the configured conflict-resolution strategy: `deny-overrides` (any explicit deny wins) or `permit-overrides` (any explicit allow wins). Default is `deny-overrides`.
6. A final decision of `allow` or `deny` is produced along with the ID of the matching policy, the matched rule ID, and an optional human-readable reason.
7. The response `{ "decision": "allow", "policy_id": "pol_abc", "rule_id": "rule_xyz", "reason": "..." }` is returned in under 10ms (P99 target).
8. If the policy grants access with conditions (e.g., field-level filtering), those conditions are returned in the `obligations` array.
9. The decision is logged to the authorization event log if audit logging for authz decisions is enabled for the tenant.

**Alternative Flows:**

- **AF-01 — Batch Evaluation:** `POST /v1/authz/evaluate/batch` accepts an array of evaluation requests and returns decisions for all in a single round trip.

- **AF-02 — No Applicable Policy:** At step 3, if no policy matches the resource-action pair, the engine returns `deny` with reason `NO_POLICY_MATCH` (implicit deny default).

**Exception Flows:**

- **EF-01 — Policy Engine Unavailable:** If the policy cache and primary database are both unreachable, the engine fails closed: all decisions return `deny` with `error_code: POLICY_ENGINE_UNAVAILABLE`. This is logged as a critical alert.

**Postconditions:**
- Authorization decision returned to the caller.
- If audit logging is enabled, an `authz.decision` event is persisted.

**Business Rules Referenced:**
- BR-AUTHZ-001: Default stance is deny; explicit allow is required for access.
- BR-AUTHZ-002: Policy evaluation latency P99 target is 10ms; decisions must not block user-facing operations.
- BR-AUTHZ-003: Policies support RBAC (role checks), ABAC (attribute conditions), and time-bound rules (active_from, active_to).

**Audit Events Emitted:**
- `authz.decision` (when tenant audit logging for authz is enabled)
- `authz.policy_engine.unavailable` (critical alert)

---

## UC-010: Request and Use Break-Glass Access

**Use Case ID:** UC-010
**Name:** Request and Use Break-Glass Access
**Primary Actor:** End User (Requestor)
**Secondary Actors:** Approver (Tenant Admin or Platform Admin), Notification Service, Break-Glass Service, Audit Service
**Goal:** An authorized user obtains time-limited elevated access to a protected resource in an emergency, with mandatory approval, step-up authentication, and comprehensive audit logging throughout the access period.

**Preconditions:**
1. The requestor has the `iam:breakglass:request` scope.
2. The tenant has at least two configured break-glass approvers.
3. The requestor has an active MFA device for step-up verification.
4. The target resource and access level are defined in the break-glass resource catalog.

**Main Success Scenario:**
1. The requestor submits `POST /v1/breakglass/requests` with body: `{ "resource_id": "...", "access_level": "admin", "justification": "Production database unreachable, oncall engineer needs emergency read access to diagnose", "requested_duration_minutes": 60 }`.
2. The platform validates the requestor's current session is MFA-authenticated. If not, an MFA step-up challenge is issued (UC-001 step 6–8) before proceeding.
3. The platform creates a break-glass request record with status `pending`, assigns a unique `request_id`, and calculates the approval expiry time (`now + approval_window`, default 15 minutes).
4. The platform dispatches approval notifications to all configured approvers via email (with a signed approval link) and in-app notification.
5. An approver clicks the signed approval link or uses the admin console to call `POST /v1/breakglass/requests/{rid}/approve` with an optional comment.
6. The platform validates the approver's identity and that they have the `iam:breakglass:approve` scope and are not the same person as the requestor (self-approval is never permitted).
7. The request status transitions to `approved`. A time-bound credential is generated: a JWT access token with elevated permissions, scoped to the requested resource and access level, with TTL equal to the approved duration.
8. The platform returns the break-glass credential to the requestor.
9. The requestor uses the credential to access the target resource. Every API call made with this credential is logged with the break-glass `request_id` tag.
10. On credential expiry (or explicit revocation), the session is terminated and a `breakglass.session.expired` event is emitted.
11. The platform generates a post-access summary report: list of all actions taken, resources accessed, and timestamps, linked to the original request record.

**Alternative Flows:**

- **AF-01 — Deny:** At step 5, an approver calls `POST /v1/breakglass/requests/{rid}/deny`. The request status transitions to `denied`. The requestor is notified. No credential is issued.

- **AF-02 — Approval Window Expires:** If no approver acts within the approval window, the request transitions to `expired`. The requestor must submit a new request. An `breakglass.request.expired` event is emitted.

- **AF-03 — Emergency Self-Override (Platform Admin Only):** A Platform Admin with the `iam:breakglass:emergency_override` scope can approve their own request when no other approver is reachable. This is a restricted capability and every use emits a high-severity `breakglass.self_override` alert to the SIEM.

**Exception Flows:**

- **EF-01 — MFA Step-Up Failure:** At step 2, if step-up MFA fails three times, the request is cancelled and `breakglass.request.mfa_failed` is emitted.

- **EF-02 — No Approvers Configured:** At step 4, if no approvers are configured for the tenant, HTTP 422 is returned with `error_code: NO_APPROVERS_CONFIGURED`.

**Postconditions:**
- A break-glass request record with final status (`approved`, `denied`, `expired`) exists.
- If approved: a time-bound credential was issued; all actions were individually audited.
- A post-access report exists linked to the request record.
- `breakglass.request.completed` audit event persisted.

**Business Rules Referenced:**
- BR-BG-001: Self-approval is never permitted except with explicit `emergency_override` scope.
- BR-BG-002: Approved credential TTL cannot exceed 8 hours.
- BR-BG-003: All API calls using a break-glass credential are individually logged with the `request_id` tag.
- BR-BG-004: Two approvers must independently approve for access levels classified as `critical`.

**Audit Events Emitted:**
- `breakglass.request.submitted`
- `breakglass.request.approved`
- `breakglass.request.denied`
- `breakglass.request.expired`
- `breakglass.credential.issued`
- `breakglass.session.expired`
- `breakglass.self_override` (high-severity alert)
- `breakglass.action.*` (one event per API call within the session)
- `breakglass.report.generated`

---

## UC-011: Manage Role Assignments

**Use Case ID:** UC-011
**Name:** Manage Role Assignments
**Primary Actor:** Tenant Admin
**Secondary Actors:** RBAC Service (internal), Policy Cache, Audit Service
**Goal:** The admin assigns or revokes role bindings for users and groups, controlling what those principals are authorized to do within the IAM platform and downstream applications.

**Preconditions:**
1. The actor has the `iam:roles:assign` scope.
2. The target user or group exists in the tenant.
3. The role to be assigned exists (either a built-in platform role or a custom tenant role).

**Main Success Scenario:**
1. The actor sends `POST /v1/tenants/{tid}/users/{uid}/role-assignments` with body: `{ "role_id": "role_tenant_admin", "resource_scope": { "type": "tenant", "id": "{tid}" }, "expires_at": null }`.
2. The platform validates the actor has permission to grant the requested role (actors cannot grant roles with higher privilege than their own — privilege escalation prevention).
3. The platform checks for existing duplicate role assignment; if a duplicate is found, it returns the existing assignment (idempotent).
4. The platform creates the role assignment record with a UUID assignment ID, effective timestamp, optional expiry, and optional condition expression.
5. The platform invalidates the policy cache entries for the affected user (and all groups the user belongs to).
6. HTTP 201 is returned with the role assignment record.
7. A `role_assignment.created` audit event is emitted.

**Alternative Flows:**

- **AF-01 — Group Role Assignment:** On `POST /v1/tenants/{tid}/groups/{gid}/role-assignments`, the role is bound to the group. All group members inherit the role. Cache invalidation covers all group members.

- **AF-02 — Time-Bound Role Assignment:** If `expires_at` is provided, the assignment is active only until that timestamp. A scheduled job revokes expired assignments and emits `role_assignment.expired` events.

- **AF-03 — Revoke Assignment:** On `DELETE /v1/tenants/{tid}/role-assignments/{rid}`, the assignment is deleted and cache is invalidated. A `role_assignment.revoked` event is emitted.

**Exception Flows:**

- **EF-01 — Privilege Escalation Attempt:** At step 2, if the actor attempts to grant a role with higher privilege than they themselves hold, HTTP 403 is returned with `error_code: PRIVILEGE_ESCALATION_DENIED`.

- **EF-02 — Role Not Found:** HTTP 404 with `error_code: ROLE_NOT_FOUND`.

**Postconditions:**
- Role assignment record created (or deleted).
- Policy cache invalidated for the affected principal.
- `role_assignment.created` or `role_assignment.revoked` audit event persisted.

**Business Rules Referenced:**
- BR-RBAC-001: Users cannot grant roles with higher privilege than their own.
- BR-RBAC-002: Built-in platform roles (`platform_admin`, `tenant_admin`, `auditor`) cannot be deleted.
- BR-RBAC-003: Role assignments support conditions (e.g., `time_of_day`, `ip_range`, `resource_tag`) for ABAC-enhanced RBAC.

**Audit Events Emitted:**
- `role_assignment.created`
- `role_assignment.revoked`
- `role_assignment.expired`
- `role_assignment.privilege_escalation_denied`

---

## UC-012: Review and Export Audit Logs

**Use Case ID:** UC-012
**Name:** Review and Export Audit Logs
**Primary Actor:** Security Auditor (or Tenant Admin / Platform Admin)
**Secondary Actors:** Audit Log Service (internal), Export Service (internal), Object Storage
**Goal:** An authorized actor queries the immutable audit log, applies filters to scope results, and optionally exports events to a file or external SIEM system for compliance review.

**Preconditions:**
1. The actor has the `iam:audit:read` scope.
2. For exports, the actor also requires `iam:audit:export`.
3. The actor's role scope limits the visible tenants (tenant admins see only their tenant; platform admins see all).

**Main Success Scenario:**
1. The actor sends `GET /v1/tenants/{tid}/audit-logs` with query parameters: `event_type`, `actor_id`, `resource_type`, `resource_id`, `outcome` (`success`, `failure`), `from_time` (ISO 8601), `to_time` (ISO 8601), `page` (cursor-based), `limit` (max 1000 per page).
2. The platform validates the actor's scope; if the actor's token tenant does not match `{tid}` and the actor is not a platform admin, HTTP 403 is returned.
3. The platform queries the audit log store (append-only event store, e.g., Elasticsearch or ClickHouse) using the provided filters.
4. Results are returned as a paginated JSON array: each event contains `event_id`, `event_type`, `actor`, `target`, `outcome`, `metadata`, `timestamp`, `correlation_id`.
5. The actor uses the `next_cursor` from the response to page through results.
6. For export: the actor sends `POST /v1/tenants/{tid}/audit-logs/export` with `{ "filters": {...}, "format": "csv" | "json" | "ndjson", "destination": "download" | "s3://{bucket}/{key}" }`.
7. The platform enqueues an async export job and returns an export job ID with HTTP 202.
8. The export job queries the full dataset (no pagination limit), serializes to the requested format, and stores the file in object storage.
9. The actor polls `GET /v1/tenants/{tid}/audit-logs/export/{job_id}` for status. On completion, a signed download URL (15-minute TTL) is returned.
10. The actor downloads the export file via the signed URL.

**Alternative Flows:**

- **AF-01 — SIEM Streaming:** The platform supports a continuous event stream via `GET /v1/tenants/{tid}/audit-logs/stream` (Server-Sent Events). Events are pushed in near-real-time. The SIEM integration can use this endpoint with a long-lived service account token.

**Exception Flows:**

- **EF-01 — Date Range Too Large:** If `to_time - from_time > 90 days`, the query endpoint returns HTTP 400 with `error_code: DATE_RANGE_TOO_LARGE`. Export jobs support up to 365 days.

- **EF-02 — Audit Log Integrity Violation:** Each audit event is hash-chained to the previous event. If a gap or hash mismatch is detected during export, the job completes with a warning field `integrity_violations` listing the affected event IDs.

**Postconditions:**
- Audit log query results returned to the caller.
- If export: export job completed; signed download URL issued.
- A `audit.log.queried` event is emitted (to prevent audit log access from being invisible).
- A `audit.log.exported` event is emitted if an export was performed.

**Business Rules Referenced:**
- BR-AUDIT-001: Audit logs are immutable; no delete or update operations are permitted on audit records.
- BR-AUDIT-002: Audit logs are retained for a minimum of 365 days (standard) and 7 years (compliance tier).
- BR-AUDIT-003: Audit events are hash-chained to ensure tamper detection.
- BR-AUDIT-004: Export access is logged as an audit event itself (meta-auditing).

**Audit Events Emitted:**
- `audit.log.queried`
- `audit.log.exported`
- `audit.log.integrity_violation` (if hash chain check fails)
