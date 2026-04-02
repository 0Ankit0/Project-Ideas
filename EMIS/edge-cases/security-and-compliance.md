# Edge Cases — Security and Compliance

Domain-specific failure modes, impact assessments, and mitigation strategies for authentication, authorisation, data protection, and regulatory compliance.

Edge case IDs in this file are permanent: **EC-SEC-001 through EC-SEC-008**.

---

## EC-SEC-001 — JWT Refresh Token Theft and Session Hijacking

| Field | Detail |
|---|---|
| **Failure Mode** | An attacker obtains a valid JWT refresh token (via XSS, phishing, or a compromised device). They use it to silently generate a stream of new access tokens, maintaining persistent access to the victim's account. |
| **Impact** | Attacker can impersonate student/faculty, view grades, submit assignments, initiate payments, or exfiltrate personal data indefinitely — even after the victim has changed their password. |
| **Detection** | (1) Refresh token is rotated on every use (single-use tokens). If an already-used refresh token is presented, this indicates token theft — the system immediately revokes the entire refresh token family. (2) Anomaly detection: `refresh_token.used_from_new_ip_country` alert triggers on geographic impossibility (e.g., login from Mumbai, then refresh from Germany 10 minutes later). |
| **Mitigation / Recovery** | (1) On detection of a replayed refresh token: revoke all tokens in the family, force logout all sessions, notify user via email and SMS. (2) User must re-authenticate and reset password. (3) IT Security team investigates using AuditLog to identify what data was accessed. |
| **Prevention** | Refresh tokens stored as secure HttpOnly cookies (not localStorage), preventing XSS exfiltration. Token rotation on every refresh. MFA enforced for high-privilege roles (ADMIN, FINANCE_STAFF). IP binding is optional (configurable per role). |

---

## EC-SEC-002 — Privilege Escalation via Role Manipulation

| Field | Detail |
|---|---|
| **Failure Mode** | A malicious student discovers that the `PATCH /api/students/{id}/` endpoint accepts a `role` field in the request body and does not strip it before processing, allowing the student to escalate their own account role to ADMIN. |
| **Impact** | Full administrative access: student can view all records, issue invoices, publish grades, and grant access to other users. |
| **Detection** | DRF serializer `fields` and `read_only_fields` definitions explicitly exclude `role`, `is_staff`, and `is_superuser` from every non-admin serializer. Security integration test suite includes privilege-escalation test cases. |
| **Mitigation / Recovery** | (1) If a role escalation attempt is discovered via AuditLog: immediately revoke all tokens for the affected user, reset their role to the original value, and lock the account pending investigation. (2) Security incident report is filed. |
| **Prevention** | Role and permission fields are designated `read_only` on all non-admin serializers. API security tests (run in CI) attempt to escalate roles and assert 400/403 responses. Regular OWASP ZAP scan in the staging environment. |

---

## EC-SEC-003 — IDOR — Student Accessing Another Student's Records

| Field | Detail |
|---|---|
| **Failure Mode** | A student with `student_id = 001` changes the URL from `GET /api/students/001/grades/` to `GET /api/students/002/grades/` and successfully retrieves another student's grade records due to missing object-level permission checks. |
| **Impact** | Privacy breach. Student data (grades, attendance, fee details) exposed to an unauthorised peer. FERPA/PDPA violation. |
| **Detection** | Django REST framework object-level permission class `IsOwnerOrHasRole` is applied on all student-scoped endpoints. Permission class checks `request.user.student_id == pk` OR `request.user.role in [ADMIN, FACULTY]`. |
| **Mitigation / Recovery** | (1) On detection via access log anomaly: identify all records accessed by the violating user in the session, assess data exposure. (2) Notify affected students in accordance with PDPA breach notification requirements (within 72 hours). (3) Lock violating account pending investigation. |
| **Prevention** | All student-scoped endpoints use `get_object_or_404` with an ownership filter: `.filter(id=pk, user=request.user)` for student-role access. Automated IDOR tests in the security test suite cycle through multiple user tokens attempting cross-user access. |

---

## EC-SEC-004 — SQL Injection via Search Parameters

| Field | Detail |
|---|---|
| **Failure Mode** | An attacker submits a malicious payload in the `?search=` query parameter of the student listing endpoint: `?search=' OR '1'='1`. If the search is implemented via raw SQL string interpolation, the query returns all student records. |
| **Impact** | Full database dump of student PII. Credential exposure. PDPA and FERPA violation. |
| **Detection** | WAF AWS Managed Rule Set (SQL Database Rules) blocks common SQL injection patterns at the edge before reaching the API. Application-level: DRF filter uses Django ORM `Q` objects exclusively — no raw SQL with user input. |
| **Mitigation / Recovery** | (1) WAF blocks the request with 403. (2) Attack attempt is logged in WAF logs and CloudWatch, triggering a security alert. (3) If WAF is bypassed and attack succeeds: invoke incident response plan, rotate all database credentials via Secrets Manager, review access logs for exfiltrated data. |
| **Prevention** | Strict policy: no raw SQL with user-supplied input. Code review checklist item for all new endpoints. SAST pipeline checks for Django `raw()` calls with string interpolation. Penetration testing conducted annually. |

---

## EC-SEC-005 — Mass Data Export by Compromised Admin Account

