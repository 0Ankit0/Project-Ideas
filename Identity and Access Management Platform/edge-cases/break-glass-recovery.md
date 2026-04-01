# Break-Glass Recovery — Edge Cases

## Introduction

Break-glass access is the last-resort mechanism that grants elevated, time-bounded privileges to
authorized personnel when normal access channels are unavailable or insufficient during a declared
emergency. Because break-glass bypasses standard approval workflows and MFA requirements by design,
it carries the highest risk surface in any IAM platform. Misuse, misconfiguration, or audit failure
during a break-glass event can result in undetected privilege abuse, compliance violations (SOC 2,
ISO 27001, HIPAA), and operational outages.

The scenarios below cover the full break-glass lifecycle: request, approval, access, session
management, audit, and post-incident review. Teams must test these scenarios quarterly in
pre-production and include them in incident response runbooks.

---

## Edge Case Scenarios

| Failure Mode | Trigger Condition | Impact | Detection | Mitigation / Recovery |
|---|---|---|---|---|
| Break-glass token issued but approver account is suspended | Approver account is suspended for an unrelated policy violation at the exact moment the approval fires; the IAM system validates the approval against a cached, stale account status | Token is issued with an invalid approval chain; compliance audit fails because the approving account lacked authority at approval time | Audit log shows approver `account_status = suspended` at `approval_timestamp`; post-issuance integrity check alert fires | Re-validate approver account status synchronously before token issuance; reject approval if account is not `active`; revoke the issued token immediately; open a security incident and require a fresh approval cycle from a valid approver |
| Both required approvers unavailable simultaneously | Quorum approval requires 2-of-N designated approvers; all are unreachable — OOO, attending a concurrent P1 incident, no mobile access | Legitimate emergency is blocked; operations team cannot access production systems during a live outage | Break-glass request status stays `pending_approval` beyond the SLA threshold (15 min); automated escalation fires with no response | Maintain a tiered approver list with at least 3 backup approvers per tier; implement auto-escalation to CISO or VP Engineering after 15-minute no-response; define a documented "break-glass of break-glass" procedure requiring CISO + CEO joint approval for absolute last-resort access |
| Break-glass request submitted with incorrect resource scope | Requestor selects the wrong environment (production vs. staging) or specifies an over-broad wildcard under time pressure | Access granted to unintended systems; potential data exposure or destructive action on the wrong environment | Audit event shows resource ARN or path mismatch vs. incident ticket scope; post-session resource access report flags unrelated systems | Enforce scope pre-validation against the linked incident ticket; require requestor confirmation of the full resource list before approval routing; allow approvers to narrow but never expand scope; alert SIEM in real time on any access outside the approved resource list |
| Approver approves request after the approval window expires | Network delay or inattention causes the approval action to arrive after the configured approval TTL | A stale approval is silently accepted due to a race condition; token is issued on an expired authorization | Token `issued_at` is after `approval_window_expiry`; approval event timestamp exceeds the request `expires_at` field | Treat expired approval windows as hard rejects at the token issuance layer; require the requestor to resubmit; log the late approval attempt as a warning security event; configure approval TTLs by severity tier (5 min P1, 15 min P2) |
| Break-glass credentials used from unexpected geo-location | Requestor works from an approved location (US-East) but credentials are subsequently used from a foreign IP detected after issuance | Possible credential compromise or unauthorized delegation; a fabricated emergency may have enabled real attacker access | IP geolocation anomaly alert during active session; risk engine flags country-code mismatch vs. requestor baseline | Require geo-location confirmation at session activation, not only at issuance; trigger step-up challenge (push MFA, TOTP) on geo deviation; auto-suspend session pending re-verification; page on-call security analyst immediately |
| Concurrent break-glass requests for the same resource from different requestors | Two engineers independently declare an emergency for the same production database and both submit break-glass requests simultaneously | Both tokens are issued; two actors with elevated access act independently and may conflict on remediation; audit trail is ambiguous | System detects two active break-glass sessions for the same resource ARN within the same time window; concurrent-session high-risk alert fires | Implement resource-level session lock: second request is queued and requestor is notified a peer is already active; require second requestor to join existing session or justify parallel session to an approver; log dual-session activation as a high-risk event requiring mandatory security review |
| Break-glass session exceeds approved time window and auto-expiry fails | Session TTL enforcement relies on a background job; the job crashes or Redis key eviction removes the expiry record before the background job fires | Session remains active indefinitely; requestor retains elevated access long after the emergency is resolved | Session `last_heartbeat` diverges from `approved_end_time` by more than the grace period; monitoring alert on sessions older than `approved_end_time + 5 min` | Implement dual-layer expiry: Redis TTL (hard eviction) plus background job (graceful termination); treat absent Redis key as expired; run daily audit query for sessions where `actual_end > approved_end`; any overage above 5 minutes generates a SIEM P1 alert |
| Requestor attempts to escalate scope during an active session | While in an active break-glass session the requestor submits API calls targeting resources outside the originally approved scope | Unauthorized access to resources not covered by the incident; potential lateral movement within the production environment | PEP enforcement logs request to an out-of-scope resource ARN; SIEM alert on any resource not in the session `approved_resources` list | PEP enforces the scope allowlist on every request throughout the session, not only at activation; return HTTP 403 with `reason: scope_exceeded`; alert approver and security team in real time; auto-terminate session after 3 out-of-scope attempts |
| Audit trail write fails during active break-glass access | Audit log store (OpenSearch, S3, or Splunk HEC) is unavailable due to network partition or disk-full condition; audit events are dropped or delayed | Complete loss of the privileged-action audit record; compliance audit failure; forensic blind spot for the entire session duration | Audit write error rate exceeds 0% during any break-glass session; audit sink health check fails; dead-letter queue depth grows | Buffer audit events in a local durable write-ahead log; retry with exponential backoff for up to 10 minutes; if local buffer fills, fail-closed by suspending the break-glass session; alert security team immediately; all buffered events must be flushed and reconciled before session is marked complete |
| Break-glass account credential compromised after issuance | Requestor device is compromised (malware, keylogger) while break-glass credentials are active; attacker exfiltrates the token or one-time password | Attacker gains full production access under cover of a legitimate emergency; forensic attribution is confused | Concurrent session detected from two distinct IPs for the same token; behavioral anomaly — commands outside typical remediation pattern (data exports, permission changes) | Bind break-glass tokens to device fingerprint and IP at issuance; invalidate immediately on IP change; implement command-level SIEM alerting for destructive operations (DROP, DELETE, rm -rf, COPY TO); page security on concurrent-session detection |
| Break-glass session active during primary authentication service outage | Auth service goes down while a break-glass session is in progress; normal session validation can no longer be performed | Requestor locked out of break-glass session mid-remediation, blocking incident resolution; or conversely, session cannot be terminated because auth service is down | Auth service health check fails; session heartbeat cannot reach validation endpoint; support ticket volume spikes | Break-glass tokens must be self-contained signed JWTs validated locally at the PEP without requiring a live auth service call; session termination must also be possible via an out-of-band administrative CLI that bypasses the auth service entirely |
| Requestor forgets to terminate the break-glass session after resolution | Emergency is resolved but requestor leaves session open; elevated access persists beyond operational need | Unnecessary prolonged exposure to emergency-level privileges; any subsequent accidental or malicious action is performed with elevated rights | Session heartbeat active past `incident_resolved_at`; session age exceeds the approved duration | Auto-expire sessions at approved TTL plus 5-minute grace; send reminder notifications at 5 minutes and 2 minutes before auto-expiry; require explicit session close with a resolution summary; enforce post-session checklist before status transitions to `complete` |
| Break-glass used for non-emergency routine operations (abuse) | Engineer submits break-glass requests to bypass change management or approval workflows as a matter of convenience | Erodes the integrity of the emergency access control; creates compliance findings; audit history loses signal value for detecting real emergencies | Low-severity incident tickets linked to break-glass events; per-user break-glass frequency exceeds organizational baseline; sessions during business hours for non-critical operations | Require mandatory incident ticket linkage with automated severity validation (reject if ticket severity is lower than P2); alert security when a user's monthly frequency exceeds 2; include all break-glass usage in quarterly access reviews; require manager acknowledgment for every use |
| Break-glass approval notification email delivery failure | Email infrastructure is degraded or notification is blocked by a spam filter; designated approver never receives the request | Approval is delayed indefinitely; a legitimate emergency is blocked; requestor has no visibility into the delivery failure | Approval notification delivery status is `failed` or unacknowledged; request remains `pending_approval` beyond SLA; no read receipt from any notification channel | Implement multi-channel notification (email + Slack + PagerDuty + SMS) with independent delivery confirmation; require at least one channel to confirm delivery before marking the notification as sent; auto-escalate to the next approver tier if primary approver notification fails within 3 minutes |
| Break-glass credentials shared with an unauthorized party via social engineering | Under time pressure, requestor verbally shares a one-time token or password with a colleague not on the approved list | Access by an unauthorized person; all actions are attributed to the requestor in the audit log; the actual actor has plausible deniability | IP geolocation divergence mid-session; command patterns inconsistent with requestor historical skillset; second device login detected for the same session | Bind credentials to hardware token or FIDO2 key that cannot be verbally shared; deliver just-in-time credentials only to an MFA-verified device; audit command patterns against requestor UEBA baseline and alert on significant deviations |
| Post-incident break-glass report never generated | Break-glass session closes but the automated report generation job fails or is never triggered; no post-mortem record is created | Compliance gap; repeated misuse patterns go undetected; audit evidence is incomplete for SOC 2 Type II and ISO 27001 assessments | Report generation job failure alert; sessions with `status = complete` and `report_id = null` after 24 hours appear in daily reconciliation query | Auto-generate report within 1 hour of session close; block session from transitioning to `archived` until report is generated and acknowledged by security team; run daily reconciliation query to find sessions missing reports and alert the compliance team |
| Break-glass activity not correlated with an incident ticket | Access event logs record a break-glass session but the linked incident ticket has been deleted or closed before session end; no traceable justification exists | Orphaned access event; compliance finding; possible evidence of unauthorized access disguised as an emergency | Broken foreign key between `break_glass_session.incident_ticket_id` and ticket system; ticket status is `closed` while session is still active | Enforce referential integrity at session creation; validate ticket is open and `in_progress` before token issuance; archive ticket reference immutably in the audit record at session start; reject session creation if the referenced ticket is already resolved or deleted |
| Emergency contact list contains deprovisioned approvers | An approver listed in the break-glass configuration left the organization or changed roles; account is deprovisioned but configuration is not updated | All approval notifications go to deprovisioned accounts; no valid approver can respond; a live emergency is blocked until manual intervention | Approval requests time out; approver accounts in config return inactive status during notification delivery | Reconcile break-glass approver lists against active directory or SCIM weekly via automated job; alert immediately when any approver account becomes inactive; require quarterly re-certification of break-glass configuration; enforce a minimum of 3 active approvers per resource tier at all times |
| Break-glass account MFA device lost or broken | Engineer declares an emergency but their registered TOTP device or hardware key is unavailable — lost phone, broken YubiKey | Cannot complete MFA step to activate break-glass; legitimate emergency is blocked entirely | MFA authentication failure at break-glass activation; requestor escalates to verbal authorization channels | Pre-register at least two backup MFA methods per user (backup TOTP codes stored in a password manager plus a secondary hardware key); define a documented exception process requiring dual-person verbal authorization with mandatory post-event security review; distribute on-call hardware backup keys to team leads |
| Break-glass access used while audit store is in scheduled maintenance | DBA schedules maintenance on the audit database at the same time a production emergency requires break-glass access | Audit events cannot be written; compliance evidence is missing for the entire session duration; maintenance window creates a forensic blind spot | Audit sink health check fails at session activation; write attempts return connection-refused; dead-letter queue fills rapidly | Block break-glass activation if audit store is in known degraded state unless CISO explicitly overrides with dual-person authorization; route audit events to secondary sink (S3 fallback via Firehose) during maintenance windows; require all planned maintenance windows to be registered in the IAM platform scheduled-degradation calendar |

