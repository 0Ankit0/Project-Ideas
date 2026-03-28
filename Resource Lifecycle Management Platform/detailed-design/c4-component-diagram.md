# C4 Component Diagram

```mermaid
flowchart TB
  Users --> Portal
  Portal --> RequestComponent
  Portal --> LifecycleComponent
  LifecycleComponent --> PolicyComponent
  LifecycleComponent --> IntegrationComponent
  IntegrationComponent --> Cloud
  IntegrationComponent --> CMDB
  LifecycleComponent --> Store[(Lifecycle DB)]
```
