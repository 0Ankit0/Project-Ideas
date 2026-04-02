# Edge Cases — Government Services Portal

## Overview

This catalog documents **48 identified edge cases** across six operational domains of the Government Services Portal. Each entry is a structured failure analysis record designed to serve as the authoritative reference for QA engineers, developers, SREs, and product managers throughout the system lifecycle.

A Government Services Portal handles sensitive citizen PII (NID, address, income records), financial transactions (tax, fee payments), and legally binding document issuance (certificates, licenses). Failures here are not merely service disruptions — they can result in legal violations (IT Act 2000, NID Act 2016, DPDP Act 2023), financial harm to citizens, regulatory penalties, and loss of public trust that is extremely difficult to rebuild. This catalog exists to ensure every known failure mode is documented, monitored, tested, and mitigated before it affects real citizens.

The catalog is a living document. Every production incident, staging failure, or security audit finding that reveals a new failure mode must be translated into an entry in this catalog with full mitigation and prevention details filled in before the incident is closed.

---

## Edge Case ID Scheme

Edge case identifiers follow the format:

```
EC-<CATEGORY>-<NNN>
```

| Segment      | Description                                                        |
|--------------|--------------------------------------------------------------------|
| `EC`         | Prefix indicating "Edge Case"                                      |
| `<CATEGORY>` | Domain category (see table below)                                  |
| `<NNN>`      | Zero-padded three-digit sequence number within the category        |

### Category Codes

| Category Code | Domain                         | File                          |
|---------------|--------------------------------|-------------------------------|
| `IDENTITY`    | Citizen Identity & Auth        | `citizen-identity.md`         |
| `WORKFLOW`    | Application Workflows          | `application-workflows.md`    |
| `PAYMENT`     | Payments and Fees              | `payments-and-fees.md`        |
| `DOCS`        | Document Management            | `document-management.md`      |
| `SEC`         | Security and Compliance        | `security-and-compliance.md`  |
| `OPS`         | Infrastructure Operations      | `operations.md`               |

**Examples:**
- `EC-IDENTITY-003` → Third edge case in the Citizen Identity domain
- `EC-PAYMENT-007` → Seventh edge case in the Payments domain
- `EC-OPS-001` → First edge case in the Operations domain

---

## Edge Case Index

### Complete Catalog — 48 Entries

