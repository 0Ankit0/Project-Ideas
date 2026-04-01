# Sequence Diagrams — Identity and Access Management Platform

This document specifies the four most complex interaction flows in the IAM Platform,
each documented with a Mermaid sequence diagram and a detailed narrative. All diagrams
show both success and failure branches, audit emission points, and async vs synchronous
call boundaries.

---

## 1. TOTP MFA Step-Up Verification

### 1.1 Context

Called when an authenticated session requires step-up to access a sensitive resource
(`SessionStatus = STEP_UP_REQUIRED`). The user submits a 6-digit TOTP code generated
by their authenticator app. The flow validates the code, checks the replay cache, and
promotes the session to `STEP_UP_IN_PROGRESS → ACTIVE` with a short-lived step-up token.

### 1.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant U  as User
    participant AC as AuthController
    participant SM as SessionManager
    participant MO as MFAOrchestrator
    participant MDR as MFADeviceRepository
    participant TV as TOTPValidator
    participant RC as ReplayCache (Redis)
    participant AW as AuditWriter

    U->>AC: POST /auth/mfa/totp {sessionToken, code}

    AC->>AC: verifyBearerToken(sessionToken)
    note right of AC: Validates JWT signature and exp claim

    alt sessionToken invalid or expired
        AC-->>U: 401 Unauthorized — invalid session token
    end

    AC->>SM: getSession(sessionId)
    SM-->>AC: Session{status, userId, tenantId, mfaVerified}

    alt Session.status != STEP_UP_REQUIRED
        AC-->>U: 409 Conflict — step-up not in required state
    end

    AC->>MO: verifyTOTP(userId, tenantId, submittedCode)

    MO->>MDR: findActiveByUserAndType(userId, TOTP)

    alt no active TOTP device enrolled
        MDR-->>MO: []
        MO-->>AC: MFAError(DEVICE_NOT_FOUND)
        AC->>AW: emit(MFAChallengeFailed, userId, DEVICE_NOT_FOUND)
        AC-->>U: 404 No TOTP device enrolled
    end

    MDR-->>MO: MFADevice{deviceId, secretEncrypted, status, failCount}

    alt MFADevice.status == REVOKED
        MO-->>AC: MFAError(DEVICE_REVOKED)
        AC-->>U: 403 MFA device has been revoked
    end

    MO->>MO: decryptTOTPSecret(secretEncrypted) — via VaultClient
    note right of MO: Secret decrypted in-process; never logged

    MO->>TV: generateExpectedCodes(totpSecret, windowOffset=[-1, 0, +1])
    TV-->>MO: expectedCodes[3]
    note right of TV: Each window is 30 s; covers ±30 s clock skew

    MO->>MO: match(submittedCode, expectedCodes)

    alt code does not match any window
        MO->>MDR: incrementFailCount(deviceId)
        MO->>AW: emit(MFAChallengeFailed, userId, deviceId, INVALID_CODE)
        MO-->>AC: MFAError(INVALID_CODE, failCount)
        AC-->>U: 401 Invalid TOTP code
    end

    MO->>RC: checkReplay(key="totp:{deviceId}:{submittedCode}")

    alt replay entry found
        MO->>AW: emit(MFAReplayDetected, userId, deviceId, submittedCode)
        MO-->>AC: MFAError(REPLAY_DETECTED)
        AC-->>U: 401 TOTP code already used — replay detected
    end

    RC->>RC: set("totp:{deviceId}:{submittedCode}", 1, TTL=90s)
    note right of RC: TTL covers 3 TOTP windows to prevent reuse

    MO->>MDR: resetFailCount(deviceId)
    MO->>MDR: updateLastUsedAt(deviceId, now())

    MO->>SM: markStepUpComplete(sessionId, method=TOTP)
    SM->>SM: issueStepUpToken(sessionId, TTL=300s)
    SM-->>MO: StepUpToken{jwt, expiresIn=300}

    MO->>AW: emit(MFAChallengeSucceeded, userId, deviceId, sessionId)
    MO-->>AC: StepUpResult{stepUpToken, expiresIn=300}

    AC-->>U: 200 OK {stepUpToken, expiresIn}
