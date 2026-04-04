# System Context Diagram

## Overview

This document presents the C4 Level-0 system context diagram for the Order Management and Delivery System, identifying the system boundary, all external actors, and integrated external systems.

## System Context

The Order Management and Delivery System sits at the centre of the operational ecosystem, interacting with customers via web/mobile interfaces, internal staff via operational dashboards, and external services for payments, notifications, and storage.

```mermaid
graph TB
    subgraph External_Users["External Users"]
        CU["👤 Customer<br/>Browses, orders, tracks,<br/>returns via web/mobile"]
        WS["👷 Warehouse Staff<br/>Picks, packs, inspects<br/>via warehouse dashboard"]
        DS["🚚 Delivery Staff<br/>Delivers, captures POD<br/>via mobile app"]
        OM["📊 Operations Manager<br/>Monitors, reassigns<br/>via ops dashboard"]
        AD["🔧 Admin<br/>Configures platform<br/>via admin portal"]
        FN["💰 Finance<br/>Reconciles payments<br/>via finance portal"]
    end

    OMS["📦 Order Management<br/>and Delivery System<br/><br/>Manages orders, fulfillment,<br/>internal delivery, payments,<br/>returns, and analytics"]

    subgraph External_Systems["External Systems"]
        PG["💳 Payment Gateway<br/>(Stripe / Khalti)<br/>Payment capture and refunds"]
        SES["📧 Amazon SES<br/>Transactional email delivery"]
        SNS["📱 Amazon SNS<br/>SMS delivery"]
        PIN["🔔 Amazon Pinpoint<br/>Push notification delivery"]
        S3["📁 Amazon S3<br/>POD photos, product images,<br/>invoices, reports"]
        COG["🔐 Amazon Cognito<br/>Authentication, MFA, RBAC"]
    end

    CU -->|"Browse, order, track, return<br/>(HTTPS/REST)"| OMS
    WS -->|"Pick, pack, inspect<br/>(HTTPS/REST)"| OMS
    DS -->|"Deliver, update status, POD<br/>(HTTPS/REST)"| OMS
    OM -->|"Monitor, reassign, configure<br/>(HTTPS/REST)"| OMS
    AD -->|"Configure, manage catalog/staff<br/>(HTTPS/REST)"| OMS
    FN -->|"Reconcile, refund<br/>(HTTPS/REST)"| OMS

    OMS -->|"Capture, refund<br/>(HTTPS/REST)"| PG
    OMS -->|"Send email<br/>(AWS SDK)"| SES
    OMS -->|"Send SMS<br/>(AWS SDK)"| SNS
    OMS -->|"Send push<br/>(AWS SDK)"| PIN
    OMS -->|"Store/retrieve files<br/>(AWS SDK)"| S3
    OMS -->|"Authenticate, authorize<br/>(AWS SDK)"| COG
```

## Interaction Summary

| Actor / System | Direction | Protocol | Data Exchanged |
|---|---|---|---|
| Customer | Inbound | HTTPS/REST | Browse, cart, checkout, order, return requests |
| Warehouse Staff | Inbound | HTTPS/REST | Pick list queries, scan verification, pack confirmation, inspection results |
| Delivery Staff | Inbound | HTTPS/REST | Assignment queries, status updates, POD uploads |
| Operations Manager | Inbound | HTTPS/REST | Dashboard queries, reassignment commands, zone configuration |
| Admin | Inbound | HTTPS/REST | Catalog CRUD, staff CRUD, config changes, audit log queries |
| Finance | Inbound | HTTPS/REST | Reconciliation reports, manual refund commands |
| Payment Gateway | Outbound | HTTPS/REST | Authorization, capture, refund requests; webhook callbacks |
| Amazon SES | Outbound | AWS SDK | Email send requests, delivery receipts |
| Amazon SNS | Outbound | AWS SDK | SMS publish requests, delivery receipts |
| Amazon Pinpoint | Outbound | AWS SDK | Push notification requests, engagement events |
| Amazon S3 | Outbound | AWS SDK | Object put/get for POD, images, invoices, reports |
| Amazon Cognito | Outbound | AWS SDK | Sign-up, sign-in, token validation, user pool management |

## Trust Boundaries

| Boundary | Inside | Outside | Controls |
|---|---|---|---|
| API Gateway | All backend services | All client applications | JWT validation, rate limiting, WAF, TLS termination |
| VPC Private Subnets | Lambda, Fargate, RDS, ElastiCache | Public internet, API Gateway | Security groups, NACLs, NAT gateway for outbound |
| Cognito User Pool | Authenticated sessions | Unauthenticated requests | OAuth 2.0 / OIDC flows, MFA, password policies |
| Payment Boundary | Internal payment records | Payment gateway | Tokenisation, PCI-DSS scope isolation, no raw card data |
