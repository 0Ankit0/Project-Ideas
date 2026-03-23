# Data Dictionary - Library Management System

| Entity | Key Fields | Description |
|--------|------------|-------------|
| Branch | id, name, code, address, status | Physical operating location |
| Patron | id, membershipNo, category, status, homeBranchId, expiryDate | Borrowing account holder |
| StaffUser | id, role, branchScope, status | Staff or admin account |
| BibliographicRecord | id, title, subtitle, authors, isbn, format, language, subjects | Catalog title-level metadata |
| ItemCopy | id, recordId, branchId, barcode, status, shelfLocation | Circulating or reference copy |
| Loan | id, patronId, itemCopyId, issuedAt, dueAt, returnedAt, status | Checkout transaction |
| HoldRequest | id, patronId, recordId, pickupBranchId, queuePosition, status | Reservation or waitlist entry |
| FineLedgerEntry | id, patronId, loanId, amount, type, status | Fine, fee, waiver, or adjustment event |
| Vendor | id, name, accountRef, status | Supplier or content partner |
| PurchaseOrder | id, vendorId, branchId, status, orderedAt, receivedAt | Acquisition workflow container |
| TransferRequest | id, itemCopyId, sourceBranchId, destinationBranchId, status | Inter-branch movement record |
| InventoryAudit | id, branchId, startedAt, completedAt, status | Shelf count or audit session |
| DigitalLicense | id, recordId, provider, concurrentLimit, accessWindowDays | Optional digital lending entitlement |
| Notification | id, recipientType, recipientId, templateKey, channel, status | Patron or staff communication |
| AuditLog | id, actorId, action, entityType, entityId, createdAt | Immutable operational history |