```

### 1.3 Failure Matrix

| Failure Condition | HTTP Status | Audit Event | Recovery |
|---|---|---|---|
| Invalid/expired session token | 401 | None | User re-authenticates |
| Session not in STEP_UP_REQUIRED | 409 | None | No action — wrong call |
| No TOTP device enrolled | 404 | `MFAChallengeFailed(DEVICE_NOT_FOUND)` | User enrolls device |
| Device is REVOKED | 403 | None | Admin re-provisions device |
| Wrong code (< lockout threshold) | 401 | `MFAChallengeFailed(INVALID_CODE)` | User retries |
| Wrong code (lockout threshold hit) | 403 | `UserLockedOut` | Admin unlocks |
| Replay detected | 401 | `MFAReplayDetected` | User waits for next window |

---

## 2. WebAuthn Device Registration

### 2.1 Context

A user with an active session enrolls a hardware security key or platform authenticator
(Touch ID, Face ID, Windows Hello) as a second factor. The flow is split into two HTTP
calls: `begin` generates a challenge, `complete` verifies the authenticator response.

### 2.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant B   as User Browser
    participant AC  as AuthController
    participant WS  as WebAuthnService
    participant CS  as ChallengeStore (Redis)
    participant MDR as MFADeviceRepository
    participant AW  as AuditWriter

    B->>AC: POST /mfa/webauthn/register/begin
    note right of B: Requires active authenticated session (not step-up)

    AC->>AC: requireAuthenticatedSession()
    alt session invalid
        AC-->>B: 401 Unauthorized
    end

    AC->>WS: beginRegistration(userId, tenantId, displayName)

    WS->>WS: generateChallenge() — 32 bytes from CSPRNG
    WS->>CS: set("wauthn:reg:{challengeId}", {challenge, userId, tenantId}, TTL=300s)
    CS-->>WS: stored

    WS->>WS: buildPublicKeyCredentialCreationOptions(challenge, rpId, userId)
    note right of WS: rpId = platform FQDN; pubKeyCredParams = ES256, RS256

    WS-->>AC: CreationOptions{challengeId, rp, user, pubKeyCredParams, timeout, attestation="none"}
    AC-->>B: 200 OK {challengeId, creationOptions}

    B->>B: navigator.credentials.create(creationOptions)
    note right of B: Browser prompts user to touch security key or use biometric

    B->>AC: POST /mfa/webauthn/register/complete {challengeId, credential}

    AC->>WS: completeRegistration(challengeId, credential)

    WS->>CS: get("wauthn:reg:{challengeId}")

    alt challenge not found (expired or never issued)
        CS-->>WS: null
        WS-->>AC: WebAuthnError(CHALLENGE_NOT_FOUND)
        AC-->>B: 400 Challenge expired or not found
    end

    CS-->>WS: {challenge, userId, tenantId, createdAt}
    WS->>CS: del("wauthn:reg:{challengeId}")
    note right of CS: Delete challenge immediately to prevent replay

    WS->>WS: verifyClientDataJSON(credential.response.clientDataJSON)
    note right of WS: Checks type=webauthn.create, origin, challenge binding

    alt origin does not match expected origin
        WS-->>AC: WebAuthnError(ORIGIN_MISMATCH)
        AC-->>B: 400 Invalid origin in clientDataJSON
    end

    WS->>WS: verifyRpIdHash(authData.rpIdHash, expectedRpId)

    alt rpIdHash mismatch
        WS-->>AC: WebAuthnError(RP_ID_MISMATCH)
        AC-->>B: 400 Invalid relying party ID
    end

    WS->>WS: cborDecode(credential.response.attestationObject)
    WS->>WS: validateAttestationStatement(fmt, attStmt, authData)
    note right of WS: Accepts "none" and "packed" (self) attestation formats

    alt attestation verification fails
        WS-->>AC: WebAuthnError(ATTESTATION_INVALID)
        AC-->>B: 400 Attestation verification failed
    end

    WS->>WS: extractPublicKey(authData) — COSE format
    WS->>WS: extractCredentialId(authData)
    WS->>WS: extractSignCount(authData)

    WS->>MDR: existsByCredentialId(credentialId)

    alt credential already registered to any user
        WS-->>AC: WebAuthnError(CREDENTIAL_EXISTS)
        AC-->>B: 409 Credential ID already registered
    end

    WS->>MDR: save(MFADevice{
        type=WEBAUTHN,
        userId,
        credentialId,
        publicKey (COSE-encoded),
        signCount,
        status=ACTIVE,
        enrolledAt=now()
    })
    MDR-->>WS: MFADevice{deviceId}

    WS->>AW: emit(MFAEnrolled, userId, deviceId, WEBAUTHN, tenantId)
    WS-->>AC: RegistrationResult{deviceId, credentialId}

    AC-->>B: 201 Created {deviceId}
```

### 2.3 Failure Matrix

| Failure Condition | HTTP Status | Audit Event | Recovery |
|---|---|---|---|
| No authenticated session | 401 | None | User logs in first |
| Challenge expired (> 300 s) | 400 | None | User restarts registration |
| Origin mismatch | 400 | `WebAuthnRegistrationFailed(ORIGIN_MISMATCH)` | Check client config |
| RP ID hash mismatch | 400 | `WebAuthnRegistrationFailed(RP_ID_MISMATCH)` | Check server config |
| Attestation invalid | 400 | `WebAuthnRegistrationFailed(ATTESTATION_INVALID)` | User retries with different key |
| Credential ID already registered | 409 | None | Use existing device |

