# Lifecycle Orchestration

## Orchestration Strategy
Use saga orchestration for cross-context transitions where partial failures are possible.

## Compensation Examples
- Reservation confirmed but payment capture fails -> move to `CANCELLED` with release event.
- Return posted but settlement post fails -> queue retry with operator-visible exception.
- Dispute opened after provisional settlement -> transition to `DISPUTED` and freeze close.

## Operability
All orchestration steps emit correlated trace ids and domain event ids for replay.
