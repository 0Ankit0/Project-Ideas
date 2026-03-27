# Data Flow Diagrams

## Overview
Data flow diagrams (DFDs) showing how data moves through the rental management system for any asset type.

---

## Level 0 DFD – Context Diagram

```mermaid
graph LR
    Owner((Owner / Operator))
    Customer((Customer / Renter))
    Staff((Staff))
    Admin((Admin))
    PG((Payment Gateway))
    ESign((E-Signature Provider))

    RMS[Rental Management System]

    Owner -->|asset data, pricing rules, booking decisions, maintenance actions| RMS
    RMS -->|reports, notifications, signed agreements, payout statements| Owner

    Customer -->|search queries, booking requests, payments, return initiations| RMS
    RMS -->|asset listings, invoices, receipts, agreements, assessment reports| Customer

    Staff -->|assessment results, maintenance updates, cost logs| RMS
    RMS -->|assigned tasks, asset details, checklists| Staff

    Admin -->|user actions, platform config, dispute resolutions| RMS
    RMS -->|audit logs, platform metrics, alerts| Admin

    PG -->|payment confirmations, deposit webhooks, refund confirmations| RMS
    RMS -->|payment initiation, deposit hold, refund requests| PG

    ESign -->|signed documents, signature webhooks| RMS
    RMS -->|agreement documents for signing| ESign
```

---

## Level 1 DFD – Key Subsystems

```mermaid
graph TD
    subgraph Inputs
        OwnIn((Owner))
        CustIn((Customer))
        StaffIn((Staff))
        PGIn((Payment GW))
        ESignIn((E-Sign))
    end

    subgraph "Asset & Listing"
        DS1[(Asset Store)]
        DS2[(Availability Store)]
        ProcAsset[Process: Manage Assets & Listings]
    end

    subgraph "Booking & Pricing"
        DS3[(Booking Store)]
        DS4[(Pricing Rules)]
        ProcBook[Process: Handle Bookings]
        ProcPrice[Process: Calculate Price]
    end

    subgraph "Agreement Management"
        DS5[(Agreement Store)]
        DS6[(Document Store)]
        ProcAgreement[Process: Manage Agreements]
    end

    subgraph "Payment & Invoice"
        DS7[(Invoice Store)]
        DS8[(Payment Store)]
        DS9[(Deposit Store)]
        ProcPay[Process: Process Payments]
    end

    subgraph "Condition Assessments"
        DS10[(Assessment Store)]
        ProcAssess[Process: Conduct Assessments]
    end

    subgraph "Maintenance"
        DS11[(Maintenance Store)]
        ProcMaint[Process: Handle Maintenance]
    end

    subgraph "Notification Engine"
        ProcNotify[Process: Send Notifications]
    end

    OwnIn -->|asset and pricing data| ProcAsset
    ProcAsset --> DS1
    ProcAsset --> DS2
    DS4 --> ProcPrice

    CustIn -->|search, booking request| ProcBook
    DS1 --> ProcBook
    DS2 --> ProcBook
    ProcBook --> ProcPrice
    ProcPrice --> DS4
    ProcBook --> DS3
    PGIn -->|deposit webhook| ProcBook

    OwnIn -->|approve/decline booking| ProcBook
    ProcBook -->|confirmed booking| ProcAgreement
    OwnIn -->|agreement terms| ProcAgreement
    ESignIn -->|signed document| ProcAgreement
    ProcAgreement --> DS5
    ProcAgreement --> DS6

    DS3 -->|active booking triggers invoice| ProcPay
    CustIn -->|payment| ProcPay
    PGIn -->|payment webhook| ProcPay
    ProcPay --> DS7
    ProcPay --> DS8
    ProcPay --> DS9

    StaffIn -->|assessment data| ProcAssess
    DS3 --> ProcAssess
    ProcAssess --> DS10

    OwnIn -->|maintenance request, assignments| ProcMaint
    StaffIn -->|task updates| ProcMaint
    ProcMaint --> DS11

    ProcBook --> ProcNotify
    ProcAgreement --> ProcNotify
    ProcPay --> ProcNotify
    ProcAssess --> ProcNotify
    ProcMaint --> ProcNotify
```

---

## Level 2 DFD – Booking and Pricing Process

```mermaid
graph TD
    AssetStore[(Asset Store)]
    AvailStore[(Availability Store)]
    PricingStore[(Pricing Rules)]
    BookingStore[(Booking Store)]
    DepositStore[(Deposit Store)]

    Customer((Customer)) -->|search criteria| A[Search Process]
    AssetStore -->|published assets| A
    AvailStore -->|availability windows| A
    A -->|matching listings| Customer

    Customer -->|selected asset and period| B[Price Calculation Process]
    PricingStore -->|pricing rules| B
    B -->|pricing breakdown| Customer

    Customer -->|booking request| C[Booking Creation Process]
    AvailStore -->|lock availability| C
    C -->|create booking PENDING| BookingStore
    C -->|initiate deposit| D[Deposit Collection Process]
    D -->|deposit confirmed| DepositStore
    C -->|notify owner| E[Notification Process]

    Owner((Owner)) -->|approve/decline| F[Booking Confirmation Process]
    BookingStore --> F
    F -->|update status CONFIRMED| BookingStore
    F -->|trigger agreement| G[Agreement Generation Process]
    F --> E
```

---

## Level 2 DFD – Return and Settlement Process

```mermaid
graph TD
    BookingStore[(Booking Store)]
    AssessStore[(Assessment Store)]
    InvoiceStore[(Invoice Store)]
    DepositStore[(Deposit Store)]
    PaymentStore[(Payment Store)]

    Customer((Customer)) -->|initiate return| A[Return Process]
    A -->|log actual return time| BookingStore
    A -->|trigger post-rental assessment task| B[Assessment Process]

    Staff((Staff)) -->|post-rental checklist and photos| B
    AssessStore -->|pre-rental data| B
    B -->|post-rental assessment| AssessStore
    B -->|comparison report| C[Damage Detection Process]

    C --> D{Damage or Late?}
    D -- No --> E[Full Deposit Release Process]
    E --> DepositStore
    E --> PaymentStore

    D -- Yes --> F[Additional Charge Process]
    Owner((Owner)) -->|itemise charges| F
    F -->|charge records| InvoiceStore
    F -->|notify customer| G[Notification Process]

    Customer -->|pay final invoice| H[Payment Process]
    InvoiceStore --> H
    H -->|record payment| PaymentStore
    H -->|partial deposit deduction| DepositStore
    H --> G

    E --> I[Booking Closure Process]
    H --> I
    I -->|set CLOSED| BookingStore
    I -->|unblock calendar| J[(Availability Store)]
    I --> G
```
