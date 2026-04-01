# Edge Cases — Library Management System

This directory documents the failure modes, boundary conditions, and exception paths that must be handled deliberately across every domain of the Library Management System. Each file maps directly to a bounded context in the Spring Boot microservices architecture, covering the full stack: PostgreSQL/RDS for persistent state, Elasticsearch for catalog search, Redis for session and cache, Kafka for event streaming, AWS S3 for digital assets, OverDrive DRM for e-content access control, and Kubernetes for runtime orchestration.

Each edge case entry follows a consistent four-column table format:

| Failure Mode | Impact | Detection | Mitigation / Recovery |

- **Failure Mode** — the specific condition, race, or constraint violation that can occur.
- **Impact** — which patron, staff, or system function is degraded and to what degree.
- **Detection** — the observable signal: metric alert, dead-letter queue, Kafka consumer lag, HTTP error code, or audit log anomaly.
- **Mitigation / Recovery** — the corrective action the system or operator takes, including idempotency guards, compensating transactions, and staff override paths.

Business rules referenced throughout use the prefix `BR-` and are summarised in the section below.

---

## Business Rules Reference

| ID    | Rule Summary |
|-------|-------------|
| BR-01 | Concurrent loan cap by membership tier: Basic = 3, Standard = 7, Premium = 15, Scholar = unlimited. |
| BR-02 | Loan period by material type: Book = 21 days, DVD = 7 days, Periodical = 3 days, Reference = in-library use only. |
| BR-03 | Maximum 2 renewals per loan; renewal blocked when an active reservation exists on the same title. |
| BR-04 | Fine accrual: Book = $0.25/day capped at 3× replacement cost; DVD = $1.00/day; no cap override without manager approval. |
| BR-05 | Hold shelf expiry = 7 calendar days from arrival notification; uncollected items re-enter the waitlist. |
| BR-06 | Maximum 3 simultaneous digital loans per patron account. |
| BR-07 | Purchase order approval thresholds: $0–$500 auto-approve, $501–$2,000 Acquisitions Manager, $2,001+ Library Director. |
| BR-08 | Borrowing blocked when patron's outstanding balance exceeds $25. |
| BR-09 | Overdue recall triggered when a reservation exists; due date reset to today + 3 days. |
| BR-10 | Digital loan window = 14 days with auto-return; DRM failure triggers retry every 15 minutes for up to 24 hours before the loan is voided. |
| BR-11 | Interlibrary loan (ILL) available to Premium and Scholar tiers only; $3 processing fee per request. |
| BR-12 | Lost item declaration triggers replacement cost billing and removes copy from active inventory. |
| BR-13 | Grace period applies per material type before fine accrual begins. |
| BR-14 | Membership expiry grace window allows borrowing continuation for a defined period before account suspension. |
| BR-15 | ISBN must be unique per edition; duplicate detection triggers a merge workflow for bibliographic records. |

---

## Documentation Structure

| File | Domain | Description |
|------|--------|-------------|
| `catalog-and-metadata.md` | Catalog | Covers ISBN uniqueness violations, duplicate bibliographic record merges, Elasticsearch index drift, and MARC/Dublin Core import failures that corrupt copy counts or break search relevance (BR-15). |
| `circulation-and-overdues.md` | Circulation | Documents concurrent checkout races, loan-period miscalculations by material type, fine accrual cap edge cases, recall triggers, renewal blocks, and lost-item declaration flows (BR-01 through BR-04, BR-08, BR-09, BR-12, BR-13). |
| `reservations-and-waitlists.md` | Reservations | Captures hold queue ordering anomalies, eligibility re-checks at copy allocation, hold shelf expiry and no-show handling, and cross-branch transfer timing conflicts (BR-05, BR-09). |
| `acquisitions-and-inventory.md` | Acquisitions | Details PO approval threshold bypasses, duplicate order prevention, received-quantity mismatches, copy activation races, and budget overrun guards (BR-07). |
| `digital-lending-and-access.md` | Digital Lending | Addresses OverDrive DRM checkout failures, concurrent digital loan cap enforcement, auto-return idempotency, S3 asset availability gaps, and ILL eligibility enforcement (BR-06, BR-10, BR-11). |
| `api-and-ui.md` | API / UI | Covers idempotency key collisions on checkout endpoints, optimistic-lock conflicts surfaced to the UI, stale Redis cache serving outdated availability, and partial-update race conditions on patron profiles. |
| `security-and-compliance.md` | Security | Documents unauthorised cross-patron data access, privilege escalation via role assignment gaps, GDPR deletion conflicts with active loans, audit log tampering, and session fixation via Redis key reuse. |
| `operations.md` | Operations | Handles Kubernetes pod eviction mid-transaction, Kafka consumer lag causing stale event processing, PostgreSQL failover during loan writes, nightly batch job overlap with live traffic, and cross-branch sync failures. |

