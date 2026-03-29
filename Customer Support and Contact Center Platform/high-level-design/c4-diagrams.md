# C4 Diagrams

## C1 Context
```mermaid
flowchart LR
    Customer --> CCS[Contact Center Platform]
    Agent --> CCS
    Supervisor --> CCS
    CCS <--> Telephony[Telephony Platform]
    CCS <--> CRM[CRM]
    CCS --> BI[Analytics]
```

## C2 Containers
```mermaid
flowchart TB
    Console[Agent/Supervisor Console]
    API[Support API]
    Core[Core Services]
    Worker[Async Worker]
    DB[(Support DB)]
    MQ[(Event Bus)]

    Console --> API --> Core
    Core --> DB
    Core --> MQ
    Worker --> DB
    Worker --> MQ
```

## C4 Narrative Addendum
At C4 level, include personas and external systems that drive SLA behavior (pager, workforce management, compliance archive).

```mermaid
flowchart LR
    Customer-->System[Contact Center Platform]
    System-->CRM[CRM]
    System-->Pager[Incident Pager]
    System-->Archive[Compliance Archive]
    System-->WFM[Workforce Mgmt]
```

Container responsibilities should clearly split event ingestion, routing/state machine, SLA evaluation, and immutable auditing.

Operational coverage note: this artifact also specifies queue and omnichannel controls for this design view.
