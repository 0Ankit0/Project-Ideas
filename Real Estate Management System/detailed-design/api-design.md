# API Design — Real Estate Management System

## Overview

The Real Estate Management System exposes a versioned JSON REST API consumed by web and mobile clients, third-party integrations, and internal microservices. All endpoints live under the `/api/v1/` prefix. Future breaking changes will be published under `/api/v2/` without removing the v1 surface until a deprecation window closes.

### API Versioning

Versioning is path-based. The current stable version is `v1`. Clients must always specify the version segment:

```
https://api.rems.io/api/v1/<resource>
```

A response header `X-API-Version: 1` is always present. When a version is sunset, the API returns `410 Gone` with a `deprecation` field pointing to migration docs.

### Authentication

**JWT Bearer tokens** are issued by the `/api/v1/auth/token` endpoint upon successful credential verification. Tokens are RS256-signed, carry a 15-minute TTL, and are refreshed via `/api/v1/auth/refresh`. Every protected endpoint requires:

```
Authorization: Bearer <jwt>
```

The JWT payload carries:

```json
{
  "sub": "usr_01HXYZ",
  "tenantId": "ten_01HABC",
  "roles": ["landlord"],
  "scopes": ["properties:read", "properties:write", "leases:read"],
  "iat": 1715000000,
  "exp": 1715000900
}
```

**API keys** (format `rems_live_<32-char-hex>`) are used exclusively for server-to-server webhook verification and background integrations. They are passed via the `X-API-Key` header and do not carry role/scope claims — they authenticate to a specific integration profile configured per tenant.

### Rate Limiting

Rate limits are enforced per `tenantId` extracted from the JWT (or the integration profile for API-key calls). Limits are implemented with a sliding-window counter stored in Redis.

| Tier | Requests / minute | Burst |
|---|---|---|
| Free | 60 | 10 |
| Growth | 300 | 50 |
| Enterprise | 1 200 | 200 |

Rate limit state is communicated via response headers on every call:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 247
X-RateLimit-Reset: 1715001060
```

When the limit is breached the API returns `429 Too Many Requests` with a `Retry-After` header.

### Pagination

All list endpoints use **cursor-based pagination** to avoid the offset drift problem that arises when records are inserted or deleted between pages.

Query parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 25 | Max records per page (1–100) |
| `cursor` | string | — | Opaque cursor from previous `nextCursor` |
| `direction` | `asc` \| `desc` | `desc` | Sort direction on `createdAt` |

Response envelope:

```json
{
  "data": [],
  "pagination": {
    "limit": 25,
    "nextCursor": "eyJpZCI6InByb3BfMDFIWFlaIiwiY3JlYXRlZEF0IjoiMjAyNC0wNS0wMVQxMjowMDowMFoifQ==",
    "hasPreviousPage": true,
    "hasNextPage": true
  }
}
```

The cursor is a base64-encoded JSON object containing the last seen `id` and `createdAt`. Clients treat it as opaque.

### Standard Error Format

Every error response follows the same envelope regardless of status code:

```json
{
  "error": {
    "code": "PROPERTY_NOT_FOUND",
    "message": "No property found with id prop_01HXYZ for the current tenant.",
    "details": [],
    "traceId": "01HXYZ-TRACE",
    "timestamp": "2024-05-01T12:00:00Z"
  }
}
```

The `details` array is populated for validation errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request body failed validation.",
    "details": [
      { "field": "address.zip", "message": "Must match pattern ^[0-9]{5}(-[0-9]{4})?$" },
      { "field": "monthlyRent", "message": "Must be a positive number." }
    ],
    "traceId": "01HXYZ-TRACE",
    "timestamp": "2024-05-01T12:00:00Z"
  }
}
```

---

## Property Management

### GET /api/v1/properties

List properties visible to the authenticated user. Landlords see only their own properties; admins see all within the tenant.

