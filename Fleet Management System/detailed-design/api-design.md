# Fleet Management System — REST API Design

## Table of Contents
1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Conventions](#conventions)
4. [Vehicles](#vehicles)
5. [Drivers](#drivers)
6. [Trips](#trips)
7. [GPS Pings](#gps-pings)
8. [Geofences](#geofences)
9. [Maintenance Records](#maintenance-records)
10. [Fuel Records](#fuel-records)
11. [Incidents](#incidents)
12. [Routes](#routes)
13. [Reports](#reports)
14. [Alerts & Alert Rules](#alerts--alert-rules)
15. [Webhook Events](#webhook-events)
16. [Error Reference](#error-reference)

---

## Overview

| Property | Value |
|---|---|
| Base URL | `https://api.fleetmanager.io/v1` |
| Protocol | HTTPS only (TLS 1.2+) |
| Content-Type | `application/json` |
| Versioning | URL path (`/v1/`, `/v2/`) |
| Authentication | Bearer JWT in `Authorization` header |
| Fleet Scoping | `X-Fleet-ID` request header (required unless using a fleet-scoped API key) |

All timestamps are **ISO 8601 UTC** (e.g., `2024-07-15T14:23:00Z`). All distances are in **kilometres**. All monetary values are in **USD** unless otherwise specified.

---

## Authentication & Authorization

### JWT Bearer Token

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens are issued by `https://auth.fleetmanager.io/oauth/token` using the Client Credentials or Authorization Code flows. Each token embeds:

- `sub` — user or service account UUID
- `company_id` — tenant UUID
- `fleet_ids` — array of fleet UUIDs the token is authorized for
- `roles` — array of role strings: `fleet_admin`, `dispatcher`, `driver`, `maintenance_manager`, `finance`, `readonly`
- `exp` — expiry (default 1 hour for user tokens, 24 hours for device tokens)

### API Keys (Device/Server-to-Server)

GPS trackers and ELD devices authenticate with a long-lived API key passed as a header:

```
X-Api-Key: fms_live_sk_7a8b9c...
```

Device API keys are scoped to a specific vehicle and may only call the GPS ping ingestion endpoint.

### Rate Limits

| Caller Type | Limit |
|---|---|
| User JWT | 1,000 requests/min per token |
| Service account JWT | 5,000 requests/min per token |
| Device API key (GPS ingest) | 10,000 pings/min per vehicle |
| Report endpoints | 60 requests/min per token |

Rate limit headers are returned on every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1720000860
```

---

## Conventions

### Pagination (Cursor-Based)

All list endpoints support cursor-based pagination:

```
GET /vehicles?limit=25&cursor=eyJpZCI6ImFiY2QifQ==
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 25 | Max records per page. Max 200. |
| `cursor` | string | — | Opaque cursor from previous response `meta.next_cursor`. |

**Paginated Response Envelope:**

```json
{
  "data": [...],
  "meta": {
    "total": 143,
    "limit": 25,
    "has_more": true,
    "next_cursor": "eyJpZCI6InV1aWQtaGVyZSJ9"
  }
}
```

### Filtering & Sorting

```
GET /trips?status=completed&driver_id=uuid&start_time_gte=2024-07-01T00:00:00Z&sort=-start_time
```

- Prefix sort field with `-` for descending order.
- Date range filters use `_gte` (≥) and `_lte` (≤) suffixes.

### Standard Response Shape

**Success (single resource):**

```json
{
  "data": { ... }
}
```

**Error:**

```json
{
  "error": {
    "code": "VEHICLE_NOT_FOUND",
    "message": "No vehicle found with id '3fa85f64-5717-4562-b3fc-2c963f66afa6'.",
    "details": {
      "vehicle_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }
  }
}
```

---

## Vehicles

### `GET /vehicles`

Retrieve a paginated list of vehicles in the authenticated fleet.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | Filter by vehicle status enum value |
| `fuel_type` | string | Filter by fuel type |
| `make` | string | Partial match on vehicle make |
| `sort` | string | Default: `-created_at`. Allowed: `make`, `model`, `year`, `odometer_km`, `status` |
| `limit` | integer | Default: 25. Max: 200 |
| `cursor` | string | Pagination cursor |

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
      "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
      "vin": "1HGCM82633A004352",
      "license_plate": "TXK-4821",
      "license_plate_state": "TX",
      "make": "Freightliner",
      "model": "Cascadia 126",
      "year": 2022,
      "color": "White",
      "status": "available",
      "odometer_km": 48320.5,
      "fuel_type": "diesel",
      "fuel_tank_capacity_l": 378.5,
      "gps_device_serial": "CALAMP-LMU-3030-88741",
      "eld_certified": true,
      "insurance_expiry_date": "2025-03-31",
      "registration_expiry_date": "2025-01-15",
      "last_inspection_date": "2024-06-10",
      "last_inspection_pass": true,
      "acquisition_date": "2022-04-01",
      "acquisition_cost": 165000.00,
      "created_at": "2022-04-05T09:00:00Z",
      "updated_at": "2024-07-14T16:42:00Z"
    }
  ],
  "meta": {
    "total": 48,
    "limit": 25,
    "has_more": true,
    "next_cursor": "eyJpZCI6IjExYmY1YjM3In0="
  }
}
```

---

### `POST /vehicles`

Create a new vehicle in the fleet.

**Request Body:**

```json
{
  "vin": "1FTFW1ET5DFA43920",
  "license_plate": "TXM-9930",
  "license_plate_state": "TX",
  "make": "Ford",
  "model": "F-550 Super Duty",
  "year": 2023,
  "color": "Silver",
  "fuel_type": "diesel",
  "fuel_tank_capacity_l": 132.5,
  "gross_vehicle_weight_kg": 7257.0,
  "gps_device_serial": "CALAMP-LMU-3040-99182",
  "eld_device_serial": "SAMSARA-VG34-00192",
  "eld_certified": true,
  "insurance_policy_number": "AIG-COM-2024-88172",
  "insurance_expiry_date": "2025-06-30",
  "registration_expiry_date": "2025-02-28",
  "acquisition_date": "2023-01-15",
  "acquisition_cost": 78500.00
}
```

**Required fields:** `vin`, `license_plate`, `license_plate_state`, `make`, `model`, `year`, `fuel_type`

**Response `201 Created`:** Returns the created vehicle object.

**Error Responses:**

| HTTP | Code | Condition |
|---|---|---|
| 409 | `VEHICLE_VIN_CONFLICT` | A vehicle with this VIN already exists in the system |
| 409 | `VEHICLE_PLATE_CONFLICT` | License plate + state already registered in this fleet |
| 422 | `VEHICLE_VIN_INVALID` | VIN fails format validation (17 alphanumeric, no I/O/Q) |
| 403 | `FLEET_VEHICLE_LIMIT_REACHED` | Subscription vehicle cap exceeded |

---

### `GET /vehicles/{id}`

Retrieve a single vehicle by ID.

**Response `200 OK`:** Full vehicle object including `vehicle_model_id` reference and all compliance dates.

**Error Responses:** `404 VEHICLE_NOT_FOUND`

---

### `PUT /vehicles/{id}`

Update vehicle fields. Partial updates are supported (only provided fields are changed).

**Immutable fields:** `id`, `vin`, `created_at`

**Response `200 OK`:** Updated vehicle object.

---

### `DELETE /vehicles/{id}`

Soft-delete a vehicle. Sets `deleted_at` to the current timestamp. Vehicles with `status = 'in_trip'` cannot be deleted.

**Response `204 No Content`**

**Error Responses:** `409 VEHICLE_IN_ACTIVE_TRIP`

---

### `GET /vehicles/{id}/location`

Get the most recent GPS location for a vehicle.

**Response `200 OK`:**

```json
{
  "data": {
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "latitude": 29.7604,
    "longitude": -95.3698,
    "altitude_m": 14.2,
    "speed_kmh": 87.3,
    "heading_degrees": 215,
    "accuracy_m": 4.1,
    "timestamp": "2024-07-15T14:22:47Z",
    "source": "gps_device",
    "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b"
  }
}
```

**Error Responses:** `404 VEHICLE_NOT_FOUND`, `404 VEHICLE_LOCATION_UNAVAILABLE` (no recent ping within 24h)

---

### `GET /vehicles/{id}/trips`

List trips for a specific vehicle. Supports the standard pagination, filtering, and sorting parameters. Filtered by `start_time_gte`, `start_time_lte`, `status`.

---

### `GET /vehicles/{id}/maintenance-records`

List maintenance records for a vehicle. Filter by `status`, `maintenance_type`, `scheduled_date_gte`, `scheduled_date_lte`.

---

### `GET /vehicles/{id}/fuel-records`

List fuel records for a vehicle. Filter by `recorded_at_gte`, `recorded_at_lte`, `is_flagged`.

---

### `POST /vehicles/{id}/documents`

Upload document metadata for a vehicle. The file must be uploaded to the pre-signed URL returned in the response before the document is marked `is_verified`.

**Request Body:**

```json
{
  "document_type": "vehicle_registration",
  "name": "TX Registration 2025",
  "expiry_date": "2025-02-28",
  "issued_date": "2024-02-28",
  "issuing_authority": "Texas DMV",
  "document_number": "42871930-TX",
  "file_name": "registration_2025.pdf",
  "file_size_bytes": 245120,
  "mime_type": "application/pdf"
}
```

**Response `201 Created`:**

```json
{
  "data": {
    "id": "d7e8f9a0-1b2c-3d4e-5f6a-7b8c9d0e1f2a",
    "upload_url": "https://storage.fleetmanager.io/uploads/...?X-Amz-Signature=...",
    "upload_url_expires_at": "2024-07-15T14:52:00Z",
    "document_type": "vehicle_registration",
    "name": "TX Registration 2025",
    "entity_type": "vehicle",
    "entity_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "created_at": "2024-07-15T14:22:00Z"
  }
}
```

---

## Drivers

### `GET /drivers`

List drivers in the fleet. Filter by `status`, `license_class`, `license_expiry_lte` (for expiry alerts).

**Response `200 OK`:** Paginated list of driver objects.

---

### `POST /drivers`

Create a new driver.

**Request Body:**

```json
{
  "first_name": "Marcus",
  "last_name": "Torres",
  "email": "m.torres@acmelogistics.com",
  "phone": "+1-713-555-0182",
  "date_of_birth": "1985-03-22",
  "hire_date": "2021-09-01",
  "employee_id": "EMP-4471",
  "license_number": "TX-DL-9847321",
  "license_class": "A",
  "license_state": "TX",
  "license_expiry_date": "2027-03-22",
  "cdl_endorsements": ["H", "N"],
  "medical_cert_expiry": "2025-09-01"
}
```

**Required fields:** `first_name`, `last_name`, `email`, `phone`, `license_number`, `license_class`, `license_state`, `license_expiry_date`

**Response `201 Created`:** Full driver object.

**Error Responses:**

| HTTP | Code | Condition |
|---|---|---|
| 409 | `DRIVER_LICENSE_CONFLICT` | License number + state already exists in this fleet |
| 409 | `DRIVER_EMPLOYEE_ID_CONFLICT` | Employee ID already exists in this fleet |
| 403 | `FLEET_DRIVER_LIMIT_REACHED` | Subscription driver cap exceeded |

---

### `GET /drivers/{id}`

Retrieve a single driver by ID.

**Response `200 OK`:**

```json
{
  "data": {
    "id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
    "employee_id": "EMP-4471",
    "first_name": "Marcus",
    "last_name": "Torres",
    "email": "m.torres@acmelogistics.com",
    "phone": "+1-713-555-0182",
    "date_of_birth": "1985-03-22",
    "hire_date": "2021-09-01",
    "license_number": "TX-DL-9847321",
    "license_class": "A",
    "license_state": "TX",
    "license_expiry_date": "2027-03-22",
    "cdl_endorsements": ["H", "N"],
    "medical_cert_expiry": "2025-09-01",
    "status": "active",
    "driver_score": 92.4,
    "total_trips": 318,
    "total_km_driven": 148320.7,
    "hos_status": "off_duty",
    "created_at": "2021-09-05T10:00:00Z",
    "updated_at": "2024-07-14T20:00:00Z"
  }
}
```

---

### `PUT /drivers/{id}`

Update driver fields. Partial updates supported.

**Response `200 OK`:** Updated driver object.

---

### `DELETE /drivers/{id}`

Soft-delete a driver. Cannot delete drivers with `status = 'on_duty'` or `status = 'driving'`.

**Response `204 No Content`**

---

### `GET /drivers/{id}/score`

Retrieve the driver's scoring breakdown for a configurable time period.

**Query Parameters:** `period_days` (default: 90), `include_trips` (boolean, default: false)

**Response `200 OK`:**

```json
{
  "data": {
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "period_days": 90,
    "overall_score": 92.4,
    "safety_score": 94.1,
    "efficiency_score": 91.2,
    "compliance_score": 93.8,
    "total_trips": 47,
    "total_km": 22840.3,
    "harsh_braking_events": 3,
    "harsh_acceleration_events": 5,
    "speeding_events": 2,
    "total_idle_time_minutes": 412,
    "trend": "improving",
    "calculated_at": "2024-07-15T00:00:00Z"
  }
}
```

---

### `GET /drivers/{id}/trips`

List trips for a driver. Supports `status`, `start_time_gte`, `start_time_lte`, and sort parameters.

---

### `GET /drivers/{id}/hos-logs`

Retrieve HOS duty-status log for a driver.

**Query Parameters:** `start_date`, `end_date` (ISO 8601 date, default last 8 days for ELD compliance view)

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "e1f2a3b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b",
      "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
      "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
      "status": "driving",
      "started_at": "2024-07-15T07:00:00Z",
      "ended_at": "2024-07-15T11:00:00Z",
      "duration_minutes": 240,
      "location_lat": 29.7604,
      "location_lng": -95.3698,
      "eld_event_id": "SAMSARA-EVT-49182731"
    }
  ],
  "meta": { "total": 16, "limit": 50, "has_more": false, "next_cursor": null }
}
```

---

### `POST /drivers/{id}/documents`

Upload document metadata for a driver (license, medical certificate, etc.). Same request/response shape as `POST /vehicles/{id}/documents`.

---

## Trips

### `GET /trips`

List trips in the fleet with filtering.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `vehicle_id` | UUID | Filter to a specific vehicle |
| `driver_id` | UUID | Filter to a specific driver |
| `status` | string | Trip status enum value |
| `start_time_gte` | timestamp | Trips starting on or after this time |
| `start_time_lte` | timestamp | Trips starting on or before this time |
| `sort` | string | Default: `-start_time` |

---

### `POST /trips`

Create and schedule a new trip.

**Request Body:**

```json
{
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
  "route_id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "scheduled_start_time": "2024-07-16T06:00:00Z",
  "scheduled_end_time": "2024-07-16T14:00:00Z",
  "start_address": "1200 Port of Houston Dr, Houston, TX 77029",
  "end_address": "3801 W Commerce St, Dallas, TX 75212",
  "purpose": "Freight Delivery",
  "cargo_description": "Palletized consumer electronics — 8,400 lb",
  "waypoints": [
    {
      "sequence_num": 1,
      "address": "I-45 N Rest Area, Huntsville, TX 77340",
      "latitude": 30.7135,
      "longitude": -95.5498
    }
  ]
}
```

**Required fields:** `vehicle_id`, `driver_id`, `scheduled_start_time`

**Response `201 Created`:** Full trip object with `status: "scheduled"`.

**Error Responses:**

| HTTP | Code | Condition |
|---|---|---|
| 409 | `VEHICLE_ALREADY_DISPATCHED` | Vehicle is already in an active trip |
| 409 | `DRIVER_ALREADY_DISPATCHED` | Driver is already in an active trip |
| 422 | `DRIVER_LICENSE_EXPIRED` | Driver's CDL has passed expiry date |
| 422 | `VEHICLE_OUT_OF_SERVICE` | Vehicle status prevents dispatch |

---

### `GET /trips/{id}`

Retrieve a single trip with all computed metrics.

**Response `200 OK`:**

```json
{
  "data": {
    "id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
    "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "status": "completed",
    "start_time": "2024-07-15T06:12:00Z",
    "end_time": "2024-07-15T13:44:00Z",
    "scheduled_start_time": "2024-07-15T06:00:00Z",
    "scheduled_end_time": "2024-07-15T14:00:00Z",
    "start_address": "1200 Port of Houston Dr, Houston, TX 77029",
    "end_address": "3801 W Commerce St, Dallas, TX 75212",
    "distance_km": 394.2,
    "duration_minutes": 452,
    "avg_speed_kmh": 82.3,
    "max_speed_kmh": 114.7,
    "fuel_consumed_l": 138.4,
    "idle_time_minutes": 34,
    "harsh_braking_events": 0,
    "harsh_acceleration_events": 1,
    "speeding_events": 2,
    "geofence_violations": 0,
    "driver_score": 94.5,
    "purpose": "Freight Delivery",
    "created_at": "2024-07-14T16:00:00Z",
    "updated_at": "2024-07-15T13:45:00Z"
  }
}
```

---

### `PUT /trips/{id}`

Update trip metadata (purpose, notes, cargo description). Cannot update status or metrics directly.

---

### `DELETE /trips/{id}`

Cancel a trip in `draft` or `scheduled` status. Calls `POST /trips/{id}/cancel` internally.

---

### `POST /trips/{id}/start`

Start a dispatched or scheduled trip. Sets `status = 'in_progress'`, records `start_time`, and updates vehicle/driver status.

**Request Body:**

```json
{
  "start_location_lat": 29.7604,
  "start_location_lng": -95.3698,
  "odometer_km": 48320.5
}
```

**Response `200 OK`:** Updated trip object.

---

### `POST /trips/{id}/end`

Complete an in-progress trip. Triggers background scoring and odometer update.

**Request Body:**

```json
{
  "end_location_lat": 32.7767,
  "end_location_lng": -96.7970,
  "odometer_km": 48714.7,
  "fuel_consumed_l": 138.4,
  "notes": "Delivery completed. Signed by warehouse manager R. Chen."
}
```

**Response `200 OK`:** Updated trip object. `driver_score` and metrics may be null until the scoring job completes (within 60 seconds).

---

### `POST /trips/{id}/cancel`

Cancel a trip. Only possible for `draft`, `scheduled`, or `dispatched` trips.

**Request Body:**

```json
{
  "reason": "Customer cancelled shipment — order #ORD-2024-8811"
}
```

**Response `200 OK`:** Updated trip with `status: "cancelled"`.

---

### `GET /trips/{id}/waypoints`

List ordered waypoints for a trip.

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
      "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
      "sequence_num": 1,
      "address": "I-45 N Rest Area, Huntsville, TX 77340",
      "latitude": 30.7135,
      "longitude": -95.5498,
      "arrived_at": "2024-07-15T08:47:00Z",
      "departed_at": "2024-07-15T09:02:00Z",
      "notes": null
    }
  ]
}
```

---

### `GET /trips/{id}/gps-pings`

Retrieve GPS pings recorded during a trip. Returns a time-ordered array.

**Query Parameters:** `limit` (default 500, max 5000), `cursor`

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "ping-uuid-1",
      "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
      "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
      "latitude": 29.7604,
      "longitude": -95.3698,
      "altitude_m": 15.0,
      "speed_kmh": 0.0,
      "heading_degrees": 0,
      "accuracy_m": 3.5,
      "timestamp": "2024-07-15T06:12:03Z",
      "source": "gps_device"
    }
  ],
  "meta": { "total": 2714, "limit": 500, "has_more": true, "next_cursor": "..." }
}
```

---

## GPS Pings

### `POST /gps-pings`

**Bulk telemetry ingestion endpoint.** Accepts up to 500 pings per request. Authenticated with a device API key (`X-Api-Key`). This endpoint is fire-and-forget; data is written to a Kafka topic and asynchronously persisted.

**Request Body:**

```json
{
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "pings": [
    {
      "latitude": 30.0794,
      "longitude": -95.4138,
      "altitude_m": 28.5,
      "speed_kmh": 94.2,
      "heading_degrees": 352,
      "accuracy_m": 3.8,
      "timestamp": "2024-07-15T09:14:00Z",
      "signal_strength": -72,
      "source": "gps_device"
    },
    {
      "latitude": 30.0921,
      "longitude": -95.4145,
      "speed_kmh": 96.1,
      "heading_degrees": 354,
      "accuracy_m": 3.6,
      "timestamp": "2024-07-15T09:14:10Z",
      "source": "gps_device"
    }
  ]
}
```

**Response `202 Accepted`:**

```json
{
  "data": {
    "accepted": 2,
    "rejected": 0,
    "batch_id": "b-20240715-091410-00382"
  }
}
```

**Error Responses:** `413 PING_BATCH_TOO_LARGE` (over 500 pings), `422 PING_TIMESTAMP_TOO_OLD` (ping older than 24h rejected)

---

### `GET /vehicles/{id}/gps-pings`

Retrieve historical GPS pings for a vehicle by time range.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `start_time` | timestamp | Yes | Start of range (ISO 8601) |
| `end_time` | timestamp | Yes | End of range (max 24-hour window) |
| `limit` | integer | No | Default 1000, max 10000 |
| `cursor` | string | No | Pagination cursor |

---

## Geofences

### `GET /geofences`

List all geofence zones in the fleet.

**Query Parameters:** `active` (boolean, default true), `limit`, `cursor`

---

### `POST /geofences`

Create a new geofence zone.

**Request Body:**

```json
{
  "name": "Dallas Distribution Center",
  "description": "Primary inbound receiving dock zone",
  "shape_type": "polygon",
  "coordinates_json": [
    [-96.8017, 32.7812],
    [-96.7993, 32.7812],
    [-96.7993, 32.7791],
    [-96.8017, 32.7791],
    [-96.8017, 32.7812]
  ],
  "alert_on_enter": true,
  "alert_on_exit": true,
  "alert_on_dwell_minutes": 120
}
```

**Response `201 Created`:** Full geofence zone object.

---

### `GET /geofences/{id}`

Retrieve a geofence zone by ID.

---

### `PUT /geofences/{id}`

Update geofence zone attributes. Changing `coordinates_json` takes effect immediately for all new GPS pings processed after the update.

---

### `DELETE /geofences/{id}`

Deactivate a geofence zone (sets `active = false`). Historical events are preserved.

**Response `204 No Content`**

---

### `GET /geofences/{id}/events`

List boundary crossing events for a geofence zone.

**Query Parameters:** `vehicle_id`, `event_type` (`entered` | `exited` | `dwell_exceeded`), `start_time`, `end_time`, `limit`, `cursor`

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "g1h2i3j4-k5l6-7m8n-9o0p-q1r2s3t4u5v6",
      "geofence_zone_id": "z9y8x7w6-v5u4-3t2s-1r0q-p9o8n7m6l5k4",
      "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
      "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
      "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
      "event_type": "entered",
      "occurred_at": "2024-07-15T13:38:00Z",
      "location_lat": 32.7804,
      "location_lng": -96.8005,
      "alert_sent": true,
      "alert_sent_at": "2024-07-15T13:38:02Z"
    }
  ],
  "meta": { "total": 34, "limit": 25, "has_more": true, "next_cursor": "..." }
}
```

---

## Maintenance Records

### `GET /maintenance-records`

List maintenance records in the fleet.

**Query Parameters:** `vehicle_id`, `status`, `maintenance_type`, `scheduled_date_gte`, `scheduled_date_lte`, `sort` (default: `-scheduled_date`)

---

### `POST /maintenance-records`

Create a maintenance record (planned or emergency).

**Request Body:**

```json
{
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "maintenance_type": "oil_change",
  "scheduled_date": "2024-07-20",
  "description": "50,000 km scheduled oil and filter change. Synthetic 15W-40.",
  "service_provider_name": "Freightliner Houston Service Center",
  "odometer_at_service_km": 50000.0,
  "next_service_km": 58000.0,
  "next_service_date": "2024-10-20",
  "parts_cost": 84.50,
  "labor_cost": 120.00
}
```

**Response `201 Created`:** Full maintenance record object.

---

### `GET /maintenance-records/{id}`

Retrieve a single maintenance record.

---

### `PUT /maintenance-records/{id}`

Update a maintenance record. Status transitions must follow the allowed flow:
`scheduled → pending_assignment → assigned → in_progress → awaiting_parts → completed`

Emergency path: `scheduled → in_progress → completed`

---

### `DELETE /maintenance-records/{id}`

Cancel a maintenance record. Only `scheduled` and `pending_assignment` records may be cancelled.

---

### `POST /maintenance-records/{id}/complete`

Mark a maintenance record as completed and update the vehicle's odometer and next service due dates.

**Request Body:**

```json
{
  "completed_date": "2024-07-20T14:30:00Z",
  "odometer_at_service_km": 49983.2,
  "technician_name": "James Okafor",
  "labor_hours": 1.5,
  "parts_cost": 84.50,
  "labor_cost": 120.00,
  "next_service_km": 57983.2,
  "next_service_date": "2024-10-20",
  "notes": "Used Castrol Vecton 15W-40. All torque specs confirmed. No other issues found."
}
```

**Response `200 OK`:** Updated maintenance record with `status: "completed"` and `total_cost: 204.50`.

---

### `GET /vehicles/{id}/maintenance-schedules`

List all maintenance schedules configured for a vehicle.

---

### `PUT /maintenance-schedules/{id}`

Update a maintenance schedule interval or active status.

**Request Body:**

```json
{
  "interval_km": 12000.0,
  "interval_days": 120,
  "active": true
}
```

---

## Fuel Records

### `GET /fuel-records`

List fuel records for the fleet.

**Query Parameters:** `vehicle_id`, `driver_id`, `recorded_at_gte`, `recorded_at_lte`, `is_flagged`, `fuel_type`, `sort` (default: `-recorded_at`)

---

### `POST /fuel-records`

Log a fuel purchase.

**Request Body:**

```json
{
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
  "recorded_at": "2024-07-15T10:45:00Z",
  "fuel_station_name": "Love's Travel Stop #441",
  "fuel_station_address": "1100 TX-75, Huntsville, TX 77340",
  "location_lat": 30.7248,
  "location_lng": -95.5812,
  "fuel_type": "diesel",
  "quantity_l": 284.0,
  "unit_price": 1.089,
  "total_cost": 309.26,
  "odometer_km": 48612.0,
  "authorization_code": "AUTH-20240715-443821"
}
```

**Response `201 Created`:** Full fuel record object.

---

### `GET /fuel-records/{id}`

Retrieve a single fuel record.

---

### `PUT /fuel-records/{id}`

Correct a fuel record (e.g., wrong quantity). Records flagged as `is_flagged = true` require a `flag_reason` when unflagging.

---

### `DELETE /fuel-records/{id}`

Void a fuel record (soft delete). Requires `finance` or `fleet_admin` role.

---

### `GET /reports/fuel-analytics`

Aggregate fuel consumption and cost analytics.

**Query Parameters:** `start_date`, `end_date`, `vehicle_id`, `driver_id`, `group_by` (`vehicle` | `driver` | `day` | `week` | `month`)

**Response `200 OK`:**

```json
{
  "data": {
    "period": { "start": "2024-07-01", "end": "2024-07-15" },
    "summary": {
      "total_records": 187,
      "total_quantity_l": 48320.4,
      "total_cost_usd": 52698.22,
      "avg_cost_per_km": 0.134,
      "avg_fuel_economy_lper100km": 34.1,
      "flagged_transactions": 3
    },
    "breakdown": [
      {
        "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
        "vehicle_label": "2022 Freightliner Cascadia 126 — TXK-4821",
        "total_quantity_l": 1820.3,
        "total_cost_usd": 1981.91,
        "distance_km": 5340.2,
        "fuel_economy_lper100km": 34.1
      }
    ]
  }
}
```

---

## Incidents

### `GET /incidents`

List incidents for the fleet.

**Query Parameters:** `vehicle_id`, `driver_id`, `incident_type`, `severity`, `status`, `occurred_at_gte`, `occurred_at_lte`, `sort` (default: `-occurred_at`)

---

### `POST /incidents`

Report a new incident.

**Request Body:**

```json
{
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
  "incident_type": "collision",
  "severity": "moderate",
  "occurred_at": "2024-07-15T11:22:00Z",
  "location_lat": 30.4515,
  "location_lng": -95.4918,
  "location_address": "I-45 N MM 102, Montgomery County, TX",
  "description": "Rear-end collision at low speed during traffic stop. Minor rear bumper damage. No injuries. Other vehicle involved: 2019 Toyota Camry, TX plate PNX-2214.",
  "injuries_reported": false,
  "property_damage": true,
  "damage_description": "Rear ICC bar and lower bumper fairing. Estimated 8-10 panel dents.",
  "police_report_number": "MCI-2024-071500882",
  "estimated_damage_cost": 3200.00
}
```

**Response `201 Created`:** Full incident object with `status: "reported"`.

---

### `GET /incidents/{id}`

Retrieve a single incident with full details.

---

### `PUT /incidents/{id}`

Update incident details. Status transitions: `reported → under_review → investigation → resolved → closed`.

---

### `POST /incidents/{id}/report`

Submit a written report for an incident.

**Request Body:**

```json
{
  "report_type": "initial",
  "content": "At approximately 11:22 AM on July 15, 2024, Unit #18 (TXK-4821) was operating northbound on I-45 near mile marker 102 in Montgomery County, TX. Traffic slowed unexpectedly due to a construction merge. The driver applied brakes and came to a near stop when the following vehicle, a 2019 Toyota Camry (TX PNX-2214), struck the rear of Unit #18. Impact speed estimated at 15 mph. Driver Marcus Torres reported no injuries. Police were on scene within 22 minutes. Report #MCI-2024-071500882 was issued."
}
```

---

### `POST /incidents/{id}/documents`

Attach a document to an incident (photos, police report PDF, insurance correspondence). Same shape as vehicle document upload.

---

## Routes

### `GET /routes`

List saved routes for the fleet.

---

### `POST /routes`

Save a new route (pre-computed or manually defined).

**Request Body:**

```json
{
  "name": "Houston Port → Dallas Commerce",
  "origin_address": "1200 Port of Houston Dr, Houston, TX 77029",
  "origin_lat": 29.7283,
  "origin_lng": -95.2735,
  "destination_address": "3801 W Commerce St, Dallas, TX 75212",
  "destination_lat": 32.7767,
  "destination_lng": -96.8330,
  "waypoints_json": [
    { "seq": 1, "address": "I-45 N Rest Area, Huntsville, TX", "lat": 30.7135, "lng": -95.5498 }
  ],
  "optimization_criteria": "fastest"
}
```

**Response `201 Created`:** Route object. If `optimization_criteria` is provided, the system calls the routing provider to compute `distance_km`, `estimated_duration_minutes`, `estimated_fuel_l`, and `polyline_encoded`.

---

### `GET /routes/{id}`

Retrieve a route by ID.

---

### `PUT /routes/{id}`

Update route details or re-trigger optimization.

---

### `DELETE /routes/{id}`

Delete a route. Routes associated with future-scheduled trips cannot be deleted.

---

### `POST /routes/optimize`

Request route optimization for a new trip without saving the route.

**Request Body:**

```json
{
  "origin_lat": 29.7283,
  "origin_lng": -95.2735,
  "destination_lat": 32.7767,
  "destination_lng": -96.8330,
  "waypoints": [
    { "lat": 30.7135, "lng": -95.5498 }
  ],
  "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
  "optimization_criteria": "fuel_efficient",
  "departure_time": "2024-07-16T06:00:00Z"
}
```

**Response `200 OK`:**

```json
{
  "data": {
    "distance_km": 398.7,
    "estimated_duration_minutes": 289,
    "estimated_fuel_l": 136.0,
    "estimated_toll_cost": 3.25,
    "polyline_encoded": "mfn_Dvu{pNuAaBiCgE...",
    "provider": "google_maps",
    "optimized_at": "2024-07-15T14:30:01Z"
  }
}
```

---

## Reports

### `GET /reports/fleet-summary`

High-level KPI summary for the fleet over a date range.

**Query Parameters:** `start_date`, `end_date`

**Response `200 OK`:**

```json
{
  "data": {
    "period": { "start": "2024-07-01", "end": "2024-07-15" },
    "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
    "active_vehicles": 48,
    "active_drivers": 61,
    "total_trips": 743,
    "total_km_driven": 284320.4,
    "total_fuel_l": 97420.8,
    "total_fuel_cost_usd": 106089.07,
    "total_maintenance_cost_usd": 18440.00,
    "avg_driver_score": 88.4,
    "incidents": { "total": 2, "minor": 1, "moderate": 1, "severe": 0, "critical": 0 },
    "utilization_rate_pct": 78.4,
    "on_time_delivery_pct": 94.2
  }
}
```

---

### `GET /reports/driver-performance`

Driver performance rankings and scoring breakdown.

**Query Parameters:** `start_date`, `end_date`, `limit` (default 25), `sort` (`-overall_score` | `-total_km`)

---

### `GET /reports/fuel-consumption`

Detailed fuel consumption report by vehicle, driver, or time period. Equivalent to `GET /reports/fuel-analytics`.

---

### `GET /reports/maintenance-costs`

Maintenance cost breakdown by vehicle, type, and time period.

**Query Parameters:** `start_date`, `end_date`, `vehicle_id`, `maintenance_type`, `group_by` (`vehicle` | `type` | `month`)

**Response `200 OK`:**

```json
{
  "data": {
    "period": { "start": "2024-01-01", "end": "2024-06-30" },
    "total_cost_usd": 124880.00,
    "total_records": 312,
    "breakdown_by_type": [
      { "maintenance_type": "oil_change",    "count": 96,  "total_cost_usd": 19584.00 },
      { "maintenance_type": "tire_rotation", "count": 48,  "total_cost_usd": 9600.00  },
      { "maintenance_type": "brake_service", "count": 22,  "total_cost_usd": 28160.00 },
      { "maintenance_type": "dot_inspection","count": 48,  "total_cost_usd": 9600.00  },
      { "maintenance_type": "emergency",     "count": 8,   "total_cost_usd": 32480.00 }
    ]
  }
}
```

---

### `GET /reports/ifta/{year}/{quarter}`

Generate or retrieve the IFTA quarterly report for the fleet.

**Path Parameters:** `year` (e.g., `2024`), `quarter` (`1`–`4`)

**Response `200 OK`:**

```json
{
  "data": {
    "id": "r1s2t3u4-v5w6-7x8y-9z0a-b1c2d3e4f5g6",
    "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
    "report_year": 2024,
    "report_quarter": 2,
    "status": "draft",
    "total_miles": 178420.3,
    "total_gallons": 60882.1,
    "jurisdiction_data": [
      { "state": "TX", "miles": 142380.0, "gallons": 48573.2, "tax_rate": 0.20, "tax_owed": 9714.64 },
      { "state": "LA", "miles": 21840.2,  "gallons": 7452.1,  "tax_rate": 0.20, "tax_owed": 1490.42 },
      { "state": "OK", "miles": 14200.1,  "gallons": 4856.8,  "tax_rate": 0.19, "tax_owed": 922.79  }
    ],
    "generated_at": "2024-07-15T14:00:00Z",
    "file_path": null
  }
}
```

---

## Alerts & Alert Rules

### `GET /alerts`

List recent alert notifications for the fleet.

**Query Parameters:** `acknowledged` (boolean), `alert_type`, `vehicle_id`, `driver_id`, `start_time_gte`, `start_time_lte`, `limit`, `cursor`

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
      "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
      "alert_type": "geofence_exit",
      "severity": "warning",
      "title": "Vehicle exited restricted zone",
      "message": "Unit #18 (TXK-4821) exited 'Dallas Distribution Center' at 13:52 UTC without an active trip assigned.",
      "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
      "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
      "reference_id": "g1h2i3j4-k5l6-7m8n-9o0p-q1r2s3t4u5v6",
      "reference_type": "geofence_event",
      "acknowledged": false,
      "created_at": "2024-07-15T13:52:05Z"
    }
  ],
  "meta": { "total": 12, "limit": 25, "has_more": false, "next_cursor": null }
}
```

---

### `PUT /alerts/{id}/acknowledge`

Acknowledge an alert, optionally with a note.

**Request Body:**

```json
{
  "note": "Confirmed with driver — authorized yard exit for wash. No action needed."
}
```

**Response `200 OK`:** Updated alert with `acknowledged: true` and `acknowledged_at` timestamp.

---

### `GET /alert-rules`

List configured alert rules for the fleet.

**Response `200 OK`:**

```json
{
  "data": [
    {
      "id": "rule-uuid-1",
      "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
      "name": "Speeding Alert",
      "alert_type": "speeding",
      "active": true,
      "conditions": {
        "speed_threshold_kmh": 120,
        "duration_seconds": 30
      },
      "notification_channels": ["email", "push", "sms"],
      "recipients": ["dispatch@acmelogistics.com"],
      "cooldown_minutes": 15,
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

---

### `POST /alert-rules`

Create a new alert rule.

**Request Body:**

```json
{
  "name": "License Expiry Warning",
  "alert_type": "driver_license_expiring",
  "active": true,
  "conditions": {
    "days_before_expiry": 30
  },
  "notification_channels": ["email"],
  "recipients": ["fleet-admin@acmelogistics.com", "hr@acmelogistics.com"],
  "cooldown_minutes": 1440
}
```

**Supported `alert_type` values:**

| Type | Description |
|---|---|
| `speeding` | Vehicle exceeds speed threshold for sustained duration |
| `geofence_enter` | Vehicle enters a defined geofence zone |
| `geofence_exit` | Vehicle exits a defined geofence zone |
| `geofence_dwell` | Vehicle dwells in geofence beyond configured threshold |
| `harsh_braking` | Deceleration exceeds 0.4g |
| `harsh_acceleration` | Acceleration exceeds 0.4g |
| `idle_duration` | Engine idle exceeds N minutes at a stop |
| `low_driver_score` | Driver score drops below threshold |
| `maintenance_due` | Maintenance is due within N days or N km |
| `fuel_anomaly` | Flagged fuel transaction detected |
| `driver_license_expiring` | CDL expires within N days |
| `vehicle_insurance_expiring` | Insurance policy expires within N days |
| `vehicle_registration_expiring` | Registration expires within N days |
| `incident_reported` | New incident is filed in the fleet |
| `hos_violation` | Driver exceeds HOS driving or on-duty limits |

---

### `PUT /alert-rules/{id}`

Update an existing alert rule (conditions, channels, active status).

---

## Webhook Events

Webhooks deliver real-time event notifications to your configured endpoint via HTTP POST with the following envelope:

```json
{
  "event_id": "evt_3k9m2n1p4q5r6s7t",
  "event_type": "trip.completed",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T13:45:02Z",
  "data": { ... }
}
```

Delivery is at-least-once. Each request includes an `X-FleetManager-Signature` header (HMAC-SHA256 of the raw body using your webhook secret) for verification.

### Supported Event Types

| Event Type | Triggered When |
|---|---|
| `trip.created` | A new trip is scheduled |
| `trip.started` | A trip transitions to `in_progress` |
| `trip.completed` | A trip transitions to `completed` |
| `trip.cancelled` | A trip is cancelled |
| `vehicle.status_changed` | Vehicle status changes |
| `geofence.entered` | A vehicle enters a geofence zone |
| `geofence.exited` | A vehicle exits a geofence zone |
| `geofence.dwell_exceeded` | Vehicle exceeds dwell threshold |
| `maintenance.due` | A maintenance record becomes due |
| `maintenance.completed` | A maintenance record is marked complete |
| `incident.reported` | A new incident is filed |
| `incident.status_changed` | Incident status changes |
| `fuel.flagged` | A fuel transaction is auto-flagged |
| `driver.license_expiring` | Driver CDL within 30 days of expiry |
| `driver.score_updated` | Driver score recalculated after trip |
| `alert.triggered` | Any configured alert rule fires |

### Example: `trip.completed` Payload

```json
{
  "event_id": "evt_3k9m2n1p4q5r6s7t",
  "event_type": "trip.completed",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T13:45:02Z",
  "data": {
    "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "distance_km": 394.2,
    "duration_minutes": 452,
    "fuel_consumed_l": 138.4,
    "driver_score": 94.5,
    "end_time": "2024-07-15T13:44:00Z"
  }
}
```

### Example: `geofence.exited` Payload

```json
{
  "event_id": "evt_7x8y9z0a1b2c3d4e",
  "event_type": "geofence.exited",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T13:52:04Z",
  "data": {
    "geofence_event_id": "g1h2i3j4-k5l6-7m8n-9o0p-q1r2s3t4u5v6",
    "geofence_zone_id": "z9y8x7w6-v5u4-3t2s-1r0q-p9o8n7m6l5k4",
    "geofence_zone_name": "Dallas Distribution Center",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "trip_id": null,
    "location_lat": 32.7791,
    "location_lng": -96.8003,
    "occurred_at": "2024-07-15T13:52:00Z"
  }
}
```

### Example: `incident.reported` Payload

```json
{
  "event_id": "evt_2f3g4h5i6j7k8l9m",
  "event_type": "incident.reported",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T11:25:44Z",
  "data": {
    "incident_id": "i1j2k3l4-m5n6-7o8p-9q0r-s1t2u3v4w5x6",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "incident_type": "collision",
    "severity": "moderate",
    "occurred_at": "2024-07-15T11:22:00Z",
    "location_address": "I-45 N MM 102, Montgomery County, TX",
    "injuries_reported": false,
    "property_damage": true,
    "estimated_damage_cost": 3200.00
  }
}
```

### Example: `maintenance.due` Payload

```json
{
  "event_id": "evt_9n0o1p2q3r4s5t6u",
  "event_type": "maintenance.due",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T06:00:00Z",
  "data": {
    "maintenance_record_id": "m1n2o3p4-q5r6-7s8t-9u0v-w1x2y3z4a5b6",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "maintenance_type": "oil_change",
    "scheduled_date": "2024-07-20",
    "days_until_due": 5,
    "current_odometer_km": 49100.0,
    "next_service_km": 50000.0,
    "km_until_due": 900.0
  }
}
```

### Example: `alert.triggered` Payload

```json
{
  "event_id": "evt_5v6w7x8y9z0a1b2c",
  "event_type": "alert.triggered",
  "api_version": "2024-07-01",
  "fleet_id": "a82b1c3d-9e4f-4a2b-8c1d-0f5e6a7b8c9d",
  "created_at": "2024-07-15T09:18:32Z",
  "data": {
    "alert_id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
    "alert_rule_id": "rule-uuid-1",
    "alert_type": "speeding",
    "severity": "warning",
    "vehicle_id": "11bf5b37-e0b8-42e0-8dcf-dc8c4aefc000",
    "driver_id": "b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e",
    "trip_id": "c8e3a1f0-2d4b-4e6f-a8b0-1c2d3e4f5a6b",
    "details": {
      "speed_kmh": 127.4,
      "threshold_kmh": 120,
      "duration_seconds": 45,
      "location_lat": 30.2415,
      "location_lng": -95.4622
    }
  }
}
```

---

## Error Reference

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of what went wrong.",
    "details": { "field": "value" }
  }
}
```

### HTTP Status Codes

| HTTP | Meaning |
|---|---|
| 200 | Success |
| 201 | Resource created |
| 202 | Request accepted (async processing) |
| 204 | Success, no content |
| 400 | Malformed request (missing required field, bad JSON) |
| 401 | Authentication required or token expired |
| 403 | Authenticated but insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate, invalid state transition) |
| 413 | Payload too large |
| 422 | Validation failure (business rule violation) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service temporarily unavailable |

### Error Code Reference

| Code | HTTP | Description |
|---|---|---|
| `VEHICLE_NOT_FOUND` | 404 | Vehicle ID does not exist or is deleted |
| `VEHICLE_VIN_CONFLICT` | 409 | VIN already registered |
| `VEHICLE_PLATE_CONFLICT` | 409 | License plate + state already registered |
| `VEHICLE_VIN_INVALID` | 422 | VIN fails format validation |
| `VEHICLE_IN_ACTIVE_TRIP` | 409 | Cannot delete/modify vehicle during active trip |
| `VEHICLE_OUT_OF_SERVICE` | 422 | Vehicle status prevents the requested operation |
| `FLEET_VEHICLE_LIMIT_REACHED` | 403 | Subscription cap on active vehicles exceeded |
| `DRIVER_NOT_FOUND` | 404 | Driver ID does not exist or is deleted |
| `DRIVER_LICENSE_CONFLICT` | 409 | License number + state combination already registered |
| `DRIVER_EMPLOYEE_ID_CONFLICT` | 409 | Employee ID already in use within this fleet |
| `DRIVER_LICENSE_EXPIRED` | 422 | Driver CDL is past expiry date — dispatch blocked |
| `DRIVER_ALREADY_DISPATCHED` | 409 | Driver is already in an active trip |
| `FLEET_DRIVER_LIMIT_REACHED` | 403 | Subscription cap on active drivers exceeded |
| `TRIP_NOT_FOUND` | 404 | Trip ID does not exist |
| `TRIP_INVALID_STATUS_TRANSITION` | 422 | Requested status transition is not allowed |
| `VEHICLE_ALREADY_DISPATCHED` | 409 | Vehicle is already in an active trip |
| `GEOFENCE_NOT_FOUND` | 404 | Geofence zone ID does not exist |
| `GEOFENCE_NAME_CONFLICT` | 409 | A geofence with this name already exists in the fleet |
| `MAINTENANCE_RECORD_NOT_FOUND` | 404 | Maintenance record ID does not exist |
| `FUEL_RECORD_NOT_FOUND` | 404 | Fuel record ID does not exist |
| `INCIDENT_NOT_FOUND` | 404 | Incident ID does not exist |
| `ROUTE_NOT_FOUND` | 404 | Route ID does not exist |
| `PING_BATCH_TOO_LARGE` | 413 | Ping batch exceeds 500-item limit |
| `PING_TIMESTAMP_TOO_OLD` | 422 | Ping timestamp is more than 24 hours in the past |
| `UNAUTHORIZED` | 401 | Missing, expired, or invalid token |
| `FORBIDDEN` | 403 | Token does not have permission for this resource |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests — see `X-RateLimit-Reset` header |
| `INTERNAL_ERROR` | 500 | Unexpected server error — contact support with `request_id` |
