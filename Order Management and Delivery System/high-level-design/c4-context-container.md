# C4 Context and Container Diagrams

## C4 Context Diagram

```mermaid
graph TB
    C["👤 Customer<br/>[Person]<br/>Browses catalog, places orders,<br/>tracks delivery, requests returns"]
    WS["👷 Warehouse Staff<br/>[Person]<br/>Picks, packs, inspects<br/>returned items"]
    DS["🚚 Delivery Staff<br/>[Person]<br/>Delivers orders, captures POD,<br/>collects returns"]
    OM["📊 Operations Manager<br/>[Person]<br/>Monitors fulfillment, manages<br/>zones and assignments"]
    AD["🔧 Admin<br/>[Person]<br/>Manages catalog, staff,<br/>configuration, analytics"]

    OMS["📦 Order Management and<br/>Delivery System<br/>[Software System]<br/>Manages the complete order-to-delivery<br/>lifecycle with internal delivery staff"]

    PG["💳 Payment Gateway<br/>[External System]<br/>Stripe / Khalti —<br/>processes payments and refunds"]
    AWS_MSG["📨 AWS Messaging<br/>[External System]<br/>SES, SNS, Pinpoint —<br/>email, SMS, push delivery"]

    C -->|"Places orders, tracks status,<br/>manages returns [HTTPS/REST]"| OMS
    WS -->|"Pick-pack workflow,<br/>inspections [HTTPS/REST]"| OMS
    DS -->|"Delivery status updates,<br/>POD uploads [HTTPS/REST]"| OMS
    OM -->|"Dashboard, reassignments,<br/>zone config [HTTPS/REST]"| OMS
    AD -->|"Catalog, staff, config<br/>management [HTTPS/REST]"| OMS
    OMS -->|"Capture, refund<br/>[HTTPS/REST]"| PG
    OMS -->|"Send notifications<br/>[AWS SDK]"| AWS_MSG
```

## C4 Container Diagram