**Required scope:** `properties:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `city` | string | Filter by city (case-insensitive contains) |
| `state` | string | Two-letter state code (e.g. `CA`) |
| `propertyType` | string | `single_family`, `multi_family`, `condo`, `townhouse`, `commercial` |
| `ownerId` | string | Filter by landlord user ID |
| `status` | string | `active`, `inactive`, `draft`, `archived` |
| `limit` | integer | Page size, default 25 |
| `cursor` | string | Pagination cursor |

**Response schema:**

```json
{
  "data": [
    {
      "id": "prop_01HXYZ",
      "tenantId": "ten_01HABC",
      "ownerId": "usr_01HXYZ",
      "name": "Sunset Apartments",
      "propertyType": "multi_family",
      "status": "active",
      "address": {
        "street1": "1234 Sunset Blvd",
        "street2": "Suite 100",
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90028",
        "country": "US",
        "coordinates": { "lat": 34.098, "lng": -118.327 }
      },
      "unitCount": 12,
      "occupiedUnits": 10,
      "yearBuilt": 1998,
      "totalSqFt": 14400,
      "amenities": ["pool", "gym", "parking"],
      "createdAt": "2024-01-15T08:00:00Z",
      "updatedAt": "2024-04-20T14:30:00Z"
    }
  ],
  "pagination": {
    "limit": 25,
    "nextCursor": "eyJpZCI6InByb3BfMDFIWFlaIiwiY3JlYXRlZEF0IjoiMjAyNC0wMS0xNVQwODowMDowMFoifQ==",
    "hasPreviousPage": false,
    "hasNextPage": true
  }
}
```

**Status codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/properties?city=Los%20Angeles&propertyType=multi_family&limit=10" \
  -H "Authorization: Bearer $JWT"
```

---

### POST /api/v1/properties

Create a new property record. Geocoding against Google Maps API is triggered asynchronously; the `coordinates` field may be null until the geocode job completes.

**Required scope:** `properties:write`

**Request body schema:**

```json
{
  "name": "Sunset Apartments",
  "propertyType": "multi_family",
  "address": {
    "street1": "1234 Sunset Blvd",
    "street2": "Suite 100",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90028",
    "country": "US"
  },
  "yearBuilt": 1998,
  "totalSqFt": 14400,
  "amenities": ["pool", "gym", "parking"],
  "description": "Modern apartment complex with ocean views.",
  "images": [
    { "url": "https://cdn.rems.io/prop_01/main.jpg", "isPrimary": true }
  ]
}
```

**Required fields:** `name`, `propertyType`, `address.street1`, `address.city`, `address.state`, `address.zip`

**Response schema:** Returns the created property object (same structure as list item) with `201 Created`.

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `409 Conflict` (duplicate address within tenant)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/properties" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sunset Apartments","propertyType":"multi_family","address":{"street1":"1234 Sunset Blvd","city":"Los Angeles","state":"CA","zip":"90028","country":"US"}}'
```

---

### GET /api/v1/properties/{id}

Retrieve a single property by its ID.

**Required scope:** `properties:read`

**Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Property ID (prefix `prop_`) |

**Response schema:** Same as individual list item. Includes the full `images` array and `description` field.

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/properties/prop_01HXYZ" \
  -H "Authorization: Bearer $JWT"
```

---

### PUT /api/v1/properties/{id}

Full replacement update of a property. All writable fields must be provided; omitted fields are set to null. Use `PATCH` semantics by including only changed fields — the server performs a merge against the stored document.

**Required scope:** `properties:write`

**Request body schema:** Same structure as `POST /api/v1/properties`.

**Response schema:** Updated property object.

**Status codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X PUT "https://api.rems.io/api/v1/properties/prop_01HXYZ" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sunset Apartments Updated","amenities":["pool","gym","parking","ev_charging"]}'
```

---

### DELETE /api/v1/properties/{id}

Soft-deletes a property by setting `status` to `archived`. Hard delete is blocked if any active leases or open maintenance requests reference the property.

**Required scope:** `properties:delete`

**Status codes:** `204 No Content`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (active leases exist)

**Example:**

```bash
curl -X DELETE "https://api.rems.io/api/v1/properties/prop_01HXYZ" \
  -H "Authorization: Bearer $JWT"
```

---

## Unit Management

### GET /api/v1/properties/{id}/units

List all units belonging to a property.

**Required scope:** `properties:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `available` | boolean | If `true`, return only units with no active lease |
| `bedrooms` | integer | Filter by bedroom count |
| `minRent` | number | Minimum monthly rent (USD) |
| `maxRent` | number | Maximum monthly rent (USD) |
| `floorNumber` | integer | Filter by floor |
| `limit` | integer | Page size |
| `cursor` | string | Pagination cursor |

**Response schema:**

```json
{
  "data": [
    {
      "id": "unit_01HABC",
      "propertyId": "prop_01HXYZ",
      "unitNumber": "101",
      "floorNumber": 1,
      "bedrooms": 2,
      "bathrooms": 1.5,
      "sqFt": 950,
      "monthlyRent": 2450.00,
      "depositAmount": 2450.00,
      "status": "vacant",
      "features": ["balcony", "washer_dryer", "hardwood_floors"],
      "activeLeaseId": null,
      "createdAt": "2024-01-15T08:00:00Z",
      "updatedAt": "2024-04-20T14:30:00Z"
    }
  ],
  "pagination": { "limit": 25, "nextCursor": null, "hasPreviousPage": false, "hasNextPage": false }
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (property)

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/properties/prop_01HXYZ/units?available=true&bedrooms=2" \
  -H "Authorization: Bearer $JWT"
```

