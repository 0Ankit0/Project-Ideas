# Legal Case Management System

The Legal Case Management System (LCMS) is an enterprise-grade platform purpose-built for mid-to-large law firms managing complex legal portfolios across multiple practice areas. The system consolidates every operational function of a modern law firm — from initial client intake and conflict screening through matter lifecycle management, court-integrated document production, LEDES-compliant billing, and regulatory compliance — into a single, auditable platform. Designed to serve litigation, corporate transactional, family law, and intellectual property practices simultaneously, the LCMS eliminates the fragmented tooling that plagues most firms and replaces it with a unified data model that enforces firm-wide consistency while accommodating the distinct workflows of each practice group. The platform integrates natively with PACER for federal court e-filing and docket retrieval, DocuSign for legally binding electronic signatures, LEDES and UTBMS billing standards for corporate client invoice compliance, and IOLTA trust accounting rules enforced at the transaction level.

---

## Key Features

### Case & Matter Management

The LCMS manages every stage of a legal matter from initial intake through resolution, appeal, and archival. Each matter is assigned a unique, firm-formatted matter number and linked to a client, responsible attorney, billing partner, and originating attorney. The intake workflow triggers an automated conflict-of-interest check against the firm's adverse party database before a matter is formally opened. Matter types — litigation (state and federal), corporate transactional, family law, intellectual property prosecution and enforcement, and regulatory — carry practice-area-specific metadata fields and default task checklists. Matter budgets are configured at open with phase-level breakdowns, and real-time spend is calculated from approved time entries and disbursements. Linked matter hierarchies allow corporate clients with subsidiary structures to have a parent matter governing multiple child matters with unified billing visibility.

**Key capabilities:**
- Unique matter numbering with configurable firm formats (e.g., `SMITH-2024-LIT-001`)
- Conflict-of-interest check engine with configurable relationship depth and adverse party graph
- Practice area classification with custom metadata schemas per matter type
- Matter lifecycle states: Intake, Active, On Hold, Closing Review, Closed, Archived
- Phase-level budgeting with spend alerts at configurable thresholds (50%, 75%, 90%, 100%)
- Linked matter hierarchies for corporate family-of-entities clients
- Matter team roles: Responsible Attorney, Billing Partner, Originating Attorney, Associate, Paralegal, Legal Assistant

### Client Management

Client records serve as the master relationship anchor in the LCMS. Onboarding a new client triggers a structured workflow that includes identity verification, KYC documentation collection, engagement letter generation, fee agreement configuration, and trust account setup where applicable. The client portal provides secure, authenticated access for clients to review matter status, download documents, review and pay invoices, and communicate with their matter team through a logged messaging channel. Billing agreements support all common fee arrangements: hourly (with rate tables by attorney and seniority), flat fee by matter phase, contingency with configurable percentage tiers, retainer with monthly replenishment rules, and hybrid combinations.

**Key capabilities:**
- Structured digital onboarding workflow with document checklist and approval gates
- Engagement letter template library with practice-area-specific versions
- E-signature collection via DocuSign with audit trail retained in the matter file
- Fee arrangement engine: hourly, flat fee, contingency, retainer, hybrid
- Client portal with role-based access (view-only vs. full collaboration)
- GDPR and CCPA consent records and preference management
- Client relationship history, communication log, and referral source tracking

### Document Management

Every document associated with a matter is stored in the LCMS document repository with full version control, check-in/check-out locking, and an immutable audit trail. The system supports Bates numbering for litigation document production, generating sequential Bates stamps across single or multi-volume production sets with configurable prefix formats. Attorneys may designate documents or document sets as privileged, generating a structured privilege log with required fields (document date, author, recipient, privilege basis, description) suitable for court submission. The DocuSign integration allows documents to be sent for signature directly from a matter record, with the executed version automatically filed back into the document repository. Federal court filings are submitted via the PACER/CM-ECF integration, and filed documents and docket entries are automatically retrieved and stored against the matter.

**Key capabilities:**
- Version-controlled document repository with delta history and rollback
- Bates numbering engine with configurable prefix, suffix, and sequential numbering across production sets
- Privilege log wizard with required field validation and export to Excel and PDF
- DocuSign envelope creation, signer sequencing, and executed-document auto-filing
- PACER/CM-ECF integration for e-filing and docket pull
- Document templates for pleadings, motions, correspondence, contracts, and court forms
- OCR processing and full-text search across all repository documents
- Legal hold management — places a retention lock on documents responsive to a hold notice

### Time & Billing

