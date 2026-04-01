# Hotel Property Management System — Edge Cases: Security and Compliance

## Overview

Security and compliance edge cases represent the highest-stakes failures in any PMS. Unlike a double booking or a housekeeping delay, a PCI-DSS breach or a GDPR data exposure can result in regulatory fines measured in millions of euros, criminal liability for individuals, and permanent loss of the hotel brand's reputation. This file documents six categories of security and compliance edge cases with emphasis on regulatory implications, mandatory notification timelines, containment procedures, forensic requirements, and long-term preventive controls. Every section in this file should be treated as an input to the hotel's Information Security Management System (ISMS) and Data Protection Impact Assessment (DPIA).

---

## EC-SEC-001 — PCI-DSS: Cardholder Data Exposure in Logs

*Category:* Security and Compliance
*Severity:* Critical
*Likelihood:* Medium (log sanitisation gaps are among the most common PCI audit findings)
*Affected Services:* LoggingService, PaymentService, APIGateway, AuditService

**Description**
A debug log entry, error message, or API request/response trace inadvertently includes full Primary Account Number (PAN), Card Verification Value (CVV/CVC), or full magnetic stripe data. This violates PCI-DSS Requirement 3.2 (do not store sensitive authentication data after authorisation) and Requirement 3.4 (render PAN unreadable anywhere it is stored). Once cardholder data exists in application logs, it may be indexed by log aggregation systems (Elasticsearch, Splunk, Datadog), retained on disk, and accessible to any engineer with log access — dramatically expanding the scope of the cardholder data environment (CDE) and the PCI audit surface.

**Trigger Conditions**

1. A payment-related exception is thrown and the exception includes the raw payment request object (which contains the PAN).
2. An API gateway access log records the full request body of a `/payment/charge` endpoint without field-level redaction.
3. A developer adds a temporary debug log `logger.debug("Payment request: {}", paymentRequest.toString())` that includes the card number.
4. A third-party library logs payment objects during an error condition without the hotel's sanitisation layer intercepting it.

**Expected System Behaviour**

1. `LoggingService` applies a PAN sanitisation interceptor to all log events before writing to disk or transmitting to a log aggregator. The sanitiser scans log message strings for patterns matching: 13–19 digit sequences that pass the Luhn algorithm check, and replaces them with `****-****-****-{last4}`.
2. CVV/CVC fields (`cvv`, `cvc`, `security_code`) are fully redacted (replaced with `[REDACTED]`) — they may never appear in logs under any circumstances.
3. Payment request objects implement a `toSafeString()` method that returns a masked representation. `toString()` is overridden to call `toSafeString()` to prevent accidental exposure via `logger.debug("{}", object)` patterns.
4. Static analysis rules in the CI/CD pipeline reject any code that calls `logger.debug` or `logger.info` with an object of type `PaymentRequest`, `CardDetails`, or any class annotated `@ContainsSensitiveData`.

**Regulatory Implications**
- **PCI-DSS Requirement 3.2:** Sensitive authentication data must not be stored after authorisation. CVV in logs — even briefly — is a clear violation.
- **PCI-DSS Requirement 10:** Audit logs of all access to cardholder data must be maintained. If cardholder data is in the log, the log itself becomes part of the CDE and must be protected with the full set of PCI controls.
- **Notification:** If cardholder data exposure is confirmed, the hotel's Acquiring Bank must be notified immediately (within hours, not days). The bank will initiate a PCI forensic investigation.

**Immediate Containment Steps**

1. **Detect:** Automated scanning of log ingestion pipeline for PAN patterns. Alert: `PCIDataInLog` — fires within 5 minutes of a matching log entry being indexed.
2. **Isolate:** Immediately suspend the log stream to all external aggregators (Datadog, Splunk). Stop new data flowing out of the controlled environment.
3. **Purge:** Identify all log files/indices containing the exposed data. Delete or overwrite the specific log lines. Document the purge with timestamps and method.
4. **Scope Assessment:** Determine which systems received the log data: disk, log forwarders, SIEM, third-party services. Each system must be individually reviewed and purged.
5. **Notify:** Inform the CISO, Legal, and the Acquiring Bank within 24 hours. If a forensic investigation confirms data was accessible externally, card schemes (Visa/Mastercard) must also be notified.

