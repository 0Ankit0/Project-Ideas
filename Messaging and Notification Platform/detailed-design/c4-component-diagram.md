# C4 Component Diagram

```mermaid
flowchart TB
  User --> Console[Admin Console]
  App --> API[Notification API]
  API --> Dispatch[Dispatch Component]
  API --> Prefs[Preference Component]
  Dispatch --> Providers[Provider Adapters]
  Dispatch --> Store[(Notification DB)]
  Dispatch --> Bus[(Event Bus)]
```
