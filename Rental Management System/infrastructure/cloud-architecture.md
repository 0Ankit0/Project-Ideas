# Cloud Architecture

## Overview
Cloud architecture diagram and service selection for the rental management system on AWS.

---

## Full AWS Cloud Architecture

```mermaid
graph TB
    subgraph "Clients"
        Web[Web Browsers]
        Mobile[Mobile Apps]
    end

    subgraph "AWS Edge"
        R53[Route 53]
        CF[CloudFront CDN]
        WAF[AWS WAF]
        Shield[AWS Shield Standard]
    end

    subgraph "Compute - AWS Region"
        subgraph "EKS - API Cluster"
            API[API Pods]
            WS[WebSocket Pods]
        end

        subgraph "EKS - Worker Cluster"
            Workers[Worker Pods<br>Celery / BullMQ]
        end

        ALB[Application Load Balancer]
    end

    subgraph "Data Services"
        RDS[Amazon RDS<br>PostgreSQL 15<br>Multi-AZ]
        ElastiCache[Amazon ElastiCache<br>Redis 7]
        S3[Amazon S3<br>Photos, PDFs, Exports]
    end

    subgraph "Secrets & Config"
        SM[AWS Secrets Manager<br>DB credentials, API keys]
        SSM[AWS SSM Parameter Store<br>Environment config]
    end

    subgraph "Observability"
        CW[Amazon CloudWatch<br>Logs + Metrics]
        XRay[AWS X-Ray<br>Distributed Tracing]
        Grafana[Grafana<br>Dashboards]
        Alerts[CloudWatch Alarms<br>PagerDuty Integration]
    end

    subgraph "Security"
        IAM_AWS[AWS IAM<br>Service Roles + Policies]
        KMS[AWS KMS<br>Encryption Keys]
        Inspector[Amazon Inspector<br>Vulnerability Scanning]
        GuardDuty[Amazon GuardDuty<br>Threat Detection]
    end

    subgraph "Messaging"
        SES[AWS SES<br>Email]
        SNS_AWS[AWS SNS<br>SMS + Push Fan-out]
    end

    subgraph "CI/CD"
        CodePipeline[AWS CodePipeline<br>or GitHub Actions]
        ECR[Amazon ECR<br>Container Registry]
        ArgoCD[ArgoCD<br>GitOps Deployment]
    end

    Web --> R53
    Mobile --> R53
    R53 --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> API
    ALB --> WS

    API --> RDS
    API --> ElastiCache
    API --> S3
    API --> SM

    Workers --> RDS
    Workers --> ElastiCache
    Workers --> S3
    Workers --> SES
    Workers --> SNS_AWS

    API --> XRay
    Workers --> XRay
    API --> CW
    Workers --> CW

    CodePipeline --> ECR
    ECR --> ArgoCD
    ArgoCD --> API
    ArgoCD --> Workers

    KMS --> RDS
    KMS --> S3
    KMS --> SM
```

---

## AWS Service Selection

| Category | Service | Justification |
|----------|---------|---------------|
| Compute | Amazon EKS | Managed Kubernetes for container orchestration; auto-scaling |
| Load Balancing | AWS ALB | Layer 7 load balancing; path-based routing; WebSocket support |
| Database | Amazon RDS PostgreSQL | Managed relational DB; Multi-AZ for HA; point-in-time recovery |
| Caching | Amazon ElastiCache Redis | Low-latency cache; availability locks; task queue |
| Object Storage | Amazon S3 | Durable, scalable storage for photos, PDFs, reports |
| CDN | Amazon CloudFront | Edge caching for static assets; low-latency global delivery |
| DNS | Amazon Route 53 | Reliable DNS; health-check-based failover |
| Security | AWS WAF + Shield | Edge protection against OWASP Top 10, DDoS |
| Secrets | AWS Secrets Manager | Encrypted secret storage with automatic rotation |
| Email | Amazon SES | High-deliverability transactional email |
| SMS / Push | Amazon SNS | Scalable SMS and push notification fan-out |
| Logging | Amazon CloudWatch | Centralized log aggregation and metric dashboards |
| Tracing | AWS X-Ray | Distributed tracing across services |
| Container Registry | Amazon ECR | Private container image registry |
| CI/CD | GitHub Actions + ArgoCD | GitOps-based deployment pipeline |
| Encryption | AWS KMS | Key management for RDS, S3, and Secrets Manager |
| Threat Detection | Amazon GuardDuty | Automated threat detection for AWS accounts |

---

## Auto-Scaling Configuration

```mermaid
graph LR
    subgraph "Horizontal Pod Autoscaler"
        HPAAPI[API Pods<br>Min: 3, Max: 20<br>CPU > 70%]
        HPAWorker[Worker Pods<br>Min: 2, Max: 10<br>Queue depth > 100]
        HPAWS[WebSocket Pods<br>Min: 3, Max: 15<br>Connection count]
    end

    subgraph "Cluster Autoscaler"
        CA[Node Group<br>Min: 3, Max: 20 nodes<br>m6i.xlarge]
    end

    HPAAPI --> CA
    HPAWorker --> CA
    HPAWS --> CA
```

---

## Backup and Disaster Recovery

| Resource | Backup Strategy | RPO | RTO |
|----------|-----------------|-----|-----|
| RDS PostgreSQL | Automated daily snapshots + PITR | 5 minutes | 30 minutes |
| RDS Cross-Region | Async replication to DR region | 15 minutes | 1 hour |
| S3 | Cross-region replication | Real-time | Immediate |
| ElastiCache | Automatic daily snapshot | 1 hour | 15 minutes |
| Secrets Manager | Multi-region replication | Real-time | Immediate |

---

## Cost Optimisation

| Strategy | Implementation |
|----------|---------------|
| Reserved Instances | 1-year RDS and ElastiCache reservations for baseline capacity |
| Spot Instances | Worker pods on spot node groups (fault-tolerant batch jobs) |
| S3 Lifecycle Policies | Move reports > 90 days to S3-IA; > 1 year to Glacier |
| CloudFront Caching | Cache asset photos and static files to reduce origin requests |
| RDS Read Replicas | Route reporting queries to read replicas, reducing primary load |