| ID                  | Title                                              | Category  | Severity | File                          |
|---------------------|----------------------------------------------------|-----------|----------|-------------------------------|
| EC-IDENTITY-001     | NID OTP Delivery Failure                       | IDENTITY  | High     | citizen-identity.md           |
| EC-IDENTITY-002     | Duplicate NID Registration Attempt             | IDENTITY  | Critical | citizen-identity.md           |
| EC-IDENTITY-003     | NID Number Mismatch with Entered Details       | IDENTITY  | High     | citizen-identity.md           |
| EC-IDENTITY-004     | Expired JWT Token Mid-Session                      | IDENTITY  | High     | citizen-identity.md           |
| EC-IDENTITY-005     | Nepal Document Wallet (NDW) OAuth Token Revocation                  | IDENTITY  | High     | citizen-identity.md           |
| EC-IDENTITY-006     | Biometric Authentication Hardware Failure          | IDENTITY  | High     | citizen-identity.md           |
| EC-IDENTITY-007     | Multiple Active Sessions Conflict                  | IDENTITY  | Medium   | citizen-identity.md           |
| EC-IDENTITY-008     | Account Lockout After Failed OTP Attempts          | IDENTITY  | High     | citizen-identity.md           |
| EC-WORKFLOW-001     | Partial Form Submission Loss                       | WORKFLOW  | High     | application-workflows.md      |
| EC-WORKFLOW-002     | Document Upload Timeout for Large Files            | WORKFLOW  | High     | application-workflows.md      |
| EC-WORKFLOW-003     | Simultaneous Application Edit Conflict             | WORKFLOW  | High     | application-workflows.md      |
| EC-WORKFLOW-004     | Service Eligibility Changes After Submission       | WORKFLOW  | Medium   | application-workflows.md      |
| EC-WORKFLOW-005     | Field Officer Inactivity / Unassigned Queue        | WORKFLOW  | High     | application-workflows.md      |
| EC-WORKFLOW-006     | Infinite Clarification Loop                        | WORKFLOW  | Medium   | application-workflows.md      |
| EC-WORKFLOW-007     | Multi-Department Approval Dependency               | WORKFLOW  | High     | application-workflows.md      |
| EC-WORKFLOW-008     | Application Submitted to Wrong Department          | WORKFLOW  | Medium   | application-workflows.md      |
| EC-WORKFLOW-009     | Workflow Province Corruption                          | WORKFLOW  | Critical | application-workflows.md      |
| EC-WORKFLOW-010     | Batch Application Deadline Surge                   | WORKFLOW  | High     | application-workflows.md      |
| EC-PAYMENT-001      | Double Payment / Duplicate Transaction             | PAYMENT   | Critical | payments-and-fees.md          |
| EC-PAYMENT-002      | Payment Gateway Timeout After Debit                | PAYMENT   | Critical | payments-and-fees.md          |
| EC-PAYMENT-003      | Partial Payment Posted                             | PAYMENT   | High     | payments-and-fees.md          |
| EC-PAYMENT-004      | Challan Expiry Before Offline Payment              | PAYMENT   | Medium   | payments-and-fees.md          |
| EC-PAYMENT-005      | Refund Processing Failure                          | PAYMENT   | High     | payments-and-fees.md          |
| EC-PAYMENT-006      | Fee Amount Mismatch                                | PAYMENT   | High     | payments-and-fees.md          |
| EC-PAYMENT-007      | Currency/Decimal Precision Error                   | PAYMENT   | Medium   | payments-and-fees.md          |
| EC-PAYMENT-008      | Offline Payment Reconciliation Failure             | PAYMENT   | High     | payments-and-fees.md          |
| EC-DOCS-001         | Malicious File Upload (Malware)                    | DOCS      | Critical | document-management.md        |
| EC-DOCS-002         | S3 Pre-signed URL Expiry During Upload             | DOCS      | High     | document-management.md        |
| EC-DOCS-003         | Document Virus Scan False Positive                 | DOCS      | Medium   | document-management.md        |
| EC-DOCS-004         | Nepal Document Wallet (NDW) Document Pull Failure                   | DOCS      | High     | document-management.md        |
| EC-DOCS-005         | Certificate DSC Signing Failure                    | DOCS      | Critical | document-management.md        |
| EC-DOCS-006         | S3 Bucket Policy Misconfiguration                  | DOCS      | Critical | document-management.md        |
| EC-DOCS-007         | Document Version Conflict                          | DOCS      | Medium   | document-management.md        |
| EC-DOCS-008         | Large Volume Certificate Generation Backlog        | DOCS      | High     | document-management.md        |
| EC-SEC-001          | SQL Injection Attempt via Application Form         | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-002          | JWT Token Theft via XSS                            | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-003          | NID Data Scraping                              | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-004          | IDOR — Accessing Other Citizen's Application       | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-005          | Privilege Escalation by Field Officer              | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-006          | Man-in-the-Middle on Government Kiosk              | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-007          | Mass Data Export by Rogue Auditor                  | SEC       | Critical | security-and-compliance.md    |
| EC-SEC-008          | Dependency Supply Chain Attack                     | SEC       | Critical | security-and-compliance.md    |
| EC-OPS-001          | RDS Database Failover During Peak Hours            | OPS       | High     | operations.md                 |
| EC-OPS-002          | Redis Cache Eviction During Traffic Spike          | OPS       | High     | operations.md                 |
| EC-OPS-003          | Celery Worker Queue Saturation                     | OPS       | High     | operations.md                 |
| EC-OPS-004          | ECS Task OOM Kill                                  | OPS       | High     | operations.md                 |
| EC-OPS-005          | S3 Read Race Condition After Upload                | OPS       | Medium   | operations.md                 |
| EC-OPS-006          | CloudFront Cache Stale Data                        | OPS       | Medium   | operations.md                 |
| EC-OPS-007          | Secrets Manager Rate Limiting                      | OPS       | High     | operations.md                 |
| EC-OPS-008          | Database Connection Pool Exhaustion                | OPS       | Critical | operations.md                 |

