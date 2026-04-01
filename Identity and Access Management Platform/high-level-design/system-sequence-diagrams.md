# IAM Platform — System Sequence Diagrams

## 1. Password Authentication + MFA (TOTP)

This sequence covers the full interactive login flow for a user who has TOTP enrolled as their second factor. Timing annotations indicate cumulative latency budgets at each major step.

```mermaid
sequenceDiagram
    autonumber
    participant User as User
    participant Browser as Browser
    participant APIGW as API Gateway
    participant AuthSvc as Auth Service
    participant UserStore as User Store (PostgreSQL)
    participant RiskEng as Risk Engine
    participant MFASvc as MFA Service
    participant SessMgr as Session Manager
    participant TokenSvc as Token Service
    participant AuditSvc as Audit Service

    note over Browser,APIGW: TLS 1.3 — all traffic encrypted in transit
    note over AuthSvc,TokenSvc: mTLS — all internal service calls mutually authenticated

    %% ── Step 1: Submit credentials ──────────────────────────────────────────
    User->>Browser: Enter email + password
    Browser->>APIGW: POST /auth/login<br/>{email, password, device_fingerprint}<br/>Content-Type: application/json
    note right of APIGW: t=0 ms — request received

    APIGW->>APIGW: Validate Content-Type, payload size < 4 KB<br/>Rate-limit check: 5 req/min per IP sliding window<br/>WAF rule evaluation

    alt Rate limit exceeded
        APIGW-->>Browser: HTTP 429 Too Many Requests<br/>Retry-After: 60
    end

    APIGW->>AuthSvc: Forward request (mTLS)<br/>X-Forwarded-For, X-Request-ID, X-Tenant-ID headers

    %% ── Step 2: Fetch user record ─────────────────────────────────────────
    AuthSvc->>UserStore: SELECT id, password_hash, status, failed_login_count,<br/>locked_until, mfa_policy<br/>FROM users WHERE tenant_id=$1 AND normalized_email=$2<br/>[Read replica]
    note right of UserStore: t=5 ms — DB read replica query

    alt User not found
        UserStore-->>AuthSvc: 0 rows
        AuthSvc->>AuditSvc: Emit LoginFailed{reason: USER_NOT_FOUND, email_hash, ip}
        AuthSvc-->>APIGW: 401 Unauthorized {error: invalid_credentials}
        APIGW-->>Browser: HTTP 401 — generic error (no user existence leak)
    end

    UserStore-->>AuthSvc: User record {id, password_hash, status, ...}

    %% ── Step 3: Account status check ────────────────────────────────────
    AuthSvc->>AuthSvc: Check user.status<br/>ACTIVE → continue<br/>SUSPENDED → fail<br/>LOCKED and locked_until > now() → fail

    alt Account suspended or locked
        AuthSvc->>AuditSvc: Emit LoginFailed{reason: ACCOUNT_NOT_ACTIVE, userId, ip}
        AuthSvc-->>APIGW: 401 Unauthorized {error: account_disabled}
        APIGW-->>Browser: HTTP 401
    end

    %% ── Step 4: Verify password ──────────────────────────────────────────
    note right of AuthSvc: t=10 ms — bcrypt cost=12 begins (~70 ms CPU)
    AuthSvc->>AuthSvc: bcrypt.CompareHashAndPassword(storedHash, providedPassword)
    note right of AuthSvc: t=80 ms — bcrypt comparison complete

    alt Password mismatch
        AuthSvc->>UserStore: UPDATE users SET failed_login_count = failed_login_count + 1<br/>WHERE id = $1
        AuthSvc->>UserStore: Check: if failed_login_count >= 10 THEN<br/>UPDATE locked_until = now() + interval '30 minutes'
        AuthSvc->>AuditSvc: Emit LoginFailed{reason: BAD_CREDENTIALS, userId, ip, attempt_count}
        AuthSvc-->>APIGW: 401 Unauthorized {error: invalid_credentials}
        APIGW-->>Browser: HTTP 401 (same message regardless of reason)
    end

    AuthSvc->>UserStore: UPDATE users SET failed_login_count = 0 WHERE id = $1

    %% ── Step 5: Risk scoring ─────────────────────────────────────────────
    note right of RiskEng: t=82 ms — parallel risk evaluation
    AuthSvc->>RiskEng: EvaluateRisk{userId, ip, userAgent, deviceFingerprint,<br/>geo, loginHistory}
    RiskEng->>RiskEng: Score: IP reputation (0.0–0.4)<br/>+ Device familiarity (0.0–0.3)<br/>+ Velocity (0.0–0.3)<br/>= composite score (0.0–1.0)
    RiskEng-->>AuthSvc: RiskScore{score: 0.72, signals: ["new_device","unusual_geo"]}
    note right of AuthSvc: t=95 ms — risk score received

    %% ── Step 6: MFA challenge ────────────────────────────────────────────
    note over AuthSvc,MFASvc: MFA required: score > 0.5 OR tenant mfa_policy = ALWAYS
    AuthSvc->>MFASvc: CreateChallenge{userId, tenantId, preferredFactor: TOTP}
    MFASvc->>UserStore: SELECT * FROM mfa_devices<br/>WHERE user_id=$1 AND type='TOTP' AND verified=true
    UserStore-->>MFASvc: MFA device record {id, encrypted_secret, ...}
    MFASvc->>MFASvc: Generate challenge_id (UUID v4)<br/>Store nonce SETNX challenge:{id} userId EX 300<br/>(anti-replay: nonce valid for 5 min)
    MFASvc-->>AuthSvc: Challenge{challengeId, factor: TOTP, expiresAt}
    AuthSvc-->>APIGW: HTTP 200 {mfa_required: true, challenge_id, factor: TOTP}
    APIGW-->>Browser: HTTP 200 — MFA prompt
    note right of Browser: t=110 ms — MFA challenge delivered to browser

    %% ── Step 7: TOTP submission ──────────────────────────────────────────
    User->>Browser: Enter 6-digit TOTP code
    Browser->>APIGW: POST /auth/mfa/verify<br/>{challenge_id, code: "482 193"}<br/>Content-Type: application/json
    APIGW->>AuthSvc: Forward MFA verification request

    %% ── Step 8: TOTP validation ──────────────────────────────────────────
    AuthSvc->>MFASvc: VerifyTOTP{challengeId, code}
    MFASvc->>MFASvc: Resolve nonce from Redis: GET challenge:{challengeId}<br/>Check nonce not previously consumed
    MFASvc->>UserStore: Fetch encrypted TOTP seed for device
    MFASvc->>MFASvc: Decrypt seed via Vault Transit<br/>TOTP.Verify(seed, code, time.Now(), window=1)<br/>Algorithm: HMAC-SHA1, step=30s, digits=6<br/>Accepts T-1, T, T+1 (clock skew tolerance)<br/>Delete nonce from Redis (SETNX consumed)
    MFASvc->>UserStore: UPDATE mfa_devices SET last_used_at = now() WHERE id=$1

    alt TOTP code invalid or expired
        MFASvc-->>AuthSvc: VerifyFailed{reason: INVALID_CODE}
        AuthSvc->>AuditSvc: Emit MFAFailed{userId, deviceId, ip}
        AuthSvc-->>APIGW: 401 Unauthorized {error: mfa_failed}
        APIGW-->>Browser: HTTP 401
    end

    MFASvc-->>AuthSvc: VerifySuccess{assuranceLevel: AAL2}
    note right of AuthSvc: t=130 ms — MFA verified, AAL2 assurance confirmed

    %% ── Step 9: Session creation ─────────────────────────────────────────
    AuthSvc->>SessMgr: CreateSession{userId, tenantId, assuranceLevel: AAL2,<br/>ip, userAgent, absoluteExpiry: +8h, idleExpiry: +30min}
    SessMgr->>SessMgr: Generate session_id (UUID v4, 128-bit random)<br/>Compute absolute_expires_at, idle_expires_at
    SessMgr-->>SessMgr: HSET session:{sessionId}<br/>userId, tenantId, assuranceLevel, ip, ua,<br/>absolute_expires_at, idle_expires_at<br/>EXPIRE session:{sessionId} 28800 (8 h)
    SessMgr-->>AuthSvc: SessionCreated{sessionId, expiresAt}
    note right of SessMgr: t=135 ms — session persisted in Redis

    %% ── Step 10: Token issuance ──────────────────────────────────────────
    AuthSvc->>TokenSvc: IssueTokens{userId, tenantId, sessionId,<br/>scopes: ["openid","profile","email"],<br/>assuranceLevel: AAL2}
    TokenSvc->>TokenSvc: Build JWT claims:<br/>iss, sub, aud, exp (now+900s), iat, jti (UUID),<br/>tid (tenantId), sid (sessionId), aal, scope
    TokenSvc-->>TokenSvc: POST /v1/transit/sign/iam-jwt<br/>payload: base64(header.claims)<br/>algorithm: RS256 (key: iam-jwt-2024Q4)
    note right of TokenSvc: Vault Transit — private key never leaves Vault
    TokenSvc-->>TokenSvc: JWT = header.claims.signature

    TokenSvc->>TokenSvc: Generate refresh_token (256-bit random, opaque)<br/>family_id = UUID v4 (new login = new family)<br/>generation_number = 1
    TokenSvc->>UserStore: INSERT INTO refresh_tokens<br/>(id, hash, family_id, generation, user_id,<br/>session_id, tenant_id, expires_at)<br/>VALUES (...)
    TokenSvc->>SessMgr: Link token family to session<br/>HSET session:{sessionId} token_family_id={familyId}
    TokenSvc-->>AuthSvc: Tokens{accessToken, refreshToken, expiresIn: 900}
    note right of TokenSvc: t=155 ms — tokens issued and persisted

    %% ── Step 11: Audit event ─────────────────────────────────────────────
    AuthSvc->>AuditSvc: Emit LoginSucceeded{<br/>userId, tenantId, sessionId,<br/>jti: JWT.jti, familyId,<br/>ip, userAgent, assuranceLevel: AAL2,<br/>mfaFactor: TOTP, riskScore: 0.72,<br/>timestamp: now()}
    AuditSvc->>AuditSvc: Serialise to Avro schema v2<br/>Compute HMAC-SHA256 signature (Vault-managed key)<br/>Publish to iam.audit Kafka topic (acks=all)
    note right of AuditSvc: t=160 ms — audit event published (async, non-blocking)

    %% ── Step 12: Response ───────────────────────────────────────────────
    AuthSvc-->>APIGW: HTTP 200 {<br/>access_token: "eyJ...",<br/>token_type: "Bearer",<br/>expires_in: 900,<br/>scope: "openid profile email"}
    APIGW-->>Browser: HTTP 200<br/>Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=86400<br/>Body: {access_token, token_type, expires_in, scope}
    Browser->>User: Authenticated — redirect to application
    note right of Browser: t=165 ms — total end-to-end latency (p50 target: 165 ms, p99 target: 350 ms)
```

