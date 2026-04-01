# Class Diagrams — Insurance Management System

This document defines the static domain model for the P&C Insurance SaaS platform using UML class notation rendered via Mermaid. Diagrams are organized around five bounded contexts following Domain-Driven Design (DDD) principles. Each bounded context exposes a single aggregate root; all state mutations must pass through the root to preserve business invariants. Cross-context references use string identifiers only — never object references — to allow independent deployment and eventual consistency via domain events.

---

## Policy Domain

The `Policy` aggregate root governs all coverage data and endorsement history. `PolicyHolder` captures the insured party. `PolicyTerm` models the renewal chain, enabling pro-rata calculations and historical auditing. `Endorsement` records mid-term contract changes without overwriting the original coverage data.

```mermaid
classDiagram
    class Policy {
        +String policyNumber
        +String lineOfBusiness
        +String stateCode
        +Date effectiveDate
        +Date expirationDate
        +Decimal grossPremium
        +Decimal netPremium
        +PolicyStatus status
        +String agencyCode
        +String producerCode
        +bind() Policy
        +endorse(EndorsementRequest) Endorsement
        +cancel(CancellationReason) void
        +renew() Policy
        +lapse() void
        +reinstate(ReinstateRequest) void
        +calculatePremium() Decimal
        +getActiveCoverages() Coverage[]
    }

    class Coverage {
        +String coverageCode
        +String coverageType
        +Decimal limitAmount
        +Decimal deductibleAmount
        +Decimal premium
        +Boolean isMandatory
        +Date effectiveDate
        +applyEndorsement(Endorsement) void
        +computeRatedPremium(RiskScore) Decimal
        +isActive() Boolean
    }

    class Endorsement {
        +String endorsementNumber
        +String endorsementType
        +Date requestedDate
        +Date effectiveDate
        +Decimal premiumChange
        +String reason
        +String requestedById
        +EndorsementStatus status
        +apply() void
        +revert() void
        +approve() void
        +reject(String reason) void
    }

    class PolicyStatus {
        <<enumeration>>
        DRAFT
        PENDING_UNDERWRITING
        APPROVED
        DECLINED
        ACTIVE
        ENDORSED
        CANCELLED
        LAPSED
        RENEWED
        EXPIRED
        REINSTATED
    }

    class EndorsementStatus {
        <<enumeration>>
        REQUESTED
        UNDER_REVIEW
        APPROVED
        REJECTED
        APPLIED
        EFFECTIVE
    }

    class PolicyHolder {
        +String partyId
        +String firstName
        +String lastName
        +String taxId
        +String mailingAddress
        +String emailAddress
        +String phoneNumber
        +String partyType
        +Date dateOfBirth
        +verifyIdentity() Boolean
        +getActivePolicies() Policy[]
        +updateContactInfo(ContactInfo) void
    }

    class PolicyTerm {
        +String termId
        +String policyNumber
        +Date startDate
        +Date endDate
        +Integer termLengthMonths
        +Decimal annualizedPremium
        +Boolean isRenewal
        +Integer renewalSequence
        +getPreviousTerm() PolicyTerm
        +getNextTerm() PolicyTerm
        +getDaysInForce() Integer
        +computeProRataPremium(Date cancelDate) Decimal
    }

    Policy "1" *-- "1..*" Coverage : contains
    Policy "1" *-- "0..*" Endorsement : amended by
    Policy "1" --> "1" PolicyHolder : insures
    Policy "1" *-- "1..*" PolicyTerm : structured by
    Policy --> PolicyStatus : status
    Endorsement --> EndorsementStatus : status
```

**Key design decisions:**
- `Policy` is the aggregate root; all state transitions are enforced through its methods, preventing direct manipulation of child entities and ensuring minimum coverage invariants are checked.
- `Endorsement.premiumChange` records a delta value rather than recalculating gross premium, providing a complete audit trail of each incremental change across the policy term.
- `PolicyTerm` explicitly models the renewal chain; `getPreviousTerm()` allows retroactive auditing and `computeProRataPremium(cancelDate)` supports accurate mid-term cancellation refunds.
- `EndorsementStatus` is a separate enum from `PolicyStatus` because endorsements carry their own underwriting review cycle that runs in parallel to the policy lifecycle.
- `stateCode` on `Policy` drives rate/form selection and regulatory filing obligations at the domain service level without polluting individual coverages.

