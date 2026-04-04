# Use Case Diagram

## Overview

This document presents the UML use case diagram for the Order Management and Delivery System, identifying all actors and their interactions with the platform.

## Actors

| Actor | Type | Description |
|---|---|---|
| Customer | Primary | End user who browses, orders, tracks, and manages returns |
| Warehouse Staff | Primary | Staff responsible for picking, packing, and inspecting returns |
| Delivery Staff | Primary | Internal staff responsible for delivering orders and collecting returns |
| Operations Manager | Primary | Oversees fulfillment, delivery assignments, and performance |
| Admin | Primary | Manages platform configuration, catalog, staff, and analytics |
| Finance | Primary | Handles payment reconciliation and manual refunds |
| Payment Gateway | External | Third-party payment processing service (Stripe, Khalti) |
| Notification Service | External | AWS SES/SNS/Pinpoint for email, SMS, push delivery |
| System Timer | External | Scheduled triggers for reservation expiry, report generation, cleanup |

## 1. Complete System Use Case Diagram

```mermaid
graph LR
    subgraph Actors
        C[Customer]
        WS[Warehouse Staff]
        DS[Delivery Staff]
        OM[Operations Manager]
        AD[Admin]
        FN[Finance]
        PG[Payment Gateway]
        NS[Notification Service]
        ST[System Timer]
    end

    subgraph Customer_Management["Customer Management"]
        UC01[UC-01: Register Account]
        UC02[UC-02: Manage Profile]
        UC03[UC-03: Manage Addresses]
    end

    subgraph Product_Catalog["Product Catalog"]
        UC04[UC-04: Browse Products]
        UC05[UC-05: Search Products]
        UC06[UC-06: Manage Catalog]
    end

    subgraph Cart_Checkout["Cart and Checkout"]
        UC07[UC-07: Manage Cart]
        UC08[UC-08: Apply Coupon]
        UC09[UC-09: Checkout]
    end

    subgraph Order_Management["Order Management"]
        UC10[UC-10: Create Order]
        UC11[UC-11: Track Order]
        UC12[UC-12: Cancel Order]
        UC13[UC-13: Modify Order]
    end

    subgraph Payment["Payment"]
        UC14[UC-14: Process Payment]
        UC15[UC-15: Process Refund]
        UC16[UC-16: Reconcile Payments]
    end

    subgraph Fulfillment["Fulfillment"]
        UC17[UC-17: View Pick List]
        UC18[UC-18: Verify Picks]
        UC19[UC-19: Pack Order]
        UC20[UC-20: Generate Manifest]
    end

    subgraph Delivery["Delivery"]
        UC21[UC-21: View Assignments]
        UC22[UC-22: Update Delivery Status]
        UC23[UC-23: Capture POD]
        UC24[UC-24: Record Failed Delivery]
        UC25[UC-25: Manage Delivery Zones]
    end

    subgraph Returns["Returns"]
        UC26[UC-26: Initiate Return]
        UC27[UC-27: Collect Return Pickup]
        UC28[UC-28: Inspect Return]
    end

    subgraph Admin_Ops["Administration"]
        UC29[UC-29: Manage Staff]
        UC30[UC-30: Configure Settings]
        UC31[UC-31: View Analytics]
        UC32[UC-32: Manage Templates]
        UC33[UC-33: View Audit Logs]
    end

    C --> UC01
    C --> UC02
    C --> UC03
    C --> UC04
    C --> UC05
    C --> UC07
    C --> UC08
    C --> UC09
    C --> UC11
    C --> UC12
    C --> UC13
    C --> UC26

    WS --> UC17
    WS --> UC18
    WS --> UC19
    WS --> UC20
    WS --> UC28

    DS --> UC21
    DS --> UC22
    DS --> UC23
    DS --> UC24
    DS --> UC27

    OM --> UC20
    OM --> UC21
    OM --> UC25
    OM --> UC31

    AD --> UC06
    AD --> UC29
    AD --> UC30
    AD --> UC31
    AD --> UC32
    AD --> UC33

    FN --> UC15
    FN --> UC16

    UC09 --> PG
    UC14 --> PG
    UC15 --> PG

    UC10 --> NS
    UC22 --> NS
    UC24 --> NS

    ST --> UC07
    ST --> UC16
```

