# BPMN / Swimlane Diagram

## Overview

This document presents cross-functional swimlane diagrams illustrating handoffs between Customer, Warehouse Staff, Delivery Staff, Operations Manager, Admin, Finance, and System for the core business processes of the Order Management and Delivery System.

Each diagram models the responsibilities of each actor lane, the decision points that route the process to different branches, and the domain events emitted at key state transitions.

| # | Swimlane | Key Actors | Purpose |
|---|----------|------------|---------|
| 1 | Order-to-Delivery | Customer, System, Warehouse, Delivery Staff | End-to-end order placement through confirmed delivery |
| 2 | Returns Processing | Customer, System, Delivery Staff, Warehouse | Customer-initiated return, inspection, and refund |
| 3 | Failed Delivery and Rescheduling | Customer, Delivery Staff, System, Ops Manager | Retry logic, rescheduling windows, and RTO handling |
| 4 | Payment Processing and Gateway Failover | Customer, System, Primary Gateway, Secondary Gateway | Authorization, capture, failover, and webhook reconciliation |
| 5 | Analytics Report Generation | Admin/Finance, System, Report Engine, S3 | Async report export and presigned download delivery |

---

## 1. Order-to-Delivery Swimlane

Covers the standard happy-path from a customer browsing and placing an order through to final delivery and proof-of-delivery upload. The System orchestrates inventory reservation, payment processing, fulfillment task creation, and delivery assignment. Domain events are emitted at each major state change — `order.confirmed.v1` and `order.delivered.v1` — to allow downstream services to react asynchronously.

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

---

## 2. Returns Processing Swimlane

Covers the reverse logistics flow initiated when a customer requests a return on a delivered order. Return eligibility is validated against the configured return window and policy rules before a return request is created. Delivery Staff collect the item and transport it to the warehouse where it undergoes quality inspection — a passed inspection triggers an automatic refund while a failed inspection closes the request without a refund.

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

---

## 3. Failed Delivery and Rescheduling Swimlane

Covers the end-to-end flow for a failed delivery attempt through to either successful rescheduling or Return-to-Origin (RTO). The System tracks attempt counts per order, generates available rescheduling slots for the delivery zone on each failure, and transitions the order to `ReturnedToWarehouse` after three consecutive failures.

Operations Managers monitor failed deliveries from a dedicated dashboard and can manually reassign to available staff. On RTO, inventory is restored and a refund is automatically initiated. The Warehouse Staff lane handles the physical RTO receipt, verifying package condition before restoring stock.

