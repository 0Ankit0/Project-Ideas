# API Design

## Overview
REST API design for the rental management system. All endpoints are versioned under `/api/v1`. Authentication is via Bearer JWT tokens. Owner, Customer, Staff, and Admin roles have different permission scopes.

---

## Authentication Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register a new user (owner, customer, or staff) |
| POST | `/auth/login` | Public | Login and receive JWT access + refresh tokens |
| POST | `/auth/refresh` | Public | Refresh access token using refresh token |
| POST | `/auth/logout` | Authenticated | Revoke current session |
| POST | `/auth/verify-otp` | Public | Verify OTP for email/phone |
| POST | `/auth/forgot-password` | Public | Send password reset link |
| POST | `/auth/reset-password` | Public | Reset password using token |

---

## Asset Category Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/categories` | Public | List all active asset categories |
| GET | `/categories/{categoryId}` | Public | Get category details and attributes |
| POST | `/categories` | Admin | Create a new asset category |
| PUT | `/categories/{categoryId}` | Admin | Update a category |
| POST | `/categories/{categoryId}/attributes` | Admin | Add a custom attribute to a category |

---

## Asset Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/assets` | Public | Search and list published assets (with filters) |
| GET | `/assets/{assetId}` | Public | Get full asset details, photos, attributes, and pricing |
| POST | `/assets` | Owner | Create a new asset (draft) |
| PUT | `/assets/{assetId}` | Owner | Update asset details |
| DELETE | `/assets/{assetId}` | Owner | Archive an asset |
| POST | `/assets/{assetId}/publish` | Owner | Publish the asset listing |
| POST | `/assets/{assetId}/unpublish` | Owner | Unpublish the asset listing |
| POST | `/assets/{assetId}/photos` | Owner | Upload asset photos |
| DELETE | `/assets/{assetId}/photos/{photoId}` | Owner | Delete a photo |
| GET | `/assets/{assetId}/availability` | Public | Get availability calendar for a date range |
| GET | `/assets/{assetId}/price` | Public | Get pricing breakdown for a given period |

### GET /assets — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category slug |
| `start` | ISO datetime | Rental start time |
| `end` | ISO datetime | Rental end time |
| `location` | string | Location search (city or coordinates) |
| `radius_km` | number | Search radius from location |
| `min_price` | number | Minimum daily rate |
| `max_price` | number | Maximum daily rate |
| `page` | number | Page number |
| `per_page` | number | Results per page (max 50) |

---

## Pricing Rule Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/assets/{assetId}/pricing-rules` | Owner | List pricing rules for an asset |
| POST | `/assets/{assetId}/pricing-rules` | Owner | Create a pricing rule |
| PUT | `/assets/{assetId}/pricing-rules/{ruleId}` | Owner | Update a pricing rule |
| DELETE | `/assets/{assetId}/pricing-rules/{ruleId}` | Owner | Remove a pricing rule |

---

## Booking Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings` | Owner / Customer | List bookings (scoped by role) |
| GET | `/bookings/{bookingId}` | Owner / Customer | Get booking details |
| POST | `/bookings` | Customer | Submit a new booking request |
| POST | `/bookings/{bookingId}/confirm` | Owner | Confirm a pending booking |
| POST | `/bookings/{bookingId}/decline` | Owner | Decline a pending booking |
| PUT | `/bookings/{bookingId}` | Customer / Owner | Request booking modification |
| POST | `/bookings/{bookingId}/cancel` | Customer / Owner | Cancel a booking |
| POST | `/bookings/{bookingId}/return` | Customer | Initiate asset return |
| GET | `/bookings/{bookingId}/events` | Owner / Customer | Get booking event timeline |

### POST /bookings — Request Body

```json
{
  "assetId": "uuid",
  "rentalStartAt": "2025-06-15T10:00:00Z",
  "rentalEndAt": "2025-06-18T10:00:00Z",
  "specialRequests": "Please include a car seat",
  "paymentMethodId": "pm_stripe_xxx"
}
```

### POST /bookings — Response (201)

```json
{
  "bookingId": "uuid",
  "bookingNumber": "BKG-2025-00123",
  "status": "PENDING",
  "asset": { "id": "uuid", "name": "Toyota Camry 2023" },
  "rentalStartAt": "2025-06-15T10:00:00Z",
  "rentalEndAt": "2025-06-18T10:00:00Z",
  "pricing": {
    "baseFee": 180.00,
    "peakSurcharge": 20.00,
    "taxAmount": 20.00,
    "totalFee": 220.00,
    "depositAmount": 500.00
  }
}
```