---

## 2. SAML SSO Login Flow

This sequence covers the full browser-based SAML 2.0 SSO flow from initial resource access through to session establishment. The Service Provider is the IAM Platform acting on behalf of a tenant application.

```mermaid
sequenceDiagram
    autonumber
    participant User as User
    participant Browser as Browser
    participant SPApp as Service Provider App
    participant IAMSP as IAM SAML SP<br/>(Federation Service)
    participant IdP as Identity Provider<br/>(Okta / AD FS)
    participant SessMgr as Session Manager
    participant TokenSvc as Token Service
    participant AuditSvc as Audit Service

    note over Browser,IAMSP: All external HTTP traffic over TLS 1.3
    note over IAMSP,AuditSvc: Internal traffic over mTLS

    %% ── Step 1: Access protected resource ───────────────────────────────
    User->>Browser: Navigate to https://app.tenant.example.com/dashboard
    Browser->>SPApp: GET /dashboard
    SPApp->>SPApp: Check local session cookie — absent or expired

    %% ── Step 2: SP initiates SSO ─────────────────────────────────────────
    SPApp-->>Browser: HTTP 302 Redirect to<br/>https://iam.example.com/federation/saml/initiate<br/>?tenant_id={tenantId}&relay_state={encodedOriginalURL}
    Browser->>IAMSP: GET /federation/saml/initiate?tenant_id=...&relay_state=...

    IAMSP->>IAMSP: Load SAMLProvider config for tenantId<br/>Verify provider.status = ACTIVE<br/>Fetch IdP metadata (from cache or metadataUrl)

    IAMSP->>IAMSP: Build SAMLAuthnRequest:<br/>ID: "_" + UUID (prefixed per SAML spec)<br/>Version: 2.0<br/>IssueInstant: now() ISO 8601 UTC<br/>Destination: idp.ssoUrl<br/>AssertionConsumerServiceURL: iam.example.com/federation/saml/acs<br/>Issuer: tenant SP entityId<br/>NameIDPolicy Format: urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress<br/>RequestedAuthnContext: PasswordProtectedTransport

    IAMSP->>IAMSP: Sign AuthnRequest with SP private key (RSA-SHA256)<br/>Private key via Vault PKI — tenant-specific SP cert<br/>Store InResponseTo = AuthnRequest.ID in Redis<br/>SET saml:nonce:{AuthnRequestId} tenantId EX 600

    IAMSP->>IAMSP: Encode: Base64(Deflate(AuthnRequest XML))<br/>Build redirect URL: idp.ssoUrl<br/>?SAMLRequest={encoded}&RelayState={relayState}<br/>Signature: URLEncode(sign(SAMLRequest=...&RelayState=...))

    IAMSP-->>Browser: HTTP 302 Redirect to IdP SSO URL with SAMLRequest
    Browser->>IdP: GET idp.ssoUrl?SAMLRequest=...&RelayState=...&Signature=...

    %% ── Step 3: IdP authenticates user ───────────────────────────────────
    IdP->>IdP: Parse and validate SAMLRequest<br/>Verify SP signature using pre-registered SP cert<br/>Check Destination matches this IdP's SSO endpoint

    IdP-->>Browser: IdP login form (HTML)
    User->>Browser: Enter IdP credentials (username + IdP password)
    Browser->>IdP: POST credentials to IdP
    IdP->>IdP: Authenticate user against corporate directory<br/>Apply IdP-side MFA policies if configured<br/>Build SAMLResponse with Assertion

    IdP->>IdP: Build Assertion:<br/>Issuer: idp.entityId<br/>Subject/NameID: user@corp.example.com<br/>Conditions:<br/>  NotBefore: now() - 60s (clock skew)<br/>  NotOnOrAfter: now() + 300s (5-min validity)<br/>  AudienceRestriction/Audience: SP entityId<br/>AuthnStatement:<br/>  AuthnInstant: now()<br/>  SessionIndex: {sessionIndex}<br/>  AuthnContextClassRef: PasswordProtectedTransport<br/>AttributeStatement:<br/>  email, firstName, lastName, groups, department<br/>InResponseTo: {AuthnRequest.ID}<br/>Sign Assertion with IdP private key (RSA-SHA256)

    IdP-->>Browser: HTTP 200 Auto-submit form<br/><form method="POST" action="https://iam.example.com/federation/saml/acs"><br/>  <input name="SAMLResponse" value="{Base64EncodedResponse}"><br/>  <input name="RelayState" value="{relayState}"><br/></form>
    Browser->>IAMSP: POST /federation/saml/acs<br/>Body: SAMLResponse={base64}&RelayState={encoded}

    %% ── Step 4: SP validates SAMLResponse ───────────────────────────────
    IAMSP->>IAMSP: Decode: Base64(SAMLResponse) → XML
    IAMSP->>IAMSP: [Validation 1] XML signature verification<br/>Fetch IdP X.509 cert from registered SAMLProvider<br/>Verify Signature using IdP public key (RSA-SHA256)<br/>Fail → reject with SIGNATURE_INVALID

    IAMSP->>IAMSP: [Validation 2] Issuer check<br/>Assert Issuer == SAMLProvider.entityId<br/>Fail → reject with ISSUER_MISMATCH

    IAMSP->>IAMSP: [Validation 3] Audience restriction<br/>Assert Audience element contains SP entityId<br/>Fail → reject with AUDIENCE_MISMATCH

    IAMSP->>IAMSP: [Validation 4] Time conditions<br/>Assert now() > NotBefore - 60s clock skew<br/>Assert now() < NotOnOrAfter + 60s clock skew<br/>Fail → reject with ASSERTION_EXPIRED

    IAMSP->>IAMSP: [Validation 5] InResponseTo / anti-replay<br/>GET saml:nonce:{InResponseTo} from Redis<br/>Assert nonce exists (matches AuthnRequest.ID)<br/>Assert tenantId in nonce matches request tenant<br/>DELETE nonce from Redis (consume once)<br/>Fail → reject with REPLAY_DETECTED or INRESPONSETO_MISMATCH

    IAMSP->>IAMSP: [Validation 6] AuthnContextClassRef<br/>Assert matches required assurance level<br/>from SAMLProvider.requiredAuthnContext config

    alt Any validation fails
        IAMSP->>AuditSvc: Emit FederatedAssertionRejected{tenantId, idpEntityId, reason, ip}
        IAMSP-->>Browser: HTTP 400 redirect to error page
    end

    %% ── Step 5: Claim mapping and JIT provisioning ───────────────────────
    IAMSP->>IAMSP: Extract NameID: user@corp.example.com<br/>Extract attributes per SAMLProvider.claimMapping:<br/>  email ← Attribute[@Name="email"]<br/>  firstName ← Attribute[@Name="firstName"]<br/>  groups ← Attribute[@Name="memberOf"] (multi-value)

    IAMSP->>IAMSP: Lookup user by (tenantId, federatedEmail):<br/>  EXISTS → return existing userId<br/>  NOT EXISTS AND jitProvisioningEnabled → provision

    alt JIT provisioning required
        IAMSP->>IAMSP: CreateUser{tenantId, email, firstName, lastName,<br/>source: SAML_JIT, externalId: NameID,<br/>providerId: SAMLProvider.id}
        note right of IAMSP: User Service gRPC call (mTLS)
        IAMSP->>AuditSvc: Emit JITUserProvisioned{userId, tenantId, providerId, email}
    end

    IAMSP->>IAMSP: Apply group mappings from SAMLProvider.groupMapping<br/>Sync groups → roles per provisioning policy

    %% ── Step 6: Session and token creation ──────────────────────────────
    IAMSP->>SessMgr: CreateSession{userId, tenantId, idpSessionIndex,<br/>assuranceLevel: from AuthnContextClassRef,<br/>federationProviderId: SAMLProvider.id,<br/>ip, userAgent}
    SessMgr-->>IAMSP: SessionCreated{sessionId}

    IAMSP->>TokenSvc: IssueTokens{userId, tenantId, sessionId,<br/>scopes: ["openid","profile"],<br/>assuranceLevel, federationContext}
    TokenSvc-->>IAMSP: Tokens{accessToken, refreshToken}

    IAMSP->>AuditSvc: Emit FederatedLoginSucceeded{<br/>userId, tenantId, sessionId,<br/>providerId, assuranceLevel,<br/>jitProvisioned, ip}

    %% ── Step 7: Redirect to original resource ───────────────────────────
    IAMSP-->>Browser: HTTP 302 Redirect to RelayState (original URL)<br/>Set-Cookie: iam_session={sessionId}; HttpOnly; Secure; SameSite=Lax<br/>Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict
    Browser->>SPApp: GET /dashboard (with iam_session cookie)
    SPApp->>SPApp: Validate iam_session → resolve access token<br/>Authorise access to dashboard
    SPApp-->>Browser: HTTP 200 /dashboard content
    Browser->>User: Dashboard rendered
```

