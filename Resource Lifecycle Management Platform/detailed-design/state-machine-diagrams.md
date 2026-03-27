# State Machine Diagrams

## Reservation Aggregate
`DRAFT -> HELD -> CONFIRMED -> FULFILLED -> RETURNED -> SETTLED -> CLOSED`

Terminal/alternate states:
- `CANCELLED`
- `EXPIRED`
- `DISPUTED` (sub-state before `SETTLED`)

## Invariants
- Transition to `FULFILLED` requires valid reservation ownership and policy checks.
- Transition to `SETTLED` requires inspection completion and charge finalization.
- Any compensation transition appends immutable event records and reason codes.