```mermaid
flowchart TB
    subgraph Customer["👤 Customer"]
        C1[Receive Failed Delivery Push Notification]
        C2[Open App — View Failed Attempt Details and Reason]
        C3[Browse Available Reschedule Slots for Zone]
        C4[Confirm Preferred Date and Time Window]
        C5[Receive Reschedule Confirmation Notification]
        C6[Receive RTO Notification with Refund Timeline]
        C7[Optionally Request Order Cancellation After 1st Failure]
        C8[Receive Pre-Delivery Reminder Before Reattempt Window]
        C9[Receive Delivery Confirmation and POD Link on Success]
    end

    subgraph DeliveryStaff["🚚 Delivery Staff"]
        D1[Arrive at Delivery Location]
        D2[Attempt to Contact Customer — Call / Doorbell]
        D3{Contact and Delivery Successful?}
        D4[Capture Signature and Photo — Upload POD]
        D5[Record Failed Reason — Unavailable / Refused / Wrong Address]
        D6[Mark Attempt Count in Delivery App]
        D7[Update Live Location Pin on Route Completion]
        D8[On Next Assigned Window — Reattempt Delivery]
        D9[Hand Package Back to Warehouse — RTO Barcode Scan]
    end

    subgraph System["⚙️ System"]
        S1[Log Failed Delivery Attempt in DB]
        S2[Increment Attempt Counter on Order]
        S3{Attempt Count < 3?}
        S4[Generate Available Reschedule Slots for Zone]
        S5[Send Failed Delivery Notification with Slot Options]
        S6[Update Delivery Assignment with Confirmed Window]
        S7[Notify Assigned Delivery Staff of New Window]
        S8[Emit delivery.rescheduled.v1 Event]
        S9[Transition Order Status — ReturnedToWarehouse]
        S10[Restore Reserved Inventory to Available Stock]
        S11[Trigger Refund Workflow — Original Payment Method]
        S12[Emit order.rto.initiated.v1 Event]
        S13[Send RTO and Refund Info Notification to Customer]
        S14[Mark Order Status — Delivered]
        S15[Emit order.delivered.v1 Event]
        S16[Send Delivery Confirmation and POD Link]
        S17[Emit delivery.attempted.v1 Event — Audit Log Entry]
        S18[Process Customer Cancellation Request Before Reattempt]
        S19[Send Pre-Delivery Reminder Notification — 2hr Before Window]
        S20[Update Estimated Delivery Time on Order Tracking Page]
        S21[Expire Unconfirmed Reschedule Slots After 24 Hours]
    end

    subgraph OpsManager["📊 Operations Manager"]
        O1[View Failed Deliveries on Operations Dashboard]
        O2[Filter by Zone, Staff, Attempt Count, and SLA Breach]
        O3{Manual Reassignment Needed?}
        O4[Select and Reassign to Available Delivery Staff]
        O5[Log Reassignment Reason and Timestamp]
        O6[Monitor Reattempt and Delivery Outcomes]
        O7[Export Failed Delivery SLA Report for Analysis]
    end

    subgraph Warehouse["👷 Warehouse Staff"]
        W1[Receive Returned Package — Scan RTO Barcode]
        W2[Verify Package Condition and Contents]
        W3[Update Stock Record — Returned to Shelf]
    end

    D1 --> D2 --> D3
    D3 -->|Success — Delivered| D4 --> S14 --> S15 --> S16 --> C9
    D3 -->|Failed — Customer Unavailable| D5 --> D6 --> S1
    S1 --> S2 --> S17
    S2 --> S3
    S3 -->|Yes — Schedule Retry| S4 --> S5 --> C1
    C1 --> C2 --> C3 --> C4 --> S6
    S6 --> C5
    S6 --> S7 --> S8 --> D8
    D8 --> D3
    S3 -->|No — Max Attempts Reached| S9
    S9 --> S10
    S9 --> S11 --> S12 --> S13 --> C6
    D9 -.->|Returns package to warehouse| W1
    W1 --> W2 --> W3 --> S10
    D7 -.->|GPS ping updates order tracking| S1
    C7 --> S18 --> S11
    S2 --> O1
    O1 --> O2 --> O3
    O3 -->|Yes| O4 --> O5 --> S6
    O3 -->|No| O6
    O6 -.->|Monitors next attempt outcome| D8
    O6 --> O7
    S8 --> S20
    S7 --> S19 --> C8
    S21 -.->|Expires unconfirmed slots| S4
```

---

## 4. Payment Processing and Gateway Failover Swimlane

Covers payment authorization with automatic failover from the primary gateway to a secondary gateway on timeout or failure. A circuit breaker pattern prevents cascading requests to an unavailable primary gateway. The System applies a pre-authorization fraud detection check, tokenizes card details (no PAN storage), and captures payment on a valid authorization token from either gateway. Post-settlement webhooks are verified with HMAC-SHA256 and processed idempotently to prevent duplicate state updates.

