# C4 Component Diagram

## Overview

C4 Component-level diagrams for the most critical services, showing their internal components and interactions.

## Order Service — Component View

```mermaid
graph TB
    subgraph OrderService["Order Service [Lambda — Node.js]"]
        direction TB
        OrderCtrl["Order Controller<br/>[Component]<br/>REST endpoint handling,<br/>request validation"]
        StateMachine["State Machine Engine<br/>[Component]<br/>Order lifecycle transitions,<br/>guard validation"]
        PriceCalc["Price Calculator<br/>[Component]<br/>Tax, shipping, discount<br/>computation"]
        IdempGuard["Idempotency Guard<br/>[Component]<br/>Duplicate detection via<br/>ElastiCache lookup"]
        OrderRepo["Order Repository<br/>[Component]<br/>PostgreSQL CRUD for<br/>orders and line items"]
        MilestoneWriter["Milestone Writer<br/>[Component]<br/>DynamoDB writes for<br/>order timeline"]
        EventPublisher["Event Publisher<br/>[Component]<br/>EventBridge publish with<br/>retry and correlation"]
    end

    APIGW["API Gateway"] --> OrderCtrl
    OrderCtrl --> IdempGuard
    OrderCtrl --> StateMachine
    OrderCtrl --> PriceCalc
    StateMachine --> OrderRepo
    StateMachine --> EventPublisher
    OrderCtrl --> MilestoneWriter
    IdempGuard --> Redis["ElastiCache Redis"]
    OrderRepo --> RDS["PostgreSQL (RDS)"]
    MilestoneWriter --> DDB["DynamoDB"]
    EventPublisher --> EB["EventBridge"]
```

## Delivery Service — Component View

```mermaid
graph TB
    subgraph DeliveryService["Delivery Service [Fargate — Node.js]"]
        direction TB
        DelCtrl["Delivery Controller<br/>[Component]<br/>REST endpoint handling"]
        AssignEngine["Assignment Engine<br/>[Component]<br/>Zone matching, capacity<br/>check, staff selection"]
        StatusMgr["Status Manager<br/>[Component]<br/>Milestone transitions,<br/>state validation"]
        PODHandler["POD Handler<br/>[Component]<br/>Signature and photo upload,<br/>validation, S3 storage"]
        RescheduleEngine["Reschedule Engine<br/>[Component]<br/>Failed delivery retry logic,<br/>window calculation"]
        DelRepo["Delivery Repository<br/>[Component]<br/>PostgreSQL CRUD for<br/>assignments"]
        DelMilestone["Milestone Writer<br/>[Component]<br/>DynamoDB timeline writes"]
        DelPublisher["Event Publisher<br/>[Component]<br/>EventBridge integration"]
    end

    APIGW2["API Gateway"] --> DelCtrl
    DelCtrl --> AssignEngine
    DelCtrl --> StatusMgr
    DelCtrl --> PODHandler
    StatusMgr --> DelRepo
    StatusMgr --> DelMilestone
    StatusMgr --> DelPublisher
    PODHandler --> S3["Amazon S3"]
    PODHandler --> DelRepo
    AssignEngine --> DelRepo
    RescheduleEngine --> AssignEngine
    RescheduleEngine --> DelPublisher
    DelRepo --> RDS2["PostgreSQL (RDS)"]
    DelMilestone --> DDB2["DynamoDB"]
    DelPublisher --> EB2["EventBridge"]
```

## Payment Service — Component View

```mermaid
graph TB
    subgraph PaymentService["Payment Service [Lambda — Node.js]"]
        direction TB
        PayCtrl["Payment Controller<br/>[Component]<br/>REST endpoint handling"]
        CaptureHandler["Capture Handler<br/>[Component]<br/>Authorization and<br/>payment capture"]
        RefundHandler["Refund Handler<br/>[Component]<br/>Full and partial<br/>refund processing"]
        FailoverRouter["Gateway Failover<br/>[Component]<br/>Primary/secondary<br/>gateway routing"]
        ReconcileEngine["Reconciliation Engine<br/>[Component]<br/>Daily settlement matching<br/>and discrepancy detection"]
        GatewayClient["Gateway Client<br/>[Component]<br/>Stripe/Khalti SDK<br/>wrapper with retry"]
        PayRepo["Payment Repository<br/>[Component]<br/>PostgreSQL CRUD"]
        PayPublisher["Event Publisher<br/>[Component]<br/>EventBridge integration"]
    end

    APIGW3["API Gateway"] --> PayCtrl
    PayCtrl --> CaptureHandler
    PayCtrl --> RefundHandler
    PayCtrl --> ReconcileEngine
    CaptureHandler --> FailoverRouter
    RefundHandler --> GatewayClient
    FailoverRouter --> GatewayClient
    GatewayClient --> PG["Payment Gateway<br/>(Stripe / Khalti)"]
    CaptureHandler --> PayRepo
    RefundHandler --> PayRepo
    ReconcileEngine --> PayRepo
    CaptureHandler --> PayPublisher
    RefundHandler --> PayPublisher
    PayRepo --> RDS3["PostgreSQL (RDS)"]
    PayPublisher --> EB3["EventBridge"]
```

## Notification Service — Component View

```mermaid
graph TB
    subgraph NotifService["Notification Service [Lambda — Node.js]"]
        direction TB
        EventHandler["Event Handler<br/>[Component]<br/>EventBridge consumer,<br/>event routing"]
        TemplateEngine["Template Engine<br/>[Component]<br/>Template lookup and<br/>variable substitution"]
        ChannelRouter["Channel Router<br/>[Component]<br/>Route to email, SMS,<br/>or push based on prefs"]
        EmailSender["Email Sender<br/>[Component]<br/>SES integration"]
        SMSSender["SMS Sender<br/>[Component]<br/>SNS integration"]
        PushSender["Push Sender<br/>[Component]<br/>Pinpoint integration"]
        NotifRepo["Notification Repository<br/>[Component]<br/>Template and delivery<br/>record storage"]
    end

    EB4["EventBridge"] --> EventHandler
    EventHandler --> TemplateEngine
    TemplateEngine --> NotifRepo
    TemplateEngine --> ChannelRouter
    ChannelRouter --> EmailSender
    ChannelRouter --> SMSSender
    ChannelRouter --> PushSender
    EmailSender --> SES["Amazon SES"]
    SMSSender --> SNS["Amazon SNS"]
    PushSender --> PIN["Amazon Pinpoint"]
    NotifRepo --> RDS4["PostgreSQL (RDS)"]
```
