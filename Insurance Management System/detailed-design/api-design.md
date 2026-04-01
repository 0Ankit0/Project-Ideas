# API Design — Insurance Management System

## API Conventions

| Convention | Specification |
|---|---|
| **Style** | RESTful, resource-oriented, JSON (`application/json`) |
| **Versioning** | URI path prefix: `/api/v1/`. Breaking changes increment to `/api/v2/`. Non-breaking additions are backward-compatible within the same version. |
| **Authentication** | OAuth 2.0 Authorization Code + PKCE for browser clients. Client Credentials for M2M service accounts. JWT Bearer tokens (`Authorization: Bearer <token>`). |
| **Token Issuer** | Internal Auth Service (Keycloak). Token lifetime: 15 min access / 24 h refresh. |
| **Pagination** | Cursor-based. Query params: `limit` (default 20, max 100) and `after` (opaque cursor). Response envelope includes `data[]`, `pagination.next_cursor`, `pagination.has_more`. |
| **Filtering** | Query params per resource (e.g., `?status=ACTIVE&product_type=AUTO`). Date ranges: `?effective_date_from=2025-01-01&effective_date_to=2025-12-31`. |
| **Sorting** | `?sort=created_at:desc` — field colon direction. |
| **Idempotency** | POST operations accept `Idempotency-Key` header (UUID). Duplicate requests within 24 h return the cached response. |
| **Rate Limiting** | 1000 req/min per client_id. `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers on every response. |
| **Correlation** | `X-Correlation-ID` header propagated across all services for distributed tracing. |

### Standard Error Format

```json
{
  "error": {
    "code": "POLICY_NOT_FOUND",
    "message": "No policy found with the given identifier.",
    "details": [
      { "field": "policy_id", "issue": "Resource does not exist." }
    ],
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "timestamp": "2025-06-15T10:30:00Z"
  }
}
```

### Standard HTTP Status Codes

| Code | Meaning |
|---|---|
| `200 OK` | Successful GET, PUT |
| `201 Created` | Successful POST that creates a resource |
| `202 Accepted` | Async operation accepted (e.g., cancellation) |
| `204 No Content` | Successful DELETE with no response body |
| `400 Bad Request` | Validation failure |
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Valid token but insufficient scope |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Idempotency conflict or state machine violation |
| `422 Unprocessable Entity` | Business rule violation |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server fault |

---

## Policies API

### `GET /api/v1/policies`

**Scope:** `policies:read`

**Query Params:** `status`, `product_type`, `policyholder_id`, `broker_id`, `effective_date_from`, `effective_date_to`, `limit`, `after`, `sort`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "policy_number": "POL-2025-0001234",
      "status": "ACTIVE",
      "product_type": "HOME",
      "line_of_business": "PERSONAL_LINES",
      "policyholder_id": "...",
      "broker_id": "...",
      "effective_date": "2025-01-01",
      "expiry_date": "2026-01-01",
      "premium_amount": 1250.00,
      "created_at": "2025-01-01T09:00:00Z"
    }
  ],
  "pagination": { "next_cursor": "eyJpZCI6...", "has_more": true }
}
```

### `POST /api/v1/policies`

**Scope:** `policies:write`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "policyholder_id": "uuid",
  "broker_id": "uuid",
  "product_type": "AUTO",
  "line_of_business": "PERSONAL_LINES",
  "effective_date": "2025-07-01",
  "expiry_date": "2026-07-01",
  "payment_frequency": "MONTHLY",
  "coverages": [
    {
      "coverage_type": "LIABILITY",
      "coverage_code": "BI",
      "limit_amount": 300000,
      "deductible_amount": 0
    }
  ]
}
```

**Response `201`:** Full policy object with assigned `policy_number` and `status: QUOTED`.

### `GET /api/v1/policies/{id}`

**Scope:** `policies:read`

**Response `200`:** Full policy object including nested `coverages[]` and `endorsements[]`.

### `PUT /api/v1/policies/{id}`

**Scope:** `policies:write`

**Request Body:** Partial or full policy fields (excluding `policy_number`, `id`).

**Response `200`:** Updated policy object.

**Status codes:** `409` if policy is in `CANCELLED` or `EXPIRED` state.

### `DELETE /api/v1/policies/{id}`

**Scope:** `policies:cancel`

**Request Body:**
```json
{ "cancellation_reason": "INSURED_REQUEST", "cancellation_date": "2025-08-01" }
```

**Response `202`:** `{ "status": "CANCELLATION_SCHEDULED", "effective_date": "2025-08-01" }`

### `POST /api/v1/policies/{id}/endorse`

**Scope:** `policies:endorse`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "endorsement_type": "LIMIT_CHANGE",
  "effective_date": "2025-07-15",
  "changes": {
    "coverages": [{ "coverage_id": "uuid", "limit_amount": 500000 }]
  }
}
```

**Response `201`:** Endorsement object with `endorsement_number`, `status: PENDING`, and `premium_change`.

### `POST /api/v1/policies/{id}/renew`