---

## 3. Policy Evaluation Flow (PDP Internal)

### 3.1 Context

The Policy Decision Point (PDP) is invoked by the PEP middleware on every request to a
protected resource. The PDP resolves the active policy bundle for the tenant, fetches
subject and resource attributes, runs the rule engine, and returns a structured
`Decision` with obligations. The entire synchronous path must complete in under 25 ms
at the 99th percentile.

### 3.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant PEP  as PEPMiddleware
    participant PDP  as PDPService
    participant PC   as PolicyCache (Redis)
    participant PS   as PolicyStore (Postgres)
    participant SAP  as SubjectAttributeProvider
    participant RAP  as ResourceAttributeProvider
    participant RE   as RuleEngine
    participant OH   as ObligationHandler
    participant DL   as DecisionLogger (async)

    PEP->>PDP: evaluate(EvaluationRequest{
        subject{id, type},
        resource{id, type},
        action,
        environment{ip, time, devicePosture}
    })

    PDP->>PC: get(key="policy:{tenantId}:{bundleHash}")

    alt cache miss
        PC-->>PDP: null
        PDP->>PS: fetchActivePolicies(tenantId)
        PS-->>PDP: List~Policy~ with statements
        PDP->>PDP: computeBundleHash(policies)
        PDP->>PC: set(key, PolicyBundle, TTL=60s)
        PC-->>PDP: cached
    end

    PC-->>PDP: PolicyBundle{policies, bundleHash, version}

    PDP->>SAP: getAttributes(subjectId, subjectType, tenantId)
    note right of SAP: Fetches roles, group memberships, custom attributes
    SAP-->>PDP: SubjectAttributes{
        roles[],
        groups[],
        department,
        clearanceLevel,
        mfaVerified,
        deviceTrust
    }

    PDP->>RAP: getAttributes(resourceId, resourceType, tenantId)
    note right of RAP: Fetches tags, owner, classification, region
    RAP-->>PDP: ResourceAttributes{
        owner,
        classification,
        region,
        tags{},
        dataResidency
    }

    PDP->>RE: evaluate(bundle, subjectAttrs, resourceAttrs, action, environment)

    loop for each PolicyStatement in bundle
        RE->>RE: matchPrincipals(statement.principals, subject) → bool
        RE->>RE: matchResources(statement.resources, resource) → bool
        RE->>RE: matchActions(statement.actions, action) → bool
        RE->>RE: evaluateConditions(statement.conditions, subjectAttrs, resourceAttrs, environment) → bool

        alt all four matchers return true
            RE->>RE: record(effect=statement.effect, statementId, obligations)
        end
    end

    RE->>RE: applyPrecedence(results)
    note right of RE: Explicit DENY overrides any PERMIT; no-match → DENY

    RE-->>PDP: RuleEngineResult{
        decision: PERMIT|DENY,
        matchedStatements[],
        denyReason?,
        obligations[]
    }

    alt decision == DENY
        PDP->>DL: logDecision(request, DENY, matchedStatements) [fire-and-forget]
        PDP-->>PEP: Decision{DENY, reason, policyVersion, correlationId}
    end

    PDP->>OH: prepareObligations(result.obligations, subject, resource)
    OH-->>PDP: ObligationSet{
        requireMFAStepUp: bool,
        logAccessAttempt: bool,
        notifyResourceOwner: bool,
        enforceDataResidency: string?
    }

    PDP->>DL: logDecision(request, PERMIT, matchedStatements, obligations) [fire-and-forget]
    DL-->>PDP: queued

    PDP-->>PEP: Decision{
        result: PERMIT,
        obligations: ObligationSet,
        policyVersion,
        bundleHash,
        matchedRules[],
        correlationId,
        evaluationMs
    }
