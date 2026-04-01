# Implementation Guidelines — Insurance Management System

P&C Insurance SaaS platform covering policy lifecycle, underwriting, claims, premium billing, reinsurance, broker portal, and NAIC regulatory reporting.

---

## Architecture Principles

### Domain-Driven Design

All business logic lives in the domain layer. Services are organized around bounded contexts that mirror the insurance value chain:

| Bounded Context | Core Aggregates |
|---|---|
| Policy Administration | `Policy`, `Endorsement`, `Cancellation` |
| Underwriting | `UnderwritingSubmission`, `RiskScore`, `Decision` |
| Claims | `Claim`, `Coverage`, `Reserve`, `Settlement` |
| Billing | `Invoice`, `PaymentPlan`, `GracePeriod` |
| Reinsurance | `Treaty`, `Cession`, `Bordereau` |

Each bounded context owns its data store. Cross-context communication happens through **domain events** only — never through direct foreign-key joins or shared repositories.

### CQRS

Commands mutate state; queries read from projections. Separate command handlers from query handlers at the application-service layer:

```
src/policy/
  commands/          # CreatePolicyCommand, IssueEndorsementCommand
  queries/           # GetPolicyByNumberQuery, ListActivePoliciesQuery
  command-handlers/  # CreatePolicyHandler, EndorsementHandler
  query-handlers/    # PolicyQueryHandler (reads from read model)
  read-models/       # PolicySummaryView, PolicyDetailView
```

Never allow a command handler to call a query handler. Never allow a query handler to trigger side effects.

### Event Sourcing for Claims

The `Claim` aggregate uses event sourcing. Every state transition is persisted as an immutable event in the claims event store before the current state projection is updated.

```typescript
// Claim aggregate — event-sourced root
class Claim {
  private events: DomainEvent[] = [];

  openFNOL(fnol: FNOLData): void {
    this.applyAndRecord(new FNOLOpenedEvent(fnol));
  }

  assignAdjuster(adjuster: AdjusterId): void {
    if (this.status !== ClaimStatus.OPEN) {
      throw new InvalidClaimStateError(this.status, 'assignAdjuster');
    }
    this.applyAndRecord(new AdjusterAssignedEvent(adjuster, this.claimId));
  }

  private applyAndRecord(event: DomainEvent): void {
    this.apply(event);       // mutate in-memory state
    this.events.push(event); // stage for persistence
  }
}
```

Claim state is rebuilt by replaying all stored events in order — the event store is the source of truth; the projected table is a read cache only.

---

## Insurance Domain Coding Patterns

### Money Type for Premium Amounts

**Never use `float` or `double` for monetary values.** IEEE 754 floating-point arithmetic produces rounding errors that compound across invoices, cessions, and statutory reserves.

```typescript
import { BigDecimal } from 'big.js';

class Money {
  private readonly amount: BigDecimal;
  private readonly currency: CurrencyCode;

  constructor(amount: string | BigDecimal, currency: CurrencyCode = 'USD') {
    this.amount = new BigDecimal(amount);
    this.currency = currency;
  }

  add(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.amount.plus(other.amount), this.currency);
  }

  multiply(factor: string | number): Money {
    return new Money(this.amount.times(new BigDecimal(factor)), this.currency);
  }

  roundToNearestCent(): Money {
    return new Money(this.amount.toFixed(2, BigDecimal.roundHalfEven), this.currency);
  }

  equals(other: Money): boolean {
    return this.currency === other.currency && this.amount.eq(other.amount);
  }

  private assertSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new CurrencyMismatchError(this.currency, other.currency);
    }
  }
}

// Usage — never interpolate raw floats
const basePremium = new Money('1234.56');
const surcharge   = new Money('87.50');
const total       = basePremium.add(surcharge).roundToNearestCent();
```