---

### POST /api/v1/properties/{id}/units

Add a new unit to a property.

**Required scope:** `properties:write`

**Request body schema:**

```json
{
  "unitNumber": "202",
  "floorNumber": 2,
  "bedrooms": 1,
  "bathrooms": 1,
  "sqFt": 720,
  "monthlyRent": 1850.00,
  "depositAmount": 1850.00,
  "features": ["balcony", "hardwood_floors"],
  "petPolicy": {
    "allowed": true,
    "maxWeight": 50,
    "deposit": 500
  }
}
```

**Required fields:** `unitNumber`, `bedrooms`, `bathrooms`, `sqFt`, `monthlyRent`

**Response schema:** Created unit object.

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (property), `409 Conflict` (duplicate unit number within property)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/properties/prop_01HXYZ/units" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"unitNumber":"202","bedrooms":1,"bathrooms":1,"sqFt":720,"monthlyRent":1850.00}'
```

---

### GET /api/v1/properties/{id}/units/{unitId}

Retrieve a single unit.

**Required scope:** `properties:read`

**Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Property ID |
| `unitId` | string | Unit ID (prefix `unit_`) |

**Response schema:** Full unit object including `petPolicy`, `images`, and current `activeLeaseId`.

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/properties/prop_01HXYZ/units/unit_01HABC" \
  -H "Authorization: Bearer $JWT"
```

---

### PUT /api/v1/properties/{id}/units/{unitId}

Update a unit record. Rent changes do not retroactively affect active leases.

**Required scope:** `properties:write`

**Request body schema:** Same as `POST`, all fields optional.

**Response schema:** Updated unit object.

**Status codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X PUT "https://api.rems.io/api/v1/properties/prop_01HXYZ/units/unit_01HABC" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"monthlyRent":1950.00}'
```

---

## Lease Management

### POST /api/v1/leases

Create a new lease. Triggers DocuSign envelope creation for electronic signature. The lease remains in `pending_signature` status until both parties sign.

**Required scope:** `leases:write`

**Request body schema:**

```json
{
  "unitId": "unit_01HABC",
  "tenantIds": ["usr_tenant_01", "usr_tenant_02"],
  "startDate": "2024-06-01",
  "endDate": "2025-05-31",
  "monthlyRent": 2450.00,
  "securityDeposit": 2450.00,
  "petDeposit": 500.00,
  "lateFeePolicyId": "policy_01HDEF",
  "leaseTemplateId": "tmpl_01HGHI",
  "moveInInspectionScheduled": "2024-05-30T10:00:00Z",
  "notes": "Tenant requested June 1 move-in date.",
  "utilities": {
    "water": "landlord",
    "electricity": "tenant",
    "gas": "tenant",
    "trash": "landlord"
  }
}
```

**Required fields:** `unitId`, `tenantIds` (min 1), `startDate`, `endDate`, `monthlyRent`, `securityDeposit`

**Response schema:**

```json
{
  "id": "lease_01HJKL",
  "unitId": "unit_01HABC",
  "propertyId": "prop_01HXYZ",
  "tenantIds": ["usr_tenant_01", "usr_tenant_02"],
  "status": "pending_signature",
  "startDate": "2024-06-01",
  "endDate": "2025-05-31",
  "monthlyRent": 2450.00,
  "securityDeposit": 2450.00,
  "docuSignEnvelopeId": "ds_env_abc123",
  "signingUrl": "https://demo.docusign.net/Signing/...",
  "createdAt": "2024-05-01T12:00:00Z",
  "updatedAt": "2024-05-01T12:00:00Z"
}
```

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `409 Conflict` (unit already has active lease)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/leases" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"unitId":"unit_01HABC","tenantIds":["usr_tenant_01"],"startDate":"2024-06-01","endDate":"2025-05-31","monthlyRent":2450.00,"securityDeposit":2450.00}'
```

---

### GET /api/v1/leases/{id}

Retrieve a single lease with full detail.

**Required scope:** `leases:read`

**Response schema:**

