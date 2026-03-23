# ERD and Database Schema - Library Management System

```mermaid
erDiagram
    BRANCH ||--o{ PATRON : registers
    BRANCH ||--o{ ITEM_COPY : stores
    BIBLIOGRAPHIC_RECORD ||--o{ ITEM_COPY : has
    BIBLIOGRAPHIC_RECORD ||--o{ HOLD_REQUEST : targets
    BIBLIOGRAPHIC_RECORD ||--o{ DIGITAL_LICENSE : grants
    PATRON ||--o{ LOAN : owns
    PATRON ||--o{ HOLD_REQUEST : creates
    PATRON ||--o{ FINE_LEDGER_ENTRY : accrues
    ITEM_COPY ||--o{ LOAN : generates
    ITEM_COPY ||--o{ TRANSFER_REQUEST : moves
    VENDOR ||--o{ PURCHASE_ORDER : supplies
    BRANCH ||--o{ INVENTORY_AUDIT : executes
```

## Table Notes

| Table | Notes |
|-------|-------|
| branches | Operational branches and calendars |
| patrons | Patron identity, category, status, home branch |
| bibliographic_records | Title-level catalog metadata |
| item_copies | Branch-level physical inventory |
| loans | Circulation history and active borrowing state |
| hold_requests | Waitlist and pickup workflow |
| fine_ledger_entries | Financial events, waivers, and adjustments |
| purchase_orders | Acquisition process tracking |
| transfer_requests | Inter-branch movement chain of custody |
| inventory_audits | Shelf counts and discrepancy sessions |
| digital_licenses | Optional digital lending rights and caps |
| audit_logs | Immutable operational history |