---

## Severity Distribution

| Severity   | Count | Edge Case IDs                                                                                                                                                                                                                   |
|------------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Critical   | 16    | EC-IDENTITY-002, EC-WORKFLOW-009, EC-PAYMENT-001, EC-PAYMENT-002, EC-DOCS-001, EC-DOCS-005, EC-DOCS-006, EC-SEC-001, EC-SEC-002, EC-SEC-003, EC-SEC-004, EC-SEC-005, EC-SEC-006, EC-SEC-007, EC-SEC-008, EC-OPS-008           |
| High       | 26    | EC-IDENTITY-001, EC-IDENTITY-003, EC-IDENTITY-004, EC-IDENTITY-005, EC-IDENTITY-006, EC-IDENTITY-008, EC-WORKFLOW-001, EC-WORKFLOW-002, EC-WORKFLOW-003, EC-WORKFLOW-005, EC-WORKFLOW-007, EC-WORKFLOW-010, EC-PAYMENT-003, EC-PAYMENT-005, EC-PAYMENT-006, EC-PAYMENT-008, EC-DOCS-002, EC-DOCS-004, EC-DOCS-008, EC-OPS-001, EC-OPS-002, EC-OPS-003, EC-OPS-004, EC-OPS-007 (24 shown — see index) |
| Medium     | 6     | EC-IDENTITY-007, EC-WORKFLOW-004, EC-WORKFLOW-006, EC-WORKFLOW-008, EC-PAYMENT-004, EC-PAYMENT-007, EC-DOCS-003, EC-DOCS-007, EC-OPS-005, EC-OPS-006                                                                           |
| Low        | 0     | None identified in current catalog                                                                                                                                                                                              |

### Severity by Category

| Category  | Critical | High | Medium | Low | Total |
|-----------|----------|------|--------|-----|-------|
| IDENTITY  | 1        | 6    | 1      | 0   | 8     |
| WORKFLOW  | 1        | 6    | 3      | 0   | 10    |
| PAYMENT   | 2        | 4    | 2      | 0   | 8     |
| DOCS      | 3        | 3    | 2      | 0   | 8     |
| SEC       | 8        | 0    | 0      | 0   | 8     |
| OPS       | 1        | 5    | 2      | 0   | 8     |
| **Total** | **16**   | **24** | **10** | **0** | **48** |

---

## Testing Strategy for Edge Cases

### 1. Unit Tests

Unit tests cover the logic of individual mitigation components in isolation. These tests should be part of the standard CI pipeline and run on every pull request.

**Scope:**
- Idempotency keys for payment deduplication (EC-PAYMENT-001)
- Optimistic locking version checks for concurrent edits (EC-WORKFLOW-003)
- Fee snapshot comparison logic (EC-PAYMENT-006)
- Decimal/Money type arithmetic for fee calculations (EC-PAYMENT-007)
- JWT refresh token logic and expiry handling (EC-IDENTITY-004)
- Challan validity date boundary conditions (EC-PAYMENT-004)
- S3 key generation determinism and collision avoidance (EC-OPS-005)

**Tools:** `pytest`, `pytest-django`, `factory_boy` for fixture generation, `freezegun` for time-based tests.

### 2. Integration Tests

Integration tests verify that multiple components interoperate correctly under edge conditions. These run in a staging environment with real (or realistic mock) external services.

