# Deployment Diagram

## Overview
Deployment diagrams showing the mapping of software components to hardware and infrastructure for the Employee Management System.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Users / Clients]
        BiometricDevices[Biometric Devices]
    end

    subgraph "Edge Layer"
        DNS[Route 53 DNS]
        CloudFront[CloudFront CDN\nStatic Assets]
        WAF[AWS WAF\nDDoS, OWASP protection]
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
                EKS_A[EKS Worker Nodes\nAPI Service Pods]
                Worker_A[EKS Worker Nodes\nAsync Worker Pods]
            end

            subgraph "Private Subnet AZ-B - Application"
                EKS_B[EKS Worker Nodes\nAPI Service Pods]
                Worker_B[EKS Worker Nodes\nAsync Worker Pods]
            end

            subgraph "Private Subnet AZ-A - Data"
                RDS_Primary[(RDS PostgreSQL\nPrimary)]
                ElastiCache_A[(ElastiCache Redis\nAZ-A)]
            end

            subgraph "Private Subnet AZ-B - Data"
                RDS_Standby[(RDS PostgreSQL\nStandby)]
                ElastiCache_B[(ElastiCache Redis\nAZ-B)]
            end
        end

        EKS_Control[EKS Control Plane\nAWS Managed]
        S3[S3 Buckets\nDocuments, Payslips, Reports]
        SQS[Amazon SQS\nTask Queue]
        SES[Amazon SES\nEmail Service]
        SNS[Amazon SNS\nSMS & Push]
    end

    subgraph "AWS Region - DR"
        RDS_DR[(RDS Read Replica\nDR Region)]
        S3_DR[S3 Replication]
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

    EKS_A --> SQS
    EKS_B --> SQS
    SQS --> Worker_A
    SQS --> Worker_B

    Worker_A --> SES
    Worker_B --> SNS
    Worker_A --> S3

    EKS_A --> S3
    EKS_B --> S3

    RDS_Primary --> RDS_Standby
    RDS_Primary --> RDS_DR
    S3 --> S3_DR

    BiometricDevices -->|TLS| ALB_A
```

---

## Kubernetes Pod Layout

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: ems-production"
            subgraph "API Deployment"
                API_Pod1[API Pod 1\nFastAPI / Node.js]
                API_Pod2[API Pod 2]
                API_Pod3[API Pod 3]
            end

            subgraph "Worker Deployment"
                Worker_Pod1[Worker Pod 1\nPayroll Processing]
                Worker_Pod2[Worker Pod 2\nReport Generation]
                Worker_Pod3[Worker Pod 3\nNotification Delivery]
            end

            subgraph "WebSocket Deployment"
                WS_Pod1[WebSocket Pod 1]
                WS_Pod2[WebSocket Pod 2]
            end

            subgraph "Config & Secrets"
                ConfigMap[ConfigMap\nApp Settings]
                Secrets[Secrets\nDB Creds, API Keys]
            end

            HPA_API[HPA - API\nCPU/Memory based]
            HPA_Worker[HPA - Worker\nQueue depth based]
        end
    end

    IngressController[NGINX Ingress Controller] --> API_Pod1
    IngressController --> API_Pod2
    IngressController --> API_Pod3
    IngressController --> WS_Pod1
    IngressController --> WS_Pod2

    API_Pod1 --> ConfigMap
    API_Pod1 --> Secrets
    Worker_Pod1 --> Secrets

    HPA_API --> API_Pod1
    HPA_Worker --> Worker_Pod1
```

---

## CI/CD Pipeline

```mermaid
graph LR
    Dev[Developer Push] --> GitRepo[Git Repository]
    GitRepo --> CI[CI Pipeline\nGitHub Actions / GitLab CI]
    CI --> Lint[Lint & Format Check]
    Lint --> Tests[Unit & Integration Tests]
    Tests --> Build[Docker Build]
    Build --> SAST[SAST Security Scan]
    SAST --> Registry[Container Registry\nECR / DockerHub]
    Registry --> StagingDeploy[Deploy to Staging]
    StagingDeploy --> E2E[E2E Tests]
    E2E --> ManualApproval{Manual Approval}
    ManualApproval --> ProdDeploy[Deploy to Production\nRolling Update]
    ProdDeploy --> HealthCheck[Health Check\nReadiness Probe]
    HealthCheck --> Done([Deployment Complete])
```
