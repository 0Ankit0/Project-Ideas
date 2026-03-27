# Class Diagrams

## Core Classes
- `Resource`
- `Reservation`
- `Fulfillment`
- `Settlement`
- `IncidentClaim`

## Important Associations
- `Reservation` references one or many `Resource` units.
- `Fulfillment` references one `Reservation` and emits lifecycle events.
- `Settlement` composes charges, adjustments, and reconciliation records.