| Field | Detail |
|---|---|
| **Failure Mode** | An admin account is compromised (phishing attack). The attacker uses the admin's credentials to call the student listing and report export endpoints repeatedly, exfiltrating all student PII and grade data to an external service. |
| **Impact** | Full institutional data breach. 2,800+ student records compromised. Regulatory notification required. Reputational damage. |
| **Detection** | (1) Anomaly detection: `admin.bulk_export_rate` CloudWatch metric triggers alert if > 5 export jobs in 10 minutes from a single user. (2) Data exfiltration detection: unusually large response payloads to a single IP in a short window. |
| **Mitigation / Recovery** | (1) Alert → auto-revoke all tokens for the flagged admin user and force login from trusted IP only. (2) IT security reviews export job history to scope the breach. (3) Incident response: notify CISO, legal team; initiate PDPA breach notification process within 72 hours. |
| **Prevention** | All admin accounts require MFA. Admin IP allowlisting is optionally enforceable per role. Export endpoints are rate-limited (max 10 exports/hour per user). Exports are logged with requestor, timestamp, filters, and row count. Anomaly alerts on bulk export rates. |

---

## EC-SEC-006 — Insecure Direct Object Reference in Document Download

| Field | Detail |
|---|---|
| **Failure Mode** | Pre-signed S3 URLs for student documents (admission documents, transcripts) use guessable sequential IDs in the key path: `s3://emis-assets/documents/001/transcript.pdf`. A user iterates document IDs to download other students' documents. |
| **Impact** | Unauthorised access to sensitive student documents. Privacy breach. |
| **Detection** | S3 pre-signed URL generation: URL is created with a short expiry (30 minutes) and scoped to a specific object key that uses UUID-based paths, not sequential IDs. |
| **Mitigation / Recovery** | (1) S3 pre-signed URL access is logged in CloudTrail. Unusual access patterns (many different object keys from one IP) trigger a security alert. (2) If a breach is confirmed, affected students are notified. |
| **Prevention** | All S3 object keys use UUID-v4 segments: `documents/{uuid}/{document_type}/{uuid_filename}.pdf`. Pre-signed URLs expire in 30 minutes. The document download endpoint (`GET /api/files/{id}/`) checks ownership before generating the pre-signed URL. |

---

## EC-SEC-007 — CSRF Attack on State-Changing Endpoints

| Field | Detail |
|---|---|
| **Failure Mode** | A student visits a malicious website that crafts a cross-site request to `POST /api/enrollment/` using the student's active session cookie. Since the cookie is automatically included by the browser, the enrollment is processed on behalf of the student without their knowledge. |
| **Impact** | Unauthorised course enrollment on student's account. Student may not notice until the semester starts. |
| **Detection** | DRF API uses JWT in `Authorization` header (not cookies) as the primary authentication mechanism. CSRF attacks cannot forge the `Authorization` header. |
| **Mitigation / Recovery** | (1) JWT-header-based authentication is inherently CSRF-resistant. (2) If session-cookie-based authentication is ever used (e.g., the admin panel), Django's built-in CSRF middleware is enforced. |
| **Prevention** | Primary EMIS API uses JWT Bearer token authentication exclusively — no session cookies for API calls. Admin panel uses session cookies with CSRF middleware (`CsrfViewMiddleware`) enabled. CSP headers prevent cross-site script execution. `SameSite=Strict` on any cookies set by the application. |

---

## EC-SEC-008 — Audit Log Tampering by Admin

| Field | Detail |
|---|---|
| **Failure Mode** | A malicious or compromised admin account uses the admin panel to delete or modify AuditLog records to cover tracks after an unauthorised data access event. |
| **Impact** | Forensic investigation is compromised. Regulatory compliance (FERPA, PDPA) requires maintaining immutable audit trails. |
| **Detection** | AuditLog table has no `UPDATE` or `DELETE` permissions granted to any application role — only `INSERT` and `SELECT`. Any attempt to modify AuditLog triggers a PostgreSQL permission denied error. |
| **Mitigation / Recovery** | (1) AuditLog records are additionally shipped to an append-only CloudWatch Log Group using a PostgreSQL logical replication trigger or a post-save signal. (2) The CloudWatch log group has a write-only IAM policy: no AWS principal (including the EMIS API task role) can delete CloudWatch log entries. (3) For forensic investigations, CloudWatch logs serve as the tamper-evident source of truth. |
| **Prevention** | Database role `emis_app` has `REVOKE DELETE, UPDATE ON audit_log FROM emis_app` applied in the database migration. SUPER_ADMIN cannot modify audit logs through the application (only a direct DB superuser can, which requires the bastion host and is itself logged in CloudTrail). Annual database permission audit. |

---

## Operational Policy Addendum

### Academic Integrity Policies
Security incidents involving grade record access by unauthorised parties are automatically escalated to the Academic Integrity Committee. Any grade-related data exposure triggers a student notification and a formal investigation, regardless of whether the exposure was intentional. Forensic review of AuditLog data is performed by the CISO, not by the IT operations team, to maintain independence.

### Student Data Privacy Policies
EMIS follows a data-minimisation principle: API responses return only fields required for the requesting role. PII fields (date of birth, national ID) are never included in bulk listing responses, only in individual student detail views accessible to authorised roles. Data retention is enforced: student records are archived 10 years after graduation and deleted after 15 years in compliance with institutional records policy.

### Fee Collection Policies
Financial data access is strictly role-segregated: only FINANCE_STAFF and ADMIN roles can access invoice and payment data. Faculty role cannot access fee information even for their own students. Fee collection records are retained for 7 years for tax and audit compliance. All financial record exports are watermarked with the exporting user's identity.

### System Availability During Academic Calendar
Security monitoring (CloudWatch Alarms, WAF, GuardDuty) is always active regardless of academic calendar events. During exam periods and registration windows, WAF rate limits are tightened and GuardDuty findings are triaged within 1 hour (vs. standard 4-hour SLA during normal operations). A security engineer is on-call during all Mission-Critical calendar windows.