**Forensic Audit**
1. Preserve the original log files (with hashing for chain of custody) before purging.
2. Determine the first occurrence of PAN in logs: `grep -rn "[0-9]{13,19}" /var/log/app/ | luhn_validate | first_match_timestamp`.
3. Identify whether any external system ingested the logs containing PAN.
4. Determine the scope of affected cardholders (which PANs were exposed).
5. Prepare a forensic report for the Qualified Security Assessor (QSA).

**Remediation**
1. Deploy the PAN sanitiser to all log pipelines.
2. Override `toString()` on all payment-related classes.
3. Add static analysis rules to the CI/CD gate.
4. Rotate all API credentials and encryption keys used by the affected payment components.
5. Conduct a full PCI log audit for the 3 months prior to detection.

**Preventive Controls**
- Tokenise all card data at the point of entry (tokenisation service handles the raw PAN; the PMS never sees it).
- Use a dedicated, firewalled cardholder data environment (CDE). Application logs from the CDE are stored separately with access restricted to PCI-authorised personnel.
- Quarterly PCI log review as part of the regular security audit programme.

**Test Cases**
- *TC-1:* A payment exception is thrown with a raw `PaymentRequest` object. Assert the log entry contains `****-****-****-4242` and not the full PAN.
- *TC-2:* A developer submits code with `logger.debug("card: {}", cardDetails)`. Assert the CI/CD pipeline rejects the PR with a static analysis error.
- *TC-3:* The PAN scanner detects a matching pattern in a log line. Assert the `PCIDataInLog` alert fires within 5 minutes.

---

## EC-SEC-002 — GDPR: Unauthorised Access to Guest Personal Data

*Category:* Security and Compliance
*Severity:* Critical
*Likelihood:* Medium
*Affected Services:* AuthService, AuditService, GuestProfileService, DataProtectionService

**Description**
A hotel staff member (or a compromised staff account) accesses guest personal data — name, date of birth, passport number, credit card details, stay history, dietary preferences, health-related special requests — without a legitimate operational reason. This constitutes a personal data breach under GDPR Article 4(12) if the access was unauthorised or if data was exfiltrated. It may also constitute a violation of the hotel's own data minimisation policies. The severity escalates immediately if the data is exfiltrated, shared externally, or if the access pattern suggests systematic reconnaissance rather than an isolated mistake.

**Trigger Conditions**

1. A staff member accesses guest profile records at a rate significantly above their baseline (e.g., a receptionist who normally accesses 20 profiles per day suddenly accesses 500 in one session).
2. A staff member accesses profiles of guests who have no current or upcoming reservation (no legitimate operational reason).
3. A staff member accesses fields beyond their role permissions (e.g., a housekeeping staff accessing billing information or passport scans).
4. A system-level integration credential is used to query guest data in bulk without a corresponding operational trigger.

**Expected System Behaviour**

1. `AuditService` logs every access to guest personal data: `{user_id, role, action, resource_type, resource_id, fields_accessed, timestamp, ip_address, session_id}`.
2. `DataProtectionService` runs a behavioural anomaly detection job every 15 minutes: flags any user whose data access rate exceeds 3× their 30-day rolling average, or who accesses guest profiles outside their assigned property.
3. On anomaly detection: `UnauthorisedDataAccess` alert is sent to the Data Protection Officer (DPO) and CISO. The user's session is not immediately terminated (to avoid alerting the potential insider threat) — instead, enhanced logging is applied and a supervisor is discreetly notified.
4. Within 30 minutes of the alert: the DPO reviews the access logs and makes a determination. If confirmed as unauthorised: the user's credentials are suspended immediately.

