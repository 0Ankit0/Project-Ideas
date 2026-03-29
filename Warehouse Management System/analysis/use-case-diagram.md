# Use Case Diagram

```mermaid
flowchart LR
    subgraph Actors
      RA[Receiving Associate]
      IP[Inventory Planner]
      PK[Picker]
      PO[Pack Operator]
      TC[Transport Coordinator]
      SV[Supervisor]
    end

    subgraph WMS[Warehouse Management System]
      UC1((Receive & Validate Inbound))
      UC2((Generate Putaway Tasks))
      UC3((Allocate Orders))
      UC4((Create/Release Waves))
      UC5((Confirm Pick Tasks))
      UC6((Reconcile Packing))
      UC7((Confirm Shipment Handoff))
      UC8((Resolve Exceptions))
      UC9((Approve Override))
    end

    RA --> UC1 --> UC2
    IP --> UC3 --> UC4
    PK --> UC5
    PO --> UC6
    TC --> UC7
    SV --> UC8
    SV --> UC9

    UC1 -. creates .-> UC8
    UC5 -. short pick .-> UC8
    UC6 -. mismatch .-> UC8
    UC7 -. carrier outage .-> UC8
    UC8 -. may require .-> UC9
```

## Coverage Notes
- UC1/UC2 enforce receiving validation and idempotent putaway generation.
- UC5/UC6/UC7 define the controlled pick-pack-ship progression.
- UC8/UC9 ensure exception and override controls are explicit.