---

## 3. Token Refresh Flow

This sequence covers the full refresh token rotation flow including the security-critical reuse detection path that protects against refresh token theft and replay attacks.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client App
    participant APIGW as API Gateway
    participant TokenSvc as Token Service
    participant SessMgr as Session Manager
    participant UserStore as User Store (PostgreSQL)
    participant AuditSvc as Audit Service

    note over Client,APIGW: TLS 1.3 — all traffic encrypted
    note over TokenSvc,AuditSvc: mTLS — internal service calls

    %% ── Step 1: Submit refresh token ────────────────────────────────────
    Client->>APIGW: POST /auth/refresh<br/>Cookie: refresh_token={opaqueToken}<br/>Content-Type: application/x-www-form-urlencoded<br/>Body: grant_type=refresh_token&client_id={clientId}

    APIGW->>APIGW: Validate Content-Type<br/>Extract refresh_token from Cookie header<br/>Rate limit: 10 req/min per client_id

    alt Rate limit exceeded
        APIGW-->>Client: HTTP 429 Too Many Requests
    end

    APIGW->>TokenSvc: Forward refresh request (mTLS)

    %% ── Step 2: Token family lookup ─────────────────────────────────────
    TokenSvc->>TokenSvc: SHA-256(opaqueToken) → tokenHash

    TokenSvc->>UserStore: SELECT rt.id, rt.family_id, rt.generation_number,<br/>rt.user_id, rt.tenant_id, rt.session_id,<br/>rt.expires_at, rt.revoked,<br/>tf.max_generation, tf.revoked AS family_revoked<br/>FROM refresh_tokens rt<br/>JOIN token_families tf ON rt.family_id = tf.id<br/>WHERE rt.hash = $1
    note right of UserStore: PostgreSQL primary read for strong consistency

    alt Token not found
        TokenSvc->>AuditSvc: Emit RefreshFailed{reason: TOKEN_NOT_FOUND, tokenHash, ip}
        TokenSvc-->>APIGW: HTTP 401 {error: invalid_token}
        APIGW-->>Client: HTTP 401
    end

    UserStore-->>TokenSvc: Token record {familyId, generation, maxGeneration,<br/>userId, tenantId, sessionId, expiresAt,<br/>revoked, familyRevoked}

    %% ── Step 3: Reuse detection check ───────────────────────────────────
    TokenSvc->>TokenSvc: Reuse check:<br/>IF token.revoked = true<br/>OR token.generation_number < family.max_generation<br/>THEN → REUSE DETECTED (token family compromise)

    alt Reuse detected — token family compromise
        note over TokenSvc,AuditSvc: Treat as stolen token — revoke entire family
        TokenSvc->>UserStore: UPDATE token_families<br/>SET revoked = true, revoked_reason = 'REUSE_DETECTED',<br/>revoked_at = now()<br/>WHERE id = $1
        TokenSvc->>UserStore: UPDATE refresh_tokens SET revoked = true<br/>WHERE family_id = $1 AND revoked = false
        TokenSvc->>SessMgr: RevokeSession{sessionId: token.sessionId,<br/>reason: REFRESH_TOKEN_REUSE}
        SessMgr-->>SessMgr: DEL session:{sessionId} from Redis<br/>Mark session REVOKED in PostgreSQL
        TokenSvc->>AuditSvc: Emit TokenFamilyRevoked{<br/>userId, tenantId, familyId,<br/>revokedGeneration: token.generation,<br/>maxGeneration: family.maxGeneration,<br/>reason: REUSE_DETECTED, ip}
        TokenSvc-->>APIGW: HTTP 401 {error: invalid_token,<br/>error_description: "Token reuse detected. Please re-authenticate."}
        APIGW-->>Client: HTTP 401 — client must redirect to login
    end

    %% ── Step 4: Token expiry check ──────────────────────────────────────
    alt Refresh token expired
        TokenSvc->>AuditSvc: Emit RefreshFailed{reason: TOKEN_EXPIRED, userId, ip}
        TokenSvc-->>APIGW: HTTP 401 {error: invalid_token,<br/>error_description: "Refresh token has expired."}
        APIGW-->>Client: HTTP 401
    end

    %% ── Step 5: Session validation ──────────────────────────────────────
    TokenSvc->>SessMgr: ValidateSession{sessionId: token.sessionId}
    SessMgr->>SessMgr: HGETALL session:{sessionId} from Redis

    alt Session not found in Redis (expired or revoked)
        SessMgr-->>TokenSvc: SessionInvalid{reason: SESSION_NOT_FOUND}
        TokenSvc->>AuditSvc: Emit RefreshFailed{reason: SESSION_EXPIRED, userId, sessionId, ip}
        TokenSvc-->>APIGW: HTTP 401 {error: invalid_token,<br/>error_description: "Session has expired. Please re-authenticate."}
        APIGW-->>Client: HTTP 401
    end

    SessMgr-->>TokenSvc: SessionValid{userId, tenantId, assuranceLevel, idleExpiresAt}

    %% ── Step 6: User status check ───────────────────────────────────────
    TokenSvc->>UserStore: SELECT status FROM users<br/>WHERE id = $1 AND tenant_id = $2
    UserStore-->>TokenSvc: {status}

    alt User suspended or deleted
        TokenSvc->>SessMgr: RevokeSession{sessionId, reason: USER_SUSPENDED}
        TokenSvc->>UserStore: UPDATE token_families SET revoked = true<br/>WHERE user_id = $1 AND revoked = false
        TokenSvc->>AuditSvc: Emit RefreshFailed{reason: USER_SUSPENDED, userId, ip}
        TokenSvc-->>APIGW: HTTP 401 {error: access_denied,<br/>error_description: "Account is not active."}
        APIGW-->>Client: HTTP 401
    end

    %% ── Step 7: Issue new access token ──────────────────────────────────
    TokenSvc->>TokenSvc: Build new JWT claims:<br/>sub, iss, aud, iat, exp: now()+900, jti: new UUID<br/>tid, sid, aal, scope (inherit from family record)
    TokenSvc-->>TokenSvc: Sign via Vault Transit RS256<br/>GET /v1/transit/sign/iam-jwt payload=base64(header.claims)
    note right of TokenSvc: New access token issued — 15 min expiry

    %% ── Step 8: Rotate refresh token ────────────────────────────────────
    TokenSvc->>TokenSvc: Generate new_refresh_token (256-bit random, opaque)<br/>new_generation = token.generation_number + 1

    TokenSvc->>UserStore: BEGIN TRANSACTION<br/>  UPDATE refresh_tokens SET revoked = true<br/>  WHERE id = {currentTokenId};<br/><br/>  INSERT INTO refresh_tokens<br/>  (id, hash, family_id, generation_number,<br/>  user_id, tenant_id, session_id, expires_at)<br/>  VALUES (new_uuid, SHA256(new_token), family_id,<br/>  new_generation, userId, tenantId, sessionId,<br/>  now() + interval '24 hours');<br/><br/>  UPDATE token_families<br/>  SET max_generation = new_generation,<br/>  last_rotated_at = now()<br/>  WHERE id = {familyId};<br/>COMMIT;
    note right of UserStore: Atomic token rotation in single transaction

    UserStore-->>TokenSvc: Transaction committed

    %% ── Step 9: Update session idle TTL ─────────────────────────────────
    TokenSvc->>SessMgr: Touch session{sessionId} — reset idle TTL to +30 min
    SessMgr->>SessMgr: HSET session:{sessionId} last_activity_at=now()<br/>EXPIRE session:{sessionId} 1800 (reset idle timer)
    SessMgr-->>TokenSvc: OK

    %% ── Step 10: Audit event ────────────────────────────────────────────
    TokenSvc->>AuditSvc: Emit TokenIssued{<br/>eventType: TOKEN_REFRESHED,<br/>userId, tenantId, sessionId, familyId,<br/>oldJti: currentToken.jti,<br/>newJti: newAccessToken.jti,<br/>newGeneration, ip, userAgent,<br/>timestamp: now()}
    AuditSvc->>AuditSvc: Serialise Avro · sign HMAC · publish iam.audit (acks=all)

    %% ── Step 11: Return new tokens ──────────────────────────────────────
    TokenSvc-->>APIGW: HTTP 200 {<br/>access_token: "eyJ...",<br/>token_type: "Bearer",<br/>expires_in: 900,<br/>scope: "openid profile email"}
    APIGW-->>Client: HTTP 200<br/>Set-Cookie: refresh_token={newOpaqueToken}; HttpOnly; Secure;<br/>SameSite=Strict; Max-Age=86400; Path=/auth/refresh<br/>Body: {access_token, token_type, expires_in, scope}
    note right of Client: Old refresh token is now revoked<br/>New refresh token set in HttpOnly cookie<br/>Access token stored in memory (not localStorage)
```