**Regulatory Implications — GDPR**
- **72-Hour Notification:** Under GDPR Article 33, if the breach is likely to result in a risk to individuals' rights and freedoms, the supervisory authority must be notified within 72 hours of the hotel becoming aware of the breach.
- **Individual Notification:** Under GDPR Article 34, if the breach is likely to result in a high risk to individuals, each affected guest must be notified "without undue delay."
- **Record of Processing Activity (ROPA):** The breach must be documented in the hotel's ROPA under Article 30, regardless of whether it is reported to the authority.
- **Fines:** Up to €20 million or 4% of global annual turnover (whichever is higher) for serious breaches.

**Immediate Containment Steps**

1. Suspend the user account immediately upon confirmation of unauthorised access.
2. Preserve all audit logs related to the user's activity (do not purge, even if purge is part of a normal retention cycle).
3. Run a full export of all records accessed by the user in the past 30 days.
4. Determine whether data was exfiltrated: check for bulk export operations, email attachments, USB access, or external API calls from the user's session.
5. Notify the DPO within 1 hour of confirmation.

**72-Hour GDPR Notification Protocol**
- Hour 0–4: Internal confirmation and scope assessment.
- Hour 4–24: DPO drafts the supervisory authority notification. Information required: nature of the breach, categories and approximate number of individuals affected, name and contact of the DPO, likely consequences, measures taken.
- Hour 24–48: Legal review of the notification.
- Hour 48–72: Submit the notification to the relevant supervisory authority (e.g., ICO in the UK, CNIL in France).

**Forensic Audit**
1. Export the full audit trail for the compromised user account for the past 90 days.
2. Identify all guest records accessed, the fields viewed, and the time of access.
3. Determine whether any accessed records were modified, exported, or shared.
4. Cross-reference with any external data breach reports (dark web monitoring) for the hotel's guest data.

**Remediation**
1. Implement role-based access control (RBAC) with field-level permissions: housekeeping can see room assignments but not payment data or passport information.
2. Apply data minimisation: staff should only be able to access the minimum data necessary for their operational role.
3. Add a justification prompt for any access to sensitive fields (passport, DOB, payment token) outside of a current check-in/checkout operation.

**Test Cases**
- *TC-1:* User accesses 500 guest profiles in 1 hour (baseline: 20/day). Assert anomaly detection fires and DPO is notified.
- *TC-2:* Housekeeping role attempts to access guest billing data. Assert the request is rejected with HTTP 403 and an audit log entry is created.
- *TC-3:* Bulk export of guest data via API without an operational trigger. Assert the export is blocked and an alert fires.

---

## EC-SEC-003 — Physical Security: Keycard Master Key Compromise

*Category:* Security and Compliance
*Severity:* Critical
*Likelihood:* Rare
*Affected Services:* KeycardService, SecurityService, RoomService, AuditService

**Description**
A master keycard (which opens all rooms in the property, or all rooms on a floor) is lost, stolen, or cloned. A master key compromise is one of the most severe physical security incidents in hotel operations because it provides unrestricted access to all guest rooms. The response must be immediate, coordinated between digital and physical security systems, and must not create alarm among guests who are currently in their rooms.

**Trigger Conditions**

1. A staff member reports a master keycard lost or stolen.
2. Keycard access logs show the master key being used in a pattern inconsistent with the assigned staff member's shift (e.g., room accesses at 03:00 by a housekeeper whose shift ended at 18:00).
3. A guest reports a room entry by an unknown individual while the guest was in the room.
4. Physical evidence of keycard cloning equipment is discovered.

**Expected System Behaviour**

1. Security Manager immediately issues a keycard revocation: `POST /keycard/revoke {card_serial: "MASTER-FLOOR-3", reason: "LOST/COMPROMISED", revoked_by: "security_manager_id"}`.
2. KeycardService broadcasts the revocation to all lock controllers within 60 seconds via the hotel's lock management system. The compromised keycard is now denied access at every door.
3. Security Manager reviews the access log for the compromised card: `GET /keycard/access-log?card_serial=MASTER-FLOOR-3&since=T-24h`.
4. Any room that was accessed by the compromised card when no staff work order was open for that room is flagged as `POTENTIAL_UNAUTHORIZED_ENTRY`.
5. Security staff physically visits each flagged room (calling from outside the door first) to verify guest safety.
6. Guests in affected rooms are offered a complimentary room change as a precaution.
7. New master keycards are encoded with a new key generation, invalidating all previously encoded cards for that master key group.
8. The incident is reported to local law enforcement if theft or criminal intent is suspected.