---

## Break-Glass Abuse Detection Patterns

Abuse of break-glass is among the most damaging insider threat vectors because the mechanism is
designed to bypass controls. Detection requires behavioral analytics layered over structural audit
logs.

### Frequency Anomaly
Alert when a single user account submits more than two break-glass requests within a 30-day rolling
window. Legitimate emergencies are rare; repeated use indicates convenience-driven abuse or an
insider threat actor probing the limits of the control.

### Time-of-Day Correlation
Break-glass events during business hours without a corresponding P1 or P2 incident ticket are a
strong abuse signal. Correlate session start time with incident management system severity and
ticket creation timestamp. A break-glass event initiated more than 15 minutes before a ticket is
created is also suspicious — it suggests post-hoc justification.

### Scope Deviation Analysis
Compare every resource accessed during the session against the approved scope allowlist. Any access
to a resource not in the approved list must generate a P1 SIEM alert even if the PEP rejected the
call, because the attempt itself is evidence of misuse or testing.

### Command Pattern Analysis
For break-glass sessions that include shell or database access, capture and analyze command
sequences via session recording. Flag patterns inconsistent with incident remediation: enumeration
commands (ls -laR, SHOW TABLES, DESCRIBE), data export operations (mysqldump, COPY TO, aws s3 cp),
or permission modifications (GRANT, chmod 777, adduser).