```mermaid
flowchart TB
    subgraph Customer["👤 Customer"]
        C1[Enter Payment Details at Checkout]
        C2[Submit Payment]
        C3[View Payment Processing Spinner]
        C4[Receive Payment Success Confirmation]
        C5[Receive Payment Failure Notification]
        C6[Retry or Select Different Payment Method]
        C7[View Order Confirmation Page with Summary]
        C8[Receive Email and SMS Payment Receipt]
    end

    subgraph System["⚙️ System"]
        S1[Tokenize Payment Details — No PAN Storage]
        S2[Run Pre-Authorization Fraud Detection Check]
        S3{Fraud Score Acceptable?}
        S4[Select Primary Payment Gateway — Load Balanced]
        S5[Initiate Authorization Request with Token]
        S6[Start Gateway Timeout Timer — 10s]
        S7{Primary Gateway Response?}
        S8[Trip Circuit Breaker — Primary Gateway Unavailable]
        S9[Route to Secondary Payment Gateway — Failover]
        S10[Initiate Failover Authorization Request]
        S11{Secondary Gateway Response?}
        S12[Send Capture Request on Authorization Token]
        S13[Record PaymentTransaction — gatewayRef, status=CAPTURED, gatewayUsed]
        S14[Emit payment.captured.v1 Event]
        S15[Send Order Confirmation and Payment Receipt to Customer]
        S16[Block Payment — Flag Order for Manual Fraud Review]
        S17[Release Inventory Reservation — Payment Failed]
        S18[Send Payment Failure Notification with Retry Options]
        S19[Receive Webhook Callback from Gateway]
        S20[Verify Webhook Signature — HMAC-SHA256]
        S21[Idempotency Check — Prevent Duplicate Processing]
        S22[Update PaymentTransaction Status from Webhook Payload]
        S23[Log PaymentAttempt Record — All Outcomes for Audit Trail]
        S24[Notify Customer — Fraud Review Pending, Order on Hold]
        S25[Resume Order After Manual Fraud Review Cleared]
    end

    subgraph PrimaryGateway["💳 Primary Payment Gateway"]
        PG1[Receive Authorization Request]
        PG2[Route to Card Network — Visa / Mastercard / UPI]
        PG3{Issuer Authorization?}
        PG4[Return Authorization Token and Gateway Reference]
        PG5[Return Decline Code or Timeout Response]
        PG6[Send Post-Settlement Webhook to System]
    end

    subgraph SecondaryGateway["🏦 Secondary Payment Gateway — Failover"]
        SG1[Receive Failover Authorization Request]
        SG2[Route to Card Network]
        SG3{Issuer Authorization?}
        SG4[Return Authorization Token and Reference]
        SG5[Return Decline or Failure Response]
    end

    C1 --> S1 --> S2 --> S3
    S3 -->|Pass| S4 --> S5 --> PG1
    S3 -->|Fail — High Risk Score| S16
    S5 --> S6
    PG1 --> PG2 --> PG3
    PG3 -->|Approved| PG4 --> S7
    PG3 -->|Declined or Timeout| PG5 --> S7
    S7 -->|Auth Token Received| S12
    S7 -->|Failed or Timed Out| S8
    S8 --> S9 --> S10 --> SG1
    SG1 --> SG2 --> SG3
    SG3 -->|Approved| SG4 --> S11
    SG3 -->|Declined| SG5 --> S11
    S11 -->|Auth Token Received| S12
    S11 -->|Both Gateways Failed| S17
    S12 --> S13 --> S14 --> S15 --> C4
    C4 --> C7 --> C8
    C3 -.->|Polls payment status| S13
    S17 --> S18 --> C5
    C5 --> C6 --> S4
    PG6 --> S19 --> S20 --> S21 --> S22
    S5 --> S23
    S16 --> S24
    S24 -.->|After manual review approved| S25 --> S4
    S22 -.->|Reconciliation settled| S13
```

---

## 5. Analytics Report Generation Swimlane

Covers on-demand report generation triggered from the analytics dashboard by Admin or Finance users. The System validates the request, creates a job record, and dispatches an async Fargate task via SQS. The Report Engine queries an isolated RDS read replica, aggregates and transforms the data, and generates the output in CSV or PDF format. The file is uploaded to S3 with a 90-day lifecycle expiry policy, and the requestor receives a time-limited presigned URL via notification. Scheduled recurring exports follow the same pipeline, auto-triggered at cron time without a manual dashboard request. Admins can also browse their full report history and share presigned download links with team members directly from the dashboard.

