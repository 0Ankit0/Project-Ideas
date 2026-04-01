# Sequence Diagrams — Payment Orchestration and Wallet Platform

> **Scope:** Three production-level sequence diagrams covering the critical payment flows:
> card authorization/capture, PSP failover, and cross-currency wallet transfer with rollback.
> All steps include system names, synchronous vs. asynchronous call types, and error paths.

---

## SD-001: Card Payment Authorization and Capture (Full Detail)

> **Trigger:** Merchant submits `POST /v1/payments` with card token and amount.
> **Outcome:** Payment captured, ledger posted, webhook delivered.
> **3DS2 branch:** Triggered when card issuer requires strong customer authentication.

```mermaid
sequenceDiagram
    autonumber
    participant Merchant
    participant APIGateway as API Gateway
    participant AuthMiddleware as Auth Middleware
    participant PaymentOrchestrator as Payment Orchestrator
    participant IdempotencyGuard as Idempotency Guard (Redis)
    participant VaultService as Vault Service
    participant FraudEngine as Fraud Engine
    participant PSPRouter as PSP Router
    participant StripeAdapter as Stripe Adapter
    participant StripeAPI as Stripe API (External)
    participant LedgerService as Ledger Service
    participant EventBus as Event Bus (Kafka)
    participant WebhookService as Webhook Service

    Merchant->>APIGateway: POST /v1/payments {amount, currency, card_token, idempotency_key}
    APIGateway->>AuthMiddleware: validate API key + merchant scope
    AuthMiddleware-->>APIGateway: 200 merchant_id + permissions
    APIGateway->>PaymentOrchestrator: createIntent(CreateIntentRequest)

    PaymentOrchestrator->>IdempotencyGuard: checkIdempotencyKey(idempotency_key)
    alt Duplicate request
        IdempotencyGuard-->>PaymentOrchestrator: DUPLICATE — return cached response
        PaymentOrchestrator-->>APIGateway: 200 cached PaymentIntent
        APIGateway-->>Merchant: 200 {status: processing, intent_id}
    else New request
        IdempotencyGuard-->>PaymentOrchestrator: NEW — proceed

        PaymentOrchestrator->>PaymentOrchestrator: persist PaymentIntent (status: requires_confirmation)

        PaymentOrchestrator->>VaultService: tokenizeCard(card_token, merchant_id)
        VaultService-->>PaymentOrchestrator: vault_token (network_token if available)

        PaymentOrchestrator->>FraudEngine: score(FraudRequest{amount, merchant, vault_token, ip, device})
        FraudEngine-->>PaymentOrchestrator: FraudDecision{outcome: ALLOW, risk_score: 12}

        alt FraudDecision = BLOCK
            PaymentOrchestrator->>PaymentOrchestrator: update status → failed (fraud_block)
            PaymentOrchestrator-->>APIGateway: 402 fraud_block
            APIGateway-->>Merchant: 402 {error: card_declined, decline_code: fraud_block}
        else FraudDecision = REVIEW
            PaymentOrchestrator->>PaymentOrchestrator: update status → requires_review
            PaymentOrchestrator->>EventBus: emit PaymentReviewRequired
            PaymentOrchestrator-->>APIGateway: 202 {status: requires_review}
        else FraudDecision = ALLOW
            PaymentOrchestrator->>PSPRouter: selectPSP(RoutingContext{amount, currency, merchant_id, method: card})
            PSPRouter-->>PaymentOrchestrator: PSPRoute{psp: stripe, score: 0.94}

            PaymentOrchestrator->>StripeAdapter: authorize(AuthorizeRequest{vault_token, amount, currency, capture_method: auto})
            StripeAdapter->>StripeAPI: POST /v1/payment_intents {confirm: true, capture_method: automatic}

            alt 3DS2 Required (next_action: redirect_to_url)
                StripeAPI-->>StripeAdapter: {status: requires_action, next_action: {type: redirect}}
                StripeAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: requires_action, redirect_url}
                PaymentOrchestrator->>PaymentOrchestrator: update status → requires_action
                PaymentOrchestrator-->>APIGateway: 200 {status: requires_action, redirect_url}
                APIGateway-->>Merchant: 200 {status: requires_action, redirect_url}
                Note over Merchant,StripeAPI: Customer completes 3DS2 challenge in browser
                StripeAPI->>StripeAdapter: Webhook: payment_intent.succeeded (3DS complete)
                StripeAdapter->>PaymentOrchestrator: handlePSPCallback(PSPCallbackEvent)
            else Authorization succeeded immediately
                StripeAPI-->>StripeAdapter: {status: succeeded, charge_id, auth_code}
                StripeAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: succeeded, psp_charge_id}
            end

            PaymentOrchestrator->>PaymentOrchestrator: persist auth record (psp_charge_id, auth_code)
            PaymentOrchestrator->>PaymentOrchestrator: update status → processing → captured

            PaymentOrchestrator->>LedgerService: postJournal(JournalRequest{debit: merchant_receivable, credit: customer_liability, amount})
            LedgerService-->>PaymentOrchestrator: Journal{id: jrn_xxx, status: committed}

            PaymentOrchestrator->>EventBus: emit PaymentCaptured{intent_id, amount, merchant_id, psp_charge_id}

            PaymentOrchestrator-->>APIGateway: PaymentIntent{status: captured, intent_id}
            APIGateway-->>Merchant: 201 {status: captured, payment_id, amount, currency}

            EventBus->>WebhookService: consume PaymentCaptured event
            WebhookService->>Merchant: POST {merchant_webhook_url} payment_intent.succeeded {id, amount, status}
            Merchant-->>WebhookService: 200 OK
            WebhookService->>WebhookService: mark delivery: succeeded
        end
    end
```

