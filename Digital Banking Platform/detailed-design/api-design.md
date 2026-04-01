| Field | Value |
| --- | --- |
| Document ID | DBP-DD-038 |
| Version | 1.0 |
| Status | Approved |
| Owner | Architecture Team |
| Last Updated | 2025-01-15 |
| Classification | Internal — Restricted |

# REST API Design Reference — Digital Banking Platform

## Overview

The Digital Banking Platform exposes all customer-facing and integration capabilities through a unified REST API, versioned at `/v1/`, designed in strict accordance with OpenAPI 3.0.3. API design follows the JSON:API-inspired error envelope format for all error responses, cursor-based pagination for all list endpoints, and mandatory idempotency keys for all mutating operations. This document serves as the authoritative design reference for API consumers, front-end teams, and integration partners.

Every endpoint requires a valid JWT Bearer token issued by the platform's OAuth 2.0 authorisation server. Tokens are RS256-signed with a 15-minute expiry. The token payload carries `customer_id`, `scopes`, and a `device_fingerprint` claim verified against the session. Privileged operations additionally require a step-up authentication challenge verified by the FIDO2 authenticator registered to the customer's device.

Rate limiting is enforced at the API Gateway layer using a sliding window algorithm. Each customer is allocated a per-endpoint rate budget. Requests that exceed the budget receive HTTP 429 with a `Retry-After` header. All limits are documented per endpoint in this reference.

## Authentication and Authorisation

The platform implements OAuth 2.0 with JWT Bearer tokens. Tokens are issued by the platform's internal authorisation server, signed with RS256 using a 4096-bit key pair rotated every 90 days. Refresh tokens are delivered via `HttpOnly`, `Secure`, `SameSite=Strict` cookies with a 7-day rolling expiry. The following scopes control access across endpoint categories.

| Endpoint Category | Required Scope | Additional MFA Required | Notes |
| --- | --- | --- | --- |
| Account reads | `banking:read` | No | Covers balance, transaction history, statement |
| Account mutations | `banking:write` | FIDO2 step-up for amounts > £5,000 | Covers transfers, account opening |
| Card management | `banking:write` | PIN re-entry required for card number reveal | Card issuance, block, limits |
| Loan applications | `banking:write` | No | Application submission only |
| KYC verification | `banking:write` | No | Triggered by onboarding flow |
| Compliance access | `banking:compliance` | Supervisor sign-off for override | Staff-only scope; not issuable to customers |
| Admin operations | `banking:admin` | Hardware token MFA required | Internal tooling only; never exposed externally |

## Error Response Format

All error responses use a consistent JSON envelope regardless of HTTP status code. The envelope is designed to be machine-parseable by API clients without string-matching on the `message` field, which is intended for developer debugging only and must not be displayed to end users.

```json
{
  "error": {
    "code": "DAILY_LIMIT_EXCEEDED",
    "message": "The requested transfer amount of £3,500.00 exceeds the remaining daily limit of £1,200.00 for account acc_7f3a2b.",
    "details": [
      {
        "field": "amount",
        "issue": "Transfer amount 3500.00 exceeds available daily limit 1200.00",
        "code": "DAILY_LIMIT_EXCEEDED"
      }
    ],
    "traceId": "4b3f2a1c-9d8e-4f7a-b6c5-3d2e1f0a9b8c",
    "timestamp": "2025-01-15T14:32:07.483Z"
  }
}
```

