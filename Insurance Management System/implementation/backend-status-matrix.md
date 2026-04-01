# Backend Implementation Status Matrix — Insurance Management System

Last updated: 2025-07  
Status values: `Not Started` | `In Progress` | `Complete` | `Blocked`

---

## Policy Administration Service

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| New business application intake | `POST /policies/applications` | In Progress | DTO validation complete; compliance assertion pending state filing integration | StateFilingService |
| Application document upload | `POST /policies/applications/:id/documents` | Not Started | S3 presigned URL flow not wired | S3, DocumentService |
| Underwriting referral on application | `POST /policies/applications/:id/refer` | Not Started | Waits for UnderwritingService API stabilization | UnderwritingService |
| Policy issuance (bind) | `POST /policies/:id/issue` | In Progress | Core bind logic done; premium booking event not published | BillingService, EventBus |
| Policy document generation | `POST /policies/:id/documents/declarations` | Not Started | PDF template not designed | TemplateService |
| Policy detail retrieval | `GET /policies/:policyNumber` | Complete | Read model projection live; indexed on policyNumber | — |
| Endorsement — coverage change | `POST /policies/:policyNumber/endorsements` | In Progress | Coverage diff calculation complete; pro-rata premium pending | RatingService |
| Endorsement — additional insured | `POST /policies/:policyNumber/endorsements/additional-insured` | Not Started | Form filed in 3 states; 47 pending | StateFilingService |
| Endorsement approval workflow | `PUT /policies/:policyNumber/endorsements/:id/approve` | Not Started | Requires rules engine decision node | RulesEngine |
| Policy cancellation — flat | `POST /policies/:policyNumber/cancel` | Complete | Return premium calculated; refund event published | BillingService |
| Policy cancellation — pro-rata | `POST /policies/:policyNumber/cancel` | In Progress | Short-rate table lookup incomplete for TX, FL | RatingService |
| Non-payment lapse | Internal (scheduled job) | In Progress | Grace period timer fires; lapse event published; reinstatement blocked | BillingService |
| Reinstatement | `POST /policies/:policyNumber/reinstate` | Not Started | Blocked: lapse flow not complete | BillingService |
| Renewal offer generation | Internal (batch, 90 days pre-expiry) | Not Started | Renewal rating rules not finalized | RatingService, ActuarialTeam |
| Renewal issuance | `POST /policies/:policyNumber/renew` | Not Started | Depends on renewal offer generation | RatingService |
| Policy search (broker view) | `GET /policies?broker=&status=&lob=` | Complete | Paginated; ElasticSearch projection | — |
| Policy history / audit log | `GET /policies/:policyNumber/history` | Complete | Event store replay endpoint live | EventStore |

---

## Underwriting Service

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| Risk score computation | `POST /underwriting/submissions/:id/score` | In Progress | ML model integration wired; feature extraction for flood zone incomplete | GeoService, MLPlatform |
| Automated rules evaluation | `POST /underwriting/submissions/:id/evaluate` | In Progress | 142 of 200 business rules ported from legacy system | RulesEngine |
| Auto-approve decision | Internal (rules engine outcome) | In Progress | Approval threshold calibration in UAT | RulesEngine |
| Decline decision | Internal (rules engine outcome) | In Progress | Adverse action notice generation not done | NotificationService |
| Manual referral to underwriter | `POST /underwriting/submissions/:id/refer` | Complete | Assigned to underwriter queue; email notification sent | NotificationService |
| Underwriter review UI API | `GET /underwriting/queue` | Complete | Filterable by LOB, state, priority | — |
| Underwriter override decision | `POST /underwriting/submissions/:id/decision` | Complete | Audit trail recorded; role-gated to UNDERWRITER role | — |
| Risk scoring model versioning | `GET /underwriting/models` | Not Started | MLOps pipeline not connected | MLPlatform |
| Reinsurance facultative check | Internal (post-decision) | Not Started | Blocked: Reinsurance treaty API not deployed | ReinsuranceService |
| Underwriting guideline lookup | `GET /underwriting/guidelines?lob=&state=` | Not Started | Content not migrated from legacy PDF | ContentTeam |
| Submission status tracking | `GET /underwriting/submissions/:id` | Complete | Full status history with timestamps | — |

---

