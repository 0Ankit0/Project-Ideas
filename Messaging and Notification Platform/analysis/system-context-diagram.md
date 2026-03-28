# System Context Diagram

```mermaid
flowchart LR
  User[End User] --> MNP[Messaging & Notification Platform]
  Admin[Operations Admin] --> MNP
  Product[Business System] --> MNP
  MNP --> Email[Email Provider]
  MNP --> SMS[SMS Provider]
  MNP --> Push[Push Gateway]
  MNP --> Chat[Chat/Webhook Channels]
  MNP --> BI[Analytics]
```
