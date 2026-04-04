# Activity Diagram

## Overview

This document presents UML activity diagrams for the core business processes in the Order Management and Delivery System: order lifecycle, fulfillment, delivery, and returns.

## 1. Order Lifecycle — Browse to Delivery

```mermaid
flowchart TD
    Start([Start]) --> Browse[Browse / Search Products]
    Browse --> AddCart[Add Items to Cart]
    AddCart --> ViewCart{View Cart}
    ViewCart -->|Continue Shopping| Browse
    ViewCart -->|Proceed to Checkout| ValidateCart[Validate Cart Items Availability]
    ValidateCart -->|Items Unavailable| RemoveUnavail[Remove Unavailable Items and Notify Customer]
    RemoveUnavail --> ViewCart
    ValidateCart -->|All Available| SelectAddr[Select Delivery Address]
    SelectAddr --> ValidateZone{Address in Active Delivery Zone?}
    ValidateZone -->|No| PromptAddr[Prompt for Serviceable Address]
    PromptAddr --> SelectAddr
    ValidateZone -->|Yes| CalcTotal[Calculate Total: Items + Tax + Shipping - Discount]
    CalcTotal --> ApplyCoupon{Apply Coupon?}
    ApplyCoupon -->|Yes| ValidateCoupon[Validate Coupon Rules]
    ValidateCoupon -->|Invalid| ShowCouponErr[Show Coupon Error]
    ShowCouponErr --> CalcTotal
    ValidateCoupon -->|Valid| RecalcTotal[Recalculate Total with Discount]
    RecalcTotal --> ReviewOrder[Review Order Summary]
    ApplyCoupon -->|No| ReviewOrder
    ReviewOrder --> SelectPayment[Select Payment Method]
    SelectPayment --> ReserveInventory[Reserve Inventory with 15-min TTL]
    ReserveInventory -->|Reservation Failed| ShowStockErr[Show Stock Error]
    ShowStockErr --> ViewCart
    ReserveInventory -->|Reserved| InitPayment[Initiate Payment via Gateway]
    InitPayment -->|Payment Failed| ReleaseRes[Release Reservation]
    ReleaseRes --> ShowPayErr[Show Payment Error]
    ShowPayErr --> SelectPayment
    InitPayment -->|Payment Success| ConfirmOrder[Create Order — Status: Confirmed]
    ConfirmOrder --> EmitConfirmed[Emit order.confirmed.v1]
    EmitConfirmed --> NotifyCustomer[Send Confirmation Notification]
    NotifyCustomer --> EndOrder([Order Confirmed])
```

## 2. Fulfillment Workflow — Confirmed to ReadyForDispatch

```mermaid
flowchart TD
    Start([order.confirmed.v1 Received]) --> CreateTask[Create Fulfillment Task]
    CreateTask --> AssignWarehouse[Assign to Warehouse with Stock]
    AssignWarehouse --> StaffView[Staff Views Pick List on Dashboard]
    StaffView --> StartPick[Staff Starts Picking]
    StartPick --> ScanItem[Scan Item Barcode]
    ScanItem --> ValidateScan{Scan Matches Expected SKU?}
    ValidateScan -->|No| FlagMismatch[Flag for Supervisor Review]
    FlagMismatch --> ScanItem
    ValidateScan -->|Yes| MoreItems{More Items to Pick?}
    MoreItems -->|Yes| ScanItem
    MoreItems -->|No| MarkPicked[Mark Task as Picked]
    MarkPicked --> PackOrder[Pack Order — Record Dimensions and Weight]
    PackOrder --> GenSlip[Generate Packing Slip]
    GenSlip --> ConfirmPack[Staff Confirms Pack Complete]
    ConfirmPack --> TransitionReady[Order Status → ReadyForDispatch]
    TransitionReady --> GenManifest[Batch into Delivery Manifest by Zone]
    GenManifest --> EmitReady[Emit order.ready_for_dispatch.v1]
    EmitReady --> EndFulfill([Ready for Delivery Handoff])
```

## 3. Delivery Workflow — ReadyForDispatch to Delivered

