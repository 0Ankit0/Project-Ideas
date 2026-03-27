# Sequence Diagrams

## Detailed Sequence: Reservation Confirmation
1. API validates command + idempotency key.
2. Reservation service performs conflict check and transactional write.
3. Outbox publisher emits `ReservationConfirmed`.
4. Notification and fulfillment subscribers update downstream state.

## Detailed Sequence: Settlement Finalization
1. Settlement service loads usage and incident evidence.
2. Policy engine calculates charges and adjustments.
3. Ledger post and reconciliation task are emitted atomically.