Use `BigDecimal.roundHalfEven` (banker's rounding) for regulatory reporting to comply with NAIC SAP rounding conventions.

### PolicyNumber Value Object

Policy numbers encode line of business, state, and sequence. Treat them as value objects — not plain strings — to enforce format invariants at the boundary.

```typescript
class PolicyNumber {
  private static readonly PATTERN = /^[A-Z]{2}-[A-Z]{2,3}-\d{8}$/;
  // Format: <LOB>-<STATE>-<SEQUENCE>
  // Example: HO-TX-00012345

  private constructor(private readonly value: string) {}

  static of(raw: string): PolicyNumber {
    const normalized = raw.trim().toUpperCase();
    if (!PolicyNumber.PATTERN.test(normalized)) {
      throw new InvalidPolicyNumberError(raw);
    }
    return new PolicyNumber(normalized);
  }

  get lineOfBusiness(): LineOfBusiness {
    return this.value.split('-')[0] as LineOfBusiness;
  }

  get stateCode(): StateCode {
    return this.value.split('-')[1] as StateCode;
  }

  toString(): string { return this.value; }

  equals(other: PolicyNumber): boolean {
    return this.value === other.value;
  }
}
```

### Coverage Limit and Deductible Validation

Validate coverage limits against state minimums and product filed rates at domain construction time:

```typescript
class CoverageTerms {
  constructor(
    readonly limit: Money,
    readonly deductible: Money,
    readonly lineOfBusiness: LineOfBusiness,
    readonly stateCode: StateCode
  ) {
    this.validate();
  }

  private validate(): void {
    const rules = StateCoverageRules.for(this.stateCode, this.lineOfBusiness);

    if (this.limit.lessThan(rules.minimumLimit)) {
      throw new CoverageLimitBelowMinimumError(this.limit, rules.minimumLimit);
    }
    if (this.deductible.greaterThan(this.limit)) {
      throw new DeductibleExceedsLimitError(this.deductible, this.limit);
    }
    if (rules.allowedDeductibles && !rules.allowedDeductibles.includes(this.deductible)) {
      throw new DeductibleNotFiledError(this.deductible, this.stateCode);
    }
  }
}
```

### Regulatory Compliance Assertion Pattern

Encapsulate multi-step regulatory pre-conditions in a `ComplianceAssertion` that throws a structured `RegulatoryViolationError` with the NAIC rule reference:

```typescript
class PolicyIssuanceComplianceAssertion {
  constructor(
    private readonly filingService: StateFilingService,
    private readonly licenseService: BrokerLicenseService
  ) {}

  async assertCompliant(application: PolicyApplication): Promise<void> {
    const violations: RegulatoryViolation[] = [];

    const rateFilingStatus = await this.filingService.getRateFiling(
      application.stateCode,
      application.lineOfBusiness,
      application.effectiveDate
    );
    if (!rateFilingStatus.isApproved) {
      violations.push({
        rule: 'NAIC-MDL-154',
        description: `Rate form not filed/approved in ${application.stateCode}`,
        severity: 'BLOCKING',
      });
    }

    const brokerLicense = await this.licenseService.getLicense(
      application.brokerId,
      application.stateCode
    );
    if (!brokerLicense.isActiveFor(application.lineOfBusiness)) {
      violations.push({
        rule: 'STATE-BROKER-LICENSE',
        description: `Broker ${application.brokerId} not licensed for ${application.lineOfBusiness} in ${application.stateCode}`,
        severity: 'BLOCKING',
      });
    }

    if (violations.some(v => v.severity === 'BLOCKING')) {
      throw new RegulatoryViolationError(violations);
    }
  }
}
```

---

## Claims Processing Standards

### FNOL Idempotency

First Notice of Loss submissions must be idempotent. Deduplicate by the natural key: `(policyNumber, incidentDate, incidentDescription hash)`. Duplicate FNOLs within 24 hours of the first submission return the original claim reference without creating a new record.

```typescript
class FNOLService {
  async submit(dto: FNOLDto): Promise<ClaimReference> {
    const idempotencyKey = this.computeIdempotencyKey(dto);

    const existing = await this.claimsRepository.findByIdempotencyKey(idempotencyKey);
    if (existing) {
      this.logger.info('Duplicate FNOL suppressed', { idempotencyKey, claimId: existing.claimId });
      return existing.toReference();
    }

    const claim = Claim.openFNOL(dto, idempotencyKey);
    await this.claimsRepository.save(claim);
    await this.eventBus.publish(claim.pullDomainEvents());
    return claim.toReference();
  }

  private computeIdempotencyKey(dto: FNOLDto): string {
    const payload = `${dto.policyNumber}|${dto.incidentDate}|${hashDescription(dto.incidentDescription)}`;
    return sha256(payload);
  }
}
```

### Reserve Calculation Audit Trail

Every reserve change must produce an immutable audit record including the actuary ID, the calculation basis, and prior/new reserve values:

```typescript
class ReserveCalculator {
  async setInitialReserve(claim: Claim, basis: ReserveBasis): Promise<void> {
    const calculated = this.calculate(claim, basis);
    const auditEntry = ReserveAuditEntry.create({
      claimId: claim.claimId,
      changeType: ReserveChangeType.INITIAL_SET,
      priorReserve: Money.zero(),
      newReserve: calculated,
      calculationBasis: basis,
      calculatedBy: this.actuaryContext.userId,
      timestamp: Timestamp.now(),
    });
    claim.setReserve(calculated, auditEntry);
    await this.auditRepository.append(auditEntry);
  }
}
```

Reserve audit entries are append-only. No update or delete operations are permitted on the `reserve_audit` table (enforced via DB triggers and application-level policy).

### Settlement Saga with Compensation Transactions

The settlement workflow is a distributed saga. Each step registers a compensating action in case a downstream step fails:

```typescript
class SettlementSaga {
  async execute(claim: Claim, settlement: SettlementProposal): Promise<void> {
    const saga = new SagaBuilder(claim.claimId)
      .step('validate-coverage',
        () => this.coverageValidator.validate(claim, settlement),
        () => Promise.resolve() // read-only, no compensation needed
      )
      .step('reserve-funds',
        () => this.billingService.reserveFunds(settlement.amount),
        () => this.billingService.releaseFunds(settlement.amount)
      )
      .step('issue-payment',
        () => this.paymentGateway.disburse(settlement),
        () => this.paymentGateway.void(settlement.paymentRef)
      )
      .step('close-claim',
        () => claim.close(settlement),
        () => claim.reopen('settlement-reversal')
      );

    await saga.execute(); // rolls back completed steps on failure
  }
}
```

---

## Fraud Detection Integration Patterns

### Async Fraud Score Request

Fraud scoring must never block the FNOL workflow. Submit a score request to the fraud service asynchronously and continue processing:

```typescript
class ClaimDomainService {
  async processFNOL(claim: Claim): Promise<void> {
    // 1. Persist claim synchronously
    await this.claimsRepository.save(claim);

    // 2. Request fraud score — fire and forget
    await this.fraudGateway.requestScoreAsync({
      claimId: claim.claimId,
      policyNumber: claim.policyNumber,
      incidentType: claim.incidentType,
      claimantHistory: await this.claimantHistoryService.get(claim.claimantId),
      callbackTopic: 'claims.fraud-score-received',
    });

    // 3. Claim moves to PENDING_FRAUD_REVIEW; adjuster assignment waits for score
    claim.awaitFraudScore();
    await this.claimsRepository.save(claim);
  }
}
```

### Score Threshold Routing

When the fraud score callback arrives, route based on configurable thresholds:

```typescript
class FraudScoreReceivedHandler {
  async handle(event: FraudScoreReceivedEvent): Promise<void> {
    const claim = await this.claimsRepository.load(event.claimId);
    const thresholds = await this.configService.getFraudThresholds(claim.lineOfBusiness);

    if (event.score <= thresholds.autoApprove) {
      await this.claimDomainService.approveForProcessing(claim);
    } else if (event.score <= thresholds.siuReferral) {
      await this.siuReferralService.refer(claim, event.score, event.indicators);
    } else {
      await this.claimDomainService.denyOnFraud(claim, event.score, event.indicators);
    }
  }
}
```

Thresholds are configurable per line-of-business and loaded from the `fraud_thresholds` configuration table, not hardcoded. Changes to thresholds require an audit log entry.

---

## NAIC Reporting Patterns

### SAP vs GAAP Differences in Code

Statutory Accounting Principles (SAP) differ materially from GAAP. Maintain separate calculation services rather than applying adjustments as flags:

| Concept | GAAP | SAP |
|---|---|---|
| Policy acquisition costs | Deferred (DAC asset) | Expensed immediately |
| Reinsurance recoverables | Reported net | Reported gross |
| Loss reserves | Best estimate | Provision for adverse deviation included |
| Investments | Fair value | Amortized cost for bonds |

```typescript
// SAP: adds provision for adverse deviation on top of best estimate
class SAPReserveService {
  calculateLossReserve(claims: Claim[]): Money {
    const bestEstimate = this.actuarialModel.bestEstimate(claims);
    const pad = bestEstimate.multiply(this.config.adverseDeviationFactor);
    return bestEstimate.add(pad).roundToNearestCent();
  }
}

// GAAP: best estimate only, no PAD
class GAAPReserveService {
  calculateLossReserve(claims: Claim[]): Money {
    return this.actuarialModel.bestEstimate(claims).roundToNearestCent();
  }
}
```

### Reserve Adequacy Reporting

Reserve adequacy checks compare carried reserve to the actuarial indication and flag the delta for the appointed actuary review queue:

```typescript
class ReserveAdequacyReport {
  generate(asOfDate: LocalDate): ReserveAdequacyReport {
    const carried = this.reserveRepository.totalCarriedReserve(asOfDate);
    const indicated = this.actuarialService.indicatedReserve(asOfDate);
    const deficiency = indicated.subtract(carried);

    return {
      asOfDate,
      carriedReserve: carried,
      indicatedReserve: indicated,
      deficiency,
      isAdequate: deficiency.isNegativeOrZero(),
      naicScheduleP: this.scheduleP.generate(asOfDate),
    };
  }
}
```

---

## Security Standards

### PII Encryption

All personally identifiable information fields are encrypted at rest using AES-256-GCM with a per-tenant data key managed by the cloud KMS:

```typescript
@Column({ transformer: new PiiFieldTransformer() })
dateOfBirth: string; // stored encrypted, decrypted on read

@Column({ transformer: new PiiFieldTransformer() })
ssn: string; // last 4 displayed only; full value stored encrypted
```

SSN must never appear in application logs. Use `[REDACTED-SSN]` in all log statements. Enforce via ESLint rule `no-ssn-in-logs` in the shared eslint config.

### PCI-DSS for Payment Data

Payment card data is never stored in the application database. Tokenize at point of entry using the payment processor's hosted fields:

- Raw PANs must not traverse application servers
- Store only processor-issued tokens (`tok_*`) in the `payment_methods` table
- TLS 1.2 minimum for all payment API calls; TLS 1.3 preferred
- Quarterly ASV scans required; results stored in `/docs/pci-scans/`

### Role-Based Access Control

```typescript
@Roles(InsuranceRole.ADJUSTER, InsuranceRole.ADJUSTER_SUPERVISOR)
@Post('/claims/:claimId/reserve')
async setReserve(@Param('claimId') claimId: string, @Body() dto: SetReserveDto) { ... }

@Roles(InsuranceRole.UNDERWRITER, InsuranceRole.UNDERWRITER_SUPERVISOR)
@Post('/submissions/:id/decision')
async makeDecision(@Param('id') id: string, @Body() dto: DecisionDto) { ... }
```

Roles are validated at the API gateway and re-validated in the application service. Defense-in-depth: never trust role claims from an upstream service without re-verification.

---

## Testing Standards

### Property-Based Testing for Premium Calculations

Use property-based testing (fast-check) to verify actuarial invariants across the full input space:

```typescript
import fc from 'fast-check';

describe('PremiumCalculator invariants', () => {
  it('premium never decreases when coverage limit increases', () => {
    fc.assert(
      fc.property(
        fc.record({
          baseLimit: fc.integer({ min: 50_000, max: 1_000_000 }),
          stateCode: fc.constantFrom('TX', 'CA', 'FL', 'NY'),
          ageOfHome: fc.integer({ min: 0, max: 100 }),
        }),
        ({ baseLimit, stateCode, ageOfHome }) => {
          const lower = calculator.compute({ limit: baseLimit, stateCode, ageOfHome });
          const higher = calculator.compute({ limit: baseLimit * 2, stateCode, ageOfHome });
          return higher.amount.gte(lower.amount);
        }
      )
    );
  });

  it('premium is always positive', () => {
    fc.assert(
      fc.property(validPolicyArbitrary(), policy => {
        return calculator.compute(policy).amount.gt(0);
      })
    );
  });
});
```

### Contract Tests for Regulatory APIs

Regulatory API contracts must be pinned with consumer-driven contract tests using Pact:

```typescript
describe('NAIC Filing API contract', () => {
  const provider = new PactV3({ consumer: 'ReportingService', provider: 'NAICFilingApi' });

  it('submits Schedule P with correct field mappings', async () => {
    await provider
      .given('valid Schedule P data exists')
      .uponReceiving('a Schedule P submission')
      .withRequest({ method: 'POST', path: '/filings/schedule-p', body: schedulePBody })
      .willRespondWith({ status: 202, body: { confirmationNumber: like('NAIC-2024-00001') } })
      .executeTest(async (mockServer) => {
        const client = new NAICFilingClient(mockServer.url);
        const result = await client.submitScheduleP(schedulePData);
        expect(result.confirmationNumber).toBeDefined();
      });
  });
});
```

Contract tests run in CI on every PR that touches the reporting service. Pact broker URL is set in `PACT_BROKER_URL` environment variable.
