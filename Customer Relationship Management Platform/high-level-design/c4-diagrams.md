# C4 Diagrams

## C1: System Context
```mermaid
flowchart LR
    User[Sales User] --> CRM[CRM Platform]
    Manager[Manager] --> CRM
    Ops[RevOps] --> CRM
    CRM <--> MAP[Marketing Automation]
    CRM <--> ERP[ERP/Billing]
    CRM <--> Mail[Email/Calendar]
    CRM --> BI[Analytics Warehouse]
    SSO[Identity Provider] --> CRM
```

## C2: Container View
```mermaid
flowchart TB
    UI[Web/Mobile UI]
    API[API/BFF Container]
    Core[Domain Services Container]
    Jobs[Async Worker Container]
    DB[(Transactional DB)]
    Bus[(Event Bus)]
    Search[(Search Index)]
    WH[(Data Warehouse)]

    UI --> API --> Core
    Core --> DB
    Core --> Bus
    Jobs --> DB
    Jobs --> Bus
    Jobs --> Search
    Jobs --> WH
```

## Domain Glossary
- **Container Responsibility**: File-specific term used to anchor decisions in **C4 Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Context Defined -> Containers Modeled -> Components Allocated -> Reviewed`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Context Defined] --> B[Containers Modeled]
    B[Containers Modeled] --> C[Components Allocated]
    C[Components Allocated] --> D[Reviewed]
    D[Reviewed]
```

## Integration Boundaries
- C4 views connect product, platform, security, and operations stakeholders.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Contract conflicts between C4 levels block approval until resolved.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Context, container, and component levels are all present with version date.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
