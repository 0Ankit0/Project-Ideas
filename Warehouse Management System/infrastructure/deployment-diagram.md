# Deployment Diagram

## Production Deployment
```mermaid
flowchart TB
    Edge[(Corporate Network / Internet)] --> WAF[WAF]
    WAF --> LB[Load Balancer]

    subgraph RegionA[Region A]
      subgraph AppA[Private App Subnets]
        APIA[API Pods]
        WRKA[Worker Pods]
      end
      subgraph DataA[Data Subnets]
        DBA[(Primary PostgreSQL)]
        MQA[(Managed MQ)]
        RCA[(Redis)]
      end
    end

    subgraph RegionB[DR Region]
      DBB[(Standby PostgreSQL)]
      MQB[(Standby MQ)]
    end

    LB --> APIA
    APIA --> DBA
    APIA --> MQA
    APIA --> RCA
    WRKA --> DBA
    WRKA --> MQA

    DBA --> DBB
    MQA --> MQB

    APIA --> Obs[Central Observability]
    WRKA --> Obs
    DBA --> Backup[Encrypted Backups]
```

## Deployment Controls
- Blue/green deploy for API tier.
- Canary worker rollout for allocation/shipping queues.
- Automated rollback when SLO burn exceeds threshold.