## 2. Customer Use Cases (Detailed)

```mermaid
graph LR
    C([Customer])

    subgraph Account_Management["Account Management"]
        A1[Register Account]
        A2[Login / Logout]
        A3[Manage Profile]
        A4[Reset Password]
        A5[Manage Addresses]
        A6[Update Notification Preferences]
    end

    subgraph Product_Discovery["Product Discovery"]
        P1[Browse Categories]
        P2[Search Products]
        P3[View Product Details]
        P4[Filter and Sort Results]
    end

    subgraph Cart_Checkout["Cart and Checkout"]
        CC1[Add to Cart]
        CC2[Update Cart]
        CC3[Apply Coupon]
        CC4[Select Address]
        CC5[Select Payment Method]
        CC6[Complete Checkout]
    end

    subgraph Order_Management["Order Management"]
        O1[View Order History]
        O2[Track Order Status]
        O3[Cancel Order]
        O4[Modify Delivery Address]
        O5[View Order Milestones]
        O6[View Proof of Delivery]
    end

    subgraph Returns["Returns"]
        R1[Initiate Return Request]
        R2[Track Return Status]
        R3[View Refund Status]
    end

    C --> A1
    C --> A2
    C --> A3
    C --> A4
    C --> A5
    C --> A6

    C --> P1
    C --> P2
    C --> P3
    C --> P4

    C --> CC1
    C --> CC2
    C --> CC3
    C --> CC4
    C --> CC5
    C --> CC6

    C --> O1
    C --> O2
    C --> O3
    C --> O4
    C --> O5
    C --> O6

    C --> R1
    C --> R2
    C --> R3
```

## 3. Warehouse Staff Use Cases (Detailed)

```mermaid
graph LR
    WS([Warehouse Staff])

    subgraph Fulfillment["Fulfillment"]
        F1[View Pick List]
        F2[Start Fulfillment Task]
        F3[Scan Item Barcode]
        F4[Flag Scan Mismatch]
        F5[Mark Order Picked]
        F6[Pack Order]
        F7[Record Package Dimensions]
        F8[Generate Packing Slip]
        F9[Generate Delivery Manifest]
    end

    subgraph Returns["Returns"]
        R1[View Return Inspection Queue]
        R2[Inspect Returned Items]
        R3[Accept Return]
        R4[Reject Return]
        R5[Partial Accept Return]
        R6[Update Inventory after Return]
    end

    WS --> F1
    WS --> F2
    WS --> F3
    WS --> F4
    WS --> F5
    WS --> F6
    WS --> F7
    WS --> F8
    WS --> F9

    WS --> R1
    WS --> R2
    WS --> R3
    WS --> R4
    WS --> R5
    WS --> R6
```

## 4. Delivery Staff Use Cases (Detailed)

```mermaid
graph LR
    DS([Delivery Staff])

    subgraph Delivery_Operations["Delivery Operations"]
        D1[View Daily Assignments]
        D2[Pick Up Package from Warehouse]
        D3[Update Status to Out for Delivery]
        D4[Navigate to Delivery Address]
        D5[Update Delivery Status]
        D6[Capture Electronic Signature]
        D7[Capture Delivery Photo]
        D8[Upload Proof of Delivery]
    end

    subgraph Failed_Delivery["Failed Delivery"]
        FD1[Record Failed Delivery Attempt]
        FD2[Select Failure Reason]
        FD3[Note Rescheduling]
    end

    subgraph Return_Pickups["Return Pickups"]
        RP1[View Return Pickup Assignments]
        RP2[Confirm Return Collection]
        RP3[Record Item Condition]
        RP4[Generate Return Manifest]
    end

    subgraph Offline_Operations["Offline Operations"]
        OF1[Queue POD for Sync]
        OF2[Sync POD When Online]
    end

    DS --> D1
    DS --> D2
    DS --> D3
    DS --> D4
    DS --> D5
    DS --> D6
    DS --> D7
    DS --> D8

    DS --> FD1
    DS --> FD2
    DS --> FD3

    DS --> RP1
    DS --> RP2
    DS --> RP3
    DS --> RP4

    DS --> OF1
    DS --> OF2
```

