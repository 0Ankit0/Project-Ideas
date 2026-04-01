# Activity Diagrams — Payment Orchestration and Wallet Platform

This document provides detailed activity diagrams for the five core operational flows in the Payment Orchestration and Wallet Platform. Each diagram uses Mermaid flowcharts with explicit decision branches, retry paths, and terminal states, matching production-level process fidelity.

---

## 3.1 Payment Authorization and Capture Flow

This flow covers the complete lifecycle from an inbound API request through fraud scoring, 3DS2 authentication, PSP routing with failover, authorisation, optional auto-capture, ledger posting, webhook delivery, and settlement queue enqueue.

```mermaid
flowchart TD
    A([START: POST /payments received]) --> B[Validate API key & merchant account]
    B --> C{Merchant\nactive & verified?}
    C -- No --> Z1([RETURN 401/403 Unauthorized])
    C -- Yes --> D[Parse & validate request body\namount, currency, payment method, idempotency_key]
    D --> E{Request\nvalidation passed?}
    E -- No --> Z2([RETURN 422 Unprocessable Entity\nwith field-level errors])
    E -- Yes --> F[Check idempotency store\nlookup idempotency_key in cache/DB]
    F --> G{Duplicate\nrequest?}
    G -- Yes --> Z3([RETURN 200 with cached response\nno re-processing])
    G -- No --> H[Create PaymentIntent record\nstatus = INITIATED\ngenerate correlation_id]
    H --> I[Call Fraud Scoring Engine\nKount API with 50+ signals\ndevice, IP, BIN, velocity]
    I --> J{Fraud\nDecision?}
    J -- BLOCK --> Z4([RETURN 402 Declined\nreason = FRAUD_BLOCK\nupdate status = DECLINED])
    J -- REVIEW --> K[Queue for manual review\nstatus = PENDING_REVIEW\nnotify Risk Analyst]
    K --> L{Review\ndecision within\n15 minutes?}
    L -- Declined --> Z5([RETURN 402 Declined\nreason = MANUAL_DECLINE])
    L -- Approved / Timed-out --> M
    J -- ALLOW --> M[Check 3DS2 requirement\nassess SCA exemption eligibility\nAMT < €30, trusted beneficiary, etc.]
    M --> N{3DS2\nrequired?}
    N -- Yes --> O[Initiate 3DS2 flow\nsend auth request to ACS Server\nstatus = AUTHENTICATING]
    O --> P{3DS2\nChallenge\nresult?}
    P -- Failed / Abandoned --> Z6([RETURN 402 Declined\nreason = AUTHENTICATION_FAILED])
    P -- Frictionless / Challenge Passed --> Q[Attach CAVV & ECI value\nto authorisation payload]
    N -- No / Exempted --> Q
    Q --> R[Select PSP Route\napply routing rules: cost, success rate,\ncurrency, merchant preference]
    R --> S[Submit Authorisation to PSP\nstatus = AUTHORIZING]
    S --> T{PSP\nresponse?}
    T -- Timeout / Network Error --> U{Retry\nattempt ≤ 3?}
    U -- Yes --> V[Wait exponential backoff\n1s / 2s / 4s]
    V --> S
    U -- No / PSP Error 5xx --> W{Alternative\nPSP available?}
    W -- Yes --> X[Failover to next PSP\nlog failover event]
    X --> S
    W -- No --> Z7([RETURN 502 Bad Gateway\nstatus = FAILED\nreason = PSP_UNAVAILABLE])
    T -- Hard Decline --> Z8([RETURN 402 Declined\nstatus = DECLINED\nforward PSP decline code])
    T -- Authorised --> Y[Update status = AUTHORIZED\nstore auth_code, network_txn_id]
    Y --> AA{Capture\nmode?}
    AA -- Manual / Delayed --> AB[Store in AUTHORIZED state\nset auto-capture timer if configured]
    AB --> AC([RETURN 201 Created\nstatus = AUTHORIZED])
    AA -- Auto-capture --> AD[Submit Capture request to PSP\nstatus = CAPTURE_PENDING]
    AD --> AE{Capture\nconfirmed?}
    AE -- No --> AF[Retry capture up to 3x\nwith backoff]
    AF --> AE
    AE -- Timeout / Failed --> Z9([Alert Ops team\nstatus = CAPTURE_FAILED\npage on-call])
    AE -- Yes --> AG[Update status = CAPTURED\nrecord captured_at timestamp]
    AG --> AH[Post double-entry journal\nDR: Receivable account\nCR: Merchant float account]
    AH --> AI{Ledger\nposting\nsucceeded?}
    AI -- No --> Z10([Move to OPERATIONS_HOLD\npage Finance on-call\nblock settlement])
    AI -- Yes --> AJ[Enqueue in Settlement Queue\nadd to next settlement batch]
    AJ --> AK[Emit payment.captured event\nto internal event bus]
    AK --> AL[Deliver webhook to Merchant\nPOST merchant_webhook_url\nwith HMAC signature]
    AL --> AM{Webhook\ndelivered?}
    AM -- No --> AN[Retry webhook\nup to 5x with exponential backoff\n30s, 60s, 120s, 300s, 600s]
    AN --> AM
    AM -- Max retries exceeded --> AO[Mark webhook as FAILED\nlog for merchant dashboard]
    AM -- Yes --> AP([END: Payment Captured Successfully])
```

