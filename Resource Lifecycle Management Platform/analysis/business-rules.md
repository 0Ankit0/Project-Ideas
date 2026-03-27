# Business Rules

## Reservation Rules
1. A resource unit cannot be simultaneously confirmed for overlapping windows.
2. Hold tokens expire automatically and release inventory.
3. Amendment requests must pass conflict and policy checks before commit.

## Fulfillment Rules
1. Fulfillment cannot begin unless reservation is `CONFIRMED`.
2. Return evidence is mandatory for incident-prone resource classes.
3. Partial return requires unit-level state updates and prorated billing events.

## Settlement Rules
1. Closing is blocked while active disputes remain unresolved.
2. Refunds and waivers require policy evaluation and approver traceability.
3. Reconciliation exceptions must be triaged within configured SLA windows.
