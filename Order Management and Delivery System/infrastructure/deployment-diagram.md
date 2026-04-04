# Deployment Diagram

## Overview

AWS deployment topology for the Order Management and Delivery System, showing compute placement, scaling policies, and load balancing.

## Deployment Architecture

```mermaid
graph TB
    subgraph Internet["Internet"]
        Users["Users<br/>(Browsers, Mobile Apps)"]
    end

    subgraph AWS_Edge["AWS Edge"]
        CF["Amazon CloudFront<br/>CDN, SPA hosting<br/>Edge locations worldwide"]
        WAF["AWS WAF<br/>OWASP Top 10, rate limiting,<br/>geo-blocking"]
        R53["Amazon Route 53<br/>DNS, health checks,<br/>failover routing"]
    end

    subgraph Region["AWS Region (ap-south-1)"]
        subgraph PublicSubnet["Public Subnets (Multi-AZ)"]
            APIGW["Amazon API Gateway<br/>Regional endpoint<br/>REST APIs, usage plans"]
            NAT_A["NAT Gateway<br/>(AZ-a)"]
            NAT_B["NAT Gateway<br/>(AZ-b)"]
        end

        subgraph PrivateSubnet["Private Subnets (Multi-AZ)"]
            subgraph Lambda_Pool["Lambda Functions"]
                L_Order["Order Service<br/>512 MB, 30s timeout<br/>Reserved: 100 concurrent"]
                L_Payment["Payment Service<br/>512 MB, 30s timeout<br/>Reserved: 50 concurrent"]
                L_Inventory["Inventory Service<br/>256 MB, 15s timeout<br/>Reserved: 100 concurrent"]
                L_Notif["Notification Service<br/>256 MB, 15s timeout<br/>Reserved: 50 concurrent"]
                L_Search["Search Sync<br/>256 MB, 60s timeout<br/>Reserved: 20 concurrent"]
            end

            subgraph Fargate_Cluster["ECS Fargate Cluster"]
                F_Fulfill["Fulfillment Service<br/>1 vCPU, 2 GB<br/>Min: 2, Max: 10<br/>Target CPU: 70%"]
                F_Delivery["Delivery Service<br/>1 vCPU, 2 GB<br/>Min: 2, Max: 10<br/>Target CPU: 70%"]
                F_Return["Return Service<br/>0.5 vCPU, 1 GB<br/>Min: 1, Max: 5<br/>Target CPU: 70%"]
                F_Analytics["Analytics Service<br/>1 vCPU, 2 GB<br/>Min: 1, Max: 5<br/>Target CPU: 70%"]
            end
        end

        subgraph DataSubnet["Data Subnets (Multi-AZ)"]
            RDS_Primary["RDS PostgreSQL 15<br/>Primary (AZ-a)<br/>db.r6g.xlarge<br/>500 GB gp3 SSD"]
            RDS_Standby["RDS PostgreSQL 15<br/>Standby (AZ-b)<br/>Automatic failover"]
            RDS_Read["RDS Read Replica<br/>(AZ-b)<br/>Analytics queries"]
            Redis_Primary["ElastiCache Redis<br/>Primary (AZ-a)<br/>cache.r6g.large"]
            Redis_Replica["ElastiCache Redis<br/>Replica (AZ-b)"]
        end

        subgraph ManagedServices["Managed Services"]
            DDB["DynamoDB<br/>On-demand capacity<br/>PITR enabled"]
            EB["EventBridge<br/>Custom bus: oms.events"]
            SF["Step Functions<br/>Standard workflow"]
            OS["OpenSearch<br/>2-node cluster<br/>Multi-AZ"]
            S3_Assets["S3 — Assets<br/>Product images, SPA"]
            S3_POD["S3 — POD<br/>Delivery artifacts<br/>SSE-S3, versioning"]
            S3_Reports["S3 — Reports<br/>90-day lifecycle"]
        end
    end

    Users --> R53
    R53 --> CF
    CF --> WAF
    WAF --> APIGW
    CF --> S3_Assets
    APIGW --> Lambda_Pool
    APIGW --> Fargate_Cluster
    Lambda_Pool --> DataSubnet
    Lambda_Pool --> ManagedServices
    Fargate_Cluster --> DataSubnet
    Fargate_Cluster --> ManagedServices
    Lambda_Pool -->|"Outbound via"| NAT_A
    Lambda_Pool -->|"Outbound via"| NAT_B
    RDS_Primary --> RDS_Standby
    RDS_Primary --> RDS_Read
    Redis_Primary --> Redis_Replica
```

## Scaling Policies

| Component | Metric | Target | Min | Max | Cooldown |
|---|---|---|---|---|---|
| Lambda (Order) | Concurrent executions | N/A (auto) | 0 | 100 (reserved) | N/A |
| Lambda (Payment) | Concurrent executions | N/A (auto) | 0 | 50 (reserved) | N/A |
| Fargate (Fulfillment) | CPU utilisation | 70 % | 2 | 10 | 300 s |
| Fargate (Delivery) | CPU utilisation | 70 % | 2 | 10 | 300 s |
| Fargate (Return) | CPU utilisation | 70 % | 1 | 5 | 300 s |
| Fargate (Analytics) | CPU utilisation | 70 % | 1 | 5 | 300 s |
| DynamoDB | On-demand | Auto | — | — | — |
| RDS | Read Replica count | Manual | 1 | 3 | — |
| ElastiCache | Cluster mode | Manual | 1 primary + 1 replica | 1 primary + 2 replicas | — |
| OpenSearch | Instance count | Manual | 2 | 4 | — |

## Deployment Strategy

| Environment | Strategy | Details |
|---|---|---|
| Development | Direct deploy | CDK deploy from developer workstation |
| Staging | Blue/Green | Full stack clone; smoke tests before cutover |
| Production | Canary | 10% traffic → canary for 10 min; auto-rollback on error rate > 1% |
| Hotfix | Rolling | Skip canary for critical patches; manual approval gate |
