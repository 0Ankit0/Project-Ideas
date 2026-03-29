# Cloud Architecture Diagram - Slot Booking System

> **Platform Independence**: Shows cloud-agnostic architecture with provider-specific mappings.

---

## Overview

This document presents cloud architecture patterns that can be implemented on AWS, GCP, Azure, or other providers.

---

## Cloud-Agnostic Architecture

```mermaid
graph TB
    subgraph "Global Edge"
        DNS[DNS Service]
        CDN[Content Delivery<br/>Network]
    end
    
    subgraph "Region: Primary"
        subgraph "Public Subnet"
            ALB[Application<br/>Load Balancer]
            NAT[NAT Gateway]
        end
        
        subgraph "Private Subnet - Compute"
            ECS[Container<br/>Service]
            LAMBDA[Serverless<br/>Functions]
        end
        
        subgraph "Private Subnet - Data"
            RDS[(Managed<br/>Database)]
            CACHE[(Managed<br/>Cache)]
            QUEUE[Managed<br/>Queue]
            SEARCH[(Managed<br/>Search)]
        end
        
        subgraph "Storage"
            S3[Object<br/>Storage]
        end
    end
    
    subgraph "Region: DR"
        RDS_DR[(DB Replica)]
        S3_DR[Storage<br/>Replica]
    end
    
    subgraph "External Services"
        PAY[Payment<br/>Gateway]
        EMAIL[Email<br/>Service]
        SMS[SMS<br/>Provider]
    end
    
    DNS --> CDN
    CDN --> ALB
    ALB --> ECS
    ECS --> RDS
    ECS --> CACHE
    ECS --> QUEUE
    ECS --> SEARCH
    ECS --> S3
    
    LAMBDA --> QUEUE
    
    RDS -.-> RDS_DR
    S3 -.-> S3_DR
    
    ECS --> PAY
    LAMBDA --> EMAIL
    LAMBDA --> SMS
```

---

## Provider Mapping

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| DNS | Route 53 | Cloud DNS | Azure DNS |
| CDN | CloudFront | Cloud CDN | Azure CDN |
| Load Balancer | ALB | Cloud Load Balancing | Azure LB |
| Container Service | ECS / EKS | GKE / Cloud Run | AKS / Container Apps |
| Serverless | Lambda | Cloud Functions | Azure Functions |
| Database | RDS PostgreSQL | Cloud SQL | Azure PostgreSQL |
| Cache | ElastiCache | Memorystore | Azure Cache |
| Queue | SQS | Pub/Sub | Service Bus |
| Search | OpenSearch | Elastic Cloud | Cognitive Search |
| Object Storage | S3 | Cloud Storage | Blob Storage |
| Secrets | Secrets Manager | Secret Manager | Key Vault |

---

## AWS-Specific Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Route 53"
            DNS[Route 53<br/>DNS]
        end
        
        subgraph "CloudFront"
            CF[CloudFront<br/>Distribution]
        end
        
        subgraph "VPC"
            subgraph "Public Subnets"
                ALB[Application<br/>Load Balancer]
                NAT[NAT Gateway]
            end
            
            subgraph "Private Subnets - AZ1"
                ECS1[ECS Tasks]
                RDS1[(RDS Primary)]
                REDIS1[ElastiCache]
            end
            
            subgraph "Private Subnets - AZ2"
                ECS2[ECS Tasks]
                RDS2[(RDS Standby)]
                REDIS2[ElastiCache]
            end
        end
        
        SQS[SQS Queues]
        S3[S3 Bucket]
        SM[Secrets Manager]
        CW[CloudWatch]
    end
    
    DNS --> CF
    CF --> ALB
    ALB --> ECS1
    ALB --> ECS2
    
    ECS1 --> RDS1
    ECS1 --> REDIS1
    ECS1 --> SQS
    ECS1 --> S3
    ECS1 --> SM
    
    ECS1 --> CW
    
    RDS1 -.-> RDS2
    REDIS1 -.-> REDIS2
```

---

## Cost Optimization Tiers

### Starter (~$200/month)
- ECS Fargate Spot for workers
- RDS t3.micro (single AZ)
- ElastiCache t3.micro
- S3 Standard

### Growth (~$800/month)
- ECS Fargate (on-demand)
- RDS t3.medium (Multi-AZ)
- ElastiCache r6g.large
- CloudFront with custom domain

### Enterprise (~$3000+/month)
- EKS with auto-scaling
- RDS r6g.xlarge (Multi-AZ)
- ElastiCache cluster mode
- Global Accelerator
- WAF + Shield

---

## Disaster Recovery

```mermaid
graph LR
    subgraph "Primary Region"
        P_APP[Application]
        P_DB[(Database)]
        P_S3[Storage]
    end
    
    subgraph "DR Region"
        DR_APP[Application<br/>Standby]
        DR_DB[(Database<br/>Replica)]
        DR_S3[Storage<br/>Replica]
    end
    
    P_DB -->|Async Replication| DR_DB
    P_S3 -->|Cross-Region| DR_S3
    
    FAILOVER{Failover<br/>Switch} -.-> DR_APP
