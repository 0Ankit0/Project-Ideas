# User Stories - Library Management System

## Patron

- **US-PAT-001**: As a patron, I want to search by title, author, subject, and branch so I can quickly find available materials.
- **US-PAT-002**: As a patron, I want to place a hold and choose a pickup branch so I can borrow materials even when they are not currently available.
- **US-PAT-003**: As a patron, I want to renew eligible loans so I can continue borrowing without visiting the library.
- **US-PAT-004**: As a patron, I want to view due dates, fines, and account restrictions so I know when action is needed.
- **US-PAT-005**: As a patron, I want to access digital loans from my account when licenses are available.

## Librarian / Circulation Staff

- **US-LIB-001**: As circulation staff, I want to check items out to patrons with barcode scans so service is fast and accurate.
- **US-LIB-002**: As circulation staff, I want the system to block or warn on policy violations so I do not miss eligibility issues.
- **US-LIB-003**: As circulation staff, I want to process returns, holds, and fines from the same workspace so desk operations stay efficient.
- **US-LIB-004**: As circulation staff, I want to record lost, damaged, or claimed-returned items with notes so exceptions stay auditable.

## Cataloging Staff

- **US-CAT-001**: As cataloging staff, I want to create and update bibliographic records with classification metadata so the catalog stays searchable and consistent.
- **US-CAT-002**: As cataloging staff, I want duplicate-detection and merge support so redundant records do not confuse patrons or staff.
- **US-CAT-003**: As cataloging staff, I want item-copy records linked to bibliographic entries and branch locations so inventory remains accurate.

## Acquisitions Staff

- **US-ACQ-001**: As acquisitions staff, I want to manage vendors, purchase requests, and receiving workflows so new stock is tracked from request to shelf.
- **US-ACQ-002**: As acquisitions staff, I want to record receiving discrepancies and damaged deliveries so supplier issues are traceable.

## Branch Manager

- **US-BRM-001**: As a branch manager, I want dashboards for circulation, overdue trends, and inventory exceptions so I can manage branch performance.
- **US-BRM-002**: As a branch manager, I want transfer and shelf-audit visibility so I can detect misplaced or missing items quickly.

## Admin

- **US-ADM-001**: As an admin, I want configurable circulation, fine, holiday, and membership policies so the system adapts to library rules.
- **US-ADM-002**: As an admin, I want role templates, branch scopes, and audit access so privileged operations remain controlled.
- **US-ADM-003**: As an admin, I want integration settings for notifications, payments, and digital providers so supporting services are manageable.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: User-story completion criteria

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Expand stories with acceptance tests for normal, alternate, and exception paths.
- Include policy-decision visibility requirements for patron and staff UI workflows.
- Add non-functional criteria (latency, reliability, accessibility) to circulation stories.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