---

## Claims Domain

The `Claim` aggregate root manages the full FNOL-to-closure lifecycle. `ClaimLine` itemizes covered losses per coverage type. `ClaimReserve` models financial exposure using an append-only ledger pattern. `Settlement` captures agreed payment terms. `SubrogationCase` runs as a semi-independent lifecycle linked by claim reference.

```mermaid
classDiagram
    class Claim {
        +String claimNumber
        +String policyNumber
        +String termId
        +Date lossDate
        +Date reportedDate
        +String lossLocation
        +String lossDescription
        +String causeOfLoss
        +Decimal totalIncurred
        +Decimal totalPaid
        +ClaimStatus status
        +String assignedAdjusterId
        +Boolean isFraudFlagged
        +reportFNOL(FNOLRequest) Claim
        +assignAdjuster(String adjusterId) void
        +reserve(Decimal amount, String reason) ClaimReserve
        +settle(SettlementOffer) Settlement
        +deny(String reason) void
        +close() void
        +reopen(String reason) void
    }

    class ClaimLine {
        +String claimLineId
        +String claimNumber
        +String coverageCode
        +Decimal claimedAmount
        +Decimal approvedAmount
        +Decimal paidAmount
        +String itemDescription
        +String lineStatus
        +approve(Decimal approvedAmount) void
        +deny(String reason) void
        +requestDocumentation(String[] docTypes) void
        +getOutstandingAmount() Decimal
    }

    class ClaimStatus {
        <<enumeration>>
        REPORTED
        UNDER_INVESTIGATION
        RESERVED
        APPROVED
        DENIED
        DISPUTED
        SETTLEMENT_PENDING
        SETTLED
        CLOSED
        REOPENED
    }

    class Adjuster {
        +String adjusterId
        +String fullName
        +String licenseNumber
        +String[] statesLicensed
        +String specialization
        +String adjusterType
        +Integer activeCaseload
        +Integer maxCaseload
        +acceptAssignment(Claim) void
        +submitRecommendation(ClaimRecommendation) void
        +isAvailable() Boolean
        +isLicensedInState(String stateCode) Boolean
    }

    class ClaimReserve {
        +String reserveId
        +String claimNumber
        +Decimal reserveAmount
        +String reserveType
        +Date establishedDate
        +String establishedById
        +String adjustmentReason
        +Boolean isReleased
        +adjust(Decimal newAmount, String reason) ClaimReserve
        +release(String reason) void
        +getMovementHistory() ReserveMovement[]
    }

    class Settlement {
        +String settlementId
        +String claimNumber
        +Decimal settlementAmount
        +String settlementType
        +Date agreedDate
        +Date paymentDate
        +String payeeName
        +String paymentReference
        +Boolean subrogationApplicable
        +issue() void
        +voidSettlement(String reason) void
        +reissue() void
    }

    class SubrogationCase {
        +String subrogationId
        +String claimNumber
        +String tortPartyName
        +String tortPartyInsurerId
        +Decimal recoverableAmount
        +Decimal recoveredAmount
        +String status
        +Date demandLetterSentDate
        +initiate() void
        +recordRecovery(Decimal amount) void
        +settle(Decimal agreedAmount) void
        +closeCase(String reason) void
    }

    Claim "1" *-- "1..*" ClaimLine : itemized by
    Claim "1" *-- "0..*" ClaimReserve : reserves
    Claim "1" *-- "0..1" Settlement : resolved by
    Claim "1" *-- "0..1" SubrogationCase : triggers
    Claim "0..*" --> "1" Adjuster : assigned to
    Claim --> ClaimStatus : status
```