## 5. Operations Manager Use Cases (Detailed)

```mermaid
graph LR
    OM([Operations Manager])

    subgraph Fulfillment_Oversight["Fulfillment Oversight"]
        FO1[View Fulfillment Dashboard]
        FO2[Monitor SLA Status]
        FO3[View Manifest Summary]
    end

    subgraph Delivery_Management["Delivery Management"]
        DM1[View Delivery Assignments]
        DM2[Reassign Delivery Staff]
        DM3[View Delivery Map Overview]
    end

    subgraph Zone_Management["Zone Management"]
        ZM1[Create Delivery Zone]
        ZM2[Edit Delivery Zone]
        ZM3[Deactivate Delivery Zone]
        ZM4[Set Zone SLA and Fees]
    end

    subgraph Performance["Performance"]
        PR1[View Delivery Performance Reports]
        PR2[View Staff Performance Rankings]
        PR3[Export Reports]
    end

    OM --> FO1
    OM --> FO2
    OM --> FO3

    OM --> DM1
    OM --> DM2
    OM --> DM3

    OM --> ZM1
    OM --> ZM2
    OM --> ZM3
    OM --> ZM4

    OM --> PR1
    OM --> PR2
    OM --> PR3
```

## 6. Admin and Finance Use Cases (Detailed)

```mermaid
graph LR
    AD([Admin])
    FN([Finance])

    subgraph Catalog["Catalog"]
        CA1[Manage Products]
        CA2[Manage Categories]
        CA3[Bulk Import Products]
        CA4[Manage Coupons]
    end

    subgraph Staff_Roles["Staff and Roles"]
        SR1[Onboard Staff]
        SR2[Assign Staff to Zone / Warehouse]
        SR3[Deactivate Staff]
        SR4[Manage Roles]
    end

    subgraph Configuration["Configuration"]
        CF1[Update Platform Config]
        CF2[View Config History]
        CF3[Roll Back Config]
    end

    subgraph Analytics["Analytics"]
        AN1[View Sales Dashboard]
        AN2[View Inventory Reports]
        AN3[Generate Report Export]
    end

    subgraph Audit["Audit"]
        AU1[View Audit Logs]
        AU2[Search Audit Events]
    end

    subgraph Finance_Only["Finance Only"]
        FO1[View Payment Reconciliation]
        FO2[Flag Discrepancy]
        FO3[Process Manual Refund]
    end

    subgraph Notifications["Notifications"]
        NT1[Manage Notification Templates]
        NT2[Preview Template]
        NT3[Publish Template]
    end

    AD --> CA1
    AD --> CA2
    AD --> CA3
    AD --> CA4

    AD --> SR1
    AD --> SR2
    AD --> SR3
    AD --> SR4

    AD --> CF1
    AD --> CF2
    AD --> CF3

    AD --> AN1
    AD --> AN2
    AD --> AN3

    AD --> AU1
    AD --> AU2

    AD --> NT1
    AD --> NT2
    AD --> NT3

    FN --> FO1
    FN --> FO2
    FN --> FO3
```

## 7. Use Case Relationships

