# ERD / Database Schema

## Entity Relationship Diagram

```mermaid
erDiagram
    customers ||--o{ addresses : "has"
    customers ||--o{ orders : "places"
    customers ||--o{ return_requests : "initiates"

    categories ||--o{ categories : "parent"
    categories ||--o{ products : "contains"
    products ||--o{ product_variants : "has"
    product_variants ||--o{ inventory : "tracked"
    warehouses ||--o{ inventory : "holds"

    orders ||--|{ order_line_items : "contains"
    orders ||--o| coupons : "uses"
    orders ||--o| payment_transactions : "paid_via"
    orders ||--o| delivery_assignments : "assigned"
    orders ||--o| proof_of_delivery : "confirmed_by"
    orders ||--o{ return_requests : "may_have"
    orders ||--o{ order_milestones : "tracked_by"
    orders ||--o| fulfillment_tasks : "fulfilled_by"

    order_line_items }o--|| product_variants : "references"

    delivery_assignments }o--|| staff : "performed_by"
    delivery_assignments }o--|| delivery_zones : "within"

    proof_of_delivery }o--|| staff : "captured_by"

    return_requests ||--o| return_pickups : "pickup"
    return_pickups }o--|| staff : "collected_by"

    staff }o--o| warehouses : "assigned_to"
    staff }o--o| delivery_zones : "covers"

    payment_transactions ||--o{ refund_records : "refunds"

    customers {
        uuid id PK
        varchar email UK
        varchar phone UK
        varchar full_name
        varchar password_hash
        varchar auth_provider
        varchar cognito_sub UK
        jsonb notification_prefs
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    addresses {
        uuid id PK
        uuid customer_id FK
        varchar label
        varchar line1
        varchar line2
        varchar city
        varchar state
        varchar postal_code
        varchar country
        boolean is_default
        timestamptz created_at
    }

    categories {
        uuid id PK
        uuid parent_id FK
        varchar name
        integer display_order
        boolean returnable
        varchar status
    }

    products {
        uuid id PK
        uuid category_id FK
        varchar title
        text description
        decimal base_price
        char currency
        jsonb images
        jsonb specifications
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    product_variants {
        uuid id PK
        uuid product_id FK
        varchar sku UK
        jsonb attributes
        decimal price_adjustment
        integer weight_grams
        varchar status
    }

    inventory {
        uuid id PK
        uuid variant_id FK
        uuid warehouse_id FK
        integer qty_on_hand
        integer qty_reserved
        integer low_stock_threshold
        timestamptz updated_at
    }

    inventory_reservations {
        uuid id PK
        uuid inventory_id FK
        uuid order_id FK
        integer quantity
        timestamptz expires_at
        varchar status
    }

    orders {
        uuid id PK
        varchar order_number UK
        uuid customer_id FK
        uuid delivery_address_id FK
        varchar status
        decimal subtotal
        decimal tax_amount
        decimal shipping_fee
        decimal discount_amount
        decimal total_amount
        uuid coupon_id FK
        uuid payment_id FK
        varchar cancellation_reason
        timestamptz estimated_delivery
        timestamptz delivered_at
        varchar idempotency_key UK
        timestamptz created_at
        timestamptz updated_at
    }

    order_line_items {
        uuid id PK
        uuid order_id FK
        uuid variant_id FK
        varchar product_title
        varchar variant_label
        integer quantity
        decimal unit_price
        decimal line_total
    }

    order_milestones {
        uuid id PK
        uuid order_id FK
        varchar status
        uuid actor_id
        varchar actor_role
        text notes
        timestamptz recorded_at
    }

    delivery_assignments {
        uuid id PK
        uuid order_id FK
        uuid staff_id FK
        uuid delivery_zone_id FK
        timestamptz window_start
        timestamptz window_end
        integer attempt_count
        varchar status
        timestamptz created_at
    }

    proof_of_delivery {
        uuid id PK
        uuid order_id FK
        uuid staff_id FK
        varchar signature_s3_key
        jsonb photo_s3_keys
        text delivery_notes
        timestamptz captured_at
        timestamptz uploaded_at
    }

    payment_transactions {
        uuid id PK
        uuid order_id FK
        decimal amount
        char currency
        varchar gateway_name
        varchar gateway_ref
        varchar status
        varchar idempotency_key UK
        timestamptz created_at
        timestamptz updated_at
    }

    refund_records {
        uuid id PK
        uuid payment_id FK
        uuid order_id FK
        decimal amount
        varchar reason
        varchar gateway_ref
        varchar status
        timestamptz created_at
    }

    return_requests {
        uuid id PK
        uuid order_id FK
        uuid customer_id FK
        varchar reason_code
        jsonb evidence_s3_keys
        varchar status
        varchar inspection_result
        decimal refund_amount
        timestamptz created_at
        timestamptz resolved_at
    }

    return_pickups {
        uuid id PK
        uuid return_id FK
        uuid staff_id FK
        varchar status
        text condition_notes
        timestamptz collected_at
    }

    coupons {
        uuid id PK
        varchar code UK
        varchar discount_type
        decimal discount_value
        decimal min_order_value
        integer usage_limit
        integer times_used
        boolean stackable
        timestamptz valid_from
        timestamptz valid_until
        varchar status
    }

    staff {
        uuid id PK
        varchar name
        varchar email UK
        varchar phone
        varchar cognito_sub UK
        varchar role
        uuid warehouse_id FK
        uuid delivery_zone_id FK
        boolean is_active
        timestamptz created_at
    }

    warehouses {
        uuid id PK
        varchar name
        varchar location
        boolean is_active
    }

    delivery_zones {
        uuid id PK
        varchar name
        jsonb postal_codes
        decimal delivery_fee
        decimal min_order_value
        integer sla_hours
        boolean is_active
    }

    platform_config {
        uuid id PK
        varchar key UK
        jsonb value
        integer version
        timestamptz updated_at
        uuid updated_by FK
    }

    audit_logs {
        uuid id PK
        uuid actor_id
        varchar actor_role
        varchar action
        varchar resource_type
        uuid resource_id
        jsonb before_state
        jsonb after_state
        timestamptz created_at
    }

    notification_templates {
        uuid id PK
        varchar event_type
        varchar channel
        varchar subject
        text body_template
        integer version
        varchar status
        timestamptz updated_at
    }
```

