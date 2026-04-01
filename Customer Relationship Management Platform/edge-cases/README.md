# Edge Cases — Customer Relationship Management Platform

**Version:** 1.0 | **Status:** Approved | **Last Updated:** 2025-07-15

---

## Overview

This catalog documents high-risk, non-obvious, and boundary-condition scenarios that the CRM platform must handle correctly. Each entry describes a failure mode, its detection mechanism, containment strategy, recovery procedure, and prevention controls. Edge cases are linked to their governing Business Rules (`BR-xx`) and Use Cases (`UC-xx`) to ensure traceability from requirement through implementation to operational handling.

These documents are the authoritative reference for engineering teams building or maintaining platform features, QA teams designing test suites, and support engineers triaging production incidents.

---

## Documentation Structure

The edge-case pack is organised into seven specialist documents, each covering a distinct risk domain:

| # | Document | Description |
|---|----------|-------------|
| 1 | [dedupe-merge-conflicts.md](./dedupe-merge-conflicts.md) | Duplicate detection algorithms, confidence scoring, merge conflict resolution, analyst review queue, and rollback procedures for contact and account deduplication. |
| 2 | [territory-reassignment.md](./territory-reassignment.md) | Bulk and individual territory reassignment flows, conflict resolution when deals span multiple territories, rep departure handling, and notification strategies. |
| 3 | [forecast-integrity.md](./forecast-integrity.md) | Snapshot drift detection, approved forecast immutability enforcement (BR-11), month-end reconciliation, multi-currency normalisation, and variance alerting. |
| 4 | [email-calendar-sync.md](./email-calendar-sync.md) | Bidirectional sync failure modes, OAuth token lifecycle, large-attachment handling, BCC privacy rules, recurring-meeting sync, and webhook retry/dead-letter strategy. |
| 5 | [api-and-ui.md](./api-and-ui.md) | Idempotency-key patterns, cursor-based pagination consistency, optimistic locking with ETags, stale-state UI handling, and per-tenant rate-limiting behaviour. |
| 6 | [security-and-compliance.md](./security-and-compliance.md) | GDPR Right-to-be-Forgotten flow, RBAC permission matrix, field-level and record-level security, PII masking in API responses and exports, and penetration-testing controls. |
| 7 | [operations.md](./operations.md) | Incident lifecycle (P1-P4), SLO definitions, runbook summaries for PostgreSQL/Redis/Kafka/Elasticsearch failover, and backup-and-restore procedures. |

---

## Key Features

### Data Integrity
Covers scenarios where concurrent writes, merge operations, or pipeline mutations can corrupt persistent state. Includes merge-conflict resolution, optimistic locking, forecast snapshot immutability, and deduplication.

### Concurrency
Documents race conditions that arise from multi-user access: simultaneous territory reassignment, concurrent deal stage updates, duplicate idempotency-key submissions, and parallel forecast submissions for overlapping periods.

### Compliance
Addresses GDPR Article 17 (erasure), GDPR Article 30 (processing records), and SOC 2 Type II audit requirements. Covers pseudonymisation of audit logs, consent-gate enforcement, and role-based access to sensitive fields.

### Sync Failures
Covers partial and total failures in bidirectional email and calendar synchronisation: OAuth token expiry, webhook delivery failures with dead-letter queues, sync gap detection, and re-sync idempotency.

### API Consistency
Documents stable pagination under concurrent inserts, idempotent retry semantics, ETag-based conflict detection, stale-while-revalidate caching behaviour, and rate-limiting feedback to API consumers.

---

## Edge Case Master Catalogue

The table below lists every named edge case across all seven documents, grouped by domain. Severity is rated on a four-point scale (Critical / High / Medium / Low) reflecting potential business impact if the edge case is unhandled.

### Data Integrity Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-DI-01 | Circular merge detected (A to B, B to A) | Critical | dedupe-merge-conflicts.md | BR-05 | UC-12 |
| EC-DI-02 | Both records have active open deals during merge | Critical | dedupe-merge-conflicts.md | BR-05 | UC-12 |
| EC-DI-03 | Approved forecast mutated after submission | Critical | forecast-integrity.md | BR-11 | UC-18 |
| EC-DI-04 | Deal value changes after forecast submitted but not yet approved | High | forecast-integrity.md | BR-11 | UC-18 |
| EC-DI-05 | Custom field conflict on merge (both records have different values) | High | dedupe-merge-conflicts.md | BR-05 | UC-12 |
| EC-DI-06 | Multi-currency deal in forecast without FX rate at submission time | High | forecast-integrity.md | BR-11 | UC-20 |
| EC-DI-07 | Different email addresses on merge (primary vs secondary) | Medium | dedupe-merge-conflicts.md | BR-05 | UC-12 |

