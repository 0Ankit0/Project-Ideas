# Edge Cases — Security & Compliance

This document catalogues security vulnerabilities, attack vectors, and compliance edge cases identified during threat modelling, penetration testing planning, and code review for the Nepal Government Services Portal. Each case maps to a concrete failure scenario, its impact on citizens and government data, and the mitigation controls implemented. Where relevant, code snippets are provided in the Appendix for security configuration. All cases are evaluated against the **Nepal Privacy Act 2018 (Goptaniyata Sambandhi Ain, 2075)** and the Government of Nepal's Information Security Policy.

---

## Summary Table

| ID | Title | Component | Severity |
|---|---|---|---|
| EC-SEC-001 | NID data exposure via API response logging (PII leak) | API Server / Logging | Critical |
| EC-SEC-002 | JWT token not invalidated after officer account suspension | Auth Service / JWT | High |
| EC-SEC-003 | CSRF attack on application form submission | API Server / Django Middleware | High |
| EC-SEC-004 | NDW OAuth state parameter tampering | NDW Integration / OAuth | High |
| EC-SEC-005 | Unauthorized access to officer review queue | API Server / Permissions | High |
| EC-SEC-006 | Document upload malware injection (malicious PDF bypassing ClamAV) | Document Service / S3 | Critical |
| EC-SEC-007 | Audit log tampering (application status history altered) | Audit Logger / Database | Critical |
| EC-SEC-008 | Mass data extraction via paginated API (rate-limit bypass) | API Server / Rate Limiting | High |

---

## Edge Cases

---

### EC-SEC-001: NID Data Exposure via API Response Logging (PII Leak Under Nepal Privacy Act 2018)

| Field | Details |
|---|---|
| **Failure Mode** | A developer adds verbose Django request/response logging to debug a citizen registration issue in the production environment. The logging middleware captures the full request body, which includes the citizen's NID number in plaintext. The log entry is written to CloudWatch Logs. A second path: the DRF exception handler logs the full serializer `data` dictionary on `ValidationError`, and the serializer's `validated_data` includes the NID field. NID numbers from hundreds of registration attempts are now visible in plaintext in CloudWatch Logs and potentially in Sentry breadcrumbs. |
| **Impact** | NID numbers are unique government-issued identifiers analogous to SSNs. Exposure in logs violates the Nepal Privacy Act 2018 and the citizen's fundamental right to privacy. If CloudWatch logs are accessed by an unauthorised party (e.g., through compromised AWS credentials), thousands of NID numbers could be exfiltrated. The portal operator faces regulatory sanction, mandatory breach notification obligations, and loss of citizen trust. |
| **Detection** | AWS Macie continuous scan on CloudWatch Logs S3 export bucket detects NID number patterns (`[0-9]{7,12}` in the context of NID fields). Custom CloudWatch Logs Insights query runs hourly: `fields @message | filter @message like /nid_number/ | stats count()`. Security team code review checklist requires review of any logging middleware change. |
| **Mitigation / Recovery** | 1. Immediately disable verbose request/response logging middleware in production via SSM Parameter Store feature flag. 2. Export the affected CloudWatch log group to S3, then delete the log group and recreate it (this destroys the leaked logs within the AWS environment). 3. Assess whether any external log sinks (Sentry, Datadog) received the PII; if so, use their bulk delete / scrubbing APIs. 4. Conduct a privacy impact assessment and determine whether notification to affected citizens is required under the Nepal Privacy Act 2018 (72-hour reporting window for data breaches). |
| **Prevention** | 1. Implement a `SensitiveFieldsMaskingFilter` log filter (see Appendix) that replaces known PII field values with `***REDACTED***` before any log handler processes the record. Fields covered: `nid_number`, `phone_number`, `date_of_birth`, `full_name`, `address`. 2. Never log request/response bodies in production; use structured log fields for specific safe metadata (endpoint, status code, duration, user ID). 3. Configure Sentry's `before_send` hook to strip PII fields from exception breadcrumbs. 4. Add a pre-commit hook that searches for `print(request.data)`, `logger.debug(serializer.data)`, and similar patterns and rejects the commit. |

---

### EC-SEC-002: JWT Token Not Invalidated After Officer Account Suspension

