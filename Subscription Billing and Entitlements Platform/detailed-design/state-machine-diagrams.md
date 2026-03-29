# State Machine Diagrams (Implementation Ready)

## 1. Subscription Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Trialing
    Trialing --> Active: trial_converted
    Trialing --> Canceled: canceled_during_trial

    Active --> PastDue: invoice_overdue
    PastDue --> Active: payment_recovered
    Active --> Canceled: cancel_requested
    PastDue --> Canceled: dunning_terminal_failure

    Active --> Paused: manual_pause
    Paused --> Active: resume

    Canceled --> [*]
```

## 2. Invoice Lifecycle with Guard Conditions
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Finalized: finalize()\nrequires tax_lock && line_hash
    Finalized --> Issued: issue()\nrequires delivery_enqueued
    Issued --> PartiallyPaid: payment_partial
    Issued --> Paid: payment_full
    Issued --> Overdue: due_date_passed
    PartiallyPaid --> Paid: payment_remaining
    PartiallyPaid --> Overdue: due_date_passed
    Overdue --> Paid: late_payment
    Issued --> Voided: void_approved
    Overdue --> Uncollectible: writeoff_approved
    Paid --> Refunded: refund_full
    Refunded --> [*]
    Voided --> [*]
    Uncollectible --> [*]
```

## 3. Entitlement Lifecycle with Grace Rules
```mermaid
stateDiagram-v2
    [*] --> PendingActivation
    PendingActivation --> Granted: invoice_paid
    Granted --> Grace: payment_failed_within_grace
    Grace --> Granted: payment_recovered
    Grace --> Suspended: grace_expired
    Granted --> Revoked: subscription_ended
    Suspended --> Granted: arrears_cleared
    Revoked --> [*]
```

## 4. Recovery Action Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Approved: approver_signed
    Approved --> DryRunCompleted: run_dry_replay
    DryRunCompleted --> Executing: execute_confirmed
    Executing --> Verified: post_recon_success
    Executing --> Failed: execution_error
    Failed --> Approved: re_approve_after_fix
    Verified --> [*]
```

## 5. Transition Validation Rules
- Prohibit backward transitions that mutate settled financial truth.
- Require immutable transition log entry before state change commit.
- Couple transitions to side-effect dispatch only after persistence.
- Reject transitions without correlation ID for auditability.
