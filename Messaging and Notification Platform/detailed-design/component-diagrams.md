# Component Diagrams

```mermaid
flowchart LR
  API[API Layer] --> Orchestrator[Dispatch Orchestrator]
  Orchestrator --> Tmpl[Template Service]
  Orchestrator --> Pref[Preference Service]
  Orchestrator --> Queue[(Queue)]
  Queue --> Email[Email Worker]
  Queue --> SMS[SMS Worker]
  Queue --> Push[Push Worker]
  Email --> Metrics[Metrics Service]
  SMS --> Metrics
  Push --> Metrics
```
