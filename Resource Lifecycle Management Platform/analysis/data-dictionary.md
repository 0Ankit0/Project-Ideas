# Data Dictionary

Canonical definitions for every significant entity, attribute, and value type used within the **Resource Lifecycle Management Platform**. All services and integrations MUST use these definitions as the single source of truth for field names, types, and constraints.

---

## Core Entities

### Resource

The central tracked object. Can represent a physical asset (laptop, vehicle, tool), a virtual asset (cloud license, IP block), or a space (meeting room, lab bench).

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `resource_id` | UUID v4 | Required, immutable, unique | Globally unique identifier assigned at provisioning |
| `tenant_id` | UUID v4 | Required, immutable | Owner organization / tenant |
| `category` | Enum | Required | One of: `EQUIPMENT`, `VEHICLE`, `SPACE`, `LICENSE`, `TOOL`, `CONSUMABLE` |
| `asset_tag` | String(64) | Required, unique per tenant | Physical or logical tag (barcode, QR, RFID) |
| `serial_number` | String(128) | Optional | Manufacturer serial number |
| `name` | String(255) | Required | Human-readable display name |
| `description` | Text | Optional | Detailed description of the resource |
| `condition_grade` | Enum | Required | One of: `A` (new/excellent), `B` (good), `C` (fair), `D` (poor) |
| `condition_notes` | Text | Optional | Free-text condition remarks |
| `location_id` | UUID v4 | Required | Physical or logical location reference |
| `cost_centre` | String(64) | Required | Accounting cost-centre code |
| `acquisition_cost` | Decimal(12,2) | Optional | Original acquisition cost in `currency` |
| `currency` | ISO 4217(3) | Conditional | Required when `acquisition_cost` is set |
| `policy_profile_id` | UUID v4 | Required | Points to the active allocation policy profile |
| `state` | Enum | Required | Current lifecycle state (see State Machine) |
| `created_at` | ISO 8601 UTC | Immutable | Record creation timestamp |
| `updated_at` | ISO 8601 UTC | System-managed | Last modification timestamp |
| `version` | Integer | Required | Optimistic-lock version counter |

---

### Reservation

A time-bound hold on a resource before physical/logical checkout.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `reservation_id` | UUID v4 | Required, immutable | Unique reservation identifier |
| `resource_id` | UUID v4 | Required, FK → Resource | The reserved resource |
| `requestor_id` | UUID v4 | Required | User or system requesting the resource |
| `tenant_id` | UUID v4 | Required | Tenant context |
| `start_at` | ISO 8601 UTC | Required | Window start (inclusive) |
| `end_at` | ISO 8601 UTC | Required | Window end (inclusive); must be > `start_at` |
| `priority` | Integer(1–10) | Required, default 5 | Higher value = higher priority |
| `state` | Enum | Required | One of: `PENDING`, `CONFIRMED`, `CANCELLED`, `EXPIRED`, `CONVERTED` |
| `idempotency_key` | String(128) | Required, unique per tenant | Client-supplied key for duplicate-safe creation |
| `sla_due_at` | ISO 8601 UTC | System-managed | Computed SLA deadline for checkout |
| `cancellation_reason` | String(255) | Optional | Reason code when cancelled |
| `created_at` | ISO 8601 UTC | Immutable | — |

---

### Allocation

Active custody record; created when a reservation transitions to checkout.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `allocation_id` | UUID v4 | Required, immutable | Unique allocation identifier |
| `reservation_id` | UUID v4 | Optional, FK → Reservation | Source reservation (null for direct allocation) |
| `resource_id` | UUID v4 | Required, FK → Resource | The allocated resource |
| `custodian_id` | UUID v4 | Required | User currently holding custody |
| `tenant_id` | UUID v4 | Required | — |
| `checkout_at` | ISO 8601 UTC | Required | Actual checkout timestamp |
| `due_at` | ISO 8601 UTC | Required | Agreed return deadline |
| `checkin_at` | ISO 8601 UTC | Optional | Actual check-in timestamp; null = still allocated |
| `checkout_condition` | Enum (A–D) | Required | Condition grade recorded at checkout |
| `checkin_condition` | Enum (A–D) | Optional | Condition grade recorded at check-in |
| `condition_delta` | Enum | Computed | `NONE`, `MINOR`, `MAJOR`, `LOSS`; drives settlement |
| `state` | Enum | Required | `ACTIVE`, `OVERDUE`, `RETURNED`, `LOST`, `FORCED_RETURN` |
| `extended_count` | Integer | Default 0 | Number of extension grants |
| `created_at` | ISO 8601 UTC | Immutable | — |

---

### Policy Profile

