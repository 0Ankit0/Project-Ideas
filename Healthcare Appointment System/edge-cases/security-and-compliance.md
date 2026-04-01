# Security and Compliance Edge Cases

This document catalogues the ten highest-risk security and regulatory failure modes for the Healthcare Appointment System. Each case follows a structured format covering failure mode, business impact, detection signals, mitigation/recovery steps, and permanent prevention measures. All scenarios are mapped to applicable regulatory frameworks (HIPAA Security Rule, HIPAA Privacy Rule, GDPR, SOC 2 Type II).

---

## Table of Contents

1. [EC-SEC-001: IDOR — Unauthorized Access to Another Patient's Appointment](#ec-sec-001)
2. [EC-SEC-002: Brute-Force Enumeration of Appointment IDs](#ec-sec-002)
3. [EC-SEC-003: PHI Exposure in Application Error Logs](#ec-sec-003)
4. [EC-SEC-004: Privilege Escalation by Front-Desk Staff to Clinical Notes](#ec-sec-004)
5. [EC-SEC-005: Failed HIPAA Audit Trail — Data Export Gap](#ec-sec-005)
6. [EC-SEC-006: GDPR Deletion Conflicting with 7-Year Medical Records Retention](#ec-sec-006)
7. [EC-SEC-007: SQL/NoSQL Injection via Provider Notes or Appointment Reason Fields](#ec-sec-007)
8. [EC-SEC-008: Session Token Not Invalidated After Password Reset](#ec-sec-008)
9. [EC-SEC-009: API Key Leaked in Client-Side JavaScript Bundle](#ec-sec-009)
10. [EC-SEC-010: Third-Party Integration Receiving PHI Without Signed BAA](#ec-sec-010)

---

### EC-SEC-001: Unauthorized Access to Another Patient's Appointment Data via IDOR {#ec-sec-001}

- **Failure Mode:** A patient with a valid session token calls `GET /appointments/{appointmentId}` or `GET /patients/{patientId}/records` using an ID that belongs to a different patient. The API returns the resource if the backend performs no ownership check beyond confirming the resource exists. The attacker can enumerate sequential or UUID-based IDs to harvest appointment details, diagnoses, and provider names for hundreds of patients before the breach is detected.
- **Impact:** Direct HIPAA Privacy Rule violation (45 CFR §164.502). Each unauthorised disclosure of PHI carries a minimum civil penalty of $100 per violation; wilful neglect raises this to $50,000 per record. Reputational damage leads to patient churn estimated at 15–20% post-breach. OCR investigation, mandatory breach notification to affected patients within 60 days, and potential criminal referral for the attacker.
- **Detection:**
  - Monitoring query: `SELECT actor_id, COUNT(DISTINCT patient_id) AS unique_patients_accessed FROM audit_log WHERE action = 'READ_APPOINTMENT' AND timestamp > NOW() - INTERVAL '10 minutes' GROUP BY actor_id HAVING COUNT(DISTINCT patient_id) > 5;`
  - Alert threshold: Any single authenticated user accessing data belonging to ≥ 3 distinct patients within 10 minutes.
  - Log pattern: `[SECURITY] IDOR_ATTEMPT actor=<userId> resource=appointment/<id> owner=<ownerId> requestor≠owner`
  - WAF rule: Flag requests with sequential or UUID-pattern ID scanning from a single IP within a sliding 5-minute window.
- **Mitigation/Recovery:**
  1. Immediately revoke the session token of the suspected actor via `POST /auth/revoke-session` with `actorId` and `reason=IDOR_INVESTIGATION`.
  2. Quarantine the actor account (`account_status = SUSPENDED`) pending security review.
  3. Pull full audit log for the actor for the preceding 30 days; identify all resources accessed that do not belong to the actor.
  4. Generate a breach inventory: list all affected patient IDs, appointment IDs, and PHI fields returned in each response.
  5. Notify the Privacy Officer within 1 hour; initiate OCR breach assessment checklist.
  6. If ≥ 500 patients affected, file OCR breach notification within 60 calendar days and notify prominent media outlets in affected states (45 CFR §164.408).
  7. Patch the vulnerable endpoint before re-enabling the actor's access or the affected endpoint.
- **Prevention:**
  - Enforce a resource ownership assertion in every data-access service method: `if (appointment.patientId !== requestingUser.patientId && !requestingUser.hasRole('PROVIDER', 'ADMIN')) throw ForbiddenException`.
  - Write a parameterised policy check using an Attribute-Based Access Control (ABAC) library (e.g., CASL, OPA) so that ownership is declared at the domain layer, not scattered in controllers.
  - Add integration tests that assert a 403 response when Patient B requests Patient A's resources.
  - Enable OPA/Cedar policy evaluation in CI so that any new endpoint without an explicit ownership policy fails the build.
  - Reference: OWASP API Security Top 10 — API1:2023 Broken Object Level Authorization.

---

### EC-SEC-002: Brute-Force Enumeration of Appointment IDs Exposing Scheduling Patterns {#ec-sec-002}

- **Failure Mode:** Appointment IDs are sequential integers (`/appointments/10001`, `/appointments/10002`, …) or short UUIDs. An unauthenticated or low-privileged attacker iterates through IDs at high speed. Even if the payload returns `404 Not Found` vs `403 Forbidden` inconsistently, the attacker can infer which providers are popular, which time slots are busy, and how many appointments a clinic handles per day — competitive intelligence and a privacy risk.
- **Impact:** Indirect PHI inference (provider specialty, visit frequency) may constitute a HIPAA violation. Enumerating clinic capacity data constitutes trade-secret theft. High-volume enumeration may exhaust API rate quota and degrade service for legitimate users, resulting in appointment booking failures. Business impact: potential 5–10% drop in same-day bookings during an active attack.
- **Detection:**
  - Alert threshold: > 100 requests to `/appointments/{id}` returning 404 from a single IP within 60 seconds.
  - Monitoring query: `SELECT ip_address, COUNT(*) AS attempts, COUNT(CASE WHEN status_code = 404 THEN 1 END) AS misses FROM request_log WHERE path LIKE '/appointments/%' AND timestamp > NOW() - INTERVAL '1 minute' GROUP BY ip_address HAVING attempts > 100;`
  - Log pattern: `[RATE_LIMIT] ENUM_PROBE ip=<ip> path=/appointments/* 404_rate=92% window=60s`
- **Mitigation/Recovery:**
  1. Block the source IP at the WAF/API Gateway layer for 1 hour; escalate to 24-hour block on repeated offence.
  2. Switch all 404 responses for appointment ID lookups to 403 so the response code reveals nothing about existence to unauthenticated callers.
  3. Audit recent 404 responses for the attacking IP to determine if any 200 responses leaked data; treat confirmed leaks as a potential breach.
  4. If an internal account is the source, suspend the account and initiate HR/security review.
- **Prevention:**
  - Generate appointment IDs as non-sequential, cryptographically random UUIDs (v4) or ULID — never auto-increment integers.
  - Apply consistent 403 responses for any resource access without valid ownership, regardless of whether the resource exists (merge existence and authorization checks).
  - Implement IP-level and account-level rate limits at the API Gateway: 60 GET requests per minute per unauthenticated IP, 300 per authenticated user.
  - Add a CAPTCHA step-up challenge after 20 consecutive 403/404 responses from the same session within 5 minutes.

---

### EC-SEC-003: PHI Exposure in Application Error Logs {#ec-sec-003}

- **Failure Mode:** An unhandled exception in the appointment booking service serialises the full `Patient` domain object (including `name`, `dateOfBirth`, `insuranceMemberId`, `diagnosisCodes`) into the stack trace. The stack trace is written to the application log, which is shipped to a centralised log aggregator (e.g., Datadog, Splunk, CloudWatch). Log aggregators may be accessible to DevOps staff who are not authorised to access PHI, violating the minimum-necessary rule.
- **Impact:** HIPAA Security Rule §164.312(a)(2)(iv) requires encryption of PHI at rest, including logs. Unencrypted PHI in logs accessible by non-HIPAA-trained personnel constitutes an impermissible disclosure. Each affected patient record carries a per-violation penalty. Log aggregators operated by third parties must have a signed BAA; if they do not, every log line containing PHI is an additional violation.
- **Detection:**
  - Log pattern scan (run nightly in SIEM): regex match against PHI indicators in log lines — `\b\d{3}-\d{2}-\d{4}\b` (SSN), `\b(DOB|dateOfBirth)\s*[:=]`, `\binsuranceId\b`, patient full-name tokens cross-referenced against patient name list.
  - Alert: Any log event at WARN or ERROR level that matches PHI regex patterns triggers `SEV-2 PHI_LOG_EXPOSURE` alert to the Privacy Officer within 15 minutes.
  - SIEM query: `index=app_logs level IN ("ERROR","WARN") | regex _raw="(?i)(dateOfBirth|ssn|insuranceMemberId|diagnosisCode)" | table _time, service, message`
- **Mitigation/Recovery:**
  1. Immediately purge the offending log lines from all sinks (log aggregator, S3 archive, backup) — retain only a redacted version with an incident reference ID.
  2. Rotate access credentials for the log aggregator if non-PHI-authorised users may have already viewed the data.
  3. Identify patients whose PHI appeared in logs; treat as a potential breach and begin OCR assessment.
  4. Patch the exception handler within 4 hours: replace object serialisation with a safe summary string (`Patient[id=<uuid>, redacted=true]`).
  5. Issue a postmortem with root cause and timeline within 5 business days.
- **Prevention:**
  - Implement a global exception filter (e.g., NestJS `ExceptionFilter`) that catches all unhandled exceptions and logs only: error code, correlation ID, service name, and stack frames (no domain object serialisation).
  - Apply a structured log sanitiser middleware that strips any field matching a PHI field name allowlist before writing to the log sink.
  - Annotate domain model fields with `@Sensitive` and enforce a compile-time rule (ESLint custom rule or ArchUnit) that `@Sensitive` fields are never referenced inside logger calls.
  - Configure log aggregator to mask fields matching PHI patterns at ingestion; enable field-level encryption for the `message` field.
  - Require BAAs with all log aggregation vendors; document in vendor registry.

---

### EC-SEC-004: Excessive Privilege Escalation by Front-Desk Staff Accessing Clinical Notes {#ec-sec-004}

- **Failure Mode:** A front-desk staff member with the `RECEPTIONIST` role discovers that the clinical notes endpoint `GET /appointments/{id}/clinical-notes` returns `200 OK` when called directly (e.g., via Postman or browser dev tools), because the API only checks that the user is authenticated, not that they hold a `CLINICIAN` or `PROVIDER` role. The receptionist can read sensitive diagnoses, medication histories, and mental health notes that they have no operational need to access.
- **Impact:** HIPAA minimum-necessary standard violation (45 CFR §164.502(b)). Clinical notes often include mental health, substance abuse (42 CFR Part 2), and HIV status — all of which carry heightened legal protections. Exposure to a non-clinical employee constitutes a reportable breach. Risk of insider threat: leaked diagnoses used for discrimination, blackmail, or sale. Legal liability under state mental-health confidentiality statutes (e.g., California Welfare and Institutions Code §5328).
- **Detection:**
  - Access anomaly query: `SELECT u.user_id, u.role, COUNT(*) AS clinical_note_reads FROM audit_log al JOIN users u ON al.actor_id = u.user_id WHERE al.resource_type = 'CLINICAL_NOTE' AND al.action = 'READ' AND u.role NOT IN ('CLINICIAN','PROVIDER','ADMIN') AND al.timestamp > NOW() - INTERVAL '24 hours' GROUP BY u.user_id, u.role HAVING COUNT(*) > 0;`
  - Alert: Any `READ` on `CLINICAL_NOTE` by a non-clinical role fires `SEV-1 UNAUTHORISED_CLINICAL_ACCESS` immediately.
- **Mitigation/Recovery:**
  1. Revoke the staff member's session immediately.
  2. Audit all clinical note reads by the staff member for the past 90 days.
  3. Identify patients whose clinical notes were accessed; begin OCR breach assessment.
  4. Report to the Privacy Officer and initiate workforce sanctions per HIPAA §164.530(e).
  5. Patch the endpoint: add `@Roles('CLINICIAN', 'PROVIDER', 'ADMIN')` guard before the 4-hour SLA.
- **Prevention:**
  - Define a role-permission matrix in a central RBAC configuration file; map `READ_CLINICAL_NOTE` only to `CLINICIAN`, `PROVIDER`, and `ADMIN` roles.
  - Apply role guards as mandatory decorators on all clinical endpoints; make the build fail if any clinical endpoint lacks an explicit `@Roles` decorator (enforce via custom ESLint rule).
  - Run quarterly automated access recertification: compare current role assignments against the RBAC matrix and flag anomalies for manager sign-off.
  - Include clinical-note endpoint authorisation in integration test suite with role matrix coverage.

---

### EC-SEC-005: Failed HIPAA Audit Trail — Data Export Not Logged, Gap in Access Record {#ec-sec-005}

- **Failure Mode:** A bulk data export endpoint (`POST /reports/appointments/export`) is added as an emergency feature during a product sprint. The developer forgets to inject the audit-log interceptor. Thousands of PHI records are exported to a CSV and emailed to an analyst. There is no audit log entry for this export. During an OCR investigation or internal audit, the gap in the access record creates suspicion of a cover-up and prevents demonstrating compliance.
- **Impact:** HIPAA Security Rule §164.312(b) requires audit controls — hardware, software, and procedural mechanisms to record and examine access to information systems containing PHI. A missing audit trail for a PHI export is a direct regulatory violation. OCR may impose corrective action plans lasting 1–3 years. SOC 2 Type II auditors will issue a finding that jeopardises the certification. Internal investigation costs: $50,000–$500,000 in legal and forensic fees.
- **Detection:**
  - Nightly completeness check: `SELECT e.export_id, e.actor_id, e.timestamp FROM data_exports e LEFT JOIN audit_log al ON al.correlation_id = e.export_id WHERE al.correlation_id IS NULL;`
  - Alert: Any row returned by the completeness check fires `SEV-1 AUDIT_GAP_DETECTED`.
  - CI gate: Static analysis rule scans all HTTP handlers for the `@AuditLog` decorator; build fails if any endpoint touching PHI resources lacks it.
- **Mitigation/Recovery:**
  1. Immediately disable the un-audited export endpoint until the audit interceptor is deployed.
  2. Reconstruct the export event from system logs (network logs, email gateway logs, object storage access logs) and create a manual audit record with a `RECONSTRUCTED` flag.
  3. Notify the Privacy Officer and document the gap in the HIPAA risk assessment log.
  4. Patch the endpoint to add the audit interceptor and deploy within 2 hours.
  5. Run the completeness check retroactively for the past 90 days; document all gaps found.
- **Prevention:**
  - Create a mandatory NestJS global interceptor (`AuditLogInterceptor`) registered at the application level so that all requests are logged by default, with an explicit opt-out (`@SkipAudit`) that requires Privacy Officer approval in the PR.
  - Enforce the opt-in pattern in reverse: the default is audit-on, and the team must explicitly justify any audit skip.
  - Run the audit-completeness SQL as a nightly scheduled job; page on-call if any rows are returned.
  - Include audit-log coverage in the definition of done for every new API endpoint.

---

### EC-SEC-006: GDPR Deletion Request Conflicting with 7-Year Medical Records Retention Requirement {#ec-sec-006}

- **Failure Mode:** A patient in a GDPR-covered jurisdiction (EU/EEA) submits a Right to Erasure request under GDPR Article 17. The system attempts full deletion of all patient data. However, the appointment records and clinical notes are legally required to be retained for 7 years under applicable national health law (e.g., UK NHS Records Management Code of Practice, German §630f BGB). Deleting them violates the retention obligation; retaining them fully violates the erasure request. Neither path is compliant without a nuanced response.
- **Impact:** Failure to honour an erasure request within 30 days: GDPR fine up to €20 million or 4% of global annual turnover. Wrongful deletion of legally required medical records: regulatory sanctions from health authority, potential criminal liability, and inability to defend medical negligence claims. Conflicting legal obligations create irreducible legal risk without a documented, auditable decision trail.
- **Detection:**
  - Workflow trigger: every `DELETE /patients/{id}` or `POST /patients/{id}/erasure-request` creates a `GDPR_ERASURE_REQUEST` record and routes to the Data Protection Officer (DPO) queue.
  - SLA monitor: `SELECT * FROM gdpr_erasure_requests WHERE status = 'PENDING' AND created_at < NOW() - INTERVAL '25 days';` — alert at 25 days to leave 5 days for response before the 30-day deadline.
- **Mitigation/Recovery:**
  1. Acknowledge the erasure request to the patient within 72 hours, stating that the request is under legal review.
  2. DPO assesses which data categories are subject to conflicting retention obligations: appointment metadata, clinical notes, billing records (tax law), prescription records.
  3. Apply a selective retention response: pseudonymise or anonymise non-required fields (name, contact details, identifiers) while retaining clinically/legally mandated records in a restricted-access archive.
  4. Document the legal basis for each retained record category in the `gdpr_erasure_requests` table (`retained_fields`, `retention_basis`, `retention_expiry`).
  5. Respond to the patient in writing within 30 days explaining what was deleted, what was retained, the legal basis, and when retained records will be deleted at retention expiry.
  6. At retention expiry, an automated job deletes the restricted archive records and marks the erasure request `FULLY_COMPLETED`.
- **Prevention:**
  - Define a data-category taxonomy with retention periods and legal bases in a `data_retention_policy` configuration table; every data field in the schema is tagged to a category.
  - Build the erasure workflow to evaluate the taxonomy automatically and apply the least-invasive compliant action (delete, pseudonymise, or archive with restricted access).
  - Implement automated retention-expiry deletion jobs that run nightly and log each deletion to the audit trail.
  - Engage legal counsel to produce a jurisdiction-specific retention matrix; update the taxonomy table as laws change.

---

### EC-SEC-007: SQL/NoSQL Injection via Provider Notes or Appointment Reason Fields {#ec-sec-007}

- **Failure Mode:** The appointment reason field (`reason_for_visit`) and provider notes field (`clinical_notes`) accept free-text input. A malicious actor submits a payload such as `'; DROP TABLE appointments; --` or a MongoDB operator injection `{"$where": "sleep(5000)"}`. If the backend constructs queries by string concatenation or passes raw user input to a document query, the injected payload executes with database user privileges, potentially destroying data or exfiltrating the entire patient dataset.
- **Impact:** Complete database compromise results in mass PHI exfiltration affecting all patients — a catastrophic HIPAA breach requiring OCR notification and individual notification to every patient. Data destruction causes irrecoverable appointment record loss, disrupting care continuity. Estimated remediation cost: $500,000–$5 million (forensics, breach notification, legal, regulatory fines). Service downtime: 24–72 hours for database restoration.
- **Detection:**
  - WAF rule: block requests containing SQL meta-characters (`'`, `--`, `;`, `UNION`, `DROP`, `INSERT`, `SELECT`) in free-text fields; log and alert on match.
  - Application-level log pattern: `[SECURITY] INJECTION_ATTEMPT field=reason_for_visit actor=<userId> payload_hash=<sha256>`
  - Database slow-query alert: queries exceeding 2 seconds on the appointments table trigger `SEV-2 SLOW_QUERY` — often an indicator of a `SLEEP`-based time-delay injection probe.
  - Alert threshold: 3 or more injection-pattern matches from the same actor within 5 minutes triggers account suspension.
- **Mitigation/Recovery:**
  1. Immediately block the source IP and suspend the actor account.
  2. Check database integrity: run row counts and checksum validations against the last known-good backup snapshot for the `appointments`, `patients`, and `clinical_notes` tables.
  3. Review database query logs for the past 24 hours for unusual DDL statements (`DROP`, `ALTER`, `TRUNCATE`) or large SELECT operations.
  4. If data exfiltration is confirmed, initiate breach response: identify affected patient IDs, notify Privacy Officer, begin OCR timeline.
  5. If data destruction is confirmed, restore from the most recent verified backup and replay the write-ahead log up to the point of the attack.
- **Prevention:**
  - Use parameterised queries / prepared statements exclusively — never string-interpolate user input into SQL. In TypeORM: `repository.findOne({ where: { id: param } })` not `repository.query(\`SELECT * WHERE id = '${param}'\`)`.
  - For MongoDB/Mongoose, use schema-level type coercion so that `$where` and operator keys in user-submitted JSON are rejected before reaching the query engine.
  - Sanitise free-text fields with an allowlist (Unicode letters, numbers, common punctuation) using a server-side validator (`class-validator` `@IsString`, `@MaxLength(500)`, `@Matches(/^[a-zA-Z0-9 .,\-']+$/)`) — reject at the DTO validation layer before the service layer is reached.
  - Run SAST (Semgrep, Snyk Code) in CI with injection-detection rules; block merge on any finding.
  - Grant the application database user only `SELECT`, `INSERT`, `UPDATE` privileges — never `DROP`, `ALTER`, or `TRUNCATE`.

---

### EC-SEC-008: Session Token Not Invalidated After Password Reset, Allowing Session Hijacking {#ec-sec-008}

- **Failure Mode:** A patient resets their password after suspecting their account was compromised. The system issues a new JWT and updates the `password_hash` in the database. However, the previous JWT (stolen by the attacker) remains valid until its natural expiry (e.g., 24 hours). The attacker continues to access the account, read appointment history, and book or cancel appointments using the old token for the remainder of the expiry window.
- **Impact:** The password reset — intended as a security recovery action — provides no immediate protection. The attacker retains full account access for up to 24 hours. PHI accessed during this window constitutes an ongoing HIPAA breach. If the attacker cancels appointments, the patient loses care access; if they book fraudulent appointments, billing fraud occurs. Patient trust is severely damaged.
- **Detection:**
  - Log pattern: `[AUTH] SESSION_POST_RESET actor=<userId> token_issued_at=<old_iat> password_reset_at=<reset_ts> token_iat < reset_ts`
  - Alert: Any request authenticated with a JWT whose `iat` (issued-at) claim predates the actor's `password_changed_at` timestamp fires `SEV-1 STALE_TOKEN_USED`.
  - Monitoring query: `SELECT al.actor_id, al.token_iat, u.password_changed_at FROM request_log al JOIN users u ON al.actor_id = u.user_id WHERE al.token_iat < u.password_changed_at AND al.timestamp > NOW() - INTERVAL '1 hour';`
- **Mitigation/Recovery:**
  1. Immediately add the old token's `jti` (JWT ID) to the token blocklist (Redis set: `SADD blocklist:<userId> <jti>` with TTL = token expiry).
  2. Force logout all active sessions for the user by incrementing a `token_version` counter in the user record; all tokens issued before the current version are invalid.
  3. Audit all actions performed with the stale token post-reset; document for the breach record.
  4. Notify the patient of the suspicious access and advise them to review recent appointments.
- **Prevention:**
  - Store a `token_version` (integer) on the user record. Embed it as a claim in every JWT. On every authenticated request, validate that the token's `version` claim matches the database value. Increment `token_version` on password reset, role change, and account suspension — instantly invalidating all pre-existing tokens without a centralised blocklist.
  - As a defence-in-depth layer, maintain a Redis token blocklist for explicit revocations (logout, suspicious activity) with TTL equal to token max expiry.
  - Reduce JWT access token expiry to 15 minutes; use refresh tokens (stored as HTTP-only cookies with `SameSite=Strict`) with a 7-day sliding expiry.
  - Send a push/email notification to the patient after every password reset: "Your password was changed. All active sessions have been signed out."

---

### EC-SEC-009: API Key Leaked in Client-Side JavaScript Bundle, Exposed in Browser {#ec-sec-009}

- **Failure Mode:** A backend API key for an insurance eligibility verification service or SMS gateway is embedded in the React frontend source code as an environment variable prefixed with `REACT_APP_` or `NEXT_PUBLIC_`, causing it to be bundled into the client-side JavaScript. The bundle is publicly served; any user who opens DevTools or uses a source-map explorer can extract the key. The key is then used to make direct API calls, bypass rate limits, or exfiltrate data from the third-party service.
- **Impact:** A leaked SMS gateway API key enables the attacker to send thousands of SMS messages at the clinic's expense (financial loss: $10,000–$100,000+). A leaked insurance eligibility API key enables lookup of any member's insurance status — a significant PHI breach affecting the insurer's members. Third-party vendors may immediately revoke the key on detection, causing outage for all production booking flows. The BAA with the insurer may be voided, creating legal liability.
- **Detection:**
  - CI pipeline step: run `truffleHog` or `detect-secrets` on the compiled JavaScript bundle as part of the build; fail the build on any high-entropy string that matches API key patterns.
  - Periodic secret scanning: GitHub Advanced Security / GitLeaks runs on every commit and PR; alerts within 5 minutes of a secret being pushed.
  - Third-party API anomaly: monitor for unusual spikes in API calls to the insurance verifier or SMS gateway from IPs other than your server's egress IPs.
  - Log pattern: `[SECRET_SCAN] HIGH_ENTROPY_STRING file=main.<hash>.js pattern=API_KEY_PATTERN`
- **Mitigation/Recovery:**
  1. Immediately rotate the leaked API key in the third-party vendor's dashboard; update the secret in the server-side secrets manager (AWS Secrets Manager, HashiCorp Vault).
  2. Invalidate all cached responses that used the old key.
  3. Audit third-party service logs for the period the key was exposed; identify any unauthorised API calls.
  4. If PHI was accessible via the leaked key, initiate breach assessment.
  5. Remove the key from the frontend codebase and redeploy within 1 hour.
- **Prevention:**
  - Never expose non-public API keys in frontend code under any prefix. All calls to third-party services that require API keys must be proxied through a backend service (BFF pattern).
  - Frontend should only ever call your own backend APIs, which authenticate the user and then call third-party services server-side using secrets stored in a secrets manager — never in environment variables committed to source control.
  - Add `detect-secrets` as a pre-commit hook and CI gate; fail the build on any detected secret.
  - Implement secret rotation on a 90-day schedule for all API keys; automate via AWS Secrets Manager rotation Lambda.

---

### EC-SEC-010: Third-Party Integration Receiving PHI Without a Signed BAA {#ec-sec-010}

- **Failure Mode:** The development team integrates a third-party insurance eligibility verification API. During onboarding, they pass patient name, date of birth, insurance member ID, and insurance group number in the request payload to verify coverage at booking time. No Business Associate Agreement (BAA) has been reviewed or signed with the vendor. The integration is live in production for 3 months before a compliance audit identifies the gap.
- **Impact:** Under HIPAA, any covered entity that discloses PHI to a business associate without a signed BAA is in direct violation of 45 CFR §164.308(b) and §164.502(e). The covered entity bears full liability for any PHI misuse by the vendor. Penalties: $100–$50,000 per violation, capped at $1.9 million per violation category per year. Each API call containing PHI is a separate disclosure; 3 months at 500 calls/day = ~45,000 individual violations. OCR may require a corrective action plan lasting 3 years.
- **Detection:**
  - Vendor registry check: nightly automated report cross-references all active integrations (from service mesh egress rules or API gateway outbound policies) against the BAA tracking database.
  - Alert: Any outbound integration to a non-BAA-listed vendor that transmits PHI fields fires `SEV-1 BAA_MISSING` immediately.
  - Query: `SELECT i.vendor_name, i.endpoint, i.phi_fields_transmitted FROM integrations i LEFT JOIN baas b ON i.vendor_id = b.vendor_id WHERE b.vendor_id IS NULL AND i.phi_transmitted = TRUE;`
- **Mitigation/Recovery:**
  1. Immediately disable the integration endpoint to stop further PHI disclosure.
  2. Contact the vendor's legal/compliance team; initiate BAA review and signing process.
  3. Quantify the exposure: count API calls, identify PHI fields transmitted, and list affected patients.
  4. Notify the Privacy Officer; begin OCR breach assessment for the 3-month period.
  5. If the vendor cannot or will not sign a BAA, the integration must be permanently replaced with a BAA-compliant alternative.
  6. Re-enable the integration only after a signed BAA is on file in the legal document repository.
- **Prevention:**
  - Establish a "PHI integration approval gate" in the engineering process: any new integration that transmits PHI requires (a) a signed BAA on file, (b) a security review of the vendor's SOC 2 report, and (c) Privacy Officer sign-off before the PR is merged.
  - Maintain a vendor registry table (`vendor_id`, `vendor_name`, `baa_status`, `baa_signed_date`, `baa_expiry`, `phi_fields_shared`); enforce foreign key constraints so that integration configuration records cannot reference a vendor without a valid BAA.
  - Automate BAA expiry reminders: alert at 60 days and 30 days before expiry; block the integration if BAA lapses.
  - Document all integrations and their PHI exposure in the HIPAA Risk Assessment, reviewed annually.

---

## Cross-Cutting Controls

| Control | Implementation | Regulatory Mapping |
|---|---|---|
| Encryption in transit | TLS 1.3 minimum, HSTS with preload | HIPAA §164.312(e)(1) |
| Encryption at rest | AES-256, customer-managed keys for regulated tenants | HIPAA §164.312(a)(2)(iv) |
| Access control | RBAC + ABAC via OPA; MFA for all privileged roles | HIPAA §164.312(a)(1) |
| Audit logging | Immutable append-only audit log; 7-year retention | HIPAA §164.312(b) |
| PHI minimisation | Data masking in non-prod; field-level encryption for exports | GDPR Article 25 |
| Incident response | 72-hour internal notification SLA; 60-day OCR notification SLA | HIPAA §164.408 |
| BAA management | Vendor registry with automated expiry tracking | HIPAA §164.308(b) |
| Penetration testing | Annual third-party pentest + quarterly automated DAST | SOC 2 CC7.1 |
| Vulnerability management | SAST in CI (Semgrep, Snyk); DAST on staging; CVE monitoring | SOC 2 CC7.1 |
| Secret management | HashiCorp Vault / AWS Secrets Manager; 90-day rotation | SOC 2 CC6.7 |
