# Business Rules - Library Management System

## Membership and Eligibility
- Patrons with expired memberships cannot initiate new checkouts or holds until renewed.
- Borrowing limits vary by patron category, item format, and branch policy.
- Staff override actions require explicit reason capture and audit logging.

## Circulation Rules

| Policy Area | Baseline Rule |
|-------------|---------------|
| Standard loan period | Configurable by patron category and item type |
| Renewal eligibility | Allowed only if no active hold exists and max-renewal count not exceeded |
| Overdue handling | Fines or blocks apply after grace period based on policy |
| Claimed returned | Item enters exception review; account restrictions may be partial or full |
| Lost or damaged | Replacement fee or workflow decision required before item is closed out |

## Hold and Waitlist Rules
- Hold queues are ordered by policy priority, request time, and patron eligibility.
- A returned item with an active hold cannot be reshelved as generally available inventory.
- Hold pickup windows expire automatically according to branch policy.

## Cataloging Rules
- Duplicate bibliographic records should be merged when a canonical record is confirmed.
- Item-copy barcodes must be unique across all branches.
- Non-circulating and reference materials must not enter standard loan workflows.

## Inventory and Acquisition Rules
- Received quantities must reconcile with purchase orders or create discrepancy records.
- Transfers must maintain chain-of-custody states from source branch to destination branch.
- Inventory write-offs, waivers, and repairs require auditable approval flows.
