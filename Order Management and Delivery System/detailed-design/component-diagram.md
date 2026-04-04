# Component Diagram

## Overview

UML component diagrams showing the internal structure and dependencies of each microservice in the Order Management and Delivery System.

## System-Level Component View

```mermaid
graph TB
    subgraph ClientLayer["Client Layer"]
        CSpa["Customer SPA"]
        StaffApp["Staff Mobile App"]
        AdminSpa["Admin Portal"]
    end

    subgraph GatewayLayer["Gateway Layer"]
        APIGW["API Gateway"]
        Auth["Cognito Authorizer"]
    end

    subgraph ServiceLayer["Service Layer"]
        OrderSvc["Order Service"]
        PaymentSvc["Payment Service"]
        InventorySvc["Inventory Service"]
        FulfillSvc["Fulfillment Service"]
        DeliverySvc["Delivery Service"]
        ReturnSvc["Return Service"]
        NotifSvc["Notification Service"]
        AnalyticsSvc["Analytics Service"]
        SearchSync["Search Sync Service"]
    end

    subgraph EventLayer["Event Layer"]
        EventBridge["EventBridge"]
        StepFunctions["Step Functions"]
        DLQ["SQS DLQs"]
    end

    subgraph DataLayer["Data Layer"]
        RDS["PostgreSQL (RDS)"]
        DynamoDB["DynamoDB"]
        Redis["ElastiCache Redis"]
        OpenSearch["OpenSearch"]
        S3["S3"]
    end

    ClientLayer --> GatewayLayer
    GatewayLayer --> ServiceLayer
    ServiceLayer --> EventLayer
    ServiceLayer --> DataLayer
    EventLayer --> ServiceLayer
    EventLayer --> DLQ
```

## Order Service Components

```mermaid
graph TB
    subgraph OrderService["Order Service (Lambda)"]
        API["API Handler<br/>REST endpoint routing"]
        SM["State Machine Engine<br/>Transition validation"]
        Calc["Price Calculator<br/>Tax, shipping, discount"]
        Idemp["Idempotency Guard<br/>Duplicate request detection"]
        Publish["Event Publisher<br/>EventBridge integration"]
        Repo["Order Repository<br/>PostgreSQL access"]
        MilestoneRepo["Milestone Repository<br/>DynamoDB access"]
        CacheClient["Cache Client<br/>ElastiCache access"]
    end

    API --> SM
    API --> Calc
    API --> Idemp
    SM --> Repo
    SM --> Publish
    Calc --> Repo
    Idemp --> CacheClient
    API --> MilestoneRepo
```

## Delivery Service Components

```mermaid
graph TB
    subgraph DeliveryService["Delivery Service (Fargate)"]
        DAPI["API Handler<br/>REST endpoint routing"]
        Assign["Assignment Engine<br/>Zone matching, capacity check"]
        StatusMgr["Status Manager<br/>Milestone state transitions"]
        PODMgr["POD Manager<br/>Upload, validation, linking"]
        Reschedule["Rescheduler<br/>Failed delivery retry logic"]
        DRepo["Assignment Repository<br/>PostgreSQL access"]
        DPub["Event Publisher<br/>EventBridge integration"]
        S3Client["S3 Client<br/>POD artifact storage"]
        DMilestone["Milestone Writer<br/>DynamoDB access"]
    end

    DAPI --> Assign
    DAPI --> StatusMgr
    DAPI --> PODMgr
    StatusMgr --> DRepo
    StatusMgr --> DPub
    StatusMgr --> DMilestone
    PODMgr --> S3Client
    PODMgr --> DRepo
    Assign --> DRepo
    Reschedule --> Assign
    Reschedule --> DPub
```

## Payment Service Components

```mermaid
graph TB
    subgraph PaymentService["Payment Service (Lambda)"]
        PAPI["API Handler<br/>REST endpoint routing"]
        Capture["Capture Handler<br/>Authorization and capture"]
        Refund["Refund Handler<br/>Full and partial refunds"]
        Failover["Gateway Failover<br/>Primary/secondary routing"]
        Reconcile["Reconciliation Engine<br/>Daily settlement matching"]
        GWClient["Gateway Client<br/>Stripe/Khalti SDK"]
        PRepo["Payment Repository<br/>PostgreSQL access"]
        PPub["Event Publisher<br/>EventBridge integration"]
    end

    PAPI --> Capture
    PAPI --> Refund
    PAPI --> Reconcile
    Capture --> Failover
    Refund --> GWClient
    Failover --> GWClient
    Capture --> PRepo
    Capture --> PPub
    Refund --> PRepo
    Refund --> PPub
    Reconcile --> PRepo
```

## Component Dependencies Matrix

| Service | Depends On | Communication | Data Owned |
|---|---|---|---|
| Order Service | Inventory Service, Payment Service, EventBridge, RDS, DynamoDB, Redis | Sync (API) + Async (events) | orders, order_line_items, order_milestones |
| Payment Service | Payment Gateway, EventBridge, RDS | Sync (API + gateway) + Async (events) | payment_transactions, refund_records |
| Inventory Service | EventBridge, RDS, Redis | Sync (API) + Async (events) | inventory, inventory_reservations |
| Fulfillment Service | Order Service, EventBridge, Step Functions, RDS | Sync (API) + Async (events + workflows) | fulfillment_tasks |
| Delivery Service | EventBridge, RDS, DynamoDB, S3 | Sync (API) + Async (events) | delivery_assignments, proof_of_delivery |
| Return Service | Payment Service, Inventory Service, EventBridge, RDS | Sync (API) + Async (events) | return_requests, return_pickups |
| Notification Service | SES, SNS, Pinpoint, EventBridge, RDS | Async (events) | notification_records, notification_templates |
| Analytics Service | RDS (read replica), OpenSearch | Sync (API read-only) | Materialized views, report exports |
| Search Sync | OpenSearch, EventBridge | Async (events) | OpenSearch index (mirror) |
