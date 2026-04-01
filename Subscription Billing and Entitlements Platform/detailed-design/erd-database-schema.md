# ERD & Database Schema — Subscription Billing and Entitlements Platform

## Overview

This document defines the complete relational database schema for the Subscription Billing and Entitlements Platform. All tables use `UUID` primary keys, `TIMESTAMPTZ` for all timestamps, and `NUMERIC(19,6)` for all monetary values to avoid floating-point precision errors. The database target is **PostgreSQL 15+**.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    accounts { uuid account_id PK; varchar email; char currency; varchar status; timestamptz created_at }
    subscriptions { uuid subscription_id PK; uuid account_id FK; uuid plan_version_id FK; varchar status; timestamptz trial_end; timestamptz current_period_start; timestamptz current_period_end; timestamptz cancelled_at }
    plans { uuid plan_id PK; varchar name; int trial_days; varchar status }
    plan_versions { uuid plan_version_id PK; uuid plan_id FK; int version_number; timestamptz effective_from; timestamptz effective_to; varchar status }
    prices { uuid price_id PK; uuid plan_version_id FK; varchar pricing_model; char currency; numeric unit_amount; jsonb tiers; varchar billing_period }
    usage_records { uuid usage_id PK; uuid subscription_id FK; varchar metric_name; numeric quantity; timestamptz recorded_at; varchar idempotency_key }
    invoices { uuid invoice_id PK; uuid account_id FK; uuid subscription_id FK; varchar status; numeric subtotal; numeric tax_amount; numeric total; numeric amount_due; char currency; timestamptz finalized_at; timestamptz paid_at }
    invoice_line_items { uuid line_item_id PK; uuid invoice_id FK; text description; numeric quantity; numeric unit_price; numeric amount; varchar line_item_type }
    payment_methods { uuid payment_method_id PK; uuid account_id FK; varchar type; varchar gateway_token; char last_four; int expiry_month; int expiry_year; boolean is_default }
    payment_attempts { uuid attempt_id PK; uuid invoice_id FK; uuid payment_method_id FK; numeric amount; varchar status; varchar gateway_transaction_id; jsonb gateway_response }
    credits { uuid credit_id PK; uuid account_id FK; numeric amount; numeric remaining_amount; text reason; timestamptz expires_at }
    credit_notes { uuid credit_note_id PK; uuid invoice_id FK; uuid account_id FK; numeric amount; varchar status }
    entitlements { uuid entitlement_id PK; uuid subscription_id FK; varchar feature_key; varchar limit_type; numeric limit_value; numeric current_usage }
    entitlement_grants { uuid grant_id PK; uuid entitlement_id FK; varchar granted_by; numeric granted_amount; timestamptz valid_from; timestamptz valid_to }
    coupon_codes { uuid coupon_id PK; varchar code; varchar discount_type; numeric discount_value; int max_redemptions; int redemptions_count; timestamptz expires_at }
    discount_applications { uuid application_id PK; uuid invoice_id FK; uuid coupon_id FK; numeric discount_amount }
    tax_jurisdictions { uuid jurisdiction_id PK; char country_code; varchar state_code; varchar zip_code }
    tax_rates { uuid tax_rate_id PK; uuid jurisdiction_id FK; numeric rate; varchar tax_type; timestamptz effective_from; timestamptz effective_to }
    dunning_cycles { uuid dunning_cycle_id PK; uuid subscription_id FK; uuid invoice_id FK; varchar status; int current_step; timestamptz started_at; timestamptz resolved_at }
    dunning_steps { uuid step_id PK; uuid dunning_cycle_id FK; int step_number; timestamptz scheduled_at; timestamptz executed_at; varchar result }

    accounts ||--o{ subscriptions : "has"
    accounts ||--o{ payment_methods : "owns"
    accounts ||--o{ credits : "holds"
    accounts ||--o{ invoices : "billed on"
    accounts ||--o{ credit_notes : "receives"
    plans ||--o{ plan_versions : "versioned by"
    plan_versions ||--o{ prices : "priced by"
    plan_versions ||--o{ subscriptions : "subscribed on"
    subscriptions ||--o{ usage_records : "generates"
    subscriptions ||--o{ invoices : "invoiced via"
    subscriptions ||--o{ entitlements : "grants"
    subscriptions ||--o{ dunning_cycles : "subject to"
    invoices ||--o{ invoice_line_items : "contains"
    invoices ||--o{ payment_attempts : "paid via"
    invoices ||--o{ discount_applications : "discounted by"
    invoices ||--o{ credit_notes : "adjusted by"
    payment_methods ||--o{ payment_attempts : "charged via"
    entitlements ||--o{ entitlement_grants : "extended by"
    coupon_codes ||--o{ discount_applications : "applied as"
    tax_jurisdictions ||--o{ tax_rates : "governs"
    dunning_cycles ||--o{ dunning_steps : "composed of"
```

---

## SQL CREATE TABLE Statements

### accounts

```sql
CREATE TABLE accounts (
    account_id    UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(320)  NOT NULL,
    currency      CHAR(3)       NOT NULL DEFAULT 'USD',
    status        VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')),
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_accounts_email ON accounts (email);
CREATE INDEX idx_accounts_status ON accounts (status);
```

### plans

```sql
CREATE TABLE plans (
    plan_id       UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255)  NOT NULL,
    description   TEXT,
    trial_days    INTEGER       NOT NULL DEFAULT 0 CHECK (trial_days >= 0),
    status        VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE'
                  CHECK (status IN ('ACTIVE', 'ARCHIVED', 'DRAFT')),
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_plans_status ON plans (status);
CREATE INDEX idx_plans_name ON plans (name);
```

### plan_versions

```sql
CREATE TABLE plan_versions (
    plan_version_id  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id          UUID         NOT NULL REFERENCES plans (plan_id) ON DELETE RESTRICT,
    version_number   INTEGER      NOT NULL CHECK (version_number > 0),
    effective_from   TIMESTAMPTZ  NOT NULL,
    effective_to     TIMESTAMPTZ,
    status           VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
                     CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'DRAFT')),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_version UNIQUE (plan_id, version_number),
    CONSTRAINT chk_effective_range CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX idx_plan_versions_plan_id ON plan_versions (plan_id);
CREATE INDEX idx_plan_versions_effective ON plan_versions (plan_id, effective_from, effective_to)
    WHERE status = 'ACTIVE';
```

### prices

```sql
CREATE TABLE prices (
    price_id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_version_id      UUID           NOT NULL REFERENCES plan_versions (plan_version_id) ON DELETE RESTRICT,
    pricing_model        VARCHAR(20)    NOT NULL
                         CHECK (pricing_model IN ('FLAT', 'PER_UNIT', 'TIERED', 'VOLUME', 'PACKAGE')),
    currency             CHAR(3)        NOT NULL,
    unit_amount          NUMERIC(19,6)  CHECK (unit_amount >= 0),
    tiers                JSONB,
    billing_period       VARCHAR(20)    NOT NULL
                         CHECK (billing_period IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUAL')),
    billing_period_count INTEGER        NOT NULL DEFAULT 1 CHECK (billing_period_count > 0),
    created_at           TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_flat_has_amount CHECK (
        pricing_model != 'FLAT' OR unit_amount IS NOT NULL
    ),
    CONSTRAINT chk_tiered_has_tiers CHECK (
        pricing_model NOT IN ('TIERED', 'VOLUME') OR tiers IS NOT NULL
    )
);

CREATE INDEX idx_prices_plan_version ON prices (plan_version_id);
CREATE INDEX idx_prices_currency ON prices (plan_version_id, currency);
```

### subscriptions

```sql
CREATE TABLE subscriptions (
    subscription_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id            UUID         NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
    plan_version_id       UUID         NOT NULL REFERENCES plan_versions (plan_version_id) ON DELETE RESTRICT,
    status                VARCHAR(20)  NOT NULL DEFAULT 'TRIALING'
                          CHECK (status IN ('TRIALING', 'ACTIVE', 'PAST_DUE', 'PAUSED', 'CANCELLED', 'EXPIRED')),
    trial_start           TIMESTAMPTZ,
    trial_end             TIMESTAMPTZ,
    current_period_start  TIMESTAMPTZ  NOT NULL,
    current_period_end    TIMESTAMPTZ  NOT NULL,
    cancelled_at          TIMESTAMPTZ,
    paused_at             TIMESTAMPTZ,
    cancel_at_period_end  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_period_order CHECK (current_period_end > current_period_start),
    CONSTRAINT chk_trial_order CHECK (trial_end IS NULL OR trial_end > trial_start)
);

CREATE INDEX idx_subscriptions_account ON subscriptions (account_id);
CREATE INDEX idx_subscriptions_status ON subscriptions (status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions (current_period_end)
    WHERE status IN ('TRIALING', 'ACTIVE', 'PAST_DUE');
CREATE INDEX idx_subscriptions_plan_version ON subscriptions (plan_version_id);
```

### usage_records

```sql
CREATE TABLE usage_records (
    usage_id         UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id  UUID           NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE RESTRICT,
    metric_name      VARCHAR(255)   NOT NULL,
    quantity         NUMERIC(19,6)  NOT NULL CHECK (quantity > 0),
    recorded_at      TIMESTAMPTZ    NOT NULL,
    idempotency_key  VARCHAR(512)   NOT NULL,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_usage_records_idempotency ON usage_records (idempotency_key);
CREATE INDEX idx_usage_records_subscription_metric
    ON usage_records (subscription_id, metric_name, recorded_at);
CREATE INDEX idx_usage_records_recorded_at ON usage_records (recorded_at);
```

### invoices

```sql
CREATE TABLE invoices (
    invoice_id       UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id       UUID           NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
    subscription_id  UUID           NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE RESTRICT,
    status           VARCHAR(20)    NOT NULL DEFAULT 'DRAFT'
                     CHECK (status IN ('DRAFT', 'OPEN', 'FINALIZED', 'PAID', 'VOID')),
    period_start     TIMESTAMPTZ    NOT NULL,
    period_end       TIMESTAMPTZ    NOT NULL,
    subtotal         NUMERIC(19,6)  NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount       NUMERIC(19,6)  NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    total            NUMERIC(19,6)  NOT NULL DEFAULT 0 CHECK (total >= 0),
    amount_due       NUMERIC(19,6)  NOT NULL DEFAULT 0 CHECK (amount_due >= 0),
    currency         CHAR(3)        NOT NULL,
    tax_calc_failed  BOOLEAN        NOT NULL DEFAULT FALSE,
    finalized_at     TIMESTAMPTZ,
    paid_at          TIMESTAMPTZ,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_period_order CHECK (period_end > period_start),
    CONSTRAINT chk_total_sum CHECK (total = subtotal + tax_amount)
);

CREATE INDEX idx_invoices_account ON invoices (account_id);
CREATE INDEX idx_invoices_subscription ON invoices (subscription_id);
CREATE INDEX idx_invoices_status ON invoices (status);
CREATE INDEX idx_invoices_finalized_at ON invoices (finalized_at) WHERE status = 'FINALIZED';
CREATE UNIQUE INDEX idx_invoices_subscription_period ON invoices (subscription_id, period_start)
    WHERE status NOT IN ('VOID');
```

### invoice_line_items

```sql
CREATE TABLE invoice_line_items (
    line_item_id    UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID           NOT NULL REFERENCES invoices (invoice_id) ON DELETE CASCADE,
    description     TEXT           NOT NULL,
    quantity        NUMERIC(19,6)  NOT NULL DEFAULT 1,
    unit_price      NUMERIC(19,6)  NOT NULL DEFAULT 0,
    amount          NUMERIC(19,6)  NOT NULL,
    tax_amount      NUMERIC(19,6)  NOT NULL DEFAULT 0,
    line_item_type  VARCHAR(30)    NOT NULL
                    CHECK (line_item_type IN (
                        'SUBSCRIPTION_FEE', 'USAGE_CHARGE', 'PRORATION',
                        'CREDIT_ADJUSTMENT', 'DISCOUNT', 'TAX'
                    )),
    metric_name     VARCHAR(255),
    period_start    TIMESTAMPTZ,
    period_end      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_line_items_invoice ON invoice_line_items (invoice_id);
CREATE INDEX idx_line_items_type ON invoice_line_items (invoice_id, line_item_type);
```

### payment_methods

```sql
CREATE TABLE payment_methods (
    payment_method_id  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id         UUID         NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
    type               VARCHAR(30)  NOT NULL
                       CHECK (type IN ('CARD', 'BANK_ACCOUNT', 'WALLET', 'ACH', 'SEPA_DEBIT')),
    gateway_token      VARCHAR(512) NOT NULL,
    last_four          CHAR(4),
    expiry_month       INTEGER      CHECK (expiry_month BETWEEN 1 AND 12),
    expiry_year        INTEGER      CHECK (expiry_year >= 2000),
    is_default         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_methods_account ON payment_methods (account_id);
CREATE INDEX idx_payment_methods_default ON payment_methods (account_id)
    WHERE is_default = TRUE;
```

### payment_attempts

```sql
CREATE TABLE payment_attempts (
    attempt_id              UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id              UUID           NOT NULL REFERENCES invoices (invoice_id) ON DELETE RESTRICT,
    payment_method_id       UUID           NOT NULL REFERENCES payment_methods (payment_method_id) ON DELETE RESTRICT,
    amount                  NUMERIC(19,6)  NOT NULL CHECK (amount > 0),
    currency                CHAR(3)        NOT NULL,
    status                  VARCHAR(20)    NOT NULL DEFAULT 'PENDING'
                            CHECK (status IN ('PENDING', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'REFUNDED')),
    gateway_transaction_id  VARCHAR(512),
    gateway_response        JSONB,
    failure_code            VARCHAR(100),
    failure_message         TEXT,
    attempted_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_attempts_invoice ON payment_attempts (invoice_id);
CREATE INDEX idx_payment_attempts_status ON payment_attempts (invoice_id, status);
CREATE INDEX idx_payment_attempts_gateway_txn ON payment_attempts (gateway_transaction_id)
    WHERE gateway_transaction_id IS NOT NULL;
```

### credits

```sql
CREATE TABLE credits (
    credit_id         UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id        UUID           NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
    amount            NUMERIC(19,6)  NOT NULL CHECK (amount > 0),
    remaining_amount  NUMERIC(19,6)  NOT NULL CHECK (remaining_amount >= 0),
    reason            TEXT           NOT NULL,
    expires_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_remaining_lte_amount CHECK (remaining_amount <= amount)
);

CREATE INDEX idx_credits_account ON credits (account_id);
CREATE INDEX idx_credits_active ON credits (account_id, expires_at)
    WHERE remaining_amount > 0;
```

### credit_notes

```sql
CREATE TABLE credit_notes (
    credit_note_id  UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID           NOT NULL REFERENCES invoices (invoice_id) ON DELETE RESTRICT,
    account_id      UUID           NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
    amount          NUMERIC(19,6)  NOT NULL CHECK (amount > 0),
    reason          TEXT           NOT NULL,
    status          VARCHAR(20)    NOT NULL DEFAULT 'ISSUED'
                    CHECK (status IN ('ISSUED', 'APPLIED', 'VOID')),
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credit_notes_invoice ON credit_notes (invoice_id);
CREATE INDEX idx_credit_notes_account ON credit_notes (account_id);
```

### entitlements

```sql
CREATE TABLE entitlements (
    entitlement_id  UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID           NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE CASCADE,
    feature_key     VARCHAR(255)   NOT NULL,
    limit_type      VARCHAR(20)    NOT NULL
                    CHECK (limit_type IN ('HARD_CAP', 'SOFT_CAP', 'METERED', 'UNLIMITED')),
    limit_value     NUMERIC(19,6),
    current_usage   NUMERIC(19,6)  NOT NULL DEFAULT 0 CHECK (current_usage >= 0),
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_subscription_feature UNIQUE (subscription_id, feature_key),
    CONSTRAINT chk_cap_has_limit CHECK (
        limit_type = 'UNLIMITED' OR limit_value IS NOT NULL
    )
);

CREATE INDEX idx_entitlements_subscription ON entitlements (subscription_id);
CREATE INDEX idx_entitlements_feature ON entitlements (feature_key);
```

### entitlement_grants

```sql
CREATE TABLE entitlement_grants (
    grant_id        UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    entitlement_id  UUID           NOT NULL REFERENCES entitlements (entitlement_id) ON DELETE CASCADE,
    granted_by      VARCHAR(255)   NOT NULL,
    granted_amount  NUMERIC(19,6)  NOT NULL CHECK (granted_amount > 0),
    valid_from      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    valid_to        TIMESTAMPTZ    NOT NULL,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_grant_validity CHECK (valid_to > valid_from)
);

CREATE INDEX idx_entitlement_grants_entitlement ON entitlement_grants (entitlement_id);
CREATE INDEX idx_entitlement_grants_active ON entitlement_grants (entitlement_id, valid_from, valid_to)
    WHERE valid_to > NOW();
```

### coupon_codes

```sql
CREATE TABLE coupon_codes (
    coupon_id          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    code               VARCHAR(100)   NOT NULL,
    discount_type      VARCHAR(20)    NOT NULL
                       CHECK (discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')),
    discount_value     NUMERIC(19,6)  NOT NULL CHECK (discount_value > 0),
    max_redemptions    INTEGER        CHECK (max_redemptions IS NULL OR max_redemptions > 0),
    redemptions_count  INTEGER        NOT NULL DEFAULT 0 CHECK (redemptions_count >= 0),
    expires_at         TIMESTAMPTZ,
    created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_percentage_range CHECK (
        discount_type != 'PERCENTAGE' OR discount_value <= 100
    ),
    CONSTRAINT chk_redemptions CHECK (
        max_redemptions IS NULL OR redemptions_count <= max_redemptions
    )
);

CREATE UNIQUE INDEX idx_coupon_codes_code ON coupon_codes (UPPER(code));
CREATE INDEX idx_coupon_codes_active ON coupon_codes (expires_at)
    WHERE expires_at IS NULL OR expires_at > NOW();
```

### discount_applications

```sql
CREATE TABLE discount_applications (
    application_id   UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id       UUID           NOT NULL REFERENCES invoices (invoice_id) ON DELETE RESTRICT,
    coupon_id        UUID           NOT NULL REFERENCES coupon_codes (coupon_id) ON DELETE RESTRICT,
    discount_amount  NUMERIC(19,6)  NOT NULL CHECK (discount_amount > 0),
    applied_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_invoice_coupon UNIQUE (invoice_id, coupon_id)
);

CREATE INDEX idx_discount_applications_invoice ON discount_applications (invoice_id);
CREATE INDEX idx_discount_applications_coupon ON discount_applications (coupon_id);
```

### tax_jurisdictions

```sql
CREATE TABLE tax_jurisdictions (
    jurisdiction_id  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code     CHAR(2)      NOT NULL,
    state_code       VARCHAR(10),
    city             VARCHAR(100),
    zip_code         VARCHAR(20),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tax_jurisdictions_lookup
    ON tax_jurisdictions (country_code, COALESCE(state_code, ''), COALESCE(zip_code, ''));
CREATE INDEX idx_tax_jurisdictions_country ON tax_jurisdictions (country_code);
```

### tax_rates

```sql
CREATE TABLE tax_rates (
    tax_rate_id      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id  UUID           NOT NULL REFERENCES tax_jurisdictions (jurisdiction_id) ON DELETE RESTRICT,
    rate             NUMERIC(8,6)   NOT NULL CHECK (rate >= 0 AND rate <= 1),
    tax_type         VARCHAR(20)    NOT NULL
                     CHECK (tax_type IN ('VAT', 'GST', 'SALES_TAX', 'SERVICE_TAX')),
    effective_from   TIMESTAMPTZ    NOT NULL,
    effective_to     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_tax_rate_range CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX idx_tax_rates_jurisdiction ON tax_rates (jurisdiction_id);
CREATE INDEX idx_tax_rates_effective ON tax_rates (jurisdiction_id, effective_from, effective_to);
```

### dunning_cycles

```sql
CREATE TABLE dunning_cycles (
    dunning_cycle_id  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id   UUID         NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE RESTRICT,
    invoice_id        UUID         NOT NULL REFERENCES invoices (invoice_id) ON DELETE RESTRICT,
    status            VARCHAR(20)  NOT NULL DEFAULT 'INITIATED'
                      CHECK (status IN ('INITIATED', 'STEP_1', 'STEP_2', 'STEP_3', 'STEP_4', 'RESOLVED', 'ABANDONED')),
    current_step      INTEGER      NOT NULL DEFAULT 0 CHECK (current_step >= 0 AND current_step <= 4),
    started_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_invoice_dunning UNIQUE (invoice_id)
);

CREATE INDEX idx_dunning_cycles_subscription ON dunning_cycles (subscription_id);
CREATE INDEX idx_dunning_cycles_status ON dunning_cycles (status)
    WHERE status NOT IN ('RESOLVED', 'ABANDONED');
```

### dunning_steps

```sql
CREATE TABLE dunning_steps (
    step_id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    dunning_cycle_id  UUID         NOT NULL REFERENCES dunning_cycles (dunning_cycle_id) ON DELETE CASCADE,
    step_number       INTEGER      NOT NULL CHECK (step_number BETWEEN 1 AND 4),
    scheduled_at      TIMESTAMPTZ  NOT NULL,
    executed_at       TIMESTAMPTZ,
    result            VARCHAR(20)
                      CHECK (result IS NULL OR result IN ('SUCCEEDED', 'FAILED', 'SKIPPED')),
    failure_reason    TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cycle_step UNIQUE (dunning_cycle_id, step_number)
);

CREATE INDEX idx_dunning_steps_cycle ON dunning_steps (dunning_cycle_id);
CREATE INDEX idx_dunning_steps_scheduled ON dunning_steps (scheduled_at)
    WHERE executed_at IS NULL;
```

---

## Schema Conventions

| Convention | Decision |
|---|---|
| Monetary type | `NUMERIC(19,6)` — sub-cent precision; rounded to 2dp at display only |
| Currency codes | `CHAR(3)` ISO 4217 stored per-row on every financial entity |
| Primary keys | `gen_random_uuid()` (PostgreSQL 13+); avoids sequential ID exposure |
| Soft deletes | Status-based (`ARCHIVED`, `CANCELLED`, `VOID`); no `is_deleted` columns |
| Cascade deletes | Only child tables with no independent audit need (`line_items`, `entitlement_grants`, `dunning_steps`) |
| Partial indexes | Applied on status columns to skip terminal rows in hot-path queries |
| JSONB columns | `prices.tiers` (tier breakpoints) and `payment_attempts.gateway_response` (raw audit); never queried relationally |
| Idempotency | Unique index on `usage_records.idempotency_key` and `UNIQUE` constraint on `invoices(subscription_id, period_start)` as final deduplication layer |
