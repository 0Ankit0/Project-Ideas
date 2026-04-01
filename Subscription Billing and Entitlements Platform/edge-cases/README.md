# Edge Cases — Subscription Billing and Entitlements Platform

This directory contains the authoritative failure-mode catalog for the Subscription Billing and Entitlements Platform. Every document here represents real production risks: billing defects carry direct revenue impact, regulatory exposure, and customer trust damage. Engineers, QA leads, product managers, and on-call SREs should treat these documents as living references — not aspirational checklists.

The goal of this documentation is to make the unknown known. Billing systems fail in subtle, compounding ways. A proration miscalculation can cascade into a dunning cycle, which can cascade into a customer dispute, which can cascade into a chargeback. This catalog exists so that each failure mode is anticipated, detected early, and recovered from systematically.

---

## Documentation Structure

| File | Domain | Failure Modes Documented | Primary Audience |
|------|--------|--------------------------|------------------|
| [proration.md](./proration.md) | Plan changes, billing cycle math | 12 | Backend Engineers, Billing Team |
| [dunning-retries.md](./dunning-retries.md) | Payment retry, grace periods | 12 | Backend Engineers, Customer Success |
| [credit-notes.md](./credit-notes.md) | Refunds, credits, adjustments | 12 | Finance, Backend Engineers |
| [tax-jurisdiction-rules.md](./tax-jurisdiction-rules.md) | Tax calculation, compliance | 12 | Finance, Tax Team, Backend Engineers |
| [api-and-ui.md](./api-and-ui.md) | API reliability, idempotency, UI | 12 | API Consumers, Frontend, QA |
| [security-and-compliance.md](./security-and-compliance.md) | PCI DSS, GDPR, SOC 2 | 12 | Security, Compliance, SRE |
| [operations.md](./operations.md) | Infrastructure, pipelines, jobs | 12 | SRE, Platform Engineering |

Each document follows a consistent structure:
1. **Introduction** — Context and why this domain requires special care
2. **Failure Mode Table** — Structured catalog with detection and mitigation
3. **Domain-Specific Checklist or Runbook Index** — Actionable validation steps

---

## Key Features

### Comprehensive Failure Mode Catalog

Each of the 84 documented failure modes is classified by:

- **Failure Mode** — A precise, named description of what goes wrong. Names follow the pattern `[Trigger] → [System State]` so they can be referenced unambiguously in incident reports and regression tests.
- **Impact** — The business, financial, or compliance consequence if the failure is not caught. Impacts are expressed in terms observable to stakeholders: revenue leakage, regulatory risk, customer experience degradation, or data integrity loss.
- **Detection** — The observable signal that reveals the failure has occurred. Detection strategies include: metric thresholds, log patterns, reconciliation mismatches, alert conditions, and manual audit triggers.
- **Mitigation / Recovery** — Concrete, ordered recovery steps. Not generic advice. Where relevant, these include idempotency considerations, rollback procedures, customer communication triggers, and finance team notification requirements.

### Detection Strategies

Failure modes in this catalog are detectable through multiple complementary signals:

- **Metric-based detection**: Counters and gauges exposed via Prometheus/Grafana — e.g., `billing_proration_calculation_errors_total`, `dunning_retry_duplicate_count`, `invoice_tax_mismatch_gauge`.
- **Log-pattern detection**: Structured log queries in Datadog or CloudWatch — e.g., `event=proration_conflict concurrent_changes=true`.
- **Reconciliation-based detection**: Scheduled batch jobs that compare billing records against payment gateway ledgers, tax service audit trails, and general ledger entries.
- **Customer-reported signals**: Inbound support tickets categorized by billing issue type serve as a lagging but high-signal detector for systematic failures.
- **Audit trail gaps**: SOC 2 and PCI audit readiness reviews surface failures in logging and access control not visible in real-time metrics.

### Mitigation Playbooks

Recovery procedures documented here adhere to these principles:

