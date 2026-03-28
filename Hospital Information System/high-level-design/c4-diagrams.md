# C4 Diagrams

## C1: Context
```mermaid
flowchart LR
    Clinician[Clinician] --> HIS[Hospital Information System]
    FrontDesk[Front Desk] --> HIS
    BillingTeam[Billing Team] --> HIS
    HIS <--> Lab[Lab System]
    HIS <--> Radiology[Radiology System]
    HIS --> Payer[Payer Gateway]
    IdP[SSO/IdP] --> HIS
```

## C2: Containers
```mermaid
flowchart TB
    UI[Web/Portal]
    API[API/BFF]
    Core[Core Clinical Services]
    Worker[Async Worker]
    DB[(OLTP DB)]
    MQ[(Event Bus)]
    WH[(Warehouse)]

    UI --> API --> Core
    Core --> DB
    Core --> MQ
    Worker --> DB
    Worker --> MQ
    Worker --> WH
```
