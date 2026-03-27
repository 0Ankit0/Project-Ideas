# Deployment Diagram

## Overview
Deployment diagrams showing the mapping of the rental management system's software components to cloud infrastructure. The architecture targets a scaled production environment on AWS, but the design is cloud-agnostic.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Users / Clients]
    end

    subgraph "Edge Layer"
        DNS[Route 53 DNS]
        CloudFront[CloudFront CDN]
        WAF[AWS WAF]
    end

    subgraph "AWS Region - Primary"
        subgraph "VPC - Production"
            subgraph "Public Subnet AZ-A"
                ALB_A[Application Load Balancer]
                NAT_A[NAT Gateway]
            end

            subgraph "Public Subnet AZ-B"
                ALB_B[Application Load Balancer]
                NAT_B[NAT Gateway]
            end

            subgraph "Private Subnet AZ-A - Application"
                EKS_A[EKS Worker Nodes]
                Worker_A[Async Worker Nodes]
            end

            subgraph "Private Subnet AZ-B - Application"
                EKS_B[EKS Worker Nodes]
                Worker_B[Async Worker Nodes]
            end

            subgraph "Private Subnet AZ-A - Data"
                RDS_Primary[(RDS Primary<br>PostgreSQL)]
                ElastiCache_A[(ElastiCache Redis)]
            end

            subgraph "Private Subnet AZ-B - Data"
                RDS_Standby[(RDS Standby)]
                ElastiCache_B[(ElastiCache Redis)]
            end
        end

        EKS_Control[EKS Control Plane<br>AWS Managed]
        S3[S3 Buckets<br>Photos, PDFs, Reports]
    end

    subgraph "External Services"
        PG[Payment Gateway<br>Stripe / PayPal]
        ESign[E-Signature Provider<br>DocuSign / Adobe Sign]
        ID[Identity Verification<br>Onfido / Jumio]
        SES[AWS SES Email]
        SNS[AWS SNS SMS]
        FCM[FCM / APNs Push]
    end

    Users --> DNS
    DNS --> CloudFront
    CloudFront --> WAF
    WAF --> ALB_A
    WAF --> ALB_B

    ALB_A --> EKS_A
    ALB_B --> EKS_B

    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    EKS_A --> ElastiCache_A
    EKS_B --> ElastiCache_B

    Worker_A --> RDS_Primary
    Worker_B --> RDS_Primary
    Worker_A --> ElastiCache_A
    Worker_B --> ElastiCache_B

    EKS_A --> S3
    EKS_B --> S3
    Worker_A --> S3
    Worker_B --> S3

    RDS_Primary -.-> RDS_Standby
    ElastiCache_A <-.-> ElastiCache_B

    EKS_Control --> EKS_A
    EKS_Control --> EKS_B

    EKS_A --> PG
    EKS_A --> ESign
    EKS_A --> ID
    Worker_A --> SES
    Worker_A --> SNS
    Worker_A --> FCM
```

---

## Kubernetes Deployment

```mermaid
graph TB
    subgraph "EKS Cluster"
        subgraph "Ingress"
            Ingress[NGINX Ingress Controller]
        end

        subgraph "API Namespace"
            Gateway[API Gateway<br>Kong - 3 replicas]
        end

        subgraph "Services Namespace"
            subgraph "Auth Domain"
                AuthSvc[Auth Service<br>2 replicas]
            end

            subgraph "Asset Domain"
                AssetSvc[Asset Service<br>3 replicas]
                SearchSvc[Search Service<br>2 replicas]
            end

            subgraph "Booking Domain"
                BookingSvc[Booking Service<br>5 replicas]
                PricingSvc[Pricing Service<br>3 replicas]
            end

            subgraph "Agreement Domain"
                AgreeSvc[Agreement Service<br>2 replicas]
            end

            subgraph "Payment Domain"
                PaymentSvc[Payment Service<br>3 replicas]
                PayoutSvc[Payout Service<br>2 replicas]
            end

            subgraph "Operations Domain"
                AssessSvc[Assessment Service<br>2 replicas]
                MaintSvc[Maintenance Service<br>2 replicas]
            end

            subgraph "Notification Domain"
                NotifySvc[Notification Service<br>3 replicas]
                WSSvc[WebSocket Service<br>3 replicas]
            end
        end

        subgraph "Workers Namespace"
            BookingWorker[Booking Reminder Worker<br>2 replicas]
            OverdueWorker[Overdue Detection Worker<br>2 replicas]
            PayoutWorker[Payout Batch Worker<br>1 replica]
            ReportWorker[Report Generation Worker<br>2 replicas]
        end

        subgraph "Monitoring Namespace"
            Prometheus[Prometheus]
            Grafana[Grafana]
            Jaeger[Jaeger Tracing]
        end
    end

    Ingress --> Gateway
    Gateway --> AuthSvc
    Gateway --> AssetSvc
    Gateway --> BookingSvc
    Gateway --> AgreeSvc
    Gateway --> PaymentSvc
    Gateway --> AssessSvc
    Gateway --> MaintSvc
    Gateway --> NotifySvc
    Gateway --> WSSvc