### Concurrency Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-CC-01 | Simultaneous territory reassignment of the same account | Critical | territory-reassignment.md | BR-07 | UC-14 |
| EC-CC-02 | Concurrent PUT on same contact without If-Match header | High | api-and-ui.md | BR-02 | UC-03 |
| EC-CC-03 | Duplicate idempotency-key submitted from two parallel requests | High | api-and-ui.md | BR-02 | UC-03 |
| EC-CC-04 | Rep submits forecast for period overlapping approved forecast | High | forecast-integrity.md | BR-11 | UC-18 |
| EC-CC-05 | Bulk reassignment job and manual reassignment collide on same account | Medium | territory-reassignment.md | BR-07 | UC-14 |
| EC-CC-06 | Pagination cursor drift during concurrent record inserts | Medium | api-and-ui.md | BR-02 | UC-03 |

### Compliance Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-CP-01 | GDPR erasure request for contact linked to active open deals | Critical | security-and-compliance.md | BR-15 | UC-22 |
| EC-CP-02 | Audit log contains PII visible to non-Admin role | Critical | security-and-compliance.md | BR-15 | UC-22 |
| EC-CP-03 | Rep accesses another rep's lead record without manager role | High | security-and-compliance.md | BR-14 | UC-21 |
| EC-CP-04 | Audit log export attempted without MFA re-authentication | High | security-and-compliance.md | BR-15 | UC-22 |
| EC-CP-05 | BCC-only email tracked as activity without consent | Medium | email-calendar-sync.md | BR-13 | UC-19 |
| EC-CP-06 | CSV export of contacts with PII by non-Admin role | Medium | security-and-compliance.md | BR-15 | UC-22 |
| EC-CP-07 | Field-level security bypass via bulk update API | High | security-and-compliance.md | BR-14 | UC-21 |

### Sync Failures Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-SF-01 | OAuth refresh token expired; user not notified | High | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-02 | Webhook dead-letter after 5 failed deliveries | High | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-03 | Sync gap > 24 hours detected for mailbox | High | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-04 | Large attachment (> 25 MB) in synced email | Medium | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-05 | Recurring meeting updated at series level after single occurrence edit | Medium | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-06 | Meeting deleted in external calendar; CRM activity preservation | Medium | email-calendar-sync.md | BR-12 | UC-19 |
| EC-SF-07 | Rep has personal and work Google accounts both connected | Medium | email-calendar-sync.md | BR-12 | UC-19 |

### API Consistency Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-AC-01 | Expired cursor (> 1 hour) used in paginated request | Medium | api-and-ui.md | BR-02 | UC-03 |
| EC-AC-02 | 429 response without Retry-After header | Medium | api-and-ui.md | BR-02 | UC-03 |
| EC-AC-03 | Optimistic lock conflict on non-conflicting field | Low | api-and-ui.md | BR-02 | UC-03 |
| EC-AC-04 | Idempotency key reused across tenants | High | api-and-ui.md | BR-02 | UC-03 |
| EC-AC-05 | Stale UI state after WebSocket disconnect | Medium | api-and-ui.md | BR-02 | UC-03 |

### Operations Domain

| ID | Edge Case | Severity | Document | BR Link | UC Link |
|----|-----------|----------|----------|---------|---------|
| EC-OP-01 | PostgreSQL primary failover during bulk reassignment | Critical | operations.md | BR-16 | UC-23 |
| EC-OP-02 | Kafka consumer lag spike causing lead assignment delay > 30s | High | operations.md | BR-16 | UC-23 |
| EC-OP-03 | Elasticsearch indexing backlog causing stale search results | High | operations.md | BR-16 | UC-23 |
| EC-OP-04 | Redis cluster failure causing idempotency-key cache miss | High | operations.md | BR-16 | UC-23 |
| EC-OP-05 | S3 backup restore fails due to corrupted snapshot | Critical | operations.md | BR-16 | UC-23 |
| EC-OP-06 | P1 incident with no on-call SRE response within 1 minute | Critical | operations.md | BR-16 | UC-23 |

---

## Severity Classification

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | Data loss, incorrect financial reporting, compliance breach, or complete feature outage affecting all users | Approved forecast mutated; GDPR erasure incomplete within 30 days |
| **High** | Core workflow broken for a subset of users; significant data quality risk; security escalation required | OAuth token expired without notification; merge with active deals |
| **Medium** | Degraded experience; data correctness risk that can be remediated; minor security concern | Large attachment not stored; pagination cursor drift |
| **Low** | Cosmetic issue; recoverable without data risk; no security impact | Optimistic lock conflict on non-conflicting field |

