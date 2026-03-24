# Cloud Architecture

## Overview
Cloud architecture diagrams showing the AWS infrastructure design for the Student Information System, including compute, storage, databases, networking, and managed services.

---

## AWS Cloud Architecture Overview

```mermaid
graph TB
    subgraph "Users"
        Students[Students]
        Faculty[Faculty]
        Admin[Admin Staff]
        Parents[Parents]
    end

    subgraph "Edge Services"
        Route53[Route 53<br>DNS]
        CloudFront[CloudFront<br>CDN + WAF]
        Certificate[ACM<br>SSL/TLS]
    end

    subgraph "AWS Region - ap-southeast-1"
        subgraph "Compute - EKS"
            EKS[EKS Cluster<br>SIS Application]
            Workers[Worker Node Group<br>m6i.large x 4-8 nodes]
            HPA[Horizontal Pod Autoscaler]
        end

        subgraph "Load Balancing"
            ALB[Application Load Balancer<br>Multi-AZ]
        end

        subgraph "Database Tier"
            RDS[RDS PostgreSQL<br>db.r6g.xlarge Multi-AZ]
            RDS_Read[RDS Read Replica<br>db.r6g.large x 2]
        end

        subgraph "Caching Tier"
            ElastiCache[ElastiCache Redis<br>cache.r6g.large Cluster]
        end

        subgraph "Storage"
            S3_Docs[S3 Bucket<br>Documents / Transcripts]
            S3_Static[S3 Bucket<br>Static Assets]
            S3_Backups[S3 Bucket<br>Database Backups]
        end

        subgraph "Messaging"
            SES[SES<br>Transactional Email]
            SNS[SNS<br>SMS / Push Notifications]
            SQS[SQS<br>Async Task Queue]
        end

        subgraph "Security"
            IAM_AWS[IAM<br>Roles and Policies]
            KMS[KMS<br>Encryption Keys]
            SecretsManager[Secrets Manager<br>DB Creds / API Keys]
            WAF_Service[WAF<br>Web Application Firewall]
        end

        subgraph "Monitoring"
            CloudWatch[CloudWatch<br>Logs / Metrics / Alarms]
            XRay[X-Ray<br>Distributed Tracing]
        end
    end

    Students --> CloudFront
    Faculty --> CloudFront
    Admin --> CloudFront
    Parents --> CloudFront

    CloudFront --> Certificate
    CloudFront --> Route53
    CloudFront --> WAF_Service
    WAF_Service --> ALB
    ALB --> EKS

    EKS --> Workers
    Workers --> HPA

    EKS --> RDS
    EKS --> RDS_Read
    EKS --> ElastiCache
    EKS --> S3_Docs
    EKS --> S3_Static
    EKS --> SES
    EKS --> SNS
    EKS --> SQS

    EKS --> SecretsManager
    EKS --> KMS
    EKS --> IAM_AWS

    EKS --> CloudWatch
    EKS --> XRay

    RDS -.->|Automated Backup| S3_Backups
    RDS -->|Replication| RDS_Read
```

---

## Auto-Scaling Architecture

```mermaid
graph LR
    subgraph "Load Triggers"
        Enrollment[Enrollment Window<br>High Traffic]
        ExamPeriod[Exam Period<br>Result Viewing]
        Regular[Regular Day<br>Normal Traffic]
    end

    subgraph "Scaling Policies"
        HPA[Kubernetes HPA<br>Pod Autoscaling<br>CPU > 70%]
        CA[Cluster Autoscaler<br>Node Autoscaling<br>Pending Pods]
    end

    subgraph "Infrastructure"
        Pods[Application Pods<br>2-10 per service]
        Nodes[Worker Nodes<br>2-8 nodes]
    end

    Enrollment -->|Scale Up| HPA
    ExamPeriod -->|Scale Up| HPA
    Regular -->|Scale Down| HPA
    HPA --> Pods
    Pods -->|Node Pressure| CA
    CA --> Nodes
```

---

## Data Residency and Compliance Architecture

```mermaid
graph TB
    subgraph "Primary Region"
        AppTier[Application Tier<br>SIS Services]
        DataTier[Data Tier<br>Student Records]
        BackupTier[Backup Tier<br>Automated Backups]
    end

    subgraph "DR Region"
        DR_Data[DR Data Tier<br>Cross-region replica]
        DR_Backup[DR Backup Storage]
    end

    subgraph "Compliance Controls"
        FERPA[FERPA Compliance<br>Student Data Privacy]
        Encrypt[Encryption at Rest<br>KMS-managed keys]
        Audit[Audit Logging<br>CloudTrail + CloudWatch]
        AccessControl[Access Control<br>IAM + RBAC]
    end

    AppTier --> DataTier
    DataTier --> BackupTier
    DataTier -.->|Async Replication| DR_Data
    BackupTier -.->|Cross-region Copy| DR_Backup

    AppTier --> FERPA
    DataTier --> Encrypt
    AppTier --> Audit
    AppTier --> AccessControl
```

---

## External Integration Architecture

```mermaid
graph TB
    subgraph "SIS Platform"
        FeeModule[Fee Module]
        IAMModule[IAM Module]
        AttendanceModule[Attendance Module]
        NotificationModule[Notification Module]
        EnrollmentModule[Enrollment Module]
    end

    subgraph "External Services"
        PaymentGW[Payment Gateways<br>Bank / Cards / UPI]
        LDAP_EXT[LDAP / AD<br>Institutional SSO]
        Biometric[Biometric Devices<br>Attendance API]
        LibraryAPI[Library System<br>REST API]
        ERPSystem[ERP / Finance<br>Fee Sync]
        EmailProv[Email Provider<br>SES / SendGrid]
        SMSProv[SMS Provider<br>SNS / Twilio]
        PushProv[Push Provider<br>FCM / APNs]
    end

    FeeModule -->|HTTPS| PaymentGW
    IAMModule -->|LDAPS| LDAP_EXT
    AttendanceModule -->|REST API| Biometric
    EnrollmentModule -->|REST API| LibraryAPI
    FeeModule -->|REST API| ERPSystem
    NotificationModule -->|SMTP/API| EmailProv
    NotificationModule -->|API| SMSProv
    NotificationModule -->|API| PushProv
```

---

## Cloud Cost Optimization Strategy

| Service | Strategy | Expected Saving |
|---------|----------|----------------|
| EKS Nodes | Reserved instances for baseline; Spot for burst | 30-40% |
| RDS | Reserved instances with 1-year commitment | 35-40% |
| ElastiCache | Reserved nodes | 30-35% |
| S3 | Intelligent-Tiering for infrequent documents | 15-20% |
| CloudFront | Cache optimization for static assets | Reduced origin costs |
| SQS/SNS | On-demand; low base cost | Pay-per-use |
