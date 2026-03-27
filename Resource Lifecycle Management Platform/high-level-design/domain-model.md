# Domain Model

## Bounded Contexts
- **Catalog Context:** resource types, units, and availability constraints.
- **Reservation Context:** holds, confirmations, amendments, cancellations.
- **Fulfillment Context:** checkout/checkin execution and evidence.
- **Settlement Context:** billing, adjustments, reconciliation, close.
- **Governance Context:** audit, compliance, dispute lifecycle.

## Aggregate Ownership
Reservation aggregate is authoritative for lifecycle progression until return completion;
settlement aggregate owns final financial closure.
