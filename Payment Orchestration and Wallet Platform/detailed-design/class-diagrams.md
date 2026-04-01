# Class Diagrams — Payment Orchestration and Wallet Platform

> **Scope:** UML class diagrams for the four core domain aggregates: Payment Orchestration,
> Wallet, Fraud Engine, and Settlement Engine. Visibility modifiers: `+` public, `-` private,
> `#` protected. All monetary values use the `Money` value object (amount + currency).

---

## CD-001: Payment Orchestration Domain

### 1.1 PaymentOrchestrator and PSP Routing

```mermaid
classDiagram
    class PaymentOrchestrator {
        -UUID id
        -PaymentIntentRepository intentRepo
        -PSPRouter pspRouter
        -FraudService fraudService
        -VaultService vaultService
        -LedgerService ledgerService
        -EventPublisher eventPublisher
        -IdempotencyStore idempotencyStore
        +createIntent(CreateIntentRequest) PaymentIntent
        +confirmIntent(UUID intentId, ConfirmRequest) PaymentIntent
        +capturePayment(UUID intentId, CaptureRequest) Capture
        +cancelPayment(UUID intentId, CancelRequest) PaymentIntent
        +routePayment(PaymentIntent) PSPRoute
        +handlePSPCallback(PSPCallbackEvent) void
        -validateIdempotency(String idempotencyKey) void
        -persistIntentTransition(PaymentIntent, PaymentStatus) void
    }

    class PSPRouter {
        -List~PSPAdapter~ adapters
        -RoutingConfigCache configCache
        -CircuitBreakerRegistry cbRegistry
        -RoutingMetricsStore metricsStore
        +selectPSP(RoutingContext) PSPRoute
        +failover(PSPRoute, FailoverReason) PSPRoute
        +scoreRoute(PSPAdapter, RoutingContext) Float
        -applyStrategy(RoutingStrategy, List~PSPAdapter~) PSPAdapter
        -updateMetrics(PSPRoute, RouteOutcome) void
        -isCircuitOpen(String pspCode) Boolean
    }

    class RoutingContext {
        +Money amount
        +String currency
        +String merchantId
        +String paymentMethodType
        +String countryCode
        +Boolean requires3DS
        +RoutingStrategy strategy
    }

    class PSPRoute {
        +String pspCode
        +String adapterClass
        +Integer priority
        +Float successScore
        +Float latencyMs
        +Float costBps
        +Instant selectedAt
    }

    class PSPAdapter {
        <<interface>>
        +authorize(AuthorizeRequest) AuthorizeResponse
        +capture(CaptureRequest) CaptureResponse
        +refund(RefundRequest) RefundResponse
        +cancel(CancelRequest) CancelResponse
        +getCapabilities() PSPCapabilities
    }

    class StripeAdapter {
        -StripeHttpClient httpClient
        -String apiKey
        -String webhookSecret
        +authorize(AuthorizeRequest) AuthorizeResponse
        +capture(CaptureRequest) CaptureResponse
        +refund(RefundRequest) RefundResponse
        +cancel(CancelRequest) CancelResponse
        +getCapabilities() PSPCapabilities
        -buildStripePaymentIntent(AuthorizeRequest) Map
        -parseStripeResponse(StripeResponse) AuthorizeResponse
    }

    class AdyenAdapter {
        -AdyenClient adyenClient
        -String merchantAccount
        -String hmacKey
        +authorize(AuthorizeRequest) AuthorizeResponse
        +capture(CaptureRequest) CaptureResponse
        +refund(RefundRequest) RefundResponse
        +cancel(CancelRequest) CancelResponse
        +getCapabilities() PSPCapabilities
        -buildAdyenPaymentRequest(AuthorizeRequest) PaymentRequest
    }

    class BraintreeAdapter {
        -BraintreeGateway gateway
        -String merchantId
        +authorize(AuthorizeRequest) AuthorizeResponse
        +capture(CaptureRequest) CaptureResponse
        +refund(RefundRequest) RefundResponse
        +cancel(CancelRequest) CancelResponse
        +getCapabilities() PSPCapabilities
    }

    class PaymentIntent {
        +UUID id
        +String idempotencyKey
        +UUID merchantId
        +UUID customerId
        +Money amount
        +String currency
        +PaymentIntentStatus status
        +String pspCode
        +String pspIntentId
        +Map~String,String~ metadata
        +Instant createdAt
        +Instant updatedAt
        +Instant expiresAt
    }

    PaymentOrchestrator --> PSPRouter : uses
    PaymentOrchestrator --> FraudService : calls
    PaymentOrchestrator --> VaultService : calls
    PaymentOrchestrator --> LedgerService : calls
    PSPRouter --> PSPAdapter : selects
    PSPAdapter <|.. StripeAdapter : implements
    PSPAdapter <|.. AdyenAdapter : implements
    PSPAdapter <|.. BraintreeAdapter : implements
    PSPRouter --> RoutingContext : receives
    PSPRouter --> PSPRoute : returns
    PaymentOrchestrator --> PaymentIntent : creates/updates
```

