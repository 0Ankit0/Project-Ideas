# Component Diagrams — Insurance Management System

## Policy Administration System

### Component Diagram

```mermaid
flowchart TB
    subgraph PAS["Policy Administration System"]
        direction TB

        PC["PolicyController
        ────────────────
        REST entry-point.
        Validates HTTP requests,
        delegates to application
        service, maps to DTOs."]

        PAS_SVC["PolicyApplicationService
        ────────────────
        Orchestrates use-cases:
        bind, endorse, renew,
        cancel. Manages
        transaction boundaries."]

        PDS["PolicyDomainService
        ────────────────
        Enforces policy lifecycle
        invariants: state machine
        transitions, coverage
        consistency rules."]

        PR["PolicyRepository
        ────────────────
        Persists and retrieves
        Policy aggregates.
        Implements read-model
        projections for CQRS."]

        RE["RulesEngine
        ────────────────
        Evaluates eligibility
        rules, exclusions, and
        appetite rules against
        risk attributes."]

        CC["CoverageCalculator
        ────────────────
        Computes coverage limits,
        sublimits, coinsurance,
        and deductible structures
        per product line."]

        EP["EventPublisher
        ────────────────
        Publishes domain events
        (PolicyBound, PolicyCancelled,
        EndorsementApplied) to
        the message broker."]
    end

    subgraph EXT_PAS["External Dependencies"]
        DB_PAS[("Policy DB
        PostgreSQL")]
        CACHE_PAS[("Redis Cache")]
        MSG_PAS[/"Kafka Topic
        policy-events"/]
        UW_SVC["Underwriting
        Service"]
        BILLING_SVC["Billing
        Service"]
    end

    PC -->|"delegatesTo"| PAS_SVC
    PAS_SVC -->|"invokes"| PDS
    PAS_SVC -->|"invokes"| RE
    PAS_SVC -->|"invokes"| CC
    PAS_SVC -->|"persists via"| PR
    PAS_SVC -->|"publishes via"| EP
    PDS -->|"readModel via"| PR
    PR -->|"queries/writes"| DB_PAS
    PR -->|"caches reads"| CACHE_PAS
    EP -->|"produces to"| MSG_PAS
    PAS_SVC -->|"requests decision"| UW_SVC
    EP -->|"triggers invoice"| BILLING_SVC
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **PolicyController** | Accepts and validates inbound REST calls. Performs auth-scope enforcement. Returns structured API responses. |
| **PolicyApplicationService** | Coordinates multi-step use-cases (bind → issue → invoice) using domain services. Owns transaction boundaries. |
| **PolicyDomainService** | Enforces lifecycle state machine (QUOTED → BOUND → ACTIVE → RENEWED / CANCELLED). Validates domain invariants. |
| **PolicyRepository** | Ports interface for persistence. Write-model writes to PostgreSQL. Read-model projections served from Redis. |
| **RulesEngine** | Evaluates Drools-based eligibility and appetite rules. Returns decision: ACCEPT, REFER, DECLINE with reason codes. |
| **CoverageCalculator** | Applies actuarial rating factors to determine coverage limits, deductibles, and premium components. |
| **EventPublisher** | Ensures reliable at-least-once delivery of domain events to Kafka. Uses the transactional outbox pattern. |

---

## Claims Management System

### Component Diagram

```mermaid
flowchart TB
    subgraph CMS["Claims Management System"]
        direction TB

        CC2["ClaimsController
        ────────────────
        REST entry-point for FNOL
        intake, status queries,
        reserve and settlement
        actions."]

        FNOL["FNOLService
        ────────────────
        Validates first notice of
        loss, creates claim record,
        triggers coverage
        verification."]

        INV["InvestigationService
        ────────────────
        Manages investigation
        workflow: assigns adjusters,
        schedules inspections,
        tracks evidence."]

        RES["ReserveCalculator
        ────────────────
        Applies case reserve
        methodology (BF, Chain
        Ladder) to set initial
        and revised reserves."]

        SETTLE["SettlementService
        ────────────────
        Calculates net settlement
        after deductibles and
        coinsurance. Generates
        payment instructions."]

        FDE["FraudDetectionEngine
        ────────────────
        Scores claims against
        fraud indicators: SIU
        rules, ML anomaly model,
        social graph analysis."]

        SUB["SubrogationService
        ────────────────
        Identifies subrogation
        potential, tracks recovery
        actions, posts recovery
        credits to claim."]

        CAP["ClaimsEventPublisher
        ────────────────
        Emits ClaimOpened,
        ReserveChanged,
        ClaimSettled events
        to downstream systems."]
    end

    subgraph EXT_CMS["External Dependencies"]
        DB_CMS[("Claims DB
        PostgreSQL")]
        FRAUD_ML["ML Fraud
        Scoring API"]
        PAY_GW["Payment
        Gateway"]
        POLICY_SVC2["Policy
        Service"]
        MSG_CMS[/"Kafka Topic
        claims-events"/]
        NOTIF["Notification
        Service"]
    end

    CC2 -->|"delegatesTo"| FNOL
    CC2 -->|"delegatesTo"| INV
    CC2 -->|"delegatesTo"| SETTLE
    FNOL -->|"verifies coverage via"| POLICY_SVC2
    FNOL -->|"persists"| DB_CMS
    FNOL -->|"triggers"| FDE
    INV -->|"updates reserve via"| RES
    RES -->|"writes"| DB_CMS
    SETTLE -->|"dispatches payment"| PAY_GW
    SETTLE -->|"updates"| DB_CMS
    FDE -->|"calls ML"| FRAUD_ML
    FDE -->|"flags"| DB_CMS
    SUB -->|"posts recovery"| DB_CMS
    CAP -->|"produces"| MSG_CMS
    CAP -->|"triggers"| NOTIF
    SETTLE -->|"publishes via"| CAP
    FNOL -->|"publishes via"| CAP
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **ClaimsController** | Routes FNOL intake, reserve actions, settlement approvals. Enforces role-based access (adjuster, supervisor, public portal). |
| **FNOLService** | Validates that loss date falls within policy effective period, coverage applies to reported loss type, deductible not exhausted. |
| **InvestigationService** | Manages adjuster assignment queue, inspection scheduling, document requests, and investigation timeline tracking. |
| **ReserveCalculator** | Computes initial reserve using actuarial benchmarks by loss type. Triggers reserve adequacy review on status change. |
| **SettlementService** | Applies deductibles and coinsurance, checks aggregate limits, generates EFT/check payment instructions via Payment Gateway. |
| **FraudDetectionEngine** | Runs rule-based SIU screening and calls ML scoring API. Escalates high-score claims to SIU queue automatically. |
| **SubrogationService** | Identifies liable third parties, tracks demand letters and legal proceedings, posts subrogation recoveries. |
| **ClaimsEventPublisher** | Reliably emits domain events for downstream consumers (reinsurance cession, financial posting, notification dispatch). |

---

## Billing and Premium System

### Component Diagram

```mermaid
flowchart TB
    subgraph BPS["Billing and Premium System"]
        direction TB

        BC["BillingController
        ────────────────
        REST entry-point for
        invoice queries, payment
        submissions, and schedule
        retrieval."]

        INV_SVC["InvoiceService
        ────────────────
        Generates premium
        invoices on bind and
        renewal. Applies taxes,
        surcharges, and fees."]

        PGA["PaymentGatewayAdapter
        ────────────────
        Abstracts Stripe/Braintree
        for card/ACH. Handles
        tokenization, retries,
        and webhook callbacks."]

        GPS["GracePeriodService
        ────────────────
        Monitors overdue invoices.
        Sends D+1, D+10, D+29
        dunning notices before
        triggering lapse."]

        LAPSE["LapseService
        ────────────────
        Cancels policy for non-
        payment after grace period
        exhaustion. Generates
        cancellation notice."]

        REC["ReconciliationService
        ────────────────
        Matches bank remittances
        to invoices. Identifies
        short-pays, over-payments,
        and unallocated funds."]

        BILL_EP["BillingEventPublisher
        ────────────────
        Emits InvoiceCreated,
        PaymentReceived,
        PolicyLapsed events
        to downstream systems."]
    end

    subgraph EXT_BPS["External Dependencies"]
        DB_BPS[("Billing DB
        PostgreSQL")]
        PAY_GW2["Payment Gateway
        (Stripe / ACH)"]
        MSG_BPS[/"Kafka Topics
        billing-events"/]
        POLICY_SVC3["Policy
        Service"]
        NOTIF2["Notification
        Service"]
        GL["General Ledger
        (ERP)"]
    end

    BC -->|"delegatesTo"| INV_SVC
    BC -->|"delegatesTo"| PGA
    INV_SVC -->|"persists invoice"| DB_BPS
    INV_SVC -->|"publishes"| BILL_EP
    PGA -->|"tokenizes/charges"| PAY_GW2
    PGA -->|"posts payment"| DB_BPS
    PGA -->|"publishes"| BILL_EP
    GPS -->|"reads overdue"| DB_BPS
    GPS -->|"triggers"| LAPSE
    GPS -->|"triggers notices"| NOTIF2
    LAPSE -->|"cancels policy via"| POLICY_SVC3
    LAPSE -->|"publishes"| BILL_EP
    REC -->|"matches"| DB_BPS
    REC -->|"posts entries"| GL
    BILL_EP -->|"produces"| MSG_BPS
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **BillingController** | Exposes invoice lookup, payment submission, schedule generation, and direct-bill/agency-bill mode switching. |
| **InvoiceService** | Creates installment schedules on policy bind. Recalculates invoices on mid-term endorsements with pro-rata adjustments. |
| **PaymentGatewayAdapter** | Implements adapter pattern over multiple payment processors. Handles idempotent retries and reconciliation callbacks. |
| **GracePeriodService** | Runs nightly batch to detect invoices overdue past grace threshold. Queues dunning notifications via Notification Service. |
| **LapseService** | Executes policy cancellation workflow after grace period exhaustion. Generates statutory cancellation notices. |
| **ReconciliationService** | Processes daily bank statement files (BAI2/ISO 20022), matches remittances to open invoices, flags exceptions. |
| **BillingEventPublisher** | Produces events consumed by GL for revenue recognition and by Policy Service for lapse-triggered status updates. |

---

## Underwriting Engine

### Component Diagram

```mermaid
flowchart TB
    subgraph UWE["Underwriting Engine"]
        direction TB

        APP_SVC["ApplicationService
        ────────────────
        Receives submission,
        validates completeness,
        initiates underwriting
        workflow."]

        RSE["RiskScoringEngine
        ────────────────
        Computes composite risk
        score from applicant
        attributes, loss history,
        and external data."]

        UWRE["UnderwritingRulesEngine
        ────────────────
        Applies appetite rules,
        mandatory exclusions,
        and referral thresholds
        per product/state."]

        AFS["ActuarialFactorService
        ────────────────
        Retrieves rate tables,
        class factors, territory
        factors, and discount/
        surcharge schedules."]

        DEC["DecisionService
        ────────────────
        Synthesizes risk score,
        rules outcome, and
        actuarial factors into
        ACCEPT / REFER / DECLINE
        with premium indication."]

        UW_EP["UWEventPublisher
        ────────────────
        Emits ApplicationReceived,
        DecisionIssued events
        for audit trail and
        downstream routing."]
    end

    subgraph EXT_UWE["External Dependencies"]
        DB_UW[("Underwriting DB
        PostgreSQL")]
        CREDIT_API["Credit Bureau
        API (LexisNexis)"]
        MVR_API["MVR / CLUE
        API"]
        CLUE_API["ISO / Verisk
        Loss History"]
        MSG_UW[/"Kafka Topic
        uw-events"/]
        POLICY_SVC4["Policy
        Service"]
    end

    APP_SVC -->|"triggers"| RSE
    APP_SVC -->|"triggers"| UWRE
    RSE -->|"fetches credit"| CREDIT_API
    RSE -->|"fetches MVR"| MVR_API
    RSE -->|"fetches loss history"| CLUE_API
    RSE -->|"feeds score to"| DEC
    UWRE -->|"applies rules to"| DEC
    AFS -->|"provides factors to"| DEC
    DEC -->|"persists decision"| DB_UW
    DEC -->|"publishes via"| UW_EP
    DEC -->|"triggers bind"| POLICY_SVC4
    UW_EP -->|"produces"| MSG_UW
    APP_SVC -->|"persists submission"| DB_UW
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **ApplicationService** | Accepts new business submissions and renewal applications. Validates required fields per state filing requirements. |
| **RiskScoringEngine** | Aggregates credit score, prior loss history (CLUE), motor vehicle record (MVR), and property inspection data into a composite risk score (0–100). |
| **UnderwritingRulesEngine** | Evaluates mandatory decline rules (e.g., FAIR Plan referrals), referral conditions (score > 70), and appetite restrictions by state/territory. |
| **ActuarialFactorService** | Retrieves versioned rate tables. Applies ISO/NCCI base rates, class codes, territory multipliers, credits, and surcharges. |
| **DecisionService** | Produces underwriting decision with premium indication. Straight-Through-Processing (STP) for low-risk; queue for manual referral. |
| **UWEventPublisher** | Emits events consumed by Broker Portal (decision notification), Policy Service (bind authorization), and Compliance (audit log). |

---

## Cross-System Event Flow

```mermaid
flowchart LR
    UWE2["Underwriting
    Engine"]
    PAS2["Policy
    Administration"]
    BPS2["Billing &
    Premium"]
    CMS2["Claims
    Management"]
    NOTIF3["Notification
    Service"]
    GL2["General
    Ledger"]
    REINSU["Reinsurance
    Module"]

    UWE2 -->|"DecisionIssued"| PAS2
    PAS2 -->|"PolicyBound"| BPS2
    PAS2 -->|"PolicyBound"| REINSU
    PAS2 -->|"PolicyCancelled"| BPS2
    BPS2 -->|"PaymentReceived"| PAS2
    BPS2 -->|"PolicyLapsed"| PAS2
    BPS2 -->|"InvoiceCreated"| NOTIF3
    BPS2 -->|"PaymentReceived"| GL2
    CMS2 -->|"ClaimSettled"| GL2
    CMS2 -->|"ClaimSettled"| REINSU
    PAS2 -->|"PolicyBound"| NOTIF3
    CMS2 -->|"ClaimOpened"| NOTIF3
```
