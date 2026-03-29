# Class Diagrams

```mermaid
classDiagram
    class Receipt {
      +receiptId
      +asnLineId
      +receivedQty
      +status
      +confirm()
      +reject(reason)
    }

    class InventoryBalance {
      +warehouseId
      +sku
      +binId
      +onHand
      +reserved
      +reserve(qty)
      +release(qty)
      +assertNonNegativeATP()
    }

    class Reservation {
      +reservationId
      +orderLineId
      +qty
      +state
      +activate()
      +cancel()
    }

    class PickTask {
      +taskId
      +reservationId
      +state
      +confirmPick(qty)
      +markShortPick()
    }

    class PackSession {
      +packSessionId
      +shipmentId
      +reconcileLines()
      +close()
    }

    class Shipment {
      +shipmentId
      +trackingNo
      +status
      +confirmHandoff()
    }

    class ExceptionCase {
      +caseId
      +type
      +state
      +resolve(action)
    }

    Receipt --> InventoryBalance : creates ledger movement
    InventoryBalance --> Reservation : supports
    Reservation --> PickTask : fulfilled by
    PickTask --> PackSession : reconciled in
    PackSession --> Shipment : generates
    PickTask --> ExceptionCase : may raise
```

## Domain Rules in Classes
- `InventoryBalance.assertNonNegativeATP()` maps BR-7.
- `PackSession.close()` must fail on reconciliation mismatch (BR-8).
- `ExceptionCase.resolve()` requires evidence for override path (BR-4).
