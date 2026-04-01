# Implementation Guidelines — Digital Banking Platform

End-to-end implementation playbook covering phased delivery, technology stack, testing strategy, and compliance checklists. All phases follow a trunk-based development model with feature flags for safe progressive rollout.

---

## Technology Stack

### Core Languages and Frameworks

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Primary backend | Java 21 (Virtual Threads) + Spring Boot 3.3 | Proven banking ecosystem, JDBC maturity, virtual threads for high throughput |
| Async workers | Go 1.22 | High-concurrency event processors (Kafka consumers, fraud scoring) |
| ML model serving | Python 3.12 + TorchServe | Fraud/underwriting ML models |
| API gateway layer | Kong 3.x + Lua plugins | OAuth validation, rate limiting, mTLS |
| Frontend web | React 18 + TypeScript | Customer portal |
| Mobile | React Native + Expo | iOS/Android unified codebase |
| Infrastructure as Code | Terraform 1.8 + Terragrunt | Multi-environment, module-based |
| Container orchestration | Kubernetes 1.30 on EKS | Managed control plane |
| Service mesh | Istio 1.21 (optional, evaluate vs. Calico for simplicity) | mTLS, traffic management |

### Data Technologies

| Technology | Version | Use Case |
|-----------|---------|---------|
| PostgreSQL (Aurora) | 15.x | Primary OLTP store |
| Redis | 7.2 | Cache, sessions, rate limiting |
| Apache Kafka (MSK) | 3.6 | Event streaming, audit trail |
| OpenSearch | 2.13 | Log analysis, transaction search |
| Flyway | 10.x | Database schema migrations |

### External Integrations

| Category | Vendor | Fallback |
|----------|--------|---------|
| Core banking | Mambu (SaaS) or Thought Machine (Vault) | — (critical dependency) |
| KYC/Identity | Jumio (primary), Onfido (secondary) | Manual review queue |
| Card issuance | Marqeta | Galileo Financial Technologies |
| ACH rail | Modern Treasury | Dwolla |
| AML screening | ComplyAdvantage | LexisNexis WorldCompliance |
| Credit bureaus | Experian (primary), Equifax, TransUnion | Bureau consolidator (Merge API) |
| Fraud ML | Featurespace ARIC | Sardine |
| Notification | Twilio (SMS), SendGrid (email), FCM/APNs (push) | — |

---

## Phase 1: Account Management and KYC (Weeks 1–4)

### Objectives

Deliver a working end-to-end customer onboarding flow with identity verification and core banking integration. Target KYC automated pass rate above 85%.

### Week 1: Foundation and Core Infrastructure

**Infrastructure Setup:**
- Provision EKS cluster, VPC, subnets, security groups via Terraform
- Deploy RDS Aurora PostgreSQL with initial schema (Flyway migrations)
- Set up MSK Kafka cluster, ElastiCache Redis cluster
- Configure AWS KMS CMKs per service, Secrets Manager secrets
- Deploy Kong API Gateway with OAuth 2.0 + FAPI plugin configuration
- Set up GitLab CI/CD pipeline with OPA policy checks, SAST (Semgrep), DAST (OWASP ZAP)
- Configure CloudTrail, GuardDuty, SecurityHub, AWS Config conformance packs

**Database Schema — Phase 1 Tables:**
```sql
-- Core tables initialized in Week 1
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_KYC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE kyc_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    status VARCHAR(32) NOT NULL DEFAULT 'DOCUMENT_SUBMITTED',
    risk_rating VARCHAR(16),
    provider VARCHAR(32), -- JUMIO, ONFIDO, MANUAL
    provider_reference VARCHAR(128),
    verified_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    account_number VARCHAR(16) UNIQUE NOT NULL,
    routing_number VARCHAR(9) NOT NULL DEFAULT '021000021',
    account_type VARCHAR(32) NOT NULL, -- CHECKING, SAVINGS
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_KYC',
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    available_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    ledger_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    core_banking_ref VARCHAR(128), -- Mambu account ID
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Week 2: Customer Service and Account Service

**Customer Service API endpoints:**
- `POST /customers` — Create customer profile (draft state)
- `GET /customers/{id}` — Retrieve customer profile
- `PATCH /customers/{id}` — Update profile fields
- `POST /customers/{id}/kyc/initiate` — Start KYC flow, return upload URL

**Account Service API endpoints:**
- `POST /accounts` — Create checking or savings account (requires KYC APPROVED)
- `GET /accounts/{id}` — Get account details and balance
- `GET /accounts/{id}/transactions` — Paginated transaction history (cursor-based)
- `POST /accounts/{id}/statements` — Request statement generation (async)

**Mambu / Thought Machine Integration:**
- Implement core banking adapter (port-and-adapter pattern — hexagonal architecture)
- Account creation in Mambu via REST API — store external reference in local DB
- Balance synchronization: event-driven via Mambu webhooks + local ledger
- Implement reconciliation job (nightly): compare local balance with Mambu — alert on discrepancy > $0.01

### Week 3: KYC Service Integration

**Jumio NetVerify Integration:**
```java
// KYC Service — Jumio integration (Spring Boot 3.3, Java 21)
@Service
public class JumioKYCProvider implements KYCProvider {