---

## CD-002: Wallet Aggregate

```mermaid
classDiagram
    class Wallet {
        +UUID id
        +UUID ownerId
        +WalletOwnerType ownerType
        +String currency
        +WalletStatus status
        +WalletBalance balance
        +List~WalletTransaction~ transactions
        +Instant createdAt
        +Instant updatedAt
        +credit(Money amount, String reference) WalletTransaction
        +debit(Money amount, String reference) WalletTransaction
        +transfer(Wallet target, Money amount, String reference) TransferResult
        +freeze(String reason) void
        +unfreeze(String approvedBy) void
        -ensureActive() void
        -ensureSufficientBalance(Money amount) void
        -applyDomainEvent(WalletDomainEvent) void
    }

    class WalletBalance {
        -Money totalBalance
        -Money reservedBalance
        +reserve(Money amount, String reservationId) void
        +release(String reservationId) void
        +getAvailable() Money
        +getReserved() Money
        +getTotal() Money
        -validateReservation(String reservationId) void
    }

    class WalletTransaction {
        +UUID id
        +UUID walletId
        +WalletTransactionType type
        +Money amount
        +Money balanceBefore
        +Money balanceAfter
        +String reference
        +String externalReference
        +WalletTransactionStatus status
        +Instant createdAt
        +Map~String,String~ metadata
    }

    class BalanceReservation {
        +String reservationId
        +Money amount
        +Instant reservedAt
        +Instant expiresAt
        +ReservationStatus status
    }

    class Money {
        +BigDecimal amount
        +String currency
        +Money add(Money other) Money
        +Money subtract(Money other) Money
        +Money multiply(BigDecimal factor) Money
        +Boolean equals(Money other) Boolean
        +Boolean isPositive() Boolean
        +Boolean isZero() Boolean
        +String formatted() String
        -validateSameCurrency(Money other) void
    }

    class TransferResult {
        +UUID transferId
        +WalletTransaction sourceDebit
        +WalletTransaction destinationCredit
        +FXConversion fxConversion
        +TransferStatus status
    }

    Wallet "1" *-- "1" WalletBalance : contains
    Wallet "1" *-- "many" WalletTransaction : records
    WalletBalance "1" *-- "many" BalanceReservation : tracks
    WalletTransaction --> Money : uses
    Wallet --> TransferResult : produces
    Money --* WalletBalance : composes
```

---

## CD-003: Fraud Engine

