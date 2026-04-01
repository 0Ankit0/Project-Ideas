# REST API Design — Library Management System

## API Overview

| Property         | Value                                          |
|------------------|------------------------------------------------|
| Base URL         | `https://api.library.example.com/v1`           |
| Protocol         | HTTPS only (TLS 1.2+)                          |
| Authentication   | JWT Bearer token (`Authorization: Bearer <token>`) |
| Content-Type     | `application/json` (requests and responses)    |
| API Version      | URI path versioning (`/v1`). Breaking changes bump to `/v2`. |
| Idempotency      | `Idempotency-Key` header required on `POST /loans`, `POST /reservations`, `POST /fines/{id}/pay` |
| Rate Limiting    | 1 000 req/min per member token; 10 000 req/min per staff token |
| Compression      | `Accept-Encoding: gzip` supported on all GET responses |

### Versioning Strategy

Non-breaking changes (new optional fields, new endpoints) are deployed without version increment and announced in the changelog. Breaking changes (field removals, changed semantics) are released under a new URI version. Each version is supported for a minimum of 12 months after the successor is published. The `Deprecation` and `Sunset` response headers are set on deprecated endpoints.

### Role Hierarchy

| Role      | Scope                                                       |
|-----------|-------------------------------------------------------------|
| `member`  | Own account, own loans, own reservations, own fines         |
| `staff`   | All member data within their branch; checkout / return      |
| `manager` | All branch data; acquisition approval; fine waiver          |
| `admin`   | System-wide; membership tier management; reports            |

---

## Standard Response Envelope

### Success (single resource)

```json
{
  "data": { },
  "meta": { "traceId": "7f3a1b9c-e402-4d8e-b5f1-2c9d0e6a4f31" }
}
```

### Success (collection)

```json
{
  "data": [ ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 243,
    "totalPages": 13
  },
  "meta": { "traceId": "7f3a1b9c-e402-4d8e-b5f1-2c9d0e6a4f31" }
}
```

### Error Response

```json
{
  "error": {
    "code": "FINE_BLOCK_ACTIVE",
    "message": "Member has outstanding fines exceeding the borrowing block threshold",
    "details": {
      "outstandingAmount": 27.50,
      "threshold": 25.00
    },
    "traceId": "abc123def456"
  }
}
```

---

## Pagination

### Offset-based (default for collections)

Query params: `page` (default `1`), `pageSize` (default `20`, max `100`).

### Cursor-based (event feeds and audit logs)

Query params: `cursor` (opaque string from previous response), `limit` (default `50`, max `200`).
Response includes `"nextCursor": "<string>"` when more results exist.

---

## Endpoint Reference

### Catalog — `/catalog`

#### `GET /catalog/items`

Search and filter the catalog.

**Query Parameters**

| Param        | Type    | Description                                          |
|--------------|---------|------------------------------------------------------|
| `q`          | string  | Full-text search across title, subtitle, and authors |
| `isbn`       | string  | Exact ISBN-10 or ISBN-13 match                       |
| `author`     | string  | Partial author name match                            |
| `format`     | string  | `book`, `ebook`, `audiobook`, `dvd`, `periodical`    |
| `language`   | string  | BCP 47 language code (e.g. `en`, `fr`)               |
| `branchId`   | UUID    | Filter availability to a specific branch             |
| `available`  | boolean | `true` returns only items with available copies      |
| `deweyClass` | string  | Dewey decimal prefix (e.g. `510`, `510.5`)           |
| `page`       | integer | Page number (default `1`)                            |
| `pageSize`   | integer | Results per page (default `20`, max `100`)           |

**Response `200 OK`**