## Claims Service

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| FNOL submission | `POST /claims/fnol` | Complete | Idempotency key enforced; duplicate detection live | EventStore |
| FNOL duplicate detection | Internal (FNOL flow) | Complete | SHA-256 key on policy + date + description hash | — |
| Coverage verification on FNOL | Internal (FNOL flow) | In Progress | PolicyService cache TTL issue; stale coverage causing rejections (bug) | PolicyService |
| Adjuster assignment | `POST /claims/:claimId/adjuster` | Complete | Round-robin assignment with workload cap per adjuster | — |
| Claim status retrieval | `GET /claims/:claimId` | Complete | Read model includes reserve history | — |
| Claim list (adjuster view) | `GET /claims?adjuster=&status=` | Complete | Paginated; sortable by severity, reserve amount | — |
| Initial reserve setting | `POST /claims/:claimId/reserve` | In Progress | SAP reserve with adverse deviation factor; GAAP path pending | ActuarialTeam |
| Reserve adjustment | `PUT /claims/:claimId/reserve` | Not Started | Pending initial reserve completion | ActuarialTeam |
| Reserve audit trail | `GET /claims/:claimId/reserve/audit` | In Progress | Append-only table live; query endpoint not exposed | — |
| Investigation workflow | `POST /claims/:claimId/investigation` | Not Started | Investigation checklist schema not finalized | ProductTeam |
| Field inspection scheduling | `POST /claims/:claimId/inspections` | Not Started | Third-party inspection vendor API not integrated | VendorAPI |
| Settlement proposal submission | `POST /claims/:claimId/settlement` | In Progress | Saga wired; payment disbursement step pending | BillingService, PaymentGateway |
| Settlement approval | `PUT /claims/:claimId/settlement/:id/approve` | Not Started | Supervisor approval role not configured in RBAC | SecurityTeam |
| Settlement void / reversal | `DELETE /claims/:claimId/settlement/:id` | Not Started | Depends on settlement approval completion | BillingService |
| Subrogation identification | `POST /claims/:claimId/subrogation` | Not Started | Legal workflow not scoped | LegalTeam |
| Subrogation recovery recording | `POST /claims/:claimId/subrogation/recovery` | Not Started | Depends on subrogation identification | LegalTeam |
| SIU referral | `POST /claims/:claimId/siu` | In Progress | Referral event published; SIU case creation in SIU module pending | SIUModule |
| Claim denial | `POST /claims/:claimId/deny` | Complete | Denial code lookup, adverse action notice published | NotificationService |
| Claim closure | `POST /claims/:claimId/close` | In Progress | Close event published; reserve release to billing pending | BillingService |
| Loss run report | `GET /claims/reports/loss-run?policy=&from=&to=` | Not Started | Reporting schema not finalized | ReportingService |

---

## Billing Service

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| Invoice generation on issuance | Internal (PolicyIssued event) | In Progress | Invoice created; PDF generation not wired | TemplateService |
| Payment plan selection | `POST /billing/policies/:policyNumber/payment-plan` | Complete | Monthly, quarterly, semi-annual, annual options live | — |
| Payment collection (card) | `POST /billing/payments` | In Progress | Tokenization via Stripe hosted fields; 3DS2 not implemented | PaymentGateway |
| Payment collection (ACH) | `POST /billing/payments/ach` | Not Started | ACH origination agreement with bank not signed | FinanceTeam |
| Payment receipt | `GET /billing/payments/:paymentId` | Complete | Payment status and receipt data | — |
| Grace period initiation | Internal (missed payment detection) | In Progress | 10-day grace period timer; multi-state grace period lengths not configured | StateConfig |
| Grace period notice | Internal (grace period start) | In Progress | Email notice sent; SMS notice pending | NotificationService |
| Lapse on grace period expiry | Internal (scheduled) | In Progress | Lapse event published; PolicyService consumption complete | PolicyService |
| Reinstatement billing | `POST /billing/policies/:policyNumber/reinstate` | Not Started | Blocked: reinstatement premium calculation not scoped | RatingService |
| Refund on cancellation | Internal (PolicyCancelled event) | In Progress | Pro-rata refund calculated; ACH refund path blocked | PaymentGateway |
| Commission calculation | Internal (PolicyIssued event) | Not Started | Commission schedule not loaded | BrokerPortal |
| Commission disbursement | `POST /billing/commissions/disburse` | Not Started | Depends on commission calculation | BrokerPortal |
| Payment history | `GET /billing/policies/:policyNumber/payments` | Complete | Full payment history with applied invoices | — |
| Outstanding balance | `GET /billing/policies/:policyNumber/balance` | Complete | Real-time balance from ledger | — |
| Billing statement | `GET /billing/policies/:policyNumber/statements/:period` | Not Started | Statement template not designed | TemplateService |