---

## 3.2 Refund Processing Flow

This flow handles merchant- or customer-initiated refunds, from request validation through PSP refund execution, ledger reversal, optional wallet credit, and settlement adjustment.

```mermaid
flowchart TD
    A([START: POST /payments/id/refunds received]) --> B[Authenticate request\nvalidate merchant API key]
    B --> C{Authenticated?}
    C -- No --> Z1([RETURN 401 Unauthorized])
    C -- Yes --> D[Load original payment\nfetch PaymentIntent by ID]
    D --> E{Payment\nfound?}
    E -- No --> Z2([RETURN 404 Not Found])
    E -- Yes --> F{Payment\nstatus is\nCAPTURED or SETTLED?}
    F -- No --> Z3([RETURN 409 Conflict\nreason = INVALID_STATE_FOR_REFUND])
    F -- Yes --> G[Check refund amount ceiling\nsum of existing refunds + requested amount]
    G --> H{Requested\namount ≤\noriginal captured amount?}
    H -- No --> Z4([RETURN 422 Unprocessable Entity\nreason = REFUND_EXCEEDS_ORIGINAL])
    H -- Yes --> I[Check refund policy window\ncompare payment.captured_at vs now]
    I --> J{Within\nrefund window?\ndefault: 180 days}
    J -- No --> Z5([RETURN 422 Unprocessable Entity\nreason = REFUND_WINDOW_EXPIRED])
    J -- Yes --> K[Check idempotency key\nlookup refund_idempotency_key]
    K --> L{Duplicate\nrefund request?}
    L -- Yes --> Z6([RETURN 200 with existing refund record])
    L -- No --> M[Create Refund record\nstatus = REFUND_PENDING\namount, currency, reason_code]
    M --> N[Call PSP Refund API\nsubmit refund to original PSP\nusing stored PSP transaction reference]
    N --> O{PSP\nresponse?}
    O -- Timeout --> P{Retry\nattempt ≤ 3?}
    P -- Yes --> Q[Backoff and retry\n2s / 4s / 8s]
    Q --> N
    P -- No --> Z7([Move refund to FAILED\nAlert Ops\nrequire manual processing])
    O -- PSP Error / Declined --> Z8([RETURN 502\nstatus = REFUND_FAILED\ninclude PSP error code])
    O -- Accepted / Pending --> R[Update refund status = REFUND_IN_PROGRESS\nstore PSP refund reference ID]
    R --> S{PSP refund\nconfirmation\nreceived?]
    S -- Poll / Webhook awaited --> T[Wait for PSP webhook\nor poll every 60s up to 24h]
    T --> S
    S -- Confirmed --> U[Update refund status = REFUNDED\nupdate payment.refunded_amount]
    U --> V{Full refund\nor partial?}
    V -- Full --> W[Update payment status = REFUNDED]
    V -- Partial --> X[Update payment status = PARTIALLY_REFUNDED\nrecalculate remaining refundable amount]
    W --> Y
    X --> Y[Post reversal journal entry\nDR: Merchant float account\nCR: Receivable account]
    Y --> Z{Funded via\nWallet balance?}
    Z -- Yes --> AA[Credit customer wallet\npost WalletCredited event\nupdate wallet balance]
    Z -- No / Card funding --> AB[PSP issues direct card refund\nno wallet action required]
    AA --> AC
    AB --> AC[Emit refund.completed event\nto internal event bus]
    AC --> AD[Notify customer\nSMS via Twilio + email via SendGrid]
    AD --> AE[Flag transaction in Settlement Adjustment queue\nadjust net settlement amount for batch]
    AE --> AF([END: Refund Processed Successfully])
```

