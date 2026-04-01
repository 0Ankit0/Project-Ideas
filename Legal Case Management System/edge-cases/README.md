# Edge Cases — Legal Case Management System

## Overview

This folder documents every known edge case, failure mode, and exceptional workflow path in the Legal Case Management System (LCMS). Each sub-document covers a functional domain in depth: case lifecycle, document management, billing and time tracking, court deadlines, API and UI behavior, security and compliance, and operations.

Edge cases in legal software carry consequences that differ fundamentally from those in typical enterprise applications. A missed deadline is not a degraded user experience — it is malpractice exposure. An unauthorized document disclosure is not a privacy incident — it is an ethical violation that can result in bar discipline, disqualification of counsel, or evidence suppression. A trust accounting error is not a ledger imbalance — it is a potential violation of Rule 1.15 of the Model Rules of Professional Conduct, carrying sanctions up to license revocation.

This documentation exists so that engineers, QA teams, product managers, and legal technology administrators can understand, test, and mitigate these failure modes before they reach production.

---

## Why Edge Cases Matter in Legal Systems

### Malpractice Exposure

Legal malpractice claims arise when an attorney's negligence causes harm to a client. Software failures that contribute to malpractice include:

- **Missed statutes of limitations**: If the system fails to surface a deadline or miscalculates a court holiday, the underlying claim may be forever barred. The average legal malpractice verdict in the United States exceeds $250,000 per incident.
- **Conflict of interest failures**: If a conflict check is bypassed during emergency intake and the conflict is discovered post-engagement, the firm may be required to withdraw, disgorge fees, and face a malpractice claim from the harmed client.
- **Incorrect billing**: Systematic overbilling, even when unintentional, exposes the firm to fee arbitration, disgorgement, and reputational damage.
- **Lost or inaccessible documents**: If a critical case document is lost due to a system failure and that document was required evidence, the firm may face sanctions and a malpractice claim.

### Bar Association Violations

State bar rules impose affirmative obligations on attorneys that the LCMS must support:

- **Rule 1.3 (Diligence)**: Attorneys must act with reasonable diligence. Deadline management failures directly implicate this rule.
- **Rule 1.4 (Communication)**: Attorneys must keep clients reasonably informed. Client portal failures and notification system outages may constitute violations.
- **Rule 1.6 (Confidentiality)**: Attorneys must protect client confidences. Data breaches, inadvertent disclosures, and unauthorized access must be detected and reported.
- **Rule 1.7 / 1.9 (Conflicts)**: Attorneys must not represent clients with conflicting interests. The conflict check system is the primary technical safeguard.
- **Rule 1.15 (Safekeeping Property)**: Attorneys must maintain client trust funds separately and account for them accurately. IOLTA accounting errors are a leading cause of bar discipline.
- **Rule 1.16 (Declining or Terminating Representation)**: When attorneys depart mid-matter, specific notification and handoff obligations arise.

### Financial Penalties

Beyond malpractice liability, software failures can cause direct financial harm:

- **Trust account overdrafts**: Drawing against uncleared funds violates bar rules and can trigger banking penalties and regulatory scrutiny.
- **Escheatment failures**: Unclaimed trust funds must be remitted to the state after the required dormancy period. Failure to escheate results in penalties that compound annually.
- **LEDES billing rejections**: Insurance defense and corporate clients often mandate LEDES-formatted invoices. Validation failures delay payment and may result in invoice rejection under billing guidelines.
- **Court filing fees**: Failed PACER/CM-ECF submissions that result in untimely filings can require emergency motions to file out of time, with associated fees and reputational cost.
- **OFAC violations**: Accepting payment from a sanctioned entity without prior screening can result in civil penalties up to $1 million per transaction under 31 C.F.R. Part 501.

---

## Edge Case Inventory

The following table summarizes every documented edge case across all domain files. Severity is rated on a three-point scale:

| Rating | Label | Description |
|--------|-------|-------------|
| 🔴 | **Critical** | Can cause malpractice, bar violation, financial penalty, or data loss |
| 🟡 | **High** | Causes significant business disruption, client impact, or billing error |
| 🟢 | **Medium** | Degrades system usability or data consistency without immediate legal consequence |

