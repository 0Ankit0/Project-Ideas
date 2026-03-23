# Domain Model - Library Management System

## Core Domain Areas

| Domain Area | Key Concepts |
|-------------|--------------|
| Identity and Membership | Patron, StaffUser, PatronCategory, Branch |
| Catalog and Inventory | BibliographicRecord, ItemCopy, Subject, Classification, ShelfLocation |
| Circulation | Loan, Renewal, FineLedgerEntry, CirculationPolicy |
| Reservation and Transfer | HoldRequest, PickupWindow, TransferRequest |
| Acquisitions | Vendor, PurchaseOrder, ReceivingRecord, Accession |
| Digital Access | DigitalLicense, DigitalLoan, ProviderAccount |
| Operations | Notification, AuditLog, InventoryAudit |

## Relationship Summary
- A **bibliographic record** may own many item copies and optional digital licenses.
- A **patron** may have many loans, holds, and financial ledger entries.
- Each **item copy** belongs to a branch and moves through circulation, transfer, repair, or audit states.
- **Policies** govern eligibility, fines, queue behavior, and holiday-aware due dates.

```mermaid
erDiagram
    BRANCH ||--o{ ITEM_COPY : stores
    BRANCH ||--o{ PATRON : serves
    BIBLIOGRAPHIC_RECORD ||--o{ ITEM_COPY : has
    BIBLIOGRAPHIC_RECORD ||--o{ HOLD_REQUEST : targets
    PATRON ||--o{ LOAN : borrows
    PATRON ||--o{ HOLD_REQUEST : creates
    PATRON ||--o{ FINE_LEDGER_ENTRY : owes
    ITEM_COPY ||--o{ LOAN : circulates
    ITEM_COPY ||--o{ TRANSFER_REQUEST : moves
    VENDOR ||--o{ PURCHASE_ORDER : supplies
```
