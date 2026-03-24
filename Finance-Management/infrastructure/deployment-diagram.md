# Deployment Diagram

## Overview
Production deployment architecture for the Finance Management System on AWS EKS, showing the mapping from software components to infrastructure nodes.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Finance Users]
    end

    subgraph "Edge Layer"
        R53[Route 53<br>DNS Failover]
        CF[CloudFront<br>Static Assets CDN]
        WAF[AWS WAF<br>Layer 7 Security]
    end

    subgraph "AWS Region (us-east-1)"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Public Subnets (AZ-a, AZ-b)"
                ALB[Application Load Balancer<br>HTTPS / TLS 1.3]
                NATGW[NAT Gateways]
            end

            subgraph "Private App Subnets (AZ-a, AZ-b)"
                subgraph "EKS Cluster"
                    subgraph "App Node Group"
                        FinanceAPI[Finance API Pod<br>FastAPI<br>HPA: 2-8 replicas]
                        WorkerPod[Worker Pod<br>Celery<br>HPA: 1-4 replicas]
                        WSPod[WebSocket Pod<br>FastAPI WS<br>2 replicas]
                    end

                    subgraph "System Pods"
                        Ingress[Nginx Ingress Controller]
                        ExtSecrets[External Secrets Operator<br>Syncs from Secrets Manager]
                        CertManager[Cert Manager]
                    end
                end
            end

            subgraph "Private Data Subnets (AZ-a, AZ-b)"
                subgraph "Database Tier"
                    RDSPrimary[(RDS PostgreSQL<br>Primary<br>db.r6g.2xlarge)]
                    RDSReplica[(RDS PostgreSQL<br>Read Replica<br>db.r6g.xlarge)]
                    AuditRDS[(Audit RDS<br>Append-Only<br>db.r6g.large)]
                    ElastiCache[(ElastiCache Redis<br>3-node Cluster)]
                end
            end
        end

        S3[S3 Buckets<br>Documents, Reports, Bank Files]
        SQS[SQS Queues<br>Report Jobs, Notifications]
        SecretsManager[Secrets Manager]
        KMS[KMS Keys]
    end

    subgraph "DR Region (us-west-2)"
        RDS_DR[(RDS Replica)]
        AuditRDS_DR[(Audit DR)]
        S3_DR[S3 CRR]
    end

    Users --> R53
    R53 --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> Ingress
    Ingress --> FinanceAPI
    Ingress --> WSPod

    FinanceAPI --> RDSPrimary
    FinanceAPI --> AuditRDS
    FinanceAPI --> ElastiCache
    FinanceAPI --> S3
    FinanceAPI --> SQS
    FinanceAPI --> SecretsManager
    SecretsManager --> KMS
    KMS --> RDSPrimary

    SQS --> WorkerPod
    WorkerPod --> RDSPrimary
    WorkerPod --> S3

    RDSReplica -.->|Read queries| FinanceAPI

    RDSPrimary -.->|Replication| RDS_DR
    AuditRDS -.->|Replication| AuditRDS_DR
    S3 -.->|CRR| S3_DR
```

---

## Kubernetes Deployment Detail

```mermaid
graph TB
    subgraph "Kubernetes Namespace: finance-prod"
        subgraph "Ingress"
            NginxIngress[nginx-ingress-controller]
        end

        subgraph "Finance API Deployment"
            APISvc[finance-api Service<br>ClusterIP]
            APIPod1[finance-api Pod 1<br>FastAPI Container<br>CPU: 500m-2000m<br>Mem: 512Mi-2Gi]
            APIPod2[finance-api Pod 2]
            APIPod3[finance-api Pod 3]
            APIHPA[HorizontalPodAutoscaler<br>min:2 max:8<br>CPU: 70%]
        end

        subgraph "Worker Deployment"
            WorkerSvc[worker Service]
            WorkerPod1[worker Pod 1<br>Celery Worker<br>Queues: reports, payroll, notifications]
            WorkerPod2[worker Pod 2]
            WorkerHPA[HorizontalPodAutoscaler<br>min:1 max:4<br>Queue depth metric]
        end

        subgraph "WebSocket Deployment"
            WSSvc[websocket Service<br>ClusterIP]
            WSPod1[websocket Pod 1<br>FastAPI WS<br>Sticky sessions]
            WSPod2[websocket Pod 2]
        end

        subgraph "Config & Secrets"
            ConfigMap[ConfigMap<br>App Settings]
            Secret[Secret<br>Synced from AWS Secrets Manager]
            PVC[PersistentVolumeClaim<br>gp3 StorageClass]
        end
    end

    NginxIngress --> APISvc
    NginxIngress --> WSSvc
    APISvc --> APIPod1
    APISvc --> APIPod2
    APISvc --> APIPod3
    APIHPA --> APIPod1

    WorkerSvc --> WorkerPod1
    WorkerSvc --> WorkerPod2
    WorkerHPA --> WorkerPod1

    WSSvc --> WSPod1
    WSSvc --> WSPod2

    APIPod1 --> ConfigMap
    APIPod1 --> Secret
    WorkerPod1 --> ConfigMap
    WorkerPod1 --> Secret
```

---

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Source Control"
        Git[GitHub Repository]
    end

    subgraph "CI Pipeline (GitHub Actions)"
        Lint[Lint & Type Check<br>ruff, mypy]
        Test[Run Tests<br>pytest + coverage]
        SAST[SAST Scan<br>bandit, semgrep]
        Build[Docker Build<br>multi-stage]
        Scan[Container Scan<br>Amazon Inspector]
        Push[Push to ECR]
    end

    subgraph "CD Pipeline (ArgoCD)"
        ArgoProd[ArgoCD<br>Production Sync]
        K8sDeploy[kubectl apply<br>Rolling Update]
        HealthCheck[Readiness Check<br>/health /ready]
        Rollback[Auto-Rollback<br>on failure]
    end

    subgraph "Infrastructure"
        ECR[Amazon ECR]
        EKS[Amazon EKS]
    end

    Git --> Lint
    Lint --> Test
    Test --> SAST
    SAST --> Build
    Build --> Scan
    Scan --> Push
    Push --> ECR

    ECR --> ArgoProd
    ArgoProd --> K8sDeploy
    K8sDeploy --> EKS
    K8sDeploy --> HealthCheck
    HealthCheck -->|Unhealthy| Rollback
    Rollback --> EKS
```
