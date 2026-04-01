# System Sequence Diagrams — Rental Management System

This document captures the key interaction flows between actors and system components
for the Rental Management System. Each diagram uses UML sequence notation and
represents production-level behaviour including error paths, asynchronous events,
and compensating transactions.

---

## 1. Online Booking Flow

A registered customer searches for available assets, selects one, receives a dynamic
price quote, creates a booking, and pays a pre-authorised security deposit. The asset
is then locked for the customer's window and a confirmation is dispatched.

```mermaid
sequenceDiagram
    autonumber
    participant Customer
    participant WebApp
    participant BookingService
    participant AssetService
    participant PricingEngine
    participant PaymentGateway
    participant NotificationService

    Customer->>WebApp: Enter search criteria (category, dates, location)
    WebApp->>AssetService: GET /assets/search?category=&start=&end=&location=
    AssetService-->>WebApp: 200 OK — list of available assets with thumbnail URLs

    Customer->>WebApp: Select asset, view detail page
    WebApp->>AssetService: GET /assets/{assetId}
    AssetService-->>WebApp: 200 OK — full asset detail (specs, photos, policies)

    WebApp->>AssetService: GET /assets/{assetId}/availability?start=&end=
    AssetService-->>WebApp: 200 OK — { available: true, blockedSlots: [] }

    WebApp->>PricingEngine: POST /pricing/quote { assetId, customerId, start, end, promoCode }
    PricingEngine->>AssetService: GET /assets/{assetId}/rates
    AssetService-->>PricingEngine: base daily/hourly rate + deposit percentage
    PricingEngine-->>WebApp: 200 OK — { baseAmount, taxes, depositAmount, lineItems[] }

    Customer->>WebApp: Confirm booking details and proceed to payment
    WebApp->>BookingService: POST /bookings { customerId, assetId, start, end, quoteId }
    BookingService->>AssetService: GET /assets/{assetId}/availability (re-validate)
    AssetService-->>BookingService: 200 OK — still available

    BookingService->>PricingEngine: POST /pricing/finalise { quoteId }
    PricingEngine-->>BookingService: 200 OK — finalised amounts (quote locked for 15 min)

    BookingService-->>WebApp: 201 Created — { bookingId, status: PENDING_PAYMENT, expiresAt }

    WebApp->>PaymentGateway: POST /payments/pre-auth { bookingId, amount: depositAmount, card }
    PaymentGateway-->>WebApp: 200 OK — { authCode, preAuthId, expiresAt }

    WebApp->>BookingService: PATCH /bookings/{bookingId}/payment { preAuthId, authCode }
    BookingService->>AssetService: POST /assets/{assetId}/lock { bookingId, until: pickupDeadline }
    AssetService-->>BookingService: 200 OK — asset status → RESERVED

    BookingService-->>WebApp: 200 OK — { bookingId, status: CONFIRMED }

    BookingService--)NotificationService: EVENT booking.confirmed { bookingId, customerId, assetId, dates }
    NotificationService-->>Customer: Email — Booking Confirmation (PDF itinerary attached)
    NotificationService-->>Customer: SMS — "Your booking #BK-00123 is confirmed. Pick-up: 15 Jun 09:00"
```

---

## 2. Asset Checkout Flow

Staff uses the mobile app to walk through the checkout process: they verify the
booking, record the asset's pre-rental condition, capture mileage and fuel readings,
generate a legally-binding rental contract, collect the customer's digital signature,
and activate the rental.

```mermaid
sequenceDiagram
    autonumber
    participant Customer
    participant Staff as Staff (MobileApp)
    participant CheckoutService
    participant RentalService
    participant ContractService
    participant SignatureService

    Staff->>CheckoutService: POST /checkout/initiate { bookingId, staffId }
    CheckoutService->>RentalService: GET /bookings/{bookingId}
    RentalService-->>CheckoutService: booking details (customerId, assetId, dates, depositPreAuthId)
    CheckoutService-->>Staff: 200 OK — checkout session { sessionId, checklistItems[] }

    Staff->>CheckoutService: POST /checkout/{sessionId}/verify-id { customerId, documentScan }
    CheckoutService-->>Staff: 200 OK — identity verified, age check passed

    Staff->>CheckoutService: POST /checkout/{sessionId}/condition { photos[], notes, fuel: FULL, mileage: 12450 }
    CheckoutService-->>Staff: 200 OK — pre-rental condition recorded { conditionReportId }

    Staff->>ContractService: POST /contracts/generate { bookingId, conditionReportId, staffId }
    ContractService->>RentalService: GET /bookings/{bookingId}/financials
    RentalService-->>ContractService: rental amounts, deposit, policies, late-fee schedule
    ContractService-->>Staff: 200 OK — { contractId, contractUrl, pages: 4 }

    Staff->>Customer: Present contract on tablet for review
    Customer->>SignatureService: POST /signatures { contractId, signatureData, timestamp, geoLocation }
    SignatureService-->>Customer: 200 OK — signature captured { signatureId }

    SignatureService--)ContractService: EVENT contract.signed { contractId, signatureId }
    ContractService-->>Staff: contract finalised — PDF sealed with e-signature

    Staff->>CheckoutService: POST /checkout/{sessionId}/complete { signatureId }
    CheckoutService->>RentalService: POST /rentals { bookingId, conditionReportId, contractId, actualStart }
    RentalService-->>CheckoutService: 201 Created — { rentalId, status: ACTIVE }

    CheckoutService--)RentalService: EVENT rental.activated { rentalId, assetId, customerId }
    RentalService-->>Staff: 200 OK — rental is ACTIVE, keys authorised for release
    RentalService-->>Customer: Push notification — "Your rental has started. Return by: 18 Jun 17:00"
```

