# System Sequence Diagrams

## Overview
Black-box system sequence diagrams showing interactions between actors and the platform for the primary use cases of the rental management system.

---

## Customer Searches and Books an Asset

```mermaid
sequenceDiagram
    actor Customer
    participant Platform as Rental Management Platform
    participant PG as Payment Gateway
    actor Owner

    Customer->>Platform: GET /assets?category=car&start=...&end=...
    Platform-->>Customer: Available assets with pricing preview

    Customer->>Platform: GET /assets/{assetId}
    Platform-->>Customer: Asset details, photos, attributes, availability calendar

    Customer->>Platform: GET /assets/{assetId}/price?start=...&end=...
    Platform-->>Customer: Pricing breakdown { baseFee, peakSurcharge, tax, deposit, total }

    Customer->>Platform: POST /bookings { assetId, start, end }
    Platform->>PG: Hold / charge security deposit
    PG-->>Platform: Deposit confirmed
    Platform-->>Customer: 201 Booking created { bookingId, status: PENDING/CONFIRMED }
    Platform--)Owner: Notification: new booking request
```

---

## Owner Confirms Booking and Sends Rental Agreement

```mermaid
sequenceDiagram
    actor Owner
    participant Platform as Rental Management Platform
    participant ESign as E-Signature Provider
    actor Customer

    Owner->>Platform: GET /bookings/{bookingId}
    Platform-->>Owner: Booking details + customer profile

    Owner->>Platform: POST /bookings/{bookingId}/confirm
    Platform-->>Owner: 200 { status: CONFIRMED }
    Platform--)Customer: Notification: booking confirmed

    Owner->>Platform: POST /bookings/{bookingId}/agreement { templateId }
    Platform-->>Owner: 201 Agreement draft generated

    Owner->>Platform: POST /bookings/{bookingId}/agreement/send
    Platform->>ESign: Send document to customer for signature
    ESign-->>Platform: eSignRequestId
    Platform-->>Owner: 200 { status: PENDING_CUSTOMER_SIGNATURE }
    Platform--)Customer: Email: sign your rental agreement

    Customer->>ESign: Review and sign agreement
    ESign->>Platform: Webhook: customerSigned { timestamp, ip }
    Platform--)Owner: Notification: customer signed, please countersign

    Owner->>Platform: POST /bookings/{bookingId}/agreement/countersign
    Platform->>ESign: Record owner signature
    ESign-->>Platform: Final signed PDF URL
    Platform-->>Owner: 200 Agreement fully signed
    Platform--)Customer: Email: signed agreement PDF
```

---

## Pre-Rental Condition Assessment

```mermaid
sequenceDiagram
    actor Staff
    participant Platform as Rental Management Platform
    actor Customer

    Platform--)Staff: Task assigned: pre-rental assessment for booking {bookingId}

    Staff->>Platform: GET /assessments/{assessmentId}
    Platform-->>Staff: Assessment task with category-specific checklist

    Staff->>Platform: POST /assessments/{assessmentId}/items { items[] }
    Platform-->>Staff: 200 Items saved

    Staff->>Platform: POST /assessments/{assessmentId}/photos { photos[] }
    Platform-->>Staff: 200 Photos uploaded

    Staff->>Platform: POST /assessments/{assessmentId}/submit
    Platform-->>Staff: 200 Assessment submitted
    Platform--)Customer: Notification: review and sign pre-rental assessment

    Customer->>Platform: GET /assessments/{assessmentId}
    Platform-->>Customer: Assessment report with photos

    Customer->>Platform: POST /assessments/{assessmentId}/countersign
    Platform-->>Customer: 200 Countersigned; handover complete
    Platform--)Staff: Notification: handover confirmed
```

---

## Customer Pays Invoice

```mermaid
sequenceDiagram
    actor Customer
    participant Platform as Rental Management Platform
    participant PG as Payment Gateway
    actor Owner

    Platform--)Customer: Notification: invoice due { amount, dueDate }

    Customer->>Platform: GET /invoices/{invoiceId}
    Platform-->>Customer: Invoice details { lineItems, total, dueDate }

    Customer->>Platform: POST /invoices/{invoiceId}/pay { paymentMethod }
    Platform->>PG: Initiate payment { amount, method }
    PG-->>Platform: Payment session / redirect URL
    Platform-->>Customer: 200 { paymentUrl }

    Customer->>PG: Complete payment
    PG->>Platform: Webhook: paymentConfirmed { gatewayRef, amount }
    Platform-->>Platform: Mark invoice PAID; update ledger
    Platform--)Customer: Email: payment receipt
    Platform--)Owner: Notification: payment received
```

---

## Post-Rental Return and Settlement

```mermaid
sequenceDiagram
    actor Customer
    participant Platform as Rental Management Platform
    actor Staff
    participant PG as Payment Gateway
    actor Owner

    Customer->>Platform: POST /bookings/{bookingId}/return { actualReturnAt }
    Platform-->>Customer: 200 Return initiated
    Platform--)Staff: Notification: perform post-rental assessment

    Staff->>Platform: POST /assessments { bookingId, type: POST_RENTAL }
    Staff->>Platform: PUT /assessments/{id}/submit { items[], photos[] }
    Platform-->>Staff: 200 Assessment submitted

    Platform->>Platform: Compare pre vs post assessment

    alt No Damage, On Time
        Platform->>PG: Initiate full deposit refund
        PG-->>Platform: Refund confirmed
        Platform--)Customer: Notification: deposit refunded
    else Damage or Late Return
        Platform--)Owner: Notification: review post-rental assessment
        Owner->>Platform: POST /bookings/{bookingId}/additional-charges { charges[] }
        Platform-->>Owner: 200 Charges recorded
        Platform--)Customer: Notification: additional charges applied
        Customer->>Platform: POST /invoices/{finalInvoiceId}/pay
        Platform->>PG: Charge additional fees
        PG-->>Platform: Confirmed
    end

    Platform->>Platform: Close booking; unblock asset calendar
    Platform--)Owner: Notification: rental closed
```

---

## Maintenance Request Lifecycle

```mermaid
sequenceDiagram
    actor Owner
    participant Platform as Rental Management Platform
    actor Staff

    Owner->>Platform: POST /maintenance-requests { assetId, title, description, priority }
    Platform-->>Owner: 201 { requestId, status: OPEN }
    Platform->>Platform: Block asset availability calendar

    Owner->>Platform: PUT /maintenance-requests/{id}/assign { staffUserId }
    Platform-->>Owner: 200 Assigned
    Platform--)Staff: Notification: new maintenance task

    Staff->>Platform: PUT /maintenance-requests/{id}/status { status: IN_PROGRESS }
    Platform-->>Staff: 200 Updated

    Staff->>Platform: PUT /maintenance-requests/{id}/complete { notes, photos, materials }
    Platform-->>Staff: 200 Marked completed
    Platform--)Owner: Notification: work completed - review needed

    Owner->>Platform: PUT /maintenance-requests/{id}/approve
    Platform-->>Owner: 200 Approved and closed
    Owner->>Platform: POST /maintenance-requests/{id}/cost { amount, category }
    Platform-->>Owner: 200 Cost logged
    Platform->>Platform: Unblock asset availability calendar
```
