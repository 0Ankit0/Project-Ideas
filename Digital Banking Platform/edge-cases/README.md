---
document-id: DBP-EDGE-027
version: 1.0.0
status: Approved
owner: Platform Engineering — Reliability Chapter
created: 2025-01-15
last-updated: 2025-01-15
---

# Edge Cases — Digital Banking Platform

## Purpose

Edge case documentation occupies a unique role in banking systems. Unlike
conventional software projects where unhandled edge cases degrade user
experience, in banking they produce regulatory violations, financial loss,
customer harm, and reputational damage that can take years to recover from.

This directory captures every material edge case identified for the Digital
Banking Platform, organised by functional domain. Each document serves four
distinct audiences with different but overlapping needs.

**Regulatory and compliance teams** require evidence that the platform has
identified, analysed, and controlled for failure modes intersecting with legal
obligations — PSD2, BSA/AML, OFAC sanctions screening, GDPR, PCI-DSS, and KYC
regulations. These documents form part of the evidence pack submitted to
regulators during licensing reviews, supervision visits, and incident-reporting
processes.

**Site Reliability Engineers** require precise failure mode descriptions,
detection signals, and resolution procedures to construct actionable runbooks.
Edge case documents translate business scenarios into observable system
behaviours: which metrics spike, which log patterns appear, which automated
remediations should execute, and which manual steps are required when automation
is insufficient.

**Software engineers** use edge case analysis during design and implementation
to ensure that failure paths are handled explicitly rather than by accident.
Each edge case document provides test scenario tables that translate directly
into unit, integration, and contract test specifications.

**Audit and assurance teams** require a traceable chain from identified risk to
implemented control. These documents, versioned alongside source code in the
same repository, provide that chain and demonstrate that risk identification is
a continuous engineering discipline rather than a point-in-time compliance
exercise.

---

## Edge Case Categories

The following table lists all edge case documents in this directory, their
risk classification, and their regulatory relevance. Documents marked CRITICAL
represent scenarios where a failure could result in direct regulatory breach,
financial crime facilitation, or customer data exposure.

| Category | File | Description | Risk Level | Regulatory Impact |
|---|---|---|---|---|
| Account Lifecycle | `account-lifecycle.md` | Closure during active transactions, dormancy reactivation, balance discrepancy on merge, concurrent double-spend, overdraft on scheduled payment | HIGH | GDPR data retention, FSA account dormancy rules, COBS |
| Transaction Processing | `transaction-processing.md` | Duplicate detection, partial SWIFT failures, network timeout on payment rail, FX rate expiry, reversal race conditions | HIGH | PSD2 payment finality, BSA transaction integrity, SWIFT compliance |
| Fraud and AML Compliance | `fraud-and-aml-compliance.md` | False positive blocks, AML alert storms, sanctions list update failure, ML model drift, SIM-swap fraud | CRITICAL | BSA/AML, OFAC sanctions screening, FCA financial crime rules |
| KYC and Onboarding | `kyc-and-customer-onboarding.md` | KYC provider outage, OCR failure, liveness spoofing, PEP false positive, expired document on re-KYC | HIGH | KYC/CDD regulations, FATF recommendations R.10–R.12, MLR 2017 |
| API and UI | `api-and-ui.md` | Rate limit breaches, session expiry mid-transaction, Open Banking PSD2 failures, mobile connection loss, WebSocket drops | MEDIUM | PSD2 Strong Customer Authentication, GDPR session management |
| Security and Compliance | `security-and-compliance.md` | PCI-DSS scope creep, GDPR data subject requests, SOX audit controls, MFA bypass, data breach response | CRITICAL | PCI-DSS SAQ D, GDPR Articles 17/15/20, SOX Section 404 |
| Operations | `operations.md` | DB failover during peak traffic, Kafka consumer lag, core banking sync delay, broker failure, memory pressure, certificate expiry | HIGH | PRA SS1/21 operational resilience, EBA ICT risk guidelines |

---

## Severity Classification

The following classification governs all edge cases in this directory. Severity
determines response time obligations, escalation paths, and regulatory
notification requirements. Classifications are reviewed during each quarterly
risk assessment.

| Severity | Description | Customer Impact | Response Time | Escalation Path | Example Scenarios |
|---|---|---|---|---|---|
| CRITICAL | Financial loss, regulatory breach, or data exposure in progress | Severe — direct harm or crime in progress | Immediate (< 15 min) | CTO + CISO + Legal + Compliance on-call | Active OFAC match unblocked, PAN data in logs, fraud wave undetected |
| HIGH | Service degradation affecting material transaction flows | Significant — customers cannot transact or access funds | < 1 hour | Engineering Director + Compliance Lead | DB failover during salary run, AML alert storm, SWIFT partial failure |
| MEDIUM | Partial degradation or recoverable error affecting subset of users | Moderate — some customers affected; workaround available | < 4 hours | Service Owner + On-Call Lead | KYC provider outage, rate limit breach by TPP, WebSocket disconnects |
| LOW | Minor degradation or informational edge case | Minimal — isolated incident; no financial impact | < 24 hours | Team Lead | Notification preference gap, standing order UI delay, CSV export delay |

---

## How to Use These Documents

### Incident Response

When an incident is declared, the on-call engineer identifies the relevant
category (Account Lifecycle, Transaction Processing, etc.) and navigates to the
corresponding edge case document. Each document contains a **Detection** section
describing the observable signals — metric names, log patterns, alert titles —
and a **Handling** section describing the ordered resolution steps. The Runbook
Index at the end of each document provides references to the operational
runbooks in PagerDuty and Confluence.

