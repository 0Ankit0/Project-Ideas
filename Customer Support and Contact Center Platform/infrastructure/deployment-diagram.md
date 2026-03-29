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

## Deployment Narrative with Resilience
Deployment diagram should include active-active channel ingress, active-passive workflow DB failover, and isolated audit storage.

```mermaid
flowchart LR
    LB[Global LB] --> R1[Region A Services]
    LB --> R2[Region B Services]
    R1 --> DBA[(Primary Workflow DB)]
    R2 --> DBB[(Standby DB)]
    R1 --> AUD[(WORM Audit Store)]
    R2 --> AUD
```

Incident runbook trigger: fail over only after queue-drain checkpoint and SLA clock continuity verification.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
