# Access and Permissions — Edge Cases

## Introduction

The access and permissions subsystem governs who can read, write, publish, and manage content across all workspaces. It encompasses role-based access control (RBAC), SAML 2.0 SSO via identity providers (IdPs), JWT-based session management stored in Redis, guest link generation, workspace member management, and public knowledge base article exposure. Because this subsystem sits between every user request and every piece of content, its failures have an outsized impact on both security and user experience.

Permission failures are particularly insidious because they are often silent: a user who silently gains access they should not have may not know they have it; a user who silently loses access they should have may be blocked at a critical moment. The eight edge cases below cover the full range of access failure modes: logical loops in permission inheritance, SSO dependency failures, timing race conditions, privilege escalation, session hygiene, content exposure, enumeration bypasses, and token replay attacks.

---

## EC-ACCESS-001: Permission Inheritance Loop

### Failure Mode
The platform supports nested article collections (folders) where permissions can be inherited from parent collections. A Workspace Admin creates Collection A and sets it as a child of Collection B. Another admin then sets Collection B as a child of Collection A, creating a circular parent-child relationship. When the `PermissionService.resolveEffectivePermissions()` method traverses the inheritance chain for a user's request, it enters an infinite loop: A inherits from B which inherits from A, recursing until the Node.js call stack overflows with `RangeError: Maximum call stack size exceeded`.

### Impact
**Severity: High**
- All permission checks for articles in Collection A or B fail with a 500 Internal Server Error.
- Users cannot read, write, or manage any article in the affected collections.
- If the affected collections are large (thousands of articles), a significant portion of the workspace becomes inaccessible.
- The ECS task handling the request is not killed (it returns 500), but the call stack overflow may corrupt in-flight state.

### Detection
- **API Error Spike**: CloudWatch alarm on `5XXError` rate spike for `GET /api/articles/:id` requests.
- **Sentry Error**: `RangeError: Maximum call stack size exceeded` in `PermissionService.resolveEffectivePermissions` captured in Sentry.
- **Circular Reference Detection**: A nightly PostgreSQL recursive CTE query detects cycles in the `collection_parents` table.
- **Admin Activity Log**: Two admin actions creating a circular parent-child relationship within a short time window are flagged in the audit log.

### Mitigation/Recovery
1. Add a visited-node set to `PermissionService.resolveEffectivePermissions()` immediately — abort traversal and return a `PERMISSION_LOOP_DETECTED` error if a collection ID is visited twice.
2. Deploy the fix. The immediate fix is surgical and can be deployed without a maintenance window.
3. Identify the circular collection pair using the PostgreSQL CTE query and notify the Workspace Admin.
4. Provide an admin UI action to "break" the circular reference by removing the secondary parent assignment.
5. Until the admin resolves the circular reference, serve the articles in the affected collections using only direct (non-inherited) permissions.

### Prevention
- Validate all parent-child collection assignments at write time: before saving a new `collection_parents` record, run a cycle-detection query using a recursive CTE and reject the assignment if a cycle would be created. Return a clear error: "This assignment would create a circular inheritance loop."
- Add a PostgreSQL constraint that enforces a maximum collection nesting depth of 10.
- Write an automated test that creates a 3-deep circular collection reference and asserts the API returns a proper error (not a 500) and that `resolveEffectivePermissions` terminates in finite time.

---

## EC-ACCESS-002: SSO Provider Outage

### Failure Mode
The workspace is configured to use SAML 2.0 SSO with an enterprise IdP (Okta, Azure AD, Google Workspace). The IdP's SAML endpoint becomes unavailable due to an infrastructure outage on the IdP's side. Internal users who attempt to log in are redirected to the IdP's login page, which returns a 503 or a timeout. They cannot complete the SAML handshake and are locked out of the platform. Because all internal users are configured with SSO-only login (no local password), they have no fallback authentication method.

### Impact
**Severity: Critical**
- All SSO-only internal users cannot log in for the duration of the outage.
- If users are not already logged in (active session), they are fully locked out.
- Engineering teams cannot access internal runbooks, further complicating incident response during the outage.
- Customer support teams cannot access the knowledge base they use to resolve customer issues.

### Detection
- **SAML ACS Endpoint Monitor**: Synthetic monitoring pings the IdP's SAML metadata URL (`/saml/metadata`) every 60 seconds. Alert if it returns non-200.
- **Login Failure Spike**: CloudWatch alarm on `auth.saml_login_failures` > 10 per minute.
- **IdP Status Webhook**: Subscribe to the IdP's status page for notifications.
- **Active Session Coverage**: Track the ratio of users with active sessions vs. those attempting to log in. A spike in failed login attempts without corresponding session creations is an SSO outage signal.