**Notification Obligations**
- If any guest experienced an unauthorised room entry: that guest must be informed immediately, regardless of hour.
- If the incident involves evidence of physical harm or theft from a guest room: law enforcement must be contacted immediately.
- If guest personal data or valuables were potentially accessed by the intruder: GDPR notification procedures (EC-SEC-002) may also apply.

**Forensic Audit**
1. Preserve all keycard access logs before any system changes.
2. Timeline reconstruction: identify every room accessed by the compromised card in the past 24 hours.
3. Cross-reference with room occupancy records to identify which rooms were occupied when the card was used.
4. Interview the staff member assigned to the card about its last known location.
5. Review CCTV footage near any flagged room access.

**Preventive Controls**
- Master keycards should be logged in and out of a physical key safe at the start and end of each shift.
- Master keycards should expire at the end of each shift (daily re-encoding with a new key).
- Access logs for master keycards should be reviewed by Security Manager at the end of every shift.
- Master keycards should never leave the hotel premises.

**Test Cases**
- *TC-1:* Master keycard is reported lost. Assert revocation is broadcast to all lock controllers within 60 seconds.
- *TC-2:* Access log shows master card used at 03:00 by a housekeeper whose shift ended at 18:00. Assert an anomaly alert fires and Security Manager is notified.
- *TC-3:* New master keycards are encoded after a compromise. Assert the old card serial no longer grants access to any door.

---

## EC-SEC-004 — Payment Card Tokenisation Service Unavailable

*Category:* Security and Compliance
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* TokenisationService, PaymentService, CheckInService, CheckoutService

**Description**
The hotel uses a tokenisation service (a dedicated PCI-DSS Level 1 certified vault) to replace raw PANs with non-sensitive tokens before the PMS stores or processes them. When the tokenisation service is unavailable, the hotel cannot safely accept new credit card information — because storing a raw PAN in any non-CDE system is a PCI violation. Check-ins that require a new card guarantee and checkouts that require a new card payment are blocked.

**Trigger Conditions**

1. `TokenisationService.tokenise(pan)` returns a 503 or times out.
2. The tokenisation service API is unreachable.

**Expected System Behaviour**

1. Circuit breaker on `TokenisationService` opens after 3 failures.
2. `CheckInService` and `CheckoutService` receive a `TOKENISATION_UNAVAILABLE` state notification.
3. For check-in: the system prompts the agent to complete check-in without a credit card guarantee for now, using a `DEFERRED_GUARANTEE` flag. The guest is asked to provide their card at checkout.
4. For checkout: if the guest has an existing valid token on file, checkout proceeds normally. If no valid token exists and a new card must be processed, the checkout is flagged as `MANUAL_PAYMENT_REQUIRED` and the agent uses the hotel's standalone (offline) card terminal (not connected to the PMS) to process the payment.
5. All manual payment references are entered into the folio as `OFFLINE_PAYMENT_REF` entries.
6. `TokenisationServiceDown` alert fires — severity Critical. IT support team is paged.

**PCI Implications**
- Under no circumstances should the raw PAN be stored in the PMS database as a fallback. The correct response is to defer the tokenisation until the service recovers.
- Manual card terminals (physical POS devices with their own PCI-compliant processing) are the approved fallback.

**Recovery Procedure**
1. Restore the tokenisation service.
2. Process all `DEFERRED_GUARANTEE` reservations: prompt agents to collect card details and tokenise via the recovered service.
3. No retroactive tokenisation of raw PANs is necessary because no raw PANs were stored.

**Test Cases**
- *TC-1:* Tokenisation service returns 503. Assert check-in proceeds with DEFERRED_GUARANTEE flag and no raw PAN is written to the database.
- *TC-2:* A guest with an existing token checks out. Assert checkout proceeds normally without calling the tokenisation service.
- *TC-3:* Tokenisation service recovers. Assert DEFERRED_GUARANTEE reservations are surfaced in the daily agent task queue.

