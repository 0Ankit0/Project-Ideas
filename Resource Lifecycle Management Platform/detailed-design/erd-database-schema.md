# ERD Database Schema

Complete entity-relationship diagram and table definitions for the **Resource Lifecycle Management Platform** PostgreSQL primary datastore.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
  TENANT {
    uuid tenant_id PK
    string name
    string plan
    timestamp created_at
  }

  LOCATION {
    uuid location_id PK
    uuid tenant_id FK
    string name
    string building
    string floor
    string zone
    decimal lat
    decimal lng
  }

  POLICY_PROFILE {
    uuid policy_profile_id PK
    uuid tenant_id FK
    string name
    int max_duration_hours
    int max_extensions
    int extension_max_hours
    int quota_per_requestor
    int quota_per_tenant
    jsonb eligible_roles
    jsonb priority_rules
    uuid deposit_rate_card_id
    boolean is_active
    int version
    timestamp created_at
  }

  RESOURCE {
    uuid resource_id PK
    uuid tenant_id FK
    string category
    string asset_tag
    string serial_number
    string name
    text description
    varchar condition_grade
    text condition_notes
    uuid location_id FK
    string cost_centre
    decimal acquisition_cost
    varchar currency
    uuid policy_profile_id FK
    varchar state
    timestamp created_at
    timestamp updated_at
    int version
  }

  RESERVATION {
    uuid reservation_id PK
    uuid resource_id FK
    uuid requestor_id
    uuid tenant_id FK
    timestamp start_at
    timestamp end_at
    int priority
    varchar state
    string idempotency_key
    timestamp sla_due_at
    string cancellation_reason
    timestamp created_at
  }

  ALLOCATION {
    uuid allocation_id PK
    uuid reservation_id FK
    uuid resource_id FK
    uuid custodian_id
    uuid tenant_id FK
    timestamp checkout_at
    timestamp due_at
    timestamp checkin_at
    varchar checkout_condition
    varchar checkin_condition
    varchar condition_delta
    varchar state
    int extended_count
    timestamp created_at
  }

  CUSTODY_TRANSFER {
    uuid transfer_id PK
    uuid allocation_id FK
    uuid from_actor
    uuid to_actor
    timestamp transferred_at
    text reason
  }

  INCIDENT_CASE {
    uuid case_id PK
    uuid resource_id FK
    uuid allocation_id FK
    varchar case_type
    varchar severity
    varchar state
    uuid owner_id
    timestamp sla_due_at
    text description
    text resolution_notes
    timestamp created_at
    timestamp resolved_at
  }

  SETTLEMENT_RECORD {
    uuid settlement_id PK
    uuid case_id FK
    uuid allocation_id FK
    varchar charge_type
    decimal amount
    varchar currency
    uuid rate_card_id
    varchar state
    uuid ledger_event_id
    timestamp created_at
  }

  DECOMMISSION_REQUEST {
    uuid request_id PK
    uuid resource_id FK
    uuid requested_by
    text reason
    string disposal_method
    boolean requires_approval
    uuid approved_by
    timestamp approved_at
    varchar state
    timestamp created_at
  }

  AUDIT_EVENT {
    uuid audit_id PK
    uuid entity_id
    varchar entity_type
    varchar command
    uuid actor_id
    uuid correlation_id
    varchar reason_code
    jsonb before_state
    jsonb after_state
    timestamp timestamp
    varchar hash
  }

  OUTBOX {
    uuid outbox_id PK
    varchar event_type
    uuid aggregate_id
    jsonb payload
    varchar state
    int retry_count
    timestamp created_at
    timestamp delivered_at
  }

  TENANT ||--o{ RESOURCE : "owns"
  TENANT ||--o{ POLICY_PROFILE : "defines"
  TENANT ||--o{ LOCATION : "has"
  RESOURCE ||--|| POLICY_PROFILE : "governed by"
  RESOURCE ||--|| LOCATION : "located at"
  RESOURCE ||--o{ RESERVATION : "reserved via"
  RESOURCE ||--o{ ALLOCATION : "allocated via"
  RESOURCE ||--o{ INCIDENT_CASE : "involved in"
  RESOURCE ||--o{ DECOMMISSION_REQUEST : "terminates via"
  RESERVATION ||--o| ALLOCATION : "converted into"
  ALLOCATION ||--o{ CUSTODY_TRANSFER : "has"
  ALLOCATION ||--o{ INCIDENT_CASE : "triggers"
  INCIDENT_CASE ||--o{ SETTLEMENT_RECORD : "resolved by"
```

---

## Key Table Definitions

### resources

```sql
CREATE TABLE resources (
  resource_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(tenant_id),
  category          VARCHAR(32) NOT NULL CHECK (category IN ('EQUIPMENT','VEHICLE','SPACE','LICENSE','TOOL','CONSUMABLE')),
  asset_tag         VARCHAR(64) NOT NULL,
  serial_number     VARCHAR(128),
  name              VARCHAR(255) NOT NULL,
  description       TEXT,
  condition_grade   CHAR(1) NOT NULL CHECK (condition_grade IN ('A','B','C','D')),
  condition_notes   TEXT,
  location_id       UUID NOT NULL REFERENCES locations(location_id),
  cost_centre       VARCHAR(64) NOT NULL,
  acquisition_cost  NUMERIC(12,2),
  currency          CHAR(3),
  policy_profile_id UUID NOT NULL REFERENCES policy_profiles(policy_profile_id),
  state             VARCHAR(32) NOT NULL DEFAULT 'PENDING',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  version           INTEGER NOT NULL DEFAULT 1,
  CONSTRAINT resources_tenant_tag_unique UNIQUE (tenant_id, asset_tag)
);

CREATE INDEX idx_resources_tenant_state    ON resources(tenant_id, state);
CREATE INDEX idx_resources_tenant_category ON resources(tenant_id, category);
CREATE INDEX idx_resources_location        ON resources(location_id);
```

---

### reservations

```sql
CREATE TABLE reservations (
  reservation_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id       UUID NOT NULL REFERENCES resources(resource_id),
  requestor_id      UUID NOT NULL,
  tenant_id         UUID NOT NULL REFERENCES tenants(tenant_id),
  start_at          TIMESTAMPTZ NOT NULL,
  end_at            TIMESTAMPTZ NOT NULL CHECK (end_at > start_at),
  priority          INTEGER NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
  state             VARCHAR(32) NOT NULL DEFAULT 'PENDING',
  idempotency_key   VARCHAR(128) NOT NULL,
  sla_due_at        TIMESTAMPTZ,
  cancellation_reason VARCHAR(255),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT reservations_idempotency_unique UNIQUE (tenant_id, idempotency_key)
);

-- Exclusion constraint prevents overlapping CONFIRMED reservations for same resource
ALTER TABLE reservations
  ADD CONSTRAINT no_overlap_confirmed
  EXCLUDE USING gist (
    resource_id WITH =,
    tstzrange(start_at, end_at, '[]') WITH &&
  )
  WHERE (state = 'CONFIRMED');

CREATE INDEX idx_reservations_resource_state ON reservations(resource_id, state);
CREATE INDEX idx_reservations_requestor      ON reservations(requestor_id, tenant_id);
CREATE INDEX idx_reservations_sla            ON reservations(sla_due_at) WHERE state = 'CONFIRMED';
```

---

### allocations

```sql
CREATE TABLE allocations (
  allocation_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id      UUID REFERENCES reservations(reservation_id),
  resource_id         UUID NOT NULL REFERENCES resources(resource_id),
  custodian_id        UUID NOT NULL,
  tenant_id           UUID NOT NULL REFERENCES tenants(tenant_id),
  checkout_at         TIMESTAMPTZ NOT NULL,
  due_at              TIMESTAMPTZ NOT NULL,
  checkin_at          TIMESTAMPTZ,
  checkout_condition  CHAR(1) NOT NULL CHECK (checkout_condition IN ('A','B','C','D')),
  checkin_condition   CHAR(1) CHECK (checkin_condition IN ('A','B','C','D')),
  condition_delta     VARCHAR(16) CHECK (condition_delta IN ('NONE','MINOR','MAJOR','LOSS')),
  state               VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  extended_count      INTEGER NOT NULL DEFAULT 0,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_allocations_resource_state ON allocations(resource_id, state);
CREATE INDEX idx_allocations_custodian      ON allocations(custodian_id, state);
CREATE INDEX idx_allocations_overdue        ON allocations(due_at) WHERE state = 'ACTIVE';
```

---

### incident_cases

```sql
CREATE TABLE incident_cases (
  case_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id     UUID NOT NULL REFERENCES resources(resource_id),
  allocation_id   UUID REFERENCES allocations(allocation_id),
  case_type       VARCHAR(32) NOT NULL,
  severity        VARCHAR(16) NOT NULL,
  state           VARCHAR(32) NOT NULL DEFAULT 'OPEN',
  owner_id        UUID NOT NULL,
  sla_due_at      TIMESTAMPTZ NOT NULL,
  description     TEXT NOT NULL,
  resolution_notes TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at     TIMESTAMPTZ
);

CREATE INDEX idx_incidents_resource ON incident_cases(resource_id, state);
CREATE INDEX idx_incidents_sla      ON incident_cases(sla_due_at) WHERE state IN ('OPEN','IN_REVIEW');
```

---

### audit_events

```sql
CREATE TABLE audit_events (
  audit_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id      UUID NOT NULL,
  entity_type    VARCHAR(64) NOT NULL,
  command        VARCHAR(128) NOT NULL,
  actor_id       UUID NOT NULL,
  correlation_id UUID NOT NULL,
  reason_code    VARCHAR(64),
  before_state   JSONB,
  after_state    JSONB,
  timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  hash           VARCHAR(64) NOT NULL
) PARTITION BY RANGE (timestamp);

-- Monthly partitions for efficient retention management
CREATE TABLE audit_events_2025_06 PARTITION OF audit_events
  FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE INDEX idx_audit_entity ON audit_events(entity_id, timestamp);
CREATE INDEX idx_audit_actor  ON audit_events(actor_id, timestamp);
```

---

### outbox

```sql
CREATE TABLE outbox (
  outbox_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    VARCHAR(128) NOT NULL,
  aggregate_id  UUID NOT NULL,
  payload       JSONB NOT NULL,
  state         VARCHAR(16) NOT NULL DEFAULT 'PENDING',
  retry_count   INTEGER NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  delivered_at  TIMESTAMPTZ
);

CREATE INDEX idx_outbox_pending ON outbox(created_at) WHERE state = 'PENDING';
```

---

## Indexing Strategy

| Table | Hot Queries | Index Strategy |
|---|---|---|
| `resources` | Tenant + state lookup; category filter | Composite `(tenant_id, state)`, `(tenant_id, category)` |
| `reservations` | Overlap check; requestor's active reservations | GiST exclusion on `(resource_id, tstzrange)`; composite `(requestor_id, tenant_id)` |
| `allocations` | Overdue scan; custodian view | Partial index on `due_at WHERE state='ACTIVE'`; composite `(custodian_id, state)` |
| `incident_cases` | Open cases by resource; SLA breach scan | Partial index on `sla_due_at WHERE state IN ('OPEN','IN_REVIEW')` |
| `audit_events` | Per-resource history; compliance export | Partitioned table; composite `(entity_id, timestamp)` |
| `outbox` | Relay job scan | Partial index on `created_at WHERE state='PENDING'` |

---

## Data Retention

| Table | Retention | Archival |
|---|---|---|
| `resources` | Active + 7 years post-decommission | Decommissioned records archived to cold storage |
| `reservations` | 3 years | Archive to cold storage after expiry + 3 years |
| `allocations` | 7 years | Archive to cold storage after checkin + 7 years |
| `audit_events` | 7 years minimum (configurable per compliance profile) | Monthly partitions moved to cold storage on expiry |
| `incident_cases` | 7 years | Archive with linked settlement records |
| `outbox` | 7 days | Delete after delivery; DLQ retains undelivered for 30 days |

---

## Cross-References

- Data dictionary: [../analysis/data-dictionary.md](../analysis/data-dictionary.md)
- Domain model: [../high-level-design/domain-model.md](../high-level-design/domain-model.md)
- Class diagrams: [class-diagrams.md](./class-diagrams.md)
