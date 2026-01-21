# API Design - Slot Booking System

> **Platform Independence**: RESTful API design applicable to any backend technology.

---

## API Overview

| Base URL | Version | Auth |
|----------|---------|------|
| `https://api.example.com` | `/v1` | Bearer Token (JWT) |

---

## Authentication Endpoints

### Register
```
POST /v1/auth/register
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "John Doe",
  "phone": "+1234567890"
}
```
**Response:** `201 Created`
```json
{
  "userId": "uuid",
  "message": "Verification email sent"
}
```

### Login
```
POST /v1/auth/login
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```
**Response:** `200 OK`
```json
{
  "accessToken": "jwt_token",
  "refreshToken": "refresh_token",
  "expiresIn": 3600,
  "user": { "id": "uuid", "email": "...", "name": "...", "role": "user" }
}
```

### Refresh Token
```
POST /v1/auth/refresh
```

### Password Reset
```
POST /v1/auth/password/reset-request
POST /v1/auth/password/reset
```

---

## Resource Endpoints

### List Resources
```
GET /v1/resources
```
**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| category | string | Filter by category |
| lat, lng | float | Center for location search |
| radius | int | Radius in km |
| minPrice, maxPrice | float | Price range |
| page, limit | int | Pagination |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Court A",
      "category": "futsal",
      "location": { "address": "...", "lat": 0, "lng": 0 },
      "basePrice": 50.00,
      "rating": 4.5,
      "imageUrl": "https://..."
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 100 }
}
```

### Get Resource Details
```
GET /v1/resources/:resourceId
```
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Court A",
  "description": "...",
  "category": { "id": "uuid", "name": "Futsal" },
  "capacity": 10,
  "amenities": [{ "id": "uuid", "name": "Parking" }],
  "images": [{ "url": "...", "isPrimary": true }],
  "location": { "address": "...", "lat": 0, "lng": 0 },
  "basePrice": 50.00,
  "operatingHours": { "monday": { "open": "08:00", "close": "22:00" } },
  "rating": 4.5,
  "reviewCount": 28
}
```

### Get Available Slots
```
GET /v1/resources/:resourceId/slots
```
**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| date | string | Date (YYYY-MM-DD) |
| startDate, endDate | string | Date range |

**Response:** `200 OK`
```json
{
  "date": "2024-01-20",
  "slots": [
    { "id": "uuid", "startTime": "09:00", "endTime": "10:00", "price": 50.00, "status": "available" },
    { "id": "uuid", "startTime": "10:00", "endTime": "11:00", "price": 50.00, "status": "booked" }
  ]
}
```

---

## Booking Endpoints

### Create Booking
```
POST /v1/bookings
```
**Request:**
```json
{
  "resourceId": "uuid",
  "slotIds": ["uuid1", "uuid2"],
  "promoCode": "SAVE10",
  "notes": "Optional notes"
}
```
**Response:** `201 Created`
```json
{
  "bookingId": "uuid",
  "bookingNumber": "BK-20240120-001",
  "status": "pending",
  "totalAmount": 90.00,
  "discountAmount": 10.00,
  "paymentUrl": "/v1/payments/initiate?bookingId=uuid"
}
```

### Get User Bookings
```
GET /v1/bookings
```
**Query:** `status=upcoming|past|cancelled`, `page`, `limit`

### Get Booking Details
```
GET /v1/bookings/:bookingId
```

### Cancel Booking
```
DELETE /v1/bookings/:bookingId
```
**Request:**
```json
{ "reason": "Schedule conflict" }
```
**Response:** `200 OK`
```json
{
  "status": "cancelled",
  "refundAmount": 45.00,
  "refundStatus": "processing"
}
```

### Reschedule Booking
```
PUT /v1/bookings/:bookingId/reschedule
```
**Request:**
```json
{ "newSlotIds": ["uuid3", "uuid4"] }
```

---

## Payment Endpoints

### Initiate Payment
```
POST /v1/payments/initiate
```
**Request:**
```json
{
  "bookingId": "uuid",
  "method": "card",
  "returnUrl": "https://app.example.com/payment/complete"
}
```
**Response:** `200 OK`
```json
{
  "paymentId": "uuid",
  "clientSecret": "stripe_client_secret",
  "amount": 90.00,
  "currency": "USD"
}
```

### Verify Payment
```
POST /v1/payments/:paymentId/verify
```

### Payment Webhook
```
POST /v1/webhooks/payment
```

---

## Provider Endpoints

### Create Resource
```
POST /v1/provider/resources
```
**Request:**
```json
{
  "name": "Court A",
  "categoryId": "uuid",
  "description": "...",
  "capacity": 10,
  "basePrice": 50.00,
  "location": { "address": "...", "lat": 0, "lng": 0 },
  "amenityIds": ["uuid1", "uuid2"],
  "operatingHours": { "monday": { "open": "08:00", "close": "22:00" } },
  "slotDurationMinutes": 60
}
```

### Update Availability
```
PUT /v1/provider/resources/:resourceId/availability
```

### Get Provider Bookings
```
GET /v1/provider/bookings
```

### Get Earnings
```
GET /v1/provider/earnings
```

---

## Admin Endpoints

### List Users
```
GET /v1/admin/users
```

### Approve Provider
```
POST /v1/admin/providers/:providerId/approve
POST /v1/admin/providers/:providerId/reject
```

### Platform Analytics
```
GET /v1/admin/analytics/dashboard
GET /v1/admin/analytics/bookings
GET /v1/admin/analytics/revenue
```

---

## Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid input |
| 401 | UNAUTHORIZED | Authentication required |
| 403 | FORBIDDEN | Permission denied |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Slot unavailable |
| 429 | RATE_LIMITED | Too many requests |
| 500 | SERVER_ERROR | Internal error |

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Auth endpoints | 10 req/min |
| Read endpoints | 100 req/min |
| Write endpoints | 30 req/min |
| Search | 50 req/min |