### Mitigation/Recovery
1. Activate the emergency local login bypass: for a configurable list of break-glass accounts (engineering leads, security team), enable local password authentication as a temporary override.
2. Communicate to users via Slack/email: "SSO is currently experiencing issues. We are monitoring the situation. Use previously established sessions where possible."
3. Extend active JWT session TTLs from 8 hours to 24 hours in Redis to keep currently logged-in users active during the outage.
4. If the SSO outage is confirmed to be long-term (>4 hours), activate a temporary local password reset flow for all affected users, notifying them via email with a one-time recovery link.
5. When SSO is restored, invalidate all temporary local sessions and require users to re-authenticate via SSO.

### Prevention
- Maintain at least 2 break-glass admin accounts per workspace with local password authentication as a backup login method.
- Configure the SAML flow with a session persistence setting: if the IdP is unreachable during token refresh, extend the existing session for up to 24 hours rather than forcing immediate re-authentication.
- Evaluate configuring a secondary IdP (e.g., Google as backup for Okta) that users can switch to during an outage.
- Document the SSO outage runbook and ensure it is accessible outside the platform (e.g., in a public or separately hosted recovery page).

---

## EC-ACCESS-003: Guest Link Expiry Race Condition

### Failure Mode
An external user (guest) receives a time-limited share link for a private article (e.g., valid for 7 days). The link contains a signed JWT with an expiry timestamp. The guest clicks the link at the exact moment the token expires — their browser sends the HTTP request with the token, the NestJS `GuestAuthGuard` validates the token, and a race condition occurs: the token was valid when the request was received at the load balancer but expired by the time the JWT validation middleware runs (due to clock skew between the client, load balancer, and API server). The user's browser receives a partially loaded page with an authentication error overlay on top of the article content, creating a confusing hybrid state.

### Impact
**Severity: Low**
- The guest user sees a broken page — article content may have partially rendered before the auth error appeared, depending on where the token check occurs in the rendering pipeline.
- The user cannot refresh and recover automatically without requesting a new link.
- The experience is confusing: the user saw content briefly and now cannot access it.

### Detection
- **Frontend Error Tracking**: Sentry captures `GuestAuthError` on page load when an article is partially rendered.
- **Timing Pattern Analysis**: Analyze guest link validation failures where the token `exp` claim is within 30 seconds of the validation timestamp — these are race condition candidates.
- **User Feedback**: Guest users reporting "I saw the article for a second then got an error" indicate this pattern.

### Mitigation/Recovery
1. Add a 60-second grace period to guest token validation: accept tokens that expired up to 60 seconds ago. This is safe because the link was already distributed and the 60-second window does not materially change the security posture.
2. If the user hits the expired link, display a clear, friendly message with the exact expiry time and a link to request a new share link from the article author.
3. For server-side rendered pages, perform the auth check before rendering any article content to prevent the partial render + error state.