```

### 3.3 Performance Constraints

| Step | Target Latency (P99) |
|---|---|
| Redis cache hit (policy bundle) | < 2 ms |
| Subject attribute resolution | < 5 ms |
| Resource attribute resolution | < 3 ms |
| Rule engine evaluation (≤ 50 statements) | < 8 ms |
| Obligation preparation | < 2 ms |
| End-to-end PDP evaluation | < 25 ms |

### 3.4 Failure Handling

- **PolicyStore unreachable**: PDP serves the last cached bundle if TTL < 120 s.
  If no cached bundle exists, the decision fails closed (`DENY`) and emits
  `PDPCircuitOpen` alert.
- **Attribute provider timeout**: PDP marks attributes as unavailable and evaluates
  conditions with a `missing-attribute = deny` policy for conditions that require them.
- **RuleEngine panic**: Recovered; decision fails closed (`DENY`); `PDPEvaluationError`
  emitted to the audit stream.

---

## 4. Token Revocation Cascade

### 4.1 Context

An admin or security automation triggers revocation of a specific token. The service
revokes the token's entire family (all rotated siblings), invalidates Redis cache
entries, publishes a Kafka event for real-time propagation to the API Gateway PEP, and
emits per-token audit events. A parallel branch shows the automatic family revocation
triggered by refresh token reuse detection.

### 4.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant AS  as AdminService
    participant TS  as TokenService
    participant TFR as TokenFamilyRepository
    participant RC  as RedisCache
    participant KP  as KafkaProducer
    participant PEP as GatewayPEP
    participant AW  as AuditWriter

    AS->>TS: POST /tokens/{tokenId}/revoke {reason, actorId}

    TS->>TFR: findByTokenId(tokenId)

    alt token not found
        TFR-->>TS: null
        TS-->>AS: 404 Token not found
    end

    TFR-->>TS: Token{tokenId, familyId, status, expiresAt, sessionId}

    alt Token.status already REVOKED
        TS-->>AS: 409 Token already revoked
    end

    TS->>TFR: findByFamilyId(familyId)
    TFR-->>TS: List~Token~ — all tokens in family (may include expired + active)

    TS->>TFR: revokeFamily(familyId, reason, actorId, revokedAt=now())
    note right of TFR: Single serialisable DB transaction; sets revokedAt on all rows

    TFR-->>TS: revokedTokenIds[]

    loop for each revokedTokenId
        TS->>RC: del("token:{revokedTokenId}")
        TS->>RC: sadd("revoked-tokens:{tenantId}", revokedTokenId)
        RC->>RC: expire("revoked-tokens:{tenantId}", maxTTL)
    end

    RC-->>TS: cache invalidation complete

    TS->>KP: publish(topic="iam.token.revoked", msg=TokenFamilyRevoked{
        familyId,
        tokenIds[],
        sessionId,
        reason,
        actorId,
        tenantId,
        revokedAt
    })
    KP-->>TS: offset confirmed (ack=all)

    note over PEP: GatewayPEP consumes iam.token.revoked topic
    PEP->>PEP: updateLocalDenyList(tokenIds[])
    note right of PEP: Local cache update SLA ≤ 5 s P95

    loop for each revokedTokenId [async, batched]
        TS->>AW: emit(TokenRevoked{
            tokenId,
            familyId,
            sessionId,
            reason,
            actorId,
            tenantId
        })
    end

    AW-->>TS: events queued (non-blocking)
    TS-->>AS: 200 OK {revokedCount, familyId, tokenIds[]}

    note over TS,TFR: ── Refresh Token Reuse Detection Branch ──

    rect rgb(255, 245, 245)
        TS->>TS: rotateRefreshToken(incomingRefreshToken)
        TS->>TFR: findByHash(hash(incomingRefreshToken))
        TFR-->>TS: Token{status=ROTATED, familyId}
        note right of TS: A ROTATED token re-presented = reuse detected

        TS->>TFR: revokeFamily(familyId, REUSE_DETECTED, actorId=system)
        TS->>RC: invalidateFamily(familyId)
        TS->>KP: publish(TokenFamilyRevoked{familyId, reason=REUSE_DETECTED, ...})
        TS->>AW: emit(SecurityAlert{
            type=REFRESH_TOKEN_REUSE,
            familyId,
            userId,
            tenantId,
            suspectTokenHash
        })
        TS-->>AS: 401 Unauthorized — refresh token reuse detected
    end
```

### 4.3 Propagation SLA and Guarantees

| Guarantee | Target |
|---|---|
| DB revocation write durability | Synchronous, fsync before response |
| Redis cache invalidation | < 100 ms after DB write |
| Kafka event delivery | At-least-once; consumer deduplicates by `familyId` |
| GatewayPEP local cache update | ≤ 5 s P95 after Kafka publish |
| Audit event write | Async, DLQ-backed; ≤ 30 s eventual |
| Reuse detection to family revocation | < 500 ms end-to-end |

### 4.4 Failure Handling

- **Kafka unavailable during revocation**: The DB revocation is committed regardless.
  A background reconciliation job re-publishes un-acknowledged `TokenFamilyRevoked`
  events every 10 seconds by scanning `tokens.revokedAt IS NOT NULL AND published=false`.
- **Redis unavailable**: Cache invalidation is retried with exponential backoff for
  30 seconds. The Kafka event to GatewayPEP serves as the authoritative revocation
  signal in this window.
- **Partial family revocation**: The `revokeFamily` call is a single DB transaction;
  it either revokes all family tokens or none. No partial states are possible.