    private final JumioClient jumioClient;
    private final KafkaProducer<String, KYCEvent> kafkaProducer;

    @Override
    public KYCInitiationResult initiateVerification(Customer customer) {
        var request = JumioInitRequest.builder()
            .customerInternalReference(customer.getId().toString())
            .userReference(customer.getExternalId())
            .callbackUrl(config.getCallbackBaseUrl() + "/kyc/callbacks/jumio")
            .workflowId(determineWorkflow(customer.getRiskIndicators()))
            .build();

        var response = jumioClient.initiate(request);

        return KYCInitiationResult.builder()
            .sessionToken(response.getWorkflowExecutionId())
            .sdkToken(response.getSdkToken())
            .webUrl(response.getWeb().getHref())
            .expiresAt(Instant.now().plus(30, ChronoUnit.MINUTES))
            .build();
    }

    @Override
    public void processCallback(JumioWebhookPayload payload) {
        var decision = mapJumioDecision(payload.getWorkflow().getStatus());
        var event = KYCEvent.builder()
            .customerId(payload.getUserReference())
            .provider("JUMIO")
            .providerReference(payload.getWorkflowExecutionId())
            .decision(decision)
            .riskRating(extractRiskRating(payload))
            .timestamp(Instant.now())
            .build();

        kafkaProducer.send(new ProducerRecord<>("kyc.events", event.getCustomerId(), event));
    }
}
```

**KYC Webhook Security:**
- Verify Jumio HMAC-SHA256 signature on every callback (constant-time comparison)
- Idempotency: deduplicate by `workflowExecutionId` (check Redis before processing)
- Retry handling: Jumio retries up to 3 times — idempotent processing mandatory

**Onfido Fallback:**
- Activate automatically when Jumio API returns 5xx or connection timeout > 10 seconds
- Circuit breaker: 5 failures in 30 seconds → open circuit, route to Onfido for 60 seconds
- Alert on fallback activation — SRE investigation required

### Week 4: Integration Testing and Phase 1 Completion

**Deliverables Checklist:**
- [ ] Customer creation → KYC initiation → webhook callback → account activation flow working end-to-end
- [ ] Jumio integration tested with real sandbox credentials (all document types: Passport, DL, ID card)
- [ ] Onfido fallback tested: Jumio circuit breaker fires, Onfido processes successfully
- [ ] Mambu account creation and balance sync verified
- [ ] KYC pass rate target: >85% on valid documents (US Passport baseline)
- [ ] WCAG 2.1 AA compliance on onboarding web flow (automated axe scan)
- [ ] Load test: 500 concurrent KYC initiations — P99 < 3s for session creation
- [ ] PCI-DSS: confirm KYC service does NOT touch any card data — scope exclusion documented
- [ ] All secrets in Secrets Manager — no credentials in environment variables or config files

---

## Phase 2: Card Management and Transactions (Weeks 5–8)

### Week 5: Card Service and Marqeta Integration

**Marqeta Integration Architecture:**
- Card issuance: `POST /v3/cards` → Marqeta creates virtual card, returns PAN (received once, tokenized immediately)
- Just-In-Time (JIT) funding: Marqeta calls our Authorization Service for every transaction in real-time
- Webhook: Marqeta sends card events (activated, blocked, transaction authorized)
- PAN handling: PAN received from Marqeta → immediately tokenized via Visa VTS → PAN never persisted in our systems

**3DS 2.x Implementation (EMVCo specification):**
- `POST /3ds/authenticate` — initiate 3DS authentication
- Frictionless flow: device fingerprint + prior auth → skip OTP for low-risk
- Challenge flow: push notification OTP via FCM/APNs (30-second TOTP window)
- Decoupled flow: biometric authentication (FaceID/TouchID) via React Native
- All 3DS cryptographic operations via CloudHSM (PKCS#11)

### Week 6: ACH Transfer Service

**Modern Treasury Integration:**
```java
// Transfer Service — ACH origination via Modern Treasury
@Transactional
public TransferResult initiateACHTransfer(TransferRequest request) {
    // Phase 1: Fraud check (must complete in < 500ms)
    var fraudScore = fraudClient.score(FraudScoreRequest.from(request));
    if (fraudScore.getRiskBand() == RiskBand.HIGH) {
        return TransferResult.blocked("FRAUD_HIGH_RISK");
    }

    // Phase 2: AML screening
    var amlResult = amlClient.screen(AMLScreenRequest.from(request));
    if (amlResult.hasHit()) {
        transferRepository.updateStatus(request.getId(), TransferStatus.AML_HOLD);
        return TransferResult.hold("AML_REVIEW_REQUIRED");
    }

    // Phase 3: Debit source account (atomic, with optimistic locking)
    var debitResult = accountService.debit(
        request.getSourceAccountId(), request.getAmount(), request.getRef()
    );

    // Phase 4: Submit to Modern Treasury
    var paymentOrder = modernTreasuryClient.createPaymentOrder(
        PaymentOrderRequest.builder()
            .type(PaymentType.ACH)
            .direction("credit")
            .amount(request.getAmount().toLong()) // in cents
            .currency("USD")
            .originatingAccountId(config.getODFIAccountId())
            .receivingAccountId(resolveReceivingAccount(request))
            .metadata(Map.of("internal_ref", request.getId().toString()))
            .build()
    );

    transferRepository.updateStatus(request.getId(), TransferStatus.PROCESSING);
    transferRepository.updatePaymentOrderRef(request.getId(), paymentOrder.getId());

    // Phase 5: Emit event for async processing
    kafkaProducer.send("transfers.initiated", TransferInitiatedEvent.from(request, paymentOrder));

    return TransferResult.processing(request.getId());
}
```

**ACH Return Code Handling:**
- R01 (Insufficient Funds): auto-reverse debit, notify customer
- R02 (Account Closed): notify customer, block payee for 30 days
- R03 (No Account/Unable to Locate): notify customer, request account validation
- R10 (Customer Advises Unauthorized): initiate Reg E investigation, freeze transfer
- R29 (Corporate Customer Advises Not Authorized): compliance escalation

### Week 7: Fraud ML Model Integration

**Featurespace ARIC Integration:**
- Real-time scoring: gRPC API, P99 SLA 200ms
- Feature engineering: velocity features computed in Redis (last 1h, 24h, 7d counts/amounts)
- Model feedback loop: confirmed fraud/false positive events → Kafka topic `fraud.feedback` → Featurespace retraining pipeline
- Shadow scoring: run Sardine in parallel for model comparison (no blocking decision)

**AML ComplyAdvantage Integration:**
- Sanctions screening: called synchronously on every outbound transfer
- Transaction monitoring: async rules engine running on Kafka `transactions.audit` topic
- SAR/CTR generation: automated drafting from flagged transaction records
- Refresh schedule: OFAC/UN/EU sanctions list pulled every 4 hours

### Week 8: Phase 2 Testing and Certification

**Deliverables Checklist:**
- [ ] End-to-end card issuance: request → Marqeta → PAN tokenization → card active
- [ ] 3DS 2.x frictionless + challenge + decoupled flows tested
- [ ] JIT authorization flow: < 100ms P99 (Marqeta's SLA is 2 seconds)
- [ ] ACH transfer: initiate → fraud check → AML → debit → submit → settlement → credit
- [ ] ACH return codes R01–R10 handled correctly (test via Modern Treasury sandbox)
- [ ] Fraud ML scoring: P99 < 200ms under 1000 TPS load
- [ ] AML sanctions screening: tested with OFAC SDN test names
- [ ] PCI-DSS SAQ-D scope: card data flow documented, PAN never in non-CDE logs
- [ ] 3DS EMVCo compliance certification initiated with card network

---

## Phase 3: Loan Origination (Weeks 9–12)

### Week 9: Loan Application Service

**Loan Application API:**
- `POST /loans/apply` — Submit application, trigger hard inquiry
- `GET /loans/{id}` — Get application status and offer details
- `POST /loans/{id}/accept` — Accept offer, trigger disbursement
- `GET /loans/{id}/schedule` — Amortization schedule (36 rows for 36-month loan)
- `POST /loans/{id}/payment` — Submit repayment (ACH debit from linked account)

**ECOA/Reg B Compliance (Equal Credit Opportunity Act):**
- Every credit decision must be explainable — log all decision factors
- Adverse action notice: auto-generated PDF within 30 days of decline
- Disparate impact monitoring: quarterly statistical analysis of approval rates by protected class
- No protected class attributes (race, sex, religion, national origin, marital status, age, receipt of public assistance) used in or correlated with underwriting model features

### Week 10: Credit Bureau Integration

**Experian Integration (primary):**
```java
// Credit bureau client — Experian Premier Attributes
@Service
public class ExperianCreditBureauClient implements CreditBureauClient {