---

## 3.3 Chargeback Dispute Flow

This flow models the full chargeback lifecycle from the moment the platform receives a dispute notification through evidence collection, representment, issuer decision, and ledger finalisation.

```mermaid
flowchart TD
    A([START: Chargeback webhook received from PSP]) --> B[Parse dispute notification\nextract chargeback_id, reason_code,\namount, deadline from payload]
    B --> C[Validate webhook signature\nHMAC verification against PSP secret]
    C --> D{Signature\nvalid?}
    D -- No --> Z1([Discard event\nlog security alert])
    D -- Yes --> E[Look up original payment\nby PSP transaction reference]
    E --> F{Payment\nfound?}
    F -- No --> Z2([Log orphaned chargeback\nalert Ops team\nmanual investigation required])
    F -- Yes --> G[Create Dispute record\nstatus = CHARGEBACK_OPEN\nreason_code, amount, chargeback_deadline]
    G --> H[Debit provisional hold\nDR: Merchant float account\nCR: Chargeback reserve account\nfor disputed amount + fees]
    H --> I[Update payment status = CHARGEBACK_OPEN]
    I --> J[Notify Merchant immediately\nPOST webhook: dispute.opened\nemail alert with deadline]
    J --> K[Start evidence collection countdown\nset deadline = chargeback_deadline - 2 days\nbuffer for upload processing]
    K --> L{Merchant\nresponds with\nevidence before deadline?}
    L -- No response / Withdrawal --> M[Merchant concedes dispute\nupdate status = CHARGEBACK_LOST]
    M --> N[Finalise debit\nDR: Merchant float account\nCR: Chargeback reserve account\nnote: provisional → confirmed]
    N --> O[Notify merchant of loss\nemit dispute.lost event]
    O --> P
    L -- Evidence submitted --> Q[Validate evidence package\ncheck file types, sizes, completeness]
    Q --> R{Evidence\npackage valid?}
    R -- No --> S[Return validation errors to merchant\nremaining time to resubmit]
    S --> L
    R -- Yes --> T[Relay evidence to PSP\nPOST /disputes/id/evidence\nattach documents, transaction logs]
    T --> U{PSP\naccepted\nevidence?}
    U -- No --> V[PSP rejection — resubmit or escalate\nnotify merchant]
    V --> L
    U -- Yes --> W[Update status = EVIDENCE_SUBMITTED\nstore submission timestamp]
    W --> X[Await issuer decision\npoll PSP every 24h or await webhook\ntypical window: 20-45 days]
    X --> Y{Issuer\ndecision?}
    Y -- Still pending --> X
    Y -- Dispute WON\nRepresentment successful --> Z[Update status = CHARGEBACK_WON]
    Z --> AA[Reverse provisional hold\nDR: Chargeback reserve account\nCR: Merchant float account]
    AA --> AB[Return funds to merchant\nnet of any chargeback processing fees]
    AB --> AC[Notify merchant of win\nemit dispute.won event]
    AC --> P
    Y -- Dispute LOST --> M
    P[Post final journal entry\nclose chargeback reserve balance\nrecord outcome and fees] --> Q2[Update compliance records\nlog reason code, outcome for reporting]
    Q2 --> R2([END: Dispute closed])
```

---

## 3.4 Settlement Batch Run Flow

This flow describes the end-of-day settlement process, from batch trigger through PSP file collection, three-way reconciliation, net amount calculation, bank submission, and batch closure.

