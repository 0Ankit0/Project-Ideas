# Swimlane Diagrams

## Ticket Resolution Swimlane
```mermaid
flowchart LR
    subgraph Customer
      A[Submit issue]
      B[Respond to clarification]
    end

    subgraph Platform
      C[Create and classify ticket]
      D[Route to queue]
      E[Track SLA]
    end

    subgraph Agent
      F[Investigate and respond]
      G[Resolve ticket]
    end

    subgraph Supervisor
      H[Intervene on escalation]
    end

    A --> C --> D --> F --> B --> F --> G
    E --> H --> F
```

## QA Evaluation Swimlane
```mermaid
flowchart LR
    subgraph Platform
      A[Sample interactions]
      B[Prepare QA scorecard]
    end

    subgraph QA
      C[Review transcript/call]
      D[Score criteria]
    end

    subgraph Supervisor
      E[Coach agent]
      F[Track improvement]
    end

    A --> B --> C --> D --> E --> F
```

## Swimlane Operational Narrative
Swimlanes should model **Customer**, **Bot**, **Routing Service**, **Agent**, **Supervisor**, and **Compliance/Audit** tracks with explicit handoff points.

```mermaid
flowchart LR
    subgraph Customer
      C1[Submit Message]
    end
    subgraph Bot
      B1[Intent + Deflection]
    end
    subgraph Routing
      R1[Queue + Skill Match]
    end
    subgraph Agent
      A1[Handle Case]
    end
    subgraph Supervisor
      S1[Escalation Decision]
    end
    subgraph Audit
      U1[Immutable Log]
    end
    C1-->B1-->R1-->A1-->U1
    A1-- breach risk -->S1-->U1
```

SLA checkpoints should be shown on lane boundaries, and incident responsibilities should be explicit (who acknowledges degraded routing, who authorizes queue bypass).

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
