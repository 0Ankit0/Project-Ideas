# Class Diagram - Library Management System

```mermaid
classDiagram
    class Branch {
      +UUID id
      +string name
      +string code
      +string status
    }
    class Patron {
      +UUID id
      +string membershipNo
      +string category
      +string status
      +date expiryDate
    }
    class BibliographicRecord {
      +UUID id
      +string title
      +string format
      +string language
    }
    class ItemCopy {
      +UUID id
      +string barcode
      +string status
      +string shelfLocation
    }
    class Loan {
      +UUID id
      +datetime issuedAt
      +datetime dueAt
      +datetime returnedAt
      +string status
    }
    class HoldRequest {
      +UUID id
      +int queuePosition
      +string status
      +datetime expiresAt
    }
    class FineLedgerEntry {
      +UUID id
      +decimal amount
      +string type
      +string status
    }
    class Vendor {
      +UUID id
      +string name
      +string status
    }
    class PurchaseOrder {
      +UUID id
      +string status
      +datetime orderedAt
    }
    class TransferRequest {
      +UUID id
      +string status
    }
    class DigitalLicense {
      +UUID id
      +int concurrentLimit
      +int accessWindowDays
    }

    Branch "1" --> "many" ItemCopy
    Branch "1" --> "many" Patron
    BibliographicRecord "1" --> "many" ItemCopy
    BibliographicRecord "1" --> "many" HoldRequest
    BibliographicRecord "0..1" --> "many" DigitalLicense
    Patron "1" --> "many" Loan
    Patron "1" --> "many" HoldRequest
    Patron "1" --> "many" FineLedgerEntry
    ItemCopy "1" --> "many" Loan
    ItemCopy "1" --> "many" TransferRequest
    Vendor "1" --> "many" PurchaseOrder
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Domain model and aggregate integrity

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Identify aggregate roots (`Loan`, `HoldRequest`, `Copy`) and enforce invariants within aggregate boundaries.
- Represent value objects for policy snapshot and money to avoid primitive obsession.
- Document invariants as class-level constraints so generated code/tests can enforce them.

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
classDiagram
    class Copy {+id +state +rowVersion}
    class Loan {+id +copyId +memberId +dueAt +closedAt}
    class HoldRequest {+id +titleId +memberId +rank +status}
    class FineLedgerEntry {+id +loanId +amount +type}
    Copy "1" --> "0..1" Loan : activeLoan
    HoldRequest "*" --> "1" Copy : allocatedCopy
    Loan "1" --> "*" FineLedgerEntry : charges
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