```json
{
  "data": [
    {
      "catalogItemId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "isbn": "9780131103627",
      "title": "The C Programming Language",
      "subtitle": "Second Edition",
      "format": "book",
      "language": "en",
      "publicationYear": 1988,
      "coverImageUrl": "https://covers.library.example.com/9780131103627.jpg",
      "authors": [
        { "authorId": "a1b2c3d4-...", "name": "Brian W. Kernighan", "role": "author" },
        { "authorId": "e5f6a7b8-...", "name": "Dennis M. Ritchie",  "role": "author" }
      ],
      "publisher": { "publisherId": "...", "name": "Prentice Hall" },
      "deweyClassification": { "number": "005.133", "description": "Specific programming languages" },
      "availability": {
        "totalCopies": 4,
        "availableCopies": 2,
        "branchAvailability": [
          { "branchId": "...", "branchName": "Central Branch", "available": 1, "total": 2 }
        ]
      }
    }
  ],
  "pagination": { "page": 1, "pageSize": 20, "totalItems": 1, "totalPages": 1 },
  "meta": { "traceId": "7f3a1b9c" }
}
```

#### `GET /catalog/items/{catalogItemId}`

Returns full catalog item details including all copies.
**Auth:** Public (no token required for availability data).

#### `POST /catalog/items`

Create a new catalog item. **Auth:** `staff`, `manager`, `admin`.

**Request Body**

```json
{
  "isbn": "9780131103627",
  "title": "The C Programming Language",
  "subtitle": "Second Edition",
  "publisherId": "uuid",
  "deweyId": "uuid",
  "format": "book",
  "language": "en",
  "publicationYear": 1988,
  "description": "The authoritative reference manual for the C language.",
  "coverImageUrl": "https://covers.library.example.com/9780131103627.jpg",
  "authorIds": [
    { "authorId": "uuid", "role": "author", "displayOrder": 1 }
  ]
}
```

**Response:** `201 Created` with created catalog item.

#### `PUT /catalog/items/{catalogItemId}`

Replace catalog item metadata. **Auth:** `staff`, `manager`, `admin`.

#### `DELETE /catalog/items/{catalogItemId}`

Logically withdraw a catalog item. Fails with `409 Conflict` if active loans or reservations exist.
**Auth:** `manager`, `admin`.

#### `POST /catalog/items/import/isbn`

Look up an ISBN from OpenLibrary and Google Books APIs and create the catalog record.
**Auth:** `staff`, `manager`, `admin`.

**Request Body**

```json
{ "isbn": "9780131103627", "deweyId": "uuid" }
```

#### `POST /catalog/items/import/bulk`

Bulk CSV import. Multipart form upload: `file` field contains the CSV.
Returns a `202 Accepted` with a `jobId` to poll for import status.
**Auth:** `manager`, `admin`.

---

### Copies — `/copies`

#### `GET /copies`

List physical copies with filters.

| Param           | Type    | Description                           |
|-----------------|---------|---------------------------------------|
| `catalogItemId` | UUID    | Filter by catalog item                |
| `branchId`      | UUID    | Filter by branch                      |
| `status`        | string  | `available`, `checked_out`, etc.      |
| `barcode`       | string  | Exact barcode lookup                  |

#### `GET /copies/{copyId}` — get copy details including current loan.

#### `POST /copies`

Add a new physical copy to a branch. **Auth:** `staff`, `manager`, `admin`.

```json
{
  "catalogItemId": "uuid",
  "branchId": "uuid",
  "barcode": "LIB-000123456",
  "rfidTag": "RFID-ABC-001",
  "shelfLocation": "005.133 KER",
  "condition": "new",
  "acquisitionDate": "2024-03-15",
  "replacementCost": 49.99
}
```

#### `PUT /copies/{copyId}/status`

Update copy status (e.g. mark as `lost`, `damaged`, `in_repair`). **Auth:** `staff`, `manager`.

```json
{ "status": "lost", "reason": "Not found during annual audit" }
```

#### `DELETE /copies/{copyId}`

Withdraw a copy. Fails with `409 Conflict` if copy is currently on loan.
**Auth:** `manager`, `admin`.

---

### Members — `/members`