**Key design decisions:**
- `ClaimReserve` is append-only; `adjust()` creates a new record rather than mutating the existing one. This pattern is required for NAIC Schedule P statutory reporting, which tracks reserve development over time (cumulative paid vs. incurred by accident year).
- `Claim.totalIncurred` is a computed aggregate of active reserve amounts and settlement amounts, recalculated on every reserve movement to keep the claim-level exposure figure current.
- `SubrogationCase` is linked to `Claim` by string ID only; the subrogation lifecycle can outlive a closed claim and must not be blocked by claim closure rules.
- `isFraudFlagged` on `Claim` triggers an asynchronous domain event consumed by `FraudDetectionService`, avoiding synchronous coupling in the critical FNOL path.
- `Adjuster` is a shared entity (not part of the Claim aggregate); caseload limits and state licensing checks are enforced by `AssignmentService` before assignment is written to the claim.

---

## Billing Domain

Premium collection is modeled around `BillingSchedule` as the installment plan and `PremiumInvoice` as individual payment demands. `GracePeriod` is a statutory first-class entity rather than a boolean flag, capturing the regulatory basis for each activation separately for audit purposes.

```mermaid
classDiagram
    class PremiumInvoice {
        +String invoiceId
        +String policyNumber
        +String termId
        +String scheduleId
        +Integer installmentNumber
        +Decimal invoiceAmount
        +Decimal paidAmount
        +Decimal balanceDue
        +Date dueDate
        +Date issuedDate
        +InvoiceStatus status
        +generate() void
        +send() void
        +applyPayment(Payment) void
        +markOverdue() void
        +voidInvoice(String reason) void
        +getOutstandingBalance() Decimal
    }

    class Payment {
        +String paymentId
        +String invoiceId
        +Decimal amount
        +Date paymentDate
        +Date postedDate
        +String paymentStatus
        +String transactionReference
        +String externalGatewayRef
        +process() void
        +refund(Decimal amount) Payment
        +reverse(String reason) void
    }

    class PaymentMethod {
        +String methodId
        +String partyId
        +String methodType
        +String maskedAccountNumber
        +String routingNumber
        +String bankName
        +Date expiryDate
        +Boolean isDefault
        +Boolean isVerified
        +verify() Boolean
        +tokenize() String
        +deactivate() void
        +updateExpiry(Date newExpiry) void
    }

    class BillingSchedule {
        +String scheduleId
        +String policyNumber
        +String termId
        +String frequency
        +Date firstDueDate
        +Integer installmentCount
        +Decimal totalPremium
        +Decimal installmentAmount
        +Decimal downPaymentAmount
        +generateInstallments() PremiumInvoice[]
        +adjustForEndorsement(Decimal premiumDelta) void
        +recalculate() void
    }

    class GracePeriod {
        +String gracePeriodId
        +String policyNumber
        +String invoiceId
        +Date graceStartDate
        +Date graceEndDate
        +Integer graceDays
        +String status
        +String statutoryBasis
        +activate() void
        +expire() void
        +extend(Integer additionalDays) void
        +isExpired() Boolean
    }

    class InvoiceStatus {
        <<enumeration>>
        GENERATED
        SENT
        PARTIALLY_PAID
        PAID
        OVERDUE
        IN_GRACE_PERIOD
        LAPSED
        VOIDED
        REINSTATED
    }

    class BillingFrequency {
        <<enumeration>>
        MONTHLY
        QUARTERLY
        SEMI_ANNUAL
        ANNUAL
    }

    PremiumInvoice "0..*" --> "1" BillingSchedule : governed by
    PremiumInvoice "1" *-- "0..*" Payment : settled by
    PremiumInvoice "1" *-- "0..1" GracePeriod : subject to
    Payment "0..*" --> "1" PaymentMethod : via
    PremiumInvoice --> InvoiceStatus : status
    BillingSchedule --> BillingFrequency : frequency
```

