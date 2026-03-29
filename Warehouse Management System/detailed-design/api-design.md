# API Design

## Purpose
Define concrete API contracts for receiving, allocation, picking, packing, shipping, and exception handling.

## API Standards
- REST JSON with versioned paths (`/api/v1/...`).
- Mutating endpoints require `Idempotency-Key` and `X-Correlation-Id`.
- Errors include `code`, `message`, `retryable`, `rule_id`.

## Core Command Endpoints

| Endpoint | Purpose | Success | Common Failure |
|---|---|---|---|
| `POST /api/v1/receipts` | Record received quantity by ASN line | `201` with `receipt_id` | `422 RECEIPT_TOLERANCE_BREACH` |
| `POST /api/v1/putaway/tasks/generate` | Create putaway work from receipt | `202` with task batch id | `409 DUPLICATE_GENERATION` |
| `POST /api/v1/waves` | Build wave from eligible orders | `202` with `wave_id` | `409 INSUFFICIENT_ALLOCATABLE_STOCK` |
| `POST /api/v1/picks/{taskId}/confirm` | Confirm pick execution | `200` | `409 RESERVATION_MISMATCH` |
| `POST /api/v1/packs/{shipmentId}/close` | Reconcile and close package | `200` | `422 PACK_RECONCILIATION_FAILED` |
| `POST /api/v1/shipments/{shipmentId}/confirm` | Finalize shipping handoff | `200` | `503 CARRIER_CONFIRMATION_UNAVAILABLE` |
| `POST /api/v1/exceptions/{caseId}/resolve` | Resolve exception with action | `200` | `409 EXCEPTION_STATE_CONFLICT` |

## Example: Pick Confirmation Request
```json
{
  "taskId": "PT-100045",
  "reservationId": "RSV-9922",
  "sku": "SKU-1234",
  "pickedQty": 4,
  "bin": "A-03-07",
  "deviceTimestamp": "2026-03-28T10:10:33Z"
}
```

### Validation and Rule Mapping
1. Verify task is `Assigned|InProgress` (BR-2).
2. Verify reservation linkage and non-negative ATP post-mutation (BR-7).
3. Persist mutation + audit + outbox in one transaction (BR-5).

## Exception API Behavior
- Exception resolution actions allowed: `RETRY`, `REALLOCATE`, `HOLD`, `BACKORDER`, `MANUAL_OVERRIDE`.
- `MANUAL_OVERRIDE` requires `approverId`, `reasonCode`, `expiresAt` (BR-4).
- Retry actions must preserve original `Idempotency-Key` lineage.

## Observability Requirements
- Emit RED metrics per endpoint and warehouse partition.
- Audit log every state-changing call with outcome and violated rule ids.
- Record p95/p99 latency and retry counts for carrier/OMS integrations.