### Prevention
- Implement a 60-second clock skew tolerance in `GuestAuthGuard` as the default behavior.
- Add clock skew compensation: use NTP-synchronized server time and include a `clock_skew_tolerance_seconds` field in the JWT validation configuration.
- Display the link expiry countdown in the article header for guest users so they are aware of the impending expiry.
- Implement link refresh: 1 hour before expiry, if the guest is actively viewing the article, automatically extend the link expiry by 24 hours (subject to the author's max extension policy).

---

## EC-ACCESS-004: Role Escalation Attack

### Failure Mode
A regular user (Reader role) discovers that the `PATCH /api/workspaces/:id/members/:userId` endpoint accepts a `role` parameter in the request body and does not properly validate that the requesting user has the authority to assign the requested role. By sending `{"role": "WORKSPACE_ADMIN"}` directly to the API, the attacker upgrades their own role to Workspace Admin without authorization. This gives them full read/write/delete access to all articles, settings, and member management in the workspace.

### Impact
**Severity: Critical**
- Full workspace takeover by an unauthorized user.
- The attacker can read all private articles, delete content, modify permissions for other users, exfiltrate data, and lock out legitimate admins.
- Under GDPR and enterprise contracts, this constitutes a data breach.
- Damage may be irreversible if the attacker deletes content before detection.

### Detection
- **Role Change Audit Log**: Every role assignment must be logged in the `audit_logs` table with the actor's user ID, the target user ID, the previous role, and the new role. Alert when a user assigns themselves a higher role.
- **Anomalous Role Assignments**: Alert when a non-admin user's role is elevated to Admin or Owner without the action being initiated by an existing Admin.
- **API Authorization Metrics**: Track `auth.role_assignment_denied` vs `auth.role_assignment_allowed`. An unusual spike in successful role assignments warrants investigation.
- **Sentry**: Log every role change event with actor role context. Flag any case where actor role < target role.

### Mitigation/Recovery
1. Immediately revoke the escalated role: set the user's role back to their previous role.
2. Invalidate all active JWT tokens for the affected user by deleting their session records from Redis.
3. Review the audit log for all actions taken by the user during the period of elevated access.
4. Assess and remediate any data that was accessed, modified, or deleted.
5. Fix the API authorization check immediately and deploy as an emergency hotfix.

### Prevention
- Implement strict server-side authorization in the `MemberController`: only a user with `WORKSPACE_ADMIN` or `OWNER` role may call the role assignment endpoint. Validate this using a NestJS `@Roles()` guard, not client-supplied data.
- Enforce the invariant: no user may assign a role equal to or higher than their own role. An `ADMIN` cannot create another `OWNER`.
- Write penetration test cases for horizontal and vertical privilege escalation on all member management endpoints.
- Apply the principle of least privilege across all API endpoints: every endpoint must declare its minimum required role and the NestJS guard must enforce it before any business logic executes.

---

## EC-ACCESS-005: Orphaned Permissions After Member Removal

### Failure Mode
A workspace admin removes a user from the workspace via `DELETE /api/workspaces/:id/members/:userId`. The `MemberService.removeMember()` method deletes the user's workspace membership record. However, the user has an active JWT token in Redis with a 24-hour TTL. The JWT has not expired. The user's browser still holds this token and continues to make API requests. The API's `AuthGuard` validates the JWT signature as valid (the token is cryptographically intact) and does not check for workspace membership revocation against the database. The user continues to read and write articles in the workspace they were removed from.

### Impact
**Severity: High**
- A removed user retains unauthorized access for up to 24 hours.
- For termination scenarios (employee offboarding, contractor completion), this is a security and compliance failure.
- Sensitive articles published during the access window may be read or leaked by the former member.

### Detection
- **Token Revocation Check**: Implement a Redis-based token revocation list. When a user is removed, add their `userId` to a `revoked_users` Redis set. On every API request, the `AuthGuard` must check this set.
- **Membership Validation on Request**: On every authenticated API request, perform a lightweight Redis-cached check of whether the user's workspace membership is still active. Cache the membership status for 60 seconds to avoid per-request DB queries.
- **Access After Removal Alert**: Log a `REMOVED_USER_ACCESS_ATTEMPT` event if a user whose membership was deleted makes an API request. Alert immediately.

### Mitigation/Recovery
1. Immediately add the removed user's `userId` and all their active `jti` (JWT IDs) to the Redis revocation set.
2. Invalidate all of the user's active sessions in Redis by deleting their session keys: `DEL session:{userId}:*`.
3. Audit all API requests made by the user after the membership deletion timestamp.
4. If sensitive articles were accessed post-removal, notify the workspace admin and conduct a data access review.

### Prevention
- Implement a token revocation mechanism: store `jti` claims in Redis and remove them on logout and on membership revocation. The `AuthGuard` must check the revocation list on every request.
- Reduce JWT TTL from 24 hours to 1 hour, with a silent refresh token mechanism (stored in Redis). This limits the maximum exposure window to 1 hour.
- Add a database membership validation step on each API request, cached in Redis with a 60-second TTL (stale-while-revalidate). This bounds the exposure window to 60 seconds even without full token revocation.
- Add membership revocation as a step in the HR system's offboarding automation workflow.

---

## EC-ACCESS-006: Public KB Accidental Private Content Exposure

### Failure Mode
An article in a public knowledge base is marked as public and accessible to unauthenticated readers. The article body contains TipTap attachment nodes referencing files uploaded to S3. While the article's public visibility is correctly enforced, the S3 attachment URLs served via CloudFront are pre-signed URLs with a 7-day expiry. When these pre-signed URLs are included in the publicly visible article, any unauthenticated user who reads the article (or anyone they share it with) can access the attachments directly via the pre-signed URL without any access check — even if the attachments were originally uploaded for internal use and are classified as private.

### Impact
**Severity: High**
- Private attachments embedded in public articles are accessible to anyone with the URL for 7 days.
- Internal documents (spreadsheets, PDFs, diagrams) can be downloaded by external users.
- The author who embedded the attachment may not have been aware that making the article public would expose the attachment.
- Under GDPR, exposing personal data in attachments to unauthorized parties is a data breach.

### Detection
- **Attachment Visibility Mismatch**: On every article publish with public visibility, check all attachment references in the article body. If any attachment has `visibility = 'private'`, flag as `VISIBILITY_MISMATCH`.
- **Public Article Attachment Scan**: Nightly job scans all public articles for attachment references and audits their visibility settings.
- **Sentry Alert**: `AttachmentVisibilityConflict` event created when the publish-time check detects a mismatch.

### Mitigation/Recovery
1. At publish time, display a warning to the author: "This article contains private attachments. Publishing will make these attachments accessible to anyone who reads the article. Change attachments to Public or remove them before publishing."
2. For already-published articles with exposed attachments, immediately revoke the current pre-signed URLs by rotating the S3 object's presigning key, rendering all outstanding URLs invalid.
3. Notify the article author and workspace admin of the exposure, including the attachment names and the date range of exposure.
4. Conduct a data inventory to determine if the exposed attachments contained PII or confidential information and follow breach notification procedures if required.

### Prevention
- Implement an attachment visibility model: attachments inherit the visibility of the article they are first attached to. When an article's visibility changes from private to public, all its attachments are auto-promoted to public (with author confirmation) or must be manually reviewed.
- Add a publish-time validation gate that blocks publishing if any attachment's visibility is lower than the article's visibility.
- For public articles, serve attachment files through the NestJS API as a proxy (which enforces visibility checks) rather than via direct pre-signed S3 URLs.

---

## EC-ACCESS-007: Domain Allowlist Bypass

### Failure Mode
A workspace admin configures a domain allowlist to restrict workspace registration to `company.com` email addresses. The validation logic checks whether the user's email ends with `@company.com`. An attacker registers with an email address at a subdomain: `attacker@trusted.company.com` or `attacker@company.com.evil.com`. If the validation is implemented as a simple `email.endsWith('@company.com')` string check (rather than proper domain parsing), both bypass attempts succeed. The attacker gains access to the workspace.

### Impact
**Severity: High**
- Unauthorized external user gains access to a workspace with potentially sensitive internal knowledge.
- The domain allowlist, which the workspace admin relies on as a security control, is ineffective.
- Depending on the workspace's article visibility settings, the attacker may access confidential product documentation, internal processes, or customer data.

### Detection
- **Registration Domain Audit**: Log the email domain (not full email) for every new workspace member. Flag registrations where the domain is not an exact match for the allowlisted domain (only subdomains or suffixes match).
- **Anomalous Email Pattern**: Alert on new user registrations where the email domain contains the allowlisted domain as a non-final component (e.g., `example.company.com` where `company.com` is allowlisted but `example.company.com` is not).
- **Admin Review Queue**: New member registrations via self-service invite links should be queued for admin review in high-security workspaces.

### Mitigation/Recovery
1. Immediately remove the bypassed user from the workspace and revoke their session.
2. Audit all articles accessed by the attacker during their access window.
3. Fix the domain validation logic to use proper domain parsing: extract the domain portion of the email using a proper URL/email parser and compare it against the exact allowlist entries using `===` comparison, not `endsWith` or `includes`.
4. Notify the workspace admin of the bypass and the corrected user count.

### Prevention
- Use a proper email parsing library (e.g., `email-addresses` npm package) to extract the domain portion. Compare `parsedDomain === allowlistedDomain` exactly.
- Support both exact domain matching (`company.com`) and explicit subdomain allowlisting (`*.company.com` — only if explicitly configured).
- Write security tests that attempt to bypass the domain allowlist with subdomain and suffix attacks, asserting all are rejected.
- Require email verification for new registrations: send a verification link to the registered email to confirm it is under the user's control.

---

## EC-ACCESS-008: JWT Token Replay After Logout

### Failure Mode
A user logs out of the platform. The NestJS `AuthService.logout()` method invalidates the frontend's access token by clearing the cookie. However, the JWT itself is stateless — it does not expire until its `exp` claim. An attacker who intercepted the JWT (e.g., via XSS, man-in-the-middle on an insecure network, or a compromised browser extension) can continue to make authenticated API requests with the captured token for the remainder of its TTL (up to 24 hours). The API's `AuthGuard` validates the signature and expiry, finds both valid, and serves the request — unaware that the user has logged out.

### Impact
**Severity: High**
- An attacker can impersonate a logged-out user for up to 24 hours.
- If the token was captured from an admin user before they logged out, the attacker has admin-level access.
- Standard logout provides a false sense of security — users believe they are logged out but their token remains valid.
- In shared computer environments (libraries, kiosks), this is a significant risk.

### Detection
- **Token Revocation List**: If a `jti`-based revocation list is maintained in Redis, all replay attempts return 401 and are logged as `REVOKED_TOKEN_REPLAY_ATTEMPT`.
- **Concurrent Session Anomaly**: Alert if the same `jti` is used from two different IP addresses simultaneously (indicates a replayed token).
- **Geographic Anomaly**: Alert if a token is used from a geographic location that is inconsistent with the user's previous activity (e.g., used from Europe then from Asia within 30 minutes).

### Mitigation/Recovery
1. If a token replay is detected, immediately add the token's `jti` to the Redis revocation list and all future requests with that `jti` will be rejected.
2. Force-revoke all active sessions for the affected user by deleting all `session:{userId}:*` keys from Redis.
3. Notify the user of the suspicious activity via email.
4. If the compromised token belonged to an admin, audit all API calls made with the replayed token.

### Prevention
- Implement a server-side session registry: store all active `jti` values in Redis. On every authenticated API request, check that the `jti` is in the active sessions set. On logout, remove the `jti`.
- Reduce JWT access token TTL to 15 minutes. Use a long-lived refresh token (stored as an `HttpOnly` cookie with `SameSite=Strict`) to silently obtain new access tokens. This limits the replay window to 15 minutes.
- Use `HttpOnly`, `Secure`, and `SameSite=Strict` attributes on all token cookies to minimize token theft vectors.
- Implement HSTS (HTTP Strict Transport Security) to prevent downgrade attacks that could expose tokens.

---

## Summary Table

| ID             | Edge Case                                  | Severity | Primary Owner         | Status   |
|----------------|--------------------------------------------|----------|-----------------------|----------|
| EC-ACCESS-001  | Permission Inheritance Loop                | High     | Backend               | Open     |
| EC-ACCESS-002  | SSO Provider Outage                        | Critical | Infrastructure / Auth | Open     |
| EC-ACCESS-003  | Guest Link Expiry Race Condition           | Low      | Backend               | Open     |
| EC-ACCESS-004  | Role Escalation Attack                     | Critical | Security / Backend    | Open     |
| EC-ACCESS-005  | Orphaned Permissions After Member Removal  | High     | Backend / Security    | Open     |
| EC-ACCESS-006  | Public KB Private Content Exposure         | High     | Backend / Storage     | Open     |
| EC-ACCESS-007  | Domain Allowlist Bypass                    | High     | Backend / Security    | Open     |
| EC-ACCESS-008  | JWT Token Replay After Logout              | High     | Security / Backend    | Open     |

---

## Operational Policy Addendum

### 1. Role Assignment Policy

Role assignments (including self-service invitations) are audited events. All role changes must be recorded in the `audit_logs` table with the actor, target, previous role, new role, and timestamp. The audit log is immutable for standard users and workspace admins; only the Security team may view (not modify) audit log entries. Automated alerts must fire for any role elevation above the current user's own role. The principle of least privilege must be applied: new users are assigned the minimum required role (Reader by default).

### 2. Session Management Policy

JWT access tokens must have a maximum TTL of 15 minutes in production. Refresh tokens must be stored as `HttpOnly`, `Secure`, `SameSite=Strict` cookies. All active session JTIs must be stored in Redis. Logout must immediately remove the user's session from Redis. Users may view their active sessions (device, IP, last used) and remotely revoke any session from the Security Settings page. Sessions inactive for more than 8 hours must be automatically invalidated.

### 3. Member Offboarding Policy

When a workspace member is removed (either by an admin or by the user leaving the workspace), all of their active sessions must be invalidated within 60 seconds using the Redis revocation mechanism. The offboarding checklist must include: session invalidation, article ownership transfer (assign their articles to another author), and notification of workspace admin. For employee offboardings, the HR system integration must trigger workspace removal automatically on the user's last day.

### 4. Guest Access Policy

Guest links must have a maximum TTL of 30 days. Guest links must never grant write or admin access — only read access to the specific article or collection they were generated for. Guest access logs (which articles were accessed, when, from which IP) must be retained for 30 days. Workspace admins may view all active guest links and revoke them individually. When an article's visibility changes from public/shared to private, all outstanding guest links for that article must be automatically invalidated.
