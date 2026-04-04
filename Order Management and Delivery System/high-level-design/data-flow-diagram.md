# Data Flow Diagram

## Overview

This document presents DFD Level-0 and Level-1 diagrams showing data inputs, processing, data stores, and outputs for the Order Management and Delivery System.

## DFD Level 0 — Context

```mermaid
flowchart LR
    C([Customer]) -->|"Orders, returns,<br/>profile data"| OMS["Order Management<br/>and Delivery System"]
    OMS -->|"Confirmations,<br/>status updates, POD"| C
    WS([Warehouse Staff]) -->|"Pick/pack<br/>confirmations"| OMS
    OMS -->|"Pick lists,<br/>manifests"| WS
    DS([Delivery Staff]) -->|"Status updates,<br/>POD uploads"| OMS
    OMS -->|"Assignments,<br/>route sheets"| DS
    OM([Ops Manager]) -->|"Reassignments,<br/>zone config"| OMS
    OMS -->|"Dashboards,<br/>reports"| OM
    AD([Admin]) -->|"Catalog, config,<br/>staff management"| OMS
    OMS -->|"Analytics,<br/>audit logs"| AD
    FN([Finance]) -->|"Manual refunds"| OMS
    OMS -->|"Reconciliation<br/>reports"| FN
    PG([Payment Gateway]) -->|"Capture/refund<br/>responses"| OMS
    OMS -->|"Capture/refund<br/>requests"| PG
```

## DFD Level 1 — Major Processes

```mermaid
flowchart TB
    subgraph External["External Entities"]
        C([Customer])
        WS([Warehouse Staff])
        DS([Delivery Staff])
        PG([Payment Gateway])
    end

    subgraph Processes["Core Processes"]
        P1["1.0<br/>Manage Catalog<br/>and Inventory"]
        P2["2.0<br/>Process Cart<br/>and Checkout"]
        P3["3.0<br/>Manage Orders"]
        P4["4.0<br/>Process Payments"]
        P5["5.0<br/>Fulfill Orders"]
        P6["6.0<br/>Manage Deliveries"]
        P7["7.0<br/>Process Returns"]
        P8["8.0<br/>Send Notifications"]
    end

    subgraph DataStores["Data Stores"]
        D1[(Product Catalog<br/>RDS)]
        D2[(Inventory<br/>RDS)]
        D3[(Cart Data<br/>DynamoDB)]
        D4[(Order Records<br/>RDS)]
        D5[(Payment Records<br/>RDS)]
        D6[(Delivery Records<br/>RDS)]
        D7[(POD Artifacts<br/>S3)]
        D8[(Milestones<br/>DynamoDB)]
        D9[(Search Index<br/>OpenSearch)]
    end

    C -->|"Browse, search"| P1
    P1 -->|"Product data"| D1
    P1 -->|"Index updates"| D9
    D1 -->|"Product info"| P1
    D9 -->|"Search results"| P1
    P1 -->|"Results"| C

    C -->|"Add to cart, checkout"| P2
    P2 -->|"Cart state"| D3
    D3 -->|"Cart items"| P2
    P2 -->|"Reserve stock"| D2
    D2 -->|"Availability"| P2
    P2 -->|"Create order"| P3
    P2 -->|"Initiate payment"| P4

    P4 -->|"Capture request"| PG
    PG -->|"Capture response"| P4
    P4 -->|"Transaction record"| D5
    P4 -->|"Payment result"| P3

    P3 -->|"Order record"| D4
    P3 -->|"Milestones"| D8
    D4 -->|"Order status"| C
    P3 -->|"Confirmed order"| P5
    P3 -->|"Notify"| P8

    WS -->|"Pick/pack updates"| P5
    P5 -->|"Pick list"| WS
    P5 -->|"Fulfilled order"| P6
    P5 -->|"Update order"| D4

    DS -->|"Status, POD"| P6
    P6 -->|"Assignments"| DS
    P6 -->|"POD files"| D7
    P6 -->|"Delivery records"| D6
    P6 -->|"Milestones"| D8
    P6 -->|"Notify"| P8

    C -->|"Return request"| P7
    P7 -->|"Return record"| D4
    P7 -->|"Refund trigger"| P4
    P7 -->|"Notify"| P8

    P8 -->|"Email, SMS, Push"| C
```

## Data Store Details

| Store | Technology | Data | Access Pattern | Retention |
|---|---|---|---|---|
| Product Catalog | RDS (PostgreSQL) | Products, variants, categories | Read-heavy; cached in ElastiCache | Indefinite (soft delete) |
| Inventory | RDS (PostgreSQL) | Stock levels, reservations | Read-write; optimistic locking | Indefinite |
| Cart Data | DynamoDB | Cart items, session state | Key-value by customer_id | 30 days TTL for abandoned carts |
| Order Records | RDS (PostgreSQL) | Orders, line items, return requests | Primary key + status index lookups | 2 years active; then S3 archive |
| Payment Records | RDS (PostgreSQL) | Transactions, refunds | Primary key + order_id lookups | 7 years (regulatory) |
| Delivery Records | RDS (PostgreSQL) | Assignments, attempt logs | Zone + staff + date range queries | 2 years active |
| POD Artifacts | S3 | Signature images, delivery photos | Object key by order_id | 5 years; lifecycle to Glacier |
| Milestones | DynamoDB | Status timeline per order | order_id sort key by timestamp | 2 years TTL |
| Search Index | OpenSearch | Product search index | Full-text + structured queries | Mirrors catalog (real-time sync) |

## Data Privacy and Retention

- **PII fields** (customer name, email, phone, addresses) are encrypted at rest in RDS and can be purged on account deletion (right to erasure).
- **Payment tokens** are stored; raw card numbers are never persisted (PCI-DSS).
- **POD photos** may contain identifiable information; access is restricted to order owner, admin, and finance roles via signed S3 URLs with 1-hour expiry.
- **Audit logs** are immutable and retained for 1 year in CloudWatch Logs, then archived to S3 Glacier for long-term compliance.