---

## Rental Agreement Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings/{bookingId}/agreement` | Owner / Customer | Get the rental agreement for a booking |
| POST | `/bookings/{bookingId}/agreement` | Owner | Generate an agreement from a template |
| POST | `/bookings/{bookingId}/agreement/send` | Owner | Send agreement to customer for signature |
| POST | `/bookings/{bookingId}/agreement/countersign` | Owner | Owner countersigns the agreement |
| POST | `/webhooks/esign` | Internal | E-signature provider webhook receiver |

---

## Invoice & Payment Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/invoices` | Owner / Customer | List invoices (scoped by role) |
| GET | `/invoices/{invoiceId}` | Owner / Customer | Get invoice details with line items |
| POST | `/invoices/{invoiceId}/pay` | Customer | Pay an invoice |
| GET | `/invoices/{invoiceId}/receipt` | Customer | Download payment receipt |
| POST | `/bookings/{bookingId}/additional-charges` | Owner | Add a post-rental additional charge |
| POST | `/additional-charges/{chargeId}/dispute` | Customer | Dispute an additional charge |
| GET | `/payouts` | Owner | List owner payouts |
| GET | `/payouts/{payoutId}` | Owner | Get payout details |
| POST | `/webhooks/payment` | Internal | Payment gateway webhook receiver |

---

## Condition Assessment Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings/{bookingId}/assessments` | Owner / Customer / Staff | List assessments for a booking |
| GET | `/assessments/{assessmentId}` | Owner / Customer / Staff | Get assessment details |
| POST | `/assessments` | Staff | Create an assessment for a booking |
| POST | `/assessments/{assessmentId}/items` | Staff | Submit checklist items |
| POST | `/assessments/{assessmentId}/photos` | Staff | Upload assessment photos |
| POST | `/assessments/{assessmentId}/submit` | Staff | Submit the completed assessment |
| POST | `/assessments/{assessmentId}/countersign` | Customer | Customer countersigns pre-rental assessment |
| GET | `/assessments/{assessmentId}/report` | Owner / Customer | Download assessment PDF report |
| GET | `/bookings/{bookingId}/assessments/comparison` | Owner | Get pre vs post rental comparison |

---

## Maintenance Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/maintenance-requests` | Owner / Staff | List maintenance requests |
| GET | `/maintenance-requests/{requestId}` | Owner / Staff | Get request details |
| POST | `/maintenance-requests` | Owner | Log a new maintenance request |
| PUT | `/maintenance-requests/{requestId}/assign` | Owner | Assign to a staff member |
| PUT | `/maintenance-requests/{requestId}/status` | Staff | Update task status |
| POST | `/maintenance-requests/{requestId}/complete` | Staff | Submit completion with notes and photos |
| POST | `/maintenance-requests/{requestId}/approve` | Owner | Approve completed maintenance |
| POST | `/maintenance-requests/{requestId}/reopen` | Owner | Reopen the request |
| POST | `/maintenance-requests/{requestId}/cost` | Owner | Log maintenance cost |
| GET | `/assets/{assetId}/preventive-services` | Owner | List preventive service tasks |
| POST | `/assets/{assetId}/preventive-services` | Owner | Schedule a preventive service task |

---

## Reporting Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/reports/dashboard` | Owner / Admin | Financial dashboard summary |
| POST | `/reports/revenue` | Owner | Generate revenue report |
| POST | `/reports/utilisation` | Owner | Generate asset utilisation report |
| POST | `/reports/tax-summary` | Owner | Generate tax summary report |
| GET | `/reports/{reportId}/download` | Owner | Download generated report file |

---

## Standard Response Envelope

```json
{
  "success": true,
  "data": { },
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 150
  }
}
```

## Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "BOOKING_UNAVAILABLE",
    "message": "The asset is not available for the selected dates.",
    "details": null
  },
  "requestId": "req_abc123"
}
```

## Common Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Insufficient role permissions |
| `NOT_FOUND` | 404 | Resource does not exist |
| `VALIDATION_ERROR` | 422 | Request body fails schema validation |
| `BOOKING_UNAVAILABLE` | 409 | Asset unavailable for requested dates |
| `PAYMENT_FAILED` | 402 | Payment gateway rejected the transaction |
| `DEPOSIT_REQUIRED` | 402 | Deposit payment must be completed first |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
