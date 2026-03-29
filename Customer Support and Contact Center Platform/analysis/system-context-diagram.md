# System Context Diagram

```mermaid
flowchart LR
    subgraph Actors
      Agent[Support Agent]
      Supervisor[Contact Center Supervisor]
      Customer[End Customer]
      QA[Quality Analyst]
    end

    CCS[Customer Support and Contact Center Platform]

    subgraph External
      CRM[CRM]
      Telephony[Telephony/CCaaS]
      Chat[Chat & Messaging Channels]
      KB[Knowledge Base]
      WFM[Workforce Management]
      BI[Analytics/BI]
    end

    Agent --> CCS
    Supervisor --> CCS
    Customer --> CCS
    QA --> CCS

    CCS <--> CRM
    CCS <--> Telephony
    CCS <--> Chat
    CCS --> KB
    CCS --> WFM
    CCS --> BI
```

## System Context Narrative (Operational Concerns)
The context diagram must represent external channels (telephony, email, messaging apps), identity providers, CRM, workforce tools, and compliance archive.

```mermaid
flowchart TB
    U[Customers] --> CH[Omnichannel Gateways]
    CH --> CCS[Contact Center Core]
    CCS --> CRM[CRM/Case System]
    CCS --> WFM[Workforce Manager]
    CCS --> SLA[SLA/Policy Engine]
    CCS --> AUD[Audit Vault]
    CCS --> IR[Incident/On-call Platform]
```

- Queue routing is centralized in Contact Center Core; SLA policy engine is authoritative for escalation clocks.
- Omnichannel normalization occurs before core ingestion to avoid channel-specific branching.
- Audit vault is write-once and independently retained for compliance.
- Incident platform receives health and breach-risk signals for automated paging.