---

## Reinsurance Service

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| Treaty setup | `POST /reinsurance/treaties` | In Progress | Quota share and XL treaty types; per-risk XL not modeled | ActuarialTeam |
| Treaty detail retrieval | `GET /reinsurance/treaties/:treatyId` | Complete | Full treaty terms and layers | — |
| Cession on policy issuance | Internal (PolicyIssued event) | Not Started | Treaty eligibility rules not coded | PolicyService |
| Cession on endorsement | Internal (EndorsementApplied event) | Not Started | Depends on issuance cession | PolicyService |
| Cession adjustment on cancellation | Internal (PolicyCancelled event) | Not Started | Return cession calculation not scoped | PolicyService |
| Large loss facultative cession | `POST /reinsurance/facultative` | Not Started | Blocked: UnderwritingService facultative check not deployed | UnderwritingService |
| Bordereau generation | `POST /reinsurance/bordereau?period=` | Not Started | Bordereau template per reinsurer not designed | ActuarialTeam |
| Bordereau submission | `POST /reinsurance/bordereau/:id/submit` | Not Started | Reinsurer EDI connection not established | ReinsurancePartners |
| Settlement with reinsurer | `POST /reinsurance/settlements` | Not Started | Depends on bordereau submission | ReinsurancePartners |
| Recoverable tracking | `GET /reinsurance/recoverables` | Not Started | Schedule F reporting requirement; not scoped | FinanceTeam |
| Claims cession | Internal (ClaimSettled event) | Not Started | Loss participation calculation pending | ClaimsService |

---

## Broker Portal

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| Broker authentication (SSO) | `POST /auth/broker/login` | Complete | SAML 2.0 with agency management system providers | IdentityService |
| Broker registration | `POST /broker-portal/brokers` | Complete | License validation against NIPR API | NIRPService |
| Real-time quote | `POST /broker-portal/quotes` | In Progress | Homeowners and auto quoting live; commercial lines pending | RatingService |
| Quote comparison (multi-carrier) | `POST /broker-portal/quotes/compare` | Not Started | Carrier connectivity not established | CarrierAPIs |
| Quote bind | `POST /broker-portal/quotes/:quoteId/bind` | In Progress | Binding logic wired to PolicyService; payment collection step pending | PolicyService, BillingService |
| Policy endorsement request | `POST /broker-portal/policies/:policyNumber/endorsements` | Not Started | Broker-initiated endorsement workflow not scoped | PolicyService |
| Policy cancellation request | `POST /broker-portal/policies/:policyNumber/cancel` | Not Started | Depends on cancellation workflow completion | PolicyService |
| Commission statement | `GET /broker-portal/commissions?period=` | Not Started | Depends on commission calculation in BillingService | BillingService |
| Book of business view | `GET /broker-portal/book` | In Progress | Active policies list live; renewal pipeline view pending | PolicyService |
| FNOL submission on behalf of client | `POST /broker-portal/claims/fnol` | Not Started | Permission model for broker-submitted claims not defined | ClaimsService |
| Renewal pipeline | `GET /broker-portal/renewals` | Not Started | Depends on renewal offer generation | PolicyService |
| Portal activity audit log | `GET /broker-portal/audit` | Not Started | Audit log schema not finalized | AuditService |

---