Time entry is the revenue engine of the firm, and the LCMS enforces completeness and accuracy through structured entry forms, UTBMS task and activity code validation, and attorney-specific billing rate application. Every time entry is tagged with a matter, phase, UTBMS task code (L100–L600 for litigation, C100–C400 for corporate), and UTBMS activity code, enabling granular billing narrative generation and client reporting. Invoice generation produces LEDES 1998B and LEDES 2000 formatted files for corporate clients with e-billing portals, while standard invoices are generated in PDF format for direct delivery. Trust accounting is managed under IOLTA rules: client funds are held in segregated ledger accounts, disbursements require two-party approval above configurable thresholds, and three-way reconciliation (firm ledger, client ledger, bank statement) is enforced at month-end.

**Key capabilities:**
- Time entry with UTBMS task and activity codes, narrative, and matter/phase assignment
- Non-billable time capture for administrative, pro bono, and firm development activities
- LEDES 1998B and LEDES 2000 invoice generation with line-item UTBMS codes
- Multi-currency billing with exchange rate management for international matters
- IOLTA trust accounting with segregated client ledgers and three-way reconciliation
- Automated invoice approval workflows with partner sign-off and client delivery
- Accounts receivable aging reports with collections workflow integration
- Billing rate tables: by attorney, by matter type, by client agreement, with effective date versioning

### Court Calendar & Deadlines

Missing a court deadline is a malpractice event. The LCMS treats court calendar management as a safety-critical function, implementing multiple layers of deadline calculation, verification, and notification. The statute of limitations calculator applies jurisdiction-specific rules and tolling provisions, producing a documented calculation record that is filed in the matter. Court deadlines are computed from trigger events (complaint filing date, service of process date, order date) using the applicable procedural rules (FRCP, state civil procedure, local rules), with calendar-day vs. business-day logic and holiday exclusion lists maintained per jurisdiction. PACER docket synchronization for federal matters pulls new docket entries automatically, parses hearing dates and order deadlines, and presents them for attorney confirmation before adding to the master calendar.

**Key capabilities:**
- Statute of limitations calculator with jurisdiction rules and tolling provisions
- Deadline engine computing FRCP, state civil procedure, and local-rule deadlines from trigger events
- PACER docket sync with parsed hearing and deadline entries pending attorney confirmation
- Multi-attorney calendar with conflict detection for hearings and depositions
- Critical deadline notifications via email, SMS, and in-app alerts with configurable lead times (30, 14, 7, 3, 1 days)
- Hearing scheduling with court location, judge assignment, and courtroom details
- Docket management with manual entry fallback for state court matters

### Task Management

The LCMS task engine drives day-to-day matter execution. Precedent-based task checklists — built from the firm's institutional knowledge of common matter types — are instantiated at matter open with automatically computed due dates relative to key matter dates (filing date, trial date, closing date). Tasks support dependency chains (task B cannot start until task A is complete), delegation with completion confirmation requirements, and escalation rules that notify supervising attorneys when tasks become overdue. Matter teams collaborate through a shared activity feed on each matter record, with @mention notifications and document attachment capabilities. The workload management dashboard gives supervising attorneys and firm administrators a real-time view of open tasks, upcoming deadlines, and utilization by timekeeper.

**Key capabilities:**
- Precedent task checklist library organized by matter type and jurisdiction
- Dependency-aware task scheduling with automatic due date recalculation on matter date changes
- Task delegation with role-based assignment, completion confirmation, and escalation chains
- Matter-level activity feed with @mention notifications and document linking
- Integration with Microsoft 365 (Outlook + Teams) and Google Workspace (Gmail + Calendar)
- Workload dashboard with task counts, overdue items, and upcoming deadline views per timekeeper
- Recurring task support for compliance-driven activities (bar registration renewals, CLE tracking)

### Compliance & Security

Law firms operate under strict professional responsibility rules, data privacy regulations, and bar ethics requirements. The LCMS embeds compliance controls into core workflows rather than treating them as bolt-on features. Every document is classified for privilege status. Conflicts screening runs at matter intake and can be re-run at any time against the latest conflict database. The bar rules compliance engine is configurable per jurisdiction and flags potential rule violations (fee-splitting, communication with represented parties, unauthorized practice). GDPR and CCPA data subject requests are managed through an automated workflow that identifies all personal data stored for the requestor, produces a report, and executes deletion or restriction orders within regulatory time limits. All user actions, data access events, and configuration changes are written to an immutable audit log.