For CRITICAL severity incidents, the on-call engineer must simultaneously
notify the Compliance Lead (for potential regulatory impact) and the CISO (for
potential data exposure) within 15 minutes of incident declaration, regardless
of whether the root cause has been identified.

### Test Case Derivation

Each edge case document contains one or more **Test Scenarios** tables that
list discrete test inputs, expected system outputs, and the system state at the
point of observation. Engineers translate these tables into:

- **Unit tests** covering isolated domain logic (JUnit 5 + AssertJ)
- **Integration tests** covering service behaviour under failure conditions
  (Testcontainers + WireMock for stubbed dependencies)
- **Contract tests** verifying API behaviour across service boundaries (Pact)
- **Chaos engineering scenarios** validated in the staging environment
  (AWS Fault Injection Simulator)

Test cases derived from this directory carry the tag `[edge-case]` in their
test class annotations, making them filterable in the CI pipeline report and
traceable to this documentation.

### Runbook Creation

SREs map each HIGH and CRITICAL edge case to a named runbook stored in
PagerDuty. The runbook must reference the edge case document (by document ID)
as its source of truth for detection signals and resolution steps. When an
incident post-mortem reveals a new failure mode, the corresponding edge case
document is updated first, and the runbook is updated to reference the new
version. This ensures the two artefacts remain synchronised.

### Compliance Evidence Mapping

The compliance team maintains a mapping from each regulatory requirement to the
edge case documents that evidence the corresponding technical control. For
example, the OFAC screening requirement maps to `fraud-and-aml-compliance.md`
(Sanctions List Update Failure section), and the PSD2 SCA requirement maps to
`api-and-ui.md` and `security-and-compliance.md`. This mapping is submitted as
part of the annual compliance attestation package and reviewed during external
audits.

---

## Cross-Cutting Concerns

The following concerns apply universally across all edge case categories. Each
domain-specific document assumes these foundations are in place.

### Idempotency as a Universal Defence

Every mutating API endpoint requires an `X-Idempotency-Key` header (UUID v4
format). The key is stored with a UNIQUE constraint and a 24-hour TTL. When a
duplicate request arrives with a key matching a previously completed operation,
the server returns the original response without re-executing the operation.
This single mechanism eliminates an entire class of duplicate-submission edge
cases across payment initiation, account creation, card issuance, and loan
disbursement.

| Layer | Mechanism | Storage | TTL |
|---|---|---|---|
| API Gateway | Key extraction; early 200 return for in-flight duplicates | Redis (clustered) | 30 minutes |
| Service application layer | Idempotency check before command handler execution | PostgreSQL UNIQUE index | 24 hours |
| Payment rail submission | Rail-level reference number deduplication | Payment rail operator | Per-rail rules |

### Distributed Tracing for Edge Case Debugging

All services emit OpenTelemetry spans with a shared `traceId` propagated
through HTTP headers (`traceparent`) and Kafka message headers
(`X-B3-TraceId`). When an edge case manifests in production, the `traceId`
from the customer request allows the complete cross-service execution path to
be reconstructed in Jaeger or AWS X-Ray within seconds, regardless of which
service introduced the failure. All edge case detection queries in CloudWatch
Logs Insights include `traceId` in the projected fields for this reason.

### Circuit Breakers

All outbound service-to-service and external gateway calls are wrapped in
Resilience4j circuit breakers. Standard configuration across the platform is:

| Parameter | Value | Rationale |
|---|---|---|
| Failure rate threshold | 50% | Opens circuit if half of recent calls fail |
| Slow call rate threshold | 80% calls > 2 s | Guards against latency-induced cascading failures |
| Wait duration in OPEN state | 30 seconds | Short enough to auto-recover quickly |
| Permitted calls in HALF-OPEN | 3 | Probes recovery conservatively |
| Minimum calls in sliding window | 10 | Prevents premature opening on low traffic |

Circuit breaker state transitions are published as Micrometer metrics
(`resilience4j.circuitbreaker.state`) and trigger PagerDuty HIGH-severity
alerts when any CRITICAL-path circuit enters the OPEN state.

### Compensating Transactions

For every multi-step operation that modifies state across service boundaries —
such as fund reservation followed by payment rail submission — a compensating
transaction is defined in the saga orchestrator (AWS Step Functions). Compensating
transactions are triggered automatically when a saga step fails beyond its retry
limit. Each edge case document covering cross-service state changes includes a
**Compensating Actions** section specifying the exact reversal sequence and the
conditions under which it is invoked.

### Observability Requirements

An edge case is not considered adequately controlled until it is detectable
through the observability stack. The minimum detection requirements are:

| Signal Type | Tooling | Requirement |
|---|---|---|
| Metrics alert | Prometheus + Alertmanager | Alert fires within 60 seconds of condition onset |
| Structured log query | CloudWatch Logs Insights | Affected records identifiable within 5 minutes |
| Distributed trace | Jaeger / AWS X-Ray | Full trace reconstructable within 30 seconds of request |
| Dashboard panel | Grafana | Anomaly visible without manual ad-hoc query |
| Incident ticket | PagerDuty | On-call engineer notified within 5 minutes for HIGH/CRITICAL |

Any edge case for which these requirements cannot be met must be documented as
an open risk item in the platform risk register, reviewed at each quarterly
risk assessment, and assigned a target remediation sprint.
