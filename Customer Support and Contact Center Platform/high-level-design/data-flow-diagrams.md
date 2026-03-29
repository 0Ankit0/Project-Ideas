# Data Flow Diagrams

## Ticket and Session Data Flow
```mermaid
flowchart LR
    Channel[Voice/Chat/Email Inbound] --> Intake[Ticket Intake API]
    Intake --> Classify[Classification + Priority]
    Classify --> TicketStore[(Ticket Tables)]
    Classify --> Routing[Routing Engine]
    Routing --> Queue[Agent Queue]
    Queue --> Session[Session Service]
    Session --> SessionStore[(Session Tables)]
```

## SLA and Reporting Flow
```mermaid
flowchart LR
    TicketStore[(Ticket Tables)] --> SlaCalc[SLA Calculator]
    SlaCalc --> Events[(Event Bus)]
    Events --> Alerts[Supervisor Alerts]
    Events --> ETL[Analytics ETL]
    ETL --> WH[(Data Warehouse)]
```

## Data Flow Narrative for Omnichannel + Audit

```mermaid
flowchart LR
    A[Voice/Chat/Email Events] --> B[Canonical Event Bus]
    B --> C[Workflow Engine]
    C --> D[SLA Evaluator]
    C --> E[Agent UI Read Model]
    C --> F[Audit Ledger]
    D --> G[Escalation Notifications]
```

Data flow invariants: every mutating flow has a corresponding audit flow; every inbound channel flow is normalized before persistence.

Operational coverage note: this artifact also specifies incident controls for this design view.