```json
{
  "id": "lease_01HJKL",
  "unitId": "unit_01HABC",
  "propertyId": "prop_01HXYZ",
  "tenantIds": ["usr_tenant_01"],
  "status": "active",
  "startDate": "2024-06-01",
  "endDate": "2025-05-31",
  "monthlyRent": 2450.00,
  "securityDeposit": 2450.00,
  "petDeposit": 0,
  "utilities": { "water": "landlord", "electricity": "tenant", "gas": "tenant", "trash": "landlord" },
  "signedAt": "2024-05-02T09:15:00Z",
  "terminatedAt": null,
  "terminationReason": null,
  "renewalOfferedAt": null,
  "lateFeePolicy": {
    "gracePeriodDays": 5,
    "feeType": "percentage",
    "feeValue": 5,
    "maxFee": 200
  },
  "createdAt": "2024-05-01T12:00:00Z",
  "updatedAt": "2024-05-02T09:15:00Z"
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/leases/lease_01HJKL" \
  -H "Authorization: Bearer $JWT"
```

---

### PUT /api/v1/leases/{id}/terminate

Initiate lease termination. Validates that the provided `effectiveDate` satisfies the notice period defined in the lease. Sends termination notice via SendGrid/Twilio.

**Required scope:** `leases:write`

**Request body schema:**

```json
{
  "effectiveDate": "2024-08-31",
  "reason": "tenant_request",
  "noticePeriodDays": 30,
  "notes": "Tenant relocating for employment.",
  "securityDepositDisposition": "full_refund"
}
```

**Validation rules:**
- `effectiveDate` must be at least `noticePeriodDays` in the future from today
- `reason` must be one of: `tenant_request`, `landlord_termination`, `lease_violation`, `non_payment`, `mutual_agreement`
- `securityDepositDisposition` must be one of: `full_refund`, `partial_refund`, `forfeited`

**Response schema:**

```json
{
  "id": "lease_01HJKL",
  "status": "termination_pending",
  "terminationNoticeDate": "2024-05-15",
  "effectiveTerminationDate": "2024-08-31",
  "securityDepositDisposition": "full_refund",
  "noticesSent": ["email", "sms"]
}
```

**Status codes:** `200 OK`, `400 Bad Request` (notice period not met), `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (lease not in terminable state)

**Example:**

```bash
curl -X PUT "https://api.rems.io/api/v1/leases/lease_01HJKL/terminate" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"effectiveDate":"2024-08-31","reason":"tenant_request","noticePeriodDays":30}'
```

---

### GET /api/v1/leases/{id}/documents

List all documents attached to a lease (signed lease, addenda, notices).

**Required scope:** `leases:read`

**Response schema:**

```json
{
  "data": [
    {
      "id": "doc_01HMNP",
      "leaseId": "lease_01HJKL",
      "type": "signed_lease",
      "fileName": "lease_signed_2024-05-02.pdf",
      "mimeType": "application/pdf",
      "sizeBytes": 204800,
      "downloadUrl": "https://api.rems.io/api/v1/documents/doc_01HMNP/download",
      "uploadedAt": "2024-05-02T09:15:00Z",
      "expiresAt": "2024-05-02T10:15:00Z"
    }
  ]
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/leases/lease_01HJKL/documents" \
  -H "Authorization: Bearer $JWT"
```

---

## Tenant Management

### GET /api/v1/tenants

List tenants visible to the authenticated user.

**Required scope:** `tenants:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `search` | string | Full-text search on name and email |
| `propertyId` | string | Filter to tenants with a lease on the property |
| `status` | string | `active`, `former`, `applicant` |
| `limit` | integer | Page size |
| `cursor` | string | Pagination cursor |

**Response schema:**

```json
{
  "data": [
    {
      "id": "usr_tenant_01",
      "tenantId": "ten_01HABC",
      "firstName": "Jane",
      "lastName": "Doe",
      "email": "jane.doe@email.com",
      "phone": "+13105551234",
      "status": "active",
      "activeLeaseIds": ["lease_01HJKL"],
      "backgroundCheckStatus": "approved",
      "creditScore": 740,
      "createdAt": "2024-03-10T10:00:00Z",
      "updatedAt": "2024-04-01T08:00:00Z"
    }
  ],
  "pagination": { "limit": 25, "nextCursor": null, "hasPreviousPage": false, "hasNextPage": false }
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/tenants?status=active&propertyId=prop_01HXYZ" \
  -H "Authorization: Bearer $JWT"
```

---

### POST /api/v1/tenants

Create a tenant profile. Optionally triggers a background check via Checkr/TransUnion.

**Required scope:** `tenants:write`

**Request body schema:**

```json
{
  "firstName": "Jane",
  "lastName": "Doe",
  "email": "jane.doe@email.com",
  "phone": "+13105551234",
  "dateOfBirth": "1990-04-15",
  "ssn": "XXX-XX-XXXX",
  "governmentIdType": "drivers_license",
  "governmentIdNumber": "D1234567",
  "governmentIdState": "CA",
  "currentAddress": {
    "street1": "500 Main St",
    "city": "Santa Monica",
    "state": "CA",
    "zip": "90401"
  },
  "employmentInfo": {
    "employer": "Acme Corp",
    "position": "Engineer",
    "monthlyIncome": 8000,
    "employmentType": "full_time",
    "startDate": "2021-06-01"
  },
  "initiateBackgroundCheck": true,
  "emergencyContact": {
    "name": "John Doe",
    "relationship": "spouse",
    "phone": "+13105559876"
  }
}
```

**Required fields:** `firstName`, `lastName`, `email`, `phone`

**Response schema:** Created tenant object (SSN is never returned; only the last 4 digits as `ssnLast4`).

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `409 Conflict` (email already registered in tenant)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/tenants" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Jane","lastName":"Doe","email":"jane.doe@email.com","phone":"+13105551234"}'
```

---

### GET /api/v1/tenants/{id}

Retrieve a single tenant profile.

**Required scope:** `tenants:read`

**Response schema:** Full tenant object excluding PII fields (`ssn`, `dateOfBirth`). Include `ssnLast4` only for users with `tenants:pii` scope.

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/tenants/usr_tenant_01" \
  -H "Authorization: Bearer $JWT"
```

