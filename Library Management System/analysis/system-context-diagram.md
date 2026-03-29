# System Context Diagram - Library Management System

```mermaid
flowchart LR
    patrons[Patrons]
    staff[Library Staff]
    vendors[Book and Media Vendors]
    payment[Payment Provider]
    notify[Email / SMS Services]
    digital[Digital Content Provider]
    devices[Barcode / RFID Devices]

    subgraph lms[Library Management System]
        portal[Patron Portal]
        workspace[Staff Workspace]
        api[Application API]
        search[Catalog Search]
    end

    patrons --> portal
    staff --> workspace
    portal --> api
    workspace --> api
    api --> vendors
    api --> payment
    api --> notify
    api --> digital
    api --> devices
    api --> search
```

## Context Notes

- Patrons mainly interact through discovery, holds, and account-management workflows.
- Staff use operational tools for circulation, cataloging, acquisitions, inventory, and reporting.
- The platform may integrate with payments, notifications, RFID/barcode tooling, and digital-content vendors.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: External system dependencies

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Show trust boundaries and token propagation between identity provider, payment gateway, and messaging platform.
- Define failure isolation behavior when external systems are degraded so circulation invariants remain intact.
- Include data residency boundaries for multi-branch or multi-region deployments.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Mermaid implementation reference
```mermaid
flowchart LR
    Patron --> LMS[Library Management System]
    Staff --> LMS
    LMS --> IDP[Identity Provider]
    LMS --> PAY[Payment Gateway]
    LMS --> MSG[Email/SMS Gateway]
    LMS --> ERP[Procurement/Finance]
    PAY -. outage .-> LMS
    MSG -. retry/outbox .-> LMS
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