---

## SD-002: PSP Failover Sequence

> **Trigger:** Primary PSP (Stripe) times out or returns a non-retryable error during authorization.
> **Outcome:** Payment routes to secondary PSP (Adyen), metrics updated, alert emitted.
> **Circuit Breaker:** Opens after 5 failures in 60s; half-open probe after 30s.

```mermaid
sequenceDiagram
    autonumber
    participant PaymentOrchestrator as Payment Orchestrator
    participant PSPRouter as PSP Router
    participant CircuitBreaker as Circuit Breaker (Resilience4j)
    participant StripeAdapter as Stripe Adapter (Primary)
    participant StripeAPI as Stripe API
    participant AdyenAdapter as Adyen Adapter (Secondary)
    participant AdyenAPI as Adyen API
    participant MetricsStore as Routing Metrics (Redis)
    participant AlertManager as Alert Manager
    participant LedgerService as Ledger Service
    participant EventBus as Event Bus (Kafka)

    PaymentOrchestrator->>PSPRouter: selectPSP(RoutingContext)
    PSPRouter->>CircuitBreaker: isCircuitOpen(psp: stripe)
    CircuitBreaker-->>PSPRouter: CLOSED — allow call

    PSPRouter-->>PaymentOrchestrator: PSPRoute{psp: stripe, priority: 1}
    PaymentOrchestrator->>StripeAdapter: authorize(AuthorizeRequest)
    StripeAdapter->>StripeAPI: POST /v1/payment_intents

    alt Stripe timeout (> 30s)
        StripeAPI--xStripeAdapter: ConnectTimeout / ReadTimeout
        StripeAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: timeout, psp: stripe}

        PaymentOrchestrator->>CircuitBreaker: recordFailure(psp: stripe)
        CircuitBreaker->>CircuitBreaker: failure_count=5 → state: OPEN
        CircuitBreaker->>AlertManager: emit CircuitBreakerOpened{psp: stripe}
        AlertManager->>AlertManager: page on-call via PagerDuty (P2)

        PaymentOrchestrator->>PSPRouter: failover(PSPRoute{psp: stripe}, reason: timeout)
        PSPRouter->>CircuitBreaker: isCircuitOpen(psp: adyen)
        CircuitBreaker-->>PSPRouter: CLOSED — allow call
        PSPRouter->>MetricsStore: scoreRoute(adyen, context) → 0.89
        PSPRouter-->>PaymentOrchestrator: PSPRoute{psp: adyen, priority: 2}

        PaymentOrchestrator->>AdyenAdapter: authorize(AuthorizeRequest)
        AdyenAdapter->>AdyenAPI: POST /v1/payments

        alt Adyen succeeds
            AdyenAPI-->>AdyenAdapter: {resultCode: Authorised, pspReference: xxx}
            AdyenAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: succeeded, psp_charge_id: adyen_xxx}

            PaymentOrchestrator->>MetricsStore: recordSuccess(psp: adyen, latency_ms: 420)
            PaymentOrchestrator->>MetricsStore: recordFailover(from: stripe, to: adyen, reason: timeout)

            PaymentOrchestrator->>LedgerService: postJournal(debit: merchant_receivable, credit: customer_liability)
            LedgerService-->>PaymentOrchestrator: Journal{committed}

            PaymentOrchestrator->>EventBus: emit PaymentCaptured{psp: adyen, failover: true}
            PaymentOrchestrator->>EventBus: emit PSPFailoverOccurred{from: stripe, to: adyen, reason: timeout}

        else Adyen also fails
            AdyenAPI--xAdyenAdapter: 5xx error
            AdyenAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: failed}
            PaymentOrchestrator->>AlertManager: emit AllPSPsUnavailable (P1 critical)
            AlertManager->>AlertManager: page on-call via PagerDuty (P1 — wake up)
            PaymentOrchestrator->>PaymentOrchestrator: update PaymentIntent → failed (psp_unavailable)
            PaymentOrchestrator-->>PaymentOrchestrator: return error to caller
        end

    else Stripe non-retryable error (card_declined, insufficient_funds)
        StripeAPI-->>StripeAdapter: {status: failed, decline_code: insufficient_funds}
        StripeAdapter-->>PaymentOrchestrator: AuthorizeResponse{status: declined, decline_code}
        Note over PaymentOrchestrator: Decline is terminal — no failover for card declines
        PaymentOrchestrator->>PaymentOrchestrator: update status → failed (card_declined)
        PaymentOrchestrator->>MetricsStore: recordDecline(psp: stripe, decline_code)
    end

    Note over CircuitBreaker: After 30s, circuit enters HALF_OPEN
    CircuitBreaker->>StripeAdapter: probe authorize (test transaction)
    alt Probe succeeds
        StripeAdapter-->>CircuitBreaker: success
        CircuitBreaker->>CircuitBreaker: state: CLOSED
        CircuitBreaker->>AlertManager: emit CircuitBreakerClosed{psp: stripe}
    else Probe fails
        CircuitBreaker->>CircuitBreaker: state: OPEN (reset timer)
    end
```

