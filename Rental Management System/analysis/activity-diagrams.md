# Activity Diagrams

## Overview
Activity diagrams for key business processes in the rental management system. These flows apply regardless of the asset type being rented (car, flat, gear, equipment, etc.).

---

## Asset Booking Flow

```mermaid
flowchart TD
    A([Customer Starts Search]) --> B[Enter Category and Rental Period]
    B --> C[System Displays Available Listings]
    C --> D[Customer Selects an Asset]
    D --> E[System Shows Pricing Breakdown]
    E --> F{Customer Confirms?}
    F -- No --> C
    F -- Yes --> G[Customer Pays Security Deposit]
    G --> H{Payment Successful?}
    H -- No --> I[Customer Retries Payment]
    I --> G
    H -- Yes --> J[Booking Created]
    J --> K{Instant Booking Enabled?}
    K -- Yes --> L[Status = CONFIRMED]
    L --> M[Both Parties Notified]
    M --> N([End - Asset Reserved])
    K -- No --> O[Status = PENDING]
    O --> P[Owner Notified]
    P --> Q{Owner Reviews}
    Q -- Declined --> R[Deposit Refunded]
    R --> S[Customer Notified of Decline]
    S --> N
    Q -- Approved --> L
```

---

## Rental Lifecycle Flow

```mermaid
flowchart TD
    A([Booking Confirmed]) --> B[Generate Rental Agreement]
    B --> C[Send Agreement to Customer for Signature]
    C --> D{Customer Signs?}
    D -- No --> E[Reminder Sent]
    E --> D
    D -- Yes --> F[Owner Countersigns]
    F --> G[Signed PDF Stored]
    G --> H[Pre-Rental Condition Assessment]
    H --> I[Customer Countersigns Assessment]
    I --> J[Asset Handed Over]
    J --> K([Rental Period Active])
    K --> L[Customer Uses Asset]
    L --> M{Rental Period Ends or Customer Returns Early?}
    M -- Yes --> N[Customer Initiates Return]
    N --> O[Staff Completes Post-Rental Assessment]
    O --> P{Damage or Late Return?}
    P -- No --> Q[Full Deposit Refund]
    P -- Yes --> R[Owner Calculates Additional Charges]
    R --> S[Customer Notified]
    S --> T{Customer Pays Additional Charges?}
    T -- Yes --> U[Final Invoice Settled]
    T -- Disputed --> V[Admin Mediates]
    V --> U
    Q --> U
    U --> W[Asset Status = AVAILABLE]
    W --> X([Rental Closed])
```

---

## Pricing Calculation Flow

```mermaid
flowchart TD
    A([Customer Selects Rental Period]) --> B[System Retrieves Asset Pricing Rules]
    B --> C{Multiple Rate Tiers Available?}
    C -- Yes --> D[Calculate Cost Per Tier: hourly, daily, weekly, monthly]
    D --> E[Select Optimal Tier Combination for Duration]
    C -- No --> F[Apply Single Rate for Duration]
    E --> G{Period Overlaps Peak Window?}
    F --> G
    G -- Yes --> H[Apply Peak Pricing Surcharge]
    H --> I[Apply Applicable Discount if Any]
    G -- No --> I
    I --> J[Calculate Tax per Jurisdiction]
    J --> K[Add Security Deposit Amount]
    K --> L[Generate Price Breakdown]
    L --> M[Display to Customer]
    M --> N([End])
```

---

## Condition Assessment Flow

```mermaid
flowchart TD
    A([Assessment Task Triggered]) --> B{Assessment Type?}
    B -- Pre-Rental --> C[Staff Opens Pre-Rental Checklist]
    B -- Post-Rental --> D[Staff Opens Post-Rental Checklist]

    C --> E[Complete Category-Specific Checklist Items]
    E --> F[Capture Photos for Each Item]
    F --> G[Submit Pre-Rental Assessment]
    G --> H[Send Report to Customer]
    H --> I{Customer Countersigns?}
    I -- Yes --> J[Handover Complete - Rental Begins]
    I -- Dispute --> K[Customer Adds Dispute Note]
    K --> L[Owner Notified for Review]
    L --> J

    D --> M[Complete Post-Rental Checklist]
    M --> N[Capture Photos for Each Item]
    N --> O[System Compares Pre vs Post Condition]
    O --> P{Discrepancies Found?}
    P -- No --> Q[Report Generated - No Damage]
    Q --> R[Full Deposit Release Initiated]
    P -- Yes --> S[Discrepancies Highlighted in Report]
    S --> T[Owner Prompted to Add Damage Charges]
    T --> U[Customer Notified of Charges]
    U --> V([End - Awaiting Settlement])
    R --> V
```

---

## Maintenance Request Flow

```mermaid
flowchart TD
    A([Owner Logs Maintenance Request]) --> B[System Creates Request - OPEN]
    B --> C[Asset Availability Calendar Blocked]
    C --> D[Owner Assigns to Staff Member]
    D --> E[Staff Notified]
    E --> F{Staff Accepts?}
    F -- No --> G[Staff Declines with Reason]
    G --> D
    F -- Yes --> H[Status = ASSIGNED]
    H --> I[Staff Works on Asset]
    I --> J[Status = IN_PROGRESS]
    J --> K[Staff Adds Notes, Photos, Materials]
    K --> L[Staff Marks COMPLETED]
    L --> M[Owner Reviews Completion]
    M --> N{Owner Approves?}
    N -- No --> O[Owner Reopens with Reason]
    O --> J
    N -- Yes --> P[Status = CLOSED]
    P --> Q[Owner Logs Maintenance Cost]
    Q --> R[Asset Calendar Unblocked]
    R --> S([Asset Available for Bookings])
```

---

## Cancellation and Refund Flow

```mermaid
flowchart TD
    A([Cancellation Requested]) --> B{Who Cancels?}
    B -- Customer --> C[Customer Submits Cancellation]
    B -- Owner --> D[Owner Cancels with Reason]

    C --> E[System Checks Cancellation Policy]
    D --> E

    E --> F{Time Before Rental Start?}
    F -- More than Free Cancellation Window --> G[Full Deposit Refund]
    F -- Within Partial Refund Window --> H[Partial Refund per Policy]
    F -- Within No Refund Window --> I[No Refund]

    G --> J[Refund Processed to Customer]
    H --> J
    I --> K[No Refund Issued]

    J --> L[Asset Calendar Unblocked]
    K --> L
    L --> M[Both Parties Notified]
    M --> N([Booking Cancelled])
```
