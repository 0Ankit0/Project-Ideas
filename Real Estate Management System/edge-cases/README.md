# Real Estate Management System — Edge Cases Index

## Overview

This directory contains structured edge-case documentation for the Real Estate Management System (REMS). Each file covers a specific domain area and documents the failure modes, their impact, detection signals, mitigation strategies, recovery steps, and prevention measures.

Edge cases in REMS have heightened stakes compared to typical SaaS platforms. Errors in lease records carry legal liability. Payment failures affect people's housing security. Fair Housing Act violations can trigger regulatory action. This documentation exists to ensure that every non-happy-path scenario has been thought through before it occurs in production.

All edge cases were identified through a combination of:
- Production incident retrospectives
- Regulatory compliance reviews (Fair Housing Act, FCRA, GDPR/CCPA)
- Threat modeling sessions for the payments and tenant-screening subsystems
- Stripe Connect integration review

---

## Risk Classification

| Risk Level | Criteria | Response SLA | Example |
|-----------|---------|-------------|---------|
| **Critical** | Financial loss, legal liability, or data breach affecting tenants or landlords | Immediate — P1 pager alert, < 15 min response | Payment double-charge; PII data breach |
| **High** | Significant disruption to operations or tenant experience; potential regulatory exposure | < 2 hours — P2 alert, on-call engineer | Background check API unavailable; lease renewal job failed |
| **Medium** | Feature degradation that affects a subset of users; workaround available | < 8 hours — P3 alert, next business hour | Search index staleness; duplicate maintenance requests |
| **Low** | Minor UX issue or edge case with minimal user impact; deferred resolution acceptable | < 48 hours — P4 ticket, next sprint | CSV import with mixed address formats; dashboard cache staleness |

---

## Edge-Case Index

| File | Domain Area | EC Count | Risk Level |
|------|------------|---------|-----------|
| [property-listings.md](./property-listings.md) | Property listing creation, geocoding, search | 6 | High–Medium |
| [tenant-management.md](./tenant-management.md) | Tenant screening, onboarding, PII management | 6 | Critical–Medium |
| [lease-lifecycle.md](./lease-lifecycle.md) | Lease creation, renewals, terminations, disputes | 6 | Critical–High |
| [maintenance-requests.md](./maintenance-requests.md) | Work order creation, dispatch, resolution | 6 | High–Medium |
| [api-and-ui.md](./api-and-ui.md) | API failures, UI rendering, integration errors | 6 | High–Low |
| [security-and-compliance.md](./security-and-compliance.md) | Fair Housing, GDPR/CCPA, fraud, access control | 6 | Critical–High |
| [operations.md](./operations.md) | Infrastructure, batch jobs, payment processing | 6 | Critical–Medium |

Total: **42 documented edge cases** across 7 domain areas.

---

## Risk Distribution Summary

| Risk Level | Count |
|-----------|-------|
| Critical | 9 |
| High | 16 |
| Medium | 12 |
| Low | 5 |

---

## Cross-Cutting Concerns

The following concerns apply across all edge cases in this directory. Each edge-case file references these concerns where relevant rather than repeating them in full.

### PII Handling

All Personally Identifiable Information (PII) — including tenant names, Social Security Numbers, date of birth, income documents, and bank account details — is:

- Encrypted at rest using AES-256 (RDS encryption, S3 SSE-S3)
- Encrypted in transit via TLS 1.2+
- Subject to field-level encryption for the most sensitive fields (SSN, bank account) using application-layer encryption before persistence
- Accessible only to roles with explicit need (property managers cannot access SSNs; only the screening subsystem can)

Any edge case that involves PII exposure, incorrect PII, or PII sent to the wrong party is automatically classified **Critical**.

### Audit Logging

Every state change to the following entities is captured in the `audit_log` table with: `entity_type`, `entity_id`, `action`, `actor_id`, `actor_role`, `before_state` (JSON), `after_state` (JSON), `timestamp`, and `ip_address`.

Covered entities:
- Leases (all state transitions)
- Payments (all payment events and status changes)
- Tenant applications (all status changes and decisions)
- Maintenance work orders (status changes, reassignments)
- User accounts (login, password change, role change, MFA events)

Audit logs are immutable and retained for **7 years** per FCRA requirements. They are replicated to S3 for long-term archival separate from the operational database.

### Multi-Tenant Isolation

REMS is a multi-tenant platform. Each landlord's data is isolated at the application layer via `landlord_id` on every resource. The following controls enforce isolation:

- **Row-level security (RLS)** is enabled on all core tables in PostgreSQL. Every query is executed with a `SET app.current_landlord_id` session variable, and RLS policies reject rows belonging to other landlords.
- **API middleware** validates that the JWT's `landlord_id` claim matches the resource being accessed.
- **Stripe Connect** ensures that each landlord can only access their own payment account via their `stripe_account_id`.

Any edge case involving data from one landlord being visible to another is automatically classified **Critical** and treated as a security incident.

### Idempotency

All payment operations, notification sends, and batch job runs are idempotent. Idempotency is enforced via:

- `idempotency_key` column on `payment_intents` and `notifications` tables
- Stripe API calls include a client-generated idempotency key
- Batch jobs record their run state in a `job_runs` table and skip already-processed records

Any edge case involving duplicate charges or duplicate notification sends references the idempotency mechanisms documented in `operations.md`.

### Regulatory Compliance References

Edge cases in this repository reference the following regulations:

| Regulation | Applicability |
|-----------|-------------|
| Fair Housing Act (FHA) | All tenant screening decisions and listing content |
| Fair Credit Reporting Act (FCRA) | Background check data handling, retention, and adverse action notices |
| GDPR | EU tenant PII, data subject rights, breach notification |
| CCPA | California tenant PII, right to delete, opt-out of sale |
| Stripe's Platform Agreement | Payment processing, fund flow, dispute handling |

All adverse action notices (rejecting a tenant application) must comply with FCRA Section 615, which requires notifying the applicant of the action, the consumer reporting agency used, and their right to dispute the report.
