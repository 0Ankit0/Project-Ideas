# ERD / Database Schema - Slot Booking System

> **Platform Independence**: Schema uses standard SQL types adaptable to PostgreSQL, MySQL, or other RDBMS.

---

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ bookings : makes
    users ||--o{ reviews : writes
    users ||--o{ payments : initiates
    users ||--o| providers : becomes
    users ||--o{ notification_preferences : has
    users ||--o{ audit_logs : performs
    users ||--o{ idempotency_keys : owns
    
    providers ||--|{ resources : owns
    providers ||--o{ payouts : receives
    
    resources ||--|{ slots : has
    resources ||--o{ reviews : receives
    resources ||--|{ resource_images : has
    resources }|--|| categories : belongs_to
    
    slots ||--o| bookings : reserved_by
    bookings ||--|| payments : paid_with
    payments ||--o| refunds : has
    bookings ||--o{ booking_events : emits
    payments ||--o{ webhook_events : receives
    
    users {
        uuid id PK
        varchar email UK
        varchar phone
        varchar password_hash
        varchar name
        enum role
        enum status
        timestamp created_at
    }
    
    providers {
        uuid id PK
        uuid user_id FK
        varchar business_name
        enum status
        jsonb bank_details
    }
    
    resources {
        uuid id PK
        uuid provider_id FK
        uuid category_id FK
        varchar name
        text description
        decimal base_price
        enum status
        jsonb location
    }
    
    slots {
        uuid id PK
        uuid resource_id FK
        timestamp start_time
        timestamp end_time
        decimal price
        enum status
    }
    
    bookings {
        uuid id PK
        varchar booking_number UK
        uuid user_id FK
        uuid resource_id FK
        enum status
        decimal total_amount
        timestamp booked_at
    }
    
    payments {
        uuid id PK
        uuid booking_id FK
        decimal amount
        enum method
        enum status
        varchar gateway_txn_id
    }
    
    refunds {
        uuid id PK
        uuid payment_id FK
        decimal amount
        enum status
    }
    
    reviews {
        uuid id PK
        uuid user_id FK
        uuid resource_id FK
        int rating
        text comment
    }

    notification_preferences {
        uuid id PK
        uuid user_id FK
        boolean email_enabled
        boolean sms_enabled
        boolean push_enabled
        jsonb quiet_hours
    }

    booking_events {
        uuid id PK
        uuid booking_id FK
        varchar type
        jsonb payload
        timestamp created_at
    }

    webhook_events {
        uuid id PK
        uuid payment_id FK
        varchar provider_event_id
        varchar event_type
        jsonb payload
        timestamp received_at
    }

    audit_logs {
        uuid id PK
        uuid actor_id FK
        varchar action
        jsonb metadata
        timestamp created_at
    }

    idempotency_keys {
        uuid id PK
        uuid user_id FK
        varchar idempotency_key
        varchar endpoint
        varchar request_hash
        varchar status
        jsonb response_snapshot
        timestamp created_at
        timestamp expires_at
    }
```

---

## Core Table Definitions

### `users`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| phone | VARCHAR(20) | UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| role | ENUM | 'user','provider','admin' |
| status | ENUM | 'pending','active','suspended' |
| created_at | TIMESTAMP | DEFAULT NOW() |

### `providers`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | FK → users, UNIQUE |
| business_name | VARCHAR(255) | NOT NULL |
| status | ENUM | 'pending','approved','rejected' |
| bank_details | JSONB | |
| verified_at | TIMESTAMP | |

### `resources`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| provider_id | UUID | FK → providers |
| category_id | UUID | FK → categories |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| capacity | INT | DEFAULT 1 |
| base_price | DECIMAL(10,2) | NOT NULL |
| status | ENUM | 'draft','active','inactive' |
| location | JSONB | {address, lat, lng} |
| slot_duration_minutes | INT | DEFAULT 60 |

### `slots`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| resource_id | UUID | FK → resources |
| start_time | TIMESTAMP | NOT NULL |
| end_time | TIMESTAMP | NOT NULL |
| price | DECIMAL(10,2) | NOT NULL |
| status | ENUM | 'available','locked','booked','blocked' |
| locked_by | UUID | FK → users |
| locked_until | TIMESTAMP | |

### `bookings`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| booking_number | VARCHAR(20) | UNIQUE |
| user_id | UUID | FK → users |
| resource_id | UUID | FK → resources |
| status | ENUM | 'pending','confirmed','cancelled','completed' |
| total_amount | DECIMAL(10,2) | NOT NULL |
| discount_amount | DECIMAL(10,2) | DEFAULT 0 |
| notes | TEXT | |
| booked_at | TIMESTAMP | |
| cancelled_at | TIMESTAMP | |

### `payments`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| booking_id | UUID | FK → bookings |
| amount | DECIMAL(10,2) | NOT NULL |
| method | ENUM | 'card','wallet','upi' |
| status | ENUM | 'pending','completed','failed','refunded' |
| gateway_txn_id | VARCHAR(255) | |
| paid_at | TIMESTAMP | |

### `refunds`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| payment_id | UUID | FK → payments |
| amount | DECIMAL(10,2) | NOT NULL |
| reason | TEXT | |
| status | ENUM | 'pending','completed','failed' |
| refunded_at | TIMESTAMP | |

---

## Supporting Tables

### `categories`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| name | VARCHAR(100) | NOT NULL |
| slug | VARCHAR(100) | UNIQUE |
| parent_id | UUID | FK → categories |

### `amenities` & `resource_amenities`
```sql
-- Many-to-many relationship
CREATE TABLE resource_amenities (
    resource_id UUID REFERENCES resources(id),
    amenity_id UUID REFERENCES amenities(id),
    PRIMARY KEY (resource_id, amenity_id)
);
```

### `reviews`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | FK → users |
| resource_id | UUID | FK → resources |
| booking_id | UUID | FK → bookings |
| rating | INT | 1-5 |
| comment | TEXT | |
| provider_response | TEXT | |

### `promo_codes`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| code | VARCHAR(50) | UNIQUE |
| discount_type | ENUM | 'percentage','fixed' |
| discount_value | DECIMAL | |
| valid_from | TIMESTAMP | |
| valid_to | TIMESTAMP | |
| is_active | BOOLEAN | |

### `notification_preferences`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | FK → users |
| email_enabled | BOOLEAN | DEFAULT true |
| sms_enabled | BOOLEAN | DEFAULT false |
| push_enabled | BOOLEAN | DEFAULT true |
| quiet_hours | JSONB | |

### `booking_events`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| booking_id | UUID | FK → bookings |
| type | VARCHAR(50) | NOT NULL |
| payload | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |

### `webhook_events`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| payment_id | UUID | FK → payments |
| provider_event_id | VARCHAR(255) | UNIQUE |
| event_type | VARCHAR(100) | NOT NULL |
| payload | JSONB | |
| received_at | TIMESTAMP | DEFAULT NOW() |

### `audit_logs`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| actor_id | UUID | FK → users |
| action | VARCHAR(100) | NOT NULL |
| metadata | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |

### `idempotency_keys`
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | FK → users |
| idempotency_key | VARCHAR(64) | NOT NULL |
| endpoint | VARCHAR(255) | NOT NULL |
| request_hash | VARCHAR(64) | NOT NULL |
| status | VARCHAR(20) | NOT NULL |
| response_snapshot | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| expires_at | TIMESTAMP | |

---

## Key Indexes

```sql
-- Performance indexes
CREATE INDEX idx_slots_search ON slots(resource_id, start_time, status);
CREATE INDEX idx_bookings_user ON bookings(user_id, status);
CREATE INDEX idx_resources_provider ON resources(provider_id);
CREATE INDEX idx_payments_booking ON payments(booking_id);
```

---

## Enum Definitions

| Enum | Values |
|------|--------|
| user_role | guest, user, provider, admin |
| user_status | pending, active, suspended, deleted |
| provider_status | pending, approved, rejected, suspended |
| resource_status | draft, pending_review, active, inactive |
| slot_status | available, locked, booked, blocked, completed |
| booking_status | pending, confirmed, cancelled, completed, no_show |
| payment_status | pending, processing, completed, failed, refunded |
| payment_method | card, wallet, upi, bank_transfer |

---
## Implementation-Ready Erd Database Schema

### Slot allocation rules in this document's context
- Allocation decisions must be based on **resource calendar + operational policy + channel limits** before any payment action is attempted.
- All provisional allocations require an explicit **hold record with expiry**, and expiry must be visible to clients.
- Shared-capacity resources must use atomic decrement semantics; exclusive resources must enforce single-active-booking constraints.

### Conflict resolution in this document's context
- Competing writes must use deterministic conflict handling (optimistic version checks or transactional locks as documented here).
- API and admin paths must converge on one canonical conflict reason taxonomy (`SLOT_TAKEN`, `STALE_VERSION`, `PROVIDER_BLOCKED`, `PAYMENT_STATE_MISMATCH`).
- Every conflict rejection must emit structured audit telemetry including actor, correlation ID, and rule version.

### Payment coupling / decoupling behavior
- **Coupled flow**: booking moves to confirmed only after successful authorization/capture.
- **Decoupled flow**: booking can be confirmed with `PAYMENT_PENDING`, but with a bounded grace window and auto-cancel guardrail.
- Compensation is mandatory for split-brain outcomes (payment succeeded but booking failed, or inverse).

### Cancellation and refund policy detail
- Refund outcomes depend on lead time, policy tier, no-show status, and jurisdiction-specific fee constraints.
- Refund processing must be idempotent and expose lifecycle states (`REQUESTED`, `INITIATED`, `SETTLED`, `FAILED`, `MANUAL_REVIEW`).
- Cancellation side effects must include slot reallocation and downstream notification consistency.

### Observability and incident playbook focus
- Monitor: availability latency, hold expiry lag, conflict rate, payment callback success, refund aging.
- Alerts must map to operator runbooks with first-response steps and data reconciliation queries.
- Post-incident review must record policy gaps and required control changes for this documentation area.

### Detailed implementation contracts
- Transaction boundaries for hold, confirm, cancel, and refund actions.
- Outbox/inbox idempotency strategy for webhook and event replay safety.
- Data model constraints and indexes required to prevent overlap anomalies.


### Mermaid ERD for operational entities
```mermaid
erDiagram
  SLOT ||--o{ HOLD : allocates
  SLOT ||--o{ BOOKING : booked_as
  BOOKING ||--o{ PAYMENT_TXN : charged_by
  BOOKING ||--o{ REFUND_CASE : refunded_by
  HOLD {
    uuid id PK
    uuid slot_id FK
    timestamptz expires_at
    text status
  }
  REFUND_CASE {
    uuid id PK
    uuid booking_id FK
    text status
    numeric amount
  }
```