### Case Lifecycle Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| CL-01 | Re-opening a closed matter without managing partner approval | 🔴 Critical | case-lifecycle.md |
| CL-02 | Merging two matters with conflicting parties | 🔴 Critical | case-lifecycle.md |
| CL-03 | Split billing across multiple clients on a single matter | 🟡 High | case-lifecycle.md |
| CL-04 | Attorney departure mid-matter without client notification | 🔴 Critical | case-lifecycle.md |
| CL-05 | Matter number collision detection across offices | 🟢 Medium | case-lifecycle.md |
| CL-06 | Conflict check failure discovered after matter is partially open | 🔴 Critical | case-lifecycle.md |
| CL-07 | Circular related-matter references causing infinite traversal | 🟢 Medium | case-lifecycle.md |
| CL-08 | Retroactive billing rate changes on finalized invoices | 🟡 High | case-lifecycle.md |
| CL-09 | Matter closed with zero time entries | 🟡 High | case-lifecycle.md |
| CL-10 | Emergency intake bypassing conflict check | 🔴 Critical | case-lifecycle.md |

### Document Management Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| DM-01 | Simultaneous document edits causing data loss | 🟡 High | document-management.md |
| DM-02 | Bates numbering gaps from deleted documents | 🟡 High | document-management.md |
| DM-03 | Inadvertent privilege waiver via document disclosure | 🔴 Critical | document-management.md |
| DM-04 | Litigation hold conflicts with retention policy | 🔴 Critical | document-management.md |
| DM-05 | Large file upload failure (>500 MB) | 🟢 Medium | document-management.md |
| DM-06 | OCR failure on handwritten documents | 🟢 Medium | document-management.md |
| DM-07 | E-signature timeout and expiry | 🟡 High | document-management.md |
| DM-08 | DocuSign webhook failure and missed completion event | 🟡 High | document-management.md |
| DM-09 | Version branch divergence (two attorneys editing separately) | 🟡 High | document-management.md |
| DM-10 | Document shared to wrong client portal | 🔴 Critical | document-management.md |
| DM-11 | Cross-matter document references causing unauthorized access | 🔴 Critical | document-management.md |

### Billing and Time Tracking Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| BT-01 | Time entry submitted after invoice finalization | 🟡 High | billing-and-time-tracking.md |
| BT-02 | Negative time entry and credit memo handling | 🟢 Medium | billing-and-time-tracking.md |
| BT-03 | Bulk import with duplicate time entry detection | 🟢 Medium | billing-and-time-tracking.md |
| BT-04 | Multi-currency billing for international clients | 🟡 High | billing-and-time-tracking.md |
| BT-05 | Write-off approval workflow exceeding threshold | 🟡 High | billing-and-time-tracking.md |
| BT-06 | Line-item invoice dispute while matter is ongoing | 🟡 High | billing-and-time-tracking.md |
| BT-07 | LEDES 1998B/2.0 file validation failures | 🟡 High | billing-and-time-tracking.md |
| BT-08 | Billing rate change mid-matter blended calculation | 🟡 High | billing-and-time-tracking.md |
| BT-09 | Contingency fee matter conversion to hourly | 🟡 High | billing-and-time-tracking.md |
| BT-10 | Trust account overdraft prevention | 🔴 Critical | billing-and-time-tracking.md |
| BT-11 | Unclaimed trust funds escheatment | 🔴 Critical | billing-and-time-tracking.md |
| BT-12 | Split origination credit calculation | 🟡 High | billing-and-time-tracking.md |