---

### GET /api/v1/tenants/{id}/applications

List rental applications submitted by this tenant.

**Required scope:** `tenants:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | `pending`, `approved`, `denied`, `withdrawn` |
| `limit` | integer | Page size |
| `cursor` | string | Pagination cursor |

**Response schema:**

```json
{
  "data": [
    {
      "id": "app_01HQRS",
      "tenantId": "usr_tenant_01",
      "unitId": "unit_01HABC",
      "propertyId": "prop_01HXYZ",
      "status": "approved",
      "submittedAt": "2024-04-20T11:00:00Z",
      "decidedAt": "2024-04-22T16:00:00Z",
      "backgroundCheckId": "chk_01HTUV",
      "backgroundCheckStatus": "approved"
    }
  ],
  "pagination": { "limit": 25, "nextCursor": null, "hasPreviousPage": false, "hasNextPage": false }
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/tenants/usr_tenant_01/applications?status=approved" \
  -H "Authorization: Bearer $JWT"
```

---

## Maintenance Management

### POST /api/v1/maintenance-requests

Submit a new maintenance request.

**Required scope:** `maintenance:write`

**Request body schema:**

```json
{
  "propertyId": "prop_01HXYZ",
  "unitId": "unit_01HABC",
  "requestedById": "usr_tenant_01",
  "category": "plumbing",
  "priority": "high",
  "title": "Kitchen sink leaking",
  "description": "Hot water pipe under kitchen sink has a steady drip. Causing water damage to cabinet.",
  "images": [
    { "url": "https://cdn.rems.io/maint/img1.jpg", "caption": "Under sink pipe" }
  ],
  "accessInstructions": "Key under mat. Dog friendly.",
  "preferredSchedule": [
    { "date": "2024-05-10", "startTime": "09:00", "endTime": "12:00" },
    { "date": "2024-05-11", "startTime": "14:00", "endTime": "17:00" }
  ]
}
```

**Required fields:** `propertyId`, `category`, `priority`, `title`, `description`

**Priority values:** `emergency`, `high`, `medium`, `low`

**Category values:** `plumbing`, `electrical`, `hvac`, `appliance`, `structural`, `pest_control`, `landscaping`, `other`

**Response schema:**

```json
{
  "id": "maint_01HWXY",
  "propertyId": "prop_01HXYZ",
  "unitId": "unit_01HABC",
  "status": "open",
  "priority": "high",
  "category": "plumbing",
  "title": "Kitchen sink leaking",
  "assignedVendorId": null,
  "estimatedCompletionDate": null,
  "createdAt": "2024-05-05T09:00:00Z",
  "updatedAt": "2024-05-05T09:00:00Z"
}
```

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (property/unit)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/maintenance-requests" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"propertyId":"prop_01HXYZ","unitId":"unit_01HABC","category":"plumbing","priority":"high","title":"Kitchen sink leaking","description":"Steady drip under sink."}'
```

---

### GET /api/v1/maintenance-requests

List maintenance requests with filters.

**Required scope:** `maintenance:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | `open`, `in_progress`, `awaiting_parts`, `completed`, `cancelled` |
| `priority` | string | `emergency`, `high`, `medium`, `low` |
| `propertyId` | string | Filter by property |
| `unitId` | string | Filter by unit |
| `assignedVendorId` | string | Filter by assigned vendor |
| `category` | string | Filter by maintenance category |
| `createdAfter` | ISO 8601 | Filter by creation date |
| `limit` | integer | Page size |
| `cursor` | string | Pagination cursor |

**Response schema:** List of maintenance request objects (same structure as POST response).

**Status codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/maintenance-requests?status=open&priority=emergency&propertyId=prop_01HXYZ" \
  -H "Authorization: Bearer $JWT"
```

---

### PUT /api/v1/maintenance-requests/{id}/status

Update the status of a maintenance request. Triggers notifications to the tenant via SendGrid/Twilio when status changes.

**Required scope:** `maintenance:write`

**Request body schema:**

```json
{
  "status": "in_progress",
  "assignedVendorId": "vendor_01HZAB",
  "scheduledDate": "2024-05-10T10:00:00Z",
  "estimatedCompletionDate": "2024-05-10T14:00:00Z",
  "notes": "Vendor confirmed appointment.",
  "internalNotes": "Vendor has correct access code.",
  "laborCostEstimate": 250.00,
  "partsCostEstimate": 75.00
}
```

**Valid status transitions:**
- `open` → `in_progress`, `cancelled`
- `in_progress` → `awaiting_parts`, `completed`, `cancelled`
- `awaiting_parts` → `in_progress`, `cancelled`
- `completed` → (terminal)
- `cancelled` → (terminal)

**Response schema:** Updated maintenance request object.

**Status codes:** `200 OK`, `400 Bad Request` (invalid transition), `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X PUT "https://api.rems.io/api/v1/maintenance-requests/maint_01HWXY/status" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","assignedVendorId":"vendor_01HZAB","scheduledDate":"2024-05-10T10:00:00Z"}'
```

---

### GET /api/v1/maintenance-requests/{id}/timeline

Retrieve the full audit timeline for a maintenance request.

**Required scope:** `maintenance:read`

**Response schema:**

```json
{
  "requestId": "maint_01HWXY",
  "timeline": [
    {
      "id": "tl_01HCDE",
      "eventType": "created",
      "actorId": "usr_tenant_01",
      "actorRole": "tenant",
      "timestamp": "2024-05-05T09:00:00Z",
      "metadata": { "priority": "high", "category": "plumbing" }
    },
    {
      "id": "tl_01HCDF",
      "eventType": "status_changed",
      "actorId": "usr_landlord_01",
      "actorRole": "landlord",
      "timestamp": "2024-05-06T10:30:00Z",
      "metadata": { "from": "open", "to": "in_progress", "assignedVendorId": "vendor_01HZAB" }
    }
  ]
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/maintenance-requests/maint_01HWXY/timeline" \
  -H "Authorization: Bearer $JWT"
```

---

## Payments

### POST /api/v1/payments

Record a payment or initiate a Stripe charge. If `paymentMethodId` is provided, the API creates a Stripe PaymentIntent. Manual (check, cash) payments are recorded directly.

**Required scope:** `payments:write`

**Request body schema:**

```json
{
  "leaseId": "lease_01HJKL",
  "amount": 2450.00,
  "currency": "USD",
  "type": "rent",
  "paymentMethod": "stripe",
  "paymentMethodId": "pm_stripe_abc123",
  "dueDate": "2024-06-01",
  "notes": "June rent",
  "metadata": {
    "invoiceId": "inv_01HFGH"
  }
}
```

**Payment types:** `rent`, `security_deposit`, `pet_deposit`, `late_fee`, `maintenance_reimbursement`, `other`

**Payment methods:** `stripe`, `ach`, `check`, `cash`, `money_order`

**Response schema:**

```json
{
  "id": "pay_01HIJK",
  "leaseId": "lease_01HJKL",
  "amount": 2450.00,
  "currency": "USD",
  "status": "processing",
  "type": "rent",
  "paymentMethod": "stripe",
  "stripePaymentIntentId": "pi_abc123",
  "paidAt": null,
  "dueDate": "2024-06-01",
  "createdAt": "2024-05-28T10:00:00Z"
}
```

**Status codes:** `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `402 Payment Required` (Stripe charge failed), `404 Not Found` (lease)

**Example:**

```bash
curl -X POST "https://api.rems.io/api/v1/payments" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"leaseId":"lease_01HJKL","amount":2450.00,"currency":"USD","type":"rent","paymentMethod":"stripe","paymentMethodId":"pm_stripe_abc123","dueDate":"2024-06-01"}'
```

---

### GET /api/v1/payments

List payments. Landlords see all payments on their properties; tenants see only their own.

**Required scope:** `payments:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `leaseId` | string | Filter by lease |
| `tenantId` | string | Filter by tenant |
| `propertyId` | string | Filter by property |
| `status` | string | `pending`, `processing`, `completed`, `failed`, `refunded` |
| `type` | string | Payment type filter |
| `from` | ISO 8601 date | Filter by `dueDate` range start |
| `to` | ISO 8601 date | Filter by `dueDate` range end |
| `limit` | integer | Page size |
| `cursor` | string | Pagination cursor |

