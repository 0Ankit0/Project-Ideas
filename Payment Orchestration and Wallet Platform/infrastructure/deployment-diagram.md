# Deployment Diagram

## Production Deployment
```mermaid
flowchart TB
    Internet[(Internet)] --> WAF[WAF/CDN]
    WAF --> LB[Load Balancer]

    subgraph VPC[Payments VPC]
      subgraph AppSubnets[Private App Subnets]
        API[Payments API Pods]
        Worker[Settlement/Reconciliation Workers]
      end

      subgraph DataSubnets[Private Data Subnets]
        DB[(PostgreSQL HA)]
        MQ[(Managed MQ)]
        Redis[(Redis)]
      end
    end

    LB --> API
    API --> DB
    API --> MQ
    API --> Redis
    Worker --> DB
    Worker --> MQ

    API --> Obs[Observability Stack]
    Worker --> Obs
    DB --> Backup[Encrypted Backups]
```

## Environment Promotion
```mermaid
flowchart LR
    Dev --> Stage --> Prod
    Stage --> Gate[Risk + Finance Approval Gate]
    Gate --> Prod
```
