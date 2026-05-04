# C4 Diagrams — Payment Orchestration and Wallet Platform

These diagrams describe the payment platform from context through container decomposition, with emphasis on event-driven orchestration, PSP adapters, wallet and ledger isolation, reconciliation, payout controls, and PCI segmentation.

## 1. C1 — System Context

```mermaid
flowchart LR
    Merchant[Merchant backend and admin console]
    Customer[Customer web or mobile client]
    PSP[PSP and acquirer partners]
    Bank[Bank rails and virtual account partners]
    KYC[KYC and AML providers]
    Ops[Risk, finance, and compliance operators]
    POWP[Payment Orchestration and Wallet Platform]

    Merchant --> POWP
    Customer --> POWP
    POWP --> PSP
    POWP --> Bank
    POWP --> KYC
    Ops --> POWP
```

**Context notes:**
- Merchants integrate once with the platform instead of integrating independently with each PSP.
- Customers interact through merchant channels or hosted payment flows.
- Banks and PSPs are external systems of execution; the platform remains the internal system of record for orchestration, ledger, and audit history.

## 2. C2 — Container View

```mermaid
flowchart TB
    subgraph Clients[External clients]
        MerchantApp[Merchant API client]
        MerchantUI[Merchant console]
        Checkout[Customer checkout]
    end

    subgraph Edge[Edge layer]
        Gateway[API Gateway and WAF]
        Auth[Auth and tenant policy]
    end

    subgraph Core[Core services]
        Orchestrator[Payment orchestration]
        Wallet[Wallet service]
        Ledger[Ledger service]
        Risk[Fraud and risk service]
        Payout[Payout service]
        Settlement[Settlement service]
        Recon[Reconciliation service]
        Webhook[Webhook delivery]
        Vault[Vault and tokenization]
    end

    subgraph Data[Platform data]
        Pg[(PostgreSQL write stores)]
        Redis[(Redis)]
        Kafka[(Kafka event bus)]
        S3[(Object storage)]
    end

    subgraph Partners[External partners]
        PSPAdapters[PSP adapters]
        BankAdapters[Bank rail adapters]
        KYCAdapters[KYC and AML adapters]
    end

    MerchantApp --> Gateway
    MerchantUI --> Gateway
    Checkout --> Gateway
    Gateway --> Auth
    Gateway --> Orchestrator
    Gateway --> Wallet
    Gateway --> Payout
    Gateway --> Recon
    Orchestrator --> Risk
    Orchestrator --> Vault
    Orchestrator --> Ledger
    Orchestrator --> PSPAdapters
    Wallet --> Ledger
    Wallet --> Risk
    Wallet --> Kafka
    Payout --> Ledger
    Payout --> BankAdapters
    Payout --> KYCAdapters
    Settlement --> Ledger
    Settlement --> PSPAdapters
    Settlement --> S3
    Recon --> Ledger
    Recon --> PSPAdapters
    Recon --> BankAdapters
    Recon --> S3
    Webhook --> Kafka
    Orchestrator --> Kafka
    Ledger --> Kafka
    Settlement --> Kafka
    Gateway --> Redis
    Orchestrator --> Redis
    Risk --> Redis
    Orchestrator --> Pg
    Wallet --> Pg
    Ledger --> Pg
    Payout --> Pg
    Settlement --> Pg
    Recon --> Pg
    Vault --> Pg
```

### Container responsibilities

| Container | Responsibilities | Scaling profile |
|---|---|---|
| API Gateway | Authentication, rate limiting, request shaping, WAF, tenant routing | Scale on incoming RPS |
| Payment Orchestration | Payment intent state machine, routing, PSP retry logic, saga coordination | Scale on online transaction TPS |
| Wallet Service | Wallet commands, balance read model, freeze and reserve logic | Scale on wallet command volume |
| Ledger Service | Double-entry journals, account balances, posting API, GL export | Scale on financial event write rate |
| Settlement Service | Batch construction, fee aggregation, provider settlement integration | Scale on nightly batch size |
| Reconciliation Service | Ledger vs PSP vs bank matching, break queue, attestation | Scale on file ingestion and match volume |
| Payout Service | Reserve funds, compliance gates, bank dispatch, return handling | Scale on payout count and payout schedule bursts |
| Fraud and Risk | Real-time rules, velocity checks, manual review, case management | Scale on scoring latency budget |
| Vault and Tokenization | Token lifecycle and PCI-scoped card storage | Isolated scaling inside PCI zone |

## 3. C3 — Payment Orchestration Container Decomposition

```mermaid
flowchart LR
    API[Command API] --> Idem[Idempotency guard]
    Idem --> Saga[Saga coordinator]
    Saga --> Router[Routing engine]
    Saga --> Risk[Risk gateway]
    Saga --> Vault[Tokenization client]
    Saga --> PSP[PSP execution manager]
    Saga --> Ledger[Ledger command client]
    Saga --> Outbox[Outbox writer]
    Outbox --> Kafka[Kafka topics]
    Router --> Rules[Merchant rule store]
    Router --> Health[Provider health cache]
    PSP --> Attempts[Attempt store]
```

**Decomposition notes:**
- `Idempotency guard` is a synchronous gate, not an async best effort cache.
- `Saga coordinator` owns the authoritative payment state machine.
- `PSP execution manager` is responsible for ambiguous outcome handling, provider polling, and fallback eligibility.

## 4. C3 — Finance Domain Decomposition

```mermaid
flowchart LR
    Capture[Capture event] --> LedgerPost[Ledger posting]
    LedgerPost --> Pending[Merchant funds pending settlement]
    Pending --> Batch[Settlement batch builder]
    Batch --> ProviderFile[Provider settlement artifact]
    ProviderFile --> Recon[Three way reconciliation]
    BankFile[Bank statement artifact] --> Recon
    LedgerSnap[Ledger snapshot] --> Recon
    Recon --> Breaks[Break queue]
    Recon --> PayoutGate[Payout release gate]
```

## 5. Trust Boundaries

| Boundary | Included components | Controls |
|---|---|---|
| Public edge | Gateway, WAF, CDN, webhook ingress | TLS 1.3, bot protection, request signing, DDoS controls |
| Core services | Orchestration, wallet, ledger, payout, settlement, recon | mTLS, service mesh authz, per-service IAM, audit logging |
| PCI zone | Vault, HSM integration, token lifecycle jobs | Network isolation, dedicated secrets, outbound allowlist only |
| Finance evidence zone | Settlement files, bank files, evidence packages, attestation exports | Object lock, restricted IAM roles, checksum validation |

## 6. Design Consequences

- Stateless services and Kafka-backed events allow replay and recovery without distributed transactions.
- Ledger and wallet are separate bounded contexts: wallet owns customer-facing balances, ledger owns accounting truth.
- Settlement and reconciliation are decoupled from online authorization so PSP or bank file delays do not block checkout.
