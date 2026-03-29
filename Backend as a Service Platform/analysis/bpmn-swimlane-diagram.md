# BPMN Swimlane Diagram - Backend as a Service Platform

```mermaid
flowchart LR
    subgraph lane1[Project Owner / Tenant Admin]
        o1[Create project and environment]
        o2[Choose providers]
        o3[Approve migration / switchover]
    end

    subgraph lane2[App Developer]
        d1[Integrate SDK]
        d2[Use auth, data, storage, functions, events]
    end

    subgraph lane3[Control Plane]
        c1[Validate bindings and secrets]
        c2[Store metadata in Postgres]
        c3[Generate migration plan]
    end

    subgraph lane4[Capability Adapters]
        a1[Activate provider binding]
        a2[Execute capability operations]
        a3[Run migration or cutover steps]
    end

    subgraph lane5[Platform Operations]
        p1[Monitor health and audits]
        p2[Approve rollback or retry]
    end

    o1 --> c1 --> c2 --> o2 --> c1 --> a1 --> d1 --> d2 --> a2 --> p1
    o3 --> c3 --> a3 --> p2 --> p1
```

## Swimlane Interpretation

- The control plane owns validation, metadata, policy, and migration orchestration.
- Capability adapters perform provider-specific activation and runtime work while staying behind unified contracts.
- Platform operations remain involved whenever migration, health degradation, or rollback decisions are needed.

## BPMN Extension: Migration Governance Swimlane

```mermaid
flowchart LR
    subgraph Admin
      A1[Submit migration plan]
      A2[Approve cutover]
    end
    subgraph ControlPlane
      B1[Validate contract/version]
      B2[Start operation]
      B3[Track lifecycle state]
    end
    subgraph Adapter
      C1[Run dry-run]
      C2[Apply migration]
      C3[Return verification]
    end
    subgraph Observability
      D1[Compute SLI/SLO impact]
      D2[Trigger alert if burn high]
    end
    A1 --> B1 --> C1 --> B2 --> C2 --> C3 --> B3 --> D1
    D1 --> D2
    B3 --> A2
```
