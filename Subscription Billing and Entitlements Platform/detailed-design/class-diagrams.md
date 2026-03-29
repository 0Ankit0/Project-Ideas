# Class Diagrams (Implementation Ready)

## 1. Domain Model Classes
```mermaid
classDiagram
    class Plan {
      +UUID planId
      +String code
      +PlanStatus status
      +publishVersion()
      +deprecate()
    }

    class PlanVersion {
      +UUID planVersionId
      +int versionNo
      +DateTime effectiveFrom
      +DateTime effectiveTo
      +MigrationPolicy migrationPolicy
      +Checksum checksum
    }

    class PriceComponentVersion {
      +UUID priceComponentVersionId
      +String metricKey
      +BillingCadence cadence
      +Money unitAmount
      +String currency
      +RoundingMode roundingMode
    }

    class Subscription {
      +UUID subscriptionId
      +SubscriptionStatus status
      +DateTime periodStart
      +DateTime periodEnd
      +activate()
      +pause()
      +cancel()
    }

    class SubscriptionItem {
      +UUID subscriptionItemId
      +UUID planVersionId
      +int quantity
      +amend()
    }

    class SubscriptionAmendment {
      +UUID amendmentId
      +ChangeType changeType
      +ProrationPolicy policy
      +DateTime effectiveAt
      +String idempotencyKey
    }

    class Invoice {
      +UUID invoiceId
      +InvoiceStatus status
      +Money subtotal
      +Money tax
      +Money total
      +finalize()
      +issue()
      +markPaid()
    }

    class InvoiceLine {
      +UUID invoiceLineId
      +LineType type
      +Decimal quantity
      +Money unitAmount
      +Money lineTotal
      +UUID sourceId
    }

    class Payment {
      +UUID paymentId
      +PaymentStatus status
      +Money amount
      +Money fees
      +settle()
    }

    class EntitlementGrant {
      +UUID entitlementId
      +String featureKey
      +EntitlementState state
      +int quotaLimit
      +DateTime graceUntil
      +grant()
      +suspend()
      +revoke()
    }

    class ReconRun {
      +UUID reconRunId
      +ReconType runType
      +ReconStatus status
      +execute()
      +publishReport()
    }

    class ReconDrift {
      +UUID driftId
      +DriftClass driftClass
      +String objectType
      +String objectId
      +Decimal amountDelta
      +openIncident()
    }

    class RecoveryAction {
      +UUID actionId
      +ActionType actionType
      +boolean dryRun
      +ActionStatus status
      +approve()
      +execute()
      +verify()
    }

    Plan "1" --> "many" PlanVersion
    PlanVersion "1" --> "many" PriceComponentVersion
    Subscription "1" --> "many" SubscriptionItem
    SubscriptionItem "1" --> "many" SubscriptionAmendment
    SubscriptionItem "many" --> "1" PlanVersion
    Subscription "1" --> "many" Invoice
    Invoice "1" --> "many" InvoiceLine
    Invoice "1" --> "many" Payment
    SubscriptionItem "1" --> "many" EntitlementGrant
    ReconRun "1" --> "many" ReconDrift
    ReconDrift "1" --> "many" RecoveryAction
```

## 2. Aggregate Ownership and Transaction Boundaries
- **Catalog Aggregate**: `Plan`, `PlanVersion`, `PriceComponentVersion` (immutable post-publish).
- **Subscription Aggregate**: `Subscription`, `SubscriptionItem`, `SubscriptionAmendment`.
- **Billing Aggregate**: `Invoice`, `InvoiceLine`, `Payment` with state transition logs.
- **Integrity Aggregate**: `ReconRun`, `ReconDrift`, `RecoveryAction`.

## 3. Invariants at Class Level
- `PlanVersion` cannot mutate economic fields after publish.
- `InvoiceLine` mutations are disallowed when parent invoice is finalized or later.
- `RecoveryAction.execute()` requires approved status unless `dryRun=true`.
