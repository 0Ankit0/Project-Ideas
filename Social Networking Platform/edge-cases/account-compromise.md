# Account Compromise — Edge Cases

## Overview

Account compromise attacks target the authentication layer, session management, and account
recovery flows. Social networking accounts are high-value targets: they hold personal data,
financial connections, and can be used to spread misinformation at scale. This file documents
the most dangerous attack vectors — from large-scale credential stuffing campaigns to targeted
social-engineering of phone carriers — and the defenses required at each layer.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| Credential stuffing attack | Mass account takeover using leaked credentials from other breaches | Login failure rate spike from novel IPs; account-velocity anomalies; impossible travel | CAPTCHA on elevated-risk login attempts; device fingerprinting; rate limiting per IP/subnet | Force-reset compromised accounts; notify affected users; revoke all sessions | Leaked-credential feed integration (HaveIBeenPwned API); breached-password blocking at login |
| Session hijacking via stolen cookie | Attacker impersonates user without needing credentials | Concurrent sessions from geographically impossible locations; device-fingerprint mismatch mid-session | Session binding to device fingerprint and IP range; re-authentication for sensitive actions | Revoke hijacked session; notify user; force step-up auth | HttpOnly/Secure/SameSite cookie attributes; session expiry and rotation on privilege changes |
| Account takeover via SIM swap | Attacker transfers victim's phone number to their SIM; intercepts SMS 2FA | Sudden phone-number deregistration and re-registration event; new device registration following SIM event | Binding 2FA to authenticator app or hardware key instead of SMS; 48-hour phone-number change cooldown | Lock account; require government-ID verification for recovery | Educate users on authenticator-based 2FA; allow users to flag SIM-swap risk on their account |
| 2FA bypass via phishing (real-time relay) | Attacker proxies victim's login to capture 2FA code before it expires | Login attempt from new device while user is on a phishing page (correlated timing) | Passkey/WebAuthn as phishing-resistant 2FA option; session context mismatch detection | Revoke compromised session; notify user of real-time phishing attempt | Promote WebAuthn enrollment; anti-phishing page-alert browser extension integration |
| Recovery flow enumeration | Attacker probes recovery flow to confirm registered email/phone numbers | High rate of recovery lookups from a single IP; unusual recovery-initiation patterns | Consistent response for found/not-found recovery attempts (no oracle); rate limiting on recovery initiation | No action needed if oracle is closed; monitor for continued probing | Normalized response times for all recovery outcomes; recovery-attempt rate limiting and CAPTCHA |
| Trusted-device bypass after device compromise | User's trusted device is stolen/compromised; attacker bypasses 2FA | Device access from new physical location while user is elsewhere | Remote device deregistration from account settings; geolocation anomaly triggers re-auth | Revoke trusted-device status; notify user; require re-enrollment | Periodic trusted-device re-verification; biometric or PIN unlock for app on device |
| Account merge collision | Two accounts linked to the same email/phone post-merge create data integrity issues | Duplicate identity event in account management system; merge audit log discrepancy | Pre-merge identity deduplication check; transactional merge with rollback capability | Roll back failed merge; notify user; require manual review | Idempotent merge operations; unique constraint enforcement at database level |
| OAuth token abuse by malicious third-party app | Rogue app with valid OAuth token exfiltrates data or posts without consent | Anomalous API usage pattern for token (high read volume, off-hours activity) | OAuth scope minimization; token expiry enforcement; per-app rate limits | Revoke token; notify user; remove malicious app from app directory | App review process before OAuth approval; user-visible permission grant screen; token audit logs |

---

## Detailed Scenarios

### Scenario 1: Large-Scale Credential Stuffing Campaign

**Trigger**: A data broker sells a 400-million-row credential list (email + plaintext password
pairs) from a recent third-party breach. Attackers run the list against the platform's login
endpoint using a residential proxy network to avoid IP-based blocks. 800,000 valid credential
pairs produce 800,000 successful logins before automated defenses escalate.

**Attack Pattern**:
- Login attempts distributed across 120,000 unique residential proxy IPs.
- Attempt rate: ~5 attempts/second/IP — below per-IP thresholds.
- Aggregate platform-wide failure rate rises from 12% to 19% (7-point increase triggers anomaly).

**Detection**:
1. **Aggregate failure rate anomaly**: Platform-wide login failure rate exceeds 1.5× 7-day
   baseline; P1 alert fires within 8 minutes.
