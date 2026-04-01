# C4 Code-Level Diagram — PolicyService & ClaimsService

This document contains C4 Level 4 (code-level) diagrams for the two core services of the Insurance Management System. Each diagram shows internal class structure, method signatures, package layout, inter-service event contracts, and dependency injection wiring.

---

## PolicyService — Code-Level Diagram

### Package Structure

```
policy-service/
├── api/
│   └── PolicyController.ts
├── application/
│   ├── PolicyApplicationService.ts
│   ├── commands/
│   │   ├── CreatePolicyApplicationCommand.ts
│   │   ├── IssuePolicyCommand.ts
│   │   ├── IssueEndorsementCommand.ts
│   │   └── CancelPolicyCommand.ts
│   └── queries/
│       ├── GetPolicyQuery.ts
│       └── ListPoliciesByBrokerQuery.ts
├── domain/
│   ├── model/
│   │   ├── Policy.ts                  ← aggregate root
│   │   ├── PolicyNumber.ts            ← value object
│   │   ├── CoverageTerms.ts           ← value object
│   │   ├── Endorsement.ts             ← entity
│   │   └── PolicyStatus.ts            ← enum
│   ├── service/
│   │   └── PolicyDomainService.ts
│   ├── factory/
│   │   └── CoverageFactory.ts
│   ├── repository/
│   │   └── PolicyRepository.ts        ← interface
│   └── events/
│       ├── PolicyIssuedEvent.ts
│       ├── EndorsementAppliedEvent.ts
│       └── PolicyCancelledEvent.ts
├── infrastructure/
│   ├── persistence/
│   │   └── PostgresPolicyRepository.ts
│   ├── adapters/
│   │   └── RulesEngineAdapter.ts
│   └── messaging/
│       └── PolicyEventPublisher.ts
└── config/
    └── PolicyServiceModule.ts         ← DI wiring
```

### Class Diagram

```mermaid
classDiagram
    class PolicyController {
        -applicationService: PolicyApplicationService
        +createApplication(dto: CreateApplicationDto): Promise~PolicyApplicationResponse~
        +issuePolicy(policyId: string, dto: IssuePolicyDto): Promise~PolicyResponse~
        +issueEndorsement(policyNumber: string, dto: EndorsementDto): Promise~EndorsementResponse~
        +cancelPolicy(policyNumber: string, dto: CancellationDto): Promise~void~
        +renewPolicy(policyNumber: string): Promise~PolicyResponse~
        +getPolicy(policyNumber: string): Promise~PolicyDetailView~
    }

    class PolicyApplicationService {
        -domainService: PolicyDomainService
        -repository: PolicyRepository
        -eventBus: EventBus
        -complianceAssertion: PolicyIssuanceComplianceAssertion
        +handleCreateApplication(cmd: CreatePolicyApplicationCommand): Promise~string~
        +handleIssuePolicy(cmd: IssuePolicyCommand): Promise~PolicyNumber~
        +handleIssueEndorsement(cmd: IssueEndorsementCommand): Promise~EndorsementId~
        +handleCancelPolicy(cmd: CancelPolicyCommand): Promise~void~
        +handleRenewalPolicy(cmd: RenewPolicyCommand): Promise~PolicyNumber~
    }

    class PolicyDomainService {
        -coverageFactory: CoverageFactory
        -rulesEngine: RulesEngineAdapter
        +evaluateApplication(application: PolicyApplication): Promise~EvaluationResult~
        +buildCoverageTerms(application: PolicyApplication): Promise~CoverageTerms~
        +applyEndorsementRules(policy: Policy, endorsement: EndorsementRequest): Promise~EndorsementValidation~
        +computeRenewalTerms(policy: Policy): Promise~RenewalTerms~
    }

    class Policy {
        -policyId: PolicyId
        -policyNumber: PolicyNumber
        -status: PolicyStatus
        -coverageTerms: CoverageTerms
        -endorsements: Endorsement[]
        -effectiveDate: LocalDate
        -expirationDate: LocalDate
        -events: DomainEvent[]
        +static create(application: PolicyApplication, terms: CoverageTerms): Policy
        +issue(issuedBy: UserId): void
        +applyEndorsement(endorsement: EndorsementRequest, approvedBy: UserId): Endorsement
        +cancel(reason: CancellationReason, cancelledBy: UserId): void
        +renew(newTerms: CoverageTerms): Policy
        +reinstate(reinstatedBy: UserId): void
        +pullDomainEvents(): DomainEvent[]
        +isActive(): boolean
        +isInGracePeriod(): boolean
    }

    class PolicyRepository {
        <<interface>>
        +findById(id: PolicyId): Promise~Policy | null~
        +findByPolicyNumber(number: PolicyNumber): Promise~Policy | null~
        +findByBroker(brokerId: BrokerId): Promise~Policy[]~
        +save(policy: Policy): Promise~void~
        +findExpiringPolicies(asOfDate: LocalDate, daysAhead: number): Promise~Policy[]~
    }

    class CoverageFactory {
        -stateFilingService: StateFilingService
        -ratingService: PremiumRatingService
        +buildFromApplication(application: PolicyApplication): Promise~CoverageTerms~
        +buildEndorsementCoverage(existing: CoverageTerms, change: CoverageChange): CoverageTerms
        +validateLimitsForState(terms: CoverageTerms, state: StateCode): ValidationResult
    }

    class RulesEngineAdapter {
        -httpClient: HttpClient
        -circuitBreaker: CircuitBreaker
        +evaluate(context: PolicyRuleContext): Promise~RulesDecision~
        +getApplicableRules(lob: LineOfBusiness, state: StateCode): Promise~Rule[]~
        +healthCheck(): Promise~boolean~
    }

    PolicyController --> PolicyApplicationService
    PolicyApplicationService --> PolicyDomainService
    PolicyApplicationService --> PolicyRepository
    PolicyDomainService --> CoverageFactory
    PolicyDomainService --> RulesEngineAdapter
    PolicyApplicationService ..> Policy : creates / loads
    PolicyRepository ..> Policy : persists
```