```mermaid
classDiagram
    class FraudEngine {
        -VelocityChecker velocityChecker
        -RuleEngine ruleEngine
        -MLScorer mlScorer
        -AlertManager alertManager
        -FraudCaseRepository caseRepo
        +score(FraudRequest) FraudDecision
        +checkVelocity(String entityId, EntityType type) VelocityResult
        +applyRules(FraudRequest) List~RuleResult~
        +flagAlert(FraudAlert) void
        -aggregateSignals(VelocityResult, List~RuleResult~, Float) FraudDecision
        -shouldCreateCase(FraudDecision) Boolean
    }

    class FraudDecision {
        +FraudOutcome outcome
        +Float riskScore
        +String decisionReason
        +List~String~ triggeredRules
        +Boolean requiresReview
        +Instant decidedAt
    }

    class VelocityChecker {
        -RedisClient redisClient
        -VelocityConfigRepository configRepo
        +checkHourly(String key, Integer threshold) Boolean
        +checkDaily(String key, Integer threshold) Boolean
        +checkWeekly(String key, Integer threshold) Boolean
        +incrementCounters(String key, List~VelocityWindow~ windows) void
        -buildRedisKey(String entity, VelocityWindow window) String
        -getWindowExpiry(VelocityWindow window) Duration
    }

    class RuleEngine {
        -List~FraudRule~ rules
        -RuleRepository ruleRepo
        +evaluate(FraudRequest) List~RuleResult~
        +addRule(FraudRule rule) void
        +removeRule(String ruleId) void
        +reloadRules() void
        -sortByPriority(List~FraudRule~) List~FraudRule~
    }

    class MLScorer {
        -OnnxModelClient modelClient
        -FeatureExtractor featureExtractor
        -ModelRegistry modelRegistry
        +predict(FraudRequest) Float
        +getFeatures(FraudRequest) FeatureVector
        -loadModel(String modelVersion) OnnxModel
        -normalizeFeatures(FeatureVector) Float[]
    }

    class FraudRule {
        <<interface>>
        +String getRuleId()
        +String getName()
        +Integer getPriority()
        +RuleResult evaluate(FraudRequest context)
        +Boolean isEnabled()
    }

    class AmountThresholdRule {
        -BigDecimal maxAmountUSD
        -String currency
        +String getRuleId()
        +RuleResult evaluate(FraudRequest context)
        -convertToUSD(Money amount) BigDecimal
    }

    class CountryBlocklistRule {
        -Set~String~ blockedCountryCodes
        -String blocklistVersion
        +String getRuleId()
        +RuleResult evaluate(FraudRequest context)
        -isBlocked(String countryCode) Boolean
    }

    class BINBlocklistRule {
        -Set~String~ blockedBINPrefixes
        +String getRuleId()
        +RuleResult evaluate(FraudRequest context)
        -matchesBIN(String cardNumber) Boolean
    }

    class AlertManager {
        -KafkaProducer kafkaProducer
        -PagerDutyClient pagerDutyClient
        -AlertRepository alertRepo
        +createAlert(FraudAlert) void
        +escalate(UUID alertId, EscalationLevel level) void
        +dismiss(UUID alertId, String dismissedBy) void
    }

    FraudEngine --> VelocityChecker : uses
    FraudEngine --> RuleEngine : uses
    FraudEngine --> MLScorer : uses
    FraudEngine --> AlertManager : uses
    FraudEngine --> FraudDecision : produces
    RuleEngine --> FraudRule : evaluates
    FraudRule <|.. AmountThresholdRule : implements
    FraudRule <|.. CountryBlocklistRule : implements
    FraudRule <|.. BINBlocklistRule : implements
```

---

## CD-004: Settlement Engine

