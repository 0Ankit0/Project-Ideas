# Library Management System

> A multi-branch library operations platform delivering unified catalog management, physical and digital circulation, patron self-service, acquisitions workflows, inter-library loans, and analytics across an unlimited number of branch locations.

The system is designed around five core bounded contexts — **Catalog**, **Circulation**, **Identity**, **Acquisitions**, and **Billing** — each independently deployable and integrated through versioned domain events. Branch managers operate within a single pane of glass while system administrators configure global policies that cascade to every branch.

---

## Documentation Structure

```text
Library Management System/
├── README.md                              ← You are here
│
├── requirements/
│   ├── requirements-document.md          ← Functional and non-functional requirements
│   └── user-stories.md                   ← Epics and user stories by role
│
├── analysis/
│   ├── use-case-diagram.md               ← UML use-case diagram (all actors)
│   ├── use-case-descriptions.md          ← Detailed use-case specifications
│   ├── system-context-diagram.md         ← External actors and system boundaries
│   ├── activity-diagram.md               ← Key workflow activity diagrams
│   ├── bpmn-swimlane-diagram.md          ← BPMN 2.0 process flows
│   ├── data-dictionary.md                ← Canonical field definitions
│   ├── business-rules.md                 ← Normative policy rules (BR-01…BR-15+)
│   └── event-catalog.md                  ← Domain event definitions and schemas
│
├── high-level-design/
│   ├── architecture-diagram.md           ← Service topology and integration overview
│   ├── c4-context-container.md           ← C4 Level 1 & Level 2 diagrams
│   ├── domain-model.md                   ← Aggregate, entity, and value-object map
│   ├── data-flow-diagram.md              ← Data flows between services
│   └── system-sequence-diagram.md        ← Cross-service sequence for core flows
│
├── detailed-design/
│   ├── api-design.md                     ← REST API contracts (OpenAPI-aligned)
│   ├── c4-component.md                   ← C4 Level 3 component diagrams
│   ├── class-diagram.md                  ← UML class diagram for core domain
│   ├── component-diagram.md              ← Internal component dependencies
│   ├── erd-database-schema.md            ← Entity-relationship diagram + DDL notes
│   ├── sequence-diagram.md               ← Detailed intra-service sequences
│   └── state-machine-diagram.md          ← Copy, loan, reservation, and fine FSMs
│
├── infrastructure/
│   ├── cloud-architecture.md             ← Cloud provider layout and managed services
│   ├── deployment-diagram.md             ← Kubernetes / container deployment model
│   └── network-infrastructure.md         ← VPC, subnets, DNS, TLS, and firewall rules
│
├── edge-cases/
│   ├── README.md                         ← Edge-case index and triage guide
│   ├── catalog-and-metadata.md           ← ISBN conflicts, merge, and import edge cases
│   ├── circulation-and-overdues.md       ← Overdue, lost, damaged, and recall scenarios
│   ├── reservations-and-waitlists.md     ← Hold expiry, no-show, and priority edge cases
│   ├── acquisitions-and-inventory.md     ← PO conflicts, budget overrun, and receiving gaps
│   ├── digital-lending-and-access.md     ← DRM failure, token expiry, and format edge cases
│   ├── api-and-ui.md                     ← Concurrency, idempotency, and UI error edge cases
│   ├── security-and-compliance.md        ← PII, GDPR, audit trail, and access-control gaps
│   └── operations.md                     ← Failover, migration, and runbook edge cases
│
└── implementation/
    ├── code-guidelines.md                ← Coding standards, patterns, and review checklist
    ├── c4-code-diagram.md                ← C4 Level 4 code-level diagrams
    └── implementation-playbook.md        ← Phased delivery plan, milestones, and DoD criteria
```

---

## Key Features

### Catalog Management
- **ISBN lookup and enrichment** via Open Library and Google Books APIs; automatic metadata population on ISBN scan.
- **Bulk import** from MARC 21 / MARCXML feeds, CSV manifests, and vendor EDI files with conflict resolution.
- Dewey Decimal and LC classification support; custom subject tagging and cross-reference linking.
- Duplicate detection by ISBN, ISSN, and OCLC number with staff-guided merge workflow.

### Physical Circulation
- **Checkout and return** at any branch counter or self-service kiosk; barcode and RFID scan support.
- **Loan period rules** by material type: Books (21 days), DVDs (7 days), Periodicals (3 days), Reference (in-library only).
- **Renewal** up to two times per loan unless a reservation is active on the copy; online, kiosk, and staff-initiated.
- Overdue detection on nightly batch and real-time on return; fine accrual per material-type rate.

### Digital Lending
- **EPUB and PDF delivery** with Adobe DRM and LCP (Readium) token issuance.
- Simultaneous digital loan cap (3 titles per member); 14-day auto-return with zero staff intervention.
- Integration with OverDrive / Libby and Hoopla for consortia digital collections.
- Offline reading window enforced by DRM token TTL; token revocation on early return or account suspension.

### Reservations and Waitlists
- Branch-aware hold queue; member selects preferred pickup branch and is notified when copy is transferred.
- FIFO queue with priority escalation for Scholar-tier members and accessibility-accommodation flags.
- **Hold shelf period**: 7 days from notification; auto-cancellation and next-patron allocation on expiry.
- Waitlist position visibility in the member self-service portal with estimated availability dates.

