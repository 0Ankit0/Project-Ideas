# System Sequence Diagrams

```mermaid
sequenceDiagram
  actor User
  participant API
  participant WF
  participant Cloud
  User->>API: request resource
  API->>WF: start lifecycle workflow
  WF->>Cloud: provision
  Cloud-->>WF: success
  WF-->>API: complete
```