1. **Idempotency First** — Every recovery action must be safe to execute more than once. Re-running a proration correction job must not double-apply adjustments.
2. **Audit Trail Preservation** — All manual corrections must be logged with actor identity, timestamp, and justification. Finance teams require an immutable correction ledger.
3. **Customer Communication Gating** — Recovery actions that change invoice amounts or subscription state must trigger customer notifications unless explicitly suppressed with justification.
4. **Least-Privilege Execution** — Correction scripts run under service accounts with scoped permissions. No manual `UPDATE` statements against production billing tables without change-management approval.

### Domain-Specific Coverage

| Domain | Why It Requires a Dedicated Document |
|--------|--------------------------------------|
| Proration | Billing math interacts with timezone offsets, plan configuration, trial states, and hybrid pricing in non-obvious ways. One bad formula affects every mid-cycle change. |
| Dunning Retries | The dunning engine is a state machine. Concurrency bugs, scheduler double-fires, and race conditions with payment method updates produce hard-to-reproduce failures with real churn impact. |
| Credit Notes | Credits interact with multi-currency accounts, invoice voiding, partial applications, and expiry windows. Incorrect credit application violates accounting standards. |
| Tax Jurisdiction Rules | SaaS tax is jurisdictionally complex. Errors produce regulatory penalties, not just billing mistakes. Tax logic must be correct at finalization, not at draft creation. |
| API and UI | Billing APIs require idempotency, versioning discipline, and graceful degradation. API failures in billing are not recoverable by retry in all cases. |
| Security and Compliance | PCI DSS, GDPR, and SOC 2 impose hard correctness requirements. Failures here are not just operational — they carry regulatory and legal consequences. |
| Operations | Billing infrastructure failures during month-end billing runs can affect thousands of customers simultaneously. Operational edge cases require runbook-level precision. |

---

## Getting Started

### For Engineers Implementing a New Feature

1. **Identify your domain** — Locate the relevant edge case file(s) for the area you are building in. A plan-change feature touches both `proration.md` and potentially `tax-jurisdiction-rules.md`.
2. **Review the full failure mode table** — Read every row, not just the ones that seem relevant. Billing interactions are non-obvious. A plan upgrade on day 1 of a cycle (zero proration days) looks like a no-op but has specific handling requirements.
3. **Map failure modes to acceptance criteria** — Each failure mode in the table should have a corresponding test case or explicitly acknowledged out-of-scope note in your design doc.
4. **Add new failure modes you discover** — If during implementation you encounter a failure mode not catalogued here, open a PR to add it before merging your feature. This documentation is the canonical record.

### For QA Engineers Writing Test Plans

1. **Use the failure mode tables as test case seeds** — Each row in a failure mode table maps directly to at least one test scenario. The "Detection" column describes what observable state to assert. The "Impact" column describes what incorrect behavior looks like.
2. **Prioritize by impact** — Revenue leakage and compliance failures are P0. Customer experience degradation is P1. Operational inefficiency is P2. Allocate test effort accordingly.
3. **Cover concurrency scenarios** — Several failure modes (concurrent plan changes, dunning race conditions, credit note double-issuance) require concurrent test execution, not sequential happy-path tests.
4. **Use the domain checklists** — Each document ends with a checklist. These are designed for pre-release sign-off.

### For On-Call SREs During an Incident

1. **Identify the domain of the incident** — Is this a billing run failure? Check `operations.md`. Customer reporting duplicate charges? Check `security-and-compliance.md` (double-charge prevention) and `api-and-ui.md` (idempotency key reuse).
2. **Cross-reference the failure mode** — Match the observable symptoms to a failure mode by detection signal. Each detection description references the metric name, log pattern, or alert that fires.
3. **Execute the mitigation steps in order** — Mitigation steps are ordered and idempotency-safe. Do not skip steps or execute them out of order.
4. **File an incident report referencing the failure mode ID** — Use the format `[domain-abbreviation]-[row-number]`, e.g., `PRO-3` for proration failure mode row 3. This links incidents to the catalog for future pattern analysis.

### For Finance and Compliance Teams

1. **Tax jurisdiction rules** — `tax-jurisdiction-rules.md` documents the scenarios where tax calculation can produce incorrect results and the reconciliation procedures to detect them.
2. **Credit notes and adjustments** — `credit-notes.md` documents the accounting edge cases that require manual ledger entries or credit note voiding.
3. **Audit readiness** — `security-and-compliance.md` provides the security compliance checklist that maps to SOC 2 control objectives and PCI DSS requirements.

