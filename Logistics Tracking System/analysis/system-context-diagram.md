# System Context Diagram

```mermaid
flowchart LR
  Dispatcher --> LTS[Logistics Tracking System]
  Driver --> LTS
  Customer --> LTS
  LTS --> Carrier[Carrier APIs]
  LTS --> Maps[Maps/GPS]
  LTS --> ERP
```