**Response schema:** Paginated list of payment objects.

**Status codes:** `200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/payments?leaseId=lease_01HJKL&status=completed&from=2024-01-01&to=2024-05-31" \
  -H "Authorization: Bearer $JWT"
```

---

### GET /api/v1/payments/{id}/receipt

Generate and retrieve a payment receipt as a signed download URL pointing to a PDF stored in S3.

**Required scope:** `payments:read`

**Response schema:**

```json
{
  "paymentId": "pay_01HIJK",
  "receiptNumber": "REC-2024-001234",
  "downloadUrl": "https://cdn.rems.io/receipts/pay_01HIJK.pdf?X-Amz-Signature=...",
  "expiresAt": "2024-05-28T11:00:00Z",
  "generatedAt": "2024-05-28T10:05:00Z"
}
```

**Status codes:** `200 OK`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict` (payment not yet completed)

**Example:**

```bash
curl -X GET "https://api.rems.io/api/v1/payments/pay_01HIJK/receipt" \
  -H "Authorization: Bearer $JWT"
```

---

## Webhook Endpoints

Webhook events are delivered to endpoints registered per tenant under `/api/v1/webhooks/`. The server signs all outbound payloads with an HMAC-SHA256 signature in the `X-REMS-Signature-256` header. Inbound webhooks from third parties are routed to dedicated integration endpoints.

### POST /api/v1/webhooks/stripe

Handles Stripe webhook events: `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded`.

**Authentication:** `X-API-Key` header + Stripe signature verification via `stripe-signature` header.

**Request body:** Raw Stripe event object (do not parse before verifying signature).

**Event handling:**

```json
{
  "id": "evt_stripe_abc123",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_abc123",
      "amount": 245000,
      "currency": "usd",
      "metadata": { "paymentId": "pay_01HIJK", "leaseId": "lease_01HJKL" }
    }
  }
}
```

**Response:** Always return `200 OK` immediately; process asynchronously via job queue to avoid Stripe retry storms.

---

### POST /api/v1/webhooks/docusign

Handles DocuSign Connect webhook events: `envelope-completed`, `envelope-voided`, `recipient-declined`.

**Authentication:** `X-API-Key` + HMAC verification of the `X-DocuSign-Signature-1` header.

**Request body:**

```json
{
  "event": "envelope-completed",
  "envelopeId": "ds_env_abc123",
  "status": "completed",
  "completedDateTime": "2024-05-02T09:15:00Z",
  "recipients": [
    { "recipientId": "1", "email": "jane.doe@email.com", "status": "completed" }
  ]
}
```

**On `envelope-completed`:** Download signed document from DocuSign API, store in S3, update lease status to `active`, provision Stripe subscription for rent collection, notify tenant via SendGrid.

---

### POST /api/v1/webhooks/checkr

Handles Checkr background check webhooks: `report.completed`, `report.dispute.created`.

**Authentication:** `X-API-Key` + Checkr webhook signature.

**Request body:**

```json
{
  "type": "report.completed",
  "data": {
    "object": {
      "id": "chk_abc123",
      "status": "clear",
      "result": "clear",
      "candidateId": "cand_abc123"
    }
  }
}
```

**On `report.completed`:** Update tenant `backgroundCheckStatus`, notify property manager, update application status if pending.

---

## Authentication Flows

### JWT Issuance

```
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "landlord@example.com",
  "password": "s3cur3P@ss!"
}
```

**Response:**

```json
{
  "accessToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIs...",
  "expiresIn": 900,
  "tokenType": "Bearer"
}
```

Access tokens expire in 15 minutes. Refresh tokens expire in 30 days and are rotated on use (refresh token rotation).

### JWT Refresh

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJSUzI1NiIs..."
}
```

