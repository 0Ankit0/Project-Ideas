# ERD / Database Schema

## Core Tables
- `resources`
- `availability_windows`
- `reservations`
- `reservation_events`
- `fulfillments`
- `settlements`
- `incident_claims`
- `reconciliation_runs`

## Constraints
- Unique `(resource_id, start_at, end_at, state)` for active reservation overlap guard.
- Foreign key integrity between reservation, fulfillment, and settlement chains.
- Tenant-scoped partition keys for isolation and retention controls.