---

## 3. Asset Return and Deposit Release Flow

Staff processes the return: checks condition against the pre-rental report, records
closing mileage and fuel, raises damage claims if defects are found, charges any late
fees, notifies the customer, and manages the deposit release or deduction within the
48-hour damage assessment window.

```mermaid
sequenceDiagram
    autonumber
    participant Customer
    participant Staff as Staff (MobileApp)
    participant ReturnService
    participant DamageService
    participant DepositService
    participant PaymentGateway
    participant NotificationService

    Staff->>ReturnService: POST /returns/initiate { rentalId, staffId }
    ReturnService-->>Staff: 200 OK — return session { sessionId, preRentalCondition, expectedReturn }

    Staff->>ReturnService: POST /returns/{sessionId}/condition { photos[], fuel: 3_4, mileage: 12920, notes }
    ReturnService-->>Staff: 200 OK — post-rental condition recorded { conditionReportId }

    ReturnService->>ReturnService: Compare pre vs post condition reports

    alt No damage detected
        ReturnService-->>Staff: condition delta — no damage flagged
    else Damage detected
        ReturnService->>DamageService: POST /damage-reports { rentalId, conditionReportId, damageItems[] }
        DamageService-->>ReturnService: 201 Created — { damageReportId, estimatedRepairCost: 350.00 }
        ReturnService-->>Staff: damage report created — customer will be notified
    end

    ReturnService->>ReturnService: Calculate late fee (actualReturn vs scheduledReturn)

    alt Returned late
        ReturnService->>DepositService: GET /deposits/{rentalId}
        DepositService-->>ReturnService: { depositId, heldAmount: 500.00 }
        ReturnService->>PaymentGateway: POST /charges { rentalId, amount: lateFee, reason: LATE_RETURN }
        PaymentGateway-->>ReturnService: 200 OK — { chargeId, status: CAPTURED }
    end

    ReturnService->>ReturnService: Mark rental status → RETURNED

    ReturnService--)NotificationService: EVENT return.processed { rentalId, customerId, lateFee, damageReportId }
    NotificationService-->>Customer: Email — Return Receipt (mileage, fuel, charges summary)
    NotificationService-->>Customer: SMS — "Return received. Deposit review in progress — 48h window."

    alt No damage report
        DepositService->>PaymentGateway: POST /deposits/{depositId}/release
        PaymentGateway-->>DepositService: 200 OK — deposit refunded to original payment method
        DepositService--)NotificationService: EVENT deposit.released { customerId, amount: 500.00 }
        NotificationService-->>Customer: Email — "Your deposit of $500 has been released."
    else Damage report exists
        DepositService->>DepositService: Start 48-hour damage assessment window
        DepositService--)NotificationService: EVENT damage.assessment.started { customerId, deadline }
        NotificationService-->>Customer: Email — "Damage identified. Assessment due by [deadline]. You may dispute."

        Note over DamageService,DepositService: 48h later — damage assessment complete
        DamageService->>DepositService: POST /deposits/{depositId}/deduct { amount: repairCost, damageReportId }
        DepositService->>PaymentGateway: POST /charges { depositId, amount: repairCost, reason: DAMAGE }
        PaymentGateway-->>DepositService: 200 OK — { chargeId, status: CAPTURED }

        DepositService->>PaymentGateway: POST /deposits/{depositId}/release { remainingAmount }
        PaymentGateway-->>DepositService: 200 OK — remainder refunded

        DepositService--)NotificationService: EVENT deposit.partially.released { customerId, deducted, refunded }
        NotificationService-->>Customer: Email — Damage charge breakdown + remaining deposit refund notice
    end
```

---

## 4. Rental Extension Flow

A customer requests to extend an active rental from the web app. The system verifies
the asset is not reserved by another booking, recalculates the price for the
additional period, charges the stored payment method, updates the rental end date,
and notifies the customer.

