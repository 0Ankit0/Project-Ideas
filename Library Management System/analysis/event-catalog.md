# Event Catalog - Library Management System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| patron.registered | Membership Service | Notification, Reporting | New patron created |
| catalog.record_published | Catalog Service | Search Index, Reporting | Title ready for discovery |
| item.checked_out | Circulation Service | Notification, Reporting | Loan created |
| item.returned | Circulation Service | Hold Service, Reporting | Loan closed and inventory updated |
| hold.placed | Hold Service | Notification, Reporting | Patron joined reservation queue |
| hold.ready_for_pickup | Hold Service | Notification Service | Item available for patron |
| loan.overdue | Policy Engine | Notification, Fine Service | Loan crossed overdue threshold |
| fine.assessed | Fine Service | Patron Account, Reporting | Fine or charge applied |
| purchase_order.received | Acquisitions Service | Cataloging Queue, Reporting | Stock intake recorded |
| transfer.dispatched | Transfer Service | Destination Branch, Reporting | Item left source branch |
| inventory.discrepancy_found | Inventory Service | Branch Manager, Audit | Count mismatch detected |
| digital_loan.started | Digital Lending Service | Notification, Reporting | Digital access granted |
| admin.policy_changed | Admin Service | Audit, Policy Engine | Rules or calendars updated |