**Scope:** `policies:write`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "renewal_effective_date": "2026-01-01",
  "premium_override": null,
  "coverage_changes": []
}
```

**Response `201`:** New policy object representing the renewal term, linked to originating policy.

---

## Claims API

### `GET /api/v1/claims`

**Scope:** `claims:read`

**Query Params:** `status`, `policy_id`, `adjuster_id`, `loss_type`, `fnol_date_from`, `fnol_date_to`, `fraud_flag`, `limit`, `after`

**Response `200`:** Paginated list of claim summary objects.

### `POST /api/v1/claims` (FNOL Intake)

**Scope:** `claims:write`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "policy_id": "uuid",
  "incident_date": "2025-06-10",
  "fnol_date": "2025-06-11",
  "loss_type": "AUTO_COLLISION",
  "incident_description": "Vehicle struck from rear at intersection.",
  "loss_location": "123 Main St, Austin TX 78701",
  "coverage_code": "BI",
  "estimated_loss_amount": 15000
}
```

**Response `201`:** Claim object with `claim_number`, `status: FNOL`, `reserve_amount` (initial automated reserve).

### `GET /api/v1/claims/{id}`

**Scope:** `claims:read`

**Response `200`:** Full claim object including reserve history and notes.

### `PUT /api/v1/claims/{id}/status`

**Scope:** `claims:adjust`

**Request Body:**
```json
{ "status": "UNDER_INVESTIGATION", "note": "Adjuster assigned. Inspection scheduled 2025-06-15." }
```

**Response `200`:** Updated claim object. `422` if transition is invalid.

### `POST /api/v1/claims/{id}/reserve`

**Scope:** `claims:adjust`

**Request Body:**
```json
{ "reserve_amount": 22000, "reason": "Revised estimate after inspection." }
```

**Response `201`:** Reserve change record with `previous_amount`, `new_amount`, `changed_by`, `timestamp`.

### `POST /api/v1/claims/{id}/settle`

**Scope:** `claims:settle`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "settlement_amount": 18500,
  "payment_method": "ACH",
  "payee_bank_account": "****4321",
  "settlement_notes": "Agreed final settlement. Signed release obtained."
}
```

**Response `202`:** `{ "status": "PENDING_SETTLEMENT", "payment_reference": "PAY-2025-98765" }`

---

## Premiums API

### `GET /api/v1/premiums`

**Scope:** `billing:read`

**Query Params:** `policy_id`, `status`, `due_date_from`, `due_date_to`, `limit`, `after`

**Response `200`:** Paginated list of invoice summaries.

### `GET /api/v1/premiums/{id}`

**Scope:** `billing:read`

**Response `200`:**
```json
{
  "id": "uuid",
  "invoice_number": "INV-2025-004521",
  "policy_id": "uuid",
  "billing_period": "2025-Q3",
  "amount_due": 312.50,
  "tax_amount": 25.00,
  "fees_amount": 5.00,
  "due_date": "2025-07-01",
  "paid_amount": 0,
  "status": "PENDING",
  "grace_period_end": "2025-07-31"
}
```

### `POST /api/v1/premiums/{id}/pay`

**Scope:** `billing:pay`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "payment_method": "CREDIT_CARD",
  "payment_token": "tok_visa_4242",
  "amount": 342.50
}
```

**Response `200`:** `{ "status": "PAID", "payment_reference": "ch_3Pf...", "paid_date": "2025-06-15" }`

### `GET /api/v1/premiums/{id}/schedule`

**Scope:** `billing:read`

**Response `200`:**
```json
{
  "policy_id": "uuid",
  "payment_frequency": "QUARTERLY",
  "installments": [
    { "invoice_number": "INV-2025-004521", "due_date": "2025-07-01", "amount_due": 342.50, "status": "PENDING" },
    { "invoice_number": "INV-2025-004522", "due_date": "2025-10-01", "amount_due": 342.50, "status": "PENDING" }
  ],
  "total_annual_premium": 1370.00
}
```

---

## Underwriting API

### `POST /api/v1/underwriting/applications`

**Scope:** `underwriting:submit`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "product_type": "AUTO",
  "applicant": {
    "policyholder_id": "uuid",
    "date_of_birth": "1985-03-22",
    "license_number": "TX12345678"
  },
  "vehicles": [{ "vin": "1HGCM82633A004352", "year": 2020, "make": "Honda", "model": "Accord" }],
  "coverage_requests": [
    { "coverage_type": "LIABILITY", "requested_limit": 300000 },
    { "coverage_type": "COLLISION", "requested_deductible": 500 }
  ],
  "broker_id": "uuid"
}
```

**Response `202`:** `{ "application_id": "uuid", "status": "RECEIVED", "estimated_decision_at": "2025-06-15T10:35:00Z" }`

### `GET /api/v1/underwriting/applications/{application_id}/status`

**Scope:** `underwriting:read`

**Response `200`:**
```json
{
  "application_id": "uuid",
  "status": "APPROVED",
  "risk_score": 42,
  "decision": "ACCEPT",
  "premium_indication": 1250.00,
  "decision_reasons": [],
  "valid_until": "2025-07-15T00:00:00Z"
}
```

### `POST /api/v1/underwriting/applications/{application_id}/decision`

**Scope:** `underwriting:decide` (underwriter role only)

**Request Body:**
```json
{ "decision": "ACCEPT", "override_reason": "Manual review — borderline credit.", "premium_override": 1300.00 }
```

**Response `200`:** Updated application with `status: APPROVED` and `decided_by`.

---

## Brokers API

### `GET /api/v1/brokers`

**Scope:** `brokers:read`

**Query Params:** `status`, `license_state`, `limit`, `after`

**Response `200`:** Paginated list of broker summaries including `commission_rate`, `status`, `license_expiry`.

### `GET /api/v1/brokers/{id}`

**Scope:** `brokers:read`

**Response `200`:** Full broker profile including appointed states, book of business stats (`active_policy_count`, `ytd_premium_volume`).

### `POST /api/v1/brokers/{id}/bind-policy`

**Scope:** `brokers:bind`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "application_id": "uuid",
  "payment_method": "AGENCY_BILL",
  "effective_date": "2025-07-01"
}
```

