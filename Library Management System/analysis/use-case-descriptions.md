# Use Case Descriptions - Library Management System

## UC-01: Search Catalog and Discover Availability
**Primary Actor**: Patron  
**Goal**: Find relevant titles and determine availability by branch or digital access.

**Preconditions**:
- Catalog and search index are available.
- Patron has access to the public discovery interface.

**Main Flow**:
1. Patron enters keywords, author, subject, or identifier.
2. System returns relevant titles with format, branch availability, and hold status.
3. Patron opens a title detail page to inspect copies, descriptions, and pickup options.

**Postconditions**:
- Patron can proceed to hold, borrow, or save the title.

---

## UC-02: Check Out Item to Patron
**Primary Actor**: Librarian / Circulation Staff

**Main Flow**:
1. Staff identifies the patron account.
2. Staff scans the item barcode or RFID tag.
3. System validates membership, account restrictions, item eligibility, and hold ownership.
4. System creates the loan, calculates due date, and updates item status.
5. Patron receives due-date confirmation.

**Exceptions**:
- E1: Account blocked by fines or expiry -> checkout is denied or escalated.
- E2: Item reserved for another patron -> issue is blocked.

---

## UC-03: Return and Queue Next Hold
**Primary Actor**: Librarian / Circulation Staff

**Main Flow**:
1. Staff scans the returned item.
2. System closes the open loan and calculates overdue fines if any.
3. System checks for active hold queues.
4. If a hold exists, system marks the item `on_hold_shelf` or triggers transfer.
5. Notifications are sent to the relevant patron or branch.

---

## UC-04: Place Hold and Select Pickup Branch
**Primary Actor**: Patron

**Main Flow**:
1. Patron selects a title and requests a hold.
2. System validates eligibility, branch rules, and queue position.
3. Patron selects a pickup branch.
4. System confirms hold placement and expected wait visibility.

---

## UC-05: Catalog New Title and Item Copies
**Primary Actor**: Cataloging Staff

**Main Flow**:
1. Staff creates or imports a bibliographic record.
2. System checks for likely duplicates.
3. Staff assigns classification, subjects, language, and format metadata.
4. Staff creates copy/item records with branch, barcode, and shelf location.
5. Title becomes available for discovery and circulation when released.

---

## UC-06: Procure and Receive Materials
**Primary Actor**: Acquisitions Staff

**Main Flow**:
1. Staff creates a purchase request or purchase order.
2. Vendor and expected delivery details are recorded.
3. On receipt, staff records delivered quantities and discrepancies.
4. Items proceed to accessioning and cataloging.

---

## UC-07: Execute Branch Transfer and Inventory Audit
**Primary Actor**: Branch Manager

**Main Flow**:
1. Manager or staff initiates transfer or count activity.
2. System creates transfer tasks or audit sessions.
3. Staff scans items during packing, shipping, receipt, or shelf count.
4. System records discrepancies, missing items, and status changes.

---

## UC-08: Configure Policies and Operational Rules
**Primary Actor**: Admin

**Main Flow**:
1. Admin updates loan periods, fine rules, branch calendars, or patron-category limits.
2. System validates conflicts and effective dates.
3. New policies are versioned and applied according to configuration.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Scenario-level behavioral contracts

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Each use case must include primary path, alternate path, business exceptions, and post-conditions.
- Add explicit data mutations and emitted events for each step to support service decomposition.
- Capture actor authorization constraints per step rather than only at use-case level.

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