```mermaid
flowchart TD
    A([START: Settlement batch triggered\nscheduled T+1 22:00 UTC or manual]) --> B[Acquire batch lock\nprevent concurrent batch runs\nuse distributed lock with TTL = 4h]
    B --> C{Lock\nacquired?}
    C -- No --> Z1([RETURN: Batch already running\nlog and exit])
    C -- Yes --> D[Set batch status = RUNNING\nrecord batch_start_time, triggered_by]
    D --> E[Collect all CAPTURED transactions\nsince last settlement cutoff\ngroup by merchant, currency, PSP]
    E --> F{Any transactions\nto settle?}
    F -- No --> Z2[Release lock\nclose empty batch\nlog: no transactions]
    F -- Yes --> G[For each PSP group:\ncalculate gross settlement amount\nin settlement currency]
    G --> H[Apply fee rules\nplatform fee %\nPSP interchange fee\ncurrency conversion spread]
    H --> I[Calculate net settlement amount\ngross - platform fees - PSP fees\n± FX conversion if needed]
    I --> J[Fetch latest FX rates\nfrom Bloomberg / OER for cross-currency nets]
    J --> K[Generate PSP settlement file\nISO 20022 / CSV per PSP format]
    K --> L[Transmit settlement file to bank\nvia SFTP or bank API\nfor each acquiring bank account]
    L --> M{File\ntransmission\nsucceeded?}
    M -- No --> N[Retry transmission up to 3x\n5 min intervals]
    N --> M
    M -- Max retries failed --> Z3([Alert Finance on-call\nbatch status = TRANSMISSION_FAILED\nblock merchant payouts])
    M -- Yes --> O[Update transactions status = SETTLEMENT_PENDING\nrecord batch_id on each transaction]
    O --> P[Await bank acknowledgment\npoll bank API or await SFTP response\ntimeout: 4 hours]
    P --> Q{Bank\nconfirmation\nreceived?}
    Q -- Timeout --> R{Retry\ncheck?}
    R -- Yes --> P
    R -- No --> Z4([Escalate to Finance team\nbatch status = CONFIRMATION_TIMEOUT])
    Q -- Rejected --> Z5([Alert Finance team\nbatch status = REJECTED_BY_BANK\ninclude rejection reason code])
    Q -- Confirmed --> S[Update transactions status = SETTLED\nrecord settlement_date, bank_reference]
    S --> T[Reconcile against PSP settlement report\ndownload PSP settlement file from SFTP/API]
    T --> U[Three-way match\nledger amount vs PSP file vs bank statement\nfor each transaction line]
    U --> V{All lines\nmatched?}
    V -- No --> W[Classify breaks:\nTIMING, AMOUNT, MISSING, DUPLICATE\nauto-resolve TIMING breaks within tolerance]
    W --> X{Breaks\nresolved?}
    X -- No --> Y[Create reconciliation exceptions\nassign to Finance team for manual review\nstatus = RECON_EXCEPTION]
    Y --> Z[Generate exception report\nemail to Finance Manager]
    X -- Yes / After manual resolution --> Z[Generate exception report\nemail to Finance Manager]
    V -- Yes --> AA
    Z --> AA[Post final settlement journal entries\nDR: PSP receivable\nCR: Merchant bank account]
    AA --> AB[Calculate platform revenue\nsum of all fees collected]
    AB --> AC[Update batch status = COMPLETED\nrecord batch_end_time, total_settled_amount]
    AC --> AD[Release distributed lock]
    AD --> AE[Emit settlement.batch.completed event\nnotify merchants of individual payouts]
    AE --> AF([END: Settlement batch closed successfully])
```

---

## 3.5 Wallet Top-Up Flow

This flow covers the complete wallet funding journey, from customer-initiated top-up through payment intent creation, card authorisation, wallet credit posting, and customer notification.

