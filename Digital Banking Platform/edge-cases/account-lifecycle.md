# Edge Cases: Account Lifecycle — Digital Banking Platform

---

## Account Closure While Pending Transaction Outstanding

### Scenario
A customer requests account closure at 2:47 PM. At 2:43 PM, they had initiated a $3,200 ACH transfer that is in `PROCESSING` state — the debit was written to the source account, and the NACHA file is scheduled for the 3:00 PM same-day ACH cut-off. The customer expects the account to close immediately.

### Failure Mode
If the system honors the closure request immediately, the account moves to `CLOSED` state. When ACH return code R04 (Invalid Account Number Structure) or settlement confirmation arrives at 4:15 PM, the system has no open account to credit or reverse into. If the transfer settles at the counterparty, the funds are gone. If an ACH return arrives, there is no account to credit the reversal — funds become orphaned in a suspense ledger entry.

### Impact
- **Financial:** Up to the pending transaction amount stuck in suspense; potential loss if settlement completes without open receiving account.
- **Operational:** Manual intervention required from back-office team to resolve suspense entries.
- **Regulatory:** Reg E violation if a disputed transaction cannot be resolved because the account was prematurely closed.
- **Customer:** Closure is not honored as expected; customer receives conflicting communication.

### Detection
- Account Service validates pending transaction count before executing state transition to `PENDING_CLOSURE`.
- Query: `SELECT COUNT(*) FROM transactions WHERE account_id = ? AND status NOT IN ('COMPLETED', 'FAILED', 'REVERSED')`.
- Pre-closure validation also checks: authorized card holds, open disputes, linked standing orders not yet cancelled.

### Mitigation
- **Block immediate closure:** If any transaction is in `INITIATED`, `FRAUD_REVIEW`, `PROCESSING`, or `PENDING_SETTLEMENT` state, return HTTP 409 Conflict with a response body listing each pending item and its estimated settlement date.
- **Deferred closure:** Set account status to `PENDING_CLOSURE` with a `closure_requested_at` timestamp. A scheduled job re-attempts closure every hour.
- **Customer communication:** Notify customer: "Your account closure has been requested. It will complete within 2 business days once all pending transactions settle (ACH transfer $3,200 — expected settlement 2024-06-03)."
- **Timeout safeguard:** If account remains in `PENDING_CLOSURE` for more than 10 business days (all transactions should have settled or returned by then), escalate to back-office for manual investigation.
- **Freeze controls:** While in `PENDING_CLOSURE`, block new debit transactions. Allow credits (ACH returns, settlement credits) and allow outbound ACH return processing.

### Recovery
1. Monitor `pending_closure_accounts` table via scheduled job.
2. On each cycle, query outstanding transactions — when count = 0, execute closure: deactivate account, cancel all cards, generate closing statement, disburse closing balance via ACH or check.
3. If ACH return arrives for a `PENDING_CLOSURE` account, process the return credit normally (account can accept credits in this state), then re-attempt closure on next cycle.
4. If settlement completes (debit confirmed), proceed with closure — balance now reflects settled state.
5. Closing balance disbursement: if balance > $0 after closure, auto-issue ACH credit to customer's forwarding account or mail check within 5 business days (Reg E requirement).

---

## Dormant Account Reactivation with Outdated or Expired KYC

### Scenario
A customer's account has been dormant for 28 months. Their KYC record (verified at account opening) expired after 24 months per the platform's risk-based review schedule. The customer now logs in and initiates a $7,500 transfer to a new payee.

### Failure Mode
The system allows the reactivation (customer has valid credentials) and processes the transfer without triggering KYC refresh. The customer's circumstances may have changed substantially (new address, updated source of wealth, potential sanctions list addition after initial KYC). Permitting a large-value transaction without current KYC exposes the institution to BSA/AML violation.