**Key design decisions:**
- `PremiumInvoice.balanceDue` is stored for query performance but recalculated from `invoiceAmount - SUM(appliedPayments)` on every payment application to prevent ledger drift.
- Payment reversals never delete records; a compensating negative-amount `Payment` is created with the original `transactionReference`, satisfying double-entry ledger requirements for insurance statutory accounting.
- `GracePeriod.statutoryBasis` captures the state statute or regulation that mandates the grace period, enabling compliance reporting and defending lapse disputes with regulators.
- `BillingSchedule.adjustForEndorsement()` redistributes the premium delta across remaining unpaid installments rather than modifying historical invoices.

---

## Underwriting Domain

The underwriting context evaluates submitted applications against risk appetite rules. `RiskScore` is the structured output of an external rating engine. `UnderwritingRule` uses a DSL expression engine to support compliance officer updates without engineering deployments.

```mermaid
classDiagram
    class Application {
        +String applicationId
        +String brokerId
        +String applicantPartyId
        +String lineOfBusiness
        +String stateCode
        +String status
        +Date submittedDate
        +Date decisionDeadline
        +Map~String,Object~ riskAttributes
        +submit() void
        +withdraw(String reason) void
        +requestAdditionalInfo(String[] requiredDocs) void
        +bind() Policy
        +getRequiredForms() String[]
    }

    class RiskScore {
        +String scoreId
        +String applicationId
        +Decimal overallScore
        +Decimal frequencyScore
        +Decimal severityScore
        +RiskTier tier
        +Date calculatedAt
        +String modelVersion
        +Map~String,Decimal~ componentScores
        +getRecommendedRate() Decimal
        +isInsurable() Boolean
        +getScoreExplanation() String[]
    }

    class UnderwritingDecision {
        +String decisionId
        +String applicationId
        +DecisionType decision
        +String underwriterId
        +Date decisionDate
        +Boolean isSystemGenerated
        +Decimal approvedPremium
        +String[] declinationReasons
        +String[] appliedModifications
        +String[] requiredConditions
        +approve(Decimal premium) void
        +decline(String[] reasons) void
        +referToSenior(String notes) void
        +recordOverride(String justification) void
    }

    class UnderwritingRule {
        +String ruleId
        +String ruleName
        +String lineOfBusiness
        +String stateCode
        +String ruleExpression
        +String action
        +Integer priority
        +Boolean isActive
        +String version
        +Date effectiveDate
        +evaluate(Map~String,Object~ attributes) RuleResult
        +enable() void
        +disable() void
        +test(Map~String,Object~ sampleData) RuleResult
    }

    class RiskTier {
        <<enumeration>>
        PREFERRED
        STANDARD
        SUBSTANDARD
        HIGH_RISK
        DECLINED
    }

    class DecisionType {
        <<enumeration>>
        APPROVED
        APPROVED_WITH_CONDITIONS
        REFERRED
        DECLINED
    }

    Application "1" --> "1" RiskScore : scored by
    Application "1" --> "1" UnderwritingDecision : results in
    UnderwritingDecision "0..*" --> "0..*" UnderwritingRule : governed by
    RiskScore --> RiskTier : tier
    UnderwritingDecision --> DecisionType : decision
```

**Key design decisions:**
- `Application.riskAttributes` is an untyped `Map` rather than a fixed schema, supporting diverse lines of business (personal auto, homeowners, commercial GL) without a per-LOB class hierarchy or schema migration for new risk factors.
- `UnderwritingRule.ruleExpression` stores a DSL string evaluated by the `RuleEngine` service at runtime, enabling compliance officers to modify underwriting rules without engineering deployments. Rules carry a `version` field for backward-compatible rollback.
- `RiskScore.modelVersion` records the exact rating model version used at scoring time, supporting future recalibration impact analysis and regulatory model documentation requirements.
- `UnderwritingDecision.isSystemGenerated` distinguishes automated decisions from manual overrides; overrides require a recorded `justification` for the SOX audit trail.

---

## Reinsurance Domain

Reinsurance captures risk transfer agreements (`ReinsuranceTreaty`) and individual cession events (`CessionRecord`). Treaty matching logic lives in the `TreatyMatchingEngine` domain service, not within the treaty entity, to support multi-treaty stacking with configurable priority ordering.