| Error Code | HTTP Status | Trigger Condition | Retryable |
| --- | --- | --- | --- |
| `VALIDATION_ERROR` | 400 | Request body fails JSON Schema validation | No — fix request |
| `INSUFFICIENT_FUNDS` | 422 | Available balance < requested amount after hold | No — fund account first |
| `DAILY_LIMIT_EXCEEDED` | 422 | Transfer would exceed customer `daily_transfer_limit` | No — wait for reset or update limit |
| `KYC_REQUIRED` | 403 | Customer KYC status is not `passed` | No — complete KYC flow |
| `FRAUD_SUSPECTED` | 422 | Fraud score >= 0.75; transaction placed in review | No — contact support |
| `AML_HOLD` | 422 | AML screening result is `blocked` | No — compliance review required |
| `ACCOUNT_FROZEN` | 422 | Account status is `frozen` or `dormant` | No — account must be unfrozen |
| `IDEMPOTENCY_CONFLICT` | 409 | Idempotency key reused with different request body | No — use a new key |
| `RATE_LIMIT_EXCEEDED` | 429 | Per-customer rate budget exhausted for endpoint | Yes — after `Retry-After` interval |
| `INTERNAL_ERROR` | 500 | Unexpected server-side failure | Yes — retry with backoff |

## API Endpoints

The following endpoints constitute the core banking API surface. Each endpoint specification includes the full request and response schemas, applicable HTTP status codes with their conditions, and rate limit budget.

---
### GET /v1/accounts

Returns a paginated list of accounts owned by the authenticated customer, with optional filters for account status and currency.

**Auth Scope:** `banking:read` | **Idempotency Required:** No | **Rate Limit:** 60 requests/minute per customer

**Request Headers:**

| Header | Required | Description |
| --- | --- | --- |
| `Authorization` | Yes | `Bearer {jwt_token}` |
| `Accept` | No | `application/json` (default) |
| `X-Correlation-ID` | No | UUID for distributed tracing; generated if absent |

**Query Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `status` | string | Filter by account status: `active`, `frozen`, `dormant` |
| `currency` | string | ISO 4217 currency code |
| `cursor` | string | Opaque base64 pagination cursor from previous response |
| `limit` | integer | Page size; default 20, maximum 100 |

**Response Body (200 OK):**