### Impact
- **Regulatory:** BSA/AML violation — failure to maintain current customer due diligence (CDD). FinCEN may fine the institution; potential loss of banking charter.
- **Financial:** If the customer is now on a sanctions list, OFAC violation fines (up to $20M per transaction under IEEPA).
- **Operational:** Retroactive investigation required for any transactions processed during the expired KYC window.

### Detection
- On every login, check `kyc_records.expires_at` against `NOW()`.
- On every high-value transaction (> $5,000), additionally check KYC validity regardless of login state.
- Separate alert for accounts where KYC expired > 90 days ago AND balance > $10,000 — proactive outreach required.

### Mitigation
- **Soft restriction:** Account reactivates for low-risk activities (balance check, statement download) but transactions above $500 are blocked until KYC refresh completes.
- **KYC refresh flow:** On login, display prominent in-app banner: "Please verify your identity to continue using your account." Initiate KYC refresh via Jumio (same flow as onboarding but pre-fills known data).
- **Sanctions re-screening:** Immediately re-screen dormant customer against current OFAC/UN/EU/PEP lists before permitting any transaction — do not rely on historic screen result.
- **Risk-based escalation:** If account was dormant > 24 months AND last KYC was `MEDIUM` or `HIGH` risk rating, require full EDD refresh before any transactions.
- **New payee controls:** Transfers to new payees (not seen in last 12 months) require additional step-up regardless of KYC status during reactivation period.

### Recovery
1. Customer completes KYC refresh — Jumio processes in ~3 minutes for clear cases.
2. If KYC refresh approved, account fully reactivated; queued transfer released.
3. If KYC refresh results in `ADDITIONAL_INFO_REQUIRED`, transaction remains blocked; customer given 14-day window.
4. If KYC refresh fails (sanctions hit, document fraud), account immediately frozen; compliance team alerted; SAR consideration triggered if funds > $5,000.
5. Audit log: all reactivation events logged with KYC status at time of reactivation for regulatory examination.

---

## Balance Discrepancy on Account Number Migration

### Scenario
The platform migrates from legacy account numbers (10-digit) to new IBAN-compatible account numbers (20-digit) as part of an infrastructure upgrade. The migration runs over a weekend, reassigning new account numbers to all 2.3 million accounts. A small batch (0.003% — approximately 690 accounts) encounters a race condition: an ACH credit arrives via the old account number at 11:58 PM Saturday during the migration window, and the routing lookup table has already updated to the new number.

### Failure Mode
The inbound ACH credit cannot be matched to a customer account because the old account number no longer resolves. The RDFI (our system) cannot return an R03 (Account Closed) because the account is technically active — just with a new number. The credit is posted to a catch-all suspense account. The customer's balance never reflects the incoming funds.

### Impact
- **Financial:** Funds suspended in a suspense GL account — not visible to customer or bank ledger. If undetected, funds may be reported as income (incorrect P&L).
- **Customer:** Expected salary deposit does not appear — customer's direct debits bounce (NSF fees).
- **Regulatory:** Reg E violation — funds not credited within required timeline.
- **Operational:** Reconciliation of suspense account is manual and time-consuming at scale.

### Detection
- Reconciliation job: nightly comparison of ACH settled credits vs. posted transactions. Any settled credit without a matching posted transaction triggers alert within 2 hours.
- Suspense account monitoring: any balance > $0 in suspense GL triggers immediate PagerDuty alert.
- Migration monitoring dashboard: real-time count of unmatched ACH transactions during migration window.

### Mitigation
- **Dual-lookup routing:** During migration and for 90 days post-migration, ACH routing table accepts BOTH old and new account numbers (backwards-compatible mapping table `old_to_new_account_numbers`).
- **Migration window:** Schedule migration between 11 PM and 4 AM, the lowest ACH activity window. Coordinate with ACH operator to defer late-arriving credits by 15 minutes.
- **Idempotent credit application:** ACH credit processor is idempotent — deduplicate by ACH trace number before posting; prevents double-credit if retry occurs.
- **Automated suspense resolution:** Job runs hourly to match suspense entries against old account numbers via the mapping table and post corrections automatically.
- **Cutover testing:** Run 100% reconciliation in staging environment against prior month's transaction volume before executing production migration.

