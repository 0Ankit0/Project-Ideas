# API Design

Complete REST API specification for the **Resource Lifecycle Management Platform**. All endpoints require a valid Bearer JWT. All write commands require an `Idempotency-Key` header.

---

## Base URL

```
https://api.rlmp.example.com/v1
```

## Authentication

All requests require `Authorization: Bearer <jwt>`. JWT claims must include `tenant_id`, `user_id`, and `roles[]`. The API Gateway validates tokens against the configured Identity Provider.

## Common Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <jwt>` |
| `Idempotency-Key` | Yes (write ops) | Client-generated UUID; ensures exactly-once processing |
| `X-Correlation-ID` | Optional | Client-supplied; propagated through all services |
| `Content-Type` | Yes (body) | `application/json` |

## Common Error Response

```json
{
  "error_code": "WINDOW_CONFLICT",
  "message": "Reservation window conflicts with existing reservation",
  "correlation_id": "abc123",
  "details": { "conflicting_reservation_id": "...", "alternatives": [] }
}
```

---

## Resources

### POST /resources
Provision a new resource into the catalog.

**Required role**: `resource_manager`

**Request Body**:
```json
{
  "template_id": "uuid",
  "name": "MacBook Pro 16 #42",
  "category": "EQUIPMENT",
  "asset_tag": "MBPR-0042",
  "serial_number": "C02XG123HV2N",
  "condition_grade": "A",
  "condition_notes": "New in box",
  "location_id": "uuid",
  "cost_centre": "ENG-012",
  "acquisition_cost": 2499.00,
  "currency": "USD",
  "policy_profile_id": "uuid"
}
```

**Response 201**:
```json
{
  "resource_id": "uuid",
  "state": "AVAILABLE",
  "created_at": "2025-06-01T09:00:00Z"
}
```

**Error Codes**: `400 VALIDATION_FAILED`, `422 QUOTA_EXCEEDED`, `404 TEMPLATE_NOT_FOUND`

---

### GET /resources
Search and filter the resource catalog.

**Required role**: Any authenticated user

**Query Parameters**:

| Parameter | Type | Description |
|---|---|---|
| `category` | Enum | Filter by resource category |
| `state` | Enum | Filter by lifecycle state |
| `location_id` | UUID | Filter by location |
| `available_from` | ISO 8601 | Availability window start |
| `available_to` | ISO 8601 | Availability window end |
| `condition_grade` | A–D | Minimum condition grade |
| `q` | String | Full-text search on name/tag |
| `page` | Integer | Pagination (default 1) |
| `page_size` | Integer | Results per page (max 100) |

**Response 200**:
```json
{
  "items": [
    {
      "resource_id": "uuid",
      "name": "MacBook Pro 16 #42",
      "category": "EQUIPMENT",
      "asset_tag": "MBPR-0042",
      "condition_grade": "A",
      "state": "AVAILABLE",
      "location": { "name": "HQ Floor 3", "building": "A" }
    }
  ],
  "total": 142,
  "page": 1,
  "page_size": 20
}
```

---

### GET /resources/{resource_id}
Get full details for a specific resource.

**Response 200**:
```json
{
  "resource_id": "uuid",
  "name": "MacBook Pro 16 #42",
  "category": "EQUIPMENT",
  "asset_tag": "MBPR-0042",
  "serial_number": "C02XG123HV2N",
  "condition_grade": "B",
  "state": "AVAILABLE",
  "location_id": "uuid",
  "cost_centre": "ENG-012",
  "acquisition_cost": 2499.00,
  "currency": "USD",
  "policy_profile_id": "uuid",
  "created_at": "2025-06-01T09:00:00Z",
  "updated_at": "2025-06-10T14:30:00Z",
  "version": 3
}
```

**Error Codes**: `404 RESOURCE_NOT_FOUND`

---

### POST /resources/bulk
Bulk provision resources from a validated CSV.

**Required role**: `resource_manager`

**Request**: `multipart/form-data` with `file` (CSV) and `template_id` fields.

**Response 201**: `{ "imported_count": 250, "resource_ids": ["uuid", ...] }`

**Response 400** (partial validation failure):
```json
{
  "error_code": "BULK_VALIDATION_FAILED",
  "row_errors": [
    { "row": 3, "field": "asset_tag", "message": "Duplicate asset_tag" }
  ]
}
```

---

### POST /resources/{resource_id}/decommission
Request decommissioning of a resource.

**Required role**: `resource_manager`

**Request Body**:
```json
{
  "reason": "End of support lifecycle",
  "disposal_method": "RESALE"
}
```

**Response 202**: `{ "request_id": "uuid", "requires_approval": true, "approval_task_id": "uuid" }`

**Error Codes**: `409 DECOMMISSION_BLOCKED`, `409 RETENTION_LOCK_ACTIVE`

---

## Reservations

### POST /reservations
Create a new reservation.

**Required role**: `requestor` or any authenticated user with `reservation:create` scope

**Request Body**:
```json
{
  "resource_id": "uuid",
  "start_at": "2025-07-01T09:00:00Z",
  "end_at": "2025-07-03T18:00:00Z",
  "priority": 5,
  "notes": "Required for client demo"
}
```

**Response 201**:
```json
{
  "reservation_id": "uuid",
  "resource_id": "uuid",
  "state": "CONFIRMED",
  "start_at": "2025-07-01T09:00:00Z",
  "end_at": "2025-07-03T18:00:00Z",
  "sla_due_at": "2025-07-01T09:30:00Z",
  "priority": 5
}
```

**Error Codes**: `409 WINDOW_CONFLICT`, `422 QUOTA_EXCEEDED`, `422 ELIGIBILITY_DENIED`

---

### DELETE /reservations/{reservation_id}
Cancel a reservation.