#### `GET /members`

Paginated member list. **Auth:** `staff`, `manager`, `admin`.

| Param      | Type   | Description                              |
|------------|--------|------------------------------------------|
| `q`        | string | Search by name or email                  |
| `status`   | string | `active`, `suspended`, `expired`         |
| `tierId`   | UUID   | Filter by membership tier                |
| `branchId` | UUID   | Filter by home branch                    |

#### `GET /members/{memberId}` — member profile. **Auth:** Own account or `staff+`.

#### `POST /members`

Register a new member. **Auth:** `staff`, `manager`, `admin`.

```json
{
  "libraryId": "uuid",
  "email": "jane.doe@example.com",
  "firstName": "Jane",
  "lastName": "Doe",
  "phone": "+1-555-0100",
  "address": "42 Maple Street, Springfield, IL 62701",
  "tierId": "uuid",
  "expiresAt": "2025-12-31"
}
```

**Response:** `201 Created` with member record.

#### `PUT /members/{memberId}` — update member details. **Auth:** Own account (limited fields) or `staff+`.

#### `GET /members/{memberId}/loans`

Returns the member's loan history.

| Param    | Type   | Description                                  |
|----------|--------|----------------------------------------------|
| `status` | string | `active`, `returned`, `overdue`              |
| `page`   | int    | Page number                                  |

#### `GET /members/{memberId}/reservations` — member's reservations.

#### `GET /members/{memberId}/fines` — member's fines including outstanding total.

---

### Loans — `/loans`

#### `POST /loans`

Check out a physical item. **Auth:** `staff`, `manager`.

**Request Body**