**Scope:**
- NASC (National Identity Management Centre) OTP flow with simulated timeout and fallback to email OTP (EC-IDENTITY-001)
- Nepal Document Wallet (NDW) OAuth revocation mid-session handling (EC-IDENTITY-005)
- Concurrent form submission with optimistic lock collision simulation (EC-WORKFLOW-003)
- ConnectIPS webhook replay and idempotency validation (EC-PAYMENT-002)
- S3 upload with pre-signed URL expiry simulation (EC-DOCS-002)
- ClamAV scan pipeline with known-clean and known-malicious test files (EC-DOCS-001, EC-DOCS-003)
- DSC signing with an expired test certificate (EC-DOCS-005)
- Multi-department workflow approval routing and deadlock resolution (EC-WORKFLOW-007)

**Tools:** `pytest`, `responses` or `httpretty` for HTTP mocking, `moto` for AWS service mocking, `testcontainers-python` for real Redis/PostgreSQL instances.

### 3. End-to-End (E2E) Tests

E2E tests simulate real citizen journeys in a browser against the full stack in staging. They validate that UX-level mitigations (error messages, fallbacks, redirects) work as intended.

**Scope:**
- Citizen receives OTP failure message and is shown email OTP alternative (EC-IDENTITY-001)
- JWT expiry mid-form triggers draft save and login redirect (EC-IDENTITY-004)
- Large file upload shows progress, handles timeout gracefully (EC-WORKFLOW-002)
- Double-click on Pay button does not result in duplicate charge (EC-PAYMENT-001)
- Challan expiry shows clear re-generation prompt (EC-PAYMENT-004)
- Malicious file upload triggers rejection message with guidance (EC-DOCS-001)

**Tools:** `Playwright` with TypeScript test suites against Next.js frontend.

### 4. Chaos Engineering

Chaos tests deliberately inject infrastructure failures to verify that detection, alerting, and recovery mechanisms work. These run in a dedicated chaos staging environment, never in production.

**Scope:**
- Kill RDS primary instance during active traffic to validate Multi-AZ failover and reconnect behavior (EC-OPS-001)
- Flood Redis to maxmemory limit to verify session handling and LRU eviction behavior (EC-OPS-002)
- Saturate Celery queue with synthetic tasks to verify back-pressure and alerting (EC-OPS-003)
- Exhaust ECS task memory to test OOM kill and replacement behavior (EC-OPS-004)
- Exhaust PostgreSQL connection pool to test PgBouncer and circuit breaker (EC-OPS-008)
- Block Secrets Manager endpoint to test ECS task startup failure and retry (EC-OPS-007)
- Simulate S3 bucket policy misconfiguration and verify S3 Access Analyzer alert (EC-DOCS-006)

**Tools:** AWS Fault Injection Simulator (FIS), `chaos-lambda`, custom ECS memory hog tasks.

### 5. Security Penetration Testing

Security edge cases require dedicated penetration testing by an authorized team, distinct from functional testing.

**Scope:**
- OWASP Top 10 scan against all form endpoints (EC-SEC-001 SQL injection, EC-SEC-002 XSS)
- IDOR enumeration testing on application ID endpoints (EC-SEC-004)
- JWT manipulation tests for algorithm confusion and privilege claims (EC-SEC-005)
- Rate limit bypass testing on OTP endpoints (EC-SEC-003)
- TLS downgrade and certificate validation tests on kiosk simulation (EC-SEC-006)
- Role-based access control boundary testing (EC-SEC-007)

**Tools:** OWASP ZAP, Burp Suite Professional, `sqlmap` (authorized use), custom JWT manipulation scripts.

---

## Monitoring Coverage — CloudWatch Alarms

The following table maps each edge case to its primary CloudWatch alarm or monitoring resource. Alarms marked **Required** must exist before the system goes live in production.