```mermaid
graph TB
    subgraph Clients["Client Applications"]
        SPA["Customer Web SPA<br/>[Container: React]<br/>Product browsing, cart,<br/>checkout, order tracking"]
        STAFF_APP["Staff Mobile App<br/>[Container: React Native]<br/>Delivery status, POD capture,<br/>pick-pack dashboard"]
        ADMIN_SPA["Admin Portal<br/>[Container: React]<br/>Catalog, staff, config,<br/>analytics dashboards"]
    end

    subgraph OMS["Order Management and Delivery System"]
        APIGW["API Gateway<br/>[Container: Amazon API Gateway]<br/>REST API routing, JWT validation,<br/>rate limiting, WAF integration"]

        ORDER_SVC["Order Service<br/>[Container: AWS Lambda — Node.js]<br/>Order lifecycle, state machine,<br/>idempotency, milestone recording"]

        PAYMENT_SVC["Payment Service<br/>[Container: AWS Lambda — Node.js]<br/>Payment capture and refund,<br/>gateway failover, reconciliation"]

        INVENTORY_SVC["Inventory Service<br/>[Container: AWS Lambda — Node.js]<br/>Stock reservation, release,<br/>adjustment, low-stock alerting"]

        NOTIF_SVC["Notification Service<br/>[Container: AWS Lambda — Node.js]<br/>Template rendering, multi-channel<br/>dispatch, delivery tracking"]

        FULFILL_SVC["Fulfillment Service<br/>[Container: AWS Fargate — Node.js]<br/>Pick-pack workflow, barcode<br/>validation, manifest generation"]

        DELIVERY_SVC["Delivery Service<br/>[Container: AWS Fargate — Node.js]<br/>Assignment, status tracking,<br/>POD management, rescheduling"]

        RETURN_SVC["Return Service<br/>[Container: AWS Fargate — Node.js]<br/>Eligibility, pickup assignment,<br/>inspection, refund trigger"]

        ANALYTICS_SVC["Analytics Service<br/>[Container: AWS Fargate — Node.js]<br/>Dashboard aggregation,<br/>report generation, KPIs"]

        SEARCH_SYNC["Search Sync<br/>[Container: AWS Lambda — Node.js]<br/>Catalog sync to<br/>OpenSearch index"]

        EVENT_BUS["Event Bus<br/>[Container: Amazon EventBridge]<br/>Domain event routing,<br/>decoupled communication"]

        STEP_FN["Workflow Engine<br/>[Container: AWS Step Functions]<br/>Fulfillment orchestration,<br/>return processing pipelines"]

        RDS_DB["Primary Database<br/>[Container: Amazon RDS PostgreSQL]<br/>Orders, products, inventory,<br/>staff, payments, returns"]

        DDB["Timeline Store<br/>[Container: Amazon DynamoDB]<br/>Cart items, order milestones,<br/>session data"]

        CACHE["Cache<br/>[Container: Amazon ElastiCache Redis]<br/>Cart hot-path, sessions,<br/>idempotency keys"]

        SEARCH["Search Engine<br/>[Container: Amazon OpenSearch]<br/>Full-text product search,<br/>order search, analytics"]

        OBJ_STORE["Object Storage<br/>[Container: Amazon S3]<br/>POD photos, product images,<br/>invoices, reports"]
    end

    subgraph External["External Systems"]
        PG["Payment Gateway<br/>[External: Stripe / Khalti]"]
        SES["Amazon SES"]
        SNS["Amazon SNS"]
        PIN["Amazon Pinpoint"]
        COG["Amazon Cognito<br/>[External: Auth Provider]"]
    end

    SPA --> APIGW
    STAFF_APP --> APIGW
    ADMIN_SPA --> APIGW

    APIGW --> COG
    APIGW --> ORDER_SVC
    APIGW --> PAYMENT_SVC
    APIGW --> INVENTORY_SVC
    APIGW --> FULFILL_SVC
    APIGW --> DELIVERY_SVC
    APIGW --> RETURN_SVC
    APIGW --> ANALYTICS_SVC

    ORDER_SVC --> RDS_DB
    ORDER_SVC --> DDB
    ORDER_SVC --> CACHE
    ORDER_SVC --> EVENT_BUS

    PAYMENT_SVC --> RDS_DB
    PAYMENT_SVC --> PG
    PAYMENT_SVC --> EVENT_BUS

    INVENTORY_SVC --> RDS_DB
    INVENTORY_SVC --> CACHE
    INVENTORY_SVC --> EVENT_BUS

    FULFILL_SVC --> RDS_DB
    FULFILL_SVC --> EVENT_BUS
    FULFILL_SVC --> STEP_FN

    DELIVERY_SVC --> RDS_DB
    DELIVERY_SVC --> DDB
    DELIVERY_SVC --> OBJ_STORE
    DELIVERY_SVC --> EVENT_BUS

    RETURN_SVC --> RDS_DB
    RETURN_SVC --> EVENT_BUS

    ANALYTICS_SVC --> RDS_DB
    ANALYTICS_SVC --> SEARCH

    SEARCH_SYNC --> SEARCH
    EVENT_BUS --> SEARCH_SYNC

    NOTIF_SVC --> SES
    NOTIF_SVC --> SNS
    NOTIF_SVC --> PIN
    EVENT_BUS --> NOTIF_SVC

    EVENT_BUS --> ORDER_SVC
    EVENT_BUS --> INVENTORY_SVC
    EVENT_BUS --> DELIVERY_SVC
    EVENT_BUS --> RETURN_SVC

    STEP_FN --> ORDER_SVC
    STEP_FN --> INVENTORY_SVC
```

## Container Responsibilities and Communication

| Container | Runtime | Communication Style | Data Owned |
|---|---|---|---|
| API Gateway | Managed | Synchronous REST | None (stateless proxy) |
| Order Service | Lambda | Sync (API) + Async (EventBridge) | orders, order_line_items, order_milestones |
| Payment Service | Lambda | Sync (API + Gateway) + Async (EventBridge) | payment_transactions, refund_records |
| Inventory Service | Lambda | Sync (API) + Async (EventBridge) | inventory, inventory_reservations |
| Notification Service | Lambda | Async (EventBridge consumer) | notification_records, notification_templates |
| Fulfillment Service | Fargate | Sync (API) + Async (EventBridge + Step Functions) | fulfillment_tasks, packing_slips |
| Delivery Service | Fargate | Sync (API) + Async (EventBridge) | delivery_assignments, proof_of_delivery |
| Return Service | Fargate | Sync (API) + Async (EventBridge) | return_requests, return_inspections |
| Analytics Service | Fargate | Sync (API, read-only) | Derived metrics (materialized views) |
| Search Sync | Lambda | Async (EventBridge consumer) | OpenSearch index (mirror) |