### Session Duration Outliers
Calculate the 95th-percentile of historical break-glass session durations across all resolved
incidents. Alert when any active session exceeds that duration by more than 20%. Long sessions
correlate with scope creep or a requestor using the session for purposes beyond the declared
emergency.

### Concurrent Session Detection
A single break-glass token must never produce activity from more than one IP address or device
simultaneously. Concurrent session detection must be implemented at the session validation layer on
every request, not only at token issuance.

---

## Runbook: Emergency Access Activation

**Step 1 — Declare Emergency**
Submit a break-glass request via the IAM portal or CLI:

```
iam-cli bg request \
  --resource <resource-arn> \
  --justification "<text describing the emergency>" \
  --ticket <INC-ID> \
  --duration 60m
```

The request must reference an open incident ticket with severity P1 or P2. Requests linked to
tickets with severity P3 or lower are rejected automatically.

**Step 2 — Approver Notification**
The system delivers approval requests simultaneously via Slack DM, PagerDuty push notification,
and email. Approvers have 10 minutes to respond before automatic escalation to the next tier.
The requestor sees live delivery confirmation status on the request page.

**Step 3 — Scope Confirmation**
Before token issuance, the approver reviews and confirms or narrows the resource scope. The
approver may reduce scope but may not expand it beyond what the requestor originally specified.
Scope confirmation is recorded as a separate, immutable audit event.