### Court Deadline Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| CD-01 | Deadline landing on court holiday | 🔴 Critical | court-deadlines.md |
| CD-02 | Overlapping statutes of limitations for the same claim | 🔴 Critical | court-deadlines.md |
| CD-03 | Single attorney acknowledgment when dual acknowledgment required | 🔴 Critical | court-deadlines.md |
| CD-04 | Court order retroactively modifying a deadline | 🟡 High | court-deadlines.md |
| CD-05 | PACER/CM-ECF submission failure at deadline | 🔴 Critical | court-deadlines.md |
| CD-06 | Time zone mismatch between local court and filing system | 🔴 Critical | court-deadlines.md |
| CD-07 | Emergency motion requiring same-day filing | 🟡 High | court-deadlines.md |
| CD-08 | Bankruptcy stay halting all active deadlines | 🟡 High | court-deadlines.md |
| CD-09 | Deadline cascade from single triggering event | 🟡 High | court-deadlines.md |
| CD-10 | Statute of limitations tolling (discovery rule, minor plaintiff) | 🔴 Critical | court-deadlines.md |

### API and UI Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| AU-01 | Concurrent API modification of the same matter | 🟡 High | api-and-ui.md |
| AU-02 | JWT expiry during long document upload | 🟡 High | api-and-ui.md |
| AU-03 | Large result set pagination consistency | 🟢 Medium | api-and-ui.md |
| AU-04 | API rate limiting under bulk PACER query load | 🟢 Medium | api-and-ui.md |
| AU-05 | Webhook delivery failure and idempotent retry | 🟡 High | api-and-ui.md |
| AU-06 | Client portal multi-tab session conflicts | 🟢 Medium | api-and-ui.md |
| AU-07 | Offline mobile time entry sync conflict | 🟡 High | api-and-ui.md |
| AU-08 | Search relevance degradation with large document sets | 🟢 Medium | api-and-ui.md |
| AU-09 | Deep link routing for court deadline notifications | 🟢 Medium | api-and-ui.md |
| AU-10 | CSRF protection on document upload forms | 🔴 Critical | api-and-ui.md |
| AU-11 | API versioning breaking change management | 🟡 High | api-and-ui.md |

### Security and Compliance Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| SC-01 | Attorney-client privilege breach detection | 🔴 Critical | security-and-compliance.md |
| SC-02 | GDPR data subject access request for client data | 🟡 High | security-and-compliance.md |
| SC-03 | Inadvertent privilege waiver via email | 🔴 Critical | security-and-compliance.md |
| SC-04 | Multi-jurisdiction data residency for cross-border matters | 🟡 High | security-and-compliance.md |
| SC-05 | 7-year audit trail retention for bar compliance | 🔴 Critical | security-and-compliance.md |
| SC-06 | Insider access to unassigned matters | 🔴 Critical | security-and-compliance.md |
| SC-07 | IOLTA trust accounting error correction | 🔴 Critical | security-and-compliance.md |
| SC-08 | OFAC sanctions screening for new clients | 🔴 Critical | security-and-compliance.md |
| SC-09 | 2FA bypass for emergency access | 🟡 High | security-and-compliance.md |
| SC-10 | Encryption key rotation without data loss | 🟡 High | security-and-compliance.md |
| SC-11 | Audit log tampering prevention | 🔴 Critical | security-and-compliance.md |
| SC-12 | SOC 2 evidence collection automation | 🟢 Medium | security-and-compliance.md |

### Operations Edge Cases

| ID | Edge Case | Severity | File |
|----|-----------|----------|------|
| OP-01 | Database failover during active court filing | 🔴 Critical | operations.md |
| OP-02 | Message queue overflow during bulk document import | 🟡 High | operations.md |
| OP-03 | Search index corruption recovery | 🟡 High | operations.md |
| OP-04 | Elasticsearch reindex during active queries | 🟢 Medium | operations.md |
| OP-05 | Zero-downtime deployment with in-flight transactions | 🟡 High | operations.md |
| OP-06 | Backup restoration IOLTA consistency check | 🔴 Critical | operations.md |
| OP-07 | Redis cache invalidation during billing rate updates | 🟡 High | operations.md |
| OP-08 | Court e-filing TLS certificate expiry | 🔴 Critical | operations.md |
| OP-09 | Third-party API outage (DocuSign, PACER) | 🟡 High | operations.md |
| OP-10 | IOLTA reconciliation discrepancy runbook | 🔴 Critical | operations.md |
| OP-11 | Monitoring alert fatigue and tuning | 🟢 Medium | operations.md |
| OP-12 | Capacity planning for discovery-heavy matters | 🟢 Medium | operations.md |