---

## SD-003: Wallet-to-Wallet Transfer with FX and Rollback

> **Trigger:** User calls `POST /v1/wallets/transfers` to send USD to a EUR wallet.
> **Outcome:** Source wallet debited, destination wallet credited in EUR, double-entry ledger posted.
> **Rollback:** Any failure after balance reservation triggers full compensating transactions.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant WalletAPI as Wallet API
    participant TransferOrchestrator as Transfer Orchestrator
    participant SourceWallet as Source Wallet (USD)
    participant DestWallet as Destination Wallet (EUR)
    participant FXService as FX Rate Service
    participant LedgerService as Ledger Service
    participant EventBus as Event Bus (Kafka)

    User->>WalletAPI: POST /v1/wallets/transfers {from_wallet, to_wallet, amount: 100 USD}
    WalletAPI->>TransferOrchestrator: initiateTransfer(TransferRequest)

    TransferOrchestrator->>SourceWallet: getBalance(wallet_id: src)
    SourceWallet-->>TransferOrchestrator: WalletBalance{available: 250 USD}

    alt Insufficient balance
        TransferOrchestrator-->>WalletAPI: 422 insufficient_funds
        WalletAPI-->>User: 422 {error: insufficient_funds, available: 250 USD}
    else Sufficient balance

        TransferOrchestrator->>FXService: getRate(from: USD, to: EUR)
        FXService-->>TransferOrchestrator: FXRate{rate: 0.9185, markup: 0.003, locked_until: +30s, quote_id: q_xxx}

        TransferOrchestrator->>TransferOrchestrator: calculate EUR amount = 100 * 0.9185 = 91.85 EUR

        TransferOrchestrator->>SourceWallet: reserve(amount: 100 USD, reservation_id: res_xxx)

        alt Reserve fails (concurrent debit raced ahead)
            SourceWallet-->>TransferOrchestrator: ReserveError{reason: stale_balance}
            TransferOrchestrator-->>WalletAPI: 409 concurrent_modification
            WalletAPI-->>User: 409 {error: please retry}
        else Reserve succeeds
            SourceWallet-->>TransferOrchestrator: ReservationConfirmed{reserved: 100 USD}

            TransferOrchestrator->>LedgerService: beginJournal(idempotency_key: txfr_yyy)
            LedgerService-->>TransferOrchestrator: JournalContext{journal_id: jrn_zzz}

            TransferOrchestrator->>LedgerService: postDebit(account: wallet_balance_USD, amount: 100 USD, ref: txfr_yyy)
            LedgerService-->>TransferOrchestrator: JournalLine{line_id: l1, status: pending}

            TransferOrchestrator->>LedgerService: postCredit(account: fx_conversion_transit, amount: 100 USD, ref: txfr_yyy)
            LedgerService-->>TransferOrchestrator: JournalLine{line_id: l2, status: pending}

            TransferOrchestrator->>LedgerService: postDebit(account: fx_conversion_transit, amount: 91.85 EUR, ref: txfr_yyy)
            LedgerService-->>TransferOrchestrator: JournalLine{line_id: l3, status: pending}

            TransferOrchestrator->>LedgerService: postCredit(account: wallet_balance_EUR, amount: 91.85 EUR, ref: txfr_yyy)
            LedgerService-->>TransferOrchestrator: JournalLine{line_id: l4, status: pending}

            TransferOrchestrator->>LedgerService: postDebit(account: wallet_balance_USD, amount: 0.30 USD, ref: txfr_yyy_fee)
            TransferOrchestrator->>LedgerService: postCredit(account: fx_markup_income, amount: 0.30 USD, ref: txfr_yyy_fee)

            TransferOrchestrator->>DestWallet: credit(amount: 91.85 EUR, reference: txfr_yyy)

            alt Destination credit fails (wallet frozen or closed)
                DestWallet-->>TransferOrchestrator: CreditError{reason: wallet_frozen}

                Note over TransferOrchestrator: Begin compensating transactions (SAGA rollback)
                TransferOrchestrator->>LedgerService: rollbackJournal(JournalContext)
                LedgerService-->>TransferOrchestrator: Journal{status: rolled_back}

                TransferOrchestrator->>SourceWallet: release(reservation_id: res_xxx)
                SourceWallet-->>TransferOrchestrator: ReservationReleased

                TransferOrchestrator->>EventBus: emit TransferFailed{transfer_id, reason: destination_wallet_frozen}
                TransferOrchestrator-->>WalletAPI: 422 destination_wallet_frozen
                WalletAPI-->>User: 422 {error: destination_wallet_frozen, transfer_id}

            else Destination credit succeeds
                DestWallet-->>TransferOrchestrator: WalletTransaction{id: wtxn_dest, amount: 91.85 EUR}

                TransferOrchestrator->>SourceWallet: debit(amount: 100.30 USD, reference: txfr_yyy)
                SourceWallet->>SourceWallet: release reservation res_xxx + post debit
                SourceWallet-->>TransferOrchestrator: WalletTransaction{id: wtxn_src, amount: 100.30 USD}

                TransferOrchestrator->>LedgerService: commitJournal(JournalContext)
                LedgerService->>LedgerService: validate sum(debits) == sum(credits)
                LedgerService-->>TransferOrchestrator: Journal{id: jrn_zzz, status: committed}

                TransferOrchestrator->>EventBus: emit WalletTransferCompleted{transfer_id, from_wallet, to_wallet, amount_usd: 100, amount_eur: 91.85, fx_rate: 0.9185}

                TransferOrchestrator-->>WalletAPI: TransferResult{status: completed, transfer_id}
                WalletAPI-->>User: 200 {status: completed, transfer_id, debited: 100.30 USD, credited: 91.85 EUR, rate: 0.9185}
            end
        end
    end
```

---

## Diagram Reference

| Diagram | Primary Flow | Error Paths | Async Steps |
|---|---|---|---|
| SD-001 | Auth → 3DS2 → Capture → Ledger → Webhook | Fraud block, Review hold, Stripe decline | Webhook delivery (post-response) |
| SD-002 | Stripe auth → Timeout → Circuit open → Adyen failover | All PSPs down (P1), Card decline (no failover) | Circuit half-open probe |
| SD-003 | FX quote → Reserve → Ledger → Credit → Debit → Commit | Insufficient funds, Race condition, Destination frozen | Event emission (post-commit) |