---

## EC-SEC-005 — Privileged Account Misuse (Manager Override Abuse)

*Category:* Security and Compliance
*Severity:* High
*Likelihood:* Medium
*Affected Services:* AuthService, AuditService, FolioService, ComplianceService

**Description**
Hotel PMS systems include manager override capabilities: supervisors can waive charges, apply discounts, access closed folios, and override system restrictions. These capabilities are necessary for legitimate operational reasons but can be abused — intentionally (fraud, embezzlement) or unintentionally (approving a waiver without understanding the financial impact). EC-SEC-005 documents the detection and response framework for manager override anomalies.

**Trigger Conditions**

1. A supervisor account applies a number of discounts or voids in a single shift that significantly exceeds the property average.
2. A supervisor applies overrides that consistently benefit a specific set of guests (suggesting a relationship or kickback scheme).
3. Overrides are applied outside of business hours without a corresponding shift record.
4. A supervisor override is applied to their own folio (clear conflict of interest).

**Expected System Behaviour**

1. `AuditService` logs every override: supervisor ID, guest ID, folio ID, action type, amount, timestamp, reason code.
2. `ComplianceService` runs a weekly override analysis:
   - Flag any supervisor with an override value > 2× the property average for the week.
   - Flag any supervisor who applied overrides to their own personal folios.
   - Flag any supervisor with a pattern of overrides to the same guest or the same group of guests.
3. Weekly override report is sent to the General Manager and Financial Controller.
4. Any anomalous override triggers a `ManagerOverrideAnomaly` alert to the GM and Financial Controller.

**Immediate Containment Steps**
1. Suspend the supervisor's override privileges pending investigation (not their entire account — they still need to work).
2. Review all overrides applied by the account in the past 90 days.
3. Calculate the financial impact: total value of overrides applied.
4. Determine whether any overrides were applied in error (can be reversed) or intentionally (must be escalated to HR and potentially law enforcement).

**Forensic Audit**
1. Pull all override audit logs for the flagged account.
2. Cross-reference override recipients with staff personal relationships (family members, known associates).
3. Review CCTV of the front desk at the times of suspicious overrides.
4. Compare folio adjustments with the property's daily revenue report.

**Preventive Controls**
- Dual control for overrides above a threshold: any override > $200 requires a second supervisor's approval.
- Supervisors cannot apply overrides to folios where they are listed as the booking agent.
- All override reasons must be selected from a defined list (no free-text reasons for high-value overrides).
- Quarterly override audit as part of the financial control programme.

**Test Cases**
- *TC-1:* Supervisor applies 50 voids in one shift (average: 5). Assert ManagerOverrideAnomaly alert fires.
- *TC-2:* Supervisor applies a $300 override without a second approval. Assert the override is blocked and an approval request is created.
- *TC-3:* Supervisor attempts to apply an override to their own folio. Assert the action is blocked with error `SELF_OVERRIDE_PROHIBITED`.

---

## EC-SEC-006 — Data Retention Violation (Guest Data Not Purged)

*Category:* Security and Compliance
*Severity:* High
*Likelihood:* Medium
*Affected Services:* DataRetentionService, GuestProfileService, FolioService, AuditService

**Description**
GDPR and many national privacy laws require that personal data not be retained beyond the purpose for which it was collected. For hotel guest data, this typically means: guest profile data (name, contact, preferences) is retained for the duration of the relationship plus a defined period (e.g., 3 years after last stay). Folio and financial data is retained for the accounting retention period (typically 7 years). Sensitive identity documents (passport scans, ID photos) are typically retained for a shorter period (30 days after checkout, or the duration required by the local registration law). A retention violation occurs when any of these categories of data persist beyond their configured retention deadline.

**Trigger Conditions**