```mermaid
graph TB
    subgraph Include_Relationships["«include» Relationships"]
        Checkout[Checkout]
        ValidateCart[Validate Cart Availability]
        ReserveInventory[Reserve Inventory]
        CalcTaxes[Calculate Taxes and Fees]
        CompleteCheckout[Complete Checkout]
        ProcessPayment[Process Payment]
        RecordTx[Record Payment Transaction]
        CreateAssignment[Create Delivery Assignment]
        ValidateZone[Validate Delivery Zone]
        CapturePOD[Capture POD]
        UploadS3[Upload to S3]
        InspectReturn[Inspect Return]
        CalcRefund[Calculate Refund Amount]
    end

    subgraph Extend_Relationships["«extend» Relationships"]
        BrowseProducts[Browse Products]
        ApplyPriceFilters[Apply Price Filters]
        SortResults[Sort Results]
        ViewOrder[View Order]
        ViewMilestones[View Milestones]
        ViewPOD[View POD]
        RecordFailed[Record Failed Delivery]
        RescheduleDelivery[Reschedule Delivery]
        TriggerReturn[Trigger Return to Warehouse]
        PaymentCapture[Payment Capture]
        GatewayFailover[Gateway Failover]
    end

    Checkout -->|includes| ValidateCart
    Checkout -->|includes| ReserveInventory
    Checkout -->|includes| CalcTaxes
    CompleteCheckout -->|includes| ProcessPayment
    ProcessPayment -->|includes| RecordTx
    CreateAssignment -->|includes| ValidateZone
    CapturePOD -->|includes| UploadS3
    InspectReturn -->|includes| CalcRefund

    BrowseProducts -.->|extends| ApplyPriceFilters
    BrowseProducts -.->|extends| SortResults
    ViewOrder -.->|extends| ViewMilestones
    ViewOrder -.->|extends| ViewPOD
    RecordFailed -.->|extends| RescheduleDelivery
    RecordFailed -.->|extends| TriggerReturn
    PaymentCapture -.->|extends| GatewayFailover
```

## Use Case Summary Table

| ID | Use Case | Primary Actor | Related Requirements |
|---|---|---|---|
| UC-01 | Register Account | Customer | FR-CM-001, FR-CM-004 |
| UC-02 | Manage Profile | Customer | FR-CM-002 |
| UC-03 | Manage Addresses | Customer | FR-CM-003 |
| UC-04 | Browse Products | Customer | FR-PC-001, FR-PC-002 |
| UC-05 | Search Products | Customer | FR-PC-004 |
| UC-06 | Manage Catalog | Admin | FR-PC-001, FR-PC-002, FR-PC-003 |
| UC-07 | Manage Cart | Customer | FR-SC-001 |
| UC-08 | Apply Coupon | Customer | FR-SC-003 |
| UC-09 | Checkout | Customer | FR-SC-002 |
| UC-10 | Create Order | System | FR-OM-001 |
| UC-11 | Track Order | Customer | FR-OM-002 |
| UC-12 | Cancel Order | Customer | FR-OM-003 |
| UC-13 | Modify Order | Customer | FR-OM-004 |
| UC-14 | Process Payment | System | FR-PM-001, FR-PM-002 |
| UC-15 | Process Refund | Finance | FR-PM-003 |
| UC-16 | Reconcile Payments | Finance | FR-PM-004 |
| UC-17 | View Pick List | Warehouse Staff | FR-FP-001 |
| UC-18 | Verify Picks | Warehouse Staff | FR-FP-002 |
| UC-19 | Pack Order | Warehouse Staff | FR-FP-002 |
| UC-20 | Generate Manifest | Warehouse Staff / Ops Mgr | FR-FP-003 |
| UC-21 | View Assignments | Delivery Staff | FR-DM-001 |
| UC-22 | Update Delivery Status | Delivery Staff | FR-DM-002 |
| UC-23 | Capture POD | Delivery Staff | FR-DM-003 |
| UC-24 | Record Failed Delivery | Delivery Staff | FR-DM-004 |
| UC-25 | Manage Delivery Zones | Operations Manager | FR-DM-005 |
| UC-26 | Initiate Return | Customer | FR-RR-001 |
| UC-27 | Collect Return Pickup | Delivery Staff | FR-RR-002 |
| UC-28 | Inspect Return | Warehouse Staff | FR-RR-003 |
| UC-29 | Manage Staff | Admin | FR-AM-003 |
| UC-30 | Configure Settings | Admin | FR-AM-002 |
| UC-31 | View Analytics | Admin / Ops Mgr | FR-AR-001, FR-AR-002 |
| UC-32 | Manage Templates | Admin | FR-NM-004 |
| UC-33 | View Audit Logs | Admin | FR-AM-001 |