```mermaid
flowchart TB
    subgraph AdminFinance["👨‍💼 Admin / Finance"]
        A1[Navigate to Analytics Dashboard]
        A2[View Real-Time Metrics — Orders, Revenue, Delivery Rate]
        A3[Apply Filters — Date Range, Zone, Category]
        A4[Request Report Export]
        A5[Select Report Type — Orders / Revenue / Delivery SLA]
        A6[Select Output Format — CSV or PDF]
        A7[Submit Export Request]
        A8[View Report Generation Status — Pending / Processing / Done]
        A9[Receive Report Ready Notification with Download Link]
        A10[Download Report via Presigned URL]
        A11[Open and Review Report Locally]
        A12[Configure Scheduled Recurring Report — Daily or Weekly Cadence]
        A13[View Report History — Filter by Type, Date, and Status]
        A14[Share Download Link with Team Members]
    end

    subgraph System["⚙️ System"]
        S1[Load Real-Time Metrics from CloudWatch and RDS Read Replica]
        S2[Serve Dashboard Data via Cached API Response — TTL=30s]
        S3[Validate Export Request — Auth, Params, Rate Limit Check]
        S4[Create Report Job Record — status=PENDING, jobId=uuid]
        S5[Return jobId to Client for Status Polling]
        S6[Dispatch Async Report Task to Fargate via SQS]
        S7[Receive Job Completion Signal from Report Engine via SQS]
        S8[Update Report Job — status=COMPLETED]
        S9[Record Presigned S3 URL against Report Job — TTL=1hr]
        S10[Send Email and In-App Notification with Download Link]
        S11[Auto-trigger Scheduled Report at Cron Time — Bypass Manual Step]
        S12[Mark Report Job status=FAILED and Notify Admin on Exhausted Retries]
        S13[Serve Report History via Paginated API — Filter by Status and Date]
        S14[Revoke Presigned URL and Expire Report Job Record After TTL]
    end

    subgraph ReportEngine["🔧 Report Engine — AWS Fargate Task"]
        R1[Pull Job Parameters from SQS Queue]
        R2[Connect to RDS Read Replica — Isolated Read Pool]
        R3[Execute Parameterized SQL Queries for Date Range and Filters]
        R4[Aggregate Metrics — Group by Zone, SKU, Staff, Status]
        R5[Apply Business Logic — SLA Thresholds, Refund Rates, AOV]
        R6[Generate CSV via Streaming Writer]
        R7[Generate PDF with Charts via Headless Renderer]
        R8[Upload Report File to S3 with Metadata Tags]
        R9[Publish Completion Event to SQS]
        R10[Retry Up to 3 Times on Query or Upload Failure]
    end

    subgraph S3Storage["☁️ Amazon S3 — Report Storage Bucket"]
        ST1[Receive and Store Report File]
        ST2[Tag with Metadata — jobId, userId, reportType, generatedAt]
        ST3[Apply 90-Day Lifecycle Expiry Policy]
        ST4[Generate Presigned Download URL — TTL=1hr]
        ST5[Serve File on Authenticated Download Request]
        ST6[Record Access in S3 Server Access Logs]
    end

    A1 --> S1 --> S2 --> A2
    A2 --> A3 --> A4 --> A5 --> A6 --> A7 --> S3
    S3 --> S4 --> S5 --> A8
    S4 --> S6 --> R1
    A12 --> S11 --> S4
    R1 --> R2 --> R3 --> R4 --> R5
    R5 --> R6
    R5 --> R7
    R6 --> R8
    R7 --> R8
    R10 -.->|Retries on transient failure| R2
    R8 --> ST1
    ST1 --> ST2 --> ST3
    R8 --> R9 --> S7
    S7 --> S8 --> S9
    S9 --> ST4
    S8 --> S10 --> A9
    A9 --> A10 --> ST4 --> ST5 --> ST6
    A10 --> A11
    A10 --> A14
    A1 --> A13 --> S13
    S9 -.->|TTL expiry| S14
    R10 -->|All retries exhausted| S12
```

---

## Design Notes

- All diagrams use `flowchart TB` (top-to-bottom layout) with named `subgraph` blocks representing each actor or system lane.
- Solid arrows (`-->`) represent synchronous hand-offs or direct data flows between steps.
- Dashed arrows (`-.->`) represent asynchronous, polling, or background flows — such as GPS pings, event subscriptions, or TTL-based expiry.
- Decision diamonds (`{}`) mark branching points where the process diverges based on a runtime condition (e.g., attempt count, gateway response, fraud score).
- Domain events follow the naming convention `{entity}.{verb}.v{version}` (e.g., `order.confirmed.v1`, `payment.captured.v1`) and are consumed asynchronously by downstream services.
- Cross-subgraph edges are the primary modelling mechanism for hand-offs between actors; they surface ownership boundaries and integration points.
- The `ReturnedToWarehouse` state in the Failed Delivery flow is terminal — once an RTO is initiated, inventory is restored and a refund is triggered automatically with no further delivery attempts.
- The Payment gateway circuit breaker in Swimlane 4 is reset automatically after a configurable cool-down period; manual override is available through the Ops dashboard.
- Report presigned URLs in Swimlane 5 carry a 1-hour TTL enforced by S3; report job records and S3 objects themselves expire after 90 days via a lifecycle policy.
- Warehouse Staff lanes in Swimlanes 1 and 3 handle physical package operations — pick, pack, and RTO receipt — decoupled from the System's digital state transitions via fulfillment task records.
- The OpsManager lane in Swimlane 3 is a supervisory lane with no blocking dependency on the core delivery flow; all OpsManager actions feed back into the same System hand-off points used by automatic rescheduling.
- Scheduled reports in Swimlane 5 share the same async Fargate pipeline as on-demand exports, with the cron trigger substituting for the manual Admin request step.
- All payment authorization and capture steps in Swimlane 4 are idempotent by design — duplicate webhook deliveries from the gateway are safely ignored via the idempotency key stored against the PaymentTransaction record.
- The fraud detection check in Swimlane 4 runs synchronously on the hot path; a high-risk score suspends the payment flow and puts the order on hold pending manual review, rather than silently declining the transaction.

