# Cloud Architecture Diagram

## Overview
This document describes the cloud architecture for the CMS platform deployed on AWS. The design is cloud-provider-agnostic and maps directly to equivalent GCP and Azure services.

---

## AWS Cloud Architecture

```mermaid
graph TB
    subgraph "Global"
        Route53[Route 53<br>DNS]
        CloudFront[CloudFront<br>CDN + WAF]
        ACM[ACM<br>TLS Certificates]
        S3Media[S3 Bucket<br>Media Assets]
        S3Exports[S3 Bucket<br>Report Exports & Backups]
    end

    subgraph "AWS Region — Primary"
        subgraph "Availability Zone A"
            ALB[Application Load Balancer]

            subgraph "EKS Node Group A"
                APIA[CMS API Pod]
                WorkerA[Worker Pod]
                FrontendA[Frontend Pod]
            end

            RDSPrimary[(RDS PostgreSQL<br>Multi-AZ Primary)]
            ElastiCachePrimary[(ElastiCache Redis<br>Primary node)]
        end

        subgraph "Availability Zone B"
            subgraph "EKS Node Group B"
                APIB[CMS API Pod]
                WorkerB[Worker Pod]
                FrontendB[Frontend Pod]
            end

            RDSStandby[(RDS PostgreSQL<br>Multi-AZ Standby)]
            ElastiCacheReplica[(ElastiCache Redis<br>Replica node)]
        end

        subgraph "Shared Services"
            EKS[Amazon EKS<br>Kubernetes control plane]
            ECR[ECR<br>Container Registry]
            SES[SES<br>Email Service]
            Meilisearch[Meilisearch<br>EC2 or EKS StatefulSet]
            CloudWatch[CloudWatch<br>Logs, Metrics, Alarms]
            XRay[X-Ray<br>Distributed Tracing]
            SecretsManager[Secrets Manager<br>DB credentials, API keys]
        end
    end

    subgraph "AWS Region — DR / Read Replica"
        RDSReplica[(RDS Read Replica<br>Cross-region)]
        S3Replica[S3 Replication<br>Media backup]
    end

    Route53 --> CloudFront
    CloudFront --> ALB
    CloudFront --> S3Media
    ACM --> CloudFront
    ACM --> ALB

    ALB --> APIA
    ALB --> APIB
    ALB --> FrontendA
    ALB --> FrontendB

    APIA --> RDSPrimary
    APIA --> ElastiCachePrimary
    APIA --> Meilisearch
    APIA --> S3Media
    APIA --> SES
    APIA --> SecretsManager

    WorkerA --> RDSPrimary
    WorkerA --> ElastiCachePrimary
    WorkerA --> S3Media
    WorkerA --> SES

    RDSPrimary --> RDSStandby
    RDSPrimary --> RDSReplica
    ElastiCachePrimary --> ElastiCacheReplica
    S3Media --> S3Replica

    EKS --> APIA
    EKS --> APIB
    EKS --> WorkerA
    EKS --> WorkerB
    ECR --> EKS
    CloudWatch --> APIA
    XRay --> APIA
    S3Exports --> CloudWatch
```

---

## Cloud Service Mapping

| Function | AWS | GCP | Azure |
|----------|-----|-----|-------|
| DNS | Route 53 | Cloud DNS | Azure DNS |
| CDN + WAF | CloudFront + AWS WAF | Cloud CDN + Cloud Armor | Azure Front Door |
| Load Balancer | ALB | Cloud Load Balancing | Azure App Gateway |
| Kubernetes | EKS | GKE | AKS |
| Container Registry | ECR | Artifact Registry | ACR |
| PostgreSQL | RDS PostgreSQL | Cloud SQL | Azure Database for PostgreSQL |
| Redis | ElastiCache | Memorystore | Azure Cache for Redis |
| Object Storage | S3 | Cloud Storage | Azure Blob Storage |
| Email | SES | — (use SendGrid) | Azure Communication Services |
| TLS Certificates | ACM | Google-managed SSL | App Service Managed Cert |
| Secrets | Secrets Manager | Secret Manager | Azure Key Vault |
| Logging | CloudWatch Logs | Cloud Logging | Azure Monitor Logs |
| Tracing | X-Ray | Cloud Trace | Azure Application Insights |
| CI/CD | CodePipeline / GitHub Actions | Cloud Build | Azure DevOps |

---

## Backup and Disaster Recovery

| Asset | Backup Method | RPO | RTO |
|-------|---------------|-----|-----|
| PostgreSQL | RDS automated snapshots (daily) + continuous WAL archiving | 1 h | 1 h |
| Redis | ElastiCache daily snapshot to S3 | 24 h | 30 min |
| Media (S3) | S3 versioning + cross-region replication | 1 h | 15 min |
| Search Index | Rebuilt from PostgreSQL on recovery | N/A | 2 h |
| Container Images | Immutable tags in ECR; multi-region replication | N/A | 5 min |

---

## Auto-Scaling Configuration

| Component | Metric | Min | Max |
|-----------|--------|-----|-----|
| CMS API Pods | CPU > 60% | 2 | 10 |
| Worker Pods | Redis queue depth > 100 | 2 | 8 |
| Frontend Pods | CPU > 70% | 2 | 6 |
| RDS | — | 1 primary | 1 primary + 1 replica |
| ElastiCache | — | 1 primary | 1 primary + 2 replicas |

---

## Cost Optimisation

| Strategy | Implementation |
|----------|---------------|
| CDN caching | Cache public posts, feeds, and sitemap at CDN for 5 min; media for 365 days |
| Spot / Preemptible nodes | Use spot instances for worker pods; on-demand for API pods |
| Read replicas | Route all public GET queries to RDS read replica |
| S3 lifecycle | Move exports older than 90 days to S3 Glacier |
| Reserved instances | Reserve 1-year term for RDS and ElastiCache primary nodes |
