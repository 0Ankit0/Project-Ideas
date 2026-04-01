# Supply Chain Management Platform - State Machine Diagrams

## Purchase Requisition State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft
    
    Draft --> SubmittedForApproval: Submit for Approval
    Draft --> Cancelled: Cancel
    
    SubmittedForApproval --> Approved: Approval Given
    SubmittedForApproval --> Rejected: Approval Denied
    SubmittedForApproval --> Draft: Recall (Requester)
    
    Approved --> RFQIssued: Create RFQ
    Approved --> Cancelled: Cancel
    
    RFQIssued --> POCreated: Quotes Received & PO Created
    RFQIssued --> RFQIssued: Additional Quotes Received
    
    POCreated --> [*]
    
    Rejected --> Draft: Resubmit
    Rejected --> Cancelled: Cancel
    
    Cancelled --> [*]
    
    note right of Draft
        Initial state
        Requester can edit
    end note
    
    note right of SubmittedForApproval
        Awaiting manager approval
        Can be recalled by requester
    end note
    
    note right of Approved
        Approved by manager
        Ready to send RFQ to suppliers
    end note
    
    note right of RFQIssued
        RFQ sent to suppliers
        Quotes received
    end note
    
    note right of POCreated
        PO generated from
        selected quotation
    end note
```

## Purchase Order State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft
    
    Draft --> SentToSupplier: Send to Supplier
    Draft --> Cancelled: Cancel
    
    SentToSupplier --> Confirmed: Supplier Confirms
    SentToSupplier --> Cancelled: Cancel
    SentToSupplier --> Draft: Withdraw
    
    Confirmed --> PartiallyReceived: Partial GRN Posted
    Confirmed --> FullyReceived: GRN Received 100%
    Confirmed --> Cancelled: Cancel
    
    PartiallyReceived --> PartiallyReceived: Additional Receipt
    PartiallyReceived --> FullyReceived: Remaining Items Received
    PartiallyReceived --> Cancelled: Cancel by Agreement
    
    FullyReceived --> [*]
    
    Cancelled --> [*]
    
    note right of Draft
        PO created
        Can be modified
        Default: 30-day validity
    end note
    
    note right of SentToSupplier
        Transmitted to supplier
        Awaits confirmation
    end note
    
    note right of Confirmed
        Supplier acknowledged
        Awaiting delivery
    end note
    
    note right of PartiallyReceived
        Goods partially
        received and inspected
    end note
    
    note right of FullyReceived
        All goods received
        Final state
    end note
```

## Supplier State Machine

```mermaid
stateDiagram-v2
    [*] --> Invited
    
    Invited --> QualificationInProgress: Start Onboarding
    Invited --> Inactive: No Response (90 days)
    
    QualificationInProgress --> Approved: All Docs Approved
    QualificationInProgress --> Rejected: Qualification Failed
    QualificationInProgress --> QualificationInProgress: Additional Info Required
    
    Approved --> Active: First PO Issued
    
    Active --> Suspended: Breach of SLA
    Active --> Blacklisted: Serious Violation
    Active --> Active: Performance Score Updated
    
    Suspended --> Active: Issue Resolved
    Suspended --> Blacklisted: Repeated Violations
    
    Rejected --> Invited: Reapplication
    
    Inactive --> Invited: Reactivated
    
    Blacklisted --> [*]
    
    note right of Invited
        Initial state
        Waiting for response
    end note
    
    note right of QualificationInProgress
        KYC verification
        Document review
        Quality assessment
    end note
    
    note right of Approved
        Ready to supply
        Awaiting first PO
    end note
    
    note right of Active
        Actively supplying
        Performance tracked
        OTIF, Quality, Compliance
    end note
    
    note right of Suspended
        Temporary hold
        SLA issues
        Resolution required
    end note
    
    note right of Blacklisted
        Permanent ban
        Do not use
        No future business
    end note
```

## Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> Received
    
    Received --> UnderReview: Auto-review Started
    Received --> OnHold: Manual Review Required
    
    UnderReview --> Matched: 3-Way Match Passed
    UnderReview --> OnHold: Exception Found
    UnderReview --> Rejected: Invalid Invoice
    
    OnHold --> Matched: Issue Resolved
    OnHold --> Disputed: Queried with Supplier
    OnHold --> Rejected: Cannot Resolve
    
    Matched --> ApprovedForPayment: Finance Approval
    Matched --> OnHold: Further Review Needed
    
    Disputed --> Matched: Resolved
    Disputed --> Rejected: Cannot Reconcile
    
    ApprovedForPayment --> Paid: Payment Processed
    ApprovedForPayment --> ApprovedForPayment: Partial Payment
    
    Paid --> [*]
    
    Rejected --> [*]
    
    note right of Received
        Invoice submitted
        Initial state
    end note
    
    note right of UnderReview
        Automated 3-way match
        PO ↔ GRN ↔ Invoice
    end note
    
    note right of OnHold
        Manual investigation
        Qty/Price variance
        Tax discrepancy
    end note
    
    note right of Matched
        All validations passed
        Ready for payment
    end note
    
    note right of Disputed
        Supplier contacted
        Clarification pending
    end note
    
    note right of ApprovedForPayment
        Approved by finance
        Queued for settlement
    end note
    
    note right of Paid
        Payment transmitted
        Final state
        Archival
    end note
```

## Integration Notes

- All state transitions are logged with timestamp, user, reason
- State change events published to Kafka for downstream processing
- Timeouts implemented:
  - SubmittedForApproval: 5 business days (escalate if no approval)
  - RFQIssued: 10 days (auto-close if no quotes)
  - SentToSupplier: 30 days (auto-cancel if no confirmation)
  - OnHold (Invoice): 7 days (escalate to senior finance officer)
  - ApprovedForPayment: 3 days (process payment if still pending)

