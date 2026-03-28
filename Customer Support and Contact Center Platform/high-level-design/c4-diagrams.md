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