### Events Published by PolicyService

| Event | Trigger | Payload |
|---|---|---|
| `PolicyApplicationCreated` | Application submitted | `applicationId`, `policyNumber`, `applicantId`, `lob`, `stateCode` |
| `PolicyIssued` | Policy bound | `policyNumber`, `effectiveDate`, `expirationDate`, `premium`, `coverageTerms` |
| `EndorsementApplied` | Endorsement approved | `policyNumber`, `endorsementId`, `changeType`, `premiumImpact`, `effectiveDate` |
| `PolicyCancelled` | Policy cancelled | `policyNumber`, `cancellationReason`, `cancellationDate`, `returnPremium` |
| `PolicyRenewed` | Renewal issued | `oldPolicyNumber`, `newPolicyNumber`, `newExpirationDate`, `newPremium` |
| `PolicyLapsed` | Grace period expired | `policyNumber`, `lapseDate` |

### Events Consumed by PolicyService

| Event | Source | Purpose |
|---|---|---|
| `UnderwritingDecisionMade` | UnderwritingService | Advance application to issuance if approved |
| `PaymentReceived` | BillingService | Trigger policy activation on first payment |
| `GracePeriodExpired` | BillingService | Mark policy lapsed |
| `ReinstatementApproved` | BillingService | Restore active status |

---

## ClaimsService — Code-Level Diagram

### Package Structure

