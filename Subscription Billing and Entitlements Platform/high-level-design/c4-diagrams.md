# C4 Diagrams

## C1 Context
```mermaid
flowchart LR
    Customer --> SBEP[Billing Platform]
    Support --> SBEP
    Finance --> SBEP
    SBEP <--> PSP[Payment Provider]
    SBEP --> ERP[ERP/GL]
    SBEP --> CRM[CRM]
    SBEP --> Notify[Notification Service]
```

## C2 Containers
```mermaid
flowchart TB
    Portal[Customer/Admin Portal]
    API[Billing API]
    Core[Core Billing Services]
    Worker[Async Worker]
    DB[(Billing DB)]
    MQ[(Event Bus)]

    Portal --> API --> Core
    Core --> DB
    Core --> MQ
    Worker --> DB
    Worker --> MQ
```
