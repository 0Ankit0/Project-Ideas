# Payment Reconciliation Across Channels

## Failure Modes
- Card, wallet, and bank-transfer settlements arriving asynchronously
- Gateway fee adjustments not reflected in internal ledger
- Refund/cancellation mismatch across sub-ledgers

## Controls
- Daily three-way reconciliation (bookings, gateway reports, GL)
- Adjustment journal entries with approval workflow
- Exception dashboard with aging SLA and ownership