```
claims-service/
├── api/
│   └── ClaimsController.ts
├── application/
│   ├── FNOLService.ts
│   ├── commands/
│   │   ├── SubmitFNOLCommand.ts
│   │   ├── AssignAdjusterCommand.ts
│   │   ├── SetReserveCommand.ts
│   │   ├── SettleClaimCommand.ts
│   │   └── ReferToSIUCommand.ts
│   └── queries/
│       ├── GetClaimQuery.ts
│       └── ListOpenClaimsQuery.ts
├── domain/
│   ├── model/
│   │   ├── Claim.ts                   ← aggregate root (event-sourced)
│   │   ├── ClaimId.ts                 ← value object
│   │   ├── Reserve.ts                 ← value object
│   │   ├── Settlement.ts              ← entity
│   │   └── ClaimStatus.ts             ← enum
│   ├── service/
│   │   └── ClaimDomainService.ts
│   ├── repository/
│   │   └── ClaimsRepository.ts        ← interface
│   └── events/
│       ├── FNOLOpenedEvent.ts
│       ├── ReserveSetEvent.ts
│       ├── ClaimSettledEvent.ts
│       └── ClaimDeniedEvent.ts
├── infrastructure/
│   ├── persistence/
│   │   ├── EventStoreClaimsRepository.ts
│   │   └── ReserveAuditRepository.ts
│   ├── adapters/
│   │   ├── FraudGateway.ts
│   │   └── CoverageVerificationAdapter.ts
│   └── messaging/
│       └── ClaimsEventPublisher.ts
├── settlement/
│   └── SettlementService.ts
└── config/
    └── ClaimsServiceModule.ts         ← DI wiring
```

### Class Diagram

```mermaid
classDiagram
    class ClaimsController {
        -fnolService: FNOLService
        -claimDomainService: ClaimDomainService
        -settlementService: SettlementService
        +submitFNOL(dto: FNOLDto): Promise~ClaimReferenceResponse~
        +getClaimStatus(claimId: string): Promise~ClaimStatusView~
        +assignAdjuster(claimId: string, dto: AssignAdjusterDto): Promise~void~
        +setReserve(claimId: string, dto: SetReserveDto): Promise~void~
        +submitSettlement(claimId: string, dto: SettlementDto): Promise~SettlementResponse~
        +requestSIUReferral(claimId: string, dto: SIUReferralDto): Promise~void~
        +listOpenClaims(query: ListClaimsQuery): Promise~ClaimSummaryView[]~
    }

    class FNOLService {
        -claimsRepository: ClaimsRepository
        -fraudGateway: FraudGateway
        -coverageVerification: CoverageVerificationAdapter
        -eventBus: EventBus
        +submit(dto: FNOLDto): Promise~ClaimReference~
        -computeIdempotencyKey(dto: FNOLDto): string
        -verifyCoverage(dto: FNOLDto): Promise~CoverageVerificationResult~
    }

    class ClaimDomainService {
        -claimsRepository: ClaimsRepository
        -reserveCalculator: ReserveCalculator
        -fraudGateway: FraudGateway
        -eventBus: EventBus
        +processFNOL(claim: Claim): Promise~void~
        +approveForProcessing(claim: Claim): Promise~void~
        +denyOnFraud(claim: Claim, score: number, indicators: string[]): Promise~void~
        +assignAdjuster(claimId: ClaimId, adjuster: AdjusterId): Promise~void~
        +setReserve(claimId: ClaimId, basis: ReserveBasis, setBy: UserId): Promise~void~
        +subrogateRecovery(claimId: ClaimId, recovery: SubrogationRecovery): Promise~void~
    }

    class Claim {
        -claimId: ClaimId
        -policyNumber: PolicyNumber
        -status: ClaimStatus
        -reserve: Reserve
        -adjuster: AdjusterId
        -incidentDetails: IncidentDetails
        -fraudScore: number | null
        -events: DomainEvent[]
        +static openFNOL(dto: FNOLData, idempotencyKey: string): Claim
        +static reconstitute(events: DomainEvent[]): Claim
        +assignAdjuster(adjuster: AdjusterId): void
        +setReserve(amount: Money, audit: ReserveAuditEntry): void
        +awaitFraudScore(): void
        +recordFraudScore(score: number, indicators: string[]): void
        +settle(settlement: Settlement): void
        +deny(reason: DenialReason): void
        +referToSIU(referral: SIUReferral): void
        +close(): void
        +apply(event: DomainEvent): void
        +pullDomainEvents(): DomainEvent[]
    }

    class ClaimsRepository {
        <<interface>>
        +load(claimId: ClaimId): Promise~Claim~
        +save(claim: Claim): Promise~void~
        +findByIdempotencyKey(key: string): Promise~Claim | null~
        +findByPolicyNumber(policyNumber: PolicyNumber): Promise~Claim[]~
        +findOpenClaimsByAdjuster(adjuster: AdjusterId): Promise~Claim[]~
        +loadEvents(claimId: ClaimId): Promise~DomainEvent[]~
    }

    class ReserveCalculator {
        -actuarialModel: ActuarialModel
        -auditRepository: ReserveAuditRepository
        -actuaryContext: ActuaryContext
        +setInitialReserve(claim: Claim, basis: ReserveBasis): Promise~void~
        +adjustReserve(claim: Claim, newBasis: ReserveBasis, reason: string): Promise~void~
        +computeSAPReserve(claims: Claim[]): Money
        +computeGAAPReserve(claims: Claim[]): Money
    }

    class FraudGateway {
        -httpClient: HttpClient
        -circuitBreaker: CircuitBreaker
        -kafkaProducer: KafkaProducer
        +requestScoreAsync(request: FraudScoreRequest): Promise~void~
        +getScore(claimId: ClaimId): Promise~FraudScore | null~
        +updateModelFeedback(claimId: ClaimId, outcome: ClaimOutcome): Promise~void~
    }

    class SettlementService {
        -billingService: BillingServiceClient
        -paymentGateway: PaymentGatewayClient
        -coverageValidator: CoverageValidator
        -claimsRepository: ClaimsRepository
        +settle(claimId: ClaimId, proposal: SettlementProposal, approvedBy: UserId): Promise~SettlementResult~
        +void(settlementId: SettlementId, reason: string): Promise~void~
        -executeSaga(claim: Claim, settlement: SettlementProposal): Promise~void~
    }

    ClaimsController --> FNOLService
    ClaimsController --> ClaimDomainService
    ClaimsController --> SettlementService
    FNOLService --> ClaimsRepository
    FNOLService --> FraudGateway
    ClaimDomainService --> ClaimsRepository
    ClaimDomainService --> ReserveCalculator
    ClaimDomainService --> FraudGateway
    SettlementService --> ClaimsRepository
    ClaimsRepository ..> Claim : loads / persists
```

