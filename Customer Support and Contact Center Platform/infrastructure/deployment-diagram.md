# Deployment Diagram

## Production Deployment
```mermaid
flowchart TB
    Internet[(Internet/PSTN)] --> Edge[WAF + Channel Edge]
    Edge --> LB[Public Load Balancer]

    subgraph VPC[Contact Center VPC]
      subgraph AppSubnets[Private App Subnets]
        API[Support API Pods]
        Worker[SLA/QA Worker Pods]
      end

      subgraph DataSubnets[Private Data Subnets]
        DB[(PostgreSQL HA)]
        MQ[(Managed MQ)]
        Search[(Search Cluster)]
        Redis[(Redis)]
      end
    end

    LB --> API
    API --> DB
    API --> MQ
    API --> Redis
    Worker --> DB
    Worker --> MQ
    Worker --> Search

    API --> Obs[Observability Stack]
    Worker --> Obs
    DB --> Backup[Encrypted Backups]
```

## Environment Promotion
```mermaid
flowchart LR
    Dev --> Stage --> Prod
    Stage --> Gate[Load + SLA Validation Gate]
    Gate --> Prod
```