1. `DataRetentionService` scheduled purge job fails to run (due to infrastructure issue or code error).
2. A retention policy is incorrectly configured (e.g., passport scan retention is set to 10 years instead of 30 days).
3. A data category is not covered by any retention policy (a gap in the data inventory).
4. A guest requests deletion of their data under GDPR Article 17 (Right to Erasure), and the request is not fulfilled within 30 days.

**Expected System Behaviour**

1. `DataRetentionService` runs a nightly job that:
   - Queries each data category against its configured retention rule.
   - Marks expired records as `SCHEDULED_FOR_DELETION`.
   - After a 24-hour grace period (for dispute resolution), permanently deletes or anonymises the records.
   - Writes a deletion log entry: `{data_category, record_id_hash, deletion_timestamp, retention_policy_applied}`.
2. Right to Erasure requests are handled via `GuestProfileService.delete_profile(guest_id, requester_email, request_date)`. The service:
   - Validates the requester's identity.
   - Deletes personal identifiers from the guest profile (name, email, phone, address, DOB, loyalty number).
   - Retains anonymised stay history and financial records (for accounting purposes) with the guest identity replaced by a pseudonymous ID.
   - Sends a confirmation email to the requester within 30 days.
3. If the purge job fails, a `DataRetentionJobFailure` alert fires, and the Finance Controller and DPO are notified.

**Regulatory Implications**
- Retaining personal data beyond its purpose violates GDPR Article 5(1)(e) (storage limitation principle).
- Failing to respond to a Right to Erasure request within 30 days violates GDPR Article 12(3).
- Supervisory authorities can investigate and fine: up to €20 million or 4% of global annual turnover.

**Data Retention Schedules**

| Data Category | Retention Period | Legal Basis |
|---------------|-----------------|-------------|
| Guest personal profile | 3 years after last stay | Legitimate interest (loyalty, service continuity) |
| Financial records (folios, invoices) | 7 years | Accounting law (varies by jurisdiction) |
| Passport/ID scans | 30 days after checkout (or duration required by local law) | Legal obligation (immigration registration) |
| Keycard access logs | 90 days | Security interest |
| CCTV footage | 30 days | Security interest |
| Marketing preferences | Until withdrawn consent or erasure request | Consent |

**Remediation**
1. Fix the retention job failure.
2. Run a manual purge for all records that exceeded their retention deadline during the outage period.
3. Document the overretention in the ROPA.
4. Assess whether any data subject is likely to have experienced harm due to the overretention.

**Prevention**
- Data retention job must have a dead man's switch: if it does not run by 04:00, a P1 alert fires.
- All new data categories added to the system must have a retention policy configured before they go to production.
- Quarterly data inventory review: verify the data map is complete and all categories have policies.

**Test Cases**
- *TC-1:* A passport scan is created at checkout. Assert it is scheduled for deletion 30 days later and actually deleted on that date.
- *TC-2:* The retention job fails to run. Assert the alert fires by 04:00 and the DPO is notified.
- *TC-3:* A guest submits a Right to Erasure request. Assert personal identifiers are deleted within 30 days and a confirmation email is sent.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Regulatory Framework | Notification Deadline |
|----|-------|----------|------------|----------|---------------------|----------------------|
| EC-SEC-001 | PCI-DSS Log Exposure | Critical | Medium | P1 | PCI-DSS Req. 3.2, 3.4, 10 | Immediate to acquiring bank |
| EC-SEC-002 | GDPR Unauthorised Data Access | Critical | Medium | P1 | GDPR Art. 33, 34 | 72 hours to supervisory authority |
| EC-SEC-003 | Keycard Master Key Compromise | Critical | Rare | P1 | None mandated; local law if criminal | Immediate to law enforcement (if criminal) |
| EC-SEC-004 | Tokenisation Service Unavailable | Critical | Low | P1 | PCI-DSS Req. 3.4 | N/A (operational, not breach) |
| EC-SEC-005 | Privileged Account Misuse | High | Medium | P2 | Internal financial controls; SOX (if applicable) | Internal HR + Finance within 24 hours |
| EC-SEC-006 | Data Retention Violation | High | Medium | P2 | GDPR Art. 5(1)(e), Art. 17 | 30 days for erasure requests |
