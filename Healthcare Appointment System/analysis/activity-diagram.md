# Activity Diagram

```mermaid
flowchart TD
  A[Patient requests slot] --> B[Check provider availability]
  B --> C{Slot available?}
  C -- No --> D[Offer alternatives]
  C -- Yes --> E[Reserve slot]
  D --> E
  E --> F[Send confirmation/reminder]
```
