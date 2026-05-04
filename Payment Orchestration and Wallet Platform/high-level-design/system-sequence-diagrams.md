# System Sequence Diagrams — Payment Orchestration and Wallet Platform

These diagrams show the key end-to-end interactions for online payments, capture, wallet posting, refunds, and payout release. Timeout and retry rules are called out below each diagram so teams can implement them consistently.

## 1. Create and Authorize Payment with Fallback

```mermaid
sequenceDiagram
    autonumber
    actor Merchant
    participant Gateway
    participant Orchestrator
    participant Risk
    participant Vault
    participant PSP1
    participant PSP2
    participant Ledger

    Merchant->>Gateway: POST payment intent
    Gateway->>Orchestrator: Validate request
    Orchestrator->>Orchestrator: Store idempotency key
    Orchestrator->>Risk: Score transaction
    Risk-->>Orchestrator: Return ALLOW
    Orchestrator->>Vault: Tokenize card
    Vault-->>Orchestrator: Return token
    Orchestrator->>PSP1: Submit authorization
    alt PSP1 timeout
        PSP1-->>Orchestrator: Return timeout
        Orchestrator->>PSP1: Query attempt status
        PSP1-->>Orchestrator: Return no auth found
        Orchestrator->>PSP2: Submit authorization
        PSP2-->>Orchestrator: Return auth success
    else PSP1 success
        PSP1-->>Orchestrator: Return auth success
    end
    Orchestrator->>Ledger: Record auth hold
    Ledger-->>Orchestrator: Return journal id
    Orchestrator-->>Gateway: Return AUTHORIZED
    Gateway-->>Merchant: Return response
```

**Timeout and retry policy**
- Gateway request timeout: 6 seconds.
- Risk scoring budget: 150 ms p99.
- Vault tokenization budget: 100 ms p99.
- PSP authorization timeout: 3 seconds per provider.
- Fallback is allowed only after provider status query proves no surviving authorization exists.

## 2. Capture and Ledger Recognition

```mermaid
sequenceDiagram
    autonumber
    actor Merchant
    participant Gateway
    participant Orchestrator
    participant PSP
    participant Ledger
    participant Settlement
    participant Webhook

    Merchant->>Gateway: POST capture
    Gateway->>Orchestrator: Validate capture
    Orchestrator->>PSP: Submit capture
    PSP-->>Orchestrator: Return capture success
    Orchestrator->>Ledger: Post capture journal
    Ledger-->>Orchestrator: Return journal id
    Orchestrator->>Settlement: Publish settlement candidate
    Orchestrator->>Webhook: Queue merchant event
    Orchestrator-->>Gateway: Return CAPTURED
    Gateway-->>Merchant: Return response
```

**Capture notes**
- Capture is rejected if requested amount exceeds remaining authorized amount.
- If PSP capture succeeds but ledger posting fails, the payment enters `OPERATIONS_HOLD` and payout release is blocked until replay completes.
- Partial capture retains the remaining amount on the original authorization until void or expiry.

## 3. Refund and Duplicate Callback Handling

```mermaid
sequenceDiagram
    autonumber
    actor Support
    participant Refund
    participant PSP
    participant Ledger
    participant Webhook
    participant Merchant

    Support->>Refund: POST refund
    Refund->>Refund: Store refund request
    Refund->>PSP: Submit refund
    PSP-->>Refund: Return accepted
    Refund->>Ledger: Post refund reserve
    Ledger-->>Refund: Return journal id
    Refund->>Webhook: Queue refund event
    PSP-->>Refund: Send webhook
    Refund->>Refund: Deduplicate webhook
    Refund->>Ledger: Post refund finalization
    Ledger-->>Refund: Return journal id
    Webhook-->>Merchant: Deliver refund update
```

**Refund notes**
- Refund request idempotency is scoped by merchant and payment intent.
- Provider webhook processing is idempotent by provider event ID and refund reference.
- Refund reserve and refund finalization may be separate journals when the provider confirms asynchronously.

## 4. Payout Release with Compliance Hold

```mermaid
sequenceDiagram
    autonumber
    actor Treasury
    participant Payout
    participant Wallet
    participant KYC
    participant AML
    participant Bank
    participant Ledger

    Treasury->>Payout: POST payout
    Payout->>Wallet: Reserve funds
    Wallet-->>Payout: Return reserved
    Payout->>KYC: Check merchant status
    KYC-->>Payout: Return VERIFIED
    Payout->>AML: Screen beneficiary
    alt AML review required
        AML-->>Payout: Return REVIEW
        Payout->>Wallet: Keep reserve hold
        Payout-->>Treasury: Return PENDING_REVIEW
    else AML clear
        AML-->>Payout: Return CLEAR
        Payout->>Bank: Dispatch payout
        Bank-->>Payout: Return accepted
        Payout->>Ledger: Post payout journal
        Ledger-->>Payout: Return journal id
        Payout-->>Treasury: Return IN_TRANSIT
    end
```

## 5. Settlement and Three-Way Reconciliation

```mermaid
sequenceDiagram
    autonumber
    participant Settlement
    participant Ledger
    participant PSP
    participant Bank
    participant Recon
    participant Ops

    Settlement->>Ledger: Load captured journals
    Ledger-->>Settlement: Return batch candidates
    Settlement->>PSP: Submit settlement file
    PSP-->>Settlement: Return file ack
    PSP-->>Recon: Deliver clearing file
    Bank-->>Recon: Deliver bank statement
    Recon->>Ledger: Load ledger snapshot
    Recon->>Recon: Match three sources
    Recon-->>Ops: Publish break summary
```

**Reconciliation notes**
- Input snapshots are immutable and versioned by file checksum and import timestamp.
- `TIMING` breaks do not block the entire run but do block payout release for affected merchants when exposure thresholds are crossed.