```json
{
  "data": [
    {
      "accountId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "accountNumber": "GB29NWBK60161331926819",
      "type": "checking",
      "currency": "GBP",
      "balance": "4823.50",
      "availableBalance": "4323.50",
      "status": "active",
      "dailyLimitRemaining": "7500.00",
      "openedAt": "2024-03-01T09:15:00Z"
    }
  ],
  "pagination": {
    "cursor": "eyJsYXN0SWQiOiIzZmE4NWY2NCIsInRzIjoiMjAyNS0wMS0xNVQxNDozMjowN1oifQ==",
    "hasMore": true,
    "totalCount": 3
  }
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 200 | Accounts retrieved successfully; empty `data` array if no accounts exist |
| 400 | Invalid query parameter format (e.g., non-ISO currency code) |
| 401 | JWT missing, expired, or invalid signature |
| 403 | Insufficient scope — requires `banking:read` |
| 429 | Rate limit exceeded |

---
### POST /v1/accounts

Opens a new bank account of the specified type for the authenticated customer, subject to KYC status and account-count limits.

**Auth Scope:** `banking:write` | **Idempotency Required:** Yes | **Rate Limit:** 5 requests/minute per customer

**Request Headers:**

| Header | Required | Description |
| --- | --- | --- |
| `Authorization` | Yes | `Bearer {jwt_token}` |
| `Idempotency-Key` | Yes | Client-generated UUID v4; 24-hour deduplication window |
| `Content-Type` | Yes | `application/json` |

**Request Body:**

```json
{
  "accountType": "savings",
  "currency": "GBP",
  "initialDeposit": "500.00"
}
```

**Response Body (201 Created):**

```json
{
  "accountId": "7c3f1a2b-8e4d-4c7b-a9f6-1d2e3f4a5b6c",
  "accountNumber": "GB29NWBK60161331926820",
  "status": "active",
  "currency": "GBP",
  "createdAt": "2025-01-15T14:32:07Z"
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 201 | Account created; idempotency key stored for 24 hours |
| 400 | Validation error — invalid `accountType` or `currency` |
| 403 | `KYC_REQUIRED` — customer KYC status is not `passed` |
| 409 | `IDEMPOTENCY_CONFLICT` — key reused with different request body |
| 422 | Business rule violation — maximum account count reached |
| 429 | Rate limit exceeded |

---
### GET /v1/accounts/{accountId}/balance

Returns the real-time ledger balance and available balance for a single account, including any active holds.

**Auth Scope:** `banking:read` | **Idempotency Required:** No | **Rate Limit:** 120 requests/minute per customer

**Path Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `accountId` | UUID | Account identifier |

**Response Body (200 OK):**

```json
{
  "accountId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "balance": "4823.50",
  "availableBalance": "4323.50",
  "currency": "GBP",
  "asOf": "2025-01-15T14:32:07.483Z",
  "holds": [
    {
      "holdId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "amount": "500.00",
      "reason": "pending_transfer",
      "expiresAt": "2025-01-15T15:02:07Z"
    }
  ]
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 200 | Balance retrieved in real time; `asOf` reflects server timestamp |
| 401 | JWT missing or expired |
| 403 | Customer does not own this account |
| 404 | Account not found |
| 429 | Rate limit exceeded |

---
### POST /v1/transfers

Initiates a fund transfer between two accounts, supporting both internal transfers and outbound Faster Payments to third-party beneficiaries.

**Auth Scope:** `banking:write` | **Idempotency Required:** Yes | **Rate Limit:** 10 requests/minute per customer

**Request Headers:**

| Header | Required | Description |
| --- | --- | --- |
| `Authorization` | Yes | `Bearer {jwt_token}` |
| `Idempotency-Key` | Yes | UUID v4; prevents duplicate transfers on retry |
| `Content-Type` | Yes | `application/json` |

**Request Body:**

```json
{
  "sourceAccountId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "destinationAccountId": "7c3f1a2b-8e4d-4c7b-a9f6-1d2e3f4a5b6c",
  "amount": "250.00",
  "currency": "GBP",
  "reference": "Rent payment January 2025",
  "scheduledAt": null
}
```

**Response Body (202 Accepted):**

```json
{
  "transactionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "processing",
  "estimatedCompletion": "2025-01-15T14:34:07Z",
  "paymentRail": "faster_payments",
  "idempotencyKey": "b8f1c2d3-e4f5-6789-0abc-def123456789"
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 202 | Transfer accepted and queued for processing; poll transaction status |
| 400 | `VALIDATION_ERROR` — invalid amount, currency, or missing required field |
| 403 | `KYC_REQUIRED` — customer or account KYC not passed |
| 409 | `IDEMPOTENCY_CONFLICT` — key reused with differing body |
| 422 | `INSUFFICIENT_FUNDS`, `DAILY_LIMIT_EXCEEDED`, `ACCOUNT_FROZEN`, `AML_HOLD`, `FRAUD_SUSPECTED` |
| 429 | `RATE_LIMIT_EXCEEDED` |

---
### GET /v1/transactions

Returns a paginated, filterable ledger of transactions associated with the authenticated customer's accounts.

**Auth Scope:** `banking:read` | **Idempotency Required:** No | **Rate Limit:** 60 requests/minute per customer

**Query Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `accountId` | UUID | Filter by source or destination account |
| `status` | string | Filter by status: `initiated`, `processing`, `completed`, `failed`, `reversed` |
| `type` | string | Filter by type: `transfer`, `card_payment`, `direct_debit`, `fee` |
| `from` | ISO 8601 | Start of date range (inclusive) |
| `to` | ISO 8601 | End of date range (inclusive) |
| `cursor` | string | Pagination cursor from previous response |
| `limit` | integer | Page size; default 20, max 100 |

**Response Body (200 OK):**

```json
{
  "data": [
    {
      "transactionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "type": "transfer",
      "amount": "250.00",
      "currency": "GBP",
      "status": "completed",
      "counterparty": {
        "accountNumber": "GB29NWBK60161331926820",
        "name": "Jane Smith"
      },
      "reference": "Rent payment January 2025",
      "paymentRail": "faster_payments",
      "initiatedAt": "2025-01-15T14:32:07Z",
      "completedAt": "2025-01-15T14:32:45Z"
    }
  ],
  "pagination": {
    "cursor": "eyJsYXN0SWQiOiJmNDdhYzEwYiIsInRzIjoiMjAyNS0wMS0xNVQxNDozMjo0NVoifQ==",
    "hasMore": false
  }
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 200 | Transactions listed; empty array if none match filters |
| 400 | Invalid date range or filter value |
| 403 | Account does not belong to authenticated customer |
| 429 | Rate limit exceeded |

---
### POST /v1/cards

Issues a new virtual or physical debit card linked to a specified account, with configurable spend limits applied at issuance.

**Auth Scope:** `banking:write` | **Idempotency Required:** Yes | **Rate Limit:** 3 requests/minute per customer

**Request Body:**

```json
{
  "accountId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "cardType": "virtual",
  "limits": {
    "dailySpend": "1000.00",
    "perTransaction": "500.00"
  }
}
```

**Response Body (201 Created):**

```json
{
  "cardId": "c1d2e3f4-a5b6-7890-cdef-123456789012",
  "cardLastFour": "4242",
  "cardType": "virtual",
  "cardNetwork": "visa",
  "status": "issued",
  "expiryDate": "2028-01-31",
  "contactlessEnabled": true,
  "threeDsEnrolled": true
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 201 | Card issued; status `issued` until customer activates |
| 403 | `KYC_REQUIRED` or account is frozen |
| 409 | `IDEMPOTENCY_CONFLICT` |
| 422 | Maximum card limit reached for account (3 active cards) |
| 429 | Rate limit exceeded |

---
### POST /v1/loans/applications

Submits a personal loan application for underwriting assessment, returning an application reference for asynchronous status polling.

**Auth Scope:** `banking:write` | **Idempotency Required:** Yes | **Rate Limit:** 2 requests/minute per customer

**Request Body:**

```json
{
  "requestedAmount": "15000.00",
  "currency": "GBP",
  "termMonths": 36,
  "loanType": "personal",
  "purpose": "Home improvements",
  "annualIncome": "45000.00",
  "employmentStatus": "full_time"
}
```

**Response Body (202 Accepted):**

```json
{
  "applicationId": "d4e5f6a7-b8c9-0123-def4-56789abcdef0",
  "status": "pending_underwriting",
  "estimatedDecisionAt": "2025-01-15T14:52:07Z",
  "referenceNumber": "LN-2025-00847"
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 202 | Application accepted; underwriting decision delivered asynchronously |
| 400 | Validation error — `termMonths` out of range, invalid `loanType` |
| 403 | `KYC_REQUIRED` — enhanced KYC required for loan products |
| 422 | Customer already has an active loan application under review |
| 429 | Rate limit exceeded |

---
### POST /v1/kyc/verify

Initiates a document-based KYC verification for the authenticated customer, uploading identity document images for automated screening.

**Auth Scope:** `banking:write` | **Idempotency Required:** Yes | **Rate Limit:** 5 requests/hour per customer

**Request Body:**

```json
{
  "verificationType": "standard",
  "documentType": "passport",
  "documentImages": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD..."
  ]
}
```

**Response Body (202 Accepted):**

```json
{
  "kycId": "e5f6a7b8-c9d0-1234-ef56-789abcdef012",
  "status": "pending",
  "estimatedCompletionSeconds": 30,
  "pollingUrl": "/v1/kyc/e5f6a7b8-c9d0-1234-ef56-789abcdef012/status"
}
```

**HTTP Status Codes:**

| Status | Condition |
| --- | --- |
| 202 | Verification initiated; poll `pollingUrl` for result |
| 400 | Invalid `documentType`, missing images, or oversized payload (> 10 MB) |
| 409 | Active verification already in progress for this customer |
| 422 | `documentImages` count must be 2 for `passport`; 1 acceptable for `bank_statement` |
| 429 | Rate limit exceeded — maximum 5 KYC attempts per hour |

---
## Idempotency Key Semantics

Idempotency keys are UUID v4 values supplied by the client in the `Idempotency-Key` header on all mutating requests. The server stores the key and the serialised response in Redis with a 24-hour TTL anchored to the time of first submission. On a duplicate submission where the request body is identical, the stored response is replayed with the same HTTP status code and body, producing no additional side effects. A conflict (409) is returned only when the same key is submitted with a materially different request body, detected via SHA-256 hash comparison of the canonical JSON body. Clients must generate a fresh UUID v4 for each logically distinct operation and must never reuse a key across different operations even if the prior request failed at the network layer before a response was received.

| Scenario | Behaviour | Response Code | TTL |
| --- | --- | --- | --- |
| First submission of key — request succeeds | Process normally; store key + response hash in Redis | 2xx as per endpoint | 24 hours from first submission |
| Duplicate submission — identical body | Replay stored response; no side effects | Same as original (e.g., 201) | Extends to 24 hours from replay |
| Duplicate submission — different body | Reject with `IDEMPOTENCY_CONFLICT` | 409 Conflict | Key TTL unchanged |
| Submission after key expires | Process as new request; assign new key | 2xx as per endpoint | 24 hours from new submission |
| Key missing on mutating request | Reject request before processing | 400 Bad Request | N/A |

## Pagination Strategy

All list endpoints use cursor-based pagination rather than page-offset pagination, eliminating the duplicate-result and skipped-result problems that arise from offset pagination under concurrent writes. The cursor is an opaque, base64-encoded JSON object containing the `lastSeenId` (UUID of the last record returned) and `lastSeenTimestamp` (ISO 8601 timestamp). Clients must treat the cursor as opaque and must not attempt to decode or construct it manually. The absence of a `cursor` field in the request retrieves the first page. A `hasMore: false` field in the pagination block indicates that no further pages exist, and the client should cease polling.

Example cursor construction (internal only — never exposed to clients):

```json
{
  "lastSeenId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "lastSeenTimestamp": "2025-01-15T14:32:45Z"
}
```

Base64-encoded cursor value: `eyJsYXN0U2VlbklkIjoiZjQ3YWMxMGItNThjYy00MzcyLWE1NjctMGUwMmIyYzNkNDc5IiwibGFzdFNlZW5UaW1lc3RhbXAiOiIyMDI1LTAxLTE1VDE0OjMyOjQ1WiJ9`

## API Versioning Policy

The platform uses URL-path versioning with the format `/v{major}/`. Minor, non-breaking changes — such as adding optional request fields or new response properties — are deployed without a version increment. Additive changes are communicated via the platform changelog. Consumers are expected to follow the robustness principle: ignore unknown response fields rather than failing on their presence.

Breaking changes require a new major version. The decommission timeline for superseded major versions is a minimum of twelve calendar months from the date the successor version reaches general availability. During this period, both versions are served in parallel. Deprecation is signalled via a `Deprecation: true` response header and a `Sunset` header containing the planned decommission date, in accordance with RFC 9110 conventions.

| Versioning Attribute | Policy |
| --- | --- |
| Versioning scheme | URL path — `/v1/`, `/v2/` |
| Breaking change definition | Removed fields, changed field types, altered HTTP status semantics, removed endpoints |
| Non-breaking change definition | Added optional fields, new endpoints, new enum values in non-exhaustive positions |
| Deprecation notice period | Minimum 12 months before decommission |
| Deprecation signalling | `Deprecation: true` header + `Sunset: {date}` header on all deprecated-version responses |
| Parallel version support | Both old and new major versions served for minimum 12 months |
| Version discovery | `GET /` returns supported versions and their sunset dates |