```mermaid
sequenceDiagram
    autonumber
    participant Customer
    participant WebApp
    participant RentalService
    participant AssetService
    participant PricingEngine
    participant PaymentGateway

    Customer->>WebApp: Navigate to "My Rentals" → select active rental → "Request Extension"
    Customer->>WebApp: Enter new return date/time

    WebApp->>RentalService: GET /rentals/{rentalId}
    RentalService-->>WebApp: 200 OK — { rentalId, assetId, currentEnd, status: ACTIVE }

    WebApp->>AssetService: GET /assets/{assetId}/availability?start=currentEnd&end=newEnd
    AssetService-->>WebApp: 200 OK — { available: true }

    alt Asset not available
        AssetService-->>WebApp: 409 Conflict — asset reserved by another booking after currentEnd
        WebApp-->>Customer: "Extension not available for the requested period."
    else Asset available
        WebApp->>PricingEngine: POST /pricing/extension-quote { rentalId, newEnd }
        PricingEngine->>RentalService: GET /rentals/{rentalId}/rate-context
        RentalService-->>PricingEngine: original rate tier, loyalty discount, promo applied
        PricingEngine-->>WebApp: 200 OK — { extensionAmount, dailyRate, taxes, totalDue }

        Customer->>WebApp: Confirm extension and authorise charge

        WebApp->>PaymentGateway: POST /payments/charge { rentalId, amount: extensionAmount, savedCardToken }
        PaymentGateway-->>WebApp: 200 OK — { chargeId, status: CAPTURED }

        WebApp->>RentalService: PATCH /rentals/{rentalId}/extend { newEnd, chargeId, extensionAmount }
        RentalService->>AssetService: PATCH /assets/{assetId}/reservation { bookingEnd: newEnd }
        AssetService-->>RentalService: 200 OK — availability window updated

        RentalService-->>WebApp: 200 OK — { rentalId, newEnd, status: ACTIVE }
        WebApp-->>Customer: "Extension confirmed. New return date: [newEnd]"

        RentalService--)RentalService: Publish EVENT rental.extended { rentalId, customerId, newEnd, charged }
        RentalService-->>Customer: Email — Extension Confirmation with updated rental summary
        RentalService-->>Customer: Push notification — "Rental extended to [newEnd]"
    end
```

---

## 5. Late Payment and Dunning Flow

When a charge fails post-rental (e.g., damage deduction), the system retries the
payment, escalates to dunning, and eventually blocks the customer if the debt
remains unresolved.

```mermaid
sequenceDiagram
    autonumber
    participant PaymentService
    participant PaymentGateway
    participant CustomerService
    participant NotificationService
    participant DunningEngine

    PaymentService->>PaymentGateway: POST /charges { customerId, amount, reason: DAMAGE_DEDUCTION }
    PaymentGateway-->>PaymentService: 402 Payment Required — card declined

    PaymentService--)DunningEngine: EVENT payment.failed { customerId, amount, attempt: 1 }

    DunningEngine->>NotificationService: Send dunning notice attempt 1
    NotificationService-->>CustomerService: Email — "Payment of $350 failed. Please update your card."

    Note over DunningEngine: Wait 24h

    DunningEngine->>PaymentGateway: POST /charges (retry attempt 2)
    PaymentGateway-->>DunningEngine: 402 Payment Required — still declined

    DunningEngine->>NotificationService: Send dunning notice attempt 2
    NotificationService-->>CustomerService: Email — "2nd notice: outstanding balance $350. Account may be suspended."

    Note over DunningEngine: Wait 48h

    DunningEngine->>PaymentGateway: POST /charges (retry attempt 3)
    PaymentGateway-->>DunningEngine: 402 Payment Required — still declined

    DunningEngine->>CustomerService: PATCH /customers/{customerId}/status { blacklisted: true, reason: UNPAID_BALANCE }
    CustomerService-->>DunningEngine: 200 OK — customer flagged

    DunningEngine->>NotificationService: Send final dunning notice
    NotificationService-->>CustomerService: Email — "Account suspended. Contact support to resolve outstanding balance."

    DunningEngine--)PaymentService: EVENT dunning.escalated { customerId, amount, referToCreditTeam: true }
```

---

## Notes on Diagram Conventions

| Symbol | Meaning |
|--------|---------|
| `->>` | Synchronous request |
| `-->>` | Synchronous response |
| `-)` | Asynchronous fire-and-forget event |
| `Note over` | Contextual annotation or timer |
| `alt / else / end` | Conditional branching |

All services communicate over HTTPS REST internally via the API Gateway.
Asynchronous events (`->>`) are published to Apache Kafka topics and consumed by
subscriber services.

Error responses follow RFC 7807 `application/problem+json` format throughout.