## Indexes

| Table | Index | Columns | Type | Purpose |
|---|---|---|---|---|
| orders | idx_orders_customer | customer_id, created_at DESC | B-tree | Customer order history queries |
| orders | idx_orders_status | status | B-tree | Status-based filtering |
| orders | idx_orders_number | order_number | Unique | Human-readable order lookup |
| order_line_items | idx_oli_order | order_id | B-tree | Order → line items join |
| inventory | idx_inv_variant_wh | variant_id, warehouse_id | Unique | Stock lookup per variant per warehouse |
| delivery_assignments | idx_da_staff_date | staff_id, created_at DESC | B-tree | Staff assignment queries |
| delivery_assignments | idx_da_zone_status | delivery_zone_id, status | B-tree | Zone-based assignment filtering |
| order_milestones | idx_milestones_order | order_id, recorded_at | B-tree | Milestone timeline queries |
| payment_transactions | idx_pt_order | order_id | B-tree | Payment lookup by order |
| return_requests | idx_rr_order | order_id | B-tree | Return lookup by order |
| audit_logs | idx_al_actor_date | actor_id, created_at DESC | B-tree | Actor-based audit queries |
| audit_logs | idx_al_resource | resource_type, resource_id | B-tree | Resource-based audit queries |

## Partitioning Strategy

| Table | Strategy | Partition Key | Retention |
|---|---|---|---|
| order_milestones | Range (monthly) | recorded_at | 2 years active, then archive |
| audit_logs | Range (monthly) | created_at | 1 year active, then S3 Glacier |
| orders | None (indexed) | — | 2 years active, then cold archive |
| inventory_reservations | None (TTL cleanup) | — | Expired records purged daily |
