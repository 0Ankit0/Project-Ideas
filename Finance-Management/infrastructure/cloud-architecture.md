# Cloud Architecture Diagram

## Overview
Cloud architecture design for the Finance Management System on AWS. This document represents the target-state infrastructure design for a production-grade, highly available, and security-compliant financial system.

---

## AWS Architecture Overview

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Global Services"
            Route53[Route 53]
            CloudFront[CloudFront]
            WAF[AWS WAF]
            IAM[IAM]
            Shield[Shield Advanced]
        end

        subgraph "Primary Region (us-east-1)"
            subgraph "Compute"
                EKS[Amazon EKS]
                Lambda[AWS Lambda]
            end

            subgraph "Storage"
                S3[Amazon S3<br>Encrypted]
                EBS[Amazon EBS<br>GP3]
            end

            subgraph "Database"
                RDS[(Amazon RDS<br>PostgreSQL Multi-AZ)]
                AuditRDS[(Amazon RDS<br>Audit Log DB<br>Append-Only)]
                ElastiCache[(ElastiCache<br>Redis Cluster)]
            end

            subgraph "Messaging"
                SQS[Amazon SQS<br>Report & Worker Jobs]
                SNS[Amazon SNS<br>Notifications]
            end

            subgraph "Security"
                SecretsManager[Secrets Manager]
                KMS[AWS KMS<br>CMK per tenant]
                ACM[ACM]
                Macie[Amazon Macie<br>PII Detection]
            end

            subgraph "Monitoring"
                CloudWatch[CloudWatch]
                XRay[X-Ray]
                SecurityHub[Security Hub]
                GuardDuty[GuardDuty]
                CloudTrail[CloudTrail]
            end

            subgraph "Networking"
                VPC[VPC]
                ALB[ALB]
                PrivateLink[VPC PrivateLink]
            end
        end

        subgraph "DR Region (us-west-2)"
            EKS_DR[EKS - Standby]
            RDS_DR[(RDS - Read Replica)]
            AuditRDS_DR[(Audit DB - Replica)]
            S3_DR[S3 - CRR Replica]
        end
    end

    Route53 --> CloudFront
    CloudFront --> Shield
    Shield --> WAF
    WAF --> ALB
    ALB --> EKS

    EKS --> RDS
    EKS --> AuditRDS
    EKS --> ElastiCache
    EKS --> SQS
    EKS --> S3
    EKS --> SecretsManager
    SecretsManager --> KMS
    KMS --> RDS
    KMS --> S3

    CloudWatch --> EKS
    XRay --> EKS
    GuardDuty --> SecurityHub
    CloudTrail --> SecurityHub
    Macie --> SecurityHub

    RDS -.->|Async Replication| RDS_DR
    AuditRDS -.->|Replication| AuditRDS_DR
    S3 -.->|Cross-Region Replication| S3_DR
```

---

## Detailed AWS Service Architecture

```mermaid
graph TB
    subgraph "Finance Users"
        Users[Finance Users]
    end

    subgraph "Edge & CDN"
        R53[Route 53<br>DNS + Health Checks]
        CF[CloudFront<br>Web Asset CDN]
        WAF[AWS WAF<br>OWASP + Finance Rules]
        Shield[AWS Shield Advanced<br>DDoS Protection]
    end

    subgraph "Load Balancing"
        ALB[Application Load Balancer<br>Layer 7 Routing + mTLS]
    end

    subgraph "Container Platform"
        EKS[Amazon EKS<br>Finance API and Workers]

        subgraph "EKS Node Groups"
            NG_App[App Node Group<br>m6i.2xlarge x 4]
            NG_Worker[Worker Node Group<br>m6i.large x 3<br>Payroll / Report Jobs]
        end

        ECR[Amazon ECR<br>Container Registry]
    end

    subgraph "Serverless"
        Lambda[AWS Lambda<br>Bank Feed Processing]
        StepFunctions[Step Functions<br>Payroll Approval Workflow]
    end

    subgraph "Data Stores"
        RDS[(Amazon RDS<br>PostgreSQL 15<br>Multi-AZ + Read Replica)]
        AuditRDS[(Audit Log RDS<br>INSERT-only role<br>7-year retention)]
        EC[(ElastiCache<br>Redis Cluster<br>FX rates, sessions)]
    end

    subgraph "Document Storage"
        S3_Docs[S3 - Financial Documents<br>Invoices, Pay Stubs<br>AES-256 Encrypted]
        S3_Reports[S3 - Report Artifacts<br>Lifecycle: Glacier 2yr]
        S3_BankFiles[S3 - Bank Transfer Files<br>Short-lived presigned URLs]
        S3_Backups[S3 - DB Backups<br>30-day retention]
    end

    subgraph "Messaging"
        SQS[Amazon SQS<br>Report Jobs, Notifications]
        SNS[Amazon SNS<br>Budget Alerts, Approvals]
        EventBridge[EventBridge<br>GL Posting Events]
    end

    subgraph "Communication"
        SES[Amazon SES<br>Approval Emails<br>Remittance Advices]
        Pinpoint[Amazon Pinpoint<br>SMS and Push]
    end

    Users --> R53
    R53 --> CF
    CF --> Shield
    Shield --> WAF
    WAF --> ALB
    ALB --> EKS
    ECR --> EKS

    EKS --> RDS
    EKS --> AuditRDS
    EKS --> EC
    EKS --> SQS
    EKS --> EventBridge

    Lambda --> SES
    Lambda --> Pinpoint
    SQS --> Lambda
    EventBridge --> Lambda

    EKS --> S3_Docs
    EKS --> S3_Reports
    EKS --> S3_BankFiles
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Perimeter Security"
        WAF[AWS WAF<br>OWASP Top 10 Rules<br>Finance-Specific Rules]
        Shield[Shield Advanced<br>DDoS Protection]
        Firewall[AWS Network Firewall<br>Egress Filtering]
    end

    subgraph "Identity & Access"
        IAMRoles[IAM Roles<br>Least Privilege]
        STS[STS<br>Temporary Credentials]
        SecretsManager[Secrets Manager<br>DB Credentials, API Keys]
    end

    subgraph "Data Protection"
        KMS[AWS KMS<br>CMK per Entity/Tenant]
        Macie[Amazon Macie<br>PII / Financial Data Detection]
        ACM[ACM<br>TLS Certificates]
    end

    subgraph "Detection & Compliance"
        GuardDuty[GuardDuty<br>Threat Detection]
        SecurityHub[Security Hub<br>Compliance Dashboard]
        CloudTrail[CloudTrail<br>All API Calls Logged]
        Config[AWS Config<br>CIS Benchmark Rules]
        Inspector[Amazon Inspector<br>Container Vulnerability Scan]
    end

    subgraph "Database Security"
        RDS_Encrypt[RDS<br>Storage Encryption KMS]
        RDS_IAM[RDS IAM Auth<br>No password access]
        AuditDB[Audit Log DB<br>INSERT-only role]
    end

    WAF --> ALB
    IAMRoles --> EKS
    KMS --> RDS_Encrypt
    SecretsManager --> EKS
    Macie --> S3
    GuardDuty --> SecurityHub
    CloudTrail --> SecurityHub
    Config --> SecurityHub
    Inspector --> ECR