Returns a new `accessToken` and rotated `refreshToken`. The old refresh token is immediately invalidated.

### Token Revocation

```
POST /api/v1/auth/revoke
Authorization: Bearer <jwt>

{
  "refreshToken": "eyJhbGciOiJSUzI1NiIs..."
}
```

Adds the token's `jti` claim to a Redis deny-list with TTL matching the token's remaining validity.

---

## Field Validation Rules

| Field | Rule |
|---|---|
| `address.zip` | Pattern `^[0-9]{5}(-[0-9]{4})?$` |
| `address.state` | Two-letter ISO 3166-2 US state code |
| `address.country` | Two-letter ISO 3166-1 alpha-2 |
| `phone` | E.164 format `+1XXXXXXXXXX` |
| `email` | RFC 5322 compliant, max 254 chars |
| `monthlyRent` | Positive decimal, max 2 decimal places, max 99999.99 |
| `securityDeposit` | Non-negative decimal, max 2 decimal places |
| `dateOfBirth` | ISO 8601 date, must be 18+ years before today |
| `startDate` / `endDate` | ISO 8601 date; `endDate` must be after `startDate` |
| `bedrooms` | Integer 0–20 (0 = studio) |
| `bathrooms` | Decimal, increments of 0.5, range 1–10 |
| `sqFt` | Integer 100–100000 |
| `yearBuilt` | Integer 1800–(current year) |
| `noticePeriodDays` | Integer 1–365 |
| `priority` | Enum: `emergency`, `high`, `medium`, `low` |
| `currency` | ISO 4217, currently only `USD` supported |
| `limit` (pagination) | Integer 1–100 |
| `leaseTemplateId` | Must reference an existing template within tenant |

