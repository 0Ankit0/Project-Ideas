# Event Catalog

| Event | Producer | Consumers | Notes |
|---|---|---|---|
| `ReservationCreated` | Reservation Service | Fulfillment, Notifications | Contains policy snapshot id |
| `ReservationConfirmed` | Reservation Service | Fulfillment, Settlement | Marks allocation lock-in |
| `FulfillmentStarted` | Fulfillment Service | Settlement, Analytics | Begins usage window |
| `ResourceReturned` | Fulfillment Service | Settlement, Incident Service | Includes return evidence refs |
| `SettlementPosted` | Settlement Service | ERP Adapter, Analytics | Financial close candidate |
| `DisputeOpened` | Incident Service | Settlement, Ops Console | Blocks close until resolved |
