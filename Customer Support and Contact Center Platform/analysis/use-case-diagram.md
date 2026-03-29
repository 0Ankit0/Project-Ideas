# Use Case Diagram

```mermaid
flowchart LR
    Customer
    Agent
    Supervisor
    QA

    UC1((Create Ticket))
    UC2((Classify and Route Ticket))
    UC3((Handle Call/Chat Session))
    UC4((Escalate to Tier 2))
    UC5((Resolve and Close Ticket))
    UC6((Monitor SLA Breaches))
    UC7((Review Agent Quality))
    UC8((Publish Knowledge Article))

    Customer --> UC1
    Customer --> UC3
    Agent --> UC2
    Agent --> UC3
    Agent --> UC4
    Agent --> UC5
    Supervisor --> UC6
    QA --> UC7
    Supervisor --> UC8
```

## Use-Case Diagram Narrative Addendum
Actors should include **Customer**, **Agent**, **Supervisor**, **Compliance Officer**, and **Incident Commander**.

```mermaid
flowchart LR
    Customer-->UC1((Submit Issue))
    Agent-->UC2((Respond/Resolve))
    Supervisor-->UC3((Escalate Queue Item))
    Compliance-->UC4((Review Audit Trail))
    Incident-->UC5((Activate Degraded Mode))
    UC1-->UC2-->UC3
    UC2-->UC4
    UC3-->UC5
```

The diagram must explicitly show escalation and audit review as first-class use cases, not optional annotations.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