```

---

## Monitoring & Observability

```mermaid
graph TB
    subgraph "Data Sources"
        EKS[EKS API Pods]
        Worker[EKS Worker Pods]
        RDS[(RDS)]
        ALB[ALB]
        Lambda[Lambda]
    end

    subgraph "Collection"
        OTEL[OpenTelemetry Collector]
        FluentBit[Fluent Bit<br>Log Forwarding]
        CWAgent[CloudWatch Agent]
    end

    subgraph "Monitoring"
        CloudWatch[CloudWatch<br>Metrics & Logs]
        XRay[X-Ray<br>Distributed Tracing]
        Prometheus[Managed Prometheus]
    end

    subgraph "Visualization"
        Grafana[Managed Grafana<br>Finance Operations Dashboard]
        CWDash[CloudWatch Dashboards<br>System Health]
    end

    subgraph "Alerting"
        SNS[SNS Alert Topic]
        PagerDuty[PagerDuty<br>On-Call Escalation]
        Slack[Slack<br>Finance Ops Channel]
    end

    EKS --> OTEL
    EKS --> FluentBit
    Worker --> OTEL
    RDS --> CWAgent
    ALB --> CloudWatch
    Lambda --> CloudWatch

    OTEL --> XRay
    OTEL --> Prometheus
    FluentBit --> CloudWatch
    CWAgent --> CloudWatch

    Prometheus --> Grafana
    CloudWatch --> CWDash
    CloudWatch --> SNS
    SNS --> PagerDuty
    SNS --> Slack
```

---

## AWS Services Summary

| Category | Service | Purpose |
|----------|---------|---------|
| **Compute** | EKS | Finance API and worker container orchestration |
| | Lambda | Bank feed processing, notification dispatch |
| | Step Functions | Payroll and approval workflow state machines |
| **Storage** | S3 | Financial documents, reports, bank files (encrypted) |
| | EBS GP3 | EKS node block storage |
| **Database** | RDS PostgreSQL | Primary transactional database (Multi-AZ) |
| | Audit Log RDS | Append-only audit trail database |
| | ElastiCache Redis | Session tokens, FX rates, report cache |
| **Messaging** | SQS | Report job queues, notification queues |
| | SNS | Budget alerts, approval notifications |
| | EventBridge | GL posting event bus |
| **Networking** | VPC | Network isolation |
| | ALB | Layer 7 load balancing with mTLS |
| | CloudFront | CDN for static assets |
| | Route 53 | DNS and health checks |
| **Security** | WAF | OWASP and finance-specific rule groups |
| | KMS | CMK encryption for financial data at rest |
| | Secrets Manager | Credential management (DB, APIs, bank keys) |
| | Macie | PII detection in S3 |
| | GuardDuty | Threat detection |
| | CloudTrail | API-level audit logging |
| | Config | Compliance rule enforcement |
| **Monitoring** | CloudWatch | Metrics, logs, dashboards |
| | X-Ray | Distributed tracing |
| | Prometheus + Grafana | Finance operations dashboard |

---

## Estimated Monthly Costs

| Component | Specification | Est. Monthly Cost |
|-----------|---------------|-------------------|
| EKS Cluster | Control plane + 7 nodes | $1,400 |
| EC2 Instances | 7 x m6i.2xlarge | $4,800 |
| RDS PostgreSQL | db.r6g.2xlarge Multi-AZ + Read Replica | $2,500 |
| Audit Log RDS | db.r6g.large | $600 |
| ElastiCache | 3-node cluster | $900 |
| S3 Storage | 2 TB + lifecycle to Glacier | $200 |
| CloudFront | 5 TB transfer | $425 |
| Security (WAF, GuardDuty, Macie) | Standard usage | $1,200 |
| Lambda + SQS + SNS | Standard usage | $300 |
| **Total** | | **~$12,300/month** |

> Note: Costs are estimates and vary based on actual usage, region, and reserved instance commitments.