**Step 4 — Credential Delivery**
A time-bounded credential (short-lived JWT or one-time password) is delivered to the requestor's
MFA-verified device only. Credentials are bound to the requestor's registered IP range and device
fingerprint captured at delivery time.

**Step 5 — Active Session Monitoring**
All commands and API calls within the break-glass session are streamed to the SIEM in real time.
The security team is automatically paged if out-of-scope resource access is detected or if command
patterns match the destructive-operation watchlist.

**Step 6 — Session Termination**
The requestor explicitly terminates the session:

```
iam-cli bg close --session-id <id> --resolution "<summary of what was done>"
```

The session auto-expires at the approved TTL regardless. The resolution summary is included in the
post-use report.

**Step 7 — Post-Use Review**
An automated report is generated within 1 hour of session close and delivered to the security team
and the requestor's direct manager. The report includes: approval chain with timestamps, session
duration, complete resource access list, commands executed (if session recording is enabled), and
any anomalies detected by the SIEM during the session.

---

## Post-Use Checklist

Complete this checklist within 24 hours of every break-glass session closure. The session cannot
transition to `archived` status until all items are marked complete.

- [ ] Session has been explicitly terminated (not left to auto-expire with no close summary)
- [ ] All credentials issued during the session have been rotated or explicitly invalidated
- [ ] Break-glass report has been generated and reviewed by the security team
- [ ] Report is linked to the originating incident ticket in the ticket system
- [ ] All actions taken during the session are documented in the incident post-mortem
- [ ] Scope adherence confirmed — no out-of-scope resource access occurred during the session
- [ ] All SIEM anomalies detected during the session have been triaged and closed or escalated
- [ ] Session duration was within the approved window (no overage beyond 5-minute grace)
- [ ] Requestor manager and security team have acknowledged and signed off on the report
- [ ] Break-glass configuration reviewed if any procedural failure was identified during the event
- [ ] If credentials were shared or a compromise is suspected, a separate security incident is open
- [ ] Audit store confirmed to contain complete, uncorrupted, ordered events for the full session
- [ ] If the emergency contact list was found to be outdated, config has been updated and re-certified
