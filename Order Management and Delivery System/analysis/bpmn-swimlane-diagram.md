# BPMN / Swimlane Diagram

## Overview

This document presents cross-functional swimlane diagrams illustrating handoffs between Customer, Warehouse Staff, Delivery Staff, Operations Manager, Admin, and System for the core business processes.

## 1. Order-to-Delivery Swimlane

```mermaid
flowchart TB
    subgraph Customer["👤 Customer"]
        C1[Browse and Search Products]
        C2[Add Items to Cart]
        C3[Proceed to Checkout]
        C4[Select Address and Payment]
        C5[Confirm Order]
        C6[Receive Confirmation]
        C7[Track Order Status]
        C8[Receive Delivery Notification]
        C9[View POD]
    end

    subgraph System["⚙️ System"]
        S1[Validate Cart Availability]
        S2[Calculate Total with Tax and Shipping]
        S3[Reserve Inventory]
        S4[Process Payment via Gateway]
        S5[Create Order — Confirmed]
        S6[Emit order.confirmed.v1]
        S7[Send Confirmation Notification]
        S8[Create Fulfillment Task]
        S9[Generate Manifest by Zone]
        S10[Assign Delivery Staff]
        S11[Emit order.delivered.v1]
        S12[Send Delivery Notification with POD]
    end

    subgraph Warehouse["👷 Warehouse Staff"]
        W1[View Pick List]
        W2[Pick Items with Barcode Scan]
        W3[Pack Order]
        W4[Generate Packing Slip]
        W5[Handoff to Delivery Queue]
    end

    subgraph Delivery["🚚 Delivery Staff"]
        D1[View Assigned Deliveries]
        D2[Pick Up Package]
        D3[Start Delivery Run]
        D4[Arrive at Customer Location]
        D5[Capture Signature and Photo]
        D6[Upload POD]
    end

    C1 --> C2 --> C3 --> S1
    S1 --> S2 --> C4 --> S3
    S3 --> S4 --> C5 --> S5
    S5 --> S6 --> S7 --> C6
    S6 --> S8 --> W1
    W1 --> W2 --> W3 --> W4 --> W5
    W5 --> S9 --> S10 --> D1
    D1 --> D2 --> D3 --> D4 --> D5 --> D6
    D6 --> S11 --> S12 --> C8
    C7 -.->|"Polls status"| S5
    C8 --> C9
```

## 2. Failed Delivery Swimlane

```mermaid
flowchart TB
    subgraph Delivery["🚚 Delivery Staff"]
        D1[Arrive at Customer Location]
        D2[Customer Unavailable]
        D3[Record Failure Reason]
    end

    subgraph System["⚙️ System"]
        S1[Log Failed Attempt]
        S2{Attempt Count < 3?}
        S3[Schedule Next Delivery Window]
        S4[Send Reschedule Notification]
        S5[Transition to ReturnedToWarehouse]
        S6[Send Return Notification]
        S7[Restore Inventory]
    end

    subgraph Customer["👤 Customer"]
        C1[Receive Reschedule Notification]
        C2[Receive Return Notification]
    end

    subgraph Warehouse["👷 Warehouse Staff"]
        W1[Receive Returned Package]
        W2[Process Return to Stock]
    end

    D1 --> D2 --> D3 --> S1
    S1 --> S2
    S2 -->|Yes| S3 --> S4 --> C1
    S2 -->|No| S5 --> S6 --> C2
    S5 --> S7
    S7 --> W1 --> W2
```

## 3. Returns Processing Swimlane

```mermaid
flowchart TB
    subgraph Customer["👤 Customer"]
        C1[Request Return for Delivered Order]
        C2[Select Reason and Upload Evidence]
        C3[Receive Return Confirmation]
        C4[Hand Over Item to Staff]
        C5[Receive Refund Notification]
    end

    subgraph System["⚙️ System"]
        S1[Validate Return Eligibility]
        S2[Create Return Request]
        S3[Send Return Confirmation]
        S4[Assign Return Pickup]
        S5[Send Pickup Assignment]
        S6[Update Return Status]
        S7[Process Inspection Result]
        S8[Initiate Refund]
        S9[Update Inventory]
        S10[Send Refund Notification]
    end

    subgraph Delivery["🚚 Delivery Staff"]
        D1[Receive Pickup Assignment]
        D2[Collect Item from Customer]
        D3[Deliver to Warehouse]
    end

    subgraph Warehouse["👷 Warehouse Staff"]
        W1[Receive Returned Item]
        W2[Inspect Item Condition]
        W3[Record Inspection Result]
    end

    C1 --> C2 --> S1
    S1 --> S2 --> S3 --> C3
    S2 --> S4 --> S5 --> D1
    D1 --> D2 --> C4
    D2 --> D3 --> S6
    S6 --> W1 --> W2 --> W3 --> S7
    S7 -->|Accepted| S8 --> S9 --> S10 --> C5
    S7 -->|Rejected| S10
```

## 4. Payment Reconciliation Swimlane

```mermaid
flowchart TB
    subgraph System["⚙️ System"]
        S1[Generate Daily Settlement Report]
        S2[Fetch Gateway Settlement Data]
        S3[Match Captures to Settlements]
        S4{Discrepancies Found?}
        S5[Flag Discrepancies for Review]
        S6[Generate Clean Reconciliation Report]
    end

    subgraph Finance["💰 Finance"]
        F1[Review Reconciliation Dashboard]
        F2[Investigate Flagged Discrepancies]
        F3[Resolve or Escalate]
        F4[Archive Reconciliation Report]
    end

    subgraph Admin["🔧 Admin"]
        A1[Receive Escalation Alert]
        A2[Contact Payment Gateway Support]
    end

    S1 --> S2 --> S3 --> S4
    S4 -->|No| S6 --> F1 --> F4
    S4 -->|Yes| S5 --> F1
    F1 --> F2 --> F3
    F3 -->|Resolved| F4
    F3 -->|Escalate| A1 --> A2
```