```

---

## Deployment Environment Matrix

| Service | Dev | Staging | Production |
|---------|-----|---------|------------|
| Auth Service | 1 replica | 2 replicas | 2 replicas |
| Asset Service | 1 replica | 2 replicas | 3 replicas |
| Booking Service | 1 replica | 3 replicas | 5 replicas |
| Pricing Service | 1 replica | 2 replicas | 3 replicas |
| Agreement Service | 1 replica | 2 replicas | 2 replicas |
| Payment Service | 1 replica | 2 replicas | 3 replicas |
| Assessment Service | 1 replica | 2 replicas | 2 replicas |
| Notification Service | 1 replica | 2 replicas | 3 replicas |
| WebSocket Service | 1 replica | 2 replicas | 3 replicas |

---

## Database & Cache Deployment

```mermaid
graph TB
    subgraph "RDS PostgreSQL"
        subgraph "Primary Region"
            RDS_P[(Primary<br>db.r6g.2xlarge<br>Multi-AZ)]
            RDS_R1[(Read Replica 1<br>db.r6g.xlarge)]
            RDS_R2[(Read Replica 2<br>db.r6g.xlarge)]
        end
        subgraph "DR Region"
            RDS_DR[(DR Replica<br>db.r6g.2xlarge)]
        end
    end

    subgraph "ElastiCache Redis Cluster"
        subgraph "Shard 1"
            R1P[(Primary)] --> R1A[(Replica)]
            R1P --> R1B[(Replica)]
        end
        subgraph "Shard 2"
            R2P[(Primary)] --> R2A[(Replica)]
            R2P --> R2B[(Replica)]
        end
    end

    RDS_P -->|Sync| RDS_R1
    RDS_P -->|Sync| RDS_R2
    RDS_P -.->|Async| RDS_DR

    WriteOps[Write Operations] --> RDS_P
    ReadOps[Read / Report Operations] --> RDS_R1
    ReadOps --> RDS_R2
```

---

## CI/CD Pipeline

```mermaid
graph LR
    Dev[Developer] --> Git[GitHub Repository]
    Git --> Actions[GitHub Actions]
    Actions --> Build[Build & Test]
    Build --> Scan[Security Scan]
    Scan --> Push[Push to ECR]
    Push --> ECR[Amazon ECR]
    ECR --> ArgoCD[ArgoCD]
    ArgoCD --> DevCluster[Dev Cluster]
    ArgoCD --> StagingCluster[Staging Cluster]
    ArgoCD --> ProdCluster[Production Cluster]
```

---

## Resource Allocation

| Component | Instance Type | vCPU | Memory | Storage |
|-----------|---------------|------|--------|---------|
| EKS Worker (API) | m6i.xlarge | 4 | 16 GB | 100 GB |
| EKS Worker (Workers) | m6i.large | 2 | 8 GB | 50 GB |
| RDS Primary | db.r6g.2xlarge | 8 | 64 GB | 1 TB |
| RDS Replica | db.r6g.xlarge | 4 | 32 GB | 1 TB |
| ElastiCache | cache.r6g.xlarge | 4 | 26 GB | — |
| S3 (object storage) | — | — | — | Unlimited |
