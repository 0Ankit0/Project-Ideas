# Architecture Diagram

## Overview

This document presents the AWS solution architecture for the Order Management and Delivery System, showing all major components, their interactions, and the technology choices.

## Solution Architecture

```mermaid
graph TB
    subgraph Clients["Client Applications"]
        CWeb["Customer Web SPA<br/>(React on CloudFront)"]
        SMob["Staff Mobile App<br/>(React Native)"]
        Admin["Admin Portal<br/>(React on CloudFront)"]
    end

    subgraph Edge["Edge Layer"]
        CF["Amazon CloudFront<br/>CDN + SPA hosting"]
        WAF["AWS WAF<br/>OWASP Top 10 protection"]
        APIGW["Amazon API Gateway<br/>REST APIs, JWT validation,<br/>rate limiting, usage plans"]
    end

    subgraph Auth["Authentication"]
        COG["Amazon Cognito<br/>User pools, MFA, RBAC"]
    end

    subgraph Compute["Compute Layer"]
        subgraph Lambda["AWS Lambda Functions"]
            LOrder["Order Service"]
            LPayment["Payment Service"]
            LInventory["Inventory Service"]
            LNotif["Notification Service"]
            LSearch["Search Sync Service"]
        end
        subgraph Fargate["AWS Fargate Services"]
            FFulfill["Fulfillment Service"]
            FDelivery["Delivery Service"]
            FReturn["Return Service"]
            FAnalytics["Analytics Service"]
        end
    end

    subgraph EventDriven["Event-Driven Layer"]
        EB["Amazon EventBridge<br/>Custom event bus: oms.events"]
        SF["AWS Step Functions<br/>Fulfillment orchestration,<br/>return processing"]
        DLQ["Amazon SQS<br/>Dead letter queues"]
    end

    subgraph Data["Data Layer"]
        RDS["Amazon RDS<br/>PostgreSQL 15 Multi-AZ<br/>(Orders, Products, Staff)"]
        RR["RDS Read Replica<br/>(Reporting, Analytics)"]
        DDB["Amazon DynamoDB<br/>(Cart, Milestones, Sessions)"]
        REDIS["Amazon ElastiCache<br/>Redis Cluster<br/>(Cache, Idempotency, Rate Limit)"]
        OS["Amazon OpenSearch<br/>(Product Search, Order Search)"]
    end

    subgraph Storage["Storage Layer"]
        S3["Amazon S3<br/>(POD photos, product images,<br/>invoices, reports)"]
    end

    subgraph Notifications["Notification Channels"]
        SES["Amazon SES<br/>(Email)"]
        SNS["Amazon SNS<br/>(SMS)"]
        PIN["Amazon Pinpoint<br/>(Push)"]
    end

    subgraph Monitoring["Observability"]
        CW["Amazon CloudWatch<br/>(Metrics, Logs, Alarms)"]
        XR["AWS X-Ray<br/>(Distributed Tracing)"]
        AC["AWS AppConfig<br/>(Feature Flags)"]
    end

    subgraph CI_CD["CI/CD"]
        CP["AWS CodePipeline"]
        CB["AWS CodeBuild"]
        CDK["AWS CDK<br/>(Infrastructure as Code)"]
    end

    CWeb --> CF
    Admin --> CF
    SMob --> APIGW
    CF --> WAF --> APIGW
    APIGW --> COG
    APIGW --> Lambda
    APIGW --> Fargate

    LOrder --> RDS
    LOrder --> DDB
    LOrder --> REDIS
    LOrder --> EB

    LPayment --> RDS
    LPayment --> EB

    LInventory --> RDS
    LInventory --> REDIS
    LInventory --> EB

    LNotif --> SES
    LNotif --> SNS
    LNotif --> PIN

    LSearch --> OS

    FFulfill --> RDS
    FFulfill --> EB
    FFulfill --> SF

    FDelivery --> RDS
    FDelivery --> DDB
    FDelivery --> S3
    FDelivery --> EB

    FReturn --> RDS
    FReturn --> EB

    FAnalytics --> RR
    FAnalytics --> OS

    EB --> Lambda
    EB --> Fargate
    EB --> DLQ

    SF --> Lambda

    RDS --> RR

    CP --> CB --> CDK
```

## Component Responsibilities

| Component | Technology | Responsibilities |
|---|---|---|
| API Gateway | Amazon API Gateway | Request routing, JWT validation via Cognito authorizer, rate limiting, request/response transformation |
| Order Service | Lambda | Order CRUD, state machine transitions, idempotency enforcement, milestone recording |
| Payment Service | Lambda | Payment capture via gateway, refund processing, reconciliation report generation |
| Inventory Service | Lambda | Stock reservation/release, quantity adjustments, low-stock alerting |
| Notification Service | Lambda | Template rendering, multi-channel dispatch (SES/SNS/Pinpoint), delivery tracking |
| Search Sync Service | Lambda | DynamoDB Streams / EventBridge consumer syncing product data to OpenSearch |
| Fulfillment Service | Fargate | Pick-pack workflow management, barcode validation, manifest generation |
| Delivery Service | Fargate | Delivery assignment, status tracking, POD management, failed delivery handling |
| Return Service | Fargate | Return eligibility, pickup assignment, inspection result processing |
| Analytics Service | Fargate | Dashboard aggregation, report generation, KPI calculation |

## Cross-Cutting Concerns

| Concern | Implementation |
|---|---|
| Authentication | Cognito user pools with JWT; separate pools for customers and staff |
| Authorization | Cognito groups mapped to IAM roles; API Gateway authorizer enforces RBAC |
| Encryption in Transit | TLS 1.3 everywhere; API Gateway terminates TLS; internal calls use VPC endpoints |
| Encryption at Rest | RDS encryption (KMS), DynamoDB encryption, S3 SSE-S3, ElastiCache encryption |
| Logging | Structured JSON via CloudWatch Logs; correlation_id propagated across services |
| Tracing | X-Ray SDK in all Lambda/Fargate; trace segments for external calls |
| Feature Flags | AppConfig with deployment strategy for gradual rollouts |
| Secrets | AWS Secrets Manager for database credentials and API keys |
