# Architecture Diagram

```mermaid
flowchart TB
    Channels[RF Scanners, Web UI, OMS/ERP/TMS Integrations] --> Edge[API Gateway + Auth]

    subgraph CoreServices[WMS Core Services]
      Receiving[Receiving Service]
      Inventory[Inventory Service]
      Allocation[Allocation + Wave Service]
      Fulfillment[Pick/Pack Service]
      Shipping[Shipping Service]
      Exception[Exception Service]
    end

    Edge --> Receiving
    Edge --> Inventory
    Edge --> Allocation
    Edge --> Fulfillment
    Edge --> Shipping
    Edge --> Exception

    subgraph Platform[Platform Capabilities]
      RuleEngine[Rule Engine]
      Outbox[Outbox Relay]
      Observability[Metrics/Logs/Tracing]
      Policy[AuthZ + Approval Policy]
    end

    Allocation --> RuleEngine
    CoreServices --> Outbox
    CoreServices --> Observability
    Exception --> Policy

    subgraph DataInfra[Data + Messaging]
      DB[(PostgreSQL Cluster)]
      MQ[(Event Bus)]
      Cache[(Redis)]
      Lake[(Analytics Lakehouse)]
    end

    CoreServices --> DB
    CoreServices --> MQ
    CoreServices --> Cache
    MQ --> Lake
```

## Architecture Decisions
- Command-side consistency anchored in OLTP transactions + outbox.
- Read models may lag; command truth remains deterministic per partition key.
- Exception management is first-class service, not ad-hoc side effect.