```mermaid
classDiagram
    class SettlementEngine {
        -ReconciliationService reconService
        -FeeCalculator feeCalculator
        -LedgerWriter ledgerWriter
        -PSPFileGenerator fileGenerator
        -SettlementBatchRepository batchRepo
        -EventPublisher eventPublisher
        +runBatch(SettlementBatchRequest) SettlementBatch
        +aggregateCaptures(LocalDate cutoffDate, String pspCode) List~CaptureAggregate~
        +calculateFees(List~CaptureAggregate~) List~FeeResult~
        +submitToPSP(SettlementBatch) PSPSubmissionResult
        -validateCutoffTime(SettlementBatchRequest) void
        -lockBatchForProcessing(UUID batchId) void
    }

    class SettlementBatch {
        +UUID id
        +LocalDate settlementDate
        +String pspCode
        +String currency
        +Money grossAmount
        +Money totalFees
        +Money netAmount
        +SettlementBatchStatus status
        +Integer captureCount
        +String pspBatchReference
        +Instant submittedAt
        +Instant confirmedAt
    }

    class CaptureAggregate {
        +String merchantId
        +String pspCode
        +String currency
        +String paymentMethodType
        +Money totalGrossAmount
        +Integer captureCount
        +List~UUID~ captureIds
        +LocalDate captureDate
    }

    class ReconciliationService {
        -LedgerReader ledgerReader
        -PSPFileParser pspFileParser
        -BankStatementParser bankStatementParser
        -BreakRepository breakRepo
        +matchRecords(UUID batchId) ReconciliationResult
        +detectBreaks(LedgerView, PSPView, BankView) List~ReconciliationBreak~
        +classifyBreak(ReconciliationBreak) BreakType
        +resolveBreak(UUID breakId, Resolution resolution) void
        -threeWayMatch(LedgerRecord, PSPRecord, BankRecord) MatchResult
    }

    class FeeCalculator {
        -FeeRuleRepository feeRuleRepo
        +calculate(CaptureAggregate capture, FeeSchedule schedule) FeeResult
        +applyTieredFees(Money amount, List~FeeTier~ tiers) Money
        -lookupFeeSchedule(String merchantId, String pspCode) FeeSchedule
        -applyMinimumFee(Money fee, Money minFee) Money
    }

    class FeeResult {
        +String merchantId
        +Money grossAmount
        +Money processingFee
        +Money chargebackFee
        +Money refundFee
        +Money netAmount
        +String feeScheduleId
    }

    class LedgerWriter {
        -JournalRepository journalRepo
        -AccountRepository accountRepo
        -TransactionManager txManager
        +postDebit(AccountCode account, Money amount, String ref) JournalLine
        +postCredit(AccountCode account, Money amount, String ref) JournalLine
        +beginJournal(String idempotencyKey) JournalContext
        +commitJournal(JournalContext ctx) Journal
        +rollbackJournal(JournalContext ctx) void
        -validateDoubleEntry(JournalContext ctx) void
        -ensureIdempotent(String key) void
    }

    class ReconciliationBreak {
        +UUID id
        +BreakType type
        +String ledgerRef
        +String pspRef
        +String bankRef
        +Money ledgerAmount
        +Money pspAmount
        +Money bankAmount
        +BreakStatus status
        +String assignedTo
    }

    SettlementEngine --> ReconciliationService : uses
    SettlementEngine --> FeeCalculator : uses
    SettlementEngine --> LedgerWriter : uses
    SettlementEngine --> SettlementBatch : produces
    SettlementEngine --> CaptureAggregate : aggregates
    FeeCalculator --> FeeResult : returns
    ReconciliationService --> ReconciliationBreak : detects
```

---

## Design Notes

| Class | Pattern | Key Design Decision |
|---|---|---|
| `PaymentOrchestrator` | Application Service | Orchestrates cross-domain calls; holds no business state |
| `PSPRouter` | Strategy + Circuit Breaker | Strategy pattern for routing; Resilience4j circuit breakers per PSP |
| `PSPAdapter` | Adapter / Port | Anti-corruption layer isolating PSP API differences |
| `Wallet` | Aggregate Root (DDD) | All balance mutations go through `Wallet`; invariants enforced in domain |
| `Money` | Value Object | Immutable; arithmetic methods return new instances; currency-aware |
| `FraudEngine` | Facade | Composes velocity, rules, and ML signals into single decision |
| `RuleEngine` | Chain of Responsibility | Ordered rule evaluation; short-circuits on BLOCK decision |
| `LedgerWriter` | Unit of Work | Journal context tracks debit/credit pairs before commit |
| `SettlementEngine` | Domain Service | Stateless; operates on settlement batch aggregate |