**Key capabilities:**
- Attorney-client privilege classification with inheritance rules for document sets
- Conflict-of-interest screening at intake with configurable adverse party relationship depth
- Configurable bar rules compliance engine by jurisdiction (ABA Model Rules, state variations)
- GDPR Article 15/17/20 and CCPA Section 1798.100 automated request handling
- RBAC with matter-level security overlays (attorneys can be excluded from specific matters)
- Immutable audit log with tamper-evident hash chaining, exportable for regulatory review
- Data retention schedules with automated archival and legal hold override capability
- Two-factor authentication, SSO via SAML 2.0 / OIDC, and session management controls

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


| Folder | Contents | Purpose |
|--------|----------|---------|
| `requirements/` | `requirements-document.md`, `user-stories.md` | Full functional and non-functional specifications; role-based user stories with acceptance criteria |
| `analysis/` | Use case diagrams, use case descriptions, system context diagram, activity diagrams, BPMN swimlane diagrams, data dictionary, business rules, event catalog | Analytical artifacts describing system behavior, data structures, and business logic |
| `high-level-design/` | System sequence diagrams, domain model, data flow diagrams, architecture diagram, C4 context and container diagrams | High-level architectural blueprints and inter-system communication patterns |
| `detailed-design/` | Class diagrams, detailed sequence diagrams, state machine diagrams, ERD and database schema, component diagrams, API design specification, C4 component diagrams | Engineering-level design artifacts for implementation |
| `infrastructure/` | Deployment diagram, network infrastructure topology, cloud architecture design | Infrastructure layout, cloud services, networking, and deployment topology |
| `implementation/` | Code guidelines, C4 code-level diagrams, implementation playbook | Developer guidelines, coding standards, and step-by-step implementation procedures |
| `edge-cases/` | Edge case analysis by domain (case lifecycle, documents, billing, court deadlines, API/UI, security/compliance, operations) | Catalogued edge cases, boundary conditions, and failure mode handling per domain |

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Navigating the Documentation

This documentation repository follows the standard software development lifecycle from requirements capture through implementation guidance. New readers should work through the layers sequentially; experienced contributors may navigate directly to the relevant folder.

**Recommended reading order:**

1. **README** (this document) — system overview, feature summary, and documentation map.
2. **`requirements/requirements-document.md`** — the full Software Requirements Specification (SRS) with functional requirements (FR-001–FR-040+) and non-functional requirements organized by quality attribute.
3. **`requirements/user-stories.md`** — role-based user stories across all seven epics, each with acceptance criteria, story points, and priority classification.
4. **`analysis/`** — begin with `system-context-diagram.md` to understand system boundaries, then `use-case-diagram.md` and `use-case-descriptions.md` for behavioral scope. Review `data-dictionary.md` and `business-rules.md` for data semantics and constraint logic. Use `event-catalog.md` to understand domain events driving asynchronous workflows.
5. **`high-level-design/`** — start with `architecture-diagram.md` for the macro view, then `domain-model.md` for the core entity relationships, `c4-context-container.md` for the C4 system decomposition, and `data-flow-diagram.md` for data movement across boundaries.
6. **`detailed-design/`** — engineering-level artifacts. Work through `erd-database-schema.md` for persistence design, `api-design.md` for service contracts, `class-diagram.md` and `component-diagram.md` for structural decomposition, and `state-machine-diagram.md` for entity lifecycle logic.
7. **`infrastructure/`** — `cloud-architecture.md` for the overall cloud topology, `deployment-diagram.md` for service placement, and `network-infrastructure.md` for network security and connectivity.
8. **`implementation/`** — `code-guidelines.md` before writing any code, `implementation-playbook.md` for sprint-by-sprint delivery guidance, and `c4-code-diagram.md` for code-level structural context.
9. **`edge-cases/`** — consult the relevant domain file when designing for resilience or writing test cases. `edge-cases/README.md` provides a cross-domain summary and severity classification.

### Intended Audiences

| Audience | Primary Documents |
|----------|------------------|
| Product Managers | `requirements/requirements-document.md`, `requirements/user-stories.md`, `analysis/business-rules.md` |
| Business Analysts | `analysis/` folder, `requirements/requirements-document.md` |
| Solution Architects | `high-level-design/architecture-diagram.md`, `high-level-design/c4-context-container.md`, `infrastructure/cloud-architecture.md` |
| Backend Engineers | `detailed-design/erd-database-schema.md`, `detailed-design/api-design.md`, `detailed-design/class-diagram.md`, `implementation/code-guidelines.md` |
| Frontend Engineers | `detailed-design/component-diagram.md`, `detailed-design/api-design.md`, `implementation/code-guidelines.md` |
| QA Engineers | `requirements/user-stories.md`, `edge-cases/` folder, `analysis/business-rules.md` |
| DevOps / SRE | `infrastructure/` folder, `implementation/implementation-playbook.md`, `detailed-design/deployment-diagram.md` |
| Legal Operations | `requirements/requirements-document.md`, `analysis/business-rules.md`, `analysis/data-dictionary.md` |
| Security / Compliance | `edge-cases/security-and-compliance.md`, `analysis/business-rules.md`, `requirements/requirements-document.md` |