| Field | Details |
|---|---|
| **Failure Mode** | A government officer is found to have approved applications fraudulently. The Super Admin suspends the officer's account by setting `is_active=False` in the database. However, the officer holds a valid JWT access token (expiry: 60 minutes, issued 5 minutes ago). The Django REST Framework SimpleJWT middleware validates the token's signature and expiry claim but does not check the database for the officer's `is_active` status (JWT is stateless by design). The officer continues to access protected endpoints — approving, rejecting, and viewing applications — for up to 55 more minutes. |
| **Impact** | A suspended officer retains full API access during the remaining JWT lifetime. For a government portal handling permit approvals and certificate issuance, this can result in fraudulent approvals being committed to permanent records. The impact is amplified if the officer also has access to bulk approval actions. |
| **Detection** | No real-time detection in a purely stateless JWT setup. Detection is retroactive: Audit logs show officer actions after the `suspended_at` timestamp. Security monitoring query: `SELECT a.id, a.actor_id, a.action, a.created_at FROM audit_logs a JOIN officers o ON a.actor_id = o.id WHERE o.is_active = false AND a.created_at > o.suspended_at`. |
| **Mitigation / Recovery** | 1. Immediately add the officer's `user_id` to a Redis JWT blacklist set (`SET jwt_blacklist:{user_id} "1" EX 3600`). The authentication middleware checks this blacklist on every request. 2. Revoke all refresh tokens for the officer in the `outstanding_token` table (SimpleJWT token blacklisting). 3. Review all actions taken by the officer after their `suspended_at` timestamp in the audit log and reverse any fraudulent approvals. 4. Escalate to the security incident response team. |
| **Prevention** | 1. Implement a Redis-backed JWT blacklist that is checked on every authenticated request (see Appendix). The check adds <1ms latency per request. 2. Reduce JWT access token lifetime to 15 minutes for officer roles (longer for citizen roles where the impact is lower). 3. Add a post-save signal on the `Officer` model: when `is_active` transitions to `False`, immediately write to the JWT blacklist. 4. Implement a "force logout" admin action that writes to the blacklist and invalidates all refresh tokens in one click. |

---

### EC-SEC-003: CSRF Attack on Application Form Submission

