# User Stories — Identity and Access Management Platform

**Document Version:** 1.0  
**Status:** Approved  
**Last Reviewed:** 2025-01-01  
**Owner:** Platform Engineering — Identity Team

---

## Table of Contents

- [Roles and Personas](#roles-and-personas)
- [Authentication Stories (US-001 – US-008)](#authentication-stories)
- [MFA Setup Stories (US-009 – US-011)](#mfa-setup-stories)
- [SSO Stories (US-012 – US-014)](#sso-stories)
- [Session Management Stories (US-015 – US-016)](#session-management-stories)
- [Identity Lifecycle Stories (US-017 – US-021)](#identity-lifecycle-stories)
- [Provisioning and Directory Stories (US-022 – US-024)](#provisioning-and-directory-stories)
- [Authorization and Policy Stories (US-025 – US-027)](#authorization-and-policy-stories)
- [Service Account and OAuth Client Stories (US-028 – US-031)](#service-account-and-oauth-client-stories)
- [Compliance and Audit Stories (US-032 – US-037)](#compliance-and-audit-stories)
- [Security Operations Stories (US-038 – US-040)](#security-operations-stories)

---

## Roles and Personas

| Role | Description |
|------|-------------|
| **Platform Admin** | Operates the IAM Platform infrastructure, manages global settings, enables features for tenants, performs break-glass operations, and responds to platform-level incidents. |
| **Tenant Admin** | Manages identity and access configuration within a single tenant: user onboarding, role assignments, policy authoring, federation setup, IP allowlists, and compliance reporting. |
| **End User** | A human user authenticating to access protected applications. May be an employee, contractor, or external collaborator. |
| **Security Auditor** | Reviews audit logs, generates compliance reports, monitors for anomalies, and validates that controls are operating as intended. May be internal or external. |
| **Developer / App Owner** | Builds applications that integrate with the IAM Platform APIs. Registers OAuth clients, manages service accounts, and uses the policy decision API. |

---

## Authentication Stories

### US-001: Password Login

**As an** End User, **I want** to log in with my username and password, **so that** I can access protected applications without needing a separate account for each one.

**Acceptance Criteria:**
- AC1: Submitting a valid username and password returns an access token (JWT) and a refresh token within 800 ms P95.
- AC2: The access token includes `iss`, `sub`, `aud`, `exp`, `iat`, `jti`, `tid`, `sid`, `kid`, and `policy_hash` claims.
- AC3: An authentication success audit event is emitted containing the actor ID, source IP, device fingerprint, and timestamp.
- AC4: Submitting an invalid password returns HTTP 401 with a generic "Invalid credentials" message; no indication of whether the username exists is provided.
- AC5: Each failed attempt is recorded; after 5 failures within 15 minutes the account is locked and the user receives an email notification.

---

### US-002: Account Lockout and Self-Unlock

**As an** End User, **I want** to be notified when my account is locked due to failed login attempts and to have a clear path to regain access, **so that** I do not remain blocked without knowing what to do.

**Acceptance Criteria:**
- AC1: After the 5th consecutive failed login within the 15-minute window, the account enters `locked` state and a notification email is sent to the registered address.
- AC2: The notification email includes the lock time, the source IP of the last attempt, and a link to initiate a password reset.
- AC3: Attempting to log in while locked returns HTTP 423 with a message indicating the remaining lockout duration.
- AC4: A lockout event and each failed attempt that contributed to it are individually recorded in the audit log.
- AC5: After the lockout duration expires (default 15 minutes), the account is automatically unlocked and the failure counter is reset.
- AC6: A Tenant Admin can manually unlock the account from the admin console before the lockout duration expires; the manual unlock is audited.

---

### US-003: Magic Link Passwordless Login

**As an** End User, **I want** to log in by clicking a link sent to my email, **so that** I can authenticate without needing to remember a password.

**Acceptance Criteria:**
- AC1: Requesting a magic link for a valid email address returns HTTP 202; no indication is given whether the email corresponds to an existing account (to prevent enumeration).
- AC2: The magic link email is delivered within 60 seconds.
- AC3: The link token contains at least 128 bits of cryptographic randomness and is single-use.
- AC4: Clicking the link within 15 minutes authenticates the user and issues access and refresh tokens.
- AC5: Clicking the link after 15 minutes returns an error page explaining the link has expired and offering to send a new one.
- AC6: Clicking an already-used link returns an error page explaining the link has already been used.
- AC7: The authentication event records the source IP and user-agent at the time the link was clicked.

---

### US-004: Step-Up Authentication for Privileged Operations

**As an** End User, **I want** to be prompted for a second authentication factor before performing sensitive operations, **so that** a stolen session cannot be used to make destructive changes.

**Acceptance Criteria:**
- AC1: Accessing an endpoint tagged with the `require_step_up` obligation triggers a step-up challenge even when the user already holds an active session.
- AC2: The step-up challenge accepts any enrolled second factor (TOTP, WebAuthn, push notification).
- AC3: A successful step-up response returns a step-up assertion valid for 5 minutes; the step-up assertion expires if the user is inactive for 5 minutes.
- AC4: The protected operation proceeds only after a valid step-up assertion is presented.
- AC5: Failing the step-up challenge 3 consecutive times within the step-up window triggers a suspicious-activity alert and suspends the step-up session.
- AC6: The step-up event (challenge issued, success, failure) is recorded in the audit log.

---

### US-005: Adaptive MFA on Risk Signal

**As an** End User, **I want** the platform to automatically require additional verification when something unusual is detected about my login, **so that** my account is protected even if my password is compromised.

**Acceptance Criteria:**
- AC1: A login attempt with a risk score ≥ 70 is interrupted after the password phase and presents an MFA challenge before issuing tokens.
- AC2: Risk score contributors (new device, geo-velocity, anomalous time, threat IP) are each individually logged in the authentication event.
- AC3: A successful MFA response clears the risk hold and issues tokens; the authentication event records which MFA factor was used.
- AC4: A failed MFA response increments the lockout counter; three consecutive failed MFA responses within one session trigger an alert.
- AC5: Users can view the device and location information that triggered the risk challenge in their account security page.

---

### US-006: Password Reset

**As an** End User, **I want** to reset my password using my registered email address, **so that** I can regain access to my account if I forget my password.

**Acceptance Criteria:**
- AC1: Submitting a password reset request for any email address returns HTTP 202 with a generic confirmation; no account existence information is disclosed.
- AC2: A reset link with a single-use, 128-bit entropy token is sent to the registered email address and expires after 60 minutes.
- AC3: The reset page requires the new password to satisfy the tenant's configured password policy (minimum length, complexity, breach check).
- AC4: Submitting a new password that matches the current password or any of the last 10 passwords returns a validation error.
- AC5: On successful reset, all active sessions are terminated, all refresh tokens are revoked, and the user must log in again.
- AC6: A password-changed audit event is emitted including the actor, source IP, and timestamp.
- AC7: Using an expired or already-used reset token returns an error page with an offer to request a new link.

---

### US-007: Device Authorization Grant (CLI Login)

**As a** Developer, **I want** to authenticate a CLI tool by entering a short user code in my browser, **so that** the CLI can obtain tokens without requiring me to paste long tokens into the terminal.

**Acceptance Criteria:**
- AC1: The CLI calls the device authorization endpoint and receives a `device_code`, `user_code`, and `verification_uri` within 2 seconds.
- AC2: The `user_code` is an 8-character string formatted as `XXXX-XXXX` and the device code expires after 5 minutes.
- AC3: The user opens the `verification_uri` in a browser, authenticates, and approves the device; the CLI then receives tokens on its next polling call.
- AC4: The CLI polls at the specified interval (5 seconds); polling faster than the interval returns `slow_down`; polling after approval returns the token response.
- AC5: If the user denies the request or the device code expires, the CLI receives `access_denied` or `expired_token` respectively.
- AC6: The issued access token is scoped to the permissions the user approved; the authorization event is audited.

---

### US-008: Global Logout

**As an** End User, **I want** to sign out of all my active sessions at once, **so that** I can ensure no session remains active on a device I no longer control.

**Acceptance Criteria:**
- AC1: Clicking "Sign out everywhere" in the security settings page triggers global logout for the authenticated user.
- AC2: All active sessions for the user are terminated and all refresh tokens are revoked within 5 seconds P95.
- AC3: A subsequent introspection call on any formerly valid access token returns `revoked`.
- AC4: The global logout event is recorded in the audit log with the actor, the count of sessions terminated, and the timestamp.
- AC5: After global logout, the user is redirected to the login page; attempting to use a revoked refresh token returns `invalid_token`.

---

## MFA Setup Stories

### US-009: TOTP MFA Enrollment

**As an** End User, **I want** to enroll a TOTP authenticator app as my second factor, **so that** my account is protected with an additional layer of security.

**Acceptance Criteria:**
- AC1: The enrollment flow displays a QR code containing a `otpauth://` URI with the issuer, account label, secret, algorithm (SHA1), digits (6), and period (30).
- AC2: The user must successfully verify a live TOTP code before enrollment is confirmed; entering an incorrect code returns an error without saving the enrollment.
- AC3: Upon successful verification, 10 single-use recovery codes are displayed exactly once; they are not retrievable again after the user dismisses the confirmation screen.
- AC4: Recovery codes are stored as Argon2id hashes; the plaintext is never persisted.
- AC5: A TOTP-enrolled event is recorded in the audit log with the actor and timestamp.
- AC6: The user can see the TOTP factor listed in their security settings with the enrollment date and an option to remove it.
- AC7: Removing a TOTP factor while it is the only enrolled MFA factor requires the user to acknowledge that MFA protection will be reduced.

---

### US-010: WebAuthn Security Key Enrollment

**As an** End User, **I want** to register a hardware security key or platform authenticator as my second factor, **so that** I can use phishing-resistant authentication.

**Acceptance Criteria:**
- AC1: The enrollment flow calls the WebAuthn `navigator.credentials.create()` API with a server-generated challenge, the relying party ID, and the user's ID.
- AC2: The attestation response is verified server-side; the credential ID, public key (COSE format), sign count, and AAGUID are stored.
- AC3: The tenant admin can configure required attestation conveyance (`none`, `indirect`, `direct`); a mismatch between tenant policy and submitted attestation returns an error.
- AC4: The user can assign a human-readable name to each registered authenticator (e.g., "YubiKey 5C Nano — MacBook Pro").
- AC5: A WebAuthn-credential-registered event is recorded in the audit log.
- AC6: The user can register up to 10 WebAuthn credentials; attempting to register an 11th returns a clear error with instructions to remove an existing one.
- AC7: Authenticating with a registered security key verifies the assertion signature and the monotonically increasing sign count; a non-increasing sign count is rejected and generates a security alert.

---

### US-011: Push Notification MFA Enrollment

**As an** End User, **I want** to receive a push notification on my mobile device when logging in, **so that** I can approve or deny login attempts with a single tap.

**Acceptance Criteria:**
- AC1: The enrollment flow pairs the user's account with the mobile authenticator app by scanning a QR code; the pairing token expires after 10 minutes.
- AC2: A test push notification is sent immediately after enrollment to verify delivery; the user must approve it to confirm enrollment.
- AC3: At login time, a push notification is delivered to the registered device; the notification includes the source IP, approximate location, and application name of the login attempt.
- AC4: The user can approve or deny the push request; a deny response results in a failed authentication event and an alert.
- AC5: If the push notification is neither approved nor denied within 60 seconds, the challenge times out and the user is prompted to use an alternative factor.
- AC6: Three consecutive deny responses within 10 minutes trigger a suspicious-activity alert and optionally lock the account pending admin review.
- AC7: A push-notification-mfa-enrolled event and each push challenge outcome (approved, denied, timed-out) are recorded in the audit log.

---

## SSO Stories

### US-012: SSO Login via SAML

**As an** End User, **I want** to log in using my corporate identity provider via SAML SSO, **so that** I can use my existing corporate credentials without creating a separate password.

**Acceptance Criteria:**
- AC1: Clicking "Sign in with [IdP name]" initiates a SAML SP-initiated SSO flow with a valid `AuthnRequest` containing `AssertionConsumerServiceURL`, `RelayState`, and a signed request (if signing is configured).
- AC2: Upon return, the system validates the SAML Response: issuer matches the registered IdP entity ID, audience matches the SP entity ID, signature validates against the registered certificate, and `NotBefore`/`NotOnOrAfter` are within ±5-minute tolerance.
- AC3: A replayed assertion (previously seen `InResponseTo`/nonce within 5 minutes) is rejected with an audit event.
- AC4: Successfully validated attributes are mapped to the user's local profile per the configured claim mapping rules; unmapped required attributes block login with a specific error.
- AC5: If JIT provisioning is enabled and no local account exists, a new account is created with the configured default roles and a provisioning audit event is emitted.
- AC6: The issued access token `sub` matches the user's local account ID; the token `acr` claim reflects the SAML authentication context class.

---

### US-013: SSO Login via OIDC

**As an** End User, **I want** to log in using an OIDC-compliant identity provider, **so that** I can authenticate with social, enterprise, or cloud-directory identities without managing additional passwords.

**Acceptance Criteria:**
- AC1: Initiating OIDC login redirects the browser to the IdP's authorization endpoint with `response_type=code`, `scope=openid`, `state`, `nonce`, and `code_challenge` (PKCE).
- AC2: The authorization code exchange verifies the `code_verifier`; a missing or incorrect verifier returns `invalid_grant`.
- AC3: The returned ID token is validated: signature verified against IdP JWKS, `iss` matches the registered issuer, `aud` contains the client ID, `nonce` matches the stored nonce, and `exp` has not passed.
- AC4: User claims from the ID token are mapped to internal attributes per the configured OIDC claim mapping; if a required claim is absent, login fails with a descriptive error.
- AC5: If JIT provisioning is enabled and no matching local account exists, a new account is created with the configured default roles and a provisioning audit event is emitted.
- AC6: The authentication event in the audit log records the IdP alias, the OIDC subject (`sub`), and the claims received.

---

### US-014: SAML IdP Metadata Management

**As a** Tenant Admin, **I want** to configure and manage the SAML IdP metadata for my tenant's SSO integration, **so that** the federation trust is kept current without requiring platform admin intervention.

**Acceptance Criteria:**
- AC1: I can create a new SAML IdP configuration by providing a metadata URL or uploading the metadata XML directly.
- AC2: The system validates the metadata XML schema, the entity ID, the ACS URL, and the signing certificate before saving.
- AC3: I can configure the metadata refresh schedule (default 24 hours) to automatically re-fetch and validate updated metadata from the URL.
- AC4: When refreshed metadata includes a new signing certificate, the system stores both the old and new certificates during a configurable overlap window and alerts me of the pending rotation.
- AC5: The system sends an alert email and a platform notification 30 days before any configured certificate expires; a second alert is sent 7 days before expiry.
- AC6: I can run a test authentication against the IdP configuration from the admin console; the test result shows which validation steps passed or failed.
- AC7: All IdP configuration changes (create, update, enable, disable) are recorded in the audit log with my admin identity and the timestamp.

---

## Session Management Stories

### US-015: Session List and Device Review

**As an** End User, **I want** to see all my active sessions including the device and location information, **so that** I can identify and terminate any sessions I do not recognize.

**Acceptance Criteria:**
- AC1: The sessions page shows all active sessions with: device type, OS, browser, approximate city/country, last-active timestamp, authentication factors used, and session creation time.
- AC2: The current session is clearly identified.
- AC3: I can terminate any individual session other than the current one by clicking "Sign out" next to it; the session is revoked within 5 seconds.
- AC4: Terminating a session from this page emits a session-terminated audit event with my actor ID, the target session ID, and the timestamp.
- AC5: Terminated sessions disappear from the list within 10 seconds of revocation.
- AC6: A Tenant Admin can view and terminate sessions for any user in their tenant from the admin console; Platform Admins can view sessions across all tenants.

---

### US-016: Admin-Initiated Force Logout

**As a** Tenant Admin, **I want** to immediately terminate all sessions for a specific user, **so that** I can respond to a security incident or a reported compromised account.

**Acceptance Criteria:**
- AC1: From the user management page, I can click "Force logout" on any user; the action requires re-entry of my admin password as a step-up confirmation.
- AC2: All active sessions and refresh tokens for the target user are revoked within 5 seconds P95.
- AC3: A subsequent login attempt by the affected user requires full re-authentication; existing device sessions do not auto-renew.
- AC4: The force-logout event is recorded in the audit log with my admin identity, the target user ID, the count of sessions terminated, and the timestamp.
- AC5: The affected user receives an email notification that their sessions were terminated by an administrator, including the admin's display name and the time.

---

## Identity Lifecycle Stories

### US-017: User Invitation and Onboarding

**As a** Tenant Admin, **I want** to invite new users to my tenant by email, **so that** they can self-onboard with their own credentials without me having to set a temporary password.

**Acceptance Criteria:**
- AC1: I can enter one or more email addresses in the invite form, select the initial role(s), and send invitations; each invite generates an audit event.
- AC2: Each invitee receives an email with a unique invite link containing a single-use token of at least 128 bits of entropy.
- AC3: The default invite expiry is 72 hours; I can set a custom expiry between 1 hour and 30 days per invite.
- AC4: Clicking an expired invite link shows a clear expiry message and prompts the invitee to request a new invite from their administrator.
- AC5: During onboarding, the invitee sets a password meeting the tenant's password policy and, if MFA enrollment is required, is redirected to the MFA enrollment flow.
- AC6: The completed onboarding creates the user account in `active` state with the assigned roles, and emits a user-created audit event.
- AC7: I can view invite status (pending, accepted, expired) in the user management console and can re-send or revoke individual invites.

---

### US-018: User Suspension

**As a** Tenant Admin, **I want** to immediately suspend a user account, **so that** I can block access for a user under investigation without permanently deleting their data.

**Acceptance Criteria:**
- AC1: Suspending a user requires me to provide a reason code (one of: security incident, policy violation, investigation, off-boarding hold) and an optional free-text note.
- AC2: Upon suspension confirmation, all active sessions are terminated and all refresh tokens are revoked within 5 seconds.
- AC3: Any subsequent login attempt by the suspended user returns HTTP 403 with a message directing them to contact their administrator.
- AC4: The user's entitlements are frozen: they remain stored but the PDP returns `deny` for all authorization requests for the suspended user.
- AC5: The suspension event is recorded in the audit log with my admin identity, the target user ID, the reason code, the free-text note, and the timestamp.
- AC6: The user appears with a `Suspended` badge in the user management console along with the suspension timestamp and reason.

---

### US-019: User Restoration from Suspension

**As a** Tenant Admin, **I want** to restore a suspended user account, **so that** the user can resume working after an investigation is closed.

**Acceptance Criteria:**
- AC1: Restoring a user requires me to provide a restoration reason and confirm the action.
- AC2: Upon restoration, the account transitions to `active` state and login is re-enabled.
- AC3: The user's entitlements are unfrozen and the PDP resumes evaluating their authorization requests normally.
- AC4: The system validates the restored user's entitlements against the current policy state; any grants that have become invalid during suspension are flagged in a review list.
- AC5: The restoration event is recorded in the audit log with my admin identity, the target user ID, the restoration reason, and the timestamp.
- AC6: The user receives an email notification that their account has been restored.

---

### US-020: User Deprovisioning

**As a** Tenant Admin, **I want** to permanently deprovision a user when they leave the organization, **so that** all their access is removed and a verifiable record is created.

**Acceptance Criteria:**
- AC1: Initiating deprovisioning requires step-up authentication and a mandatory reason code.
- AC2: All active sessions and refresh tokens are revoked immediately upon deprovisioning initiation.
- AC3: All role assignments, group memberships, and direct permission grants are removed asynchronously; a job tracks the removal of each entitlement individually.
- AC4: A reconciliation proof is generated within 1 hour of the deprovisioning event; the proof lists every removed entitlement with its removal timestamp.
- AC5: The account transitions to `deprovisioned` state; login is blocked and the account is hidden from normal user lists but retained for the audit retention period.
- AC6: The deprovisioning event and the reconciliation proof are permanently retained in the audit log.
- AC7: I can download the reconciliation proof as a signed PDF from the user's historical record.

---

### US-021: Stale Entitlement Detection and Review

**As a** Tenant Admin, **I want** to identify and revoke role assignments that have not been used in 90 days, **so that** I can enforce the principle of least privilege.

**Acceptance Criteria:**
- AC1: The compliance dashboard shows a count of stale role assignments (unused in the last 90 days) with a drill-down to the full list.
- AC2: Each stale assignment row shows the user, the role, the last-used timestamp, and the assignment creation date.
- AC3: I can select individual stale assignments or select all and click "Revoke selected" to bulk-remove them.
- AC4: Each revocation is recorded in the audit log with my admin identity, the affected user and role, and the timestamp.
- AC5: Orphaned permissions (resource-level grants referencing non-existent resources) are shown in a separate list in the dashboard.
- AC6: An automated weekly report of new stale assignments is emailed to the tenant's security contact.

---

## Provisioning and Directory Stories

### US-022: SCIM Directory Sync Configuration

**As a** Tenant Admin, **I want** to configure automatic user provisioning from my corporate directory using SCIM 2.0, **so that** employees are automatically onboarded and deprovisioned as they join and leave the organization.

**Acceptance Criteria:**
- AC1: I can create a SCIM configuration by providing the SCIM endpoint URL, a bearer token (stored encrypted at rest), and selecting a sync schedule (every 15 minutes, 1 hour, 4 hours, or 24 hours).
- AC2: The system sends a test request (`GET /ServiceProviderConfig`) using the provided credentials and reports success or failure with the HTTP status and response summary.
- AC3: I can map SCIM attributes to internal user attributes from a configuration form; required attributes (`userName`, `emails`) are pre-mapped with warnings if absent.
- AC4: I can configure the deprovision action for users removed from the SCIM source: `suspend` or `deprovision`.
- AC5: Each sync run records start time, end time, count of users created/updated/suspended/deprovisioned, and any per-item errors in the sync history log.
- AC6: If a sync run encounters more than 10% failures in a batch, it is paused and an alert is sent to the tenant admin rather than applying partial, potentially inconsistent changes.

---

### US-023: SCIM Drift Reconciliation

**As a** Tenant Admin, **I want** the platform to automatically detect and correct drift between my corporate directory and the local IAM state, **so that** users who have left the organization do not retain access between scheduled sync cycles.

**Acceptance Criteria:**
- AC1: A drift reconciliation job runs every 15 minutes by default; the interval is configurable between 5 minutes and 24 hours.
- AC2: The reconciliation job compares each SCIM-managed user's current state in the source directory against the local IAM state.
- AC3: A user who is active locally but deprovisioned or inactive in the source directory is suspended or deprovisioned according to the configured deprovision action within one reconciliation cycle.
- AC4: Drift events (users corrected) are emitted to the audit log with the reconciliation job ID, the affected user, the detected drift type, and the corrective action taken.
- AC5: I can view a reconciliation history showing the last 100 reconciliation runs with their timing, counts, and any errors.
- AC6: A reconciliation run that fails completely (e.g., SCIM endpoint unreachable) sends an alert to the tenant admin and does not apply any changes for that cycle.

---

### US-024: JIT Provisioning via Federated Login

**As a** Tenant Admin, **I want** new users to be automatically provisioned the first time they log in via a federated IdP, **so that** I do not need to pre-create accounts or wait for SCIM sync for each new hire.

**Acceptance Criteria:**
- AC1: JIT provisioning is a configurable flag per IdP configuration; it is disabled by default and must be explicitly enabled by the tenant admin.
- AC2: When an authenticated federated identity has no matching local account and JIT provisioning is enabled, a new account is created with: `userName` from the configured claim, `email` from the configured claim, and the configured default role bootstrap.
- AC3: The JIT-provisioned account is created in `active` state; the user proceeds directly to the application after first login.
- AC4: A user-jit-provisioned audit event is emitted with the IdP alias, the federated subject, the new local account ID, the assigned default roles, and the timestamp.
- AC5: If a required claim for provisioning (e.g., `email`) is absent from the federated assertion, JIT provisioning fails and the user sees a descriptive error instructing them to contact their administrator.
- AC6: JIT-provisioned accounts are flagged in the user list for the tenant admin to review and modify the default role assignment within 7 days.

---

## Authorization and Policy Stories

### US-025: Policy Authoring and Simulation

**As a** Tenant Admin, **I want** to author access control policies and simulate their effect before activating them, **so that** I can confidently publish changes without accidentally breaking existing access.

**Acceptance Criteria:**
- AC1: I can create a new policy rule specifying subject (user, group, role, or wildcard), action (e.g., `project:write`), resource (e.g., `resource:project-123` or `resource:projects:*`), conditions (ABAC predicates), and effect (permit or deny).
- AC2: I can save the policy as a draft without activating it; drafts are not evaluated by the PDP.
- AC3: The simulation endpoint accepts a list of evaluation contexts (subject, action, resource, environment) and returns the expected decision for each, annotated with which rules would match.
- AC4: The simulation response shows a diff of changed decisions compared to the currently active policy version, clearly highlighting any regressions (previously permitted requests that would now be denied).
- AC5: Publishing a policy requires at least one policy approver to review and approve the simulation results; self-approval is not permitted.
- AC6: A published policy takes effect within 30 seconds across all PDP instances; a policy-published audit event is emitted with the policy version hash and the approver's identity.

---

### US-026: Role Assignment Management

**As a** Tenant Admin, **I want** to assign and revoke roles for users and groups, **so that** I can control what each user is permitted to do within the platform.

**Acceptance Criteria:**
- AC1: I can assign one or more roles to a user or a group from the user/group management page; the change takes effect within 30 seconds.
- AC2: I can set an expiry on a role assignment; on expiry, the role is automatically removed and a role-assignment-expired audit event is emitted.
- AC3: Revoking a role from a user or group removes the role from the user's effective permission set at next token refresh.
- AC4: Each role assignment and revocation is recorded in the audit log with the actor, target, role name, and timestamp.
- AC5: The role management page displays the full inheritance hierarchy for each role, showing which permissions are inherited from parent roles.
- AC6: Assigning a role that would create a circular inheritance dependency is rejected with a clear error message.

---

### US-027: Break-Glass Access

**As a** Platform Admin, **I want** to activate an emergency break-glass access session with dual approval, **so that** I can respond to a production incident that requires accessing a system I am not normally authorized to reach.

**Acceptance Criteria:**
- AC1: Requesting break-glass access requires: a written justification of at least 50 characters, selection of the target resource scope, and a requested duration (maximum 4 hours).
- AC2: The request is queued and two distinct platform admins (neither of whom may be the requester) must independently approve it before access is granted.
- AC3: If approval is not granted within 30 minutes, the request expires and a new request must be submitted.
- AC4: All actions taken during the break-glass session are tagged with the break-glass session ID in the audit log and flagged for post-incident review.
- AC5: The break-glass session auto-terminates at the end of the approved duration; there is no extension mechanism.
- AC6: A break-glass-activated alert is sent to the tenant's security contact and the SIEM webhook at the time of activation.
- AC7: A break-glass-session report is automatically generated at the end of the session and emailed to all approvers and the requester.

---

## Service Account and OAuth Client Stories

### US-028: Service Account Creation and Credential Management

**As a** Developer / App Owner, **I want** to create a service account for my application and manage its credentials, **so that** my application can authenticate to the IAM Platform's APIs without using a human user's credentials.

**Acceptance Criteria:**
- AC1: I can create a service account from the developer console by providing a name, description, owner email, and the minimum required permission scopes.
- AC2: Upon creation, a client ID is generated and an initial client secret is issued; the plaintext secret is displayed exactly once and is not retrievable again.
- AC3: I can rotate the client secret; a new secret is issued and both the old and new secrets are valid during a configurable overlap window (default 24 hours).
- AC4: I can suspend a service account, which immediately revokes all active tokens issued to it; suspended service accounts cannot obtain new tokens.
- AC5: I can retire a service account permanently; retirement revokes all tokens, removes all permissions, and emits a service-account-retired audit event.
- AC6: All service account lifecycle events (create, secret rotate, suspend, retire) are recorded in the audit log with my identity, the action, and the timestamp.
- AC7: The developer console shows the last 10 successful and failed authentication events for each service account to help diagnose credential issues.

---

### US-029: OAuth Client Registration

**As a** Developer / App Owner, **I want** to register my application as an OAuth 2.0 client, **so that** it can participate in authorization code flows on behalf of users.

**Acceptance Criteria:**
- AC1: I can register a client by providing: application name, redirect URIs (one or more), allowed grant types, allowed scopes, token endpoint authentication method, and a JWKS URI or public key (for `private_key_jwt` auth).
- AC2: Redirect URIs must be HTTPS (except `localhost` for development clients); registrations with non-HTTPS redirect URIs for non-development clients are rejected.
- AC3: The registration returns a `client_id`; a `client_secret` is issued for confidential clients and is displayed once and never retrievable again.
- AC4: I can update the redirect URIs, allowed scopes, and display metadata for my registered client; changes take effect immediately.
- AC5: I can delete my client registration, which immediately invalidates all tokens issued to that client.
- AC6: I can view token usage statistics for my client (daily active tokens, error rates, top scopes requested) in the developer console.

---

### US-030: Token Revocation

**As a** Developer / App Owner, **I want** to programmatically revoke access tokens and refresh tokens issued to my application, **so that** I can implement logout flows and respond to security incidents in my application.

**Acceptance Criteria:**
- AC1: My application can call the token revocation endpoint (RFC 7009) with an access token or refresh token; the endpoint returns HTTP 200 regardless of whether the token was active or already expired (to prevent token enumeration).
- AC2: Revoking a refresh token also revokes all access tokens that were issued from that refresh token family.
- AC3: A revoked token is rejected by the introspection endpoint within 5 seconds P95.
- AC4: Token revocation events are recorded in the audit log with the client ID, the token type (access/refresh), the subject of the revoked token, and the timestamp.
- AC5: My application can also call the revocation endpoint with the user's access token at user-initiated logout; the session corresponding to the access token is also terminated.

---

### US-031: IP Allowlist Configuration

**As a** Tenant Admin, **I want** to restrict authentication to specific IP address ranges, **so that** users can only log in from trusted network locations.

**Acceptance Criteria:**
- AC1: I can define an IP allowlist for my tenant as a list of CIDR ranges (IPv4 and IPv6 supported).
- AC2: I can configure the allowlist enforcement action: `block` (deny authentication from outside ranges) or `step_up_mfa` (require MFA from outside ranges).
- AC3: An authentication attempt from an IP outside the allowlist is blocked or challenged per the configured action; an allowlist-violation audit event is emitted with the source IP.
- AC4: The allowlist takes effect within 60 seconds of being saved; I can test it against a specific IP before saving using the test form.
- AC5: I can create named CIDR groups (e.g., "Corporate HQ", "VPN Range") and reference them by name in the allowlist for readability.
- AC6: Emergency bypass: a Platform Admin can temporarily disable the allowlist for a tenant for up to 4 hours (with dual approval and audit trail) to allow access during a network incident.

---

## Compliance and Audit Stories

### US-032: Audit Log Search and Export

**As a** Security Auditor, **I want** to search and export audit logs for a specific time range, user, or action type, **so that** I can investigate incidents and produce evidence for audits.

**Acceptance Criteria:**
- AC1: I can search audit events by any combination of: time range, tenant ID, actor ID, target ID, action type, decision (permit/deny/success/failure), source IP, and correlation ID.
- AC2: Search results load within 5 seconds for queries covering the 13-month hot storage window.
- AC3: I can export search results as JSON Lines, CEF, or LEEF; the export is delivered as a downloadable file or streamed to a configured SIEM endpoint.
- AC4: Exports are subject to a size limit of 1 million events per export job; larger exports are split into parts with sequential naming.
- AC5: Each exported event contains all required fields including the hash-chain link to verify integrity.
- AC6: The export action itself is recorded in the audit log with my auditor identity, the filter parameters, the record count, and the export format.

---

### US-033: Audit Log Integrity Verification

**As a** Security Auditor, **I want** to verify that audit logs have not been tampered with, **so that** I can confidently use them as evidence in compliance audits and legal proceedings.

**Acceptance Criteria:**
- AC1: I can call the integrity verification API with a time range and receive a verification result within 60 seconds for a 24-hour window.
- AC2: The verification confirms that the SHA-256 hash chain is unbroken from the first to the last event in the range.
- AC3: If the chain is broken (indicating potential tampering), the verification result identifies the approximate location (event timestamp range) of the break.
- AC4: A broken hash chain immediately triggers a critical security alert to the Platform Admin team.
- AC5: The verification API returns the first and last event IDs and hashes in the range so I can cross-reference with my archived exports.
- AC6: The verification request itself is recorded in the audit log.

---

### US-034: Legal Hold Management

**As a** Security Auditor, **I want** to place a legal hold on audit records related to a specific investigation, **so that** records are preserved beyond normal retention schedules and cannot be deleted.

**Acceptance Criteria:**
- AC1: I can create a legal hold specifying a name, justification, time range, and optionally a set of actor IDs or action types to scope it.
- AC2: Creating a legal hold requires Platform Admin authorization; I submit a request and a Platform Admin approves or rejects it.
- AC3: Once active, records covered by the legal hold cannot be deleted or archived, even if they would normally be expired by the retention policy.
- AC4: The legal hold is visible in the compliance dashboard with its scope, status (active/released), creation date, and the approver.
- AC5: Releasing a legal hold requires the same dual-authorization as creating one; records immediately return to normal retention policy processing.
- AC6: An attempt to delete a record under legal hold results in an error; the attempted deletion is itself recorded in the audit log.

---

### US-035: Access Review Campaign

**As a** Tenant Admin, **I want** to run an access review (entitlement certification) campaign, **so that** role holders and resource owners can confirm that each entitlement is still needed.

**Acceptance Criteria:**
- AC1: I can create a campaign by selecting the scope (all users, specific groups, or specific roles), assigning reviewers (managers, resource owners, or me as admin), and setting a deadline.
- AC2: Each reviewer receives an email listing the entitlements assigned to them for review, with a link to the review UI.
- AC3: Reviewers can certify (confirm the entitlement is still needed) or revoke each entitlement; they can also add a comment.
- AC4: Entitlements not reviewed by the deadline are automatically revoked if the campaign was configured with `auto_revoke_on_expiry = true`; otherwise they are marked as overdue and reported.
- AC5: The campaign dashboard shows real-time completion percentage, count of certifications, count of revocations, and count of overdue items.
- AC6: All reviewer actions (certify, revoke) are recorded in the audit log with the reviewer's identity, the reviewed entitlement, the decision, and the timestamp.
- AC7: At campaign close, I can download a signed PDF report summarizing all decisions for compliance evidence.

---

### US-036: Compliance Dashboard

**As a** Tenant Admin, **I want** a compliance dashboard that summarizes my tenant's security posture against SOC 2 and ISO 27001 controls, **so that** I can track compliance readiness and identify gaps.

**Acceptance Criteria:**
- AC1: The dashboard shows current values for key metrics: MFA enrollment percentage, count of users with admin roles, count of active break-glass sessions in the past 30 days, count of stale entitlements, days since last access review, and count of open policy changes awaiting approval.
- AC2: Each metric is mapped to the relevant SOC 2 Type II common criteria (CC6, CC7, CC8, CC9) and ISO 27001 Annex A controls; clicking a metric shows the control mapping detail.
- AC3: The dashboard highlights controls that are failing a defined threshold (e.g., MFA enrollment < 95%, stale entitlements > 0) with a red indicator.
- AC4: I can export the current compliance snapshot as a PDF or JSON for use in audit evidence packages.
- AC5: Historical compliance snapshots are retained for 13 months, allowing trend reporting.

---

### US-037: GDPR Data Subject Access Request

**As a** Platform Admin, **I want** to generate and deliver a complete data subject access request (DSAR) package for a given user, **so that** the organization meets its GDPR obligations within the 72-hour response SLA.

**Acceptance Criteria:**
- AC1: I can initiate a DSAR from the admin console by entering the subject's verified email address; the request is logged with a ticket ID.
- AC2: The DSAR compilation job collects: profile attributes (name, email, phone, department), authentication history (timestamps, source IPs, MFA factors used), entitlement history (roles granted and revoked with dates), and audit log references (all events where the subject was the actor or target).
- AC3: The DSAR package is delivered as a signed, encrypted ZIP archive to the designated data protection officer email within 72 hours.
- AC4: PII in the DSAR is pseudonymized in the exported audit log records to prevent exposure of other individuals' data (only the subject's own PII is included in full).
- AC5: The DSAR request and delivery are permanently recorded in the compliance log.
- AC6: For erasure requests, the platform pseudonymizes the subject's PII in mutable data stores while retaining required audit records in pseudonymized form; a confirmation report is generated.

---

## Security Operations Stories

### US-038: Federation Certificate Expiry Alerting

**As a** Tenant Admin, **I want** to receive advance warnings when my SAML or OIDC federation certificates are about to expire, **so that** I can renew them before they cause authentication failures for my users.

**Acceptance Criteria:**
- AC1: An alert email and platform notification are sent to the tenant admin 30 days before any configured federation certificate expires.
- AC2: A second alert is sent 7 days before expiry; a final alert is sent on the day of expiry.
- AC3: The platform notification includes the IdP alias, the certificate subject, the expiry date, and a link to the IdP configuration page.
- AC4: If the certificate expires without being renewed, the affected IdP configuration is automatically disabled and a critical audit event is emitted; users of that IdP cannot log in.
- AC5: After uploading a renewed certificate, I can re-enable the IdP configuration; the test-authentication flow verifies the new certificate before re-enablement.
- AC6: The compliance dashboard shows a certificate expiry calendar listing all federation certificates and their expiry dates.

---

### US-039: Service Account Credential Rotation

**As a** Developer / App Owner, **I want** to rotate my service account's client secret with a zero-downtime transition period, **so that** I can maintain least-privilege hygiene without causing an application outage.

**Acceptance Criteria:**
- AC1: I can initiate a credential rotation from the developer console; a new client secret is generated and displayed exactly once.
- AC2: Both the old and new client secrets are valid for a configurable overlap window (default 24 hours, maximum 7 days).
- AC3: I can manually close the overlap window once I have confirmed that all deployment instances have been updated to the new secret.
- AC4: At the end of the overlap window, the old secret is automatically invalidated; any requests using it return `invalid_client`.
- AC5: A credential-rotated audit event is emitted at rotation initiation and at old-credential-invalidation, including the service account ID, the actor, and the timestamps.
- AC6: The developer console shows a countdown indicating how much time remains in the overlap window.

---

### US-040: Anomaly Alert Investigation

**As a** Security Auditor, **I want** to investigate an anomaly alert by viewing the complete authentication and authorization chain for a specific user session, **so that** I can determine whether the alert represents a genuine threat.

**Acceptance Criteria:**
- AC1: From the security alerts page, I can click on an anomaly alert to open the investigation view for the associated session or user.
- AC2: The investigation view shows the full authentication chain: login attempt timestamp, source IP, device fingerprint, risk score and contributing signals, MFA challenge outcome, and token issuance details.
- AC3: From the same view, I can see all authorization decisions made during the session, with the policy rule matched, the decision, and any obligations applied.
- AC4: I can drill into any individual authentication or authorization event to see the full raw audit event payload.
- AC5: I can take remediation actions directly from the investigation view: suspend the account, terminate the session, or clear the alert with a justification note.
- AC6: Any remediation action taken from the investigation view is immediately recorded in the audit log, with the alert ID as a correlation reference.