```json
{
  "memberId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "copyId":   "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "staffId":  "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response `201 Created`**

```json
{
  "data": {
    "loanId":      "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "memberId":    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "copyId":      "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "checkoutAt":  "2024-06-01T09:15:00Z",
    "dueAt":       "2024-06-22T23:59:59Z",
    "renewalCount": 0,
    "status":      "active",
    "item": {
      "title":   "The C Programming Language",
      "barcode": "LIB-000123456",
      "branch":  "Central Branch"
    }
  },
  "meta": { "traceId": "abc123" }
}
```

**Error Responses**

| Condition                        | HTTP | Error Code              |
|----------------------------------|------|-------------------------|
| Member not found                 | 404  | `MEMBER_NOT_FOUND`      |
| Member suspended                 | 422  | `MEMBER_SUSPENDED`      |
| Outstanding fines exceed block   | 422  | `FINE_BLOCK_ACTIVE`     |
| Concurrent loan limit reached    | 422  | `LOAN_LIMIT_EXCEEDED`   |
| Copy not available               | 409  | `COPY_NOT_AVAILABLE`    |

#### `GET /loans/{loanId}` — loan details including item and member summary.

#### `PUT /loans/{loanId}/return`

Return a physical item. **Auth:** `staff`, `manager`.

```json
{ "staffId": "uuid", "condition": "good" }
```

Triggers: fine assessment if overdue, reservation queue advancement, copy status reset.

#### `PUT /loans/{loanId}/renew`

Renew an active loan. **Auth:** Own member token or `staff+`.

```json
{ "requestedBy": "member" }
```

Fails with `422` if `renewal_count` has reached the tier's `renewal_limit` or if the item has an active reservation.

#### `GET /loans`

List loans with filters. **Auth:** `staff+`.

| Param      | Type    | Description                              |
|------------|---------|------------------------------------------|
| `memberId` | UUID    | Filter by member                         |
| `status`   | string  | `active`, `returned`, `overdue`, `lost`  |
| `branchId` | UUID    | Filter by checkout branch                |
| `overdue`  | boolean | `true` returns only overdue loans        |
| `dueBefore`| date    | Return loans due before this date        |

---

### Reservations — `/reservations`

#### `POST /reservations`

Place a reservation (hold) on a catalog item. **Auth:** Own member token or `staff+`.

**Request Body**

```json
{
  "memberId":      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "catalogItemId": "a3bb189e-8bf9-3888-9912-ace4e6543002",
  "branchId":      "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

**Response `201 Created`**

```json
{
  "data": {
    "reservationId":  "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "memberId":       "3fa85f64-...",
    "catalogItemId":  "a3bb189e-...",
    "branchId":       "7c9e6679-...",
    "status":         "pending",
    "queuePosition":  3,
    "estimatedReadyDate": "2024-06-14",
    "createdAt":      "2024-06-01T10:00:00Z"
  },
  "meta": { "traceId": "xyz789" }
}
```

#### `GET /reservations/{reservationId}` — reservation details including queue position.

#### `DELETE /reservations/{reservationId}`

Cancel a reservation. **Auth:** Own member token or `staff+`.

#### `PUT /reservations/{reservationId}/fulfill`

Mark reservation as fulfilled when member collects the item. **Auth:** `staff+`.

```json
{ "loanId": "uuid" }
```

#### `GET /reservations`

List reservations. **Auth:** `staff+`.

| Param           | Type   | Description                                 |
|-----------------|--------|---------------------------------------------|
| `memberId`      | UUID   | Filter by member                            |
| `catalogItemId` | UUID   | Filter by item                              |
| `status`        | string | `pending`, `ready`, `fulfilled`, `cancelled` |
| `branchId`      | UUID   | Filter by pickup branch                     |

---

### Fines — `/fines`

#### `GET /fines`

List fines. **Auth:** `staff+`. Members use `GET /members/{memberId}/fines`.

| Param      | Type   | Description                            |
|------------|--------|----------------------------------------|
| `memberId` | UUID   | Filter by member                       |
| `status`   | string | `outstanding`, `paid`, `waived`        |
| `type`     | string | `overdue`, `lost_item`, `damaged_item` |

#### `GET /fines/{fineId}` — fine details.

#### `POST /fines/{fineId}/pay`

Record a payment against a fine. **Auth:** `staff+`.

```json
{
  "amount":        15.00,
  "paymentMethod": "cash",
  "reference":     "RCP-20240601-0042"
}
```

Returns updated fine with remaining balance. Fine status transitions to `paid` when `amount` fully clears outstanding balance.

#### `POST /fines/{fineId}/waive`

Waive a fine. **Auth:** `manager`, `admin`.

```json
{
  "staffId": "uuid",
  "reason":  "First-time offence waiver — borrower's explanation accepted"
}
```

---

### Digital Lending — `/digital-lending`

#### `GET /digital-lending/resources`

List digital resources with availability.

| Param           | Type    | Description                              |
|-----------------|---------|------------------------------------------|
| `catalogItemId` | UUID    | Filter by catalog item                   |
| `format`        | string  | `epub`, `pdf`, `mp3`, `mp4`              |
| `available`     | boolean | `true` returns only items with licenses  |

#### `POST /digital-lending/borrow`

Borrow a digital resource. Issues a DRM token via the configured provider.
**Auth:** Own member token or `staff+`.

**Request Body**

```json
{
  "memberId":   "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "resourceId": "c56a4180-65aa-42ec-a945-5fd21dec0538"
}
```

**Response `201 Created`**

```json
{
  "data": {
    "digitalLoanId":   "e58ed763-928d-4307-b5bb-1a8e4df7c567",
    "memberId":        "3fa85f64-...",
    "resourceId":      "c56a4180-...",
    "drmToken":        "eyJhbGciOiJSUzI1NiJ9...",
    "tokenExpiresAt":  "2024-06-22T23:59:59Z",
    "checkedOutAt":    "2024-06-01T11:00:00Z",
    "status":          "active",
    "downloadUrl":     "https://drm.provider.example.com/download?token=eyJhbGci..."
  },
  "meta": { "traceId": "drm-borrow-001" }
}
```

**Error Responses**

| Condition                          | HTTP | Error Code                      |
|------------------------------------|------|---------------------------------|
| Digital loan limit exceeded        | 422  | `DIGITAL_LOAN_LIMIT_EXCEEDED`   |
| No licenses available              | 409  | `COPY_NOT_AVAILABLE`            |
| DRM provider returned error        | 502  | `DRM_TOKEN_FAILURE`             |
| Content provider unreachable       | 503  | `CONTENT_PROVIDER_UNAVAILABLE`  |

#### `PUT /digital-lending/{digitalLoanId}/return`

Return a digital loan early, revoking the DRM token. **Auth:** Own member token or `staff+`.

#### `GET /digital-lending/active`

Returns all active digital loans for the authenticated member.
**Auth:** Own member token or `staff+` (staff can pass `memberId` query param).

---

### Acquisitions — `/acquisitions`

#### `POST /acquisitions`

Submit an acquisition request. **Auth:** `staff`, `manager`, `admin`.

```json
{
  "catalogItemId": "uuid",
  "vendorId":      "uuid",
  "branchId":      "uuid",
  "quantity":      3,
  "unitCost":      29.99,
  "notes":         "High patron demand — 6 active hold requests"
}
```

**Response `201 Created`** — acquisition record with `status: "requested"`.

#### `GET /acquisitions/{acquisitionId}` — acquisition details.

#### `PUT /acquisitions/{acquisitionId}/approve`

Approve a pending acquisition request. **Auth:** `manager`, `admin`.

```json
{ "approverId": "uuid", "notes": "Budget line Q3-2024-BOOKS approved" }
```

#### `PUT /acquisitions/{acquisitionId}/receive`

Record receipt of delivered copies. Creates `book_copies` records for each received unit.
**Auth:** `staff+`.

```json
{
  "receivedQuantity": 3,
  "receivedAt":       "2024-06-05T14:30:00Z",
  "copies": [
    { "barcode": "LIB-000123457", "condition": "new", "shelfLocation": "005.133 KER" },
    { "barcode": "LIB-000123458", "condition": "new", "shelfLocation": "005.133 KER" },
    { "barcode": "LIB-000123459", "condition": "new", "shelfLocation": "005.133 KER" }
  ]
}
```

#### `DELETE /acquisitions/{acquisitionId}`

Cancel an acquisition. Only permitted while `status` is `requested` or `approved`.
**Auth:** `manager`, `admin`.

#### `GET /acquisitions`

List acquisitions. **Auth:** `staff+`.

| Param           | Type   | Description                                           |
|-----------------|--------|-------------------------------------------------------|
| `status`        | string | `requested`, `approved`, `ordered`, `received`        |
| `vendorId`      | UUID   | Filter by vendor                                      |
| `branchId`      | UUID   | Filter by destination branch                          |
| `catalogItemId` | UUID   | Filter by catalog item                                |

---

### Reports — `/reports`

All report endpoints require `manager` or `admin` role. Reports accept `startDate` and `endDate`
query params (ISO 8601 dates) and `branchId` for branch-scoped views.

| Endpoint                        | Description                                                         |
|---------------------------------|---------------------------------------------------------------------|
| `GET /reports/circulation`      | Checkouts, returns, renewals, and overdue counts per branch/period  |
| `GET /reports/overdue`          | List of currently overdue loans with member and item details        |
| `GET /reports/fines`            | Fine totals assessed, collected, and waived per branch/period       |
| `GET /reports/acquisitions`     | Spend vs. budget by branch, vendor, and category                    |
| `GET /reports/popular-items`    | Most borrowed items ranked by checkout frequency                    |
| `GET /reports/member-activity`  | Member borrowing patterns, active vs. lapsed member counts          |

All report endpoints support `Accept: text/csv` for CSV export alongside the default JSON response.

---

## Error Codes Reference

| Code                             | HTTP | Description                                                       | Resolution                                              |
|----------------------------------|------|-------------------------------------------------------------------|---------------------------------------------------------|
| `MEMBER_NOT_FOUND`               | 404  | No member with the supplied ID exists                            | Verify `memberId` and retry                             |
| `MEMBER_SUSPENDED`               | 422  | Member account is suspended and cannot borrow                    | Resolve suspension in member management                 |
| `MEMBER_EXPIRED`                 | 422  | Membership has expired                                           | Renew membership before borrowing                       |
| `FINE_BLOCK_ACTIVE`              | 422  | Outstanding fines exceed the tier's block threshold              | Pay fines below threshold to restore borrowing rights   |
| `LOAN_LIMIT_EXCEEDED`            | 422  | Member has reached the concurrent loan limit for their tier      | Return an item or upgrade membership tier               |
| `COPY_NOT_FOUND`                 | 404  | No copy with the supplied `copyId` or `barcode` exists           | Verify barcode/ID and retry                             |
| `COPY_NOT_AVAILABLE`             | 409  | Copy exists but is not in `available` status                     | Place a reservation or choose another copy              |
| `ITEM_NOT_FOUND`                 | 404  | No catalog item with the supplied ID exists                      | Verify `catalogItemId` and retry                        |
| `LOAN_NOT_FOUND`                 | 404  | No loan with the supplied ID exists                              | Verify `loanId` and retry                               |
| `LOAN_ALREADY_RETURNED`          | 409  | The loan has already been closed                                 | No action required                                      |
| `RENEWAL_LIMIT_EXCEEDED`         | 422  | Loan has been renewed the maximum number of times                | Member must return and re-borrow the item               |
| `ITEM_HAS_RESERVATION`           | 422  | Renewal blocked because another member has reserved this item    | Return item so it can fulfil the waiting reservation    |
| `RESERVATION_NOT_FOUND`          | 404  | No reservation with the supplied ID exists                       | Verify `reservationId` and retry                        |
| `RESERVATION_EXPIRED`            | 409  | Reservation pickup window has passed and the hold was cancelled  | Place a new reservation                                 |
| `RESERVATION_ALREADY_FULFILLED`  | 409  | Reservation has already been converted to a loan                 | No action required                                      |
| `FINE_NOT_FOUND`                 | 404  | No fine with the supplied ID exists                              | Verify `fineId` and retry                               |
| `FINE_ALREADY_PAID`              | 409  | Fine has already been fully settled                              | No action required                                      |
| `INSUFFICIENT_PAYMENT`           | 422  | Payment amount is less than the outstanding balance              | Submit the correct amount or pay in full                |
| `DIGITAL_LOAN_LIMIT_EXCEEDED`    | 422  | Member has reached the concurrent digital loan limit             | Return a digital item or upgrade membership tier        |
| `DRM_TOKEN_FAILURE`              | 502  | The DRM provider returned an error when issuing the token        | Retry; if persistent, contact the DRM provider          |
| `CONTENT_PROVIDER_UNAVAILABLE`   | 503  | The digital content provider is temporarily unreachable          | Retry after a short delay                               |
| `ACQUISITION_APPROVAL_REQUIRED`  | 422  | Acquisition cannot proceed without manager approval              | Submit for approval via `PUT /acquisitions/{id}/approve`|
| `BUDGET_EXCEEDED`                | 422  | Acquisition cost exceeds remaining branch budget                 | Obtain budget exception or reduce order quantity        |
| `UNAUTHORIZED`                   | 401  | Missing or invalid Bearer token                                  | Re-authenticate and include a valid token               |
| `FORBIDDEN`                      | 403  | Token is valid but role is insufficient for this action          | Use an account with the required role                   |
| `VALIDATION_ERROR`               | 400  | Request body failed schema validation                            | See `details` field for field-level errors              |
| `INTERNAL_ERROR`                 | 500  | Unexpected server error                                          | Retry; report `traceId` if the issue persists           |
