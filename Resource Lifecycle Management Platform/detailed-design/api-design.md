# API Design

## Core APIs
- `POST /v1/resources/search`
- `POST /v1/reservations` (idempotency key required)
- `POST /v1/reservations/{id}:confirm`
- `POST /v1/fulfillments/{id}:checkout`
- `POST /v1/fulfillments/{id}:checkin`
- `POST /v1/settlements/{id}:finalize`

## API Reliability Contracts
- Idempotency key required for mutating operations.
- Error model includes typed reason codes for policy/conflict/payment failures.
- Versioned event payload schemas for downstream consumers.

## Security Controls
- Tenant context required on all domain reads/writes.
- Service-to-service auth via scoped workload identity.
- Field-level redaction for sensitive evidence payloads.