### Recovery
1. Run automated suspense-resolution job: match all suspense credits against old→new account mapping.
2. Post correcting journal entries: credit customer accounts with suspended amounts.
3. Reverse any NSF fees triggered by the missed credit (customer-friendly resolution).
4. Notify affected customers: "A technical issue delayed the posting of your deposit. It has been resolved, and any associated fees have been waived."
5. Post-incident: implement automated daily suspense reconciliation as permanent control. Target: suspense balance = $0 every morning by 6 AM.

---

## Joint Account Holder Death During Active Credit Facility

### Scenario
A joint checking account has two holders — primary holder Alice, secondary holder Bob. The account has a $25,000 overdraft facility (credit). Bob passes away. The estate executor contacts the bank, presenting a death certificate. The account has a current overdraft balance of $8,400 outstanding.

### Failure Mode
The system lacks a defined state for "deceased secondary holder." Without guidance, customer service representatives may: (1) immediately freeze the account (blocking Alice's access to funds she needs for day-to-day expenses), (2) immediately transfer full credit liability to Alice alone without proper legal review, or (3) fail to notify the credit risk team, leaving $8,400 outstanding under a partially unenforceable credit agreement.

### Impact
- **Legal:** Joint credit agreement terms govern liability — both holders are typically jointly and severally liable; surviving holder may bear full liability but legal review required.
- **Financial:** Credit risk: $8,400 outstanding — collectability may be reduced if estate has insufficient assets.
- **Customer:** Alice may be locked out of her primary account during an already stressful period.
- **Regulatory:** Fair debt collection practices apply to estate; bereavement policy required by FCA (UK) / CFPB guidance (US).

### Detection
- Bereavement notification triggers a specific case type in the CRM system.
- Estate executor provides death certificate — document stored in KYC record as a linked life event.
- Automated watchlist re-screen detects if a deceased person is still an active account holder (death notification registries, if subscribed).

### Mitigation
- **Bereavement policy:** Documented SLA — estate team contacts executor within 2 business days of notification.
- **Access preservation:** Do not freeze account immediately for the surviving holder. Convert to single-holder access — remove deceased's biometric/OTP authentication only. Alice retains full access.
- **Credit review:** Credit Risk team reviews the $8,400 facility within 5 business days. Options: (a) Alice assumes sole liability — requires underwriting review of Alice's solo creditworthiness; (b) facility converted to term loan with manageable repayment; (c) estate notified of outstanding balance — claim against estate filed.
- **Bereavement rate:** Consider temporarily reducing interest rate on outstanding balance during the estate administration period (typically 6–12 months).
- **Estate closure:** If estate is wound up and balance is uncollectible: assess for charge-off (credit loss provisioning) and write-off procedure.
- **SCRA check:** If deceased was an active military member, apply SCRA protections (50% interest cap on pre-service debt, no adverse action during active duty).

### Recovery
1. Estate team opens case, logs all communications.
2. Credit Risk approves revised facility terms or begins estate claim process.
3. Account converted to sole ownership (Alice) following legal documentation review.
4. If asset recovery from estate: formal claim submitted within probate deadline.
5. Annual review: assess bereavement policy against regulatory guidance updates (CFPB, OCC).

---

## Minor Turning 18 — Account Type Conversion

### Scenario
A custodial savings account was opened for Jamie when they were 12, with a parent as the custodian. The account has $14,200 accumulated. Jamie turns 18 tomorrow. Per UTMA (Uniform Transfers to Minors Act), the assets must transfer to Jamie's sole ownership. The system needs to convert the custodial account to an individual account.

### Failure Mode
The custodial account structure requires both the minor's and custodian's identifiers. On the 18th birthday, if the system does not automatically initiate conversion, the account remains in limbo — Jamie cannot independently access the full balance, and the parent-custodian retains access they are no longer legally entitled to. If the system converts without proper KYC for the adult Jamie, the bank is in violation of CIP rules.

### Impact
- **Legal:** UTMA mandates transfer at age of majority — non-compliance exposes institution to fiduciary liability.
- **Regulatory:** Adult Jamie must have their own CIP-compliant identity verification before becoming sole account holder.
- **Customer:** Jamie expects unrestricted access on their 18th birthday; delays cause dissatisfaction and potential complaints to CFPB.

### Detection
- Scheduled daily job: query `accounts WHERE account_type = 'CUSTODIAL' AND minor_dob + 18 years <= CURRENT_DATE AND conversion_status != 'COMPLETED'`.
- Alert 90 days before 18th birthday to initiate proactive communication campaign.

### Mitigation
- **T-90 days:** Email/push to custodian: "Jamie's account will require conversion when they turn 18. Please ask Jamie to create an account so we can complete the transfer smoothly."
- **T-30 days:** If Jamie has not registered independently, send reminder with direct link to create adult account.
- **T-7 days:** Final reminder; if no action, flag account for customer service outreach.
- **T+0 (18th birthday):** Job runs at midnight: (a) if Jamie has an active individual account with completed KYC → auto-merge: transfer $14,200 to individual account, close custodial account, generate UTMA transfer statement; (b) if Jamie has no individual account → freeze custodian's write access (read-only for 30 days), initiate KYC flow for Jamie, hold funds in custodial account until conversion completes.
- **KYC for Jamie:** Full CIP required — document (passport or DL) + SSN verification + liveness check. Same flow as new customer onboarding.
- **Custodian notification:** Inform custodian that their access ended on Jamie's 18th birthday per UTMA.

### Recovery
1. Conversion completes when Jamie's KYC is approved (target: same-day if Jamie is prepared).
2. If Jamie is unresponsive within 30 days: account placed in `PENDING_CONVERSION` state; quarterly outreach; escalate after 6 months.
3. Post-conversion: issue new account number and routing details to Jamie; old custodial account number retired.
4. Tax reporting: Form 1099 for interest earned sent under Jamie's SSN from year of conversion forward; prior years under custodian's SSN as applicable.

---

## Account Ownership Dispute — Suspected Fraud or Death

### Scenario
Customer service receives a call from a person claiming to be the rightful owner of account ACC-00291847, alleging someone else has taken over the account (suspected account takeover). Simultaneously, the current account holder claims the calling party is attempting social engineering. The account has a $42,000 balance and 3 pending outbound transfers totaling $38,000.

### Failure Mode
If the support agent acts immediately on the caller's claim and resets credentials, the attacker gains access. If the support agent dismisses the claim and does nothing, a legitimate victim continues to suffer account takeover. The 3 pending transfers, if allowed to complete, result in near-total loss.

### Impact
- **Financial:** $38,000 at risk if pending transfers complete before the dispute is resolved.
- **Customer:** Either a fraud victim loses their funds, or a fraudster successfully social-engineers account access.
- **Regulatory:** Reg E: once unauthorized access is reported, the institution has 10 business days to investigate and issue provisional credit (or 5 business days for accounts open < 30 days).

### Detection
- Anomaly flags that should have triggered before this point: new device, new IP geolocation, 3 large outbound transfers to new payees in same session.
- Fraud detection: velocity model should score this session as HIGH risk (> 0.85) and block the transfers.

### Mitigation
- **Immediate:** On first report of account dispute, place a soft hold on ALL outbound transactions from the account — do not allow any pending transfers to progress. This is the most critical control.
- **Verification of both parties:** Do not action either claim based solely on phone call. Require in-person identity verification or strong digital identity proof (government ID + liveness check) from both claimants before making any access changes.
- **Evidence gathering:** Preserve all session logs, device fingerprints, IP addresses, transaction records from the disputed period — critical for investigation.
- **Provisional access:** Neither party receives access changes until investigation concludes. The current authenticated session remains active but outbound transfers are blocked.
- **Timeline:** Investigation must complete within 10 business days (Reg E). If inconclusive, extend up to 45 business days with provisional credit to the legitimate party.

### Recovery
1. Fraud investigation team reviews device fingerprint, geolocation, behavioral biometrics for current session holder.
2. Contact the original account applicant (at KYC-verified contact details, not details changed in disputed session) — attempt to reach via documented phone number and email.
3. If original holder confirmed as victim: reverse all unauthorized transactions initiated by attacker, issue provisional credit for any completed unauthorized transfers, begin chargeback/ACH return process.
4. If investigation reveals caller is the attacker (social engineering attempt): document and close case, flag caller's identity details for fraud pattern analysis, consider SAR if pattern is systematic.
5. Post-resolution: enhanced monitoring on account for 90 days; force full re-authentication with identity verification for all sessions.

---

## Cross-Cutting Account Controls

The following controls apply across all account lifecycle edge cases and represent standing operational practices rather than per-scenario responses.

**Balance Integrity Checks:**
- Every debit and credit operation uses optimistic locking (PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED`) to prevent concurrent balance modifications.
- Nightly reconciliation job: compares Aurora balance with Mambu/Thought Machine core banking balance. Discrepancy > $0.01 → immediate P2 alert. Target: zero discrepancies by 6 AM daily.
- Intraday reconciliation: runs every 4 hours during business hours. Monitors suspense account balances — target $0 at all checkpoints.

**Audit Trail Requirements:**
- Every account state transition is an immutable event record in the `account_events` table: (event_id, account_id, from_state, to_state, reason_code, actor_id, actor_type [CUSTOMER, AGENT, SYSTEM], timestamp, metadata_json).
- Events are also published to Kafka `accounts.events` topic — retained 7 years (S3 archival after 30 days hot).
- No account event record can be deleted or updated — append-only via row-level security. Even DBAs cannot delete.

**Regulatory Retention Schedule:**
| Record Type | Retention Period | Basis |
|-------------|-----------------|-------|
| Account opening documents | 7 years post-closure | BSA §1020.220 |
| KYC verification records | 5 years post-closure | BSA §1020.220 |
| Transaction records | 7 years | BSA §1020.210 |
| Adverse action notices | 25 months | ECOA Reg B |
| OFAC screening records | 5 years | OFAC regulations |
| CTR filings | 5 years from filing | BSA §1010.430 |
| SAR filings | 5 years from filing | BSA §1020.320 |
| Call recordings (disputes) | 2 years | Reg E safe harbor |

**Customer Communication SLAs:**
- Account opening: onboarding completion notification within 5 minutes of KYC approval.
- Account freeze: customer notification within 1 business day (unless law enforcement prohibits — e.g., pending investigation notice).
- Account closure: closing statement within 5 business days; final balance disbursement within 10 business days.
- Dormancy notice: 30 days before dormancy classification; 60 days before escheatment.

**Escalation Matrix for Account State Changes:**
| Action | Level 1 Authority | Level 2 Authority | Level 3 Authority |
|--------|------------------|-------------------|-------------------|
| Freeze account (compliance hold) | Compliance Analyst | Senior Compliance Officer | CCO |
| Unfreeze account | Senior Compliance Officer | CCO | CCO + Legal Counsel |
| Close account (regulatory) | Compliance Officer | CCO | CCO + Board Notification |
| Approve EDD (PEP) | Deputy MLRO | MLRO | CCO |
| Reverse account closure | Operations Manager | VP Operations | — |

All Level 2 and above actions require dual authorization (four-eyes principle) and are logged in both the core banking system and the compliance case management system.

---

## Account Health Monitoring

Proactive account health monitoring identifies edge-case conditions before they escalate into regulatory violations or customer harm.

**Daily Account Health Checks (automated, run at 5 AM ET):**
- Accounts in `PENDING_KYC` for > 30 days → escalate to KYC ops team; customer re-notification.
- Accounts in `PENDING_CLOSURE` for > 10 business days → back-office escalation.
- Accounts in `FROZEN` for > 90 days without documented review → CCO notification.
- Accounts where KYC `expires_at` is within 60 days → initiate proactive refresh outreach.
- Custodial accounts where minor's 18th birthday is within 90 days → initiate conversion campaign.
- Dormant accounts approaching state escheatment deadline (within 90 days) → mandatory outreach.

**Balance Anomaly Detection:**
- Account balance decreased by > 50% in a single transaction → fraud review trigger (if not already flagged by real-time fraud engine).
- Negative available balance on a non-overdraft account → immediate alert (indicates ledger error or race condition).
- Available balance significantly different from ledger balance for > 24 hours (excluding pending transactions) → reconciliation investigation.

**Regulatory Exposure Metrics:**
- Total dormant account balance by state → fed into annual unclaimed property filing calculation.
- Accounts pending KYC refresh by risk tier → input to AML risk management report.
- Average account closure time → metric tracked for Reg E compliance.
- Joint accounts with deceased holder ratio → fed into estate management reporting.

**Account Lifecycle SLA Summary:**
| Lifecycle Event | Target SLA | Regulatory Basis |
|----------------|-----------|-----------------|
| KYC verification completion | 24h (automated), 5 days (manual) | CIP |
| Account activation post-KYC | 15 minutes (automated) | CIP |
| Account freeze notification to customer | 1 business day | — |
| Account closure (customer request) | 10 business days | Reg E |
| Final balance disbursement post-closure | 10 business days | — |
| Dormancy notice before state reporting | 30 days prior | State law |
| UTMA conversion at age 18 | Same day (if prepared) | UTMA |
| Dispute investigation resolution | 10 business days | Reg E |
| Provisional credit (Reg E dispute) | 5 business days | Reg E §1005.11 |

---

## Automated Account Lifecycle Governance

Account lifecycle governance runs as a scheduled Kubernetes CronJob (`account-lifecycle-governor`) executing at 5:00 AM ET on all business days and at 6:00 AM ET on weekends.

**Governance Job — Key Checks:**

```java
// Pseudo-code: AccountLifecycleGovernorJob.java
@Scheduled(cron = "0 5 * * *", zone = "America/New_York")
public void runGovernance() {
    // 1. KYC expiry approaching — low risk customers
    accountRepository.findByKYCExpiryBefore(now().plusDays(60), RiskRating.LOW)
        .forEach(account -> notificationService.sendKYCRefreshReminder(account));

    // 2. KYC expiry approaching — high risk customers (shorter window)
    accountRepository.findByKYCExpiryBefore(now().plusDays(30), RiskRating.HIGH)
        .forEach(account -> kycService.initiateRefresh(account));

    // 3. Dormancy check
    accountRepository.findInactiveAccounts(dormancyThresholdMonths)
        .filter(account -> account.getStatus() == ACTIVE)
        .forEach(account -> {
            account.setStatus(DORMANT);
            notificationService.sendDormancyNotice(account);
            auditLogger.log(account, DORMANCY_CLASSIFIED, SYSTEM);
        });

    // 4. UTMA conversion check
    accountRepository.findCustodialAccountsReachingMajority(now().plusDays(90))
        .forEach(account -> conversionService.initiateConversionCampaign(account));

    // 5. Pending closure resolution
    accountRepository.findByStatus(PENDING_CLOSURE)
        .filter(account -> transactionRepository.countPending(account) == 0)
        .forEach(account -> closureService.executeClosure(account));
}
```

**Exception Handling:** Any exception in the governance job is logged to `account_governance_errors` table and triggers a PagerDuty P3 alert. The job uses idempotent operations — safe to re-run if partial failure occurs. Job run history retained 2 years.
