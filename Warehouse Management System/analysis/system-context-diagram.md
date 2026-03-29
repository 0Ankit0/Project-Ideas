# System Context Diagram

```mermaid
flowchart LR
    subgraph InternalActors
      Picker[Picker]
      Supervisor[Supervisor]
      Planner[Planner]
      Transport[Transport Coordinator]
    end

    WMS[Warehouse Management System]

    subgraph ExternalSystems
      OMS[Order Management System]
      ERP[ERP / Procurement]
      TMS[Transportation Mgmt System]
      CARR[Carrier APIs]
      SCN[Scanner Fleet Manager]
      BI[BI / Data Platform]
      IAM[Corporate IAM]
    end

    Picker --> WMS
    Supervisor --> WMS
    Planner --> WMS
    Transport --> WMS

    WMS <--> OMS
    WMS <--> ERP
    WMS <--> TMS
    WMS <--> CARR
    WMS <--> SCN
    WMS --> BI
    IAM --> WMS
```

## Interface Contracts
- OMS: order release, cancellation, backorder updates.
- ERP: ASN/PO master data, inventory financial reconciliation.
- Carrier APIs: manifest, label, tracking events.
- Scanner manager: device identity, offline replay uploads.