| Field | Details |
|---|---|
| **Failure Mode** | A malicious actor hosts a page at `https://evil.example.com/apply` that contains a hidden form targeting `https://govportal.gov.np/api/v1/applications/`. When a logged-in citizen visits `evil.example.com`, the form is auto-submitted by JavaScript. If the portal's API does not enforce CSRF protection (e.g., the DRF `SessionAuthentication` class is used without the CSRF middleware, or a custom authentication class bypasses CSRF checking), the request is accepted as valid and a fraudulent application is submitted in the citizen's name. |
| **Impact** | Fraudulent applications can be submitted on behalf of a citizen without their knowledge. If the application also triggers a payment initiation, the citizen may be charged. At scale, a CSRF campaign could flood the system with fraudulent applications, consuming officer review capacity. Additionally, if the endpoint modifies critical data (e.g., a citizen's profile), personal information could be altered. |
| **Detection** | Unusual spike in application submissions from a single citizen (rate limit alarm: `application_submit_count per citizen per hour > 5`). CSRF token validation failure rate spike in Django logs. Security scan (OWASP ZAP automated scan in CI pipeline) detects missing CSRF token on form submission endpoints. |
| **Mitigation / Recovery** | 1. Enable Django's `CsrfViewMiddleware` for all session-authenticated endpoints. 2. For JWT-authenticated endpoints (stateless), enforce the `Origin` and `Referer` header check: reject any request where the `Origin` header does not match the portal's domain. 3. Review all applications submitted from known attack periods; cancel any fraudulent ones and notify affected citizens. |
| **Prevention** | 1. Use DRF `SessionAuthentication` only for browser-based endpoints (citizen and officer web app); it enforces CSRF checking by design. For the mobile API, use JWT-only authentication which is not susceptible to CSRF. 2. Set `CSRF_COOKIE_SAMESITE = 'Lax'` and `CSRF_COOKIE_SECURE = True` in Django settings. 3. Implement CORS with a strict allowlist (`CORS_ALLOWED_ORIGINS = ['https://govportal.gov.np', 'https://officer.govportal.gov.np']`). 4. Run OWASP ZAP baseline scan in the CI pipeline; fail the build on any CSRF-related finding. |

---

### EC-SEC-004: NDW OAuth State Parameter Tampering

| Field | Details |
|---|---|
| **Failure Mode** | During the NDW (Nepal Document Wallet) OAuth 2.0 authorization code flow, the portal generates a `state` parameter (random UUID stored in the user's session) and includes it in the authorization redirect to NDW. When NDW redirects back to the portal's callback URL with the `code` and `state` parameters, the portal is supposed to verify that the returned `state` matches the session-stored value. If the `state` validation step is skipped or incorrectly implemented (e.g., comparing against a hardcoded value or not comparing at all), an attacker can craft a malicious redirect that includes a valid `code` but a forged `state`, potentially tricking the portal into linking another citizen's NDW account to the attacker's session (OAuth CSRF / session fixation). |
| **Impact** | An attacker could link a victim citizen's NDW documents to the attacker's application, enabling identity theft and fraudulent application submission using another citizen's verified documents (e.g., land ownership certificate, passport scan). This is a serious breach of the Nepal Privacy Act 2018 and a fraud enabler. |
| **Detection** | NDW OAuth callback handler logs `state_mismatch=true` for failed verifications. Security monitoring alarm: `ndw_oauth_state_mismatch_count > 5 per hour` triggers alert. Penetration test checklist includes OAuth state parameter validation testing. |
| **Mitigation / Recovery** | 1. Immediately audit the OAuth callback handler code for correct `state` validation. 2. If tampering is detected in logs: revoke all active NDW OAuth tokens for the affected period, clear the affected citizens' NDW authorizations, and require them to re-authorize. 3. Notify affected citizens via SMS and email. |
| **Prevention** | 1. Generate a cryptographically random `state` value (32 bytes, base64url-encoded) per OAuth flow using `secrets.token_urlsafe(32)`. Store it in the user's session with a 10-minute expiry. 2. In the callback handler, compare the returned `state` with the session value using `hmac.compare_digest()` (constant-time comparison to prevent timing attacks). If mismatch: abort, log, and redirect to error page. 3. Add `state` validation test to the integration test suite: assert that a callback with a tampered `state` returns HTTP 400. 4. Use the `authlib` or `social-auth-app-django` library for OAuth flows, which implement state validation correctly, rather than a hand-rolled implementation. |

---

### EC-SEC-005: Unauthorized Access to Officer Review Queue

| Field | Details |
|---|---|
| **Failure Mode** | An officer in Department A (e.g., Land Revenue Department) exploits an IDOR (Insecure Direct Object Reference) vulnerability in the officer dashboard API. The `GET /api/v1/officer/applications/{application_id}/` endpoint uses the `application_id` (a UUID) as the only access control check but does not verify that the requesting officer belongs to the department responsible for the application. The officer can enumerate application IDs from their own department's queue and then substitute IDs from another department to read confidential application data (e.g., personal information in a health subsidy application from the Ministry of Health's queue). |
| **Impact** | Cross-department data leakage: officers can read (and potentially act on) applications they are not authorized to process. In the worst case, a corrupt officer in one department could approve or reject applications assigned to another department. This undermines the principle of least privilege and violates the Nepal Privacy Act 2018 (data minimisation principle). |
| **Detection** | Row-Level Security (RLS) violation in PostgreSQL: if properly configured, the DB rejects the query. API-level access control audit: automated test suite includes cross-department access tests. CloudWatch anomaly detection on `officer_cross_department_access_blocked` metric. |
| **Mitigation / Recovery** | 1. Audit all officer API actions in the `audit_logs` table for cross-department access: `SELECT * FROM audit_logs WHERE actor_id IN (officer_dept_A_ids) AND resource_department != 'DEPT_A'`. 2. If unauthorised access is found: escalate to the security team, suspend the officer account, and review all actions taken. 3. Apply database RLS policies immediately if not already in place (see Appendix). |
| **Prevention** | 1. Implement PostgreSQL Row-Level Security on the `applications` table: `CREATE POLICY officer_dept_access ON applications FOR ALL TO officer_role USING (department_id = current_setting('app.officer_department_id')::uuid)`. 2. In Django queryset: always filter by `department=request.user.officer.department` in the `get_queryset()` method of all officer viewsets. 3. Add `object-level permission` check in the DRF `has_object_permission()` method: `return obj.department == request.user.officer.department`. 4. Include cross-department IDOR tests in the automated security test suite: create a second test officer in a different department and assert HTTP 403 on cross-access attempts. |

---

### EC-SEC-006: Document Upload Malware Injection (Malicious PDF Bypassing ClamAV)

| Field | Details |
|---|---|
| **Failure Mode** | A citizen uploads a specially crafted PDF that exploits a known PDF renderer vulnerability (e.g., CVE targeting a PDF-to-image conversion library used for document preview). The PDF passes the ClamAV signature scan (the exploit uses a zero-day or a polymorphic payload not yet in ClamAV's signature database) and the MIME type check (it is a valid PDF with the correct magic bytes). The file is uploaded to S3. When an officer's browser loads the document preview (which renders the PDF using a server-side conversion to PNG), the malicious payload executes in the conversion container. |
| **Impact** | Remote code execution (RCE) in the document conversion container. The container has IAM permissions to access S3 (to read/write documents), which could be abused to exfiltrate all uploaded documents. If the container role has broader permissions, the blast radius is larger. This is a Critical / P0 security incident. |
| **Detection** | ClamAV scan failure alert (if ClamAV is updated and detects the payload on subsequent scans). Container runtime security tool (Falco or AWS GuardDuty) detects unusual process execution (e.g., `bash`, `curl`, `wget`) inside the PDF conversion container. Network flow anomaly: conversion container makes outbound connections to an unexpected IP. |
| **Mitigation / Recovery** | 1. Immediately isolate the affected conversion container (stop the ECS task). 2. Quarantine all documents uploaded in the last 24 hours: move from the `documents/` S3 prefix to `quarantine/` with restricted access. 3. Re-scan all quarantined documents with updated ClamAV signatures and a secondary scanner (e.g., ClamAV + VirusTotal API). 4. Assess IAM blast radius: rotate IAM credentials for the compromised role. 5. Conduct forensic analysis of the conversion container and CloudTrail logs. |
| **Prevention** | 1. Run the PDF conversion service in a dedicated, heavily sandboxed ECS task with minimal IAM permissions (only `s3:PutObject` on the preview bucket). 2. Use `sandbox2` or `gVisor` container runtime for the conversion service to limit system call surface. 3. Implement a defence-in-depth scanning pipeline: ClamAV (signature) → PDFiD (structure analysis) → upload to VirusTotal (optional, subject to privacy policy) → image-render in headless container → discard original PDF after conversion to image. 4. Set `Content-Disposition: attachment` and `Content-Security-Policy` headers on document download responses to prevent browser-side PDF rendering. 5. Keep ClamAV signatures updated daily via a cron job in the ECS task definition. |

---

### EC-SEC-007: Audit Log Tampering (Application Status History Altered)

| Field | Details |
|---|---|
| **Failure Mode** | A database administrator or a compromised superuser account executes `UPDATE audit_logs SET action='APPROVED' WHERE id='...'` or `DELETE FROM audit_logs WHERE application_id='...'` to cover up a fraudulent approval or a bribe-related action. The audit log table was created as a regular PostgreSQL table with no write-protection, relying solely on application-level enforcement (the ORM never calls `update` or `delete` on audit log records). A superuser bypasses the ORM entirely. |
| **Impact** | The audit trail — the primary mechanism for detecting and prosecuting fraud in government service delivery — is compromised. If audit logs can be altered, the portal cannot be used as evidence in anti-corruption proceedings. This undermines the legal admissibility of the portal's records and violates the requirements of the Right to Information Act (Nepal) and the e-governance policy mandating immutable audit trails. |
| **Detection** | AWS CloudTrail captures all RDS Data API calls. AWS Config rule monitors IAM policy changes. Custom integrity check: a nightly job computes a rolling SHA-256 hash chain over all audit log entries (each entry's hash includes the hash of the previous entry). If the chain is broken, an alert fires. Hash chain values are stored in a separate, write-once S3 bucket. |
| **Mitigation / Recovery** | 1. Compare the current audit log state with the latest S3 hash chain export to identify modified or deleted records. 2. Restore deleted/modified records from the most recent RDS point-in-time backup (RPO: 15 minutes). 3. Identify the IAM principal that executed the unauthorized DML from CloudTrail logs. 4. Revoke the compromised IAM credentials immediately. 5. Escalate to the security incident response team and the relevant anti-corruption authority. |
| **Prevention** | 1. Create a dedicated PostgreSQL role `audit_writer` with `INSERT`-only permission on `audit_logs`. The Django application connects as this role for audit log writes. No `UPDATE` or `DELETE` permission is granted. 2. Revoke superuser access from the application's database user entirely. Superuser access should require a break-glass procedure with dual-approval. 3. Enable PostgreSQL audit logging (`pgaudit`) to capture all DDL and DML on `audit_logs`. 4. Export audit logs to an immutable S3 bucket (Object Lock, COMPLIANCE mode, 7-year retention) in near-real-time using a DMS task or a Lambda trigger on CloudWatch Logs. 5. Implement the hash chain integrity check as described above. |

---

### EC-SEC-008: Mass Data Extraction via Paginated API (Rate-Limit Bypass)

| Field | Details |
|---|---|
| **Failure Mode** | The officer API exposes a paginated list endpoint: `GET /api/v1/officer/applications/?page=1&page_size=100`. An attacker who has compromised an officer account (or a malicious insider) writes a script that iterates through all pages (`page=1` through `page=500`) in rapid succession, extracting the full names, NID numbers, addresses, and document metadata of all citizens who have ever submitted an application. The API's rate limiter is set to 1000 requests per hour per user, which is generous enough to allow full extraction in under 10 minutes. |
| **Impact** | Full exfiltration of citizen PII from the portal's database via a legitimate API endpoint. Up to hundreds of thousands of citizen records exposed. This is a Critical breach under the Nepal Privacy Act 2018 with mandatory 72-hour breach notification obligations. The operator faces regulatory sanctions and loss of the public's trust in digital government services. |
| **Detection** | CloudWatch anomaly detection on `api_requests_per_user_per_minute > 100` fires an alert. The specific pattern of sequential `page` parameter increments is detected by a Kinesis Data Analytics streaming job. AWS WAF rule detects pagination-abuse patterns (incrementing `page` parameter from the same IP/user). |
| **Mitigation / Recovery** | 1. Immediately revoke the compromised officer's JWT tokens and add to the blacklist. 2. Analyse CloudFront/ALB access logs to determine the full scope of extraction (which pages, which time window). 3. Notify the Nepal Privacy Act 2018 data protection authority within 72 hours. 4. Notify affected citizens if individual data exposure is confirmed. 5. Temporarily lower the rate limit to 100 requests per hour for all officer accounts while the investigation proceeds. |
| **Prevention** | 1. Implement per-endpoint rate limits in addition to per-user limits: `application_list` endpoint is limited to 30 requests per minute per officer. 2. Add cursor-based pagination (`?cursor=xyz`) instead of offset pagination, making it harder to automate sequential extraction (cursors are opaque and expire after 5 minutes). 3. Restrict the `page_size` maximum to 20 for the officer list endpoint (not 100). 4. Implement field-level access control: the officer list endpoint returns only fields required for queue display (`id`, `service_name`, `submitted_at`, `status`); full PII is only returned on the individual application detail endpoint. 5. Log and alert on any officer account that fetches more than 1000 distinct application records in 24 hours. |

---

## Appendix: Security Configuration Examples

### PII Log Masking Filter (Django)

```python
# apps/core/logging_filters.py
import logging
import re

PII_PATTERNS = {
    'nid_number': re.compile(r'"nid_number"\s*:\s*"([^"]+)"'),
    'phone_number': re.compile(r'"phone_number"\s*:\s*"([^"]+)"'),
    'date_of_birth': re.compile(r'"date_of_birth"\s*:\s*"([^"]+)"'),
}

class PIIMaskingFilter(logging.Filter):
    """
    Masks PII fields in log records before they are written to any handler.
    Apply to all Django log handlers in settings.LOGGING.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for field, pattern in PII_PATTERNS.items():
                record.msg = pattern.sub(f'"{field}": "***REDACTED***"', record.msg)
        return True
```

### JWT Blacklist Middleware

```python
# apps/auth/middleware.py
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

class BlacklistCheckingJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT to check a Redis blacklist on every request.
    The blacklist is populated when an account is suspended or a
    forced logout is triggered.
    """
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        user_id = token.get('user_id')
        if cache.get(f'jwt_blacklist:{user_id}'):
            raise AuthenticationFailed(
                'Account has been suspended. Please contact support.',
                code='account_suspended',
            )
        return token
```

### CSRF + CORS Settings

```python
# settings/security.py
# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://govportal.gov.np',
    'https://officer.govportal.gov.np',
]

# CORS
CORS_ALLOWED_ORIGINS = [
    'https://govportal.gov.np',
    'https://officer.govportal.gov.np',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### ClamAV Scan Snippet (Python/Django)

```python
# apps/documents/scanners.py
import subprocess
import tempfile
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ScanResult:
    is_clean: bool
    threat_name: str | None
    raw_output: str

def scan_file_with_clamav(file_bytes: bytes, filename: str) -> ScanResult:
    """
    Scans uploaded file bytes with ClamAV (clamd daemon via clamdscan).
    Raises RuntimeError if clamdscan is not available.

    Usage in document upload view:
        result = scan_file_with_clamav(request.data['file'].read(), request.data['file'].name)
        if not result.is_clean:
            raise ValidationError(f"File failed security scan: {result.threat_name}")
    """
    # Write to an in-process temp path (not /tmp) — use a named pipe or memory file
    scan_path = Path(f'/dev/shm/{filename}')
    try:
        scan_path.write_bytes(file_bytes)
        result = subprocess.run(
            ['clamdscan', '--fdpass', str(scan_path)],
            capture_output=True, text=True, timeout=30
        )
        is_clean = result.returncode == 0
        threat_name = None
        if not is_clean:
            # Parse: "/path/to/file: Eicar-Signature FOUND"
            for line in result.stdout.splitlines():
                if 'FOUND' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        threat_name = parts[-1].strip().replace(' FOUND', '')
                    break
        return ScanResult(
            is_clean=is_clean,
            threat_name=threat_name,
            raw_output=result.stdout
        )
    finally:
        scan_path.unlink(missing_ok=True)
```

### Rate Limiting Configuration (Django REST Framework)

```python
# settings/api_throttling.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'apps.core.throttling.EndpointSpecificThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '1000/hour',
        # Endpoint-specific rates (enforced by EndpointSpecificThrottle)
        'application_submit': '10/hour',
        'application_list_officer': '30/minute',
        'nid_verify': '5/minute',
        'document_download': '100/hour',
        'password_reset': '3/hour',
    }
}
```

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policy (Nepal Privacy Act 2018)

- All personally identifiable information (PII) collected by the Nepal Government Services Portal is governed by the **Nepal Privacy Act 2018 (Goptaniyata Sambandhi Ain, 2075)**. The portal collects only the minimum PII required to deliver the requested government service (data minimisation principle).
- NID numbers are stored as one-way salted hashes in the primary database and are never written to application logs, error reports, or analytics pipelines. The plaintext NID number is used only in-memory during NASC verification and is discarded immediately after.
- Citizens have the right to: (a) access their personal data, (b) correct inaccurate data, (c) withdraw consent for non-mandatory data processing, and (d) request deletion of data related to withdrawn or rejected applications (subject to the 7-year mandatory e-governance audit retention period).
- A data breach incident must be reported to the relevant government ministry and, where individual citizen data is involved, to the affected citizens within **72 hours** of detection, as required by the Nepal Privacy Act 2018.

### 2. Service Delivery SLA Policy

- All government services on the portal have a defined statutory processing time (range: 7–21 working days) which is displayed to the citizen at the point of application submission. The SLA is enforced by the automated Celery escalation system.
- Officers who fail to act on an application within the SLA window are escalated to their supervisor. Persistent SLA breaches are reported to the relevant ministry head and the Ministry of Federal Affairs and General Administration (MoFAGA).
- Security incidents that impact service availability trigger an immediate SLA clock pause; affected citizens are notified via SMS (Nepal Telecom / Sparrow SMS gateway) and the portal's announcement banner.
- Security reviews, penetration tests, and compliance audits are conducted annually or following any security incident, and must not result in citizen-facing downtime exceeding the planned maintenance window.

### 3. Fee and Payment Policy

- Service fees are denominated in Nepalese Rupees (NPR / रू). VAT at 13% is applied to services as mandated by the Inland Revenue Department of Nepal, and is itemised separately on the payment receipt.
- The portal accepts payments via ConnectIPS, eSewa, and Khalti. All payment flows use HTTPS with TLS 1.2+ and verify webhook signatures (HMAC-SHA256) before processing any payment status update.
- Fees are frozen at submission time and are not affected by subsequent fee schedule changes. Fee updates are announced via the portal's announcement banner at least 7 days in advance.
- Refunds for rejected applications or confirmed system errors are processed via the original payment channel within 7 working days. The refund process is audited end-to-end, and each refund event is recorded in the immutable `audit_logs` table.

### 4. System Availability Policy

- The Nepal Government Services Portal targets **99.5% monthly uptime** for citizen-facing endpoints, measured by the AWS Route 53 health check from the `ap-south-1` region.
- Planned security maintenance (certificate rotation, OS patching, library updates) is performed during the approved maintenance window (11:00 PM – 5:00 AM NST, Saturday) with advance notice to citizens.
- Security patches rated Critical (CVSS ≥ 9.0) must be applied within **24 hours** of release regardless of the maintenance window, following the emergency patching process.
- Penetration testing, red team exercises, and security drills are conducted annually by an independent security firm approved by the Government of Nepal's Ministry of Information and Communication Technology (MoICT).
