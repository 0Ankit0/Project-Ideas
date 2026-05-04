# Activity Diagrams

These activities translate the requirements, API contracts, and state machines into
implementation-ready control flow. They focus on the IAM paths where security posture,
revocation guarantees, and audit evidence must remain correct under concurrency.

## Login and Token Issuance Activity

```mermaid
flowchart TD
    A["Receive login request"] --> B["Resolve tenant authentication policy"]
    B --> C{"Requested method allowed"}
    C -->|No| C1["Reject request and write denied audit event"]
    C -->|Yes| D["Validate passwordless proof or federation assertion"]
    D --> E{"Primary authentication valid"}
    E -->|No| F["Increment failure counters and risk signals"]
    F --> G{"Lockout threshold reached"}
    G -->|Yes| G1["Set identity to locked and page SecOps for privileged subjects"]
    G -->|No| G2["Return retryable authentication error"]
    E -->|Yes| H["Collect IP, geo velocity, device posture, attestation, and client assurance"]
    H --> I["Build provisional session context"]
    I --> J{"Adaptive MFA or step up required"}
    J -->|Yes| K["Issue challenge with 5 minute TTL and method preference order"]
    K --> L{"Challenge verified"}
    L -->|No| M["Increment MFA failure counter and downgrade trust score"]
    M --> N{"Retry budget remaining"}
    N -->|Yes| K
    N -->|No| O["Terminate provisional session and emit fraud alert"]
    L -->|Yes| P["Promote assurance level and record factor set"]
    J -->|No| P
    P --> Q["Persist active session in source of truth store"]
    Q --> R["Create refresh token family generation 0"]
    R --> S["Sign access token with current key version"]
    S --> T["Publish session started, login succeeded, and decision audit events"]
    T --> U["Return token pair, session metadata, and remediation hints"]
```

**Implementation notes**
- Tenant policy decides whether passwordless, social federation, enterprise federation, or password fallback is legal for the client application.
- Device posture combines device binding, WebAuthn attestation status, impossible-travel score, ASN reputation, and prior compromise markers.
- MFA challenge selection order is WebAuthn platform, WebAuthn roaming, TOTP, push, then recovery code; SMS is recovery-only for low-assurance tenants.
- Primary authentication failures lock the account after 10 attempts in 15 minutes for standard users and 5 attempts in 15 minutes for privileged users.

## Refresh Rotation and Reuse Detection Activity

```mermaid
flowchart TD
    A["Receive refresh request"] --> B["Hash presented refresh token"]
    B --> C["Load token family row with serializable isolation"]
    C --> D{"Family active and session active"}
    D -->|No| D1["Return invalid grant and emit revocation telemetry"]
    D -->|Yes| E{"Hash matches latest active generation"}
    E -->|No| F["Mark reuse detected on family"]
    F --> G["Revoke family, session, step up grants, and remembered device state"]
    G --> H["Publish token refresh reuse detected event"]
    H --> I["Push revocation watermark to gateway caches"]
    I --> J["Return invalid grant without replacement token"]
    E -->|Yes| K["Increment family generation counter"]
    K --> L["Persist new latest hash plus rotated_at timestamp"]
    L --> M["Expire superseded generation record"]
    M --> N["Sign new access token"]
    N --> O["Issue replacement refresh token"]
    O --> P["Publish token refresh rotated event"]
    P --> Q["Return new token pair"]
```

**Implementation notes**
- Exactly one concurrent refresh wins per family. Losers receive `invalid_grant` and do not mint additional access tokens.
- `generation` is a 64-bit monotonic counter scoped to `family_id`; overflow is treated as an operational defect that forces re-authentication before wraparound.
- Reuse detection cascades to the active session, step-up grant cache, and any derived token-exchange grants created from the family.
- Revocation publication target is `100 ms` commit-to-bus and `5 s P95` propagation to all gateways and PDP caches.

## Privileged Action Step-Up Activity

```mermaid
flowchart TD
    A["Privileged API call arrives at PEP"] --> B["Validate access token and current session state"]
    B --> C["Call PDP with subject, action, resource, and environment context"]
    C --> D{"Decision includes require_step_up obligation"}
    D -->|No| D1["Enforce remaining obligations and forward request"]
    D -->|Yes| E["Inspect last MFA time, device posture, and risk score"]
    E --> F{"Existing step up still valid"}
    F -->|Yes| D1
    F -->|No| G["Set session to step_up_required"]
    G --> H["Challenge strongest available factor"]
    H --> I{"Step up success within 5 minutes"}
    I -->|No| J["Deny privileged action and emit step up failure event"]
    I -->|Yes| K["Mint short lived step up grant bound to session and device"]
    K --> L["Re-run PDP with elevated assurance level"]
    L --> M{"Decision permit"}
    M -->|No| N["Return deny with explain payload"]
    M -->|Yes| O["Execute action and log reason code plus approval reference"]
```

**Implementation notes**
- Step-up freshness is `15 minutes` for admin writes, `5 minutes` for credential reset, policy publish, or break-glass approval, and `1 request` for signing-key export.
- Device posture can block step-up completion even after factor success when attestation is absent, malware risk is high, or screen lock is disabled for managed-device tenants.
- PEP must enforce obligations before forwarding the privileged request, including `require_justification`, `notify_owner`, and `record_session`.

## Deprovisioning and Emergency Access Expiry Activity

```mermaid
flowchart TD
    A["Receive suspension, termination, or break glass expiry signal"] --> B{"Trigger type"}
    B -->|Lifecycle offboarding| C["Set identity state to pending_deprovision"]
    B -->|Break glass expiry| D["Set emergency grant to expired"]
    C --> E["Revoke active sessions and refresh families immediately"]
    D --> E
    E --> F["Publish revocation events to gateways, PDP caches, and relying parties"]
    F --> G["Queue entitlement revoke jobs by downstream system priority"]
    G --> H["Collect acknowledgements plus reconciliation proof"]
    H --> I{"All privileged entitlements removed"}
    I -->|No| J["Retry with backoff and escalate to operator queue"]
    J --> K{"Grace period exceeded"}
    K -->|No| H
    K -->|Yes| L["Freeze identity, quarantine residual grants, and page on call"]
    I -->|Yes| M["Archive subject credentials and attestations"]
    M --> N["Write immutable completion audit record"]
    N --> O["Transition identity to deprovisioned or grant to completed"]
```

**Implementation notes**
- Deprovisioning priority order is session revoke, refresh family revocation, privileged entitlements, standard entitlements, downstream profile cleanup, and archive export.
- Emergency access grants never extend automatically; renewal requires a new request, new approvals, and a new step-up proof.
- Reconciliation proof is the signed set of downstream acknowledgements, residual exception list, and final operator disposition.

## Activity Guardrails

| Activity | Hard guardrail | Timeout or SLA | Required evidence |
|---|---|---|---|
| Login | No token issued before session record commits | Auth response in `P95 < 800 ms` without MFA | `auth.login.succeeded` or `auth.login.failed` |
| Refresh rotation | Single winning generation update | `P95 < 200 ms` on warm path | `token.refresh.rotated` or `token.refresh.reuse_detected` |
| Step-up | Must bind factor result to current session and device | Challenge TTL `5 min` | `auth.step_up.completed` plus obligation trace |
| Deprovisioning | Session revoke precedes entitlement cleanup | Revocation propagation `P95 < 5 s` | `identity.suspended` or `identity.deprovisioned` |
| Break-glass expiry | Expiry cannot depend on operator action | Grant TTL max `4 h` | `break_glass.grant.expired` |