2. **Credential-list feed**: HaveIBeenPwned API flags 38% of attempted credentials as
   previously breached; elevated correlation triggers fraud-detection escalation.
3. **Device fingerprint velocity**: 200,000 successful logins from previously unseen device
   fingerprints within 2 hours (normally <5,000/hour).

**Mitigation**:
1. **Step-up CAPTCHA**: Accounts with login from a new device + unrecognized IP forced through
   invisible CAPTCHA, then visible CAPTCHA if invisible fails.
2. **Leaked-password gate**: On successful authentication, check plaintext password against
   breached-credential database; if matched, force password reset before session is established.
3. **Impossible-travel block**: New logins >800 km from last session within 4 hours require
   email verification.
4. **Subnet-level rate limiting**: When a /24 subnet exceeds 500 login attempts in 5 minutes,
   apply progressive CAPTCHA difficulty to the entire subnet.

**Recovery**:
- Force-reset all accounts where session was established by an unrecognized device.
- Send breach notification email to affected users per legal obligation.
- Coordinate with security team to share IOCs with industry partners.

**Prevention**: Continuous integration with leaked-credential feed; passkey promotion campaign;
periodic forced password reset for accounts with passwords matching known-breach lists.

---

### Scenario 2: SIM Swap Leading to Account Takeover

**Trigger**: Attacker social-engineers a carrier store employee to port victim's phone number
to a new SIM. Within 20 minutes, attacker requests SMS-based password reset, receives the
OTP, resets the password, and disables 2FA — completing the takeover before the victim notices.

**Timeline**:
- T+0: SIM swap completed at carrier.
- T+8m: Attacker requests password reset via SMS.
- T+9m: OTP received on attacker's device.
- T+11m: Password reset completed; new session created.
- T+14m: 2FA phone number changed to attacker's number.
- T+20m: Victim loses account access entirely.

**Detection**:
- Phone number change event logged; if followed by password reset within 30 minutes, anomaly
  score elevated automatically.
- Account risk score spike on combination of: new device + new IP + phone number change + 2FA
  change within 30-minute window.

**Mitigation**:
1. **48-hour phone number lock**: After a phone number is associated with an account, it cannot
   be used for authentication for 48 hours.
2. **Parallel notification**: When a phone number changes, email the previous address with an
   "undo" link valid for 72 hours.
3. **High-risk action cooldown**: Password reset and 2FA changes within 1 hour of a phone
   number change require secondary verification (email + government-ID selfie match).
4. **Authenticator-app 2FA promotion**: Strongly recommend migration from SMS to TOTP or
   WebAuthn during account setup and in periodic security checkup prompts.

**Recovery**:
- Provide a dedicated account recovery path for SIM-swap victims requiring ID verification.
- Maintain a 30-day session history log so legitimate owner can confirm last real activity.
- Restore original account state from audit log; revoke all sessions created after the event.

**Prevention**: Carrier partnership for SIM-swap notification API (available from major US
carriers); allow users to enable a "SIM-swap lock" flag that blocks SMS-based recovery entirely.

---

### Scenario 3: Real-Time 2FA Phishing Relay

**Trigger**: A targeted phishing site mimics the platform's login page with a valid TLS
certificate. The attacker's site acts as a reverse proxy: victim enters credentials and 2FA
code, which are immediately relayed to the real site before the TOTP window expires. The
attacker captures a valid authenticated session cookie.

**Detection**:
- Session established from IP/device fingerprint inconsistent with 2FA initiation context.
- Behavioral biometrics: login completion time from 2FA send to success is <3 seconds (humans
  typically take 8–30 seconds); automated relay timing is detectable.
- Phishing domain flagged by Google Safe Browsing or industry threat feeds.

**Mitigation**:
1. **WebAuthn/Passkey**: The credential is bound to the legitimate domain; a phishing domain
   cannot complete WebAuthn authentication, making relay impossible.
2. **Session context binding**: Session token is bound to the TLS channel; replayed on a
   different connection is detected and invalidated.
3. **Login risk scoring**: Unusually fast 2FA completion triggers a secondary email
   verification challenge.
4. **Phishing domain takedown**: Integrate with domain registrar abuse APIs and Google Safe
   Browsing for rapid takedown requests.

**Prevention**: Make passkey enrollment a prominent default during account setup; show a
security checklist in account settings with passkey enrollment as the top recommendation.
