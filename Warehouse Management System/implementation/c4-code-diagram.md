# C4 Code Diagram

```mermaid
flowchart TB
    subgraph Interface
      ReceivingController
      AllocationController
      FulfillmentController
      ShippingController
      ExceptionController
    end

    subgraph Application
      ReceivingAppService
      AllocationAppService
      FulfillmentAppService
      ShippingAppService
      ExceptionAppService
    end

    subgraph Domain
      ReceiptAggregate
      InventoryAggregate
      ReservationAggregate
      PickPackAggregate
      ShipmentAggregate
      ExceptionAggregate
      StateGuard
    end

    subgraph Infrastructure
      Repositories
      OutboxPublisher
      CarrierAdapter
      ScannerAdapter
      MetricsAudit
    end

    Interface --> Application --> Domain
    Domain --> StateGuard
    Application --> Repositories
    Application --> OutboxPublisher
    ShippingAppService --> CarrierAdapter
    FulfillmentAppService --> ScannerAdapter
    Application --> MetricsAudit
```

## Code-Level Notes
- Aggregates own invariants; services orchestrate transactions.
- StateGuard library is reused by API and worker handlers.
- OutboxPublisher is invoked only after commit.