---

## Key Features

### Eight Failure Domains with Full Traceability

Every edge case maps to a bounded context in the microservices architecture, a specific business rule, and at least one observable signal. This traceability lets engineers write targeted regression tests and operators configure precise alerting thresholds without guesswork.

### Consistent Table Format Across All Domains

The four-column table (Failure Mode / Impact / Detection / Mitigation / Recovery) gives developers, QA engineers, and on-call staff a uniform mental model. Scanning any file in this directory yields actionable information without needing domain-specific context.

### Business Rule Anchoring

Each edge case references one or more `BR-` codes, connecting failure scenarios directly to the product requirements that govern them. This prevents silent policy drift when rules change — if BR-04 changes the DVD fine rate, engineers know exactly which tests and Kafka consumers to update.

### Technology-Specific Mitigations

Mitigations are written for the actual stack. Redis cache invalidation patterns, Kafka dead-letter-queue retry semantics, PostgreSQL advisory locks for concurrent checkout, Elasticsearch index refresh delays, OverDrive DRM retry windows, and Kubernetes liveness-probe implications are all addressed with concrete guidance rather than generic advice.

### Staff Override and Audit Coverage

Wherever a monetary adjustment, manual override, or privileged operation is possible, the edge case entry includes the audit log event and the approval flow required, supporting both compliance review and post-incident analysis.

### Test and Observability Hooks

Each entry identifies the detection mechanism — whether that is a Prometheus counter, a Kafka dead-letter-queue depth, a PostgreSQL constraint violation, or an HTTP 409 response — so that test authors and SREs can instrument coverage without re-deriving it from business logic.

---

## Getting Started

### During Feature Development

1. **Identify the domain** your feature touches (Catalog, Circulation, Reservations, Acquisitions, Digital Lending, API/UI, Security, Operations) and open the corresponding file.
2. **Locate relevant business rules** using the BR-reference index above. Cross-check your implementation against every `BR-` code listed for your domain.
3. **Review the Failure Mode column** for scenarios your feature could trigger. Confirm your service handles each one explicitly — either by preventing it, detecting it, or recovering from it.
4. **Add new entries** to the relevant file whenever you discover a failure mode not yet documented. Follow the four-column table format exactly; do not leave any cell blank.

### During Code Review

- Verify that any new Kafka producer includes an idempotency key and that the corresponding consumer entry appears in `operations.md` or the relevant domain file.
- Check that every database write that touches loan, copy, or reservation state is covered by an edge case entry in `circulation-and-overdues.md` or `reservations-and-waitlists.md`.
- Confirm that monetary operations (fines, fees, replacement billing) reference the correct BR code and include an audit log assertion.

### During QA and Integration Testing

- Use this directory as a test catalogue. Each row in every table is a test case candidate; the Detection column describes the assertion and the Mitigation/Recovery column describes the expected system behaviour after the fault is injected.
- For digital lending tests, simulate OverDrive DRM timeouts and verify the 15-minute retry loop and 24-hour void behaviour defined in BR-10.
- For concurrent checkout tests, run parallel requests against the same copy and assert that exactly one loan is created and the other receives an HTTP 409 with a `COPY_UNAVAILABLE` error code.

### During On-Call and Incident Response

- Start with the Detection column for the domain closest to the alert. Each entry identifies the observable signal and the corrective action.
- For Kafka lag incidents, consult `operations.md` for consumer group recovery procedures and dead-letter-queue reprocessing steps.
- For data integrity anomalies in catalog records, consult `catalog-and-metadata.md` for the duplicate-merge and Elasticsearch re-index recovery path.

---

## Documentation Status

All eight edge case files are complete and cover their respective domains to production-grade depth.

| File | Status | Business Rules Covered |
|------|--------|------------------------|
| `catalog-and-metadata.md` | Complete | BR-15 |
| `circulation-and-overdues.md` | Complete | BR-01, BR-02, BR-03, BR-04, BR-08, BR-09, BR-12, BR-13 |
| `reservations-and-waitlists.md` | Complete | BR-05, BR-09 |
| `acquisitions-and-inventory.md` | Complete | BR-07 |
| `digital-lending-and-access.md` | Complete | BR-06, BR-10, BR-11 |
| `api-and-ui.md` | Complete | BR-01, BR-03, BR-06 |
| `security-and-compliance.md` | Complete | BR-08, BR-14 |
| `operations.md` | Complete | BR-01 through BR-15 (cross-cutting) |

New edge cases discovered during development or production incidents must be added to the relevant file before the associated fix or feature is merged. An entry with an empty Mitigation/Recovery cell is not acceptable; if recovery is still under investigation, document the interim manual procedure and open a tracking issue linked from the table row.