    @Override
    @CircuitBreaker(name = "experian", fallbackMethod = "fallbackToEquifax")
    public CreditReport pull(CreditInquiryRequest request) {
        var experianRequest = ExperianCreditRequest.builder()
            .ssn(request.getSsn()) // transmitted via TLS 1.3 + encrypted at rest
            .dob(request.getDob())
            .firstName(request.getFirstName())
            .lastName(request.getLastName())
            .address(request.getAddress())
            .permissiblePurpose(PermissiblePurpose.CREDIT_TRANSACTION)
            .inquiryType(InquiryType.HARD) // records on consumer file
            .productCode("FICO9_PLUS_ATTRIBUTES")
            .build();

        var response = experianHttpClient.post("/v1/credit-profile", experianRequest);

        return CreditReport.builder()
            .bureau("EXPERIAN")
            .ficoScore(response.getFicoScore9())
            .dtiRatio(response.getObligations().getDTI())
            .derogatoryCount(response.getDerogatoryMarks().size())
            .openRevolvingUtilization(response.getRevolvingUtilization())
            .reportId(response.getClientReferenceId())
            .pulledAt(Instant.now())
            .build();
    }

    // Equifax fallback if Experian unavailable
    private CreditReport fallbackToEquifax(CreditInquiryRequest request, Exception ex) {
        log.warn("Experian unavailable, falling back to Equifax: {}", ex.getMessage());
        return equifaxClient.pull(request);
    }
}
```

### Week 11: Underwriting Engine

**Decision Waterfall:**
1. Hard knockouts: FICO < 580, active bankruptcy, delinquency in past 12 months → instant decline
2. DTI check: back-end DTI (including proposed payment) > 43% → decline
3. Income verification: stated income vs. bank statement analysis (> 30% discrepancy → manual review)
4. Risk tier assignment: Tier A (760+), Tier B (700–759), Tier C (640–699), Tier D (580–639)
5. Pricing: base rate + risk premium by tier + term premium (36mo=0, 60mo=+0.5%)
6. Concentration limits: personal loan book < 15% of total loan portfolio

**Amortization Schedule Generation:**
- Standard declining-balance amortization (Reg Z compliant)
- TILA disclosure: APR, finance charge, total payments, payment schedule
- Early payoff penalty: none (disclosed at origination)
- Biweekly payment option: reduces total interest, documented in schedule

### Week 12: Phase 3 Testing

**Deliverables Checklist:**
- [ ] Full origination flow: apply → KYC → bureau pull → underwrite → offer → accept → disburse
- [ ] Experian integration tested (sandbox hard inquiries validated)
- [ ] Equifax fallback tested (Experian circuit breaker fires correctly)
- [ ] Underwriting engine: 50 test cases covering all tiers, edge cases, policy knockouts
- [ ] ECOA adverse action notice generated correctly for all decline reasons
- [ ] Repayment scheduling: ACH auto-debit mandate created, tested with trial debit
- [ ] TILA disclosure: reviewed by compliance team, signed off
- [ ] Reg B compliance: adverse action letter template approved by legal
- [ ] Load test: 200 concurrent loan applications — Experian bureau calls throttled correctly

---

## Phase 4: Open Banking and Analytics (Weeks 13–16)

### Week 13: PSD2 Open Banking API

**FAPI 1.0 Advanced Profile Implementation:**
- Authorization server: Spring Authorization Server with FAPI profile
- mTLS client authentication (eIDAS QWAC certificates for European TPPs)
- PAR (Pushed Authorization Requests): `POST /oauth2/par` — prevents request object tampering
- JARM (JWT Secured Authorization Response): response integrity protection
- DPoP (Demonstrating Proof-of-Possession): token binding to client key
- Consent management: granular scopes (accounts:read, transactions:read, payments:write)
- Consent expiry: maximum 90 days, revocable by customer at any time
- TPP register: AISP/PISP role validation against Open Banking directory

**Open Banking Endpoints (PSD2 compliant):**
```
GET  /open-banking/v3.1/aisp/accounts
GET  /open-banking/v3.1/aisp/accounts/{id}/transactions
GET  /open-banking/v3.1/aisp/accounts/{id}/balances
POST /open-banking/v3.1/pisp/domestic-payments
GET  /open-banking/v3.1/pisp/domestic-payments/{id}
POST /open-banking/v3.1/cbpii/funds-confirmations
```

### Week 14: Analytics Dashboard

**Customer-Facing Analytics:**
- Spending by merchant category (MCC) — Sankey chart, 12-month trend
- Income vs. expenses waterfall — monthly view
- Savings goal progress tracker — configurable goals with milestone alerts
- Peer benchmarking (anonymized): "You spend 23% less on dining than similar customers"
- Cash flow forecast: 30-day projection based on recurring transactions and income

**Data Pipeline:**
- Kafka `transactions.audit` → Kafka Streams aggregation → OpenSearch index
- OpenSearch dashboards for internal operations (fraud rates, processing volumes, error rates)
- Amazon QuickSight for regulatory reporting (CTR count, SAR filing rate, KYC metrics)

### Week 15: Regulatory Reporting

**CTR (Currency Transaction Report — FinCEN) Automation:**
- Detect cash transactions >= $5,000 (threshold configurable)
- Auto-aggregate structuring patterns (multiple transactions <$10,000 by same customer on same day)
- CTR form 112 generation: BSA E-Filing XML format
- Daily filing: batch job at 11:45 PM ET — file all reportable transactions from prior day
- 15-day filing deadline per FinCEN regulation — alert if batch fails

**SAR (Suspicious Activity Report — FinCEN) Workflow:**
- AML alerts trigger SAR investigation case in case management system
- 30-day filing deadline from date of initial detection
- 90-day extension available with documented reason
- Confidentiality: SAR existence not disclosed to subject (tipping-off prohibition)
- Retention: 5 years from filing date

### Week 16: Performance Optimization and Sign-Off

**Load Testing to 50,000 TPS:**
- Tool: k6 or Gatling with distributed test harness
- Scenarios: 60% card authorizations, 25% account reads, 10% transfers, 5% loan queries
- Ramp-up: 0 → 10K TPS (10 min) → 10K → 50K TPS (20 min) → sustained 50K (30 min)
- Acceptance criteria: P99 < 500ms for all endpoints at 50K TPS, zero 5xx errors
- Database: validate Aurora connection pool sizing (HikariCP max-pool-size = 50 per service × N replicas)
- Fraud scoring: validate ML inference throughput (TorchServe batch size tuning)

---

## Testing Strategy

### Unit Testing
- Coverage target: 80% line coverage, 90% for financial calculation logic
- Framework: JUnit 5 + Mockito (Java), Jest (TypeScript frontend)
- Financial math: exhaustive property-based testing (jqwik) for amortization calculations
- No mocking of I/O at unit level — use fakes/in-memory implementations

### Integration Testing
- Framework: Testcontainers (PostgreSQL, Redis, Kafka, LocalStack for AWS)
- Test database: isolated schema per test class, rolled back after each test
- API integration tests: RestAssured + WireMock for external dependencies
- Kafka: EmbeddedKafka for consumer/producer integration tests

### Contract Testing
- Framework: Pact.io — consumer-driven contract tests
- All inter-service gRPC contracts covered
- Open Banking API: OBIE conformance suite

### End-to-End Testing
- Framework: Playwright (web), Detox (mobile)
- Critical user journeys automated: onboarding, transfer, card payment, loan apply
- Run on every PR in preview environment (ephemeral EKS namespace)
- Synthetic monitoring in production: canary transactions every 5 minutes

### Performance Testing
- k6 for API load testing
- Gatling for complex scenario simulation
- Database: pgbench for PostgreSQL baseline
- Acceptance: P50 < 50ms, P95 < 200ms, P99 < 500ms at expected peak load

### Security Testing
- SAST: Semgrep (custom rules for banking), integrated in CI pipeline
- DAST: OWASP ZAP automated scan on every deployment
- Dependency scanning: Snyk (all languages) — block on CVSS >= 9.0
- Annual external penetration test (PCI-DSS Req 11.4.3)
- Quarterly internal penetration test (different teams)

---

## PCI-DSS Deployment Checklist

**Network Controls:**
- [ ] CDE subnets isolated — no unauthorized inbound/outbound paths verified
- [ ] Firewall rules documented and reviewed quarterly (Req 1.3.2)
- [ ] Default credentials changed on all systems (Req 2.1)
- [ ] WAF rules active and blocking OWASP Top 10 (Req 6.4.1)
- [ ] VPC Flow Logs enabled and monitored (Req 10.6.3)

**Data Protection:**
- [ ] PAN never stored in non-CDE systems (verify via Macie scan)
- [ ] PAN masked in all logs (regex filter in Fluent Bit confirmed)
- [ ] CVV2 not stored post-authorization (Req 3.2)
- [ ] All stored PAN encrypted (AES-256 + KMS CMK) (Req 3.4)
- [ ] TLS 1.2 minimum everywhere (TLS 1.3 preferred) (Req 4.2.1)
- [ ] Key management procedures documented and tested (Req 3.7)

**Vulnerability Management:**
- [ ] All systems patched within policy (CVSS >= 9.0: 24h, >= 7.0: 7 days, < 7.0: 30 days)
- [ ] Anti-malware on all non-mainframe systems (AWS Inspector + Bottlerocket hardened OS)
- [ ] Secure development practices documented (OWASP ASVS Level 2) (Req 6.2)

**Access Control:**
- [ ] MFA enforced for all console access to CDE (Req 8.4.2)
- [ ] Least privilege principle for all service accounts (Req 7.2)
- [ ] Shared accounts eliminated — individual accountability for all CDE access
- [ ] Access review quarterly (Req 7.3.1)
- [ ] Privileged access via PAM with session recording (Req 8.6.3)

**Monitoring and Testing:**
- [ ] Centralized logging with 12-month retention (Req 10.5.1)
- [ ] Daily log review procedures documented and operational
- [ ] SIEM alerting on suspicious patterns (Req 10.7.2)
- [ ] Change detection on critical CDE files (Req 11.5.2)
- [ ] Annual penetration test completed and findings remediated (Req 11.4.3)

---

## Regulatory Compliance Sign-Off Checklist

**Banking Regulations:**
- [ ] BSA/AML Program: written AML policy approved by Board (31 CFR 1020.210)
- [ ] CIP (Customer Identification Program): procedures documented and tested
- [ ] CTR filing: automated for cash transactions >= $10,000 (31 CFR 1010.311)
- [ ] SAR filing: 30-day deadline met — automated tracking and escalation
- [ ] OFAC compliance: sanctions screening on all transactions, updated within 4 hours of list changes
- [ ] Reg E (Electronic Fund Transfer Act): consumer dispute process, provisional credit timing
- [ ] Reg Z (Truth in Lending): TILA disclosures on all credit products reviewed by legal
- [ ] ECOA/Reg B: adverse action notices tested and reviewed by legal
- [ ] FCRA: credit bureau inquiry procedures, adverse action notices

**Data Privacy:**
- [ ] GDPR Article 30 records of processing activities documented
- [ ] CCPA privacy notice published and opt-out mechanism tested
- [ ] GDPR Data Protection Impact Assessment (DPIA) completed for high-risk processing
- [ ] Data retention schedule: implemented in S3 lifecycle policies and DB TTL jobs
- [ ] Right to access: automated report generation within 30 days
- [ ] Right to erasure: implemented with carve-out for legal/regulatory retention obligations

**Cybersecurity:**
- [ ] NIST CSF alignment: identify, protect, detect, respond, recover documented
- [ ] SOC 2 Type II audit scope defined, controls in place
- [ ] ISO 27001 gap assessment completed (if required)
- [ ] Incident response plan: tested with tabletop exercise, contact list current
- [ ] Business continuity plan: BCP approved by executive team, DR tested

**Open Banking:**
- [ ] PSD2 SCA compliance (if EU customers): 3DS 2.x implementation certified
- [ ] FAPI 1.0 Advanced Profile: conformance test suite run against Open Banking sandbox
- [ ] TPP registration: eIDAS certificate validation implemented
- [ ] Open Banking API: aligned to OB Read/Write API Specification v3.1.10
