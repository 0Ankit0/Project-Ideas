# Cloud Architecture Diagram

## Overview
Cloud architecture diagram for the Employee Management System on AWS, showing managed services, regions, and service integrations.

---

## AWS Cloud Architecture

```mermaid
graph TB
    subgraph "Users"
        Employees[Employees\nWeb + Mobile]
        HRAdmin[HR / Admin\nWeb Portal]
        Biometric[Biometric Devices]
    end

    subgraph "AWS Cloud"
        subgraph "Edge Services"
            Route53[Route 53\nDNS + Health Routing]
            CloudFront[CloudFront CDN\nWeb + Assets]
            WAF[AWS WAF + Shield\nSecurity]
            ACM[Certificate Manager\nSSL/TLS]
        end

        subgraph "Compute - EKS"
            EKS[EKS Cluster\nKubernetes]
            API[API Service\nFastAPI / Node.js]
            Workers[Async Workers\nCelery / BullMQ]
            WS[WebSocket Service]
        end

        subgraph "Database - RDS"
            RDS[RDS PostgreSQL\nMulti-AZ]
            RDS_Replica[Read Replica\nReporting]
        end

        subgraph "Caching"
            ElastiCache[ElastiCache Redis\nCluster Mode]
        end

        subgraph "Async Processing"
            SQS[SQS Queues\nPayroll, Notifications, Reports]
            EventBridge[EventBridge\nScheduled payroll cycles]
        end

        subgraph "Storage"
            S3_Docs[S3 - Documents\nEmployee & Policy Docs]
            S3_Payslips[S3 - Payslips\nEncrypted Payslips]
            S3_Reports[S3 - Reports\nGenerated Report Artifacts]
            S3_Static[S3 - Static Assets\nFrontend Build]
        end

        subgraph "Communication"
            SES[SES\nTransactional Email]
            SNS[SNS\nSMS + Push Notifications]
            Pinpoint[Amazon Pinpoint\nMobile Push]
        end

        subgraph "Security"
            IAM_AWS[IAM Roles & Policies\nService Identity]
            SecretsManager[Secrets Manager\nAPI Keys + DB Creds]
            KMS[KMS\nEncryption Key Management]
            Cognito[Cognito\nExternal SSO Integration]
        end

        subgraph "Observability"
            CloudWatch[CloudWatch\nLogs + Metrics + Alarms]
            XRay[X-Ray\nDistributed Tracing]
            SecurityHub[Security Hub\nCompliance + Alerts]
            Config[AWS Config\nInfrastructure Compliance]
        end
    end

    subgraph "External"
        ERPSystem[ERP / Accounting System]
        BankingAPI[Banking / Salary Disbursement]
        IdPSAML[Enterprise IdP\nSAML 2.0]
    end

    Employees --> Route53
    HRAdmin --> Route53
    Biometric -->|TLS| Route53

    Route53 --> CloudFront
    CloudFront --> WAF
    WAF --> EKS
    ACM --> CloudFront

    EKS --> API
    EKS --> Workers
    EKS --> WS

    API --> RDS
    API --> RDS_Replica
    API --> ElastiCache
    API --> SQS
    API --> S3_Docs
    API --> S3_Payslips
    API --> SecretsManager

    Workers --> SQS
    Workers --> RDS
    Workers --> SES
    Workers --> SNS
    Workers --> Pinpoint
    Workers --> BankingAPI
    Workers --> S3_Reports

    SQS --> Workers
    EventBridge --> SQS

    S3_Static --> CloudFront

    API --> CloudWatch
    API --> XRay
    Workers --> CloudWatch

    API <--> ERPSystem
    API <--> IdPSAML
    API --> Cognito

    KMS --> S3_Docs
    KMS --> S3_Payslips
    KMS --> RDS

    CloudWatch --> SecurityHub
    Config --> SecurityHub
```

---

## Multi-Environment Setup

| Environment | Purpose | Scale | Notes |
|-------------|---------|-------|-------|
| **Development** | Developer testing | Minimal (single pod) | Shared DB, no HA |
| **Staging** | Pre-production testing | Reduced (2 pods) | Mirrors production config |
| **Production** | Live system | Full HA (3+ pods) | Multi-AZ, DR enabled |
| **DR (Disaster Recovery)** | Failover | Standby (warm) | Cross-region replica |

---

## Cost Optimization Strategies

| Strategy | Implementation |
|----------|---------------|
| **Reserved Instances** | RDS and ElastiCache 1-year reservations for predictable workloads |
| **Spot Workers** | Async workers run on Spot instances with graceful termination handling |
| **S3 Lifecycle Policies** | Archive payslips older than 2 years to S3 Glacier |
| **CloudFront Caching** | Cache static assets aggressively; API responses with short TTLs |
| **Auto-Scaling** | HPA on CPU/memory for API pods; queue-depth scaling for workers |
| **Right-Sizing** | Periodic review of instance types based on CloudWatch metrics |