Governs reservation and allocation behaviour for a resource category or individual resource.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `policy_profile_id` | UUID v4 | Required, immutable | — |
| `name` | String(128) | Required | Human-readable profile name |
| `max_duration_hours` | Integer | Required | Maximum allowed allocation window in hours |
| `max_extensions` | Integer | Default 1 | Maximum extension grants per allocation |
| `extension_max_hours` | Integer | Required | Maximum hours per extension |
| `quota_per_requestor` | Integer | Required | Concurrent allocation limit per requestor |
| `quota_per_tenant` | Integer | Required | Concurrent allocation limit per tenant |
| `eligible_roles` | String[] | Required | List of roles allowed to request this resource |
| `priority_rules` | JSON | Optional | Priority scoring rules (role-based or attribute-based) |
| `deposit_rate_card_id` | UUID v4 | Optional | Linked deposit/damage rate card |
| `is_active` | Boolean | Required | Whether this profile is currently enforced |
| `version` | Integer | Required | Policy version for audit traceability |
| `created_at` | ISO 8601 UTC | Immutable | — |

---

### Incident Case

Opened when a condition delta, overdue breach, or loss event is detected.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `case_id` | UUID v4 | Required, immutable | Unique case identifier |
| `resource_id` | UUID v4 | Required, FK → Resource | Affected resource |
| `allocation_id` | UUID v4 | Optional, FK → Allocation | Linked allocation |
| `case_type` | Enum | Required | `CONDITION_DISPUTE`, `OVERDUE`, `LOSS`, `THEFT`, `MAINTENANCE` |
| `severity` | Enum | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `state` | Enum | Required | `OPEN`, `IN_REVIEW`, `PENDING_SETTLEMENT`, `RESOLVED`, `CLOSED` |
| `owner_id` | UUID v4 | Required | User responsible for resolving the case |
| `sla_due_at` | ISO 8601 UTC | Required | Resolution SLA deadline |
| `description` | Text | Required | Description of the incident |
| `resolution_notes` | Text | Optional | Resolution summary |
| `created_at` | ISO 8601 UTC | Immutable | — |
| `resolved_at` | ISO 8601 UTC | Optional | Timestamp of resolution |

---

### Settlement Record

Financial record associated with an incident case.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `settlement_id` | UUID v4 | Required, immutable | — |
| `case_id` | UUID v4 | Required, FK → Incident Case | — |
| `allocation_id` | UUID v4 | Required, FK → Allocation | — |
| `charge_type` | Enum | Required | `DAMAGE`, `LOSS`, `OVERDUE_FEE`, `DEPOSIT_RELEASE` |
| `amount` | Decimal(12,2) | Required | Charge or refund amount |
| `currency` | ISO 4217(3) | Required | — |
| `rate_card_id` | UUID v4 | Required | Rate card version used for computation |
| `state` | Enum | Required | `PENDING`, `DISPUTED`, `APPROVED`, `POSTED`, `VOIDED` |
| `ledger_event_id` | UUID v4 | Optional | Reference to downstream ledger event |
| `created_at` | ISO 8601 UTC | Immutable | — |

---

### Audit Event

Immutable log entry for every state-changing operation.

| Attribute | Type | Constraints | Description |
|---|---|---|---|
| `audit_id` | UUID v4 | Required, immutable | — |
| `resource_id` | UUID v4 | Optional | Affected resource (if applicable) |
| `entity_type` | String(64) | Required | `RESOURCE`, `RESERVATION`, `ALLOCATION`, `INCIDENT`, etc. |
| `entity_id` | UUID v4 | Required | Primary key of the affected entity |
| `command` | String(128) | Required | Command name (e.g., `CHECKOUT`, `CANCEL_RESERVATION`) |
| `actor_id` | UUID v4 | Required | Identity of the user or system issuing the command |
| `correlation_id` | UUID v4 | Required | Request correlation ID |
| `reason_code` | String(64) | Optional | Machine-readable reason for the action |
| `before_state` | JSON | Optional | Entity state snapshot before the command |
| `after_state` | JSON | Optional | Entity state snapshot after the command |
| `timestamp` | ISO 8601 UTC | Immutable | When the event was written |
| `hash` | String(64) | Computed | SHA-256 of concatenated `(prev_hash + payload)` for chain integrity |

---

## Value Type Definitions

| Type Name | Format | Example |
|---|---|---|
| `UUID v4` | `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` | `a1b2c3d4-e5f6-4789-abcd-0123456789ab` |
| `ISO 8601 UTC` | `YYYY-MM-DDTHH:mm:ssZ` | `2025-06-15T09:30:00Z` |
| `ISO 4217(3)` | Three-letter currency code | `USD`, `EUR`, `GBP` |
| `Condition Grade` | Single character `A`–`D` | `B` |
| `Decimal(m,n)` | m total digits, n decimal places | `1234.56` |

---

## Cross-References

- ERD with table relationships: [../detailed-design/erd-database-schema.md](../detailed-design/erd-database-schema.md)
- Event payload schemas: [event-catalog.md](./event-catalog.md)
- API request/response schemas: [../detailed-design/api-design.md](../detailed-design/api-design.md)