---

## Mitigation Strategies Overview

### Defensive Architecture Patterns

**Optimistic Locking with Version Vectors**: All mutable entities (Matter, Document, TimeEntry, Invoice) carry an integer `version` field. Every mutating API call must include the current version. The database layer rejects writes where the provided version does not match the stored version, returning HTTP 409 Conflict with a diff payload. Clients must re-fetch and re-apply their changes.

**Idempotency Keys**: All POST/PUT operations that trigger financial transactions, court filings, or document deliveries must accept an `Idempotency-Key` header. The key is stored in a Redis sorted set with a 24-hour TTL. Duplicate requests within the window return the cached response. This prevents double-billing, double-filing, and duplicate e-signatures.

**Dead Letter Queues**: Every event-driven workflow (document processing, webhook delivery, deadline notification) routes failed messages to a domain-specific dead letter queue after three attempts with exponential backoff. Ops staff receive a PagerDuty alert for any DLQ depth exceeding five messages.

**Circuit Breakers**: All external integrations (PACER, DocuSign, Westlaw, payment processors) are wrapped in Resilience4j circuit breakers. When error rate exceeds 50% over a 10-second sliding window, the circuit opens. Fallback strategies vary by criticality: PACER failures surface a user-visible warning and queue the filing for retry; DocuSign failures pause the signature workflow and notify the responsible attorney.

### Legal Domain Safeguards

**Conflict Check Immutability**: Once a conflict check record is created, its result fields are append-only. A new check must be created to override a prior result. The audit trail preserves who ordered each check, when it ran, and what the result was.

**Four-Eyes Approval for Financial Mutations**: Any operation above a configurable threshold (default: $10,000 write-off, $50,000 trust disbursement) requires approval from a second principal. The approval request and response are recorded in the immutable audit log.

**Litigation Hold Supremacy**: Retention policies are evaluated after litigation hold status. A document under an active litigation hold cannot be deleted, archived, or purged by any automated policy, regardless of its age or classification.

**Deadline Acknowledgment Chains**: All court deadlines require explicit acknowledgment by the responsible attorney of record. Dual-acknowledgment requirements (e.g., attorney and supervising partner) are enforced at the database constraint level, not only in application logic.

### Monitoring and Observability

**Structured Audit Logging**: Every user action and system event that touches a legal or financial record emits a structured log entry to an append-only audit log store (AWS CloudTrail + a dedicated PostgreSQL audit schema). Log entries include: actor, action, resource type, resource ID, before-state hash, after-state hash, client IP, session ID, and timestamp with microsecond precision.

**Anomaly Detection**: Automated rules fire on:
- Bulk data exports by non-admin users
- Access to matters by attorneys not on the matter team
- Trust disbursements outside normal business hours
- More than 50 document reads in a 5-minute window by a single user

**SLO Alerting**: Separate SLOs govern deadline-critical paths (P99 < 500 ms for deadline lookup) and financial paths (P99 < 1 s for trust account balance check). Violations page the on-call engineer immediately.

---

## How to Use This Documentation

1. **New Feature Development**: Before implementing any feature that touches matters, documents, billing, or deadlines, search this index by functional area and review the relevant edge case file.
2. **QA Test Planning**: Each edge case entry in the sub-documents includes a **Test Verification** section with specific scenarios. Use these as acceptance criteria.
3. **Incident Response**: When a production incident occurs, cross-reference the incident symptoms against this index to find the relevant runbook section in the operations or security documents.
4. **Onboarding**: Engineers new to the team should read this overview file and then read the edge case files for their assigned domain area before touching production code.
5. **Compliance Evidence**: The security-and-compliance edge case file contains procedures that satisfy SOC 2 Type II controls CC6, CC7, and CC8. Auditors may be directed to that file for control evidence.