### Overdue Fines and Penalties
- Fine rates: Books \$0.25/day, DVDs \$1.00/day; capped at 3× item replacement cost.
- 1-day grace period for standard books; no grace for high-demand or recalled items.
- **Borrowing block** triggered when outstanding balance exceeds \$25; block lifted on payment or approved waiver.
- Lost-item declaration and replacement-cost billing after 45 consecutive days overdue.

### Acquisition Workflow
- Purchase request origination by any staff member; approval chain enforced above \$500.
- Vendor catalogue integration; automated PO generation, receipt confirmation, and accession numbering.
- Budget ledger per branch and per fund code; real-time spend vs. allocation dashboard.
- Donation intake, condition assessment, and selective accessioning workflow.

### Member Self-Service Portal
- Catalogue search with faceted filtering (format, branch, availability, subject, language).
- Account dashboard: active loans with due dates, reservation queue positions, fine balance, and borrowing history.
- Online renewal, hold placement and cancellation, fine payment via integrated payment gateway.
- Notification preferences: email, SMS, and push; configurable per event type (due reminder, hold ready, fine notice).

### Inter-Library Loans
- ILL eligibility restricted to Premium and Scholar membership tiers; processing fee applied per request.
- Integration with OCLC WorldShare and Z39.50 for external catalogue search and ILL request routing.
- Tracking of ILL item from request through transit, loan, return, and shipping-back stages.
- SLA monitoring for lender fulfilment; escalation workflow for unresolved requests beyond 14 days.

### Analytics and Reporting
- Branch-level circulation reports: checkouts, returns, renewals, overdues, and fines by period.
- Collection utilisation heatmap: items never checked out, turnover rate, and demand gap analysis.
- Acquisition spend reports by fund, vendor, and subject area with budget vs. actuals.
- Membership analytics: active vs. lapsed members, demographic distribution, and tier conversion rates.
- Exportable to CSV, PDF, and Power BI / Tableau via OData feed.

---

## Primary Roles

| Role | Key Responsibilities |
|---|---|
| **Member** | Search catalogue, place and manage holds, borrow and renew items, pay fines, manage notification preferences, request ILL |
| **Librarian** | Issue and return items at the counter, process kiosk exceptions, collect fines, apply waivers, handle damaged/lost declarations |
| **Cataloging Staff** | Create and edit bibliographic records, classify items, resolve ISBN conflicts, run bulk import jobs, merge duplicate records |
| **Acquisitions Manager** | Manage vendor relationships, approve purchase orders above \$500, monitor budget ledgers, oversee donation intake |
| **Branch Manager** | Monitor branch KPIs, manage transfer queues, run branch-level reports, configure branch pickup windows and hold policies |
| **System Administrator** | Configure global policies, manage membership tiers and fine schedules, integrate external services, maintain audit logs and role assignments |

---

## Getting Started

1. **Understand the scope** — Read [`requirements/requirements-document.md`](requirements/requirements-document.md) for the complete list of functional and non-functional requirements, including performance SLOs and compliance obligations.

2. **Trace the workflows** — Review [`analysis/use-case-descriptions.md`](analysis/use-case-descriptions.md) for step-by-step flows covering all six roles, then study [`analysis/bpmn-swimlane-diagram.md`](analysis/bpmn-swimlane-diagram.md) for the BPMN-level process maps.

3. **Learn the business rules** — Read [`analysis/business-rules.md`](analysis/business-rules.md) for all normative policy rules (BR-01 through BR-15+) governing loans, fines, reservations, digital lending, acquisitions, and ILL.

4. **Understand the architecture** — Study [`high-level-design/architecture-diagram.md`](high-level-design/architecture-diagram.md) and [`high-level-design/c4-context-container.md`](high-level-design/c4-context-container.md) to understand service boundaries, integration points, and the event bus topology.

5. **Plan the data model** — Use [`detailed-design/erd-database-schema.md`](detailed-design/erd-database-schema.md) alongside [`detailed-design/api-design.md`](detailed-design/api-design.md) to map database constraints to API contracts before writing any DDL or controller code.

6. **Review edge cases** — Browse [`edge-cases/`](edge-cases/) before finalising any circulation, reservation, or digital-lending logic; each file identifies known failure modes, expected system behaviour, and recommended mitigations.

7. **Begin delivery** — Follow [`implementation/implementation-playbook.md`](implementation/implementation-playbook.md) for the phased sprint plan, Definition of Done criteria per phase, and integration test harness setup instructions.

---

## Documentation Status

| Section | Status | Notes |
|---|---|---|
| ✅ Requirements | Complete | Functional + NFR with acceptance criteria |
| ✅ Analysis | Complete | Use cases, BPMN, data dictionary, event catalog, business rules |
| ✅ High-Level Design | Complete | Architecture, C4 L1/L2, domain model, DFD, system sequences |
| ✅ Detailed Design | Complete | API contracts, ERD, class diagram, state machines, C4 L3 |
| ✅ Infrastructure | Complete | Cloud architecture, Kubernetes deployment, network topology |
| ✅ Edge Cases | Complete | 8 domain-specific edge-case files with mitigations |
| ✅ Implementation | Complete | Code guidelines, C4 L4, phased playbook |