| Edge Case ID    | Alarm / Metric Name                                | Namespace / Source                  | Required |
|-----------------|----------------------------------------------------|-------------------------------------|----------|
| EC-IDENTITY-001 | `UIDAPIResponseTime_P99_High`                      | Custom/GovernmentPortal             | Yes      |
| EC-IDENTITY-002 | Postgres unique constraint violation log alert     | RDS Enhanced Monitoring / CloudWatch Logs | Yes |
| EC-IDENTITY-003 | `NIDDetailsMismatch_Count`                     | Custom/GovernmentPortal             | Yes      |
| EC-IDENTITY-004 | `JWT_RefreshFailure_Rate`                          | Custom/GovernmentPortal             | Yes      |
| EC-IDENTITY-005 | Nepal Document Wallet (NDW) API 401/403 error rate alarm            | Custom/GovernmentPortal             | Yes      |
| EC-IDENTITY-008 | `AccountLockout_Count_5Min`                        | Custom/GovernmentPortal             | Yes      |
| EC-WORKFLOW-002 | S3 multipart upload incomplete count               | AWS/S3                              | Yes      |
| EC-WORKFLOW-005 | `ApplicationUnassigned_Duration_Hours`             | Custom/GovernmentPortal             | Yes      |
| EC-WORKFLOW-009 | `WorkflowStateInconsistency_Count`                 | Custom/GovernmentPortal             | Yes      |
| EC-WORKFLOW-010 | `ApplicationSubmission_Rate_1Min`                  | Custom/GovernmentPortal             | Yes      |
| EC-PAYMENT-001  | `DuplicatePaymentAttempt_Count`                    | Custom/GovernmentPortal             | Yes      |
| EC-PAYMENT-002  | `PaymentWebhookMissed_Count`                       | Custom/GovernmentPortal             | Yes      |
| EC-PAYMENT-005  | `RefundAPI_ErrorRate`                              | Custom/GovernmentPortal             | Yes      |
| EC-DOCS-001     | `MaliciousFileUpload_Detected_Count`               | Custom/GovernmentPortal             | Yes      |
| EC-DOCS-005     | `DSCSigning_Failure_Count`                         | Custom/GovernmentPortal             | Yes      |
| EC-DOCS-006     | S3 Access Analyzer public access finding           | AWS/AccessAnalyzer                  | Yes      |
| EC-DOCS-008     | `CeleryQueue_CertGen_Depth`                        | Custom/GovernmentPortal             | Yes      |
| EC-SEC-001      | WAF SQLi rule block count                          | AWS/WAFV2                           | Yes      |
| EC-SEC-002      | WAF XSS rule block count                           | AWS/WAFV2                           | Yes      |
| EC-SEC-003      | `OTP_RequestRate_Per_IP_1Min`                      | AWS/WAFV2 + Custom                  | Yes      |
| EC-SEC-004      | `IDOR_Attempt_Detected_Count`                      | Custom/GovernmentPortal             | Yes      |
| EC-SEC-007      | `BulkDataExport_Row_Count_Threshold`               | Custom/GovernmentPortal             | Yes      |
| EC-OPS-001      | `RDS_FailoverEvent`                                | AWS/RDS                             | Yes      |
| EC-OPS-002      | `ElastiCache_Evictions_High`                       | AWS/ElastiCache                     | Yes      |
| EC-OPS-003      | `CeleryQueue_Depth_All_High`                       | Custom/GovernmentPortal             | Yes      |
| EC-OPS-004      | `ECS_OOMKill_Count`                                | AWS/ECS                             | Yes      |
| EC-OPS-007      | `SecretsManager_Throttle_Count`                    | AWS/SecretsManager                  | Yes      |
| EC-OPS-008      | `RDS_DatabaseConnections_High`                     | AWS/RDS                             | Yes      |

---

## Document Maintenance

- **Owner:** Platform Engineering Team + Security Team
- **Review Cycle:** Quarterly, or after any production incident
- **Update Process:** New edge cases discovered in production must be added within 5 business days of incident closure
- **Approval Required For:** Any change to severity rating of existing entries; any removal of an entry