```

| Metric | RTO | RPO |
|--------|-----|-----|
| Standard | 4 hours | 1 hour |
| Critical | 1 hour | 15 minutes |

---

## Monitoring & Observability

```mermaid
graph TB
    subgraph "Application"
        APP[Application<br/>Containers]
    end
    
    subgraph "Observability Stack"
        METRICS[Metrics<br/>Prometheus/CloudWatch]
        LOGS[Logs<br/>ELK/CloudWatch Logs]
        TRACES[Traces<br/>X-Ray/Jaeger]
    end
    
    subgraph "Alerting"
        ALERTS[Alert Manager]
        PAGER[PagerDuty/OpsGenie]
    end
    
    subgraph "Dashboards"
        GRAFANA[Grafana/CloudWatch]
    end
    
    APP --> METRICS
    APP --> LOGS
    APP --> TRACES
    
    METRICS --> ALERTS
    LOGS --> ALERTS
    ALERTS --> PAGER
    
    METRICS --> GRAFANA
    LOGS --> GRAFANA
    TRACES --> GRAFANA
```

---

## Security Best Practices

| Area | Implementation |
|------|----------------|
| Network | VPC, Security Groups, NACLs |
| Identity | IAM roles, MFA, least privilege |
| Encryption | TLS 1.3, KMS for at-rest |
| Secrets | Secrets Manager/Vault |
| Compliance | CloudTrail, Config Rules |
| DDoS | Shield, WAF |

---
## Implementation-Ready Cloud Architecture

### Slot allocation rules in this document's context
- Allocation decisions must be based on **resource calendar + operational policy + channel limits** before any payment action is attempted.
- All provisional allocations require an explicit **hold record with expiry**, and expiry must be visible to clients.
- Shared-capacity resources must use atomic decrement semantics; exclusive resources must enforce single-active-booking constraints.

### Conflict resolution in this document's context
- Competing writes must use deterministic conflict handling (optimistic version checks or transactional locks as documented here).
- API and admin paths must converge on one canonical conflict reason taxonomy (`SLOT_TAKEN`, `STALE_VERSION`, `PROVIDER_BLOCKED`, `PAYMENT_STATE_MISMATCH`).
- Every conflict rejection must emit structured audit telemetry including actor, correlation ID, and rule version.

### Payment coupling / decoupling behavior
- **Coupled flow**: booking moves to confirmed only after successful authorization/capture.
- **Decoupled flow**: booking can be confirmed with `PAYMENT_PENDING`, but with a bounded grace window and auto-cancel guardrail.
- Compensation is mandatory for split-brain outcomes (payment succeeded but booking failed, or inverse).

### Cancellation and refund policy detail
- Refund outcomes depend on lead time, policy tier, no-show status, and jurisdiction-specific fee constraints.
- Refund processing must be idempotent and expose lifecycle states (`REQUESTED`, `INITIATED`, `SETTLED`, `FAILED`, `MANUAL_REVIEW`).
- Cancellation side effects must include slot reallocation and downstream notification consistency.

### Observability and incident playbook focus
- Monitor: availability latency, hold expiry lag, conflict rate, payment callback success, refund aging.
- Alerts must map to operator runbooks with first-response steps and data reconciliation queries.
- Post-incident review must record policy gaps and required control changes for this documentation area.

### Infrastructure operational readiness
- Runtime scaling triggers (CPU, queue depth, payment callback lag).
- Disaster recovery path for booking ledger and refund case stores.
- Secrets, key rotation, and gateway credential failover strategy.


### Mermaid cloud reference architecture
```mermaid
flowchart TB
  Client --> GLB[Global Load Balancer]
  GLB --> K8s[Kubernetes Cluster]
  K8s --> Booking[Booking Service]
  K8s --> Finance[Payment/Refund Service]
  Booking --> PG[(Managed Postgres)]
  Booking --> Redis[(Managed Redis)]
  Booking --> Bus[(Event Bus)]
  Finance --> PSP[(Payment Provider)]
  Booking --> Obs[(Observability Platform)]
```