### Events Published by ClaimsService

| Event | Trigger | Payload |
|---|---|---|
| `FNOLSubmitted` | FNOL accepted | `claimId`, `policyNumber`, `incidentDate`, `incidentType`, `claimantId` |
| `ClaimFraudScoreRequested` | Post-FNOL async | `claimId`, `requestId`, `requestedAt` |
| `ClaimApprovedForProcessing` | Low fraud score | `claimId`, `fraudScore`, `adjusterAssigned` |
| `ReserveSet` | Reserve established | `claimId`, `reserveAmount`, `reserveBasis`, `setBy`, `timestamp` |
| `ReserveAdjusted` | Reserve changed | `claimId`, `priorReserve`, `newReserve`, `adjustmentReason` |
| `ClaimSettled` | Settlement disbursed | `claimId`, `settlementAmount`, `paymentRef`, `settledDate` |
| `ClaimDenied` | Denied (fraud/coverage) | `claimId`, `denialReason`, `denialCode`, `deniedBy` |
| `SIUReferralCreated` | High fraud score | `claimId`, `fraudScore`, `indicators`, `referredAt` |
| `SubrogationRecoveryRecorded` | Recovery identified | `claimId`, `recoveryAmount`, `thirdPartyId` |

### Events Consumed by ClaimsService

| Event | Source | Purpose |
|---|---|---|
| `PolicyIssued` | PolicyService | Seed coverage verification cache |
| `PolicyCancelled` | PolicyService | Flag claims on lapsed policies |
| `FraudScoreReceived` | FraudDetectionService | Route claim post-FNOL |
| `PaymentDisbursed` | BillingService | Confirm settlement payment completion |
| `ReinsuranceCessionCreated` | ReinsuranceService | Link large losses to treaty |