```mermaid
classDiagram
    class ReinsuranceTreaty {
        +String treatyId
        +String reinsurerName
        +String reinsurerCode
        +TreatyType treatyType
        +Date inceptionDate
        +Date expirationDate
        +Decimal retentionLimit
        +Decimal cessionLimit
        +Decimal cessionPercentage
        +String[] coveredLinesOfBusiness
        +String[] coveredStateCodes
        +Boolean isActive
        +matchPolicy(Policy) Boolean
        +calculateCession(Decimal grossPremium) Decimal
        +renew() ReinsuranceTreaty
        +terminate(String reason) void
    }

    class CessionRecord {
        +String cessionId
        +String treatyId
        +String policyNumber
        +String claimNumber
        +Decimal cededPremium
        +Decimal cededLoss
        +Decimal cededReserve
        +Decimal retainedPremium
        +Date cessionDate
        +CessionStatus status
        +String bordereauPeriod
        +settle() void
        +adjust(Decimal delta, String reason) void
        +generateBordereauLine() BordereauLine
    }

    class TreatyType {
        <<enumeration>>
        QUOTA_SHARE
        SURPLUS
        EXCESS_OF_LOSS
        STOP_LOSS
        FACULTATIVE
    }

    class CessionStatus {
        <<enumeration>>
        PENDING
        CONFIRMED
        SETTLED
        ADJUSTED
        CANCELLED
    }

    ReinsuranceTreaty "1" *-- "0..*" CessionRecord : generates
    ReinsuranceTreaty --> TreatyType : type
    CessionRecord --> CessionStatus : status
```

**Key design decisions:**
- `CessionRecord` stores both premium and loss cessions in a single record to support monthly bordereau reporting to each reinsurer without requiring a separate join between premium and loss tables.
- `cessionPercentage` applies only to quota-share and surplus treaties; XOL treaties use `retentionLimit` and `cessionLimit` exclusively — the treaty entity enforces which fields are applicable by `treatyType`.
- `bordereauPeriod` (YYYYMM format) groups cession records for the monthly bordereau batch, making it straightforward to aggregate all cessions for a given reinsurer and reporting period.
- Treaty matching is delegated to `TreatyMatchingEngine` (a domain service) to support priority-ordered multi-treaty stacking scenarios that cannot be expressed within a single treaty's methods.

---

## Cross-Domain Design Principles

**Aggregate boundaries:** All cross-context references use `String` identifiers (`policyNumber`, `claimNumber`) and never object references, enabling independent service deployment and eventual consistency through domain events published to a shared event bus.

**Monetary precision:** All `Decimal` monetary fields are backed by `BigDecimal` at the implementation level using `ROUND_HALF_EVEN` (banker's rounding). This minimizes systematic accumulation error across large premium portfolios and satisfies statutory accounting accuracy requirements.

**Audit trail enforcement:** All aggregate roots extend an `AuditableEntity` base providing `createdAt`, `createdBy`, `modifiedAt`, `modifiedBy`, and `changeReason` fields, enforced via an ORM interceptor rather than per-aggregate boilerplate.

**Statutory immutability:** `ClaimReserve`, `CessionRecord`, and `GracePeriod` are append-only. Corrections are expressed as compensating records rather than in-place updates, meeting NAIC data retention requirements and SSAP No. 55 loss reserve standards.

**Event-driven integration:** State changes on `Policy`, `Claim`, and `PremiumInvoice` emit named domain events (`PolicyBound`, `ClaimFNOLReceived`, `InvoiceOverdue`) consumed by downstream bounded contexts as decoupled subscribers, avoiding synchronous cross-aggregate calls.

**NAIC reporting alignment:** The schema reflects NAIC statistical reporting categories — `lineOfBusiness` maps to NAIC line codes, `causeOfLoss` maps to NAIC cause-of-loss codes, and `CessionRecord.bordereauPeriod` aligns with Schedule F reinsurance reporting cycles.