---

## Linkage to Business Rules

| Business Rule | Summary | Edge Cases |
|---------------|---------|------------|
| BR-02 | API requests must be idempotent and use consistent pagination | EC-CC-03, EC-CC-06, EC-AC-01 through EC-AC-05 |
| BR-05 | Duplicate contacts must be merged with full audit trail | EC-DI-01 through EC-DI-07 |
| BR-07 | Territory changes must not orphan accounts or deals | EC-CC-01, EC-CC-05 |
| BR-11 | Approved forecasts are immutable; amendments require adjustment records | EC-DI-03, EC-DI-04, EC-CC-04, EC-DI-06 |
| BR-12 | Email and calendar sync must maintain < 5-min lag and full history | EC-SF-01 through EC-SF-07 |
| BR-13 | BCC emails must not be logged as CRM activities | EC-CP-05 |
| BR-14 | Record-level security enforced at all API layers | EC-CP-03, EC-CP-07 |
| BR-15 | GDPR erasure must complete within 30 days with pseudonymised audit log | EC-CP-01, EC-CP-02, EC-CP-04, EC-CP-06 |
| BR-16 | Platform SLOs and runbooks must be tested monthly | EC-OP-01 through EC-OP-06 |

---

## Linkage to Use Cases

| Use Case | Summary | Edge Cases |
|----------|---------|------------|
| UC-03 | Manage CRM API access and integration | EC-CC-02, EC-CC-03, EC-CC-06, EC-AC-01 through EC-AC-05 |
| UC-12 | Deduplicate and merge contact/account records | EC-DI-01 through EC-DI-07 |
| UC-14 | Manage territory assignments | EC-CC-01, EC-CC-05 |
| UC-18 | Submit and approve sales forecasts | EC-DI-03, EC-DI-04, EC-CC-04, EC-DI-06 |
| UC-19 | Sync email and calendar activities | EC-SF-01 through EC-SF-07, EC-CP-05 |
| UC-20 | Manage multi-currency deal pipeline | EC-DI-06 |
| UC-21 | Enforce role-based data access | EC-CP-03, EC-CP-07 |
| UC-22 | Process GDPR data subject requests | EC-CP-01, EC-CP-02, EC-CP-04, EC-CP-06 |
| UC-23 | Operate and recover platform infrastructure | EC-OP-01 through EC-OP-06 |

---

## Getting Started

### How to Use This Documentation

1. **Find your domain.** Use the Edge Case Master Catalogue table above to locate edge cases relevant to the feature or workflow you are working on.
2. **Read the specialist document.** Each linked document contains full scenario descriptions, resolution logic, sequence diagrams, and audit requirements.
3. **Check BR and UC links.** Cross-reference the governing business rule and use case before implementing any resolution logic to ensure consistency with requirements.
4. **Write tests.** Each edge case should have at least one integration test covering the happy path to failure transition and the resolution outcome.
5. **Validate in staging.** All Critical and High severity edge cases must be validated in the staging environment before a related feature is released to production.

### Severity Triage Guide

- **Critical:** Stop current work. Escalate immediately to service owner and VP Engineering if in production. Do not deploy any related changes until resolved.
- **High:** Address in the current sprint. Requires explicit sign-off from engineering lead before release.
- **Medium:** Address in the next planned sprint. Document workaround for support team.
- **Low:** Backlog item. Address when related code is touched.

---

## Documentation Status

| Document | Version | Status | Reviewer | Last Updated |
|----------|---------|--------|----------|--------------|
| README.md (this file) | 1.0 | Approved | Platform Architect | 2025-07-15 |
| dedupe-merge-conflicts.md | 1.0 | Approved | Data Quality Lead | 2025-07-15 |
| territory-reassignment.md | 1.0 | Approved | Sales Ops Lead | 2025-07-15 |
| forecast-integrity.md | 1.0 | Approved | RevOps Lead | 2025-07-15 |
| email-calendar-sync.md | 1.0 | Approved | Integration Lead | 2025-07-15 |
| api-and-ui.md | 1.0 | Approved | API Platform Lead | 2025-07-15 |
| security-and-compliance.md | 1.0 | Approved | Security Lead | 2025-07-15 |
| operations.md | 1.0 | Approved | SRE Lead | 2025-07-15 |

---

*For questions or corrections, raise a documentation issue in the CRM Platform repository and tag the relevant document owner.*
