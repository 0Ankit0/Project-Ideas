# Component Diagrams (Implementation Ready)

## 1. Service Component Topology
```mermaid
flowchart LR
    subgraph API[API Layer]
      GW[Gateway/BFF]
      BillAPI[Billing API]
      EntAPI[Entitlements API]
      OpsAPI[Ops/Recovery API]
    end

    subgraph Core[Domain Services]
      Catalog[Catalog Service]
      SubSvc[Subscription Service]
      Proration[Proration Engine]
      InvoiceSvc[Invoice Service]
      PaymentSvc[Payment Orchestrator]
      DunningSvc[Dunning Service]
      EntSvc[Entitlement Runtime]
      EntProj[Entitlement Projector]
      ReconSvc[Reconciliation Service]
      RecoverySvc[Replay/Compensation Service]
    end

    subgraph Integrations[External Integrations]
      PSP[Payment Provider]
      Tax[Tax Engine]
      ERP[ERP/GL]
      Notify[Notification]
    end

    subgraph Data[Data and Messaging]
      OLTP[(Postgres OLTP)]
      Ledger[(Ledger DB)]
      Bus[(Event Bus)]
      Cache[(Redis)]
      Wh[(Recon Warehouse)]
    end

    GW --> BillAPI --> SubSvc
    GW --> EntAPI --> EntSvc
    GW --> OpsAPI --> RecoverySvc

    SubSvc --> Catalog
    SubSvc --> Proration
    Proration --> InvoiceSvc
    InvoiceSvc --> PaymentSvc
    InvoiceSvc --> DunningSvc
    PaymentSvc --> PSP
    InvoiceSvc --> Tax
    InvoiceSvc --> ERP

    SubSvc --> OLTP
    InvoiceSvc --> OLTP
    PaymentSvc --> OLTP
    EntSvc --> Cache
    EntProj --> OLTP
    ReconSvc --> Wh
    RecoverySvc --> OLTP
    InvoiceSvc --> Ledger
    PaymentSvc --> Ledger

    SubSvc --> Bus
    InvoiceSvc --> Bus
    PaymentSvc --> Bus
    Bus --> EntProj
    Bus --> ReconSvc
    Bus --> Notify
```

## 2. Entitlement Enforcement Components
```mermaid
flowchart TD
    Req[Incoming API Request] --> Decision[Entitlement Decision Engine]
    Decision --> CacheRead[Snapshot Cache Read]
    CacheRead --> Policy[Policy Evaluator]
    Policy --> Grace[Grace Window Evaluator]
    Grace --> Quota[Quota Validator]
    Quota --> Result[allow | deny | soft_limit]

    BusEvents[Billing/Payment Events] --> Projector[Entitlement Projector]
    Projector --> SnapshotStore[(Snapshot Store)]
    SnapshotStore --> CacheRead
```

## 3. Reconciliation and Recovery Components
```mermaid
flowchart TD
    Facts[Invoice/Ledger/Entitlement Facts] --> Compare[Drift Comparator]
    Compare --> Classify[Drift Classifier A/B/C]
    Classify --> Queue[Incident Queue]
    Queue --> Plan[Recovery Planner]
    Plan --> DryRun[Dry-run Simulator]
    DryRun --> Approve[Approval Workflow]
    Approve --> Execute[Replay/Compensation Executor]
    Execute --> Verify[Post-repair Recon]
```