All string fields are trimmed of leading/trailing whitespace before validation. Empty strings are treated as null/absent. Input exceeding 10 000 characters for `description`/`notes` fields is rejected with `400 VALIDATION_ERROR`.

---

## Common Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `VALIDATION_ERROR` | 400 | One or more request fields failed validation |
| `INVALID_JSON` | 400 | Request body is not valid JSON |
| `MISSING_REQUIRED_FIELD` | 400 | A required field is absent |
| `INVALID_ENUM_VALUE` | 400 | Field value not in allowed set |
| `INVALID_DATE_FORMAT` | 400 | Date field is not ISO 8601 |
| `DATE_RANGE_INVALID` | 400 | End date before start date |
| `NOTICE_PERIOD_NOT_MET` | 400 | Termination date violates notice period |
| `INVALID_STATUS_TRANSITION` | 400 | Status change is not allowed |
| `PAGINATION_CURSOR_INVALID` | 400 | Cursor is malformed or expired |
| `PHONE_FORMAT_INVALID` | 400 | Phone number not in E.164 format |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT/API key |
| `TOKEN_EXPIRED` | 401 | JWT access token has expired |
| `REFRESH_TOKEN_INVALID` | 401 | Refresh token is expired or revoked |
| `INSUFFICIENT_SCOPE` | 403 | JWT lacks required scope for this operation |
| `FORBIDDEN` | 403 | Authenticated user cannot access this resource |
| `TENANT_MISMATCH` | 403 | Resource belongs to a different tenant |
| `PROPERTY_NOT_FOUND` | 404 | Property with given ID does not exist |
| `UNIT_NOT_FOUND` | 404 | Unit with given ID does not exist |
| `LEASE_NOT_FOUND` | 404 | Lease with given ID does not exist |
| `TENANT_NOT_FOUND` | 404 | Tenant with given ID does not exist |
| `PAYMENT_NOT_FOUND` | 404 | Payment with given ID does not exist |
| `MAINTENANCE_REQUEST_NOT_FOUND` | 404 | Maintenance request does not exist |
| `DOCUMENT_NOT_FOUND` | 404 | Document with given ID does not exist |
| `APPLICATION_NOT_FOUND` | 404 | Application with given ID does not exist |
| `RESOURCE_GONE` | 410 | API version has been sunset |
| `DUPLICATE_ADDRESS` | 409 | Property with same address exists in tenant |
| `DUPLICATE_UNIT_NUMBER` | 409 | Unit number already exists in this property |
| `DUPLICATE_EMAIL` | 409 | Email address already registered in tenant |
| `UNIT_ALREADY_LEASED` | 409 | Unit has an active lease |
| `LEASE_NOT_TERMINABLE` | 409 | Lease status does not permit termination |
| `PAYMENT_NOT_COMPLETED` | 409 | Receipt can only be generated for completed payments |
| `ACTIVE_LEASES_EXIST` | 409 | Property cannot be archived with active leases |
| `RATE_LIMIT_EXCEEDED` | 429 | Per-tenant rate limit exceeded |
| `STRIPE_CHARGE_FAILED` | 402 | Stripe PaymentIntent creation failed |
| `INTEGRATION_UNAVAILABLE` | 503 | Downstream service (DocuSign, Checkr, etc.) is unavailable |
| `BACKGROUND_CHECK_FAILED` | 422 | Background check could not be initiated |
| `GEOCODING_FAILED` | 422 | Address could not be geocoded |
| `DOCUMENT_GENERATION_FAILED` | 422 | PDF generation or signing failed |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error; includes `traceId` for support |
| `SEARCH_UNAVAILABLE` | 503 | Elasticsearch cluster is temporarily unavailable |
| `WEBHOOK_SIGNATURE_INVALID` | 401 | Webhook HMAC signature verification failed |