**Required role**: Reservation owner or `resource_manager`

**Request Body**: `{ "reason": "No longer needed" }`

**Response 200**: `{ "reservation_id": "uuid", "state": "CANCELLED" }`

**Error Codes**: `409 RESERVATION_ALREADY_CONVERTED`, `404 RESERVATION_NOT_FOUND`

---

### GET /reservations
List reservations for the authenticated user (or all for `resource_manager`).

**Query Parameters**: `resource_id`, `state`, `from`, `to`, `requestor_id` (manager only), `page`, `page_size`

---

## Allocations

### POST /allocations
Check out a resource (initiate allocation from a reservation).

**Required role**: Custodian (reservation owner or delegated)

**Request Body**:
```json
{
  "reservation_id": "uuid",
  "condition_grade": "A",
  "condition_notes": "No marks observed"
}
```

**Response 201**:
```json
{
  "allocation_id": "uuid",
  "resource_id": "uuid",
  "custodian_id": "uuid",
  "checkout_at": "2025-07-01T09:15:00Z",
  "due_at": "2025-07-03T18:00:00Z",
  "state": "ACTIVE"
}
```

**Error Codes**: `422 CHECKOUT_WINDOW_EXPIRED`, `409 RESOURCE_UNAVAILABLE`

---

### POST /allocations/{allocation_id}/checkin
Return a resource and record condition.

**Required role**: Custodian or `operations`

**Request Body**:
```json
{
  "condition_grade": "B",
  "condition_notes": "Minor scratch on lid",
  "photo_evidence_refs": ["s3://bucket/photo1.jpg"]
}
```

**Response 200**:
```json
{
  "allocation_id": "uuid",
  "state": "RETURNED",
  "checkin_at": "2025-07-03T17:45:00Z",
  "condition_delta": "MINOR",
  "incident_case_id": null
}
```

---

### POST /allocations/{allocation_id}/extend
Request an allocation extension.

**Required role**: Custodian (current allocation owner)

**Request Body**: `{ "new_due_at": "2025-07-05T18:00:00Z", "reason": "Project extended" }`

**Response 200**: `{ "allocation_id": "uuid", "new_due_at": "2025-07-05T18:00:00Z" }`

**Error Codes**: `422 EXTENSION_LIMIT_REACHED`, `409 WINDOW_CONFLICT_AFTER_EXTENSION`

---

### POST /allocations/{allocation_id}/force-return
Initiate a forced return (operations only).

**Required role**: `operations`

**Request Body**: `{ "approver_id": "uuid", "reason_code": "UNRESPONSIVE_CUSTODIAN" }`

**Response 200**: `{ "allocation_id": "uuid", "state": "FORCED_RETURN" }`

---

### POST /allocations/{allocation_id}/transfer
Transfer custody to another user.

**Required role**: Current custodian

**Request Body**: `{ "to_actor_id": "uuid", "reason": "Temporary handoff during travel" }`

**Response 200**: `{ "transfer_id": "uuid", "allocation_id": "uuid", "new_custodian_id": "uuid" }`

---

## Incidents

### GET /incidents
List incident cases (filtered by role and scope).

**Query Parameters**: `resource_id`, `allocation_id`, `case_type`, `state`, `severity`, `from`, `to`

### GET /incidents/{case_id}
Get details of a specific incident case.

### PATCH /incidents/{case_id}
Update incident case (assign owner, update status, add notes).

**Required role**: `operations` or `resource_manager`

**Request Body**: `{ "owner_id": "uuid", "state": "IN_REVIEW", "notes": "Investigating condition" }`

### POST /incidents/{case_id}/resolve
Resolve an incident case.

**Required role**: `operations` or `resource_manager`

**Request Body**: `{ "resolution_notes": "Damage confirmed; settlement initiated", "outcome": "SETTLEMENT_REQUIRED" }`

---

## Settlements

### GET /settlements
List settlement records.

**Query Parameters**: `case_id`, `state`, `charge_type`, `from`, `to`

### POST /settlements/{settlement_id}/approve
Approve a pending settlement charge.

**Required role**: `finance`

### POST /settlements/{settlement_id}/dispute
Dispute a settlement charge.

**Required role**: `requestor` (charge owner) or `finance`

**Request Body**: `{ "dispute_notes": "Condition was pre-existing; photo evidence attached" }`

### POST /settlements/{settlement_id}/void
Void a settlement charge after dispute resolution.

**Required role**: `finance`

**Request Body**: `{ "reason": "Dispute upheld; pre-existing condition confirmed" }`

---

## Audit

### GET /audit/resources/{resource_id}
Return the full audit trail for a resource from provisioning to present.

**Required role**: `compliance`, `resource_manager`, or `operations`

**Response 200**:
```json
{
  "resource_id": "uuid",
  "events": [
    {
      "audit_id": "uuid",
      "command": "PROVISION",
      "actor_id": "uuid",
      "before_state": null,
      "after_state": { "state": "PENDING" },
      "correlation_id": "uuid",
      "timestamp": "2025-06-01T09:00:00Z"
    }
  ],
  "total": 47
}
```

---

## Rate Limiting

| Endpoint Group | Limit | Window |
|---|---|---|
| Read endpoints (GET) | 1,000 req | 1 minute per tenant |
| Write commands (POST/PATCH/DELETE) | 100 req | 1 minute per user |
| Bulk import | 5 req | 1 minute per tenant |

---

## Versioning and Backward Compatibility

- The API version is embedded in the path (`/v1`).
- Additive changes (new optional fields, new endpoints) are non-breaking.
- Breaking changes (field removal, type changes) require a new version (`/v2`) with a minimum 12-month deprecation period for `/v1`.
- Deprecation is announced via the `Deprecation` and `Sunset` HTTP headers.