---

## Inter-Service Event Flow

```mermaid
sequenceDiagram
    participant Broker
    participant PolicySvc as PolicyService
    participant UWSvc as UnderwritingService
    participant ClaimsSvc as ClaimsService
    participant FraudSvc as FraudDetectionService
    participant BillingSvc as BillingService

    Broker->>PolicySvc: Submit application
    PolicySvc->>UWSvc: PolicyApplicationCreated (event)
    UWSvc-->>PolicySvc: UnderwritingDecisionMade (event)
    PolicySvc->>BillingSvc: PolicyIssued (event)
    BillingSvc-->>PolicySvc: PaymentReceived (event)

    Broker->>ClaimsSvc: Submit FNOL
    ClaimsSvc->>FraudSvc: ClaimFraudScoreRequested (event)
    FraudSvc-->>ClaimsSvc: FraudScoreReceived (event)
    ClaimsSvc->>BillingSvc: ClaimSettled (event)
    BillingSvc-->>ClaimsSvc: PaymentDisbursed (event)
```

---

## Dependency Injection Wiring

### PolicyService Module (NestJS)

```typescript
@Module({
  imports: [
    TypeOrmModule.forFeature([PolicyEntity, EndorsementEntity]),
    HttpModule,
    CqrsModule,
  ],
  controllers: [PolicyController],
  providers: [
    // Application layer
    PolicyApplicationService,
    // Domain layer
    PolicyDomainService,
    CoverageFactory,
    PolicyIssuanceComplianceAssertion,
    // Infrastructure
    {
      provide: PolicyRepository,       // interface token
      useClass: PostgresPolicyRepository,
    },
    {
      provide: RulesEngineAdapter,
      useFactory: (httpClient: HttpClient, config: ConfigService) =>
        new RulesEngineAdapter(httpClient, config.get('RULES_ENGINE_URL')),
      inject: [HttpClient, ConfigService],
    },
    PolicyEventPublisher,
    StateFilingService,
    BrokerLicenseService,
  ],
  exports: [PolicyApplicationService],
})
export class PolicyServiceModule {}
```

### ClaimsService Module (NestJS)

```typescript
@Module({
  imports: [
    EventStoreModule.forFeature([ClaimEvent]),
    TypeOrmModule.forFeature([ReserveAuditEntity]),
    KafkaModule,
    HttpModule,
    CqrsModule,
  ],
  controllers: [ClaimsController],
  providers: [
    // Application layer
    FNOLService,
    ClaimDomainService,
    SettlementService,
    // Domain layer
    ReserveCalculator,
    ActuarialModel,
    // Infrastructure
    {
      provide: ClaimsRepository,       // interface token
      useClass: EventStoreClaimsRepository,
    },
    {
      provide: FraudGateway,
      useFactory: (kafkaProducer: KafkaProducer, httpClient: HttpClient) =>
        new FraudGateway(kafkaProducer, httpClient),
      inject: [KafkaProducer, HttpClient],
    },
    ReserveAuditRepository,
    ClaimsEventPublisher,
    CoverageVerificationAdapter,
  ],
  exports: [ClaimDomainService, FNOLService],
})
export class ClaimsServiceModule {}
```

### Wiring Notes

- `PolicyRepository` and `ClaimsRepository` are always bound to their interface tokens. Tests swap in in-memory implementations by rebinding the token in the test module.
- `RulesEngineAdapter` wraps the external rules engine with a circuit breaker (Opossum). When the circuit is open, `evaluate()` returns a `MANUAL_REVIEW` decision rather than throwing.
- `FraudGateway` publishes to Kafka for score requests and falls back to synchronous HTTP if Kafka is unavailable (detected via health check at startup).
- `ReserveCalculator` injects `ActuaryContext` as a request-scoped provider so that the logged-in actuary's identity is captured in every audit trail entry without being passed explicitly through every method call.
- All `EventBus` bindings use the shared `@insurance/events` package types to ensure schema consistency across services.
