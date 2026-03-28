# Data Flow Diagrams

```mermaid
flowchart LR
  Event --> Ingest[Ingestion API] --> Normalize[Normalize/Template] --> Dispatch[(Dispatch Queue)] --> Provider
  Provider --> Callback --> Metrics[(Delivery Metrics)]
```
