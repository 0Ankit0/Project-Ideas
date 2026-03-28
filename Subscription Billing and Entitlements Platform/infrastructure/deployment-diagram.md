# Deployment Diagram

## Production Deployment
```mermaid
flowchart TB
    Internet[(Internet)] --> Edge[CDN/WAF]
    Edge --> LB[Public Load Balancer]

    subgraph VPC[Billing VPC]
      subgraph App[Private App Subnets]
        API[Billing API Pods]
        Worker[Dunning/Reconciliation Workers]
      end

      subgraph Data[Private Data Subnets]
        DB[(PostgreSQL HA)]
        Redis[(Redis)]
        MQ[(Managed MQ)]
      end
    end

    LB --> API
    API --> DB
    API --> Redis
    API --> MQ
    Worker --> DB
    Worker --> MQ

    API --> Obs[Centralized Logs/Tracing]
    Worker --> Obs
    DB --> Backup[Encrypted Backup Storage]
```

## Environment Promotion
```mermaid
flowchart LR
    Dev --> Stage --> Prod
    Stage --> Gate[UAT + Finance Signoff]
    Gate --> Prod
```