---

## Technology Context

The LCMS is designed as a cloud-native, multi-tenant SaaS application deployable on AWS or Azure. The backend is built on a microservices architecture with domain-driven service decomposition. The following technology areas are addressed in the implementation and infrastructure documentation:

| Layer | Technology Choices Addressed |
|-------|------------------------------|
| Frontend | React 18+ SPA with TypeScript; responsive design for desktop-first legal workflows |
| Backend Services | Node.js / TypeScript microservices with REST and GraphQL APIs |
| Data Persistence | PostgreSQL (relational data), Redis (caching and session state), Elasticsearch (full-text search) |
| Document Storage | AWS S3 / Azure Blob Storage with server-side encryption |
| Authentication | Auth0 / AWS Cognito with SAML 2.0 and OIDC for enterprise SSO |
| Messaging | Apache Kafka for domain event streaming; SendGrid / AWS SES for email |
| External Integrations | PACER/CM-ECF, DocuSign eSignature API, LEDES billing interchange, QuickBooks / NetSuite accounting |
| Monitoring | Datadog APM and log aggregation; PagerDuty for incident alerting |
| CI/CD | GitHub Actions pipelines with environment-gated deployments |

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Path | Status |
|----------|------|--------|
| Requirements Document | `requirements/requirements-document.md` | Complete |
| User Stories | `requirements/user-stories.md` | Complete |
| Use Case Diagram | `analysis/use-case-diagram.md` | In Progress |
| Use Case Descriptions | `analysis/use-case-descriptions.md` | In Progress |
| System Context Diagram | `analysis/system-context-diagram.md` | In Progress |
| Activity Diagram | `analysis/activity-diagram.md` | In Progress |
| BPMN Swimlane Diagram | `analysis/bpmn-swimlane-diagram.md` | In Progress |
| Data Dictionary | `analysis/data-dictionary.md` | In Progress |
| Business Rules | `analysis/business-rules.md` | In Progress |
| Event Catalog | `analysis/event-catalog.md` | In Progress |
| System Sequence Diagram | `high-level-design/system-sequence-diagram.md` | In Progress |
| Domain Model | `high-level-design/domain-model.md` | In Progress |
| Data Flow Diagram | `high-level-design/data-flow-diagram.md` | In Progress |
| Architecture Diagram | `high-level-design/architecture-diagram.md` | In Progress |
| C4 Context & Container | `high-level-design/c4-context-container.md` | In Progress |
| Class Diagram | `detailed-design/class-diagram.md` | In Progress |
| Sequence Diagram | `detailed-design/sequence-diagram.md` | In Progress |
| State Machine Diagram | `detailed-design/state-machine-diagram.md` | In Progress |
| ERD / Database Schema | `detailed-design/erd-database-schema.md` | In Progress |
| Component Diagram | `detailed-design/component-diagram.md` | In Progress |
| API Design | `detailed-design/api-design.md` | In Progress |
| C4 Component Diagram | `detailed-design/c4-component.md` | In Progress |
| Deployment Diagram | `infrastructure/deployment-diagram.md` | In Progress |
| Network Infrastructure | `infrastructure/network-infrastructure.md` | In Progress |
| Cloud Architecture | `infrastructure/cloud-architecture.md` | In Progress |
| Code Guidelines | `implementation/code-guidelines.md` | In Progress |
| C4 Code Diagram | `implementation/c4-code-diagram.md` | In Progress |
| Implementation Playbook | `implementation/implementation-playbook.md` | In Progress |
| Edge Cases Overview | `edge-cases/README.md` | In Progress |
| Case Lifecycle Edge Cases | `edge-cases/case-lifecycle.md` | In Progress |
| Document Management Edge Cases | `edge-cases/document-management.md` | In Progress |
| Billing & Time Tracking Edge Cases | `edge-cases/billing-and-time-tracking.md` | In Progress |
| Court Deadlines Edge Cases | `edge-cases/court-deadlines.md` | In Progress |
| API & UI Edge Cases | `edge-cases/api-and-ui.md` | In Progress |
| Security & Compliance Edge Cases | `edge-cases/security-and-compliance.md` | In Progress |
| Operations Edge Cases | `edge-cases/operations.md` | In Progress |

---

*Documentation maintained by the LCMS Product & Engineering team. For questions about a specific document, refer to the Owner field in the header table of each file.*