---

## Documentation Status

| File | Status | Last Reviewed | Failure Modes | Open Issues |
|------|--------|---------------|---------------|-------------|
| proration.md | Production-Ready | Current | 12 | 0 |
| dunning-retries.md | Production-Ready | Current | 12 | 0 |
| credit-notes.md | Production-Ready | Current | 12 | 0 |
| tax-jurisdiction-rules.md | Production-Ready | Current | 12 | 0 |
| api-and-ui.md | Production-Ready | Current | 12 | 0 |
| security-and-compliance.md | Production-Ready | Current | 12 | 0 |
| operations.md | Production-Ready | Current | 12 | 0 |

### Maintenance Policy

- **Quarterly review**: Each document is reviewed against production incidents from the prior quarter. New failure modes discovered in incidents are backfilled into the catalog.
- **Feature-gated updates**: Any feature that touches billing math, payment processing, tax logic, or subscription state must include a corresponding edge case catalog update in its PR.
- **Incident-driven updates**: Any P0 or P1 billing incident whose root cause is not present in this catalog must result in a catalog update within 5 business days of incident closure.
- **Owner**: The Billing Platform team owns this documentation. The Security and Finance teams are required reviewers for their respective domain files.

---

## Edge Case Categories Overview

### Proration
Mid-cycle plan changes require calculating the credit or charge for the unused and newly-used portion of a billing period. This math is straightforward in isolation but becomes dangerous at timezone boundaries, with concurrent requests, with hybrid pricing models (fixed + metered), and when administrative changes (price updates, plan modifications) occur while a calculation is in flight. The proration document catalogs 12 distinct failure modes across these dimensions.

### Dunning and Retries
When an invoice payment fails, the dunning engine initiates a retry sequence — typically at day 1, 3, 7, and 14 post-failure — before suspending or cancelling the subscription. The dunning state machine interacts with customer-initiated payment method updates, account cancellations, scheduler reliability, and webhook delivery reliability. Double-firing a dunning step charges a customer twice. Missing a dunning step allows an uncollected invoice to age past recovery. Both failure modes exist in production billing systems.

### Credit Notes
A credit note is a formal accounting document that reduces the amount a customer owes. Credit notes interact with invoice finalization state, multi-currency accounts, partial application logic, and expiry windows. Incorrect credit application produces accounting discrepancies that require manual ledger corrections and can trigger audit findings.

### Tax Jurisdiction Rules
SaaS billing tax is a multi-jurisdictional calculation problem. A single invoice line item may be subject to federal, state, county, and city taxes simultaneously. Tax rates change mid-year. Customers move between jurisdictions. Tax-exempt status has expiry dates. Tax calculation services can time out. Each of these scenarios has different handling requirements depending on whether the invoice is in draft or finalized state.

### API and UI
The billing API must guarantee idempotency for all mutation operations. Idempotency failures produce double-charges. Race conditions on concurrent subscription upgrades produce inconsistent entitlement states. Webhook delivery failures leave customer systems in stale states. API versioning mismatches during deployment windows produce silent data corruption. The API and UI document catalogs 12 failure modes across these dimensions with specific reference to HTTP semantics, idempotency key handling, and webhook retry behavior.

### Security and Compliance
PCI DSS scope creep, GDPR deletion conflicts, SOC 2 audit trail gaps, and double-charge prevention are not theoretical concerns — they are regularly encountered in production billing systems. This document catalogs the security and compliance failure modes with specific reference to the regulatory standard implicated, the observable detection signal, and the remediation procedure.

### Operations
Month-end billing runs are the highest-risk operational window for a billing platform. Thousands of invoices are generated, tax is calculated, payments are collected, and notifications are sent — often within a narrow time window. Infrastructure failures during this window (database failover, cache eviction, Kafka partition rebalance, scheduler double-fire) can affect revenue collection for an entire customer cohort. The operations document catalogs 12 failure modes with runbook-level mitigation steps.