```mermaid
flowchart TD
    Start([order.ready_for_dispatch.v1]) --> AssignStaff[Assign to Internal Delivery Staff]
    AssignStaff --> NotifyStaff[Push Notification to Staff]
    NotifyStaff --> ViewAssign[Staff Views Assigned Deliveries]
    ViewAssign --> PickupPkg[Staff Picks Up Package from Warehouse]
    PickupPkg --> UpdatePickedUp[Update Status → PickedUp]
    UpdatePickedUp --> StartRun[Staff Starts Delivery Run]
    StartRun --> UpdateOFD[Update Status → OutForDelivery]
    UpdateOFD --> NotifyCust[Notify Customer — Out for Delivery]
    NotifyCust --> AtDest[Staff Arrives at Delivery Location]
    AtDest --> CustAvail{Customer Available?}
    CustAvail -->|No| RecordFail[Record Failed Delivery with Reason]
    RecordFail --> AttemptCheck{Attempt Count < 3?}
    AttemptCheck -->|Yes| Reschedule[Reschedule for Next Window]
    Reschedule --> NotifyReschedule[Notify Customer of Reschedule]
    NotifyReschedule --> EndFail([Delivery Rescheduled])
    AttemptCheck -->|No| ReturnWH[Return to Warehouse]
    ReturnWH --> StatusRTW[Status → ReturnedToWarehouse]
    StatusRTW --> RestoreStock[Restore Stock]
    RestoreStock --> EndReturn([Order Returned to Stock])
    CustAvail -->|Yes| CaptureSig[Capture Recipient Signature]
    CaptureSig --> CapturePhoto[Capture Delivery Photo]
    CapturePhoto --> UploadPOD[Upload POD to S3]
    UploadPOD --> StatusDelivered[Status → Delivered]
    StatusDelivered --> EmitDelivered[Emit order.delivered.v1]
    EmitDelivered --> NotifyDeliver[Notify Customer — Delivered with POD Link]
    NotifyDeliver --> EndDelivered([Delivery Complete])
```

## 4. Returns Workflow — Return Request to Refund

```mermaid
flowchart TD
    Start([Customer Initiates Return]) --> ValidateWindow{Within Return Window?}
    ValidateWindow -->|No| ShowExpired[Show Return Period Expired]
    ShowExpired --> EndIneligible([Return Ineligible])
    ValidateWindow -->|Yes| ValidateCat{Category Allows Returns?}
    ValidateCat -->|No| ShowExcluded[Show Category Excluded]
    ShowExcluded --> EndIneligible
    ValidateCat -->|Yes| SelectReason[Customer Selects Return Reason]
    SelectReason --> UploadEvidence[Customer Optionally Uploads Photo Evidence]
    UploadEvidence --> CreateReturn[Create Return Request]
    CreateReturn --> AssignPickup[Assign Return Pickup to Delivery Staff]
    AssignPickup --> NotifyPickup[Notify Staff of Return Pickup]
    NotifyPickup --> StaffCollects[Staff Collects Item from Customer]
    StaffCollects --> UpdateRPickedUp[Return Status → PickedUp]
    UpdateRPickedUp --> WarehouseReceive[Warehouse Receives Item]
    WarehouseReceive --> InspectItem[Warehouse Staff Inspects Item]
    InspectItem --> InspectResult{Inspection Result?}
    InspectResult -->|Accept| RestoreStock[Return Item to Stock]
    RestoreStock --> InitRefund[Initiate Refund to Original Payment Method]
    InitRefund --> NotifyRefund[Notify Customer — Refund Processed]
    NotifyRefund --> EndAccepted([Return Accepted and Refunded])
    InspectResult -->|Reject| NotifyReject[Notify Customer with Rejection Reason]
    NotifyReject --> EndRejected([Return Rejected])
    InspectResult -->|Partial Accept| PartialRefund[Initiate Partial Refund]
    PartialRefund --> NotifyPartial[Notify Customer — Partial Refund]
    NotifyPartial --> EndPartial([Partial Return Processed])
```