## Regulatory Reporting

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| NAIC Schedule P generation | `POST /reporting/naic/schedule-p?period=` | In Progress | Loss triangle calculation complete; tail factor selection pending | ActuarialTeam |
| NAIC Schedule F (reinsurance) | `POST /reporting/naic/schedule-f?period=` | Not Started | Blocked: Reinsurance recoverable tracking not available | ReinsuranceService |
| NAIC Annual Statement | `POST /reporting/naic/annual-statement?year=` | Not Started | Requires Schedule P and F completion | ActuarialTeam |
| State quarterly filing | `POST /reporting/state/quarterly?state=&period=` | Not Started | 50-state filing variations not mapped | ComplianceTeam |
| State form submission (XML) | `POST /reporting/state/submit?state=` | Not Started | XML schema per state DOI not collected | ComplianceTeam |
| Loss run report (per policy) | `GET /reporting/loss-run/:policyNumber` | Not Started | Depends on Claims loss run endpoint | ClaimsService |
| Loss run report (bulk) | `POST /reporting/loss-run/bulk` | Not Started | Depends on per-policy loss run | ClaimsService |
| Reserve adequacy report | `GET /reporting/reserve-adequacy?asOf=` | In Progress | SAP reserve calculation wired; GAAP comparison pending | ActuarialTeam |
| Combined ratio dashboard | `GET /reporting/metrics/combined-ratio` | Not Started | Loss and expense data not aggregated | FinanceTeam |
| Premium-to-surplus ratio | `GET /reporting/metrics/premium-surplus` | Not Started | Surplus data feed not connected | FinanceTeam |
| Rate filing status tracker | `GET /reporting/rate-filings?state=&lob=` | Complete | SERFF integration live for filed/approved status | SERFF |
| Adverse action notices | Internal (UnderwritingDeclinedEvent) | In Progress | Email delivery complete; USPS mail via print vendor pending | NotificationService |

---

## Fraud Detection

| Feature | API Endpoint | Status | Notes | Dependencies |
|---|---|---|---|---|
| Async fraud score request | Internal (FNOLSubmitted event) | In Progress | Kafka consumer live; ML model request wired; callback publishing pending | MLPlatform, Kafka |
| Fraud score callback | Internal (FraudScoreReceived event) | In Progress | ClaimsService handler wired; threshold config not loaded | ConfigService |
| Score threshold configuration | `PUT /fraud/thresholds?lob=` | Not Started | Threshold values not agreed with SIU team | SIUTeam |
| SIU referral creation | Internal (threshold routing) | In Progress | Referral event published; SIU case management UI not connected | SIUModule |
| SIU case management API | `GET /fraud/siu-cases` | Not Started | SIU module not scoped for this quarter | SIUTeam |
| Fraud indicator lookup | `GET /fraud/indicators?claimId=` | Complete | Returns raw indicators from ML response | — |
| Model version management | `GET /fraud/models` | Not Started | MLOps registry integration not started | MLPlatform |
| Model promotion / rollback | `POST /fraud/models/:modelId/promote` | Not Started | Depends on model version management | MLPlatform |
| Fraud outcome feedback | Internal (ClaimDenied / ClaimSettled events) | Not Started | Feedback loop to retrain model not designed | MLPlatform |
| Watchlist screening | Internal (FNOL flow) | Not Started | OFAC and industry watchlist feeds not procured | ComplianceTeam |

---

## Summary — Completion by Service

| Service | Total Features | Complete | In Progress | Not Started | Blocked | Completion % |
|---|---|---|---|---|---|---|
| Policy Administration | 17 | 4 | 6 | 7 | 0 | 24% |
| Underwriting | 11 | 4 | 4 | 3 | 0 | 36% |
| Claims | 20 | 5 | 7 | 8 | 0 | 25% |
| Billing | 15 | 4 | 6 | 5 | 0 | 27% |
| Reinsurance | 11 | 1 | 1 | 8 | 1 | 9% |
| Broker Portal | 12 | 2 | 3 | 7 | 0 | 17% |
| Regulatory Reporting | 12 | 1 | 4 | 7 | 0 | 8% |
| Fraud Detection | 10 | 1 | 3 | 6 | 0 | 10% |
| **TOTAL** | **108** | **22** | **34** | **51** | **1** | **20%** |

> **Completion %** counts only features with status `Complete`. `In Progress` features are tracked separately as partial work.

### Key Blockers and Risks

| Item | Blocked Feature(s) | Owner | Target Resolution |
|---|---|---|---|
| Reinsurance treaty API not deployed | Facultative cession, large-loss routing | ReinsuranceTeam | Q3 2025 |
| ACH origination agreement | ACH payment collection, ACH refunds | FinanceTeam | Q3 2025 |
| 50-state DOI XML schemas not collected | State quarterly and annual filings | ComplianceTeam | Q4 2025 |
| SIU module not scoped | SIU case management, SIU referral completion | ProductTeam | Q4 2025 |
| Fraud threshold values not agreed | Score threshold routing goes live | SIU + Actuarial | Q3 2025 |
| Coverage cache TTL bug | FNOL coverage verification failures | ClaimsTeam | Sprint 34 |
