# C4 Diagrams

## C1 Context
```mermaid
flowchart LR
    Customer --> POWP[Payments & Wallet Platform]
    Merchant --> POWP
    POWP <--> PSP[PSP/Acquirer]
    POWP <--> Bank[Bank Rails]
    POWP --> GL[General Ledger]
```

## C2 Containers
```mermaid
flowchart TB
    Portal[Merchant Console/App]
    API[Payments API]
    Core[Core Payment Services]
    Worker[Settlement Worker]
    DB[(Payments DB)]
    MQ[(Event Bus)]

    Portal --> API --> Core
    Core --> DB
    Core --> MQ
    Worker --> DB
    Worker --> MQ
```