```mermaid
flowchart TD
    A([START: Customer initiates wallet top-up\nPOST /wallets/id/topup]) --> B[Authenticate customer\nvalidate JWT / session token]
    B --> C{Authenticated?}
    C -- No --> Z1([RETURN 401 Unauthorized])
    C -- Yes --> D[Load wallet record\nverify wallet belongs to customer]
    D --> E{Wallet\nexists & active?}
    E -- No --> Z2([RETURN 404 / 409 Wallet not found or frozen])
    E -- Yes --> F[Check KYC level\nverify customer has completed required KYC tier]
    F --> G{KYC\nlevel sufficient\nfor top-up amount?}
    G -- No --> Z3([RETURN 403 Forbidden\nreason = KYC_REQUIRED\nreturn upgrade URL])
    G -- Yes --> H[Check top-up limits\nper-transaction limit, daily limit, monthly limit\nsum existing today/month deposits]
    H --> I{Within\nvelocity limits?}
    I -- No --> Z4([RETURN 422 Unprocessable Entity\nreason = LIMIT_EXCEEDED\ninclude remaining allowance])
    I -- Yes --> J[Validate payment method\ncustomer selects: saved card, new card, or bank transfer]
    J --> K{Payment\nmethod valid\nand owned by customer?}
    K -- No --> Z5([RETURN 422 Invalid payment method])
    K -- Yes --> L[Create PaymentIntent\ntype = WALLET_TOPUP\namount, currency, wallet_id\nstatus = INITIATED]
    L --> M[Check idempotency\nlookup top-up idempotency key]
    M --> N{Duplicate\nrequest?}
    N -- Yes --> Z6([RETURN 200 with existing top-up record])
    N -- No --> O[Run fraud pre-screening\nKount score on top-up event\ncheck for carding / rapid top-up patterns]
    O --> P{Fraud\nscore?}
    P -- BLOCK --> Z7([RETURN 402 Declined\nreason = FRAUD_BLOCK\nalert Risk Analyst])
    P -- REVIEW --> Q[Pause for manual review\nstatus = PENDING_REVIEW\nnotify Risk Analyst via portal]
    Q --> R{Review\ndecision?}
    R -- Declined --> Z8([RETURN 402 Declined\nreason = MANUAL_DECLINE])
    R -- Approved --> S
    P -- ALLOW --> S[Submit authorise & capture to PSP\nstatus = AUTHORIZING]
    S --> T{PSP\nauthorisation\nresult?}
    T -- Declined --> Z9([RETURN 402 Payment Declined\nforward PSP decline code to customer])
    T -- Network error --> U[Retry up to 3x with PSP failover\nif all PSPs fail → RETURN 502]
    U --> T
    T -- Authorised & Captured --> V[Update PaymentIntent status = CAPTURED]
    V --> W[Post credit to wallet\nDR: PSP receivable account\nCR: Customer wallet float account\nappend-only ledger entry]
    W --> X{Ledger\nposting\nsucceeded?}
    X -- No --> Z10([OPERATIONS_HOLD\nmanual reconciliation required\ndo NOT update wallet balance])
    X -- Yes --> Y[Update wallet balance\natomic increment: balance += top-up amount]
    Y --> Z[Emit WalletCredited event\npublish to internal event bus\nwallet_id, amount, new_balance, timestamp]
    Z --> AA[Notify customer\nSMS: 'Your wallet has been topped up with £X'\nemail receipt with transaction reference]
    AA --> AB[Update top-up velocity counters\nincrement daily and monthly counters]
    AB --> AC([END: Wallet top-up completed successfully\nRETURN 201 with new balance])
```

---

## 3.6 Activity Diagram Notes

### Decision Node Conventions
- **Diamond nodes** (`{...}`) represent decision points with explicit Yes/No or labelled branches.
- **Rounded rectangles** (`([...])`) represent terminal states (success or failure endpoints).
- **Rectangles** (`[...]`) represent processing steps.

### Error State Conventions
All terminal failure states (`Z1`, `Z2`, etc.) follow the pattern:
1. Return appropriate HTTP status code to caller
2. Update internal transaction status to reflect failure type
3. Emit failure event for monitoring / alerting
4. Log correlation ID, failure reason, and timestamp

### Retry Policies Summary

| Flow | Operation | Max Retries | Backoff Strategy | Failover |
|---|---|---|---|---|
| Auth & Capture | PSP Authorisation | 3 | Exponential (1s/2s/4s) | Yes — next PSP |
| Auth & Capture | Webhook delivery | 5 | Exponential (30s→600s) | No |
| Auth & Capture | Capture | 3 | Linear (5s) | No |
| Refund | PSP refund submission | 3 | Exponential (2s/4s/8s) | No |
| Settlement | File transmission | 3 | Linear (5 min) | No |
| Settlement | Bank confirmation poll | 12 | Linear (20 min) | No |
| Wallet Top-up | PSP authorisation | 3 | Exponential (1s/2s/4s) | Yes — next PSP |