**Response `201`:** New policy object in `BOUND` status with `policy_number`.

---

## Reinsurance API

### `GET /api/v1/reinsurance/treaties`

**Scope:** `reinsurance:read`

**Query Params:** `treaty_type`, `status`, `reinsurer_name`, `limit`, `after`

**Response `200`:** Paginated list of treaty summaries.

### `POST /api/v1/reinsurance/cessions`

**Scope:** `reinsurance:write`  **Idempotency-Key:** required

**Request Body:**
```json
{
  "policy_id": "uuid",
  "treaty_id": "uuid",
  "ceded_premium": 250.00,
  "ceded_liability": 50000.00,
  "cession_date": "2025-07-01",
  "accounting_period": "2025-Q3"
}
```

**Response `201`:** Cession record with confirmation and updated treaty utilization.

---

## Webhook Events

| Event | Trigger | Payload Fields | Delivery SLA |
|---|---|---|---|
| `policy.bound` | Policy moves to BOUND status | `policy_id`, `policy_number`, `policyholder_id`, `broker_id`, `premium_amount`, `effective_date` | < 30 s |
| `policy.cancelled` | Policy cancellation effective | `policy_id`, `policy_number`, `cancellation_reason`, `cancellation_date`, `return_premium` | < 30 s |
| `policy.renewed` | Renewal policy issued | `old_policy_id`, `new_policy_id`, `policy_number`, `effective_date`, `premium_amount` | < 30 s |
| `policy.lapsed` | Non-payment lapse triggered | `policy_id`, `policy_number`, `last_paid_date`, `lapse_date` | < 30 s |
| `endorsement.applied` | Endorsement moves to APPLIED | `endorsement_id`, `policy_id`, `endorsement_type`, `premium_change`, `effective_date` | < 60 s |
| `claim.opened` | FNOL accepted and claim created | `claim_id`, `claim_number`, `policy_id`, `loss_type`, `fnol_date`, `initial_reserve` | < 30 s |
| `claim.reserve_changed` | Reserve amount updated | `claim_id`, `claim_number`, `previous_reserve`, `new_reserve`, `changed_by` | < 60 s |
| `claim.settled` | Claim moves to SETTLED status | `claim_id`, `claim_number`, `settlement_amount`, `paid_date`, `payment_reference` | < 30 s |
| `claim.fraud_flagged` | Fraud score exceeds SIU threshold | `claim_id`, `claim_number`, `fraud_score`, `triggered_rules[]` | < 15 s |
| `premium.invoice_created` | New invoice generated | `invoice_id`, `invoice_number`, `policy_id`, `amount_due`, `due_date` | < 60 s |
| `premium.payment_received` | Payment posted to invoice | `invoice_id`, `invoice_number`, `paid_amount`, `payment_method`, `payment_reference` | < 30 s |
| `premium.overdue` | Invoice not paid by due date | `invoice_id`, `invoice_number`, `policy_id`, `amount_due`, `days_overdue` | < 5 min |
| `underwriting.decision_issued` | UW decision available | `application_id`, `decision`, `risk_score`, `premium_indication`, `valid_until` | < 30 s |
| `reinsurance.cession_posted` | Cession record created | `cession_id`, `policy_id`, `treaty_id`, `ceded_premium`, `ceded_liability`, `accounting_period` | < 60 s |

### Webhook Delivery Contract

- **Endpoint registration:** `POST /api/v1/webhooks` with `url`, `events[]`, `secret` (HMAC-SHA256 signing key).
- **Signature header:** `X-IMS-Signature: sha256=<hex_digest>` computed over the raw request body.
- **Retry policy:** Exponential backoff — 30 s, 5 min, 30 min, 2 h, 24 h. Deactivates endpoint after 5 consecutive failures.
- **At-least-once delivery:** Consumers must be idempotent on `event_id`.
- **Payload envelope:**
```json
{
  "event_id": "evt_01HZ...",
  "event_type": "policy.bound",
  "api_version": "v1",
  "created_at": "2025-06-15T10:30:00Z",
  "data": { }
}
```
