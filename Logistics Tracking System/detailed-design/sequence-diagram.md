# Sequence Diagram

```mermaid
sequenceDiagram
  actor Driver
  participant App
  participant API
  participant Track
  Driver->>App: update status/location
  App->>API: POST tracking event
  API->>Track: persist event
  Track-->>API: ack
  API-->>App: accepted
```
