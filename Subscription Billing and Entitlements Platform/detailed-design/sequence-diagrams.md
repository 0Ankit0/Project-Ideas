# Sequence Diagrams (Implementation Ready)

## 1. Checkout, Invoice Finalization, and Entitlement Activation
```mermaid
sequenceDiagram
    autonumber
    participant UI as Customer UI
    participant API as Billing API
    participant SUB as Subscription Service
    participant BILL as Invoice Service
    participant TAX as Tax Engine
    participant PAY as Payment Provider
    participant ENT as Entitlement Service

    UI->>API: POST /v1/subscriptions
    API->>SUB: validate tenant/account/plan_version
    SUB->>BILL: create draft invoice
    BILL->>TAX: calculate tax lines
    TAX-->>BILL: tax quote
    BILL->>BILL: finalize invoice (lock line_hash)
    BILL->>PAY: authorize + capture
    alt payment success
      PAY-->>BILL: settled
      BILL->>SUB: mark subscription active
      BILL->>ENT: grant features + quotas
      API-->>UI: 201 subscription active
    else payment failure
      PAY-->>BILL: declined
      BILL->>SUB: keep pending/past_due
      API-->>UI: 402 payment required
    end
```

## 2. Mid-Cycle Upgrade with Proration
```mermaid
sequenceDiagram
    autonumber
    participant Admin as Subscriber Admin
    participant API as Billing API
    participant SUB as Subscription Service
    participant RATE as Proration Engine
    participant INV as Invoice Service
    participant PAY as Payment Service
    participant ENT as Entitlement Service

    Admin->>API: POST /subscriptions/{id}/amendments
    API->>SUB: persist amendment(idempotency key)
    SUB->>RATE: calculate credit/debit from remaining period
    RATE-->>INV: proration lines + deterministic key
    INV->>INV: create and finalize proration invoice
    INV->>PAY: collect delta amount
    alt settled
      PAY-->>INV: success
      INV-->>ENT: apply upgraded entitlement
    else failed
      PAY-->>INV: failure
      INV-->>ENT: keep grace/previous entitlement
    end
```

## 3. Reconciliation Drift to Repair Closure
```mermaid
sequenceDiagram
    autonumber
    participant REC as Reconciliation Job
    participant LED as Ledger Service
    participant INV as Invoice Service
    participant ENT as Entitlement Service
    participant OPS as Ops Console
    participant RCV as Recovery Service

    REC->>INV: fetch finalized invoice facts
    REC->>LED: fetch posted ledger facts
    REC->>ENT: fetch entitlement snapshots
    REC->>REC: compare + classify drift
    alt drift found
      REC-->>OPS: incident payload (class + scope)
      OPS->>RCV: run dry replay/compensation plan
      RCV-->>OPS: impact summary
      OPS->>RCV: execute approved action
      RCV-->>REC: repaired event
      REC->>REC: post-repair recon
      REC-->>OPS: resolved
    else no drift
      REC-->>OPS: clean report
    end
```

## 4. Terminal Dunning and Entitlement Suspension
```mermaid
sequenceDiagram
    autonumber
    participant DUN as Dunning Scheduler
    participant INV as Invoice Service
    participant PAY as Payment Provider
    participant ENT as Entitlement Service
    participant NOTI as Notification Service

    DUN->>INV: fetch overdue invoice
    INV->>PAY: retry charge
    alt retry success
      PAY-->>INV: success
      INV->>ENT: ensure granted state
      INV->>NOTI: payment recovered notice
    else retry failed and terminal
      PAY-->>INV: decline terminal
      INV->>INV: mark uncollectible or canceled policy
      INV->>ENT: transition to suspended/revoked
      INV->>NOTI: suspension notice
    end
```
